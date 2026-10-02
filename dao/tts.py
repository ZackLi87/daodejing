"""逐句配音：调用 MiniMax 合成、本地缓存、去除首尾静音，并按停顿对齐分句时间。"""
import hashlib
import json
import subprocess
import sys
import time

import numpy as np

from . import config as C
from .gfx import CLAUSE_END, PUNCT

sys.path.insert(0, str(C.ROOT / "tools"))
import minimax_tts  # noqa: E402  （用户提供的独立脚本）

CACHE = C.BUILD / "tts"
_key = None


def _api_key():
    global _key
    if _key is None:
        _key = minimax_tts.load_key()
    return _key


def synth(text, voice, speed, pron, model=C.TTS_MODEL):
    """合成一句并缓存为 mp3；相同参数不重复计费。返回 (路径, 本次计费字符数)。"""
    CACHE.mkdir(parents=True, exist_ok=True)
    sig = json.dumps([text, voice, speed, sorted(pron), model], ensure_ascii=False)
    out = CACHE / (hashlib.sha1(sig.encode()).hexdigest()[:16] + ".mp3")
    if out.exists():
        return out, 0
    payload = {
        "model": model, "text": text, "stream": False, "language_boost": "auto",
        "voice_setting": {"voice_id": voice, "speed": speed, "vol": 1.0, "pitch": 0},
        "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "mp3", "channel": 1},
    }
    if pron:
        payload["pronunciation_dict"] = {"tone": list(pron)}
    for attempt in range(6):
        res = minimax_tts.post(C.TTS_HOST, "/v1/t2a_v2", _api_key(), payload)
        code = res.get("base_resp", {}).get("status_code", 0)
        if code == 0 and res.get("data", {}).get("audio"):
            break
        if code == 1002 and attempt < 5:      # 请求过于频繁
            time.sleep(2 ** attempt * 2)
            continue
        raise RuntimeError(f"配音失败（{code}）：{res.get('base_resp', {}).get('status_msg')}  文本：{text}")
    out.write_bytes(bytes.fromhex(res["data"]["audio"]))
    return out, res.get("extra_info", {}).get("usage_characters") or 0


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(C.SR), "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def _env_db(x, hop=0.01):
    n = int(C.SR * hop)
    m = len(x) // n
    rms = np.sqrt(np.mean(x[:m * n].reshape(m, n) ** 2, axis=1) + 1e-12)
    return 20 * np.log10(rms / (rms.max() + 1e-12))


def trim(x, thresh=-42, keep=0.04):
    db = _env_db(x)
    on = np.where(db > thresh)[0]
    if len(on) == 0:
        return x
    n = int(C.SR * 0.01)
    a = max(0, on[0] * n - int(keep * C.SR))
    b = min(len(x), (on[-1] + 1) * n + int(keep * C.SR))
    out = x[a:b].copy()
    fl = int(0.01 * C.SR)
    out[:fl] *= np.linspace(0, 1, fl)
    out[-fl:] *= np.linspace(1, 0, fl)
    return out


def clauses(s):
    """按句读切分：返回 [(分句文字, 有效字数)]。"""
    out, cur = [], ""
    for ch in s:
        cur += ch
        if ch in CLAUSE_END:
            out.append(cur)
            cur = ""
    if cur.strip("”’」）》 "):
        out.append(cur)
    elif cur and out:
        out[-1] += cur
    return [(c, sum(ch not in PUNCT and not ch.isspace() for ch in c)) for c in out]


def align(x, s):
    """根据音频中的停顿估计各分句起止时间（秒）。
    在候选静音段中，用动态规划为 n-1 个分界选取静音段，使各分句的语速尽量一致、所选停顿尽量明显。"""
    cl = clauses(s)
    dur = len(x) / C.SR
    n = len(cl)
    if n == 1:
        return [(cl[0][0], 0.0, dur)]
    weights = np.array([max(w, 1) for _, w in cl], float)
    db = _env_db(x)
    sil = db < -32
    runs, i = [], 0
    while i < len(sil):
        if sil[i]:
            j = i
            while j < len(sil) and sil[j]:
                j += 1
            if i > 3 and j < len(sil) - 3 and j - i >= 4:
                runs.append((i * 0.01, j * 0.01))
            i = j
        else:
            i += 1
    k, m = n - 1, len(runs)
    if m < k:
        # 停顿不足：按字数比例分配
        edges = np.concatenate([[0], np.cumsum(weights)]) / weights.sum() * dur
        return [(c, edges[i], edges[i + 1]) for i, (c, _) in enumerate(cl)]
    speech = dur - 0.3 * k
    expect = weights / weights.sum() * speech

    def cost(ci, a, b, bonus):
        d = max(b - a, 0.05)
        return np.log(d / expect[ci]) ** 2 - 0.8 * bonus

    INF = 1e18
    dp = np.full((k, m), INF)
    back = np.zeros((k, m), int)
    for q in range(m):
        dp[0, q] = cost(0, 0.0, runs[q][0], runs[q][1] - runs[q][0])
    for a in range(1, k):
        for q in range(a, m):
            best, arg = INF, -1
            for pq in range(a - 1, q):
                v = dp[a - 1, pq] + cost(a, runs[pq][1], runs[q][0], runs[q][1] - runs[q][0])
                if v < best:
                    best, arg = v, pq
            dp[a, q], back[a, q] = best, arg
    final = [dp[k - 1, q] + cost(k, runs[q][1], dur, 0) for q in range(m)]
    q = int(np.argmin(final))
    pick = [q]
    for a in range(k - 1, 0, -1):
        q = back[a, q]
        pick.append(q)
    pick.reverse()
    bounds = [runs[p] for p in pick]
    out, t0 = [], 0.0
    for idx, (c, _) in enumerate(cl):
        t1 = bounds[idx][0] if idx < k else dur
        out.append((c, t0, t1))
        if idx < k:
            t0 = bounds[idx][1]
    return out


def char_times(clause_times):
    """把每个分句的时长平均分给其中的有效字：返回 [(字, 起始时刻)]。"""
    out = []
    for c, t0, t1 in clause_times:
        chars = [ch for ch in c if ch not in PUNCT and not ch.isspace()]
        for i, ch in enumerate(chars):
            out.append((ch, t0 + (t1 - t0) * i / max(len(chars), 1)))
    return out
