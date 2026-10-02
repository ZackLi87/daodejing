"""绘图基础：字体、宣纸底、文字图块、印章、水墨显字与合成。"""
from functools import lru_cache
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .config import FONT_DIR, FONTS, H, INK, PAPER, RED, W

PUNCT = set("，。、；：？！…—“”‘’《》（）「」·")
CLAUSE_END = set("，。、；：？！")


# ---------- 缓动与时间 ----------

def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp(x)
    return 3 * x * x - 2 * x * x * x


def fade(t, t0, dur=0.5):
    """t0 起在 dur 秒内由 0 升至 1。t0 为 None 时恒为 0。"""
    if t0 is None:
        return 0.0
    return ease_out((t - t0) / dur) if dur > 0 else float(t >= t0)


# ---------- 字体与文字 ----------

@lru_cache(maxsize=None)
def font(name, size):
    return ImageFont.truetype(str(FONT_DIR / FONTS[name]), size)


@lru_cache(maxsize=4096)
def text(s, name, size, fill=INK, spacing=0, alpha=255):
    """单行横排文字图块。高度固定为字号的 1.35 倍，文字顶端对齐，便于排版。"""
    f = font(name, size)
    widths = [f.getlength(ch) for ch in s]
    w = int(math.ceil(sum(widths) + spacing * max(len(s) - 1, 0))) + 8
    h = int(size * 1.35) + 8
    im = Image.new("RGBA", (max(w, 1), h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    base = h / 2 - _ink_mid(name, size)
    x = 4
    for ch, cw in zip(s, widths):
        d.text((x, base), ch, font=f, fill=fill + (alpha,), anchor="ls")
        x += cw + spacing
    return im


@lru_cache(maxsize=None)
def _ink_mid(name, size):
    """汉字墨迹中线相对基线的偏移（负值，向上）。"""
    _, top, _, bottom = font(name, size).getbbox("中", anchor="ls")
    return (top + bottom) / 2


def text_width(s, name, size, spacing=0):
    f = font(name, size)
    return sum(f.getlength(ch) for ch in s) + spacing * max(len(s) - 1, 0)


@lru_cache(maxsize=4096)
def glyph(ch, name, size, fill=INK):
    """单字方块图块（size×size，字形居中），用于竖排与逐字显现。"""
    f = font(name, size)
    pad = int(size * 0.2)
    im = Image.new("RGBA", (size + 2 * pad, size + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if ch in "，。、；：":
        # 竖排标点置于字格右上，紧贴上一字
        d.text((pad + size * 0.55, pad + size * 0.08), ch, font=f, fill=fill + (255,), anchor="ls")
    else:
        d.text((pad + size / 2, pad + size / 2 - _ink_mid(name, size)), ch, font=f, fill=fill + (255,), anchor="ms")
    return im


def vlayout(s, size, step=1.12, punct_step=0.55):
    """竖排：返回 [(字, y 偏移)]。标点占半格。"""
    out, y = [], 0.0
    for ch in s:
        out.append((ch, y))
        y += size * (punct_step if ch in PUNCT else step)
    return out, y


# ---------- 合成 ----------

def with_alpha(im, a):
    if a >= 0.999:
        return im
    if a <= 0.001:
        return None
    out = im.copy()
    out.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    return out


def blit(canvas, im, x, y, a=1.0, anchor="lt", scale=1.0):
    """把图块按不透明度 a 叠到画布上。anchor：lt 左上 / mt 中上 / mm 居中 / rt 右上 / lm 左中。"""
    if im is None or a <= 0.001:
        return
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    im = with_alpha(im, a)
    if im is None:
        return
    w, h = im.size
    if anchor[0] == "m":
        x -= w / 2
    elif anchor[0] == "r":
        x -= w
    if anchor[1] == "m":
        y -= h / 2
    elif anchor[1] == "b":
        y -= h
    x, y = int(round(x)), int(round(y))
    # 裁去画布外部分
    sx, sy = max(0, -x), max(0, -y)
    ex, ey = min(w, canvas.width - x), min(h, canvas.height - y)
    if ex <= sx or ey <= sy:
        return
    if (sx, sy, ex, ey) != (0, 0, w, h):
        im = im.crop((sx, sy, ex, ey))
    canvas.alpha_composite(im, (x + sx, y + sy))


# ---------- 水墨显字 ----------

@lru_cache(maxsize=4096)
def _reveal_field(w, h, seed):
    """显字用的距离场：自左上向右下晕开，叠加噪声使边缘不规则。"""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w * (0.35 + 0.1 * rng.random()), h * (0.3 + 0.1 * rng.random())
    d = np.hypot((xx - cx) / w, (yy - cy) / h)
    small = rng.random((max(2, h // 12), max(2, w // 12))).astype(np.float32)
    noise = np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC),
                       dtype=np.float32) / 255
    f = d / d.max() * 0.8 + noise * 0.35
    return (f - f.min()) / (f.max() - f.min())


def ink_reveal(im, p, seed=0, soft=0.25):
    """p 由 0 到 1：墨迹由一点向四周晕开，直至字形完整。"""
    if p >= 1:
        return im
    if p <= 0:
        return None
    f = _reveal_field(im.width, im.height, seed)
    m = np.clip((p * (1 + soft) - f) / soft, 0, 1)
    a = np.asarray(im.getchannel("A"), dtype=np.float32) * m
    out = im.copy()
    out.putalpha(Image.fromarray(a.astype(np.uint8)))
    return out


# ---------- 宣纸底 ----------

def make_paper(seed=7, w=W, h=H):
    W, H = w, h  # noqa: N806  （封面等其他画幅）
    rng = np.random.default_rng(seed)
    base = np.array(PAPER, np.float32)

    def smooth(scale, amp):
        small = rng.normal(0, 1, (H // scale + 2, W // scale + 2)).astype(np.float32)
        img = Image.fromarray(((small - small.min()) / (np.ptp(small) + 1e-6) * 255).astype(np.uint8))
        arr = np.asarray(img.resize((W + scale * 2, H + scale * 2), Image.BICUBIC), np.float32)
        arr = arr[scale:scale + H, scale:scale + W] / 255 - 0.5
        return arr * amp

    mott = smooth(90, 10) + smooth(24, 4)
    grain = rng.normal(0, 1.6, (H, W)).astype(np.float32)
    rgb = base[None, None, :] + (mott + grain)[..., None] * np.array([1.0, 1.0, 1.15], np.float32)

    # 纤维
    fib = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(fib)
    for _ in range(int(1400 * W * H / (1920 * 1080))):
        x, y = rng.random() * W, rng.random() * H
        ang = rng.random() * math.pi
        ln = 6 + rng.random() * 26
        pts = []
        for k in range(5):
            s = k / 4 * ln
            pts.append((x + math.cos(ang) * s + rng.normal(0, 0.8), y + math.sin(ang) * s + rng.normal(0, 0.8)))
        d.line(pts, fill=int(40 + rng.random() * 60), width=1)
    fib = np.asarray(fib.filter(ImageFilter.GaussianBlur(0.6)), np.float32) / 255
    rgb -= fib[..., None] * np.array([10, 10, 8], np.float32)

    # 暗角
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dd = ((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2
    rgb *= (1 - 0.085 * dd)[..., None]
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert("RGBA")


# ---------- 印章 ----------

@lru_cache(maxsize=64)
def seal(chars, size, color=RED, seed=3, kind="yin"):
    """方印。kind=yin 为白文（朱底白字），yang 为朱文（红字红框）。
    chars 按印章习惯自右向左、自上而下排列；1、2、4 字自动排布。"""
    rng = np.random.default_rng(seed)
    n = len(chars)
    s = size
    sc = 4  # 超采样
    big = Image.new("L", (s * sc, s * sc), 0)
    d = ImageDraw.Draw(big)
    m = int(s * sc * 0.06)
    if kind == "yin":
        d.rounded_rectangle((m, m, s * sc - m, s * sc - m), radius=s * sc * 0.06, fill=255)
        ink, bg = 0, 255
    else:
        d.rounded_rectangle((m, m, s * sc - m, s * sc - m), radius=s * sc * 0.06, outline=255,
                            width=int(s * sc * 0.07))
        ink, bg = 255, 0
    inner = s * sc - 2 * m
    if n == 1:
        cells = [(s * sc / 2, s * sc / 2, inner * 0.78)]
    elif n == 2:
        cells = [(s * sc / 2, m + inner * 0.27, inner * 0.46), (s * sc / 2, m + inner * 0.73, inner * 0.46)]
    elif n == 3:
        cells = [(m + inner * 0.73, s * sc / 2, inner * 0.80), (m + inner * 0.27, m + inner * 0.27, inner * 0.42),
                 (m + inner * 0.27, m + inner * 0.73, inner * 0.42)]
    else:
        q = inner * 0.44
        cells = [(m + inner * 0.73, m + inner * 0.27, q), (m + inner * 0.73, m + inner * 0.73, q),
                 (m + inner * 0.27, m + inner * 0.27, q), (m + inner * 0.27, m + inner * 0.73, q)]
    for ch, (cx, cy, fs) in zip(chars, cells):
        f = font("serif_bk", int(fs))
        if n == 3 and ch == chars[0]:
            # 三字印：首字占右侧整列，纵向拉长
            tmp = Image.new("L", (int(fs), int(fs)), 0)
            ImageDraw.Draw(tmp).text((fs / 2, fs / 2), ch, font=font("serif_bk", int(fs * 0.55)), fill=255, anchor="mm")
            tmp = tmp.resize((int(fs * 0.55), int(fs)), Image.LANCZOS)
            big.paste(ink, (int(cx - fs * 0.275), int(cy - fs / 2)), tmp)
            continue
        d.text((cx, cy), ch, font=f, fill=ink, anchor="mm")
    # 斑驳：随机侵蚀
    arr = np.asarray(big, np.float32) / 255
    noise = rng.random((s // 2 + 1, s // 2 + 1)).astype(np.float32)
    noise = np.asarray(Image.fromarray((noise * 255).astype(np.uint8)).resize((s * sc, s * sc), Image.BICUBIC),
                       np.float32) / 255
    speck = rng.random(arr.shape).astype(np.float32)
    arr = np.where((noise > 0.80) & (speck > 0.5), arr * 0.25, arr)
    alpha = Image.fromarray((np.clip(arr, 0, 1) * 235).astype(np.uint8)).resize((s, s), Image.LANCZOS)
    im = Image.new("RGBA", (s, s), color + (0,))
    im.putalpha(alpha)
    return im


# ---------- 其他元件 ----------

def brush_line(w, thick=4, color=INK, seed=1, taper=True):
    """一笔横向墨线（两端收锋）。"""
    rng = np.random.default_rng(seed)
    sc = 3
    im = Image.new("L", (w * sc, (thick * 3) * sc), 0)
    d = ImageDraw.Draw(im)
    n = max(60, int(w * 2 / max(thick, 1)))
    cy = im.height / 2
    for i in range(n + 1):
        u = i / n
        x = u * w * sc
        r = thick * sc / 2 * (math.sin(math.pi * u) ** 0.35 if taper else 1) * (0.9 + 0.2 * rng.random())
        y = cy + math.sin(u * 3.1) * sc * 0.6
        d.ellipse((x - r, y - r, x + r, y + r), fill=255)
    a = im.resize((w, thick * 3), Image.LANCZOS)
    out = Image.new("RGBA", a.size, color + (0,))
    out.putalpha(a.point(lambda v: int(v * 0.92)))
    return out


def circle_mark(d, color=RED, width=3):
    """旁圈（圈点）：小空心圆。"""
    sc = 4
    im = Image.new("L", (d * sc, d * sc), 0)
    ImageDraw.Draw(im).ellipse((width * sc, width * sc, d * sc - width * sc, d * sc - width * sc),
                               outline=255, width=width * sc)
    a = im.resize((d, d), Image.LANCZOS)
    out = Image.new("RGBA", (d, d), color + (0,))
    out.putalpha(a)
    return out


def ring_box(w, h, color=RED, width=3):
    """竖长的圆角环（圈出连续数字）。"""
    sc = 4
    im = Image.new("L", (w * sc, h * sc), 0)
    ImageDraw.Draw(im).rounded_rectangle((width * sc, width * sc, w * sc - width * sc, h * sc - width * sc),
                                         radius=w * sc / 2 - width * sc, outline=255, width=width * sc)
    a = im.resize((w, h), Image.LANCZOS)
    out = Image.new("RGBA", (w, h), color + (0,))
    out.putalpha(a)
    return out


def rounded_box(w, h, fill=(0, 0, 0, 0), outline=None, width=2, radius=16):
    sc = 2
    im = Image.new("RGBA", (w * sc, h * sc), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((width, width, w * sc - width, h * sc - width), radius=radius * sc,
                                         fill=fill, outline=outline, width=width * sc)
    return im.resize((w, h), Image.LANCZOS)


def paragraph(lines, name, size, fill=INK, leading=1.6, spacing=0):
    """多行文字合成一个图块（左对齐）。"""
    sprites = [text(s, name, size, fill, spacing) for s in lines]
    w = max(s.width for s in sprites)
    h = int(size * leading * (len(lines) - 1) + sprites[-1].height)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for i, s in enumerate(sprites):
        im.alpha_composite(s, (0, int(i * size * leading)))
    return im


def rich(segments, size, spacing=0):
    """多样式单行：segments = [(文字, 字体名, 颜色), ...]，按同一基线拼接。"""
    parts = [text(s, fn, size, col, spacing) for s, fn, col in segments]
    w = sum(p.width - 8 for p in parts) + 8 + spacing * max(len(parts) - 1, 0)
    h = max(p.height for p in parts)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x = 0
    for p in parts:
        im.alpha_composite(p, (x, 0))
        x += p.width - 8 + spacing
    return im
