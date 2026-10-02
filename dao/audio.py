"""背景音：以 Karplus–Strong 拨弦合成五声音阶的稀疏琴音，加低频持续音与混响；并与人声混合。"""
import subprocess

import numpy as np

from . import config as C

# D 宫五声音阶（D E F# A B），取中低音区
NOTES = [146.83, 164.81, 185.00, 220.00, 246.94, 293.66, 329.63, 369.99, 440.00]


def pluck(freq, dur, rng, decay=0.9985, sr=C.SR):
    n = int(sr / freq)
    total = int(dur * sr)
    y = np.zeros(total + n + 1, np.float32)
    exc = rng.uniform(-1, 1, n).astype(np.float32)
    exc = np.convolve(exc, np.ones(4) / 4, mode="same")        # 柔化拨弦起音
    y[1:n + 1] = exc
    i = n + 1
    while i < len(y):
        # y[t] = decay · (y[t-n] + y[t-n-1]) / 2，按周期分块向量化
        j = min(i + n, len(y))
        y[i:j] = decay * 0.5 * (y[i - n:j - n] + y[i - n - 1:j - n - 1])
        i = j
    out = y[1:1 + total]
    env = np.minimum(1, np.arange(total) / (0.004 * sr))
    return out * env


def reverb(x, rng, seconds=2.6, wet=0.32, sr=C.SR):
    n = int(seconds * sr)
    t = np.arange(n) / sr
    ir = rng.normal(0, 1, n).astype(np.float32) * np.exp(-t / 0.55)
    ir = np.convolve(ir, np.ones(6) / 6, mode="same")           # 混响尾部略暗
    ir /= np.sqrt(np.sum(ir ** 2))
    size = 1 << int(np.ceil(np.log2(len(x) + n)))
    y = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[:len(x)]
    return (1 - wet) * x + wet * y.astype(np.float32)


def bgm(duration, seed=8, sr=C.SR):
    rng = np.random.default_rng(seed)
    total = int((duration + 1) * sr)
    out = np.zeros(total, np.float32)
    t = 1.2
    while t < duration - 3:
        k = rng.integers(1, 4)                                  # 每组 1–3 个音
        base = rng.integers(0, len(NOTES) - 2)
        for j in range(k):
            idx = int(np.clip(base + rng.integers(-2, 3), 0, len(NOTES) - 1))
            f = NOTES[idx]
            s = int((t + j * rng.uniform(0.35, 0.7)) * sr)
            note = pluck(f, 5.0, rng) * rng.uniform(0.5, 0.85)
            e = min(total, s + len(note))
            out[s:e] += note[:e - s]
            if rng.random() < 0.25:                             # 偶尔加上方五度泛音
                f5 = f * 1.5
                note = pluck(f5, 4.0, rng) * 0.3
                e = min(total, s + len(note))
                out[s:e] += note[:e - s]
        t += rng.uniform(3.2, 5.8)
    # 低频持续音（D2 + A2），缓慢起伏
    tt = np.arange(total) / sr
    drone = (np.sin(2 * np.pi * 73.42 * tt) + 0.6 * np.sin(2 * np.pi * 110.0 * tt)) * \
            (0.5 + 0.5 * np.sin(2 * np.pi * tt / 11.0)) * 0.10
    out += drone.astype(np.float32)
    out = reverb(out, rng)
    fade_in, fade_out = int(1.5 * sr), int(3.0 * sr)
    out[:fade_in] *= np.linspace(0, 1, fade_in)
    out[-fade_out:] *= np.linspace(1, 0, fade_out)
    return out[:int(duration * sr)] / (np.abs(out).max() + 1e-9)


def mix(voice, music, music_db=-25.0, duck_db=-6.0, sr=C.SR):
    """人声峰值归一后叠加背景音；人声出现时背景音再压低 duck_db。"""
    n = max(len(voice), len(music))
    v = np.zeros(n, np.float32)
    v[:len(voice)] = voice
    m = np.zeros(n, np.float32)
    m[:len(music)] = music
    v /= (np.abs(v).max() + 1e-9)
    v *= 10 ** (-1.5 / 20)
    hop = int(0.02 * sr)
    k = n // hop + 1
    env = np.array([np.abs(v[i * hop:(i + 1) * hop]).max(initial=0) for i in range(k)])
    act = (env > 0.02).astype(np.float32)
    w = int(0.6 / 0.02)                                         # 平滑 0.6 秒
    act = np.convolve(act, np.ones(w) / w, mode="same")
    gain_db = music_db + duck_db * np.clip(act * 1.5, 0, 1)
    gain = np.repeat(10 ** (gain_db / 20), hop)[:n].astype(np.float32)
    return v + m * gain


def write_wav(path, x, sr=C.SR):
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(sr), "-ac", "1", "-i", "-", str(path)],
                   input=pcm, check=True)
