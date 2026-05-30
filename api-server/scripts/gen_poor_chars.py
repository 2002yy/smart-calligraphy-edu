"""程序化生成"难看"的汉字测试图片

通过多种手法模拟常见书法毛病：
  1. 重心偏左/偏右 (skew)
  2. 结构松散 (grid warp 拉伸)
  3. 笔画抖动 (elastic distortion)
  4. 笔画过细/过粗 (stroke variation)
  5. 倾斜不稳 (rotate + shear)
  6. 中宫松散 (radial warp)

用法: python gen_poor_chars.py
输出: test-images/poor/gen_*.png
"""

import os, random, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

random.seed(42)

OUT = Path(__file__).resolve().parents[1] / "test-images" / "poor"
OUT.mkdir(parents=True, exist_ok=True)

# 尝试找到中文字体（楷体优先）
FONT_CANDIDATES = [
    "C:/Windows/Fonts/simkai.ttf",       # 楷体
    "C:/Windows/Fonts/simsun.ttc",        # 宋体
    "C:/Windows/Fonts/msyh.ttc",          # 微软雅黑
    "C:/Windows/Fonts/simhei.ttf",        # 黑体
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttf",
]
FONT_PATH = None
for f in FONT_CANDIDATES:
    if Path(f).exists():
        FONT_PATH = f
        break

if not FONT_PATH:
    # fallback: use PIL default
    print("[WARN] 未找到中文字体，使用默认字体（可能无法显示中文）")
    FONT_PATH = None

def _load_font(size=120):
    if FONT_PATH:
        try:
            return ImageFont.truetype(FONT_PATH, size)
        except Exception:
            pass
    return ImageFont.load_default()

def render_char(char, font_size=140, img_size=(200, 200)):
    """在居中的位置渲染单个汉字，返回二值化图像"""
    img = Image.new("L", img_size, 255)
    draw = ImageDraw.Draw(img)
    font = _load_font(font_size)
    # 粗略居中
    bbox = draw.textbbox((0, 0), char, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (img_size[0] - tw) // 2 - bbox[0]
    y = (img_size[1] - th) // 2 - bbox[1]
    draw.text((x, y), char, fill=0, font=font)
    return img


# ============================================================
# 变形手法
# ============================================================

def elastic_distort(img, intensity=4, grid=6):
    """网格弹性变形 — 模拟笔画抖动"""
    w, h = img.size
    cols, rows = grid + 1, grid + 1
    cw, ch = w / grid, h / grid

    # 生成偏移网格
    x_offsets = [[random.uniform(-intensity, intensity) for _ in range(cols)] for _ in range(rows)]
    y_offsets = [[random.uniform(-intensity, intensity) for _ in range(cols)] for _ in range(rows)]

    # 插值生成新图
    dst = Image.new("L", (w, h), 255)
    for yi in range(h):
        for xi in range(w):
            gx = xi / cw
            gy = yi / ch
            gix, giy = int(gx), int(gy)
            fx, fy = gx - gix, gy - giy

            if gix >= grid or giy >= grid:
                dst.putpixel((xi, yi), img.getpixel((xi, yi)))
                continue

            ox = (1-fx)*(1-fy)*x_offsets[giy][gix] + fx*(1-fy)*x_offsets[giy][gix+1] \
               + (1-fx)*fy*x_offsets[giy+1][gix] + fx*fy*x_offsets[giy+1][gix+1]
            oy = (1-fx)*(1-fy)*y_offsets[giy][gix] + fx*(1-fy)*y_offsets[giy][gix+1] \
               + (1-fx)*fy*y_offsets[giy+1][gix] + fx*fy*y_offsets[giy+1][gix+1]

            sx = min(w-1, max(0, xi + int(ox)))
            sy = min(h-1, max(0, yi + int(oy)))
            dst.putpixel((xi, yi), img.getpixel((sx, sy)))

    return dst


def skew_center(img, direction="left", amount=0.15):
    """重心偏移 — 模拟左右不平衡"""
    w, h = img.size
    if direction == "left":
        matrix = (1, -amount, 0, 0, 1, 0)
    elif direction == "right":
        matrix = (1, amount, 0, 0, 1, 0)
    elif direction == "up":
        matrix = (1, 0, 0, -amount, 1, 0)
    else:
        matrix = (1, 0, 0, amount, 1, 0)
    return img.transform(img.size, Image.AFFINE, matrix, fillcolor=255)


def expand_middle(img, factor=0.12):
    """膨胀中部 — 模拟中宫松散"""
    w, h = img.size
    cx, cy = w // 2, h // 2
    dst = Image.new("L", (w, h), 255)
    for yi in range(h):
        for xi in range(w):
            dx = (xi - cx) / cx
            dy = (yi - cy) / cy
            # 向外拉伸
            sx = int(cx + dx * cx * (1 + factor * (abs(dx) + abs(dy)) / 2))
            sy = int(cy + dy * cy * (1 + factor * (abs(dx) + abs(dy)) / 2))
            sx = min(w-1, max(0, sx))
            sy = min(h-1, max(0, sy))
            dst.putpixel((xi, yi), img.getpixel((sx, sy)))
    return dst


def compress_middle(img, factor=0.15):
    """压缩中部 — 模拟笔画挤在一起"""
    w, h = img.size
    cx, cy = w // 2, h // 2
    dst = Image.new("L", (w, h), 255)
    for yi in range(h):
        for xi in range(w):
            dx = (xi - cx) / cx
            dy = (yi - cy) / cy
            sx = int(cx + dx * cx * (1 - factor))
            sy = int(cy + dy * cy * (1 - factor))
            sx = min(w-1, max(0, sx))
            sy = min(h-1, max(0, sy))
            dst.putpixel((xi, yi), img.getpixel((sx, sy)))
    return dst


def thin_and_shaky(img, erosion_iter=1):
    """笔画过细 + 噪点 — 模拟运笔生硬"""
    from PIL import ImageFilter
    # 腐蚀使笔画变细
    for _ in range(erosion_iter):
        img = img.filter(ImageFilter.MinFilter(3))
    # 加椒盐噪声
    pixels = img.load()
    w, h = img.size
    for _ in range(int(w * h * 0.02)):
        x, y = random.randint(0, w-1), random.randint(0, h-1)
        pixels[x, y] = 255 if random.random() > 0.5 else 0
    return img


def thick_and_blotchy(img, dilation_iter=1):
    """笔画过粗 + 墨渍 — 模拟运笔失控"""
    from PIL import ImageFilter
    for _ in range(dilation_iter):
        img = img.filter(ImageFilter.MaxFilter(3))
    # 随机墨渍
    pixels = img.load()
    w, h = img.size
    for _ in range(int(w * h * 0.015)):
        x, y = random.randint(0, w-1), random.randint(0, h-1)
        r = random.randint(2, 6)
        for dy in range(-r, r+1):
            for dx in range(-r, r+1):
                nx, ny = x+dx, y+dy
                if 0 <= nx < w and 0 <= ny < h and dx*dx+dy*dy <= r*r:
                    pixels[nx, ny] = 0
    return img


def rotate_unstable(img, angle=8):
    """小幅旋转 — 模拟字写歪"""
    return img.rotate(angle, fillcolor=255, expand=False)


def add_noise_border(img, noise_level=0.05):
    """加随机噪声点"""
    pixels = img.load()
    w, h = img.size
    for i in range(int(w * h * noise_level)):
        x, y = random.randint(0, w-1), random.randint(0, h-1)
        pixels[x, y] = random.choice([0, 50, 100, 200, 255])
    return img


# ============================================================
# 批量生成
# ============================================================

CHARS_TO_RENDER = ["永", "大", "中", "木", "人"]

def save(img, name):
    img.save(OUT / name)

print("正在生成\"难看\"的汉字测试图片...\n")

for char in CHARS_TO_RENDER:
    base = render_char(char, font_size=130, img_size=(200, 200))

    # 1. 重心偏左
    img = render_char(char)
    img = skew_center(img, "left", amount=0.18)
    img = elastic_distort(img, intensity=3, grid=5)
    save(img, f"gen_{char}_center_left.png")
    print(f"  [OK] gen_{char}_center_left.png  — 重心偏左")

    # 2. 结构松散
    img = render_char(char)
    img = expand_middle(img, factor=0.15)
    img = elastic_distort(img, intensity=2, grid=4)
    save(img, f"gen_{char}_loose.png")
    print(f"  [OK] gen_{char}_loose.png       — 结构松散")

    # 3. 笔画抖动
    img = render_char(char)
    img = elastic_distort(img, intensity=6, grid=8)
    save(img, f"gen_{char}_shaky.png")
    print(f"  [OK] gen_{char}_shaky.png       — 笔画抖动")

    # 4. 又细又歪
    img = render_char(char)
    img = thin_and_shaky(img, erosion_iter=2)
    img = rotate_unstable(img, angle=6)
    save(img, f"gen_{char}_thin_crooked.png")
    print(f"  [OK] gen_{char}_thin_crooked.png — 细弱歪斜")

    # 5. 又粗又糊
    img = render_char(char)
    img = thick_and_blotchy(img, dilation_iter=2)
    img = rotate_unstable(img, angle=-4)
    save(img, f"gen_{char}_thick_blotchy.png")
    print(f"  [OK] gen_{char}_thick_blotchy.png — 粗重墨渍")

    # 6. 严重倾斜 + 噪声
    img = render_char(char)
    img = skew_center(img, "left", amount=0.25)
    img = rotate_unstable(img, angle=12)
    img = add_noise_border(img, 0.08)
    save(img, f"gen_{char}_tilted_noisy.png")
    print(f"  [OK] gen_{char}_tilted_noisy.png  — 严重倾斜+噪声")

print(f"\n生成完毕！共 {len(CHARS_TO_RENDER) * 6} 张丑字图片")
print(f"输出目录: {OUT}")
