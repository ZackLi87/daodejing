"""全局参数：画幅、帧率、配色、字体与配音设置。"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = ROOT / "assets" / "fonts"
BUILD = ROOT / "build"
OUTPUT = ROOT / "output"

W, H = 1920, 1080
FPS = 30
SR = 44100                # 音频采样率

# 配色：宣纸底、墨色三级、朱砂、水色
PAPER = (243, 237, 224)
INK = (34, 30, 27)
INK2 = (86, 78, 68)
INK3 = (146, 136, 120)
RED = (168, 50, 45)
WATER = (64, 110, 124)
WATER_L = (150, 184, 190)

FONTS = {
    "kai": "wenkai.ttf",                    # 霞鹜文楷
    "kai_m": "wenkai_med.ttf",
    "serif_l": "NotoSerifCJKsc-Light.otf",  # 思源宋体
    "serif": "NotoSerifCJKsc-Regular.otf",
    "serif_sb": "NotoSerifCJKsc-SemiBold.otf",
    "serif_bk": "NotoSerifCJKsc-Black.otf",
}

# 配音（MiniMax T2A v2）
TTS_HOST = "api.minimaxi.com"
TTS_MODEL = "speech-2.6-hd"
TTS_VOICE = "Chinese (Mandarin)_Radio_Host"   # 电台男主播
TTS_SPEED = 0.95
QUOTE_SPEED = 0.88                            # 朗读原文时稍慢

# 字幕
SUB_Y = 1000          # 字幕基线中心
SUB_SIZE = 46
SUB_MAX = 22          # 每行最多字数
