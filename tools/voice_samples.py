"""生成音色对比样音：同一段原文由多个音色依次朗读，便于选定系列配音。

    python3 tools/voice_samples.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dao import audio, config as C, tts  # noqa: E402

VOICES = [
    ("Chinese (Mandarin)_Radio_Host", "电台男主播"),
    ("Chinese (Mandarin)_Gentleman", "温润男声"),
    ("Chinese (Mandarin)_Male_Announcer", "播报男声"),
    ("Chinese (Mandarin)_Wise_Women", "阅历姐姐"),
]
TEXT = "上善若水。水善利万物而不争，处众人之所恶，故几于道。"
PRON = ["处众人/(chu3)(zhong4)(ren2)", "所恶/(suo3)(wu4)", "几于道/(ji1)(yu2)(dao4)"]


def main():
    parts = []
    gap = np.zeros(int(1.2 * C.SR), np.float32)
    for vid, name in VOICES:
        label, _ = tts.synth(f"{name}。", vid, 1.0, [])
        body, _ = tts.synth(TEXT, vid, C.QUOTE_SPEED, PRON)
        parts += [tts.trim(tts.decode(label)), gap[: C.SR // 2], tts.trim(tts.decode(body)), gap]
        print(name, vid)
    x = np.concatenate(parts)
    out = C.OUTPUT / "音色对比.mp3"
    out.parent.mkdir(parents=True, exist_ok=True)
    wav = C.BUILD / "voices.wav"
    audio.write_wav(wav, x / np.abs(x).max() * 0.85)
    import subprocess
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-b:a", "128k", str(out)], check=True)
    print(out)


if __name__ == "__main__":
    main()
