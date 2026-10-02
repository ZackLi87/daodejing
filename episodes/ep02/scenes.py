"""第 02 期专用场景：三种写法、句式对照、道隐无名与未竟之器。"""
import math

import numpy as np
from PIL import Image, ImageDraw

from dao import gfx
from dao.config import INK, INK2, INK3, RED
from dao.gfx import blit, ease_out, fade, glyph, ink_reveal, text
from dao.scenes import Scene, reveal_text, section


# ---------- 未竟之器 ----------

class Vessel:
    """以墨线勾勒的一只罐，按笔顺画出：口沿、左轮廓、右轮廓、肩部纹带、底足。
    image(p) 返回画到进度 p（0–1）时的图块；p 取 0.86 左右时底足尚未合拢，即“未完成的器”。"""

    # 轮廓控制点 (y, 半宽)，均按高度归一
    PROFILE = [(0.00, 0.21), (0.06, 0.17), (0.16, 0.15), (0.26, 0.22), (0.38, 0.38), (0.52, 0.45),
               (0.66, 0.43), (0.80, 0.33), (0.93, 0.21), (1.00, 0.22)]

    def __init__(self, h, thick=5.0, color=INK, seed=2):
        self.h = h
        w = int(h * 1.05)
        self.w = w
        sc = 3
        ys = np.linspace(0, 1, 400)
        r = np.interp(ys, *zip(*self.PROFILE))
        k = np.exp(-0.5 * (np.arange(-30, 31) / 9.0) ** 2)
        r = np.convolve(np.pad(r, 30, mode="edge"), k / k.sum(), mode="same")[30:-30]
        cx, top = w / 2, h * 0.08
        H = h * 0.86
        strokes = []
        # 口沿（椭圆）
        a = np.linspace(math.pi, 3 * math.pi, 120)
        strokes.append([(cx + r[0] * H * math.cos(t), top + 0.045 * H * math.sin(t)) for t in a])
        # 左、右轮廓
        strokes.append([(cx - ri * H, top + y * H) for y, ri in zip(ys, r)])
        strokes.append([(cx + ri * H, top + y * H) for y, ri in zip(ys, r)])
        # 肩部纹带（前半椭圆）
        yb = 0.40
        rb = np.interp(yb, ys, r) * H * 0.97
        a = np.linspace(math.pi, 0, 80)
        strokes.append([(cx + rb * math.cos(t), top + yb * H + 0.05 * H * math.sin(t)) for t in a])
        # 底足
        rf = r[-1] * H
        a = np.linspace(math.pi, 0, 60)
        strokes.append([(cx + rf * math.cos(t), top + H + 0.03 * H * math.sin(t)) for t in a])

        lens = [sum(math.dist(s[i], s[i + 1]) for i in range(len(s) - 1)) for s in strokes]
        total = sum(lens)
        rng = np.random.default_rng(seed)
        ink = Image.new("L", (w * sc, h * sc), 0)
        order = Image.new("I", (w, h), 0)
        di, do = ImageDraw.Draw(ink), ImageDraw.Draw(order)
        acc = 0.0
        for s, ln in zip(strokes, lens):
            run = 0.0
            for i, (x, y) in enumerate(s):
                if i:
                    run += math.dist(s[i - 1], s[i])
                u = run / max(ln, 1e-6)
                th = thick * (0.45 + 0.75 * math.sin(math.pi * min(max(u, 0.02), 0.98)) ** 0.6) * \
                    (0.9 + 0.2 * rng.random())
                rr = th / 2 * sc
                di.ellipse((x * sc - rr, y * sc - rr, x * sc + rr, y * sc + rr), fill=255)
                ro = th / 2 + 1.5
                do.ellipse((x - ro, y - ro, x + ro, y + ro), fill=int((acc + run) / total * 10000) + 1)
            acc += ln
        self.ink = np.asarray(ink.resize((w, h), Image.LANCZOS), np.float32)
        self.order = np.asarray(order, np.float32) / 10000
        self.color = color

    def image(self, p, alpha=1.0):
        m = np.clip((p - self.order) / 0.012, 0, 1) * (self.order > 0)
        # 收笔处渐淡，似笔锋未尽
        a = self.ink * m * alpha
        im = Image.new("RGBA", (self.w, self.h), self.color + (0,))
        im.putalpha(Image.fromarray(a.astype(np.uint8)))
        return im


def cover_art():
    """封面插图：一只尚未画完的罐（与封面插图区同为 800×690）。"""
    v = Vessel(430, thick=7)
    im = Image.new("RGBA", (800, 690), (0, 0, 0, 0))
    im.alpha_composite(v.image(0.86), (190, 130))
    return im


# ---------- 其一：三种写法 ----------

class Versions(Scene):
    CW, CH = 420, 560

    def setup(self):
        self.cards = []
        for label, sub, phrase, vi in self.p["versions"]:
            im = gfx.rounded_box(self.CW, self.CH, fill=(255, 252, 244, 150), outline=INK3 + (200,), width=2,
                                 radius=14)
            blit(im, text(label, "serif_sb", 36, INK, spacing=4), self.CW / 2, 54, anchor="mm")
            blit(im, text(sub, "serif", 24, INK3, spacing=2), self.CW / 2, 102, anchor="mm")
            size = 84
            for k, ch in enumerate(phrase):
                g = glyph(ch, "kai_m", size, RED if k == vi else INK)
                blit(im, g, self.CW / 2, 175 + k * size * 1.12 + size / 2, anchor="mm")
            self.cards.append((im, 175 + vi * size * 1.12 + size / 2))
        self.xs = [470, 960, 1450]

    def draw(self, cv, t):
        p = self.p
        section(cv, t, 0.15, "一", p["section"])
        y0 = 180
        for i, ((im, vy), x) in enumerate(zip(self.cards, self.xs)):
            tc = self.cue(f"v{i + 1}")
            reveal_text(cv, t, tc, im, x, y0, anchor="mt", rise=14)
            if tc is not None:
                k = fade(t, tc + 0.9, 0.4)
                if k > 0:
                    blit(cv, gfx.circle_mark(118, RED, 3), x, y0 + vy, k, anchor="mm", scale=1 + 0.2 * (1 - k))
        tn = self.cue("notes")
        if tn is not None:
            for j, line in enumerate(p["notes"]):
                s = self.seg("notes")
                ta = tn + s.clauses[min(1 + j, len(s.clauses) - 1)][1]
                reveal_text(cv, t, ta, gfx.rich([(line[0], "serif_sb", INK2), (line[1], "kai", INK)], 32),
                            self.xs[0], 778 + j * 56, anchor="mt")
        tl = self.cue("loan")
        reveal_text(cv, t, tl, gfx.rich([("一说  ", "serif_sb", INK2), (p["loan"], "kai", INK)], 34),
                    (self.xs[1] + self.xs[2]) / 2, 790, anchor="mt")


# ---------- 其二：句式 ----------

class Pattern(Scene):
    """『大方无隅』『大音希声』『大象无形』与『大器晚成』并列：前三句第三字皆为否定。"""

    def setup(self):
        self.size = 92
        self.xs = [1500, 1170, 840, 510]
        self.y0 = 190

    def cy(self, k):
        return self.y0 + k * self.size * 1.1 + self.size / 2

    def draw(self, cv, t):
        p = self.p
        section(cv, t, 0.15, "二", p["section"])
        sr, sg = self.seg("read"), self.seg("gloss")
        reads = [sr.t0 + c[1] for c in sr.clauses]
        gloss = [sg.t0 + c[1] for c in sg.clauses]
        tp, tsw = self.cue("pattern"), self.cue("swap")
        for i, (phrase, key, desc) in enumerate(p["items"][:3]):
            x = self.xs[i]
            ta = reads[min(i, len(reads) - 1)]
            for k, ch in enumerate(phrase):
                g = glyph(ch, "kai_m", self.size, RED if k == 2 else INK)
                kk = gfx.clamp((t - ta - k * 0.12) / 0.6)
                blit(cv, ink_reveal(g, kk, seed=200 + i * 4 + k), x, self.cy(k), anchor="mm")
            tg = gloss[min(2 * i, len(gloss) - 1)]
            reveal_text(cv, t, tg, text(key, "serif_sb", 32, RED, spacing=4), x, 650, anchor="mt")
            reveal_text(cv, t, tg + 0.15, text(desc, "kai", 34, INK2), x, 702, anchor="mt")
            if tp is not None:
                k = fade(t, tp + 0.5 + i * 0.35, 0.4)
                if k > 0:
                    blit(cv, gfx.circle_mark(126, RED, 3), x, self.cy(2), k, anchor="mm", scale=1 + 0.2 * (1 - k))
        # 第四列：先以淡墨呈现“大器晚成”，随后“晚”字隐去、朱色“免”字显出
        phrase, key, desc = p["items"][3]
        x = self.xs[3]
        a0 = fade(t, 0.6, 0.8)
        full = fade(t, tsw, 0.6) if tsw is not None else 0
        for k, ch in enumerate(phrase):
            col_a = a0 * (0.45 + 0.55 * full)
            if k == 2:
                gone = fade(t, tsw, 0.5) if tsw is not None else 0
                blit(cv, glyph(ch, "kai_m", self.size, INK), x, self.cy(k), col_a * (1 - gone), anchor="mm")
                if tsw is not None:
                    gk = gfx.clamp((t - tsw - 0.5) / 0.8)
                    blit(cv, ink_reveal(glyph(p["swap"], "kai_m", self.size, RED), gk, seed=231), x, self.cy(k),
                         anchor="mm")
                    blit(cv, gfx.circle_mark(126, RED, 3), x, self.cy(k), fade(t, tsw + 1.2, 0.4), anchor="mm")
            else:
                blit(cv, glyph(ch, "kai_m", self.size, INK), x, self.cy(k), col_a, anchor="mm")
        if tsw is not None:
            reveal_text(cv, t, tsw + 1.0, text(key, "serif_sb", 32, RED, spacing=4), x, 650, anchor="mt")
            reveal_text(cv, t, tsw + 1.15, text(desc, "kai", 34, INK2), x, 702, anchor="mt")
        else:
            blit(cv, text("？", "serif_sb", 40, INK3), x, 650, a0, anchor="mt")
        tr = self.cue("rule")
        if tr is not None:
            k = fade(t, tr, 0.8)
            if k > 0:
                line = gfx.brush_line(1300, 3, INK3, seed=8)
                blit(cv, line.crop((0, 0, max(1, int(line.width * k)), line.height)), 310, 782, 0.8)
            reveal_text(cv, t, tr + 0.3, text(p["rule"], "kai_m", 48, INK, spacing=4), 960, 810, anchor="mt")


# ---------- 其三：落点 ----------

class Landing(Scene):
    CW, CH = 760, 190

    def card(self, label, line):
        im = gfx.rounded_box(self.CW, self.CH, fill=(255, 252, 244, 150), outline=INK3 + (200,), width=2, radius=14)
        im.alpha_composite(text(label, "serif", 28, INK3, spacing=4), (40, 28))
        im.alpha_composite(text(line, "kai_m", 46, INK), (40, 90))
        return im

    def setup(self):
        p = self.p
        self.cl = self.card(*p["late"])
        self.cf = self.card(*p["free"])
        self.vessel = Vessel(340, thick=8)

    def draw(self, cv, t):
        p = self.p
        section(cv, t, 0.15, "三", p["section"])
        td = self.cue("dao")
        reveal_text(cv, t, td, text(p["dao"], "kai_m", 96, INK, spacing=8), 150, 196)
        reveal_text(cv, t, None if td is None else td + 1.6, text(p["heshang"], "kai", 38, INK2), 154, 336)
        reveal_text(cv, t, None if td is None else td + 2.0, text(p["heshang_src"], "serif", 26, INK3), 158, 394)
        # 右上：一只始终没有画完的器
        pv = 0.86 * ease_out(gfx.clamp((t - 0.6) / 9.0))
        blit(cv, self.vessel.image(pv), 1545, 110, fade(t, 0.4, 0.6), anchor="mt")
        reveal_text(cv, t, 8.0, text(p["vessel_note"], "serif", 26, INK3, spacing=6), 1545, 462, anchor="mt")
        tt = self.cue("two")
        reveal_text(cv, t, tt, text(p["two"], "kai_m", 44, INK), 180, 470)
        reveal_text(cv, t, self.cue("late"), self.cl, 180, 550)
        reveal_text(cv, t, self.cue("free"), self.cf, 980, 550)
        tm = self.cue("modern")
        if tm is not None:
            k = fade(t, tm, 0.7)
            if k > 0:
                blit(cv, gfx.rounded_box(6, 60, fill=RED + (255,), radius=3), 180, 790, k)
            reveal_text(cv, t, tm + 0.15, text(p["modern"], "kai", 40, INK2), 208, 784)
