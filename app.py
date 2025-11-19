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

# --- ЖЕСТКИЙ CUSTOM CSS ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;800&display=swap" rel="stylesheet">
<style>
    /* 1. ПРИНУДИТЕЛЬНЫЙ ШРИФТ MANROPE ДЛЯ ВСЕГО */
    html, body, p, div, span, h1, h2, h3, h4, h5, h6, button, input, textarea, label {
        font-family: 'Manrope', sans-serif !important;
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
    
    /* Скрываем стандартный хедер Streamlit и футер */
    header {visibility: hidden;}
    footer {visibility: hidden;}
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
    div[data-baseweb="input"] > div:focus-within {
        border-color: #000 !important;
    }
    input {
        font-size: 16px !important;
        color: #000 !important;
    }
    .stTextInput label, .stNumberInput label, .stTextArea label {
        font-size: 14px !important;
        color: rgba(0,0,0,0.6) !important;
    }

    /* 4. КНОПКИ (ШИРИНА 100%) */
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
    }

    /* 5. ЗАГРУЗЧИК ФАЙЛОВ */
    [data-testid="stFileUploader"] {
        padding: 20px !important;
        background-color: #F7F7F7 !important;
        border-radius: 14px !important;
    }
    
    /* 6. ТАБЫ */
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
    .stTabs [aria-selected="true"] {
        color: #000 !important;
        border-bottom: 2px solid #000 !important;
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
        st.write("")
        manual_text = st.text_area("Вставьте ссылки списком:", height=150, placeholder="https://...\nhttps://...", label_visibility="collapsed")
        if manual_text:
            links_final = [l.strip() for l in manual_text.split('\n') if l.strip()]
            
    with tab_excel:
        st.write("")
        uploaded_excel = st.file_uploader("Загрузите excel", type=["xlsx"], key="xls", label_visibility="collapsed")
        if uploaded_excel:
            try:
                df = pd.read_excel(uploaded_excel)
                cols = [c for c in df.columns if 'link' in str(c).lower() or 'ссылк' in str(c).lower()]
                if cols:
                    links_final = df[cols[0]].dropna().astype(str).tolist()
                    st.success(f"Найдено ссылок: {len(links_final)}")
            except Exception as e:
                st.error(f"Ошибка чтения файла: {e}")
    
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<div class="description" style="margin-bottom:10px;">Источник макета</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title" style="margin-top:0;">Загрузите дизайн</div>', unsafe_allow_html=True)
    
    uploaded_pdf = st.file_uploader("PDF макет", type=["pdf"], key="pdf", label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)

    # КНОПКИ
    if "zip_result" not in st.session_state:
        st.session_state.zip_result = None
        st.session_state.zip_name = ""

    if st.session_state.zip_result is None:
        # КНОПКА ГЕНЕРАЦИИ
        if st.button("Генерация"):
            if not uploaded_pdf:
                st.toast("Нужен PDF макет!", icon="⚠️")
            elif not links_final:
                st.toast("Нужны ссылки!", icon="⚠️")
            else:
                with st.spinner("Работаем..."):
                    p_n = partner_name if partner_name else "partner"
                    s_n = size_name if size_name else "size"
                    res = process_files(uploaded_pdf, links_final, p_n, s_n, x_mm, y_mm, size_mm)
                    st.session_state.zip_result = res
                    st.session_state.zip_name = f"{p_n}_{s_n}.zip"
                    st.rerun()
    else:
        # КНОПКА СКАЧИВАНИЯ
        st.download_button(
            label="Скачать архив",
            data=st.session_state.zip_result,
            file_name=st.session_state.zip_name,
            mime="application/zip"
        )
        if st.button("Начать заново", type="secondary"):
            st.session_state.zip_result = None
            st.rerun()