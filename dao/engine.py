"""时间轴、字幕、混音与逐帧渲染。用法见 dao/build.py。"""
from dataclasses import dataclass, field
import math

import numpy as np
from PIL import Image, ImageFilter

from . import config as C
from . import gfx
from .gfx import CLAUSE_END, PUNCT

OVERLAP = 0.6       # 相邻场景交叠（溶接）时长
GAP = 0.42          # 句间停顿
INTRO_FADE = 0.6
OUTRO_FADE = 1.2


@dataclass
class S:
    """一句旁白。text：字幕显示文字；say：送去配音的文字（缺省同 text）；
    cue：供画面引用的名字；sub：字幕另行指定；gap：本句之后的停顿。"""
    text: str
    cue: str = None
    say: str = None
    speed: float = None
    gap: float = None
    sub: str = None
    # 以下由构建过程填写
    t0: float = 0.0
    dur: float = 0.0
    clauses: list = field(default_factory=list)   # [(分句, 起, 止)]，相对本句起点
    chars: list = field(default_factory=list)     # [(字, 时刻)]，相对本句起点

    @property
    def tts_text(self):
        return self.say or self.text


@dataclass
class Shot:
    """一个场景。cls：场景类；segs：旁白；lead/tail：首尾留白；p：画面参数。"""
    cls: type
    segs: list
    lead: float = 0.8
    tail: float = 0.8
    min_dur: float = 0.0
    p: dict = field(default_factory=dict)
    start: float = 0.0
    dur: float = 0.0


def layout(shots):
    t = 0.0
    for i, sh in enumerate(shots):
        sh.start = t
        cur = sh.lead
        for j, s in enumerate(sh.segs):
            s.t0 = cur
            cur += s.dur
            if j < len(sh.segs) - 1:
                cur += GAP if s.gap is None else s.gap
        sh.dur = max(cur + sh.tail, sh.min_dur)
        t += sh.dur - (OVERLAP if i < len(shots) - 1 else 0)
    return t


# ---------- 字幕 ----------

def _clean(s):
    return "".join(ch for ch in s if not ch.isspace())


def sub_chunks(seg):
    """把一句旁白切成若干条字幕：[(起, 止, 文字)]，时间相对本句起点。"""
    from .tts import clauses
    disp = clauses(seg.sub or seg.text)
    times = seg.clauses
    if len(times) != len(disp):
        # 显示文字与配音文字分句数不一致时，按字数比例分配
        tot = sum(max(w, 1) for _, w in disp)
        acc, times = 0.0, []
        for c, w in disp:
            a = acc / tot * seg.dur
            acc += max(w, 1)
            times.append((c, a, acc / tot * seg.dur))
    items = [(c, w, t0, t1) for (c, w), (_, t0, t1) in zip(disp, times)]
    # 过长的分句拆成两半
    split = []
    for c, w, t0, t1 in items:
        if w > C.SUB_MAX:
            body = c.rstrip("".join(CLAUSE_END))
            k = len(body) // 2
            # 尽量不在引号内部断开
            split.append((body[:k], k, t0, t0 + (t1 - t0) * 0.5))
            split.append((c[k:], w - k, t0 + (t1 - t0) * 0.5, t1))
        else:
            split.append((c, w, t0, t1))
    chunks, cur = [], None
    for c, w, t0, t1 in split:
        if cur and cur[1] + w <= C.SUB_MAX:
            cur = [cur[0] + c, cur[1] + w, cur[2], t1]
        else:
            if cur:
                chunks.append(cur)
            cur = [c, w, t0, t1]
    chunks.append(cur)
    out = []
    for i, (c, w, t0, t1) in enumerate(chunks):
        txt = c.strip()
        for q in "”’」）》":
            for pnc in "，。、；：":
                txt = txt.replace(pnc + q, q)
        while txt and txt[-1] in "，。、；：":
            txt = txt[:-1]
        for p in "，。、；：":
            txt = txt.replace(p, "  ")
        end = chunks[i + 1][2] if i + 1 < len(chunks) else seg.dur + 0.25
        out.append((t0, end, txt))
    return out


def subtitles(shots):
    subs = []
    for sh in shots:
        for s in sh.segs:
            for a, b, txt in sub_chunks(s):
                subs.append([sh.start + s.t0 + a, sh.start + s.t0 + b, txt])
    for i in range(len(subs) - 1):
        subs[i][1] = min(subs[i][1], subs[i + 1][0])
    return subs


def srt(subs):
    def ts(x):
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    lines = []
    for i, (a, b, txt) in enumerate(subs, 1):
        lines += [str(i), f"{ts(a)} --> {ts(b)}", " ".join(txt.split()), ""]
    return "\n".join(lines)


# ---------- 渲染 ----------

class Renderer:
    def __init__(self, shots, subs, total):
        self.shots = shots
        self.subs = subs
        self.total = total
        self.paper = gfx.make_paper()
        self.scenes = [sh.cls(sh) for sh in shots]
        self._sub_cache = {}

    def sub_sprite(self, txt):
        if txt not in self._sub_cache:
            fg = gfx.text(txt, "kai_m", C.SUB_SIZE, C.INK)
            pad = 16
            im = Image.new("RGBA", (fg.width + pad * 2, fg.height + pad * 2), (0, 0, 0, 0))
            mask = Image.new("L", im.size, 0)
            mask.paste(fg.getchannel("A"), (pad, pad))
            a = mask.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(6))
            g = Image.new("RGBA", im.size, C.PAPER + (0,))
            g.putalpha(a.point(lambda v: int(min(255, v * 1.5) * 0.85)))
            im.alpha_composite(g)
            im.alpha_composite(fg, (pad, pad))
            self._sub_cache[txt] = im
        return self._sub_cache[txt]

    def frame(self, t):
        cv = self.paper.copy()
        n = len(self.shots)
        for i, (sh, sc) in enumerate(zip(self.shots, self.scenes)):
            lt = t - sh.start
            if lt < 0 or lt >= sh.dur:
                continue
            a = 1.0
            if i > 0:
                a = min(a, gfx.ease_in_out(lt / OVERLAP))
            if i < n - 1:
                a = min(a, gfx.ease_in_out((sh.dur - lt) / OVERLAP))
            if a <= 0.001:
                continue
            if a >= 0.999:
                sc.draw(cv, lt)
            else:
                layer = Image.new("RGBA", (C.W, C.H), (0, 0, 0, 0))
                sc.draw(layer, lt)
                cv.alpha_composite(gfx.with_alpha(layer, a))
        for a0, b0, txt in self.subs:
            if a0 - 0.1 <= t < b0:
                op = min(gfx.clamp((t - a0 + 0.1) / 0.15), gfx.clamp((b0 - t) / 0.12))
                gfx.blit(cv, self.sub_sprite(txt), C.W / 2, C.SUB_Y, op, anchor="mm")
        # 片头片尾淡入淡出
        g = min(gfx.clamp(t / INTRO_FADE), gfx.clamp((self.total - t) / OUTRO_FADE))
        if g < 1:
            cv = Image.blend(self.paper, cv, g)
        return cv.convert("RGB")


_R = None


def _init_worker(shots, subs, total):
    global _R
    _R = Renderer(shots, subs, total)


def _render(i):
    try:
        return _R.frame(i / C.FPS).tobytes()
    except Exception:
        import traceback
        return f"第 {i} 帧渲染失败：\n" + traceback.format_exc()
