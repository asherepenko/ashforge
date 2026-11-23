#!/usr/bin/env python3
"""fetch-doc.py — fetch a Material doc by component/topic name and trim it.

Stdlib only, so every runtime can run it — no web-fetch tool needed. The trim
modes keep a long doc (full attribute tables) out of context.

Usage:  fetch-doc.py <component-or-topic ...> [--toc | --section <keyword>]
  (none)      whole doc, image lines dropped
  --toc       headings only (fenced code is never read as a heading)
  --section   every section whose heading contains <keyword> (case-
              insensitive), with its sub-sections, up to the next heading
              of the same or a higher level
Output: first line `SOURCE=<raw url>`, then the doc text.
Exit:   0 ok · 3 ambiguous / 4 unknown (passed through from resolve-doc.py)
        · 5 fetch failed (URL on stderr) · 6 no section matched (TOC printed)
Test seam: MATERIAL_DOC_FILE=<path> reads that file instead of the network.
"""
import os
import re
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.realpath(__file__))
FENCE = re.compile(r"^\s*```")
HEADING = re.compile(r"^(#+) ")


def toc(lines):
    fenced, out = False, []
    for l in lines:
        if FENCE.match(l):
            fenced = not fenced
        elif not fenced and HEADING.match(l):
            out.append(l)
    return out


def section(lines, kw):
    kw, fenced, lvl, out = kw.lower(), False, 0, []
    for l in lines:
        if FENCE.match(l):
            fenced = not fenced
            if lvl:
                out.append(l)
            continue
        m = None if fenced else HEADING.match(l)
        if m:
            n = len(m.group(1))
            if lvl and n <= lvl:
                lvl = 0
            if not lvl and kw in l.lower():
                lvl = n
        if lvl:
            out.append(l)
    return out


def main(argv):
    mode, kw, words = "full", "", []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--toc":
            mode = "toc"
        elif a == "--section":
            mode, kw = "section", argv[i + 1] if i + 1 < len(argv) else ""
            i += 1
        else:
            words.append(a)
        i += 1
    if mode == "section" and not kw:
        print("--section needs a keyword", file=sys.stderr)
        return 4

    r = subprocess.run([sys.executable, os.path.join(HERE, "resolve-doc.py"), *words],
                       stdout=subprocess.PIPE, text=True)
    if r.returncode != 0:
        sys.stdout.write(r.stdout)
        return r.returncode
    url = next((l[4:] for l in r.stdout.splitlines() if l.startswith("URL=")), "")

    try:
        if os.environ.get("MATERIAL_DOC_FILE"):
            with open(os.environ["MATERIAL_DOC_FILE"], encoding="utf-8") as fh:
                doc = fh.read()
        else:
            with urllib.request.urlopen(url, timeout=20) as resp:
                doc = resp.read().decode("utf-8", "replace")
    except (OSError, ValueError):
        print(f"fetch failed: {url}", file=sys.stderr)
        return 5

    # Images can't be shown; their markdown is noise in context.
    lines = [l for l in doc.rstrip("\n").split("\n") if not re.match(r"^\s*(!\[|<img\s)", l)]
    print(f"SOURCE={url}")
    if mode == "full":
        out = lines
    elif mode == "toc":
        out = toc(lines)
    else:
        out = section(lines, kw)
        if not out:
            print(f"no section matching: {kw} — pick one from the headings below", file=sys.stderr)
            print("\n".join(toc(lines)))
            return 6
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
