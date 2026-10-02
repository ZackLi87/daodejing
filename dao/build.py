"""构建一期视频。

    python3 -m dao.build ep01                 # 配音 + 混音 + 渲染成片
    python3 -m dao.build ep01 --still 5 30    # 只渲染指定时刻（秒）的单帧，用于检查版面
    python3 -m dao.build ep01 --audio-only    # 只生成配音、字幕与文稿
    python3 -m dao.build ep01 --no-bgm        # 不加背景音
"""
import argparse
import importlib
import multiprocessing as mp
import os
import shutil
import subprocess
import sys
import time

import numpy as np

from . import audio, config as C, engine, tts


def prepare(ep, voice=None):
    mod = importlib.import_module(f"episodes.{ep}.script")
    shots = mod.SHOTS
    voice = voice or getattr(mod, "VOICE", C.TTS_VOICE)
    clips, billed = {}, 0
    for sh in shots:
        for s in sh.segs:
            path, used = tts.synth(s.tts_text, voice, s.speed or C.TTS_SPEED, getattr(mod, "PRON", []))
            billed += used
            x = tts.trim(tts.decode(path))
            clips[id(s)] = x
            s.dur = len(x) / C.SR
            s.clauses = tts.align(x, s.tts_text)
            s.chars = tts.char_times(s.clauses)
    total = engine.layout(shots)
    track = np.zeros(int((total + 0.5) * C.SR), np.float32)
    for sh in shots:
        for s in sh.segs:
            a = int(round((sh.start + s.t0) * C.SR))
            x = clips[id(s)]
            track[a:a + len(x)] += x[:len(track) - a]
    subs = engine.subtitles(shots)
    return mod, shots, track[:int(total * C.SR)], subs, total, billed


def manuscript(mod, shots):
    names = {"Hook": "开篇", "Title": "片名", "Original": "原文", "Summary": "小结", "Outro": "片尾"}
    out = [f"# 道德经细读 {mod.META['num']} · {mod.META['slug']} · 旁白文稿", ""]
    for i, sh in enumerate(shots, 1):
        name = names.get(sh.cls.__name__, sh.p.get("section", sh.cls.__name__))
        out.append(f"## {i}. {name}（{sh.start:.1f}–{sh.start + sh.dur:.1f} 秒）")
        out.append("")
        for s in sh.segs:
            out.append(s.text)
            out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep")
    ap.add_argument("--still", nargs="*", type=float)
    ap.add_argument("--audio-only", action="store_true")
    ap.add_argument("--no-bgm", action="store_true")
    ap.add_argument("--voice")
    ap.add_argument("--workers", type=int, default=max(1, mp.cpu_count()))
    a = ap.parse_args()

    mod, shots, voice, subs, total, billed = prepare(a.ep, a.voice)
    work = C.BUILD / a.ep
    work.mkdir(parents=True, exist_ok=True)
    print(f"时长 {total:.1f} 秒，{sum(len(sh.segs) for sh in shots)} 句旁白，本次新增计费字符 {billed}")

    if a.still is not None:
        r = engine.Renderer(shots, subs, total)
        for t in a.still:
            p = work / f"still_{t:06.2f}.png"
            r.frame(t).save(p)
            print(p)
        return

    out_dir = C.OUTPUT / a.ep
    out_dir.mkdir(parents=True, exist_ok=True)
    name = mod.META["out"]
    (out_dir / f"{name}.srt").write_text(engine.srt(subs), encoding="utf-8")
    (out_dir / "旁白文稿.md").write_text(manuscript(mod, shots), encoding="utf-8")
    info = C.ROOT / "episodes" / a.ep / "视频信息.md"
    if info.exists():
        shutil.copy(info, out_dir / "视频信息.md")

    music = np.zeros_like(voice) if a.no_bgm else audio.bgm(total)
    mixed = audio.mix(voice, music, music_db=-60 if a.no_bgm else -25)
    wav = work / "mix.wav"
    audio.write_wav(wav, mixed)
    audio.write_wav(work / "voice.wav", voice / (np.abs(voice).max() + 1e-9) * 0.84)
    if a.audio_only:
        print(wav)
        return

    mp4 = out_dir / f"{name}.mp4"
    n = int(total * C.FPS)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{C.W}x{C.H}",
           "-r", str(C.FPS), "-i", "-", "-i", str(wav), "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "44100", "-c:a", "aac", "-b:a", "192k",
           "-movflags", "+faststart", "-shortest", str(mp4)]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    with mp.get_context("fork").Pool(a.workers, initializer=engine._init_worker,
                                     initargs=(shots, subs, total)) as pool:
        for i, buf in enumerate(pool.imap(engine._render, range(n), chunksize=6)):
            if isinstance(buf, str):
                enc.kill()
                print("\n" + buf, file=sys.stderr, flush=True)
                os._exit(1)
            enc.stdin.write(buf)
            if i % (C.FPS * 10) == 0:
                el = time.time() - t0
                print(f"\r渲染 {i}/{n} 帧  {el:.0f} 秒", end="", file=sys.stderr, flush=True)
    enc.stdin.close()
    enc.wait()
    print(f"\n完成：{mp4}（用时 {time.time() - t0:.0f} 秒）")


if __name__ == "__main__":
    main()
