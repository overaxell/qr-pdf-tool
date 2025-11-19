import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import io
import zipfile
import requests
from PIL import Image

# --- КОНФИГУРАЦИЯ СТРАНИЦЫ ---
st.set_page_config(
    page_title="Кюарыч",
    page_icon="▪️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ЖЕСТКИЙ CUSTOM CSS (BLACK & WHITE) ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;800&display=swap" rel="stylesheet">
<style>
    /* 1. ГЛОБАЛЬНЫЕ НАСТРОЙКИ */
    /* Принудительный белый фон для основного контейнера (на случай если конфиг не сработает) */
    .stApp {
        background-color: #FFFFFF !important;
    }

    /* Шрифт Manrope и черный цвет текста везде */
    html, body, p, div, span, h1, h2, h3, h4, h5, h6, button, input, textarea, label, li, a {
        font-family: 'Manrope', sans-serif !important;
        color: #000000 !important;
    }

    /* 2. ТИПОГРАФИКА */
    .big-title {
        font-size: 80px !important;
        font-weight: 800 !important;
        line-height: 1 !important;
        margin-bottom: 10px !important;
        letter-spacing: -2px !important;
        color: #000 !important;
    }
    .section-title {
        font-size: 32px !important;
        font-weight: 600 !important;
        margin-top: 30px !important;
        margin-bottom: 15px !important;
        color: #000 !important;
    }
    .description {
        font-size: 16px !important;
        color: #666 !important;
        line-height: 1.5 !important;
        margin-bottom: 20px !important;
    }
    
    /* Скрываем системные элементы Streamlit */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 5rem !important;
    }

    /* 3. ИНПУТЫ (ПОЛЯ ВВОДА) */
    div[data-baseweb="input"] > div {
        border-radius: 14px !important;
        border: 1px solid #E0E0E0 !important;
        background-color: #FFFFFF !important;
    }
    /* При фокусе - черная рамка вместо красной */
    div[data-baseweb="input"] > div:focus-within {
        border-color: #000 !important;
        box-shadow: none !important;
    }
    input {
        font-size: 16px !important;
        color: #000 !important;
        background-color: #FFFFFF !important;
    }
    .stTextInput label, .stNumberInput label, .stTextArea label {
        font-size: 14px !important;
        color: rgba(0,0,0,0.6) !important;
    }
    
    /* КНОПКИ +/- В NUMBER INPUT (Убираем красный цвет) */
    button[kind="secondary"] {
        border: none !important;
        background: transparent !important;
        color: #333 !important;
    }
    button[kind="secondary"]:hover {
        color: #000 !important;
        background: #F5F5F5 !important;
    }
    button[kind="secondary"]:active, button[kind="secondary"]:focus {
        color: #000 !important;
        border: none !important;
        box-shadow: none !important;
        background: #E0E0E0 !important;
    }

    /* 4. ОСНОВНЫЕ КНОПКИ (Генерация / Скачать) */
    div.stButton, div.stDownloadButton {
        width: 100% !important;
    }
    div.stButton > button, div.stDownloadButton > button {
        width: 100% !important;
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border-radius: 14px !important;
        padding: 18px 20px !important;
        font-size: 20px !important;
        font-weight: 500 !important;
        border: none !important;
        box-shadow: none !important;
        height: auto !important;
        display: flex !important;
        justify-content: center !important;
    }
    div.stButton > button:hover, div.stDownloadButton > button:hover {
        background-color: #333333 !important;
        color: #FFFFFF !important;
        border: none !important;
    }
    /* Убираем красную обводку при нажатии */
    div.stButton > button:focus, div.stButton > button:active {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* 5. ЗАГРУЗЧИК ФАЙЛОВ */
    [data-testid="stFileUploader"] {
        padding: 20px !important;
        background-color: #F7F7F7 !important;
        border-radius: 14px !important;
    }
    [data-testid="stFileUploader"] button {
        color: #000 !important;
        border-color: #E0E0E0 !important;
    }
    [data-testid="stFileUploader"] button:hover {
        border-color: #000 !important;
    }
    
    /* 6. ТАБЫ (Вручную / Из Excel) */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 2px solid #eee !important;
        gap: 30px !important;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 20px !important;
        font-weight: 600 !important;
        color: #999 !important;
        background: transparent !important;
        border: none !important;
        padding-bottom: 10px !important;
    }
    /* Активный таб - черный */
    .stTabs [aria-selected="true"] {
        color: #000 !important;
        border-bottom: 2px solid #000 !important;
    }
    
    /* Убираем красную полоску (focus ring) у всех элементов */
    *:focus-visible {
        outline: none !important;
        box-shadow: none !important;
    }

    hr {
        border-color: #eee !important;
        margin: 40px 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- ЛОГИКА ---
MM_TO_POINT = 72 / 25.4
HEADERS = {"User-Agent": "Mozilla/5.0"}

def mm_to_pt(mm_val):
    return mm_val * MM_TO_POINT

def process_files(pdf_file, links, p_name, p_size, x_mm, y_mm, s_mm):
    rect = fitz.Rect(mm_to_pt(x_mm), mm_to_pt(y_mm), mm_to_pt(x_mm)+mm_to_pt(s_mm), mm_to_pt(y_mm)+mm_to_pt(s_mm))
    zip_buffer = io.BytesIO()
    pdf_file.seek(0)
    pdf_bytes = pdf_file.read()
    
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        for i, url in enumerate(links, start=1):
            filename = f"{p_name}_{p_size}_{i:02d}.pdf"
            try:
                resp = requests.get(url, headers=HEADERS, timeout=10)
                if resp.status_code == 200:
                    pil_img = Image.open(io.BytesIO(resp.content))
                    img_byte_arr = io.BytesIO()
                    pil_img.save(img_byte_arr, format="PNG")
                    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                        doc[0].insert_image(rect, stream=img_byte_arr.getvalue())
                        zf.writestr(filename, doc.convert_to_pdf())
            except:
                pass
    zip_buffer.seek(0)
    return zip_buffer

# --- ВЕРСТКА ---

col_left, col_spacer, col_right = st.columns([1.3, 0.1, 1])

# === ЛЕВАЯ КОЛОНКА ===
with col_left:
    st.markdown('<div class="big-title">Кюарыч</div>', unsafe_allow_html=True)
    st.markdown('<div class="description">Удобный помощник для маркетинг-команды. Загружайте макет,<br>вставляйте ссылки — а я красиво и точно расставлю QR-коды сам.</div>', unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">Как назвать файл?</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        partner_name = st.text_input("Имя партнера", placeholder="Partner name")
    with c2:
        size_name = st.text_input("Размер файла", placeholder="7x7")
        
    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown('<div class="section-title">Куда вставить QR?</div>', unsafe_allow_html=True)
    st.markdown('<div class="description" style="margin-bottom:10px;">Геометрия (мм)</div>', unsafe_allow_html=True)
    
    g1, g2, g3 = st.columns(3)
    with g1:
        x_mm = st.number_input("Отступ слева", value=20.0, step=1.0, format="%.2f")
    with g2:
        y_mm = st.number_input("Отступ сверху", value=20.0, step=1.0, format="%.2f")
    with g3:
        size_mm = st.number_input("Размер кюара", value=20.0, step=1.0, format="%.2f")


# === ПРАВАЯ КОЛОНКА ===
with col_right:
    st.write("")
    st.write("")
    
    st.markdown('<div class="description" style="margin-bottom:0;">Источник ссылок QR</div>', unsafe_allow_html=True)
    
    tab_manual, tab_excel = st.tabs(["Вручную", "Из excel"])
    
    links_final = []
    with tab_manual:
        st.write("
