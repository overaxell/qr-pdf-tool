import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import io
import zipfile
import requests
import qrcode
from PIL import Image

# --- КОНФИГУРАЦИЯ СТРАНИЦЫ ---
st.set_page_config(
    page_title="Кюарыч",
    page_icon="▪️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS СТИЛИ ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;800&display=swap" rel="stylesheet">
<style>
    /* ГЛОБАЛЬНЫЕ НАСТРОЙКИ */
    .stApp {background-color: #FFFFFF !important;}
    html, body, p, div, span, h1, h2, h3, h4, h5, h6, button, input, textarea, label, li, a {
        font-family: 'Manrope', sans-serif !important;
        color: #000000 !important;
    }
    
    /* ТИПОГРАФИКА */
    .big-title {
        font-size: 96px !important; 
        font-weight: 800 !important; 
        line-height: 1.0 !important; 
        letter-spacing: -3px !important;
        margin-bottom: 25px !important;
        display: block !important;
    }
    .description {
        font-size: 18px !important; 
        color: #666 !important; 
        line-height: 1.5 !important;
        margin-bottom: 20px !important;
        max-width: 650px;
        display: block !important;
    }
    .section-title {font-size: 32px !important; font-weight: 600 !important; margin-top: 30px !important;}
    
    /* СКРЫВАЕМ ЛИШНЕЕ */
    header, footer, #MainMenu {visibility: hidden;}
    .block-container {padding-top: 2rem !important; padding-bottom: 5rem !important;}

    /* ИНПУТЫ */
    div[data-baseweb="input"] > div {border-radius: 14px !important; border: 1px solid #E0E0E0 !important; background-color: #FFFFFF !important;}
    div[data-baseweb="input"] > div:focus-within {border-color: #000 !important;}
    
    /* КНОПКИ */
    div.stButton, div.stDownloadButton {width: 100% !important;}
    div.stButton > button, div.stDownloadButton > button {
        width: 100% !important; background-color: #000000 !important; color: #FFFFFF !important;
        border-radius: 14px !important; padding: 18px 10px !important; font-size: 18px !important; font-weight: 500 !important; border: none !important;
        display: flex !important; justify-content: center !important;
        white-space: nowrap !important;
    }
    div.stButton > button:hover, div.stDownloadButton > button:hover {background-color: #333333 !important;}
    div.stButton > button p, div.stDownloadButton > button p {color: #FFFFFF !important;}
    
    /* ТАБЫ */
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
    if not link or str(link).lower() == 'nan':
        return None
    link = str(link).strip()
    
    # 1. Попытка скачать (таймаут 3 сек)
    try:
        download_url = link
        if not download_url.startswith('http'):
            download_url = 'https://' + download_url
        
        resp = requests.get(download_url, headers=HEADERS, timeout=3)
        if resp.status_code == 200:
            pil_img = Image.open(io.BytesIO(resp.content))
            img_byte_arr = io.BytesIO()
            pil_img.save(img_byte_arr, format="PNG")
            return img_byte_arr.getvalue()
    except:
        pass 
    
    # 2. Генерация
    try:
        qr = qrcode.QRCode(box_size=10, border=0)
        qr.add_data(link)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="PNG")
        return img_byte_arr.getvalue()
    except:
        return None

def process_files(pdf_file, links, p_name, p_size, auto_center, x_mm, y_mm, size_mm):
    zip_buffer = io.BytesIO()
    pdf_file.seek(0)
    pdf_bytes = pdf_file.read()
    success_count = 0
    errors_log = []
    total_links = len(links)
    
    my_bar = st.progress(0, text="Начинаем обработку...")
    
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        for i, url in enumerate(links, start=1):
            my_bar.progress(i / total_links, text=f"Обработка {i} из {total_links}")
            try:
                filename = f"{p_name}_{p_size}_{i:02d}.pdf"
                qr_bytes = get_or_generate_qr_image(url)
                
                if qr_bytes:
                    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                        page = doc[0]
                        if auto_center:
                            page_w = page.rect.width
                            page_h = page.rect.height
                            qr_size_pt = page_w / 3
                            x_pt = (page_w - qr_size_pt) / 2
                            y_pt = (page_h - qr_size_pt) / 2
                        else:
                            x_pt = mm_to_pt(x_mm)
                            y_pt = mm_to_pt(y_mm)
                            qr_size_pt = mm_to_pt(size_mm)
                        
                        rect = fitz.Rect(x_pt, y_pt, x_pt + qr_size_pt, y_pt + qr_size_pt)
                        page.insert_image(rect, stream=qr_bytes)
                        zf.writestr(filename, doc.convert_to_pdf())
                        success_count += 1
                else:
                    errors_log.append(f"Ссылка №{i}: Не удалось сгенерировать QR")
            except Exception as e:
                errors_log.append(f"Ссылка №{i}: Ошибка {e}")
                
    my_bar.empty()
    zip_buffer.seek(0)
    
    if success_count == 0: 
        return None, errors_log
    return zip_buffer, errors_log

# --- ВЕРСТКА ---
col_left, col_spacer, col_right = st.columns([1.3, 0.1, 1])

# === ЛЕВАЯ КОЛОНКА ===
with col_left:
    st.markdown("""
    <div>
        <div class="big-title">Кюарыч</div>
        <div class="description">
            Удобный помощник для маркетинг-команды. Загружайте макет,
            вставляйте ссылки — а я красиво и точно расставлю QR-коды сам.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">Как назвать файл?</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: partner_name = st.text_input("Имя партнера", placeholder="Partner")
    with c2: size_name = st.text_input("Размер файла", placeholder="7x7")
        
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Куда вставить QR?</div>', unsafe_allow_html=True)
    
    auto_pos = st.toggle("Авто-центрирование (1/3 ширины)", value=True)
    if not auto_pos:
        g1, g2, g3 = st.columns(3)
        with g1: x_mm = st.number_input("Отступ слева", value=20.0)
        with g2: y_mm = st.number_input("Отступ сверху", value=20.0)
        with g3: size_mm = st.number_input("Размер кюара", value=20.0)
    else:
        st.info("QR встанет ровно по центру.")
        x_mm, y_mm, size_mm = 0, 0, 0

# === ПРАВАЯ КОЛОНКА ===
with col_right:
    st.write("")
    st.write("")
    st.markdown('<div class="description" style="margin-bottom:0;">Источник ссылок QR</div>', unsafe_allow_html=True)
    
    if 'links_final' not in st.session_state:
        st.session_state.links_final = []

    tab_manual, tab_excel = st.tabs(["Вручную", "Из excel"])
    
    with tab_manual:
        st.write("")
        manual_text = st.text_area("Ссылки списком", height=150, label_visibility="collapsed")
        if manual_text: 
            st.session_state.links_final = [l.strip() for l in manual_text.split('\n') if l.strip()]
    
    with tab_excel:
        st.write("")
        uploaded_excel = st.file_uploader("Excel", type=["xlsx"], key="xls", label_visibility="collapsed")
        if uploaded_excel:
            try:
                df = pd.read_excel(uploaded_excel)
                target_col = None
                
                # 1. Попытка найти по названию
                possible_names = ['link', 'ссылка', 'ссылки', 'url', 'сайт', 'web']
                for col in df.columns:
                    if any(name in str(col).lower() for name in possible_names):
                        target_col = col
                        break
                
                # 2. Если не нашли по имени - ищем по содержимому (эвристика)
                if not target_col:
                    for col in df.columns:
                        # Берем первые 5 непустых значений
                        sample = df[col].dropna().astype(str).head(5).tolist()
                        if not sample: continue
                        # Если хотя бы одно начинается на http или www - берем
                        if any(val.strip().lower().startswith(('http', 'www')) for val in sample):
                            target_col = col
                            break
                
                if target_col:
                    links = df[target_col].dropna().astype(str).tolist()
                    st.session_state.links_final = links
                    st.success(f"✅ Найдено ссылок: {len(links)}")
                else: 
                    st.error("Не нашел колонку с ссылками (искал 'link' или http...)")
            except Exception as e: 
                st.error(f"Ошибка файла: {e}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="description" style="margin-bottom:10px;">Источник макета</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title" style="margin-top:0;">Загрузите дизайн</div>', unsafe_allow_html=True)
    uploaded_pdf = st.file_uploader("PDF", type=["pdf"], key="pdf", label_visibility="collapsed")
    st.markdown("<br>", unsafe_allow_html=True)

    # КНОПКИ
    if "zip_result" not in st.session_state:
        st.session_state.zip_result = None

    if st.session_state.zip_result is None:
        if st.button("Генерация"):
            if not uploaded_pdf: st.toast("Нужен PDF!", icon="⚠️")
            elif not st.session_state.links_final: st.toast("Нужны ссылки!", icon="⚠️")
            else:
                p_n = partner_name if partner_name else "partner"
                s_n = size_name if size_name else "size"
                res, errs = process_files(uploaded_pdf, st.session_state.links_final, p_n, s_n, auto_pos, x_mm, y_mm, size_mm)
                
                if res:
                    st.session_state.zip_result = res
                    st.session_state.zip_name = f"{p_n}_{s_n}.zip"
                    st.rerun()
                else:
                    st.error("Ошибка. Проверьте ссылки.")
                    if errs:
                        with st.expander("Ошибки"):
                            for e in errs: st.write(e)
    else:
        btn_col1, btn_col2 = st.columns(2, gap="small")
        with btn_col1:
            st.download_button("Скачать архив", st.session_state.zip_result, st.session_state.zip_name, "application/zip")
        with btn_col2:
            if st.button("Начать заново", type="secondary"):
                st.session_state.zip_result = None
                st.session_state.links_final = []
                st.rerun()
