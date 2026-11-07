# -*- coding: utf-8 -*-
"""裁掉 Edge 无头截图底部的纯白留白（谱面页专用）。

用法：
    python crop_white.py                          # 默认裁 ./full/page*.png
    python crop_white.py "out/page*.png"         # 自定义 glob
    python crop_white.py "out/page*.png" 60      # 自定义底部留白像素

输出覆盖原文件。Pillow 会自动探测隔离目录。
"""
import glob
import os
import sys


def load_pil():
    try:
        from PIL import Image
        return Image
    except ImportError:
        pass
    for c in (
        os.environ.get("WB_PYLIBS", ""),
        r"C:\Users\skyes\.workbuddy\binaries\node\workspace\pylibs",
        r"C:\Users\skyes\.workbuddy\binaries\python\envs\default\Lib\site-packages",
    ):
        if c and os.path.isdir(c):
            sys.path.insert(0, c)
    try:
        from PIL import Image
        return Image
    except ImportError:
        raise SystemExit("Pillow not found; install it into the isolated pylibs dir first.")


def trim(path, Image, padding):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    last = 0
    for y in range(h):
        cnt = 0
        for x in range(0, w, 2):
            r, g, b = px[x, y]
            if r + g + b < 600:
                cnt += 1
                if cnt >= 3:
                    last = y
                    break
    out = im.crop((0, 0, w, min(h, last + padding)))
    out.save(path, optimize=True)
    print(os.path.basename(path), im.size, "->", out.size,
          round(os.path.getsize(path) / 1024, 1), "KB")


def main():
    Image = load_pil()
    pattern = sys.argv[1] if len(sys.argv) > 1 else os.path.join("full", "page*.png")
    padding = int(sys.argv[2]) if len(sys.argv) > 2 else 46
    files = sorted(glob.glob(pattern))
    if not files:
        raise SystemExit("No images matched: " + pattern)
    for p in files:
        trim(p, Image, padding)


if __name__ == "__main__":
    main()
