#!/usr/bin/env python3
"""Renders a codemap page and writes a PNG, on any platform.

    python3 render.py page.html render.png [width] [height]

Look at the result before publishing. Every fault that mattered while this
skill was being built passed static analysis and was obvious in a render: an
empty panel from a bad default selection, names clipped by the blocks in front
of them, and mojibake from a charset assumption.

Uses a Chromium-family browser in headless mode, which covers Linux, Windows
and macOS without installing anything if Chrome, Chromium, Edge or Brave is
present. On macOS with no such browser it falls back to render.swift, which
uses the system WebKit and needs nothing at all.
"""

import os
import pathlib
import platform
import shutil
import subprocess
import sys
import tempfile

# Chromium accepts these on all three platforms. --virtual-time-budget lets the
# page's timers run so the layout settles and the flow animation starts, rather
# than capturing a blank first frame.
FLAGS = ["--headless=new", "--disable-gpu", "--hide-scrollbars",
         "--no-sandbox", "--virtual-time-budget=4000"]

CANDIDATES = {
    "Darwin": [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    ],
    "Linux": [
        "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
        "microsoft-edge", "microsoft-edge-stable", "brave-browser",
    ],
    "Windows": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ],
}


def find_browser():
    for name in CANDIDATES.get(platform.system(), []):
        if os.path.sep in name or (os.path.altsep and os.path.altsep in name):
            if pathlib.Path(name).exists():
                return name
        else:
            found = shutil.which(name)
            if found:
                return found
    # Anything on PATH under a generic name, for distributions not listed above.
    for name in ("chrome", "chromium", "msedge", "brave"):
        found = shutil.which(name)
        if found:
            return found
    return None


def with_charset(page):
    """Copies the page with an explicit charset so any engine decodes it.

    The artifact host supplies the <head>, not us, so a page loaded straight
    off disk has no charset declared and engines fall back to Latin-1 — em
    dashes arrive as "a€". That is the renderer's problem to solve, not the
    page's.
    """
    html = page.read_text(encoding="utf-8")
    tmp = pathlib.Path(tempfile.mkdtemp()) / "page.html"
    tmp.write_text('<meta charset="utf-8">\n' + html, encoding="utf-8")
    return tmp


def main(argv):
    if not 3 <= len(argv) <= 5:
        sys.exit("usage: render.py page.html out.png [width] [height]")
    page = pathlib.Path(argv[1]).resolve()
    out = pathlib.Path(argv[2]).resolve()
    width = argv[3] if len(argv) > 3 else "1600"
    height = argv[4] if len(argv) > 4 else "1000"

    if not page.exists():
        sys.exit(f"no such page: {page}")

    browser = find_browser()
    if browser:
        staged = with_charset(page)
        cmd = [browser, *FLAGS,
               f"--screenshot={out}", f"--window-size={width},{height}",
               staged.as_uri()]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if out.exists() and out.stat().st_size > 0:
            print(f"wrote {out.name}  ({out.stat().st_size // 1024} KB, via {pathlib.Path(browser).name})")
            return 0
        sys.stderr.write((result.stderr or "no output from browser")[-600:] + "\n")
        return 1

    swift = pathlib.Path(__file__).with_name("render.swift")
    if platform.system() == "Darwin" and shutil.which("swift") and swift.exists():
        print("no Chromium-family browser found; using system WebKit")
        return subprocess.run(["swift", str(swift), str(page), str(out),
                               width, height]).returncode

    sys.exit(
        "No renderer available.\n"
        "Install Chrome, Chromium, Edge or Brave — headless screenshot works on\n"
        "Linux, Windows and macOS with any of them. On macOS, Xcode's swift\n"
        "toolchain also works via render.swift with nothing else installed."
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv))
