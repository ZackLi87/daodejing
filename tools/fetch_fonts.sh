#!/usr/bin/env bash
# 下载渲染所需的开源中文字体（均为 SIL OFL 授权）到 assets/fonts/。
#   霞鹜文楷（LXGW WenKai）：用于原文、字幕与正文
#   思源宋体（Noto Serif CJK SC）：用于标题与标签
set -euo pipefail
cd "$(dirname "$0")/../assets" 2>/dev/null || { mkdir -p "$(dirname "$0")/../assets"; cd "$(dirname "$0")/../assets"; }
mkdir -p fonts && cd fonts

WENKAI=https://github.com/lxgw/LxgwWenKai/releases/download/v1.520
[ -f wenkai.ttf ]     || curl -fsSL -o wenkai.ttf     "$WENKAI/LXGWWenKai-Regular.ttf"
[ -f wenkai_med.ttf ] || curl -fsSL -o wenkai_med.ttf "$WENKAI/LXGWWenKai-Medium.ttf"

if [ ! -f NotoSerifCJKsc-Regular.otf ]; then
  curl -fsSL -o noto.zip "https://github.com/notofonts/noto-cjk/releases/download/Serif2.003/09_NotoSerifCJKsc.zip"
  for w in Light Regular SemiBold Black; do
    unzip -j -o noto.zip "OTF/SimplifiedChinese/NotoSerifCJKsc-$w.otf" >/dev/null
  done
  rm -f noto.zip
fi
ls -1
