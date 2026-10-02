"""第 05 期专用场景：三组对照、以灯传灯（不积）、为而不争、系列结语。"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from dao import gfx
from dao.config import INK, INK2, INK3, RED, W
from dao.gfx import blit, ease_out, fade, glyph, ink_reveal, seal, text
from dao.scenes import Scene, reveal_text, section

FLAME_IN = (236, 166, 84)


# ---------- 灯 ----------

class Lamps:
    """一排油灯：lit[i] 为第 i 盏点亮的时刻；点灯前有一点火光自前一盏移来。"""

    def __init__(self, n=5, w=760, h=420, seed=2):
        self.n, self.w, self.h = n, w, h
        self.base_y = h - 40
        self.xs = [w * (i + 0.5) / n for i in range(n)]
        sc = 2
        ink = Image.new("L", (w * sc, h * sc), 0)
        d = ImageDraw.Draw(ink)
        for x in self.xs:
            by = self.base_y
            # 灯座、灯柱、灯盏
            d.ellipse(((x - 38) * sc, (by - 8) * sc, (x + 38) * sc, (by + 8) * sc), outline=255, width=3 * sc)
            d.line(((x) * sc, (by - 6) * sc, x * sc, (by - 120) * sc), fill=255, width=4 * sc)
            d.chord(((x - 46) * sc, (by - 150) * sc, (x + 46) * sc, (by - 106) * sc), 0, 180, outline=255, width=4 * sc)
            d.line(((x - 46) * sc, (by - 128) * sc, (x + 46) * sc, (by - 128) * sc), fill=255, width=3 * sc)
        self.ink = Image.new("RGBA", (w, h), INK + (0,))
        self.ink.putalpha(ink.resize((w, h), Image.LANCZOS).point(lambda v: int(v * 0.9)))
        self.flame_y = self.base_y - 150
        self.yy, self.xx = np.mgrid[0:h, 0:w].astype(np.float32)
        # 光晕在图块边缘渐隐，避免出现矩形边界
        self.window = (np.clip(self.yy / 110, 0, 1) * np.clip((h - self.yy) / 60, 0, 1) *
                       np.clip(self.xx / 110, 0, 1) * np.clip((w - self.xx) / 110, 0, 1))

    def flame(self, size, flick):
        s = int(size * 3)
        im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        cx, cy = s / 2, s * 0.62
        hgt = size * (1.0 + 0.06 * flick)
        pts = [(cx + math.sin(a) * size * 0.32 * (1 - (1 - math.cos(a)) / 2.4),
                cy - hgt * (1 - math.cos(a)) / 2 * 1.3 + size * 0.15) for a in np.linspace(0, 2 * math.pi, 40)]
        d.polygon(pts, fill=RED + (235,))
        inner = [(cx + (x - cx) * 0.55, cy + (y - cy) * 0.6 + size * 0.06) for x, y in pts]
        d.polygon(inner, fill=FLAME_IN + (240,))
        return im.filter(ImageFilter.GaussianBlur(0.8))

    def image(self, t, lit):
        im = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        # 光晕：点亮的灯越多，四周越亮
        glow = np.zeros((self.h, self.w), np.float32)
        yy, xx = self.yy, self.xx
        for x, tl in zip(self.xs, lit):
            k = fade(t, tl, 0.8)
            if k > 0:
                glow += k * np.exp(-(((xx - x) / 150) ** 2 + ((yy - self.flame_y) / 120) ** 2))
        glow *= self.window
        if glow.max() > 0:
            g = Image.new("RGBA", (self.w, self.h), (246, 214, 160, 0))
            g.putalpha(Image.fromarray((np.clip(glow, 0, 1.6) / 1.6 * 150).astype(np.uint8)))
            im.alpha_composite(g)
        im.alpha_composite(self.ink)
        for i, (x, tl) in enumerate(zip(self.xs, lit)):
            k = fade(t, tl, 0.5)
            if k > 0:
                f = self.flame(30 * (0.6 + 0.4 * k), math.sin(t * 7 + i * 1.7))
                blit(im, f, x, self.flame_y - 8, k, anchor="mm")
            # 火光从前一盏移来
            if i > 0 and tl is not None and tl - 0.7 < t < tl:
                u = (t - (tl - 0.7)) / 0.7
                px = self.xs[i - 1] + (x - self.xs[i - 1]) * u
                py = self.flame_y - 20 - math.sin(math.pi * u) * 60
                blit(im, self.flame(12, 0), px, py, 0.9, anchor="mm")
        return im


def cover_art():
    """封面插图：五盏点亮的灯（与封面插图区同为 800×690）。"""
    lamps = Lamps(n=4, w=700, h=420)
    im = Image.new("RGBA", (800, 690), (0, 0, 0, 0))
    im.alpha_composite(lamps.image(10.0, [0, 0, 0, 0]), (50, 170))
    return im


# ---------- 其一：三组对照 ----------

class Pairs(Scene):
    CW, CH = 500, 430

    def card(self, label, a, b):
        im = gfx.rounded_box(self.CW, self.CH, fill=(255, 252, 244, 150), outline=INK3 + (200,), width=2, radius=14)
        im.alpha_composite(text(label, "serif", 28, INK3, spacing=6), (40, 30))
        im.alpha_composite(text(a, "kai_m", 56, INK, spacing=4), (40, 100))
        im.alpha_composite(text(b, "kai_m", 56, INK3, spacing=4), (40, 190))
        return im

    def setup(self):
        self.cards = [self.card(*c) for c in self.p["pairs"]]
        self.xs = [180, 710, 1240]

    def draw(self, cv, t):
        p = self.p
        section(cv, t, 0.15, "一", p["section"])
        y = 190
        for i, (im, x) in enumerate(zip(self.cards, self.xs)):
            reveal_text(cv, t, self.clause_t("pairs", i + 1), im, x, y)
        tw = self.cue("wangbi")
        if tw is not None:
            for i, k in [(0, 1), (2, 4)]:
                ta = self.clause_t("wangbi", k)
                reveal_text(cv, t, ta, text(p["notes"][i], "kai_m", 34, RED), self.xs[i] + 40, y + 300)
                reveal_text(cv, t, ta + 0.3, text("—— 王弼注", "serif", 24, INK3), self.xs[i] + 40, y + 356)
        tb = self.cue("boshu")
        if tb is not None:
            reveal_text(cv, t, tb, text(p["notes"][1], "kai", 30, RED), self.xs[1] + 40, y + 300)
            reveal_text(cv, t, tb + 0.3, text("—— 马王堆帛书", "serif", 24, INK3), self.xs[1] + 40, y + 356)
        tn = self.cue("not")
        reveal_text(cv, t, None if tn is None else self.clause_t("not", 3), text(p["not"], "kai_m", 46, INK, spacing=4),
                    960, 668, anchor="mt")
        tm = self.cue("modern")
        if tm is not None:
            k = fade(t, tm, 0.7)
            if k > 0:
                blit(cv, gfx.rounded_box(6, 60, fill=RED + (255,), radius=3), 180, 784, k)
            reveal_text(cv, t, tm + 0.15, text(p["modern"], "kai", 40, INK2), 208, 778)


# ---------- 其二：不积 ----------

class BuJi(Scene):
    PX, PY = 1040, 260

    def setup(self):
        self.lamps = Lamps()

    def draw(self, cv, t):
        p = self.p
        section(cv, t, 0.15, "二", p["section"])
        x0 = 150
        tr = self.cue("read")
        reveal_text(cv, t, tr, text("圣人不积", "kai_m", 76, INK, spacing=8), x0, 196)
        if tr is not None:
            for j, (a, b) in enumerate(p["lines"]):
                reveal_text(cv, t, self.clause_t("read", j + 1), gfx.rich([(a, "kai_m", INK), (b, "kai_m", RED)], 54),
                            x0, 320 + j * 86)
        tg = self.cue("gloss")
        if tg is not None:
            for j, line in enumerate(p["gloss"]):
                reveal_text(cv, t, self.clause_t("gloss", 1 + 2 * j), text(line, "kai", 36, INK2), x0, 520 + j * 58)
        tm = self.cue("modern")
        if tm is not None:
            k = fade(t, tm, 0.7)
            if k > 0:
                blit(cv, gfx.rounded_box(6, 60, fill=RED + (255,), radius=3), x0, 718, k)
            reveal_text(cv, t, tm + 0.15, text(p["modern"], "kai_m", 40, INK), x0 + 28, 712)
        # 右侧：以灯传灯
        tl = self.cue("lamp")
        base = (tl if tl is not None else 99) + 1.2
        lit = [0.6] + [base + k * 1.0 for k in range(self.lamps.n - 1)]
        blit(cv, self.lamps.image(t, lit), self.PX, self.PY, fade(t, 0.3, 0.8))
        reveal_text(cv, t, None if tl is None else base + 4.4, text(p["caption"], "serif", 28, INK3, spacing=4),
                    self.PX + self.lamps.w / 2, self.PY + self.lamps.h + 20, anchor="mt")


# ---------- 其三：为而不争 ----------

class WeiErBuZheng(Scene):
    def setup(self):
        self.size = 150
        self.lay, self.h = gfx.vlayout("为而不争", self.size, step=1.1)
        self.x, self.y0 = 1560, 160

    def draw(self, cv, t):
        p = self.p
        section(cv, t, 0.15, "三", p["section"])
        # 右：竖排“为而不争”，“为”字朱色并圈出
        tw = self.cue("wei")
        for i, (ch, dy) in enumerate(self.lay):
            col = RED if (i == 0 and tw is not None and t > tw + 1.0) else INK
            g = glyph(ch, "kai_m", self.size, col)
            k = gfx.clamp((t - 0.5 - i * 0.3) / 1.0)
            blit(cv, ink_reveal(g, k, seed=300 + i), self.x, self.y0 + dy + self.size / 2, anchor="mm")
        if tw is not None:
            k = fade(t, tw + 1.0, 0.4)
            if k > 0:
                blit(cv, gfx.circle_mark(int(self.size * 1.3), RED, 4), self.x, self.y0 + self.size / 2, k,
                     anchor="mm", scale=1 + 0.15 * (1 - k))
        # 左
        x0 = 150
        tl = self.cue("last")
        if tl is not None:
            reveal_text(cv, t, tl, text(p["last"][0], "kai_m", 52, INK2, spacing=2), x0, 200)
            reveal_text(cv, t, self.clause_t("last", 2), gfx.rich([("圣人之道，", "kai_m", INK2), ("为而不争", "kai_m", INK)], 52,
                                                                spacing=2), x0, 276)
        tw2 = self.cue("wangbi")
        reveal_text(cv, t, tw2, gfx.rich([("王弼注  ", "serif", INK3), (p["wangbi"], "kai", INK)], 38), x0, 396)
        tb = self.cue("boshu")
        reveal_text(cv, t, tb, gfx.rich([("帛书  ", "serif", INK3), (p["boshu"], "kai", INK)], 38), x0, 462)
        te = self.cue("echo")
        if te is not None:
            box = gfx.rounded_box(760, 120, fill=(255, 252, 244, 150), outline=INK3 + (200,), width=2, radius=14)
            reveal_text(cv, t, te, box, x0, 548)
            reveal_text(cv, t, te + 0.2, text("第 01 期 · 上善若水", "serif", 26, INK3, spacing=3), x0 + 36, 566)
            reveal_text(cv, t, te + 0.4, gfx.rich([("水善利万物而", "kai_m", INK), ("不争", "kai_m", RED)], 44),
                        x0 + 36, 608)
        tm = self.cue("modern")
        if tm is not None:
            k = fade(t, tm, 0.7)
            if k > 0:
                blit(cv, gfx.rounded_box(6, 60, fill=RED + (255,), radius=3), x0, 742, k)
            reveal_text(cv, t, tm + 0.15, text(p["modern"], "kai", 40, INK2), x0 + 28, 736)


# ---------- 系列结语 ----------

class Finale(Scene):
    """前五期回顾：五句竖排依次显现，随后给出留言邀请。"""

    def draw(self, cv, t):
        p = self.p
        reveal_text(cv, t, 0.3, gfx.rich([(p["series"] + "  ·  ", "serif_sb", INK2), ("前五期", "serif_sb", RED)], 44,
                                         spacing=2), W / 2, 96, anchor="mt")
        s = self.seg("list")
        xs = [1460, 1210, 960, 710, 460]
        size = 84
        for i, ((num, title, chap), x) in enumerate(zip(p["items"], xs)):
            ta = s.t0 + s.clauses[min(i, len(s.clauses) - 1)][1]
            a = fade(t, ta, 0.5)
            if a <= 0:
                continue
            blit(cv, text(num, "serif_bk", 34, RED), x, 200, a, anchor="mt")
            for k, ch in enumerate(title):
                kk = gfx.clamp((t - ta - k * 0.1) / 0.6)
                blit(cv, ink_reveal(glyph(ch, "kai_m", size, INK), kk, seed=400 + i * 4 + k), x,
                     262 + k * size * 1.1 + size / 2, anchor="mm")
            reveal_text(cv, t, ta + 0.4, text(chap, "serif", 26, INK3, spacing=2), x, 650, anchor="mt")
        tc = self.cue("cta")
        if tc is not None:
            reveal_text(cv, t, tc, text(p["cta"][0], "kai_m", 48, INK, spacing=2), W / 2, 738, anchor="mt")
            reveal_text(cv, t, self.clause_t("cta", 2), text(p["cta"][1], "kai", 38, INK2, spacing=2), W / 2, 812,
                        anchor="mt")
            ts = tc + 1.6
            blit(cv, seal("细读", 84, seed=9), W / 2 - 530, 768, fade(t, ts, 0.3), anchor="mm",
                 scale=1 + 0.25 * (1 - ease_out((t - ts) / 0.3)))
