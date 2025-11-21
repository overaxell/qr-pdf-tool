import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import io
import zipfile
import requests
import qrcode
from PIL import Image
from openpyxl import load_workbook  # чтение гиперссылок из Excel
import numpy as np

# --- КОНФИГУРАЦИЯ СТРАНИЦЫ ---
st.set_page_config(
    page_title="Кюарыч",
    page_icon="▪️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS СТИЛИ + АНИМАЦИИ ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;800&display=swap" rel="stylesheet">
<style>
    .stApp {background-color: #FFFFFF !important;}

    /* span не трогаем, чтобы не ломать иконки (keyboard_arrow_right и т.п.) */
    html, body, p, div, h1, h2, h3, h4, h5, h6, button, input, textarea, label, li, a {
        font-family: 'Manrope', sans-serif !important;
        color: #000000 !important;
    }

    /* АНИМАЦИИ */
    @keyframes fadeUp {
        0% {opacity: 0; transform: translateY(8px);}
        100% {opacity: 1; transform: translateY(0);}
    }
    @keyframes fadeInSoft {
        0% {opacity: 0;}
        100% {opacity: 1;}
    }
    @keyframes pulseSoft {
        0%   {transform: scale(1);}
        50%  {transform: scale(1.02);}
        100% {transform: scale(1);}
    }

    .big-title {
        font-size: 96px !important;
        font-weight: 800 !important;
        line-height: 1.0 !important;
        letter-spacing: -3px !important;
        margin-bottom: 20px !important;
        display: block !important;
        animation: fadeUp 0.6s ease-out both;
    }
    .description {
        font-size: 18px !important;
        color: #666 !important;
        line-height: 1.5 !important;
        margin-bottom: 18px !important;
        max-width: 650px;
        display: block !important;
        animation: fadeInSoft 0.6s ease-out both;
        animation-delay: 0.1s;
    }
    .section-title {
        font-size: 32px !important;
        font-weight: 600 !important;
        margin-top: 24px !important;
    }
    header, footer, #MainMenu {visibility: hidden;}
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 4rem !important;
        animation: fadeInSoft 0.4s ease-out;
    }

    /* === ЕДИНАЯ РАМКА ДЛЯ ВСЕХ INPUT/NUMBER_INPUT === */
    div[data-baseweb="input"] {
        border-radius: 14px !important;
        border: 1px solid #E0E0E0 !important;
        background-color: #FFFFFF !important;
        box-shadow: none !important;
        overflow: hidden !important;
        transition: border-color 0.18s ease-out,
                    box-shadow 0.18s ease-out,
                    transform 0.10s ease-out;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #000000 !important;
        box-shadow: 0 0 0 1px #00000010;
        transform: translateY(-1px);
    }

    /* Убираем любые внутренние рамки и тени (в том числе у number_input) */
    div[data-baseweb="input"] * {
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }

    /* Само текстовое поле */
    div[data-baseweb="input"] input {
        background-color: transparent !important;
    }

    /* Кнопки +/- у number_input */
    div[data-baseweb="input"] button {
        background-color: #F5F5F5 !important;
        color: #000000 !important;
    }
    div[data-baseweb="input"] button:hover {
        /* фон может быть чёрным из дефолтных стилей, главное — сделать текст белым */
        color: #FFFFFF !important;
    }

    div.stButton, div.stDownloadButton {
        width: 100% !important;
        display: block !important;
    }

    /* Обычные кнопки (например, Генерация) — чёрные с микроанимацией */
    div.stButton > button {
        width: 100% !important;
        min-width: 300px !important;
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border-radius: 14px !important;
        padding: 18px 40px !important;
        font-size: 18px !important;
        font-weight: 500 !important;
        border: none !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        white-space: nowrap !important;
        transition: background-color 0.18s ease-out,
                    transform 0.12s ease-out,
                    box-shadow 0.18s ease-out;
        box-shadow: 0 6px 14px rgba(0, 0, 0, 0.08);
    }
    div.stButton > button:hover {
        background-color: #333333 !important;
        transform: translateY(-1px) scale(1.01);
        box-shadow: 0 10px 22px rgba(0, 0, 0, 0.12);
    }
    div.stButton > button:active {
        transform: translateY(0) scale(0.99);
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.10);
    }

    /* Кнопка скачивания — маджента + пульс, когда видна */
    div.stDownloadButton > button {
        width: 100% !important;
        min-width: 300px !important;
        background-color: #f0047f !important;
        color: #FFFFFF !important;
        border-radius: 14px !important;
        padding: 18px 40px !important;
        font-size: 18px !important;
        font-weight: 500 !important;
        border: none !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        white-space: nowrap !important;
        box-shadow: 0 8px 18px rgba(240, 4, 127, 0.4);
        transition: background-color 0.18s ease-out,
                    transform 0.12s ease-out,
                    box-shadow 0.18s ease-out;
        animation: pulseSoft 1.6s ease-in-out infinite;
    }
    div.stDownloadButton > button:hover {
        background-color: #c00367 !important;
        transform: translateY(-1px) scale(1.01);
        box-shadow: 0 12px 26px rgba(240, 4, 127, 0.5);
    }
    div.stDownloadButton > button:active {
        transform: translateY(0) scale(0.99);
        box-shadow: 0 6px 14px rgba(240, 4, 127, 0.4);
    }

    div.stButton > button p, div.stDownloadButton > button p {
        color: #FFFFFF !important;
        margin: 0;
    }

    /* Табы: убираем лишний статичный underline у списка табов */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 0 !important;
    }
    .stTabs [aria-selected="true"] {
        color: #000 !important;
        border-bottom: 2px solid #000 !important;
    }

    hr {border-color: #eee !important; margin: 24px 0 !important;}
</style>
""", unsafe_allow_html=True)

# --- КОНСТАНТЫ ---
MM_TO_POINT = 72 / 25.4
HEADERS = {"User-Agent": "Mozilla/5.0"}


def mm_to_pt(mm_val: float) -> float:
    return mm_val * MM_TO_POINT


# --- QR-ИЗОБРАЖЕНИЕ ---
def get_or_generate_qr_image(link: str):
    if not link or str(link).lower() == "nan":
        return None
    link = str(link).strip()
    if not link:
        return None

    try:
        download_url = link
        if not download_url.startswith("http"):
            download_url = "https://" + download_url
        resp = requests.get(download_url, headers=HEADERS, timeout=3)
        if resp.status_code == 200:
            pil_img = Image.open(io.BytesIO(resp.content))
            img_byte_arr = io.BytesIO()
            pil_img.save(img_byte_arr, format="PNG")
            return img_byte_arr.getvalue()
    except Exception:
        pass

    try:
        qr = qrcode.QRCode(box_size=10, border=0)
        qr.add_data(link)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="PNG")
        return img_byte_arr.getvalue()
    except Exception:
        return None


# --- ВСПОМОГАТЕЛЬНЫЙ РАСТРОВЫЙ ДЕТЕКТОР ---
def _detect_white_rectangles_raster(
    pdf_bytes: bytes,
    white_threshold: int = 245,
    min_area_ratio: float = 0.001,
    max_area_ratio: float = 0.9,
):
    rects_pt = []

    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        page = doc[0]
        page_w_pt = page.rect.width
        page_h_pt = page.rect.height

        pix = page.get_pixmap(alpha=False)
        img_w, img_h = pix.width, pix.height
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(img_h, img_w, 3)

    gray = img.mean(axis=2)

    mask = gray > white_threshold
    visited = np.zeros_like(mask, dtype=bool)

    img_area = img_w * img_h

    def flood_fill(sx, sy):
        stack = [(sx, sy)]
        visited[sy, sx] = True
        min_x = max_x = sx
        min_y = max_y = sy

        while stack:
            x, y = stack.pop()

            if x < min_x:
                min_x = x
            if x > max_x:
                max_x = x
            if y < min_y:
                min_y = y
            if y > max_y:
                max_y = y

            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < img_w and 0 <= ny < img_h:
                    if mask[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        stack.append((nx, ny))

        return min_x, min_y, max_x, max_y

    for y in range(img_h):
        for x in range(img_w):
            if mask[y, x] and not visited[y, x]:
                x1, y1, x2, y2 = flood_fill(x, y)

                w = x2 - x1 + 1
                h = y2 - y1 + 1
                area = w * h
                area_ratio = area / img_area
                if area_ratio < min_area_ratio or area_ratio > max_area_ratio:
                    continue

                aspect = w / h if h != 0 else 0
                if aspect < 0.5 or aspect > 2.0:
                    continue

                x_pt = x1 * page_w_pt / img_w
                y_pt = y1 * page_h_pt / img_h
                w_pt = w * page_w_pt / img_w
                h_pt = h * page_h_pt / img_h

                rects_pt.append((x_pt, y_pt, w_pt, h_pt))

    rects_pt.sort(key=lambda r: r[2] * r[3], reverse=True)
    return rects_pt


# --- ОСНОВНОЙ ДЕТЕКТОР БЕЛЫХ КВАДРАТОВ ---
def detect_white_rectangles_in_pdf(pdf_bytes: bytes):
    rects_pt = []

    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        page = doc[0]
        page_rect = page.rect
        page_w_pt = page_rect.width
        page_h_pt = page_rect.height

        drawings = page.get_drawings()

   
