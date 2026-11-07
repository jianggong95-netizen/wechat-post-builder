# 素材生成：封面、简谱、配乐

本文件记录本机实测可用的生成链路与排版坑。首次使用时先探测环境，不要假设路径一定存在。

## 0. 环境探测

```python
import os, shutil, sys
CAND = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]
for c in CAND:
    print(os.path.exists(c), c)
print("ffmpeg:", shutil.which("ffmpeg"))
try:
    import PIL; print("PIL:", PIL.__version__)
except ImportError:
    print("PIL: MISSING")
```

本机曾验证的配置（换机器后重新探测）：

- Python：`C:\Users\skyes\.workbuddy\binaries\python\versions\3.13.12\python.exe`
- Edge 无头渲染：`C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`
- Pillow 装在隔离目录，需 `sys.path.insert(0, r"C:\Users\skyes\.workbuddy\binaries\node\workspace\pylibs")`；缺失时用 `python -m pip install --quiet pillow --target <该目录>` 安装
- ffmpeg：`C:\Users\skyes\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe`（版本号会变，用 Glob 找）
- Python 标准库可完成 HTTP multipart 上传与音频合成，不必依赖 `requests` / `numpy`

## 1. 封面

### 生成

用 ImageGen（`size: 1536x1024`、`quality: high`），prompt 必须包含：

- `2.35:1 横版构图`（实际生成 3:2，靠裁切得到 2.35:1）
- 画面主体与情绪（例如「月光下的立式钢琴，琴谱页与金色音符光点飘浮」）
- **标题文字直接写进 prompt**：「画面上方居中深色渐变区域放超大号加粗白色中文标题『致爱丽丝』，下方一行亮金色小字『带指法简谱 · 零基础也能弹』」
- 「文字锐利清晰、排版醒目，适合信息流封面」

生图工具会在右下角加「AI生成 WORKBUDDY」水印，需要后续处理。

### 裁成 2.35:1

```python
from PIL import Image
im = Image.open(src)
w, h = im.size
th = int(w / 2.35)
top = 60                      # 上移取景，直接把右下角水印裁掉
im.crop((0, top, w, top + th)).save(dst, quality=94)
```

**优先用取景偏移避开水印**，这是最省事、画面最自然的方式。先生成 1536×1024，裁出 1536×653。

### 去水印（已裁切仍有水印时）

不要用 ImageGen 图生图重绘：实测它会改构图、动文字，且水印仍在。改用**邻近像素补丁**：取水印区域正上方同尺寸的干净背景，垂直翻转后轻微高斯模糊，贴回覆盖。

```python
from PIL import Image, ImageFilter
im = Image.open(src).convert("RGB")
w, h = im.size
x1, y1, x2, y2 = int(w * 0.81), h - 83, w, h   # 右下角区域，按实图调整
patch = (im.crop((x1, y1 - (y2 - y1), x2, y1))
           .transpose(Image.FLIP_TOP_BOTTOM)
           .filter(ImageFilter.GaussianBlur(2)))
im.paste(patch, (x1, y1))
im.save(dst, quality=92)
```

适合天空、晚霞、渐变背景；若水印压在复杂纹理上，改用内容识别或换一张生成图。

`scripts/prep_images.py cover --dewatermark` 已封装上述两步。

## 2. 曲谱页（自排简谱，避免盗用带水印扫描谱）

链路：`assets/jianpu_renderer.py`（改数据）→ 生成 HTML → Edge 无头截图 → `assets/crop_white.py` 裁白边 → PNG。

```bash
python build_full.py
"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" \
  --headless=new --disable-gpu --hide-scrollbars \
  --window-size=1240,1800 \
  --screenshot="<abs>/full/page1.png" \
  "file:///D:/path/to/full/page1.html"
python crop_white.py
```

`file:///` URL 里的空格要写成 `%20`，路径用正斜杠。

裁白边优先用 `assets/crop_white.py`（只裁底部空白，保留设计好的左右页边距）。`scripts/prep_images.py trim` 会裁四周，适合四周都有白边的普通截图，直接用在谱面页上会把版式裁窄。

### 排版坑（实测逐条踩过）

- flex 容器**必须显式写 `flex-direction: row`**，否则块级堆叠，谱面变成竖排。
- `.score` 用 `flex: 0 0 auto` 或 `justify-content: flex-start`，不要用 `flex: 1` + `space-evenly`，否则大片留白；最后靠裁白边收紧。
- 6 个十六分音符的小节约 480px 宽，一行最多放两个；**按内容手动分组行**，别指望 `flex-wrap` 自动排得好看。
- 高八度点用绝对定位 `.dot.up { top: -16px; }`，位置太近会让 `1̇` 看起来像字母 `i`。
- 长音用延音线「—」，不要用一串休止符 `0` 占位。
- 低八度写 `1̣ / 5̣ / 6̣`（下加点），并在图例里说明。
- 指法用红色小字标在每个音上方，1 是拇指、5 是小指；小节号放左下角，正文里可写「我卡在 13 小节」。
- 页面底部加图例与练习提示，让单张图自成信息单元（读者会单独保存图片）。

### 记谱准确性

改编曲谱前先核对音高序列（搜索该曲的 letter notes / 简谱资料），并在文章里说明省略了哪些段落、为什么。不要为了「看起来完整」编造小节。

## 3. 示范音频（可选）

`assets/make_audio.py` 用纯 Python 加法合成钢琴音色（6 个泛音分别衰减 + 约 30ms 击弦噪声 + 3 抽头混响），**直接 import 简谱脚本的数据**，保证音频与谱面逐音一致，而不是拿原曲录音凑数。

```bash
python make_audio.py                 # 产出 .wav
ffmpeg -hide_banner -loglevel error -y -i fur_elise.wav \
  -codec:a libmp3lame -b:a 160k -ar 44100 -ac 1 fur_elise.mp3
```

要点：

- 按拍号与速度算准每小节时长（例：3/8、♩.=52 → 每小节约 1.1538s，24 小节约 30s）。
- 转 mp3 用 160k / 44.1kHz / 单声道，30 秒约 600KB，便于交付。
- 音频只是示范，**公众号正文无法嵌入**，交付与说明方式见 `references/yanxu-api.md` 的「音频边界」。

## 4. 体积检查与上传前准备

`scripts/prep_images.py check <file...> [--scene body|cover]` 会列出每张图大小并标出超限项。上传前必跑：

- 正文图 ≤1MB
- 封面 ≤2MB

超限时用 `prep_images.py` 的 JPEG 转换或重生成，不要直接提交。

## 5. 文件组织建议

每次任务在独立目录里工作，保留可复现链路：

```
<project>/<topic>/
├── build_full.py / jianpu_renderer.py   # 谱面源脚本
├── crop_white.py                        # 裁白边
├── make_audio.py                        # 配乐源脚本
├── full/page1.png ...                   # 成品谱面
├── cover.png                            # 成品封面
├── fur_elise.mp3                        # 成品音频
└── <topic>_推文_定稿.md                 # 文案存档
```

中间产物（`.wav`、源 HTML、失败尝试图）可在用户确认后清理；成品与可复现脚本保留。
