#!/usr/bin/env python3
"""Batch-upload local images through Yanxu one-time upload channels.

Each image needs its OWN ticket: call mcp__yanxu__get_upload_channel N times
first, write the returned upload_url values into a text file (one per line,
in the same order as the images), then run this script.

Usage:
    python upload_images.py --tickets tickets.txt --scene body p1.png p2.png p3.png
    python upload_images.py --url "https://.../upload?ticket=..." cover.png
    python upload_images.py --tickets tickets.txt --domain "https://toolsvip.cn" \
        --api-path "/api/once/upload" p1.png p2.png     # when file holds bare tickets

Prints a mapping of local file -> file_path. Use file_path in create_article.
Only the Python standard library is required.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

LIMITS = {"body": 1 * 1024 * 1024, "cover": 2 * 1024 * 1024,
          "frame": 2 * 1024 * 1024}


def read_channels(tickets_file, domain, api_path):
    if not tickets_file:
        return []
    channels = []
    with open(tickets_file, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith(("http://", "https://")):
                channels.append(line)
            elif domain:
                sep = "?" if "?" not in api_path else "&"
                channels.append(domain.rstrip("/") + api_path + sep + "ticket=" + line)
            else:
                raise SystemExit("Bare ticket found but --domain was not provided: " + line)
    return channels


def upload(url, path, field="file"):
    data = open(path, "rb").read()
    boundary = "----b" + os.urandom(8).hex()
    name = os.path.basename(path)
    ctype = "image/png" if name.lower().endswith(".png") else "image/jpeg"
    head = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="{field}"; '
        f'filename="{name}"\r\nContent-Type: {ctype}\r\n\r\n'
    ).encode("utf-8")
    body = head + data + f"\r\n--{boundary}--\r\n".encode("ascii")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extract_path(payload):
    """Locate file_path whether the API wraps it in data/ or returns it flat."""
    if not isinstance(payload, dict):
        return None, None
    for obj in (payload, payload.get("data")):
        if isinstance(obj, dict) and obj.get("file_path"):
            return obj.get("file_path"), obj.get("url")
    return None, None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tickets", help="file with one upload_url (or bare ticket) per line")
    ap.add_argument("--url", help="single upload_url, for exactly one image")
    ap.add_argument("--domain", help="base domain when tickets file holds bare ticket ids")
    ap.add_argument("--api-path", default="/api/once/upload")
    ap.add_argument("--scene", choices=sorted(LIMITS), default="body")
    ap.add_argument("--field", default="file", help="multipart field name (file or img)")
    ap.add_argument("--out", help="optional path to save the mapping as JSON")
    ap.add_argument("images", nargs="+", help="local image paths, in ticket order")
    args = ap.parse_args()

    channels = ([args.url] if args.url else []) + read_channels(
        args.tickets, args.domain, args.api_path)

    if len(channels) != len(args.images):
        raise SystemExit(
            f"Ticket/image count mismatch: {len(channels)} channels vs "
            f"{len(args.images)} images. Tickets are ONE-TIME: call "
            f"get_upload_channel once per image, within 5 minutes."
        )

    limit = LIMITS[args.scene]
    results, failed = [], []
    for idx, (url, path) in enumerate(zip(channels, args.images), 1):
        if not os.path.isfile(path):
            failed.append((path, "file not found"))
            print(f"[{idx}] MISSING {path}")
            continue
        size = os.path.getsize(path)
        if size > limit:
            failed.append((path, f"oversize {size} > {limit}"))
            print(f"[{idx}] OVERSIZE {size}B {path}")
            continue
        try:
            payload = upload(url, path, args.field)
            fpath, public = extract_path(payload)
            if not fpath:
                failed.append((path, "no file_path in response: " + json.dumps(payload, ensure_ascii=False)[:200]))
                print(f"[{idx}] NO_PATH {json.dumps(payload, ensure_ascii=False)[:200]}")
                continue
            results.append({"local": path, "file_path": fpath, "url": public})
            print(f"[{idx}] OK  {os.path.basename(path)} ({size}B) -> {fpath}")
        except (urllib.error.URLError, ValueError, OSError) as exc:
            failed.append((path, str(exc)))
            print(f"[{idx}] FAIL {path}: {exc}")

    print("\n=== mapping (paste file_path into image.url / cover_img) ===")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(results, fh, ensure_ascii=False, indent=2)
        print("saved:", args.out)
    if failed:
        print("\n=== failures (re-take a NEW ticket for each) ===")
        for path, reason in failed:
            print(" ", path, "::", reason)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
