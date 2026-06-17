"""Enumerate a YouTube channel and fetch transcripts into a brain's sources/.

Usage:  python -m engram fetch <channel-url> <brain-dir> [--limit N]

Lists every video AND the /shorts tab via yt-dlp, fetches auto-captions for each (json3 →
plain text), writes them to `sources/transcripts/<id>.txt`, and writes/updates
`sources/manifest.json`. Re-running is incremental: ids already present are skipped, so this
doubles as the "add the most recent videos" path.

Requires `yt-dlp` on PATH (`pip install yt-dlp`). A JS runtime (deno/node) is recommended for
current YouTube extraction.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import shutil
import subprocess
import sys
import tempfile

from .core import Brain


def _run(args: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, p.stdout or "", p.stderr or ""


def enumerate_channel(channel: str) -> list:
    """Return [{id, title, type}] across the videos and shorts tabs (deduped)."""
    seen, items = set(), []
    base = channel.rstrip("/")
    for tab, kind in (("videos", "video"), ("shorts", "short")):
        rc, out, _ = _run(["yt-dlp", "--flat-playlist", "--print", "%(id)s|%(title)s",
                            f"{base}/{tab}"])
        if rc != 0:
            continue
        for line in out.splitlines():
            if "|" not in line:
                continue
            vid, title = line.split("|", 1)
            vid = vid.strip()
            if vid and vid not in seen:
                seen.add(vid)
                items.append({"id": vid, "title": title.strip(), "type": kind})
    return items


def _json3_to_text(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    out = []
    for ev in d.get("events", []):
        for s in ev.get("segs", []) or []:
            t = s.get("utf8", "")
            if t:
                out.append(t)
    return "".join(out).replace("\n", " ").strip()


def fetch_transcript(vid: str, workdir: str) -> tuple[str | None, dict]:
    """Fetch one video's auto-captions + metadata. Returns (text|None, info)."""
    _run(["yt-dlp", "--skip-download", "--write-auto-subs", "--sub-langs", "en.*",
          "--sub-format", "json3", "--write-info-json", "-o",
          os.path.join(workdir, "%(id)s.%(ext)s"), f"https://www.youtube.com/watch?v={vid}"])
    info = {}
    info_path = os.path.join(workdir, f"{vid}.info.json")
    if os.path.exists(info_path):
        with open(info_path, encoding="utf-8") as f:
            info = json.load(f)
    text = None
    for suffix in (".en.json3", ".en-orig.json3"):
        p = os.path.join(workdir, vid + suffix)
        if os.path.exists(p):
            try:
                text = _json3_to_text(p)
                if text:
                    break
            except Exception:
                pass
    return text, info


def main(argv: list[str]) -> int:
    limit = None
    if "--limit" in argv:
        i = argv.index("--limit")
        if i + 1 >= len(argv):
            print("error: --limit requires a value", file=sys.stderr)
            return 2
        try:
            limit = int(argv[i + 1])
        except ValueError:
            print(f"error: --limit must be an integer, got {argv[i + 1]!r}", file=sys.stderr)
            return 2
        argv = argv[:i] + argv[i + 2:]
    args = [a for a in argv if not a.startswith("--")]
    if len(args) < 2:
        print("usage: python -m engram fetch <channel-url> <brain-dir> [--limit N]", file=sys.stderr)
        return 2
    channel, brain = args[0], Brain(args[1])
    if not shutil.which("yt-dlp"):
        print("error: yt-dlp not found on PATH. Install it with: pip install yt-dlp", file=sys.stderr)
        return 2
    brain.ensure_dirs()

    man = brain.manifest() or {"channel": channel, "items": []}
    known = {it["id"] for it in man.get("items", [])}
    existing_txt = {fn[:-4] for fn in os.listdir(brain.transcripts_dir) if fn.endswith(".txt")}

    print(f"enumerating {channel} …")
    listing = enumerate_channel(channel)
    todo = [it for it in listing if it["id"] not in known or it["id"] not in existing_txt]
    if limit:
        todo = todo[:limit]
    print(f"{len(listing)} videos found · {len(todo)} to fetch "
          f"({len(known)} already in manifest)")

    workdir = tempfile.mkdtemp(prefix="engram-fetch-")
    added = 0
    try:
        for n, it in enumerate(todo, 1):
            vid = it["id"]
            print(f"  [{n}/{len(todo)}] {vid} … ", end="", flush=True)
            text, info = fetch_transcript(vid, workdir)
            coverage = "missed"
            if text:
                with open(os.path.join(brain.transcripts_dir, vid + ".txt"), "w",
                          encoding="utf-8") as f:
                    f.write(text)
                coverage = "transcript"
            entry = {
                "id": vid, "type": it["type"],
                "title": info.get("title") or it["title"],
                "url": f"https://www.youtube.com/watch?v={vid}",
                "coverage": coverage,
                "upload_date": info.get("upload_date"),
            }
            man["items"] = [x for x in man.get("items", []) if x["id"] != vid] + [entry]
            added += 1
            print(coverage if not text else f"{len(text.split())} words")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    items = man["items"]
    man["channel"] = channel
    man["fetched"] = _dt.date.today().isoformat()
    man["counts"] = {
        "total": len(items),
        "transcript": sum(1 for x in items if x.get("coverage") == "transcript"),
        "missed": sum(1 for x in items if x.get("coverage") == "missed"),
    }
    os.makedirs(os.path.dirname(brain.manifest_path), exist_ok=True)
    with open(brain.manifest_path, "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=2)
    print(f"done — {added} processed; manifest now {man['counts']}")
    print("\nNext: distill the new transcripts into atoms/edges, then run "
          "`python -m engram build " + brain.root + "`")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
