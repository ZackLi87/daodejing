"""第 01 期专用场景：水就低处、七善、不争之落点。"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from dao import gfx
from dao.config import INK, INK2, INK3, RED, WATER, WATER_L
from dao.gfx import blit, ease_out, fade, glyph, ink_reveal, seal, text
from dao.scenes import Scene, reveal_text, section


# ---------- 其一：处众人之所恶 ----------

class WaterLow(Scene):
    """左：要句与引文；右：山势剖面，水自高处流下，汇于谷底。"""

    PX, PY, PW, PH = 1000, 190, 800, 690       # 插图区域

    # 山势剖面控制点 (u, y)：左侧高峰，逐级下降，右侧为宽阔低地，边缘略有回升
    CTRL = [(0.00, 160), (0.07, 108), (0.16, 165), (0.26, 245), (0.34, 280), (0.44, 380), (0.54, 488),
            (0.64, 552), (0.74, 572), (0.84, 548), (0.93, 475), (1.00, 435)]

    def setup(self):
        PW, PH = self.PW, self.PH
        xs = np.arange(-200, PW + 201, dtype=float)
        us, ys = zip(*self.CTRL)
        raw = np.interp(xs / PW, us, ys)
        k = np.exp(-0.5 * (np.arange(-90, 91) / 28.0) ** 2)
        smooth = np.convolve(raw, k / k.sum(), mode="same")
        self.ys = smooth[200:200 + PW + 1] + 5 * np.sin(np.arange(PW + 1) / 23.0) * np.exp(-np.arange(PW + 1) / 400)
        self.vx = int(np.argmax(self.ys))                # 谷底
        self.peak = int(np.argmin(self.ys[: PW // 3]))
        edge = np.clip(np.minimum(np.arange(PW), PW - 1 - np.arange(PW)) / 90.0, 0, 1)   # 左右边缘渐隐
        sc = 2
        # 山体：自地面向下渐淡的墨晕
        m = Image.new("L", (PW * sc, PH * sc), 0)
        d = ImageDraw.Draw(m)
        pts = [(x * sc, self.ys[x] * sc) for x in range(0, PW + 1, 2)] + [(PW * sc, PH * sc), (0, PH * sc)]
        d.polygon(pts, fill=255)
        m = m.resize((PW, PH), Image.LANCZOS)
        yy = np.arange(PH)[:, None].astype(np.float32)
        depth = np.clip((yy - self.ys[None, :PW]) / 230, 0, 1)
        bottom = np.clip((PH - yy) / 120, 0, 1)
        wash = np.asarray(m, np.float32) / 255 * 0.30 * (1 - depth) ** 1.6 * edge[None, :] * bottom
        hill = Image.new("RGBA", (PW, PH), INK2 + (0,))
        hill.putalpha(Image.fromarray((wash * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)))
        # 山脊墨线（粗细起伏）
        ridge = Image.new("L", (PW * sc, PH * sc), 0)
        d = ImageDraw.Draw(ridge)
        rng = np.random.default_rng(3)
        for x in range(0, PW + 1):
            r = (2.0 + 1.6 * math.sin(x / 37) ** 2 + 0.5 * rng.random()) * sc
            cx, cy = x * sc, self.ys[x] * sc
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
        ridge = np.asarray(ridge.resize((PW, PH), Image.LANCZOS), np.float32) * 0.9 * edge[None, :]
        line = Image.new("RGBA", (PW, PH), INK + (0,))
        line.putalpha(Image.fromarray(ridge.astype(np.uint8)))
        hill.alpha_composite(line)
        self.hill = hill
        # 两条水路：左侧高峰 → 谷底；右侧边坡 → 谷底
        self.paths = [np.arange(self.peak + 20, self.vx + 1), np.arange(PW - 60, self.vx - 1, -1)]
        # 满水位时水面的左右端，用于放置标注
        rim = max(self.ys[:self.vx].min(), self.ys[self.vx:].min())
        wet = np.where(self.ys > rim + 30)[0]
        self.sea_x = (wet.min() + wet.max()) / 2
        self.sea_y = rim + 30 - 34          # 标注置于满水位水面之上

    def water_layer(self, t, fill_k, flow_k):
        PW, PH = self.PW, self.PH
        sc = 2
        im = Image.new("RGBA", (PW * sc, PH * sc), (0, 0, 0, 0))
        d = ImageDraw.Draw(im, "RGBA")
        # 水道：沿地面的细水线
        for path in self.paths:
            n = int(len(path) * flow_k)
            if n > 2:
                pts = [(x * sc, (self.ys[x] - 3) * sc) for x in path[:n:3]]
                d.line(pts, fill=WATER + (150,), width=3 * sc, joint="curve")
        # 水滴
        if flow_k > 0:
            for pi, path in enumerate(self.paths):
                for j in range(9):
                    ph = (t * 0.22 + j / 9 + pi * 0.37) % 1.0
                    s = ph ** 1.6                                  # 越往下越快
                    if s > flow_k:
                        continue
                    x = path[int(s * (len(path) - 1))]
                    y = self.ys[x] - 7
                    r = (3.2 + 1.5 * math.sin(j)) * sc
                    d.ellipse((x * sc - r * 1.3, y * sc - r, x * sc + r * 1.3, y * sc + r), fill=WATER + (190,))
        # 谷中积水
        if fill_k > 0:
            bottom = self.ys[self.vx]
            # 右侧回升处的最高点决定能蓄水的最高水位
            rim = max(self.ys[:self.vx].min(), self.ys[self.vx:].min())
            top = bottom - (bottom - rim - 30) * fill_k
            l = self.vx
            while l > 0 and self.ys[l - 1] > top:
                l -= 1
            r = self.vx
            while r < PW and self.ys[r + 1] > top:
                r += 1
            pts = []
            for x in range(l, r + 1):
                wave = 1.6 * math.sin(x / 11 + t * 2.2)
                pts.append((x * sc, (top + wave) * sc))
            for x in range(r, l - 1, -1):
                pts.append((x * sc, self.ys[x] * sc))
            if len(pts) > 4:
                d.polygon(pts, fill=WATER + (120,))
                d.line(pts[: r - l + 1], fill=WATER_L + (230,), width=3 * sc)
        return im.resize((PW, PH), Image.LANCZOS)

    def draw(self, cv, t):
        p = self.p
        section(cv, t, 0.15, "一", p["section"])
        # 左侧文字
        tq = self.cue("phrase")
        x0 = 150
        ty = 230
        reveal_text(cv, t, tq, text(p["phrase"], "kai_m", 84, INK, spacing=4), x0, ty)
        tp = self.clause_t("phrase", 1)
        if tp is not None:
            # 『恶』上方注音
            idx = p["phrase"].index("恶")
            cw = gfx.text_width(p["phrase"][:idx], "kai_m", 84, 4) + 4
            reveal_text(cv, t, tp + 0.6, text("wù", "serif", 30, RED), x0 + cw + 42, ty - 26, anchor="mt")
            k = fade(t, tp + 0.6, 0.5)
            if k > 0:
                blit(cv, gfx.circle_mark(104, RED, 3), x0 + cw + 42, ty + 60, k, anchor="mm")
        th = self.cue("heshang")
        reveal_text(cv, t, th, text(p["heshang"], "kai", 38, INK2), x0, 392)
        reveal_text(cv, t, None if th is None else th + 0.4, text(p["heshang_src"], "serif", 26, INK3), x0 + 4, 450)
        t66 = self.cue("ch66")
        reveal_text(cv, t, t66, text(p["ch66"], "kai", 40, INK), x0, 540)
        reveal_text(cv, t, None if t66 is None else t66 + 0.4, text(p["ch66_src"], "serif", 26, INK3), x0 + 4, 600)
        tm = self.cue("modern")
        if tm is not None:
            k = fade(t, tm, 0.7)
            if k > 0:
                bar = gfx.rounded_box(6, 128, fill=RED + (255,), radius=3)
                blit(cv, bar, x0, 700, k)
            for j, line in enumerate(p["modern"]):
                reveal_text(cv, t, tm + 0.15 + j * 0.35, text(line, "kai_m", 40, INK), x0 + 28, 700 + j * 66)

        # 右侧插图
        a = fade(t, 0.3, 1.0)
        blit(cv, self.hill, self.PX, self.PY, a)
        flow_k = gfx.clamp((t - 1.0) / 6.0)
        fill_k = 0.15 + 0.85 * gfx.clamp((t - 4.0) / max(6.0, (self.cue("ch66") or 12) + 4 - 4.0))
        fill_k = ease_out(fill_k) if t > 4 else 0
        blit(cv, self.water_layer(t, fill_k, ease_out(flow_k)), self.PX, self.PY, a)
        # 标注
        lab = lambda s, c=INK2: text(s, "kai", 34, c)
        reveal_text(cv, t, 1.5, lab(p["label_high"], INK3), self.PX + self.peak, self.PY + self.ys[self.peak] - 40,
                    anchor="mb")
        vy = self.PY + self.ys[self.vx]
        reveal_text(cv, t, 3.0, lab(p["label_low"], WATER), self.PX + self.vx, vy + 36, anchor="mt")
        if t66 is not None:
            reveal_text(cv, t, t66 + 1.0, text(p["label_sea"], "kai_m", 34, RED), self.PX + self.sea_x,
                        self.PY + self.sea_y, anchor="mm")


# ---------- 其二：七善 ----------

class Seven(Scene):
    """七句『善』自右向左竖排，随朗读显现；其下依次给出今译。"""

    def setup(self):
        self.items = self.p["items"]
        self.size = 78
        self.xs = [1640 - i * 216 for i in range(len(self.items))]
        self.y0 = 220

    def draw(self, cv, t):
        p = self.p
        section(cv, t, 0.15, "二", p["section"])
        sr = self.seg("read")
        sg = self.seg("gloss")
        reads = [sr.t0 + c[1] for c in sr.clauses]
        gloss = [sg.t0 + c[1] for c in sg.clauses]
        while len(reads) < len(self.items):
            reads.append(reads[-1])
        while len(gloss) < len(self.items):
            gloss.append(gloss[-1])
        for i, (phrase, key, desc) in enumerate(self.items):
            x = self.xs[i]
            for k, ch in enumerate(phrase):
                g = glyph(ch, "kai_m", self.size, RED if ch == "善" else INK)
                kk = gfx.clamp((t - reads[i] - k * 0.12) / 0.6)
                blit(cv, ink_reveal(g, kk, seed=100 + i * 3 + k), x, self.y0 + k * self.size * 1.14 + self.size / 2,
                     anchor="mm")
            ta = gloss[i]
            reveal_text(cv, t, ta, text(key, "serif_sb", 30, RED, spacing=4), x, 530, anchor="mt")
            reveal_text(cv, t, ta + 0.15, text(desc, "kai", 34, INK2), x, 580, anchor="mt")
        tl = self.cue("rule")
        if tl is not None:
            k = fade(t, tl, 0.8)
            if k > 0:
                line = gfx.brush_line(1360, 3, INK3, seed=8)
                blit(cv, line.crop((0, 0, max(1, int(line.width * k)), line.height)), 280, 672, 0.8)
            reveal_text(cv, t, tl + 0.3, text(p["rule"], "kai_m", 56, INK, spacing=4), 960, 712, anchor="mt")
        tm = self.cue("modern")
        reveal_text(cv, t, tm, text(p["modern"], "kai", 42, RED, spacing=2), 960, 808, anchor="mt")


# ---------- 其三：不争之落点 ----------

class Contrast(Scene):
    """左卡：常被引用的『故天下莫能与之争』（第二十二章）；右卡：第八章『故无尤』。"""

    CW, CH = 700, 290

    def card(self, label, lines, hi=None):
        im = gfx.rounded_box(self.CW, self.CH, fill=(255, 252, 244, 150), outline=INK3 + (200,), width=2, radius=14)
        im.alpha_composite(text(label, "serif", 28, INK3, spacing=4), (40, 30))
        for j, ln in enumerate(lines):
            if hi and hi in ln:
                a, b = ln.split(hi, 1)
                spr = gfx.rich([(a, "kai_m", INK), (hi, "kai_m", RED), (b, "kai_m", INK)], 54)
            else:
                spr = text(ln, "kai_m", 54, INK)
            im.alpha_composite(spr, (40, 92 + j * 84))
        return im

    def setup(self):
        p = self.p
        self.c22 = self.card(p["c22_label"], p["c22_lines"])
        self.c8 = self.card(p["c8_label"], p["c8_lines"], hi=p["c8_hi"])
        self.stamp = self.make_stamp(p["stamp"])

    def make_stamp(self, s):
        size = 34
        w = int(gfx.text_width(s, "serif_sb", size, 4)) + 44
        h = 70
        im = gfx.rounded_box(w, h, outline=RED + (230,), width=3, radius=6)
        im.alpha_composite(text(s, "serif_sb", size, RED, spacing=4), (20, 10))
        return im.rotate(8, resample=Image.BICUBIC, expand=True)

    def draw(self, cv, t):
        p = self.p
        section(cv, t, 0.15, "三", p["section"])
        xl, xr, y = 180, 1040, 200
        t22 = self.cue("c22")
        reveal_text(cv, t, t22, self.c22, xl, y)
        ts = self.cue("stamp")
        if ts is not None:
            k = fade(t, ts + 0.3, 0.25)
            blit(cv, self.stamp, xl + self.CW - 165, y + 128, k, anchor="mm",
                 scale=1 + 0.35 * (1 - ease_out((t - ts - 0.3) / 0.25)))
        t8 = self.cue("c8")
        reveal_text(cv, t, t8, self.c8, xr, y)
        # 下方：先释『尤』并引河上公注，再作取舍对照
        tn = self.cue("note")
        tc = self.cue("not")
        out = 1 - fade(t, tc, 0.5) if tc is not None else 1.0
        if tn is not None and out > 0:
            reveal_text(cv, t, tn, gfx.rich([("尤", "kai_m", RED), ("：过失、怨咎", "kai", INK)], 44), 180, 560, a=out)
            reveal_text(cv, t, tn + 1.2, text(p["heshang"], "kai", 40, INK2), 180, 650, a=out)
            reveal_text(cv, t, tn + 1.6, text(p["heshang_src"], "serif", 26, INK3), 186, 712, a=out)
        if tc is not None:
            k = fade(t, tc + 0.3, 0.6)
            if k > 0:
                spr = text(p["not_"], "kai", 44, INK3)
                blit(cv, text("不是", "serif_sb", 34, INK3), 180, 600, k, anchor="lm")
                blit(cv, spr, 296, 600, k, anchor="lm")
                kk = ease_out((t - tc - 0.9) / 0.6)
                if kk > 0:
                    strike = gfx.brush_line(int((spr.width - 8) * kk) + 1, 3, INK3, seed=6, taper=False)
                    blit(cv, strike, 300, 600, k, anchor="lm")
            tb = self.cue("but")
            reveal_text(cv, t, tb, text("而是", "serif_sb", 34, RED), 180, 690, anchor="lm")
            reveal_text(cv, t, tb, text(p["but"], "kai_m", 48, INK), 296, 690, anchor="lm")
        tm = self.cue("modern")
        if tm is not None:
            k = fade(t, tm, 0.7)
            if k > 0:
                blit(cv, gfx.rounded_box(6, 60, fill=RED + (255,), radius=3), 180, 772, k)
            reveal_text(cv, t, tm + 0.15, text(p["modern"], "kai", 40, INK2), 208, 766)


def cover_art():
    """封面插图：满水位的山势剖面。"""
    s = WaterLow.__new__(WaterLow)
    s.setup()
    im = s.hill.copy()
    im.alpha_composite(s.water_layer(1.3, 1.0, 1.0))
    return im
