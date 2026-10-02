"""封面：横版 4:3（1440×1080）与竖版 3:4（1080×1440）。

    python3 -m dao.cover ep01

本期参数取自 episodes/epNN/script.py 中的 COVER：
    title     名句（竖排大字）
    question  设问，分两列/两行
    info      出处与提要
    seal      名句旁的印章文字
    art       可选，返回本期插图（RGBA）的函数
"""
import argparse
import importlib

from PIL import Image

from . import config as C
from . import gfx
from .config import INK, INK2, RED
from .gfx import blit, glyph, seal, text
from .scenes import Ripples


def _header(cv, cx, y, num, series="道德经细读", anchor="mm"):
    """印章『细读』+『道德经细读 · NN』，整体以 (cx, y) 为中心或左端。"""
    s = seal("细读", 70, seed=9)
    lab = gfx.rich([(series + "  ·  ", "serif_sb", INK2), (num, "serif_bk", RED)], 46)
    w = s.width + 22 + lab.width
    x0 = cx - w / 2 if anchor == "mm" else cx
    blit(cv, s, x0, y, anchor="lm")
    blit(cv, lab, x0 + s.width + 22, y, anchor="lm")


def _vtext(cv, s, x, y0, size, color, step=1.06, name="kai_m"):
    lay, h = gfx.vlayout(s, size, step=step, punct_step=0.75)
    for ch, dy in lay:
        blit(cv, glyph(ch, name, size, color), x, y0 + dy + size / 2, anchor="mm")
    return h


def horizontal(cov, num):
    w, h = 1440, 1080
    cv = gfx.make_paper(seed=11, w=w, h=h)
    # 插图：左下角，淡墨
    if cov.get("art"):
        art = cov["art"]()
        art = art.resize((int(art.width * 0.78), int(art.height * 0.78)), Image.LANCZOS)
        blit(cv, art, 60, h - art.height + 70, 0.92)
    # 名句：右侧竖排大字
    size, x, y0 = 196, 1170, 104
    Ripples(470, 96, count=3, period=7.0, alpha=0.30).draw(cv, 2.6, x, y0 + 4 * size * 1.06 + 40)
    th = _vtext(cv, cov["title"], x, y0, size, INK)
    blit(cv, seal(cov.get("seal", "老子"), 82, seed=5), x - 150, y0 + th - 82 + 8)
    # 左侧：系列名、设问、提要
    _header(cv, 104, 128, num, anchor="lm")
    for i, line in enumerate(cov["question"]):
        blit(cv, text(line, "kai_m", 116, RED, spacing=4), 96, 250 + i * 150)
    blit(cv, gfx.brush_line(120, 3, RED, seed=3), 104, 584)
    blit(cv, text(cov["info"], "serif", 34, INK2, spacing=2), 104, 612)
    return cv


def vertical(cov, num):
    w, h = 1080, 1440
    cv = gfx.make_paper(seed=12, w=w, h=h)
    if cov.get("art"):
        art = cov["art"]()
        art = art.resize((int(art.width * 0.66), int(art.height * 0.66)), Image.LANCZOS)
        blit(cv, art, 40, h - art.height - 150, 0.92)
    _header(cv, w / 2, 112, num)
    # 名句：右列竖排大字；设问：左侧两列朱色竖排
    size, x, y0 = 214, 745, 225
    Ripples(400, 86, count=3, period=7.0, alpha=0.30).draw(cv, 2.6, x, y0 + 4 * size * 1.06 + 36)
    th = _vtext(cv, cov["title"], x, y0, size, INK)
    blit(cv, seal(cov.get("seal", "老子"), 80, seed=5), x - 160, y0 + th - 80 + 8)
    for i, line in enumerate(cov["question"]):
        _vtext(cv, line, 440 - i * 140, 300, 108, RED, step=1.08)
    blit(cv, text(cov["info"], "serif", 36, INK2, spacing=2), w / 2, h - 92, anchor="mm")
    return cv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep")
    a = ap.parse_args()
    mod = importlib.import_module(f"episodes.{a.ep}.script")
    cov, num = mod.COVER, mod.META["num"]
    out = C.OUTPUT / a.ep
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in [("封面_横版_4x3", horizontal), ("封面_竖版_3x4", vertical)]:
        p = out / f"{name}.png"
        fn(cov, num).convert("RGB").save(p, optimize=True)
        print(p)


if __name__ == "__main__":
    main()
