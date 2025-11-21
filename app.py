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
            x, y = stack.pop()   # <--- исправлено

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
