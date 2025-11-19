import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import io
import zipfile
import requests
import qrcode  # Нужно для генерации, если ссылка не картинка
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
    .stApp {
        background-color: #FFFFFF !important;
    }
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
    
    header, footer, #MainMenu {visibility: hidden;}
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 5rem !important;
    }

    /* 3. ИНПУТЫ */
    div[data-baseweb="input"] > div {
        border-radius: 14px !important;
        border: 1px solid #E0E0E0 !important;
        background-color: #FFFFFF !important;
    }
    div[data-baseweb="input"] > div:focus-within {
        border-color: #000 !important;
        box-shadow: none !important;
    }
    input {
        font-size: 16px !important;
        color: #000 !important;
        background-color: #FFFFFF !important;
    }
    
    /* 4. КНОПКИ ДЕЙСТВИЯ (ИСПРАВЛЕН ЦВЕТ ТЕКСТА) */
    div.stButton, div.stDownloadButton {
        width: 100% !important;
    }
    div.stButton > button, div.stDownloadButton > button {
        width: 100% !important;
        background-color: #000000 !important;
        color: #FFFFFF !important; /* БЕЛЫЙ ТЕКСТ */
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
    }
    div.stButton > button p, div.stDownloadButton > button p {
        color: #FFFFFF !important; /* Принудительно красим текст внутри кнопки */
    }

    /* 5. ЗАГРУЗЧИК */
    [data-testid="stFileUploader"] {
        padding: 20px !important;
        background-color: #F7F7F7 !important;
        border-radius: 14px !important;
    }
    [data-testid="stFileUploader"] button {
        color: #000 !important;
        border-color: #E0E0E0 !important;
    }
    
    /* 6. ЧЕКБОКС (TOGGLE) */
    label[data-baseweb="checkbox"] {
        border-radius: 14px;
    }
    
    /* TABS */
    .stTabs [data-baseweb="tab-list"] {border-bottom: 2px solid #eee !important;}
    .stTabs [aria-selected="true"] {color: #000 !important; border-bottom: 2px solid #000 !important;}
    
    hr {border-color: #eee !important; margin: 40px 0 !important;}
</style>
""", unsafe_allow_html=True)

# --- ЛОГИКА ---
MM_TO_POINT = 72 / 25.4
HEADERS = {"User-Agent": "Mozilla/5.0"}

def mm_to_pt(mm_val):
    return mm_val * MM_TO_POINT

def get_or_generate_qr_image(link):
    """
    Пытается скачать картинку по ссылке.
    Если это не картинка или ошибка - генерирует новый QR.
    Возвращает байты PNG.
    """
    # 1. Пробуем скачать как картинку
    try:
        resp = requests.get(link, headers=HEADERS, timeout=5)
        if resp.status_code == 200:
            # Пытаемся открыть как изображение
            pil_img = Image.open(io.BytesIO(resp.content))
            img_byte_arr = io.BytesIO()
            pil_img.save(img_byte_arr, format="PNG")
            return img_byte_arr.getvalue()
    except:
        pass # Если ошибка - идем к генерации

    # 2. Если не вышло - генерируем QR
    try:
        qr = qrcode.QRCode(box_size=10, border=0)
        qr.add_data(link)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="PNG")
        return img_byte_arr.getvalue()
    except Exception as e:
        print(f"QR Generation failed: {e}")
        return None

def process_files(pdf_file, links, p_name, p_size, auto_center, x_mm, y_mm, size_mm):
    zip_buffer = io.BytesIO()
    pdf_file.seek(0)
    pdf_bytes = pdf_file.read()
    
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        for i, url in enumerate(links, start=1):
            filename = f"{p_name}_{p_size}_{i:02d}.pdf"
            
            # Получаем картинку (скачанную или сгенерированную)
            qr_bytes = get_or_generate_qr_image(url)
            
            if qr_bytes:
                with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                    page = doc[0] # Работаем с первой страницей
                    
                    # ЛОГИКА ПОЗИЦИОНИРОВАНИЯ
                    if auto_center:
                        # Ширина страницы в пунктах
                        page_w = page.rect.width
                        page_h = page.rect.height
                        
                        # Размер QR = 1/3 от ширины страницы
                        qr_size_pt = page_w / 3
                        
                        # Центрирование: (ШиринаСтр - ШиринаQR) / 2
                        x_pt = (page_w - qr_size_pt) / 2
                        y_pt = (page_h - qr_size_pt) / 2 # По центру по вертикали тоже
                    else:
                        # Ручной ввод (перевод мм в пункты)
                        x_pt = mm_to_pt(x_mm)
                        y_pt = mm_to_pt(y_mm)
                        qr_size_pt = mm_to_pt(size_mm)
                    
                    # Создаем прямоугольник вставки
                    rect = fitz.Rect(x_pt, y_pt, x_pt + qr_size_pt, y_pt + qr_size_pt)
                    
                    # Вставляем
                    page.insert_image(rect, stream=qr_bytes)
                    zf.writestr(filename, doc.convert_to_pdf())
            else:
                # Если совсем не получилось (пустая ссылка и тд)
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
    
    # ЧЕКБОКС АВТОМАТИКИ
    auto_pos = st.toggle("Авто-центрирование (по центру, 1/3 ширины)", value=True)
    
    if not auto_pos:
        st.markdown('<div class="description" style="margin-bottom:10px;">Геометрия (мм)</div>', unsafe_allow_html=True)
        g1, g2, g3 = st.column
