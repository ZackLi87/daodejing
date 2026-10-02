# 道德经细读

《道德经》名句解析视频合集的制作工程：文稿、配音、画面与字幕均由脚本生成，画面为 1920×1080、30 帧。

- 选题与各期要点：[选题规划.md](选题规划.md)
- 各期成片、字幕、旁白文稿与视频信息：`output/epNN/`

## 目录

```
dao/                 渲染引擎
  config.py          画幅、配色、字体、配音参数
  gfx.py             宣纸底、文字图块、竖排、印章、水墨显字
  tts.py             逐句配音（MiniMax）、缓存、去静音、分句对齐
  audio.py           背景琴音合成与混音
  engine.py          时间轴、字幕切分、逐帧合成
  scenes.py          通用场景：开篇、片名、原文竖排、小结、片尾
  build.py           构建入口
  cover.py           封面（横版 4:3、竖版 3:4）
episodes/epNN/
  script.py          本期旁白与画面参数
  scenes.py          本期专用插图场景
  视频信息.md         标题、简介与结尾语
tools/
  minimax_tts.py     MiniMax 语音合成脚本
  fetch_fonts.sh     下载字体
output/epNN/         成片（.mp4）、封面、字幕（.srt）、旁白文稿、视频信息
```

## 使用

```bash
pip install pillow numpy          # 另需 ffmpeg
bash tools/fetch_fonts.sh         # 霞鹜文楷、思源宋体（SIL OFL）

# 密钥：放在 tools/minimax_key.txt（已被 .gitignore 忽略），或设置环境变量 MINIMAX_API_KEY
python3 -m dao.build ep01 --still 20 60     # 渲染单帧检查版面，输出到 build/ep01/
python3 -m dao.build ep01                   # 生成成片
python3 -m dao.build ep01 --voice "Chinese (Mandarin)_Gentleman"   # 更换音色
python3 -m dao.build ep01 --no-bgm          # 不加背景琴音
python3 -m dao.cover ep01                   # 封面：横版 4:3（1440×1080）、竖版 3:4（1080×1440）
```

配音逐句缓存在 `build/tts/`，修改画面后重新渲染不会重复计费；只有改动的句子会重新合成。

## 制作要点

- **读音校正**：古文中的多音字在 `script.py` 的 `PRON` 中逐词指定，例如“处众人”（chǔ）、“所恶”（wù）、“几于道”（jī）、“夫唯”（fú），通过 MiniMax 的 `pronunciation_dict` 生效。
- **分句对齐**：每句旁白单独合成，再依据音频中的停顿，用动态规划确定各分句的起止时间；原文竖排逐字显现、字幕切换与画面提示均以此为准。
- **字幕**：按中文视频惯例去除句读标点、以空格分隔，保留问号、引号与书名号；同时输出 `.srt` 文件，便于在剪辑软件中另行调整。
- **背景音**：以 Karplus–Strong 拨弦算法合成 D 宫五声音阶的稀疏琴音，人声出现时自动压低；如需替换为其他配乐，可使用 `--no-bgm` 输出后在剪辑软件中叠加。
