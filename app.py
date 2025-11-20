import streamlit as st
import pandas as pd  # можно оставить, если пригодится дальше
import fitz  # PyMuPDF
import io
import zipfile
import requests
import qrcode
from PIL import Image
from openpyxl import load_workbook  # для корректного чтения гиперссылок

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
    div[data-baseweb="input"] > div {
        border-radius: 14px !important;
        border: 1px solid #E0E0E0 !important;
        background-color: #FFFFFF !important;
    }
    div[data-baseweb="input"] > div:focus-within {border-color: #000 !important;}
    
    /* КНОПКИ */
    div.stButton, div.stDownloadButton {
        width: 100% !important;
        display: block !important;
    }
    div.stButton > button, div.stDownloadButton > button {
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


def mm_to_pt(mm_val: float) -> float:
    return mm_val * MM_TO_POINT


def get_or_generate_qr_image(link: str):
    if not link or str(link).lower() == 'nan':
        return None
    link = str(link).strip()
    if not link:
        return None

    # 1) Пытаемся скачать как картинку
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
    except Exception:
        pass

    # 2) Если это не картинка — генерируем QR по самой ссылке
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


def process_files(pdf_file, links, p_name, p_size, auto_center, x_mm, y_mm, size_mm):
    zip_buffer = io.BytesIO()
    pdf_file.seek(0)
    pdf_bytes = pdf_file.read()
    success_count = 0    # сколько реально удалось собрать
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
                    errors_log.append(f"Ссылка №{i}: Пустые данные или сбой при создании QR")
            except Exception as e:
                errors_log.append(f"Ссылка №{i}: Ошибка {e}")

    my_bar.empty()
    zip_buffer.seek(0)

    if success_count == 0:
        return None, errors_log
    return zip_buffer, errors_log


def extract_links_from_excel(file) -> list:
    """
    Чтение Excel с учётом:
    - значений ячеек
    - реальных гиперссылок (cell.hyperlink.target)
    Возвращает список ссылок из наиболее "похожей" на ссылки колонки.
    """
    file_bytes = file.read()
    bio = io.BytesIO(file_bytes)

    wb = load_workbook(bio, data_only=True)
    ws = wb.active

    all_columns = []
    max_col = ws.max_column
    max_row = ws.max_row

    for col_idx in range(1, max_col + 1):
        col_values = []
        for row_idx in range(1, max_row + 1):
            cell = ws.cell(row=row_idx, column=col_idx)

            text = ""
            if cell.hyperlink and cell.hyperlink.target:
                text = str(cell.hyperlink.target).strip()
            else:
                val = cell.value
                if val is None:
                    text = ""
                else:
                    text = str(val).strip()

            col_values.append(text)
        all_columns.append(col_values)

    import re

    def is_url_like(s: str) -> bool:
        s = s.strip()
        if len(s) <= 5:
            return False
        return bool(re.search(r'http|www|\.[a-zA-Z]{2,}', s))

    best_idx = None
    best_score = 0

    for idx, col_vals in enumerate(all_columns):
        if not col_vals:
            continue
        score = sum(1 for v in col_vals if is_url_like(v))
        if score > best_score:
            best_score = score
            best_idx = idx

    if best_idx is None or best_score == 0:
        return []

    col_vals = all_columns[best_idx]

    if col_vals and not is_url_like(col_vals[0]):
        data_vals = col_vals[1:]
    else:
        data_vals = col_vals

    clean_links = [
        v.strip()
        for v in data_vals
        if v
        and v.strip()
        and v.strip().lower() not in ("nan", "none")
    ]

    return clean_links


# --- ВЕРСТКА ---
col_left, col_spacer, col_right = st.columns([1.2, 0.1, 1.1])

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
    with c1:
        partner_name = st.text_input("Имя партнера", placeholder="Partner")
    with c2:
        size_name = st.text_input("Размер файла", placeholder="7x7")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Куда вставить QR?</div>', unsafe_allow_html=True)

    auto_pos = st.toggle("Авто-центрирование (1/3 ширины)", value=True)
    if not auto_pos:
        g1, g2, g3 = st.columns(3)
        with g1:
            x_mm = st.number_input("Отступ слева (мм)", value=20.0)
        with g2:
            y_mm = st.number_input("Отступ сверху (мм)", value=20.0)
        with g3:
            size_mm = st.number_input("Размер QR (мм)", value=20.0)
    else:
        st.info("QR встанет ровно по центру.")
        x_mm, y_mm, size_mm = 0.0, 0.0, 0.0

# === ПРАВАЯ КОЛОНКА ===
with col_right:
    st.write("")
    st.write("")
    st.markdown('<div class="description" style="margin-bottom:0;">Источник ссылок QR</div>', unsafe_allow_html=True)

    if 'links_final' not in st.session_state:
        st.session_state.links_final = []

    tab_manual, tab_excel = st.tabs(["Вручную", "Из excel"])

    # --- ВКЛАДКА "ВРУЧНУЮ" ---
    with tab_manual:
        st.write("")
        manual_text = st.text_area("Ссылки списком", height=150, label_visibility="collapsed")
        if manual_text:
            st.session_state.links_final = [
                l.strip()
                for l in manual_text.split("\n")
                if l.strip()
            ]

    # --- ВКЛАДКА "ИЗ EXCEL" ---
    with tab_excel:
        st.write("")
        uploaded_excel = st.file_uploader("Excel", type=["xlsx"], key="xls", label_visibility="collapsed")
        if uploaded_excel:
            try:
                uploaded_excel.seek(0)
                links_from_excel = extract_links_from_excel(uploaded_excel)

                st.session_state.links_final = links_from_excel

                if len(links_from_excel) > 0:
                    st.success(f"✅ Найдено ссылок: {len(links_from_excel)}")
                    # вместо экспандера — простой список, чтобы верстка не ломалась
                    st.markdown("**Найденные ссылки:**")
                    for i, link in enumerate(links_from_excel, start=1):
                        st.write(f"{i}. {link}")
                else:
                    st.warning("Не удалось найти ссылки в файле. Проверьте, что в колонке есть URL или гиперссылки.")
            except Exception as e:
                st.error(f"Ошибка файла: {e}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="description" style="margin-bottom:10px;">Источник макета</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title" style="margin-top:0;">Загрузите дизайн</div>', unsafe_allow_html=True)
    uploaded_pdf = st.file_uploader("PDF", type=["pdf"], key="pdf", label_visibility="collapsed")
    st.markdown("<br>", unsafe_allow_html=True)

    # --- КНОПКИ ГЕНЕРАЦИИ / СКАЧИВАНИЯ ---
    if "zip_result" not in st.session_state:
        st.session_state.zip_result = None
        st.session_state.zip_name = None

    if st.session_state.zip_result is None:
        if st.button("Генерация"):
            if not uploaded_pdf:
                st.toast("Нужен PDF!", icon="⚠️")
            elif not st.session_state.links_final:
                st.toast("Нужны ссылки!", icon="⚠️")
            else:
                p_n = partner_name if partner_name else "partner"
                s_n = size_name if size_name else "size"

                res, errs = process_files(
                    uploaded_pdf,
                    st.session_state.links_final,
                    p_n,
                    s_n,
                    auto_pos,
                    x_mm,
                    y_mm,
                    size_mm,
                )

                if res:
                    st.session_state.zip_result = res
                    st.session_state.zip_name = f"{p_n}_{s_n}.zip"
                    st.rerun()
                else:
                    st.error("Ошибка. Проверьте ссылки.")
                    if errs:
                        for e in errs:
                            st.write(e)
    else:
        btn_col1, btn_col2 = st.columns(2, gap="small")
        with btn_col1:
            st.download_button(
                "Скачать архив",
                st.session_state.zip_result,
                st.session_state.zip_name or "qrs.zip",
                "application/zip",
            )
        with btn_col2:
            if st.button("Начать заново", type="secondary"):
                st.session_state.zip_result = None
                st.session_state.zip_name = None
                st.session_state.links_final = []
                st.rerun()
