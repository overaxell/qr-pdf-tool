import numpy as np

def detect_white_rectangles_in_pdf(pdf_bytes, white_threshold=245, min_area_ratio=0.01, max_area_ratio=0.5):
    """
    Поиск почти белых прямоугольников БЕЗ OpenCV.
    Работает в Streamlit Cloud.
    """

    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        page = doc[0]
        page_w_pt = page.rect.width
        page_h_pt = page.rect.height

        pix = page.get_pixmap(alpha=False)
        img_w, img_h = pix.width, pix.height
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(img_h, img_w, 3)

    # переводим в яркость
    gray = img.mean(axis=2)

    # массив белых пикселей
    mask = gray > white_threshold

    # структура типа connected components
    visited = np.zeros_like(mask, dtype=bool)
    rects = []

    def flood_fill(x, y):
        stack = [(x, y)]
        min_x = max_x = x
        min_y = max_y = y

        visited[y, x] = True

        while stack:
            px, py = stack.pop()

            if px < min_x: min_x = px
            if px > max_x: max_x = px
            if py < min_y: min_y = py
            if py > max_y: max_y = py

            for nx, ny in [(px+1,py), (px-1,py), (px,py+1), (px,py-1)]:
                if 0 <= nx < img_w and 0 <= ny < img_h:
                    if mask[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        stack.append((nx, ny))

        return min_x, min_y, max_x, max_y

    # ищем connected components на маске белых пикселей
    for y in range(img_h):
        for x in range(img_w):
            if mask[y, x] and not visited[y, x]:
                x1, y1, x2, y2 = flood_fill(x, y)

                w = x2 - x1 + 1
                h = y2 - y1 + 1
                area = w * h
                area_ratio = area / (img_w * img_h)

                if area_ratio < min_area_ratio or area_ratio > max_area_ratio:
                    continue

                # фильтруем почти-квадраты
                aspect = w / h
                if aspect < 0.8 or aspect > 1.25:
                    continue

                # конвертация в PDF points
                x_pt = x1 * page_w_pt / img_w
                y_pt = y1 * page_h_pt / img_h
                w_pt = w * page_w_pt / img_w
                h_pt = h * page_h_pt / img_h

                rects.append((x_pt, y_pt, w_pt, h_pt))

    # сортировка по площади
    rects.sort(key=lambda r: r[2]*r[3], reverse=True)
    return rects
