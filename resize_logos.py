from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import os

BRANDS_DIR = os.path.join("static", "img", "brands")
CANVAS = 128
PADDING = 4     # 캔버스 여백
MIN_SHORT = 40  # 짧은 쪽 최소 픽셀 (얇은 로고 보정)

def resize_logo(path):
    img = Image.open(path).convert("RGBA")

    # 투명 여백 제거
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    max_size = CANVAS - PADDING * 2  # 60
    w, h = img.size

    # 정상 비율: max_size에 맞춤 / 얇은 로고: 짧은 쪽이 MIN_SHORT 이상 되도록 스케일업
    ratio_fit = max_size / max(w, h)
    ratio_min = MIN_SHORT / min(w, h) if min(w, h) > 0 else ratio_fit
    ratio = max(ratio_fit, ratio_min)

    new_w = min(int(w * ratio), CANVAS)
    new_h = min(int(h * ratio), CANVAS)
    img = img.resize((new_w, new_h), Image.LANCZOS)

    # 64x64 투명 캔버스에 정중앙 배치
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    x = (CANVAS - img.width) // 2
    y = (CANVAS - img.height) // 2
    canvas.paste(img, (x, y), img)

    canvas.save(path, "PNG")
    print(f"  {os.path.basename(path):30s} → {img.width}x{img.height} → {CANVAS}x{CANVAS}")

files = [f for f in os.listdir(BRANDS_DIR) if f.lower().endswith(".png")]
print(f"총 {len(files)}개 로고 처리 중...\n")
for f in sorted(files):
    resize_logo(os.path.join(BRANDS_DIR, f))
print("\n완료!")
