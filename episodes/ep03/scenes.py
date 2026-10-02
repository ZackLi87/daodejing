"""第 03 期专用场景：雨落草木（不仁）、刍狗两说、天地如橐籥（守中）。"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from dao import gfx
from dao.config import INK, INK2, INK3, RED, WATER
from dao.gfx import blit, ease_out, fade, text
from dao.scenes import Scene, reveal_text, section


# ---------- 笔画工具 ----------

def _bez(p0, p1, p2, n=48):
    return [((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
             (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1]) for u in np.linspace(0, 1, n)]


def _stroke(d, pts, w0, w1, sc, fill=255, belly=0.0):
    """沿折线画一笔，宽度由 w0 渐变到 w1；belly>0 时中段加粗（叶片）。"""
    total = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    run = 0.0
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        seg = max(1, int(math.dist(pts[i], pts[i + 1])))
        for k in range(seg):
            u = (run + math.dist(pts[i], pts[i + 1]) * k / seg) / max(total, 1e-6)
            x, y = x0 + (x1 - x0) * k / seg, y0 + (y1 - y0) * k / seg
            r = (w0 + (w1 - w0) * u + belly * math.sin(math.pi * u)) / 2 * sc
            d.ellipse((x * sc - r, y * sc - r, x * sc + r, y * sc + r), fill=fill)
        run += math.dist(pts[i], pts[i + 1])


# ---------- 草木与雨 ----------

class Garden:
    """地面上高低不一的几株草木；rain(t) 返回均匀落下的雨丝。"""

    def __init__(self, w=760, h=600, ground=540, seed=5):
        self.w, self.h, self.ground = w, h, ground
        sc = 2
        ink = Image.new("L", (w * sc, h * sc), 0)
        red = Image.new("L", (w * sc, h * sc), 0)
        wash = Image.new("L", (w, h), 0)
        d, dr, dw = ImageDraw.Draw(ink), ImageDraw.Draw(red), ImageDraw.Draw(wash)
        rng = np.random.default_rng(seed)
        g = ground
        # 地面
        _stroke(d, [(10, g + 2), (w * 0.35, g - 3), (w * 0.7, g + 3), (w - 10, g)], 2.5, 3.5, sc)

        def tuft(x, hgt, n=6):
            for j in range(n):
                dx = (j - n / 2) * hgt * 0.16 + rng.normal(0, 3)
                _stroke(d, _bez((x + j * 2, g), (x + dx * 0.3, g - hgt * 0.6), (x + dx, g - hgt * (0.7 + 0.3 * rng.random()))),
                        3.2, 0.6, sc)

        def reed(x, hgt):
            pts = _bez((x, g), (x + 12, g - hgt * 0.5), (x - 6, g - hgt))
            _stroke(d, pts, 4, 1.5, sc)
            tx, ty = pts[-1]
            # 穗：自茎顶垂下的几道细笔
            for j in range(5):
                _stroke(d, _bez((tx, ty + j * 5), (tx + 18 + j * 3, ty - 4 + j * 6), (tx + 30 + j * 4, ty + 26 + j * 9)),
                        2.0, 0.5, sc)
            for j in range(2):
                y0 = g - hgt * (0.35 + 0.2 * j)
                s = 1 if j == 0 else -1
                _stroke(d, _bez((x + 4, y0), (x + s * 50, y0 - 40), (x + s * 95, y0 - 10)), 1.0, 0.6, sc, belly=7)

        def flower(x, hgt):
            pts = _bez((x, g), (x - 14, g - hgt * 0.55), (x + 6, g - hgt))
            _stroke(d, pts, 3.4, 2.0, sc)
            for s, yy in [(-1, 0.35), (1, 0.55)]:
                y0 = g - hgt * yy
                _stroke(d, _bez((x - 6 * s, y0), (x + s * 40, y0 - 34), (x + s * 74, y0 - 6)), 1.0, 0.6, sc, belly=9)
            cx, cy = pts[-1]
            for j in range(6):
                a = j / 6 * 2 * math.pi
                px, py = cx + math.cos(a) * 15, cy - 6 + math.sin(a) * 11
                dr.ellipse(((px - 11) * sc, (py - 8) * sc, (px + 11) * sc, (py + 8) * sc), fill=230)
            d.ellipse(((cx - 5) * sc, (cy - 11) * sc, (cx + 5) * sc, (cy - 1) * sc), fill=255)

        def sapling(x, hgt):
            trunk = _bez((x, g), (x + 10, g - hgt * 0.5), (x - 4, g - hgt * 0.72))
            _stroke(d, trunk, 9, 4, sc)
            for a, l, yy in [(-0.9, 70, 0.5), (0.7, 80, 0.58), (-0.4, 60, 0.68)]:
                y0 = g - hgt * yy
                _stroke(d, [(x + 3, y0), (x + 3 + math.sin(a) * l, y0 - math.cos(a) * l * 0.8)], 4, 1.5, sc)
            # 树冠：围绕枝梢的几团淡墨
            for bx, by in [(x - 45, g - hgt * 0.72), (x + 50, g - hgt * 0.78), (x + 4, g - hgt * 0.86)]:
                for _ in range(3):
                    ox, oy = rng.normal(0, 12), rng.normal(0, 8)
                    rr = 30 + rng.random() * 16
                    dw.ellipse((bx + ox - rr, by + oy - rr * 0.75, bx + ox + rr, by + oy + rr * 0.75), fill=58)

        def bamboo(x, hgt):
            nodes = 5
            for j in range(nodes):
                y0, y1 = g - hgt * j / nodes, g - hgt * (j + 1) / nodes + 6
                _stroke(d, [(x + j * 1.5, y0 - 3), (x + (j + 1) * 1.5, y1)], 6.5, 5.5, sc)
            for j, s in [(2, 1), (3, -1), (4, 1)]:
                y0 = g - hgt * j / nodes
                for k in range(3):
                    _stroke(d, _bez((x, y0), (x + s * (30 + 12 * k), y0 - 10 + k * 8), (x + s * (70 + 18 * k), y0 + 12 + k * 14)),
                            1.0, 0.6, sc, belly=8)

        tuft(70, 90)
        reed(180, 330)
        flower(320, 210)
        sapling(470, 400)
        tuft(600, 120, 7)
        bamboo(690, 300)
        ink = np.asarray(ink.resize((w, h), Image.LANCZOS), np.float32)
        red = np.asarray(red.resize((w, h), Image.LANCZOS), np.float32)
        wash = np.asarray(wash.filter(ImageFilter.GaussianBlur(7)), np.float32)
        im = Image.new("RGBA", (w, h), INK2 + (0,))
        im.putalpha(Image.fromarray(wash.astype(np.uint8)))
        lay = Image.new("RGBA", (w, h), RED + (0,))
        lay.putalpha(Image.fromarray((red * 0.85).astype(np.uint8)))
        im.alpha_composite(lay)
        lay = Image.new("RGBA", (w, h), INK + (0,))
        lay.putalpha(Image.fromarray((ink * 0.92).astype(np.uint8)))
        im.alpha_composite(lay)
        self.im = im
        r = np.random.default_rng(seed + 1)
        n = 150
        self.drops = list(zip(r.random(n) * (w + 120) - 60, r.random(n), 0.55 + 0.25 * r.random(n), 14 + 10 * r.random(n)))

    def rain(self, t, a=1.0, top=-40):
        im = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        if a <= 0:
            return im
        d = ImageDraw.Draw(im)
        span = self.ground - top
        for x0, ph, sp, ln in self.drops:
            y = top + ((ph + t * sp) % 1.0) * span
            x = x0 + (y - top) * 0.12
            if y + ln > self.ground:
                continue
            d.line((x, y, x + ln * 0.12, y + ln), fill=WATER + (int(130 * a),), width=2)
        return im


def cover_art():
    """封面插图：雨落草木（与封面插图区同为 800×690）。"""
    g = Garden()
    im = Image.new("RGBA", (800, 690), (0, 0, 0, 0))
    im.alpha_composite(g.rain(3.3, top=110), (20, 40))
    im.alpha_composite(g.im, (20, 40))
    return im


# ---------- 其一：不仁 ----------

class BuRen(Scene):
    PX, PY = 1060, 170

    def setup(self):
        self.garden = Garden()

    def draw(self, cv, t):
        p = self.p
        section(cv, t, 0.15, "一", p["section"])
        x0 = 150
        reveal_text(cv, t, 0.6, gfx.rich([("天地", "kai_m", INK), ("不仁", "kai_m", RED)], 84, spacing=6), x0, 196)
        tw = self.cue("wangbi")
        for j, line in enumerate(p["wangbi"]):
            reveal_text(cv, t, None if tw is None else tw + 0.3 + j * 0.4, text(line, "kai", 38, INK2), x0, 320 + j * 56)
        reveal_text(cv, t, None if tw is None else tw + 1.2, text("—— 王弼注", "serif", 26, INK3), x0 + 4, 438)
        td = self.cue("def")
        if td is not None:
            reveal_text(cv, t, td, gfx.rich([("仁    ", "serif_sb", INK3), (p["ren"], "kai", INK2)], 36), x0, 508)
            reveal_text(cv, t, self.clause_t("def", 3), gfx.rich([("不仁  ", "serif_sb", RED), (p["buren"], "kai", INK)], 36),
                        x0, 562)
        ts = self.cue("sage")
        reveal_text(cv, t, ts, text(p["sage"], "kai_m", 42, INK), x0, 650)
        reveal_text(cv, t, None if ts is None else self.clause_t("sage", 3), text(p["sage_note"], "serif", 26, RED),
                    x0 + 4, 712)
        tm = self.cue("modern")
        if tm is not None:
            k = fade(t, tm, 0.7)
            if k > 0:
                blit(cv, gfx.rounded_box(6, 60, fill=RED + (255,), radius=3), x0, 786, k)
            reveal_text(cv, t, tm + 0.15, text(p["modern"], "kai", 40, INK2), x0 + 28, 780)
        # 右侧：雨落草木，不择其类
        a = fade(t, 0.3, 1.0)
        blit(cv, self.garden.rain(t, fade(t, 1.0, 1.5)), self.PX, self.PY, a)
        blit(cv, self.garden.im, self.PX, self.PY, a)
        tr = self.cue("rain")
        reveal_text(cv, t, tr, text(p["caption"], "serif", 26, INK3, spacing=3), self.PX + self.garden.w / 2,
                    self.PY + self.garden.ground + 40, anchor="mt")


# ---------- 其二：刍狗 ----------

class ChuGou(Scene):
    CW, CH = 760, 400

    def box(self):
        return gfx.rounded_box(self.CW, self.CH, fill=(255, 252, 244, 150), outline=INK3 + (200,), width=2, radius=14)

    def draw(self, cv, t):
        p = self.p
        section(cv, t, 0.15, "二", p["section"])
        xl, xr, y = 180, 980, 190
        # 左卡：《庄子·天运》
        tz = self.cue("zhuang")
        if tz is not None:
            reveal_text(cv, t, tz, self.box(), xl, y)
            reveal_text(cv, t, tz + 0.2, text(p["zhuang_label"], "serif", 28, INK3, spacing=4), xl + 40, y + 28)
            reveal_text(cv, t, tz + 0.6, gfx.rich([("祭前  ", "serif_sb", RED), (p["before"], "kai_m", INK)], 38),
                        xl + 40, y + 96)
            ta = self.cue("after")
            k = fade(t, ta, 0.6)
            if k > 0:
                arrow = gfx.brush_line(60, 3, INK3, seed=4).rotate(90, expand=True)
                blit(cv, arrow, xl + 70, y + 166, k)
            reveal_text(cv, t, ta, gfx.rich([("祭后  ", "serif_sb", INK3), (p["after"], "kai_m", INK2)], 38),
                        xl + 40, y + 232)
            reveal_text(cv, t, self.cue("point"), text(p["point"], "kai", 34, RED), xl + 40, y + 318)
        # 右卡：王弼注
        tw = self.cue("wangbi")
        if tw is not None:
            reveal_text(cv, t, tw, self.box(), xr, y)
            reveal_text(cv, t, tw + 0.2, text(p["wangbi_label"], "serif", 28, INK3, spacing=4), xr + 40, y + 28)
            for j, line in enumerate(p["wangbi"]):
                reveal_text(cv, t, self.clause_t("wangbi", 1 + 2 * j), text(line, "kai_m", 42, INK), xr + 40, y + 96 + j * 70)
            reveal_text(cv, t, self.clause_t("wangbi", 5), text(p["wangbi_point"], "kai", 34, RED), xr + 40, y + 318)
        tc = self.cue("common")
        reveal_text(cv, t, tc, text(p["common"], "kai_m", 54, INK, spacing=6), 960, 640, anchor="mt")
        tm = self.cue("modern")
        if tm is not None:
            k = fade(t, tm, 0.7)
            if k > 0:
                blit(cv, gfx.rounded_box(6, 60, fill=RED + (255,), radius=3), 180, 772, k)
            reveal_text(cv, t, tm + 0.15, text(p["modern"], "kai", 38, INK2), 208, 768)


# ---------- 其三：守中 ----------

class ShouZhong(Scene):
    """右：天地之间如橐籥，中空而气流不竭；左：多言数穷，不如守中。"""

    X0, X1, YT, YB = 1090, 1770, 250, 640

    def draw(self, cv, t):
        p = self.p
        section(cv, t, 0.15, "三", p["section"])
        cx, cy = (self.X0 + self.X1) / 2, (self.YT + self.YB) / 2
        a = fade(t, 0.3, 1.0)
        # 天、地两笔
        for yy, lab, seed in [(self.YT, "天", 1), (self.YB, "地", 2)]:
            blit(cv, gfx.brush_line(self.X1 - self.X0, 5, INK, seed=seed), self.X0, yy, a, anchor="lm")
            blit(cv, text(lab, "kai_m", 44, INK2), self.X0 - 30, yy, a, anchor="rm")
        # 中空：淡墨“虚”字
        blit(cv, gfx.glyph("虚", "kai_m", 150, INK), cx, cy, 0.10 * a, anchor="mm")
        # 气流：自中央向两侧不断涌出
        tb = self.cue("bellows")
        k = fade(t, tb, 1.5) if tb is not None else 0
        if k > 0:
            sc = 2
            w, h = self.X1 - self.X0, self.YB - self.YT
            im = Image.new("RGBA", (w * sc, h * sc), (0, 0, 0, 0))
            d = ImageDraw.Draw(im)
            for j in range(7):
                yj = h * (0.2 + 0.1 * j)
                for i in range(6):
                    s0 = ((t * 70 + i * 60 + j * 23) % 330)
                    fade_out = 1 - s0 / 330
                    for side in (-1, 1):
                        pts = []
                        for q in range(12):
                            s = s0 + q * 4
                            x = w / 2 + side * (20 + s)
                            y = yj + 9 * math.sin(s / 38 + j + t * 1.5)
                            pts.append((x * sc, y * sc))
                        d.line(pts, fill=INK3 + (int(200 * fade_out * k),), width=2 * sc, joint="curve")
            im = im.resize((w, h), Image.LANCZOS)
            blit(cv, im, self.X0, self.YT, a)
        reveal_text(cv, t, tb, text(p["bellows_caption"], "kai", 36, INK2, spacing=4), cx, self.YB + 46, anchor="mt")
        # 左侧
        x0 = 150
        td = self.cue("duo")
        if td is not None:
            spr = gfx.rich([("多言", "kai_m", INK), ("数", "kai_m", RED), ("穷，不如", "kai_m", INK), ("守中", "kai_m", RED)],
                           64, spacing=4)
            reveal_text(cv, t, td, spr, x0, 210)
            cw = gfx.text_width("多言", "kai_m", 64, 4) + 4
            reveal_text(cv, t, td + 0.8, text("shuò", "serif", 26, RED), x0 + cw + 34, 196, anchor="mt")
        tbs = self.cue("boshu")
        reveal_text(cv, t, tbs, gfx.rich([("帛书乙本  ", "serif_sb", INK3), (p["boshu"], "kai", INK2)], 36), x0, 330)
        tw = self.cue("wangbi")
        reveal_text(cv, t, tw, text(p["wangbi"], "kai_m", 48, INK), x0, 440)
        reveal_text(cv, t, None if tw is None else tw + 0.4, text("—— 王弼注", "serif", 26, INK3), x0 + 4, 510)
        tm = self.cue("modern")
        if tm is not None:
            k = fade(t, tm, 0.7)
            if k > 0:
                blit(cv, gfx.rounded_box(6, 128, fill=RED + (255,), radius=3), x0, 640, k)
            for j, line in enumerate(p["modern"]):
                reveal_text(cv, t, tm + 0.15 + j * 0.35, text(line, "kai_m", 40, INK), x0 + 28, 640 + j * 66)
