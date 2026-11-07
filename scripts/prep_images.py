#!/usr/bin/env python3
"""Prepare images for a WeChat article: crop cover to 2.35:1, remove the
bottom-right AI watermark with a neighbouring-sky patch, trim white margins
from score screenshots, and check/compress against Yanxu size limits.

Subcommands:
    check   [--scene body|cover] FILE...
    cover   SRC DST [--top 60] [--ratio 2.35] [--dewatermark] [--no-crop]
    trim    SRC [DST] [--padding 24] [--threshold 735]
    compress SRC DST [--max-kb 900]

Note: `trim` cuts white margins on ALL four sides. For score pages that only
have trailing blank space at the bottom, use assets/crop_white.py instead so
the designed left/right margins are preserved.

Pillow is auto-detected, including the isolated WorkBuddy pylibs directory.
"""

import argparse
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

LIMITS = {"body": 1 * 1024 * 1024, "cover": 2 * 1024 * 1024,
          "frame": 2 * 1024 * 1024}


def load_pil():
    try:
        from PIL import Image, ImageFilter
        return Image, ImageFilter
    except ImportError:
        pass
    candidates = [
        os.environ.get("WB_PYLIBS", ""),
        r"C:\Users\skyes\.workbuddy\binaries\node\workspace\pylibs",
        r"C:\Users\skyes\.workbuddy\binaries\python\envs\default\Lib\site-packages",
    ]
    for c in candidates:
        if c and os.path.isdir(c):
            sys.path.insert(0, c)
    try:
        from PIL import Image, ImageFilter
        return Image, ImageFilter
    except ImportError:
        raise SystemExit(
            "Pillow not found. Install into the isolated dir:\n"
            "  python -m pip install pillow --target "
            r"C:\Users\skyes\.workbuddy\binaries\node\workspace\pylibs"
        )


def cmd_check(args, _Image, _Filter):
    limit = LIMITS[args.scene]
    bad = 0
    for p in args.files:
        if not os.path.isfile(p):
            print("MISSING ", p)
            bad += 1
            continue
        size = os.path.getsize(p)
        flag = "OK" if size <= limit else "OVERSIZE"
        if size > limit:
            bad += 1
        print(f"{flag:9} {size:>9}B  {p}")
    print(f"scene={args.scene} limit={limit}B  files={len(args.files)}  over={bad}")
    return 1 if bad else 0


def cmd_cover(args, Image, ImageFilter):
    im = Image.open(args.src).convert("RGB")
    if not args.no_crop:
        w, h = im.size
        th = int(w / args.ratio)
        top = max(0, min(args.top, h - th))
        im = im.crop((0, top, w, top + th))
    if args.dewatermark:
        im = remove_watermark(im, Image, ImageFilter)
    im.save(args.dst, quality=94)
    print(f"saved {args.dst}  size={im.size}  bytes={os.path.getsize(args.dst)}")
    return 0


def remove_watermark(im, Image, ImageFilter):
    w, h = im.size
    ww = max(40, int(w * 0.186))       # watermark band width (~286px @1536)
    wh = max(40, int(h * 0.127))       # watermark band height (~83px @653)
    x1, y1, x2, y2 = w - ww, h - wh, w, h
    ph = min(wh, y1)
    if ph <= 0:
        print("WARN: image too short for watermark patch; skipped")
        return im
    patch = (im.crop((x1, y1 - ph, x2, y1))
               .transpose(Image.FLIP_TOP_BOTTOM)
               .filter(ImageFilter.GaussianBlur(2)))
    im.paste(patch, (x1, y1))
    print(f"watermark patched: region=({x1},{y1},{x2},{y2})")
    return im


def cmd_trim(args, Image, _Filter):
    im = Image.open(args.src).convert("RGB")
    w, h = im.size
    px = im.load()
    thr = args.threshold
    cols = [x for x in range(0, w, 3)
            if any(sum(px[x, y]) < thr for y in range(0, h, 4))]
    rows = [y for y in range(0, h, 3)
            if any(sum(px[x, y]) < thr for x in range(0, w, 4))]
    if not cols or not rows:
        print("WARN: nothing detected, image left unchanged")
        return 0
    pad = args.padding
    box = (max(0, cols[0] - pad), max(0, rows[0] - pad),
           min(w, cols[-1] + pad), min(h, rows[-1] + pad))
    dst = args.dst or args.src
    im.crop(box).save(dst, quality=94)
    print(f"trimmed {im.size} -> {box}  saved={dst}")
    return 0


def cmd_compress(args, Image, _Filter):
    im = Image.open(args.src).convert("RGB")
    target = args.max_kb * 1024
    for q in (92, 86, 80, 72, 64, 56):
        im.save(args.dst, "JPEG", quality=q, optimize=True)
        if os.path.getsize(args.dst) <= target:
            print(f"saved {args.dst}  quality={q}  bytes={os.path.getsize(args.dst)}")
            return 0
    scale = 0.85
    while scale > 0.4:
        small = im.resize((int(im.width * scale), int(im.height * scale)))
        small.save(args.dst, "JPEG", quality=72, optimize=True)
        if os.path.getsize(args.dst) <= target:
            print(f"saved {args.dst}  scale={scale:.2f}  bytes={os.path.getsize(args.dst)}")
            return 0
        scale -= 0.1
    print("WARN: still over target after downscaling:", os.path.getsize(args.dst))
    return 1


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check")
    c.add_argument("--scene", choices=sorted(LIMITS), default="body")
    c.add_argument("files", nargs="+")

    v = sub.add_parser("cover")
    v.add_argument("src")
    v.add_argument("dst")
    v.add_argument("--top", type=int, default=60, help="crop top offset; avoids the corner watermark")
    v.add_argument("--ratio", type=float, default=2.35)
    v.add_argument("--dewatermark", action="store_true")
    v.add_argument("--no-crop", action="store_true", help="only remove watermark")

    t = sub.add_parser("trim")
    t.add_argument("src")
    t.add_argument("dst", nargs="?")
    t.add_argument("--padding", type=int, default=24)
    t.add_argument("--threshold", type=int, default=735,
                   help="sum(rgb) below this counts as non-white")

    m = sub.add_parser("compress")
    m.add_argument("src")
    m.add_argument("dst")
    m.add_argument("--max-kb", type=int, default=900)

    args = ap.parse_args()
    Image, ImageFilter = load_pil()
    return {
        "check": cmd_check, "cover": cmd_cover,
        "trim": cmd_trim, "compress": cmd_compress,
    }[args.cmd](args, Image, ImageFilter)


if __name__ == "__main__":
    sys.exit(main())
