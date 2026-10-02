"""通用场景：片头引入、标题、原文竖排、小结、片尾。各期专用的插图场景放在 episodes/epXX/scenes.py。"""
import math

import numpy as np
from PIL import Image

from . import gfx
from .config import INK, INK2, INK3, RED, WATER, W
from .gfx import PUNCT, blit, ease_out, fade, glyph, ink_reveal, seal, text


class Scene:
    def __init__(self, shot):
        self.sh = shot
        self.p = shot.p
        self.segs = shot.segs
        self.dur = shot.dur
        self.setup()

    def setup(self):
        pass

    def seg(self, cue):
        for s in self.segs:
            if s.cue == cue:
                return s
        raise KeyError(cue)

    def cue(self, name):
        """某句旁白开始的时刻（场景内时间）；name 为 None 返回 None。"""
        if name is None:
            return None
        return self.seg(name).t0

    def clause_t(self, cue, k):
        s = self.seg(cue)
        k = min(k, len(s.clauses) - 1)
        return s.t0 + s.clauses[k][1]

    def draw(self, cv, t):
        raise NotImplementedError


# ---------- 公共元件 ----------

class Ripples:
    """水面涟漪：一组扁椭圆环由中心向外扩散并渐隐。"""

    def __init__(self, rx, ry, count=3, period=6.0, color=WATER, alpha=0.35, width=2.2):
        self.rx, self.ry, self.count, self.period = rx, ry, count, period
        self.color, self.alpha, self.width = color, alpha, width
        yy, xx = np.mgrid[-ry:ry, -rx:rx].astype(np.float32)
        self.d = np.sqrt(xx ** 2 + (yy * rx / ry) ** 2)

    def draw(self, cv, t, cx, cy, a=1.0):
        if a <= 0:
            return
        acc = np.zeros_like(self.d)
        for i in range(self.count):
            ph = (t / self.period + i / self.count) % 1.0
            r = ph * self.rx
            k = (1 - ph) ** 1.6 * min(1.0, ph * 8)
            acc = np.maximum(acc, k * np.exp(-((self.d - r) / self.width) ** 2))
        alpha = np.clip(acc * 255 * self.alpha * a, 0, 255).astype(np.uint8)
        im = Image.new("RGBA", (alpha.shape[1], alpha.shape[0]), self.color + (0,))
        im.putalpha(Image.fromarray(alpha))
        blit(cv, im, cx, cy, 1.0, anchor="mm")


def section(cv, t, t0, num, title, x=140, y=96):
    """小节标题：朱印数字 + 『第 N 层 · 标题』。"""
    a = fade(t, t0, 0.6)
    if a <= 0:
        return
    s = seal(num, 66, seed=11)
    blit(cv, s, x, y, a, scale=1 + 0.2 * (1 - ease_out((t - t0) / 0.35)))
    lab = gfx.rich([(f"第{num}层  ", "serif", INK3), (title, "serif_sb", INK)], 44)
    blit(cv, lab, x + 90, y + 33 - 4 * (1 - a), a, anchor="lm")


def reveal_text(cv, t, t0, im, x, y, anchor="lt", dur=0.7, rise=10, a=1.0):
    k = fade(t, t0, dur)
    if k > 0:
        blit(cv, im, x, y + rise * (1 - k), k * a, anchor=anchor)


# ---------- 片头引入 ----------

class Hook(Scene):
    """大字竖排名句（水墨显字）+ 左侧『常见理解』与转折。"""

    def setup(self):
        p = self.p
        self.size = 150
        self.lay, self.h = gfx.vlayout(p["quote"], self.size, step=1.12)
        self.x, self.y0 = 1250, 150
        self.rip = Ripples(560, 120, count=3, period=7.0, alpha=0.30)

    def draw(self, cv, t):
        p = self.p
        self.rip.draw(cv, t, self.x, self.y0 + self.h + 70, a=fade(t, 0.2, 1.5))
        for i, (ch, dy) in enumerate(self.lay):
            g = glyph(ch, "kai_m", self.size, INK)
            k = gfx.clamp((t - 0.4 - i * 0.45) / 1.2)
            blit(cv, ink_reveal(g, k, seed=i + 1), self.x, self.y0 + dy + self.size / 2, anchor="mm")
        ts = 0.4 + len(self.lay) * 0.45 + 0.5
        sz = 72
        blit(cv, seal(p.get("seal", "老子"), sz, seed=5), self.x - 165, self.y0 + self.h - sz + 6,
             fade(t, ts, 0.3), scale=1 + 0.25 * (1 - ease_out((t - ts) / 0.3)))

        tc, tb = self.cue(p.get("common_cue")), self.cue(p.get("but_cue"))
        dim = 1 - 0.55 * fade(t, tb, 0.6) if tb is not None else 1
        x0, y0 = 250, 380
        reveal_text(cv, t, tc, text(p["common_label"], "serif", 30, INK3, spacing=6), x0, y0, a=dim)
        for j, line in enumerate(p["common_lines"]):
            reveal_text(cv, t, None if tc is None else tc + 0.25 + j * 0.3,
                        text(line, "kai", 56, INK2), x0, y0 + 60 + j * 84, a=dim)
        if tb is not None:
            yb = y0 + 60 + len(p["common_lines"]) * 84 + 60
            k = fade(t, tb + 0.8, 0.8)
            reveal_text(cv, t, tb + 0.8, text(p["but_text"], "kai_m", 56, RED), x0, yb)
            if k > 0:
                line = gfx.brush_line(int(gfx.text_width(p["but_text"], "kai_m", 56) + 20), 5, RED, seed=4)
                blit(cv, line.crop((0, 0, max(1, int(line.width * ease_out((t - tb - 1.1) / 0.7))), line.height)),
                     x0, yb + 84, k)


# ---------- 标题 ----------

class Title(Scene):
    def draw(self, cv, t):
        p = self.p
        cx = W / 2
        reveal_text(cv, t, 0.2, gfx.rich([(p["series"] + "  ·  ", "serif_sb", INK2),
                                          (p["num"], "serif_bk", RED)], 40, spacing=0), cx, 300, anchor="mt")
        k = fade(t, 0.5, 0.9)
        if k > 0:
            line = gfx.brush_line(420, 4, INK, seed=2)
            blit(cv, line.crop((0, 0, max(1, int(line.width * k)), line.height)), cx - 210, 372, 0.85)
        title = p["title"]
        size = 128
        step = size * 1.08
        x0 = cx - step * len(title) / 2 + step / 2
        for i, ch in enumerate(title):
            g = glyph(ch, "kai_m", size, INK)
            kk = gfx.clamp((t - 0.6 - i * 0.22) / 0.9)
            blit(cv, ink_reveal(g, kk, seed=20 + i), x0 + i * step, 500, anchor="mm")
        ts = 0.6 + len(title) * 0.22 + 0.5
        blit(cv, seal(p.get("seal", "细读"), 76, seed=9), x0 + len(title) * step - step / 2 + 30, 462,
             fade(t, ts, 0.3), scale=1 + 0.25 * (1 - ease_out((t - ts) / 0.3)))
        reveal_text(cv, t, 1.3, text(p["subtitle"], "serif", 46, INK2), cx, 610, anchor="mt")
        reveal_text(cv, t, 1.7, text(p["source"], "serif", 28, INK3, spacing=4), cx, 700, anchor="mt")


# ---------- 原文竖排 ----------

class Original(Scene):
    """原文自右向左竖排，随朗读逐字显现；随后以旁圈标出要点并在左侧列出提要。"""

    def setup(self):
        p = self.p
        self.size = p.get("size", 62)
        self.colstep = p.get("colstep", 104)
        self.x_right = p.get("x_right", 1700)
        self.y0 = p.get("y0", 190)
        # 朗读时刻流
        stream = []
        for cue in p["read"]:
            s = self.seg(cue)
            stream += [(ch, s.t0 + tt) for ch, tt in s.chars]
        self.items = []     # (列号, 字序, 字, x, y, 时刻)
        si = 0
        last_t = 0.0
        ctx = p.get("context", {})
        self.ctx_cols = set(ctx.get("cols", []))
        for ci, col in enumerate(p["columns"]):
            lay, _ = gfx.vlayout(col, self.size, step=1.14, punct_step=0.6)
            x = self.x_right - ci * self.colstep
            if ci in self.ctx_cols:
                s = self.seg(ctx["cue"])
                order = sorted(self.ctx_cols).index(ci)
                t0 = s.t0 + s.dur * 0.8 * order / len(self.ctx_cols)
                for k, (ch, dy) in enumerate(lay):
                    self.items.append((ci, k, ch, x, self.y0 + dy + self.size / 2, t0 + k * 0.06))
                continue
            for k, (ch, dy) in enumerate(lay):
                tt = last_t
                if ch not in PUNCT:
                    while si < len(stream) and stream[si][0] != ch:
                        si += 1
                    if si < len(stream):
                        tt = stream[si][1]
                        si += 1
                    last_t = tt
                self.items.append((ci, k, ch, x, self.y0 + dy + self.size / 2, tt))
        self.marks = {}
        for gi, (num, spans) in enumerate(p.get("groups", [])):
            for ci, a, b in spans:
                for k in range(a, b):
                    self.marks[(ci, k)] = gi

    def draw(self, cv, t):
        p = self.p
        # 左侧题签
        reveal_text(cv, t, 0.2, text(p["book"], "serif_sb", 40, INK2, spacing=4), 150, 180)
        reveal_text(cv, t, 0.45, text(p["chapter"], "kai_m", 76, INK), 150, 238)
        reveal_text(cv, t, 0.7, text(p["edition"], "serif", 26, INK3, spacing=3), 154, 356)

        tg = self.cue(p.get("group_cue"))
        if tg is not None and p.get("group_clause") is not None:
            tg = self.clause_t(p["group_cue"], p["group_clause"])
        focus = fade(t, tg, 0.8) if tg is not None else 0
        for ci, k, ch, x, y, tt in self.items:
            kk = gfx.clamp((t - tt + 0.05) / 0.6)
            if kk <= 0:
                continue
            gi = self.marks.get((ci, k))
            col = INK
            a = 1.0
            if focus > 0:
                a = 1 - 0.62 * focus if gi is None else 1.0
            if ci in self.ctx_cols:
                a = min(a, 0.5)
            g = glyph(ch, "kai", self.size, col)
            blit(cv, ink_reveal(g, kk, seed=ci * 31 + k), x, y, a, anchor="mm")
            if gi is not None and ch not in PUNCT and focus > 0:
                ta = tg + 0.45 * gi
                m = fade(t, ta, 0.4)
                blit(cv, gfx.circle_mark(13, RED, 2), x - self.size * 0.60, y, m, anchor="mm")
        # 注音
        for ci, ch, py in p.get("pinyin", []):
            for cj, k, c2, x, y, tt in self.items:
                if cj == ci and c2 == ch:
                    blit(cv, text(py, "serif", 23, RED), x + self.size * 0.52, y, fade(t, tt + 0.5, 0.5), anchor="lm")
                    break
        # 要点编号与提要
        if focus > 0:
            for gi, (num, spans) in enumerate(p["groups"]):
                ta = tg + 0.45 * gi
                ci = spans[0][0]
                x = self.x_right - ci * self.colstep
                blit(cv, seal(num, 46, seed=40 + gi), x, self.y0 - 42, fade(t, ta, 0.35), anchor="mm",
                     scale=1 + 0.25 * (1 - ease_out((t - ta) / 0.35)))
            for gi, (num, label, src) in enumerate(p["legend"]):
                ta = tg + 0.45 * gi + 0.2
                y = 470 + gi * 92
                reveal_text(cv, t, ta, gfx.rich([(num + "  ", "serif_sb", RED), (label + "  ", "serif_sb", INK),
                                                 (src, "kai", INK2)], 34), 150, y)


# ---------- 小结 ----------

class Summary(Scene):
    def draw(self, cv, t):
        p = self.p
        cx = W / 2
        reveal_text(cv, t, 0.2, text(p["kicker"], "serif", 30, INK3, spacing=6), cx, 120, anchor="mt")
        reveal_text(cv, t, 0.4, text(p["heading"], "kai_m", 78, INK, spacing=8), cx, 168, anchor="mt")
        s = self.seg(p["rows_cue"])
        x0 = 470
        ks = p.get("row_clauses", range(len(p["rows"])))
        for i, ((num, label, main, src), k) in enumerate(zip(p["rows"], ks)):
            ta = s.t0 + s.clauses[min(k, len(s.clauses) - 1)][1]
            y = 330 + i * 150
            a = fade(t, ta, 0.6)
            if a <= 0:
                continue
            blit(cv, seal(num, 60, seed=60 + i), x0, y + 34, a, anchor="mm",
                 scale=1 + 0.25 * (1 - ease_out((t - ta) / 0.35)))
            blit(cv, text(label, "serif_sb", 40, INK2, spacing=4), x0 + 60, y + 34, a, anchor="lm")
            blit(cv, text(main, "kai_m", 64, INK, spacing=6), x0 + 240, y + 30 - 8 * (1 - a), a, anchor="lm")
            blit(cv, text(src, "kai", 30, INK3), x0 + 620, y + 34, fade(t, ta + 0.3, 0.6), anchor="lm")
        tf = self.cue(p.get("foot_cue"))
        if tf is not None:
            reveal_text(cv, t, tf + 0.2, text(p["foot"], "kai", 42, RED), cx, 800, anchor="mt")


# ---------- 片尾 ----------

class Outro(Scene):
    """下期预告：竖排名句，其中一字被圈出并在旁标出异文；随后给出留言邀请。"""

    def setup(self):
        self.size = 124
        self.lay, self.h = gfx.vlayout(self.p["next_quote"], self.size, step=1.12)
        self.x, self.y0 = 1330, 170

    def draw(self, cv, t):
        p = self.p
        reveal_text(cv, t, 0.2, text(p["next_label"], "serif", 32, INK3, spacing=8), 250, 300)
        reveal_text(cv, t, 0.5, text(p["next_title"], "kai_m", 58, INK), 250, 356)
        for i, (ch, dy) in enumerate(self.lay):
            g = glyph(ch, "kai_m", self.size, INK)
            k = gfx.clamp((t - 0.5 - i * 0.3) / 1.0)
            blit(cv, ink_reveal(g, k, seed=70 + i), self.x, self.y0 + dy + self.size / 2, anchor="mm")
        tv = self.cue(p.get("variant_cue"))
        if tv is not None:
            idx, alt, note = p["variant"]
            a, b = idx if isinstance(idx, tuple) else (idx, idx)
            ya = self.y0 + self.lay[a][1] + self.size / 2
            yb = self.y0 + self.lay[b][1] + self.size / 2
            y = (ya + yb) / 2
            k = fade(t, tv + 0.6, 0.5)
            if k > 0:
                d = int(self.size * 1.35)
                ring = gfx.circle_mark(d, RED, 4) if a == b else \
                    gfx.ring_box(d, int(yb - ya) + d, RED, 4)
                blit(cv, ring, self.x, y, k, anchor="mm", scale=1 + 0.15 * (1 - k))
            gk = gfx.clamp((t - tv - 1.2) / 1.0)
            if len(alt) == 1:
                blit(cv, ink_reveal(glyph(alt, "kai_m", 96, RED), gk, seed=91), self.x + 190, y, anchor="mm")
                ny = y + 74
            else:
                sz = 72
                y1 = y - sz * 1.08 * len(alt) / 2
                for j, ch in enumerate(alt):
                    kk = gfx.clamp((t - tv - 1.2 - j * 0.15) / 0.8)
                    blit(cv, ink_reveal(glyph(ch, "kai_m", sz, RED), kk, seed=91 + j), self.x + 175,
                         y1 + (j + 0.5) * sz * 1.08, anchor="mm")
                ny = y1 + len(alt) * sz * 1.08 + 16
            reveal_text(cv, t, tv + 1.6, text(note, "serif", 26, RED, spacing=4), self.x + 175, ny, anchor="mt")
        tc = self.cue(p.get("cta_cue"))
        if tc is not None:
            for j, line in enumerate(p["cta"]):
                reveal_text(cv, t, tc + 0.2 + j * 0.5, text(line, "kai", 44, INK if j == 0 else INK2), 250,
                            560 + j * 74)
            ts = tc + 1.4
            blit(cv, seal(p.get("seal", "细读"), 84, seed=9), 250, 760, fade(t, ts, 0.3),
                 scale=1 + 0.25 * (1 - ease_out((t - ts) / 0.3)))
            reveal_text(cv, t, ts + 0.2, text(p["series"], "serif_sb", 34, INK2, spacing=8), 356, 802, anchor="lm")
