"""第 04 期专用场景：未兆（毫末成木）、足下（百仞之高）、慎终（几成而败）。"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from dao import gfx
from dao.config import INK, INK2, INK3, RED
from dao.gfx import blit, ease_out, fade, seal, text
from dao.scenes import Scene, reveal_text, section


def _dot(d, color=INK):
    sc = 4
    m = Image.new("L", (d * sc, d * sc), 0)
    ImageDraw.Draw(m).ellipse((0, 0, d * sc - 1, d * sc - 1), fill=255)
    im = Image.new("RGBA", (d, d), color + (0,))
    im.putalpha(m.resize((d, d), Image.LANCZOS))
    return im


# ---------- 毫末成木 ----------

class Tree:
    """分枝生长的树：grow(g) 中 g 由 0 到 1，自一茎幼芽长成合抱之木。"""

    def __init__(self, height=520, seed=4, depth=7):
        rng = np.random.default_rng(seed)
        self.h = height
        self.segs = []      # (x0, y0, x1, y1, 层级, 生长起点)
        self.leaves = []    # (x, y, 半径, 出现时刻)

        def grow(x, y, ang, ln, d):
            x1, y1 = x + math.cos(ang) * ln, y + math.sin(ang) * ln
            birth = d / (depth + 1) + rng.random() * 0.03
            self.segs.append((x, y, x1, y1, d, birth))
            if d >= depth:
                self.leaves.append((x1, y1, 16 + rng.random() * 14, 0.8 + rng.random() * 0.15))
                return
            n = 2 if rng.random() < 0.7 else 3
            for k in range(n):
                spread = (k - (n - 1) / 2) * (0.42 + rng.random() * 0.12)
                grow(x1, y1, ang + spread + rng.normal(0, 0.06), ln * (0.70 + rng.random() * 0.08), d + 1)

        grow(0, 0, -math.pi / 2 + rng.normal(0, 0.03), height * 0.26, 0)

    def image(self, g, w=700, h=620):
        sc = 2
        ink = Image.new("L", (w * sc, h * sc), 0)
        wash = Image.new("L", (w, h), 0)
        d, dw = ImageDraw.Draw(ink), ImageDraw.Draw(wash)
        ox, oy = w / 2, h - 30
        step = 1 / 8
        # 整体随生长放大：幼时极小，长成后满幅
        s = 0.12 + 0.88 * ease_out(g)
        for x0, y0, x1, y1, dep, b in self.segs:
            k = (g - b) / step
            if k <= 0:
                continue
            k = min(k, 1.0)
            xe, ye = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
            wid = max(1.2, 11 * (0.68 ** dep)) * (0.4 + 0.6 * s) * sc
            p0 = ((ox + x0 * s) * sc, (oy + y0 * s) * sc)
            p1 = ((ox + xe * s) * sc, (oy + ye * s) * sc)
            d.line([p0, p1], fill=255, width=int(wid))
            r = wid / 2
            d.ellipse((p1[0] - r, p1[1] - r, p1[0] + r, p1[1] + r), fill=255)
        for x, y, r, b in self.leaves:
            if g > b:
                a = min(1.0, (g - b) / 0.1)
                rr = r * s
                dw.ellipse((ox + x * s - rr, oy + y * s - rr * 0.8, ox + x * s + rr, oy + y * s + rr * 0.8),
                           fill=int(60 * a))
        im = Image.new("RGBA", (w, h), INK2 + (0,))
        im.putalpha(wash.filter(ImageFilter.GaussianBlur(6)))
        lay = Image.new("RGBA", (w, h), INK + (0,))
        lay.putalpha(ink.resize((w, h), Image.LANCZOS))
        im.alpha_composite(lay)
        # 地面
        im.alpha_composite(gfx.brush_line(w - 80, 3, INK, seed=6), (40, int(oy - 4)))
        return im


def cover_art():
    """封面插图：长成的树（与封面插图区同为 800×690）。"""
    im = Image.new("RGBA", (800, 690), (0, 0, 0, 0))
    im.alpha_composite(Tree(height=470).image(1.0, 700, 600), (40, 0))
    return im


# ---------- 其一：未兆 ----------

class WeiZhao(Scene):
    PX, PY = 1080, 200

    def setup(self):
        self.tree = Tree()

    def draw(self, cv, t):
        p = self.p
        section(cv, t, 0.15, "一", p["section"])
        x0 = 150
        ta = self.cue("an")
        if ta is not None:
            for j, item in enumerate(p["easy"]):
                ti = self.clause_t("an", j * 2) if len(self.seg("an").clauses) > j * 2 else ta
                reveal_text(cv, t, ti, text(item, "kai", 38, INK2), x0 + (j % 2) * 300, 200 + (j // 2) * 62)
        tc = self.cue("core")
        reveal_text(cv, t, None if tc is None else self.clause_t("core", 0) + 0.6,
                    text(p["core"][0], "kai_m", 72, INK, spacing=6), x0, 360)
        reveal_text(cv, t, None if tc is None else self.clause_t("core", 1),
                    text(p["core"][1], "kai_m", 72, RED, spacing=6), x0, 460)
        tt = self.cue("tree")
        reveal_text(cv, t, tt, text(p["tree_note"], "kai", 36, INK2), x0, 600)
        tm = self.cue("modern")
        if tm is not None:
            k = fade(t, tm, 0.7)
            if k > 0:
                blit(cv, gfx.rounded_box(6, 128, fill=RED + (255,), radius=3), x0, 700, k)
            for j, line in enumerate(p["modern"]):
                reveal_text(cv, t, tm + 0.15 + j * 0.35, text(line, "kai_m", 40, INK), x0 + 28, 700 + j * 66)
        # 右侧：毫末 → 合抱
        end = (tt if tt is not None else 30) + 4
        g = 0.04 + 0.96 * gfx.clamp((t - 1.0) / (end - 1.0)) ** 1.15
        a = fade(t, 0.3, 0.8)
        im = self.tree.image(g)
        blit(cv, im, self.PX, self.PY, a)
        gy = self.PY + im.height - 30
        cx = self.PX + im.width / 2
        reveal_text(cv, t, 1.2, text(p["label_small"], "kai", 34, RED), cx + 40, gy + 22, a=1 - fade(t, end - 3, 1.0))
        reveal_text(cv, t, end - 2.5, text(p["label_big"], "kai_m", 38, INK2), cx, gy + 22, anchor="mt")


# ---------- 其二：足下 ----------

class ZuXia(Scene):
    CW, CH = 760, 290

    def box(self):
        return gfx.rounded_box(self.CW, self.CH, fill=(255, 252, 244, 150), outline=INK3 + (200,), width=2, radius=14)

    def draw(self, cv, t):
        p = self.p
        section(cv, t, 0.15, "二", p["section"])
        xl, xr, y = 180, 980, 190
        tv = self.cue("v1")
        if tv is not None:
            reveal_text(cv, t, tv, self.box(), xl, y)
            reveal_text(cv, t, tv + 0.2, text("通行本（王弼本）", "serif", 28, INK3, spacing=4), xl + 40, y + 28)
            reveal_text(cv, t, tv + 0.4, gfx.rich([("千里之行，", "kai_m", INK), ("始于足下", "kai_m", RED)], 52),
                        xl + 40, y + 110)
            tb = self.clause_t("v1", 2)
            reveal_text(cv, t, tb, self.box(), xr, y)
            reveal_text(cv, t, tb + 0.2, text("马王堆帛书", "serif", 28, INK3, spacing=4), xr + 40, y + 28)
            for j, (lab, line) in enumerate(p["boshu"]):
                reveal_text(cv, t, tb + 0.4 + j * 0.4, gfx.rich([(lab + "  ", "serif_sb", INK3), (line, "kai_m", INK)], 40),
                            xr + 40, y + 88 + j * 62)
        tr = self.cue("ren")
        reveal_text(cv, t, tr, text(p["ren"], "kai", 30, RED), xr + 40, y + self.CH - 8, anchor="lb")
        tp = self.cue("parallel")
        if tp is not None:
            for j, (a, b) in enumerate(p["parallel"]):
                ti = tp + 0.5 + j * 0.7
                reveal_text(cv, t, ti, gfx.rich([(a + "，", "kai_m", INK2), (b, "kai_m", RED)], 50, spacing=4),
                            960, 528 + j * 76, anchor="mt")
        tm = self.cue("modern")
        if tm is not None:
            k = fade(t, tm, 0.7)
            if k > 0:
                blit(cv, gfx.rounded_box(6, 60, fill=RED + (255,), radius=3), 180, 790, k)
            reveal_text(cv, t, tm + 0.15, text(p["modern"], "kai", 40, INK2), 208, 784)


# ---------- 其三：慎终 ----------

class ShenZhong(Scene):
    X0, X1, Y = 1060, 1740, 560

    def draw(self, cv, t):
        p = self.p
        section(cv, t, 0.15, "三", p["section"])
        x0 = 150
        tf = self.cue("fail")
        if tf is not None:
            spr = gfx.rich([("民之从事，常于", "kai_m", INK), ("几成", "kai_m", RED), ("而败之", "kai_m", INK)], 50,
                           spacing=2)
            reveal_text(cv, t, tf, spr, x0, 210)
            cw = gfx.text_width("民之从事，常于", "kai_m", 50, 2) + 4
            reveal_text(cv, t, tf + 0.8, text("jī", "serif", 26, RED), x0 + cw + 25, 196, anchor="mt")
        tw = self.cue("wangbi")
        reveal_text(cv, t, tw, gfx.rich([("王弼注  ", "serif", INK3), ("不慎终也", "kai_m", RED)], 56), x0, 320)
        ts = self.cue("shen")
        reveal_text(cv, t, ts, text(p["shen"], "kai_m", 60, INK, spacing=4), x0, 450)
        tm = self.cue("modern")
        if tm is not None:
            k = fade(t, tm, 0.7)
            if k > 0:
                blit(cv, gfx.rounded_box(6, 128, fill=RED + (255,), radius=3), x0, 640, k)
            for j, line in enumerate(p["modern"]):
                reveal_text(cv, t, tm + 0.15 + j * 0.35, text(line, "kai_m", 40, INK), x0 + 28, 640 + j * 66)
        # 右侧：始 —— 终 的路径
        a = fade(t, 0.3, 0.8)
        L = self.X1 - self.X0
        blit(cv, gfx.brush_line(L, 5, INK3, seed=3), self.X0, self.Y, a, anchor="lm")
        blit(cv, text("始", "kai_m", 52, INK), self.X0 - 20, self.Y, a, anchor="rm")
        blit(cv, text("终", "kai_m", 52, INK), self.X1 + 20, self.Y, a, anchor="lm")
        # “几成”危险区
        z0, z1 = 0.80, 0.96
        zk = fade(t, None if tf is None else self.clause_t("fail", 2), 0.6)
        if zk > 0:
            band = gfx.rounded_box(int(L * (z1 - z0)), 36, fill=RED + (70,), radius=10)
            blit(cv, band, self.X0 + L * z0, self.Y, zk, anchor="lm")
            blit(cv, text("几成", "kai_m", 38, RED), self.X0 + L * (z0 + z1) / 2, self.Y - 44, zk, anchor="mb")
        # 行进的墨点：先停在将成处，“慎终”之后才走到终点
        stop = 0.88
        if ts is None or t < ts + 0.5:
            u = stop * ease_out(gfx.clamp((t - 0.8) / 9.0))
        else:
            u = stop + (1 - stop) * ease_out(gfx.clamp((t - ts - 0.5) / 2.0))
        dot = _dot(30)
        blit(cv, dot, self.X0 + L * u, self.Y, a, anchor="mm")
        if tw is not None and (ts is None or t < ts + 0.5):
            blit(cv, text("败", "kai_m", 46, RED), self.X0 + L * stop, self.Y + 36, fade(t, tw + 0.3, 0.4) *
                 (1 - fade(t, ts, 0.4) if ts is not None else 1), anchor="mt")
        if ts is not None:
            k = fade(t, ts + 2.4, 0.3)
            blit(cv, seal("慎", 76, seed=31), self.X1, self.Y + 70, k, anchor="mt",
                 scale=1 + 0.25 * (1 - ease_out((t - ts - 2.4) / 0.3)))
        reveal_text(cv, t, 1.0, text(p["path_caption"], "serif", 26, INK3, spacing=4), (self.X0 + self.X1) / 2,
                    self.Y + 190, anchor="mt")
