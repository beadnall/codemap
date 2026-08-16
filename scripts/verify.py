#!/usr/bin/env python3
"""Checks a codemap page without rendering it.

    python3 verify.py page.html

Static checks only, and they are cheap. Run scripts/render.py as well before
publishing — several faults that matter are invisible to everything here.

The syntax check needs a JavaScript engine. It tries, in order: node, deno,
bun, then macOS's built-in JavaScriptCore via osascript. If none is present the
check is SKIPPED rather than failed, because the absence of a JS runtime says
nothing about the page.

Exits non-zero if a check failed, so it can gate a publish. Skips do not fail.
"""

import pathlib
import platform
import re
import shutil
import subprocess
import sys
import tempfile

FAILED = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   {detail}" if detail else ""))
    if not ok:
        FAILED.append(name)


def skip(name, why):
    print(f"  SKIP  {name}   {why}")


def syntax_ok(js_path):
    """Returns (verdict, detail). verdict is True, False, or None for skipped.

    Engines report differently, and one of them runs the script rather than
    only parsing it — so a missing `document` is the expected success signal
    there, not a failure.
    """
    if shutil.which("node"):
        r = subprocess.run(["node", "--check", js_path], capture_output=True, text=True)
        return r.returncode == 0, (r.stderr.strip().splitlines() or [""])[0][:140]

    if shutil.which("bun"):
        r = subprocess.run(["bun", "build", "--no-bundle", js_path],
                           capture_output=True, text=True)
        return r.returncode == 0, (r.stderr.strip().splitlines() or [""])[0][:140]

    if shutil.which("deno"):
        r = subprocess.run(["deno", "check", "--no-lock", js_path],
                           capture_output=True, text=True)
        err = (r.stderr or "").strip()
        bad = "SyntaxError" in err or "Expected" in err
        return not bad, err.splitlines()[0][:140] if bad else ""

    if platform.system() == "Darwin" and shutil.which("osascript"):
        # JavaScriptCore compiles the whole script, then runs it with no DOM.
        # "Can't find variable: document" therefore means the syntax is fine.
        r = subprocess.run(["osascript", "-l", "JavaScript", js_path],
                           capture_output=True, text=True)
        err = (r.stderr or "").strip()
        if "SyntaxError" in err:
            return False, err.split("execution error:")[-1].strip()[:140]
        if "Can't find variable: document" in err or "Can't find variable: window" in err:
            return True, ""
        return r.returncode == 0, err[:140]

    return None, "no JavaScript engine found — install node for this check"


def block(src, name):
    """The body of `const NAME = [ ... ];`, or "" when it is not there."""
    m = re.search(r"const %s\s*=\s*\[(.*?)\n\];" % name, src, re.S)
    return m.group(1) if m else ""


def main(path):
    src = pathlib.Path(path).read_text(encoding="utf-8")

    # --- the script parses -------------------------------------------------
    m = re.search(r"<script>(.*)</script>", src, re.S)
    if not m:
        check("page contains a script", False)
    else:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                         encoding="utf-8") as fh:
            fh.write(m.group(1))
            js = fh.name
        verdict, detail = syntax_ok(js)
        if verdict is None:
            skip("script compiles", detail)
        else:
            check("script compiles", verdict, detail)

    # --- the data is internally consistent ---------------------------------
    ids = set(re.findall(r'\bid:"([A-Za-z0-9_-]+)"', src))

    # Read the edges out of the EDGES block rather than the whole file. The
    # pattern for an edge is also the pattern for the first two members of a
    # region's `of:["a","b","c"]`, so scanning everything invented edges.
    edge_block = block(src, "EDGES")
    edges = re.findall(r'\["([A-Za-z0-9_-]+)","([A-Za-z0-9_-]+)",', edge_block)
    endpoints = {e for pair in edges for e in pair}

    check("the EDGES array is where it is expected", bool(edge_block.strip()),
          "" if edge_block.strip() else "no `const EDGES = [ ... ];` found")

    dangling = sorted(endpoints - ids)
    check("every edge names a real node", not dangling,
          f"dangling: {', '.join(dangling)}" if dangling
          else f"{len(ids)} nodes, {len(edges)} edges")
    check("node count is readable (12-24)", 12 <= len(ids) <= 24, f"{len(ids)} nodes")

    orphans = sorted(ids - endpoints)
    check("no node is unconnected", not orphans,
          f"orphans: {', '.join(orphans)}" if orphans else "")

    # --- stacked nodes have room for their plates --------------------------
    # `stack: n` splits a node's height into n plates with a 2.5 gap between
    # them. Past a certain n the plates are thinner than their own outlines and
    # the block turns into a smudge, which looks like a rendering bug rather
    # than a value that was set too high.
    node_block = block(src, "NODES")
    stacks = [(int(h), int(s)) for h, s in
              re.findall(r"\bh:\s*(\d+)\s*,\s*stack:\s*(\d+)", node_block)]
    also = re.findall(r"\bstack:\s*(\d+)\s*,\s*h:\s*(\d+)", node_block)
    stacks += [(int(h), int(s)) for s, h in also]

    bad_n = [s for _, s in stacks if not 2 <= s <= 5]
    check("stack counts are 2-5", not bad_n,
          f"out of range: {', '.join(map(str, bad_n))}" if bad_n
          else f"{len(stacks)} stacked nodes")

    thin = [(h, s, round((h - 2.5 * (s - 1)) / s, 1)) for h, s in stacks
            if (h - 2.5 * (s - 1)) / s < 3]
    check("stacked plates are thick enough to read", not thin,
          "; ".join(f"h:{h} stack:{s} gives {t}px plates" for h, s, t in thin) if thin
          else "")

    # --- regions enclose something real ------------------------------------
    # A region names its members by id and draws the box that contains them.
    # An id that matches nothing is dropped at build time, so a region with a
    # typo in it silently shrinks — or vanishes — rather than failing loudly.
    region_block = block(src, "REGIONS")
    regions = re.findall(r"\bof:\s*\[([^\]]*)\]", region_block)
    members = [(i, m) for i, grp in enumerate(regions)
               for m in re.findall(r'"([A-Za-z0-9_-]+)"', grp)]
    unknown = sorted({m for _, m in members} - ids)
    check("every region names real nodes", not unknown,
          f"unknown: {', '.join(unknown)}" if unknown
          else f"{len(regions)} regions, {len(members)} members")

    empty = [i for i, grp in enumerate(regions) if not re.search(r'"', grp)]
    check("no region is empty", not empty,
          f"regions {', '.join(str(i + 1) for i in empty)} enclose nothing" if empty else "")

    # The label is drawn under the outline, centred and unwrapped, in the same
    # crowded space the node names live in. Anything longer belongs in `note`,
    # which is panel-only and can run as long as it likes.
    long_labels = [l for l in re.findall(r"\blabel:\s*\"([^\"]+)\"", region_block)
                   if len(l) > 16]
    check("region labels fit under the outline (<=16 chars)", not long_labels,
          f"too long: {', '.join(long_labels)}" if long_labels else "")

    # --- the panel will actually draw --------------------------------------
    # A default selection naming a node from another project throws on an
    # undefined lookup and the page opens with an empty panel. It looks
    # structurally perfect, which is why this check exists.
    default = re.search(r"let current = (.+?), tab", src)
    d = default.group(1).strip() if default else ""
    check("default selection resolves", d == "NODES[0].id" or d.strip('"') in ids,
          d or "not found")

    # Labels sit centred under their block and crowd the neighbours once they
    # run long. Sixteen characters clears the block width at this scale.
    names = re.findall(r'name:"([^"]+)"', src)
    too_long = [n for n in names if len(n) > 16]
    check("node names fit under a block (<=16 chars)", not too_long,
          f"too long: {', '.join(too_long)}" if too_long
          else f"longest {max((len(n) for n in names), default=0)}")

    # --- it is self-contained ----------------------------------------------
    external = re.findall(r'(?:src|href)\s*=\s*["\'](https?:|//)', src)
    check("no external resources (the artifact CSP blocks them)", not external,
          f"{len(external)} found" if external else "")

    # --- it has been made specific -----------------------------------------
    title = re.search(r"<title>(.*?)</title>", src, re.S)
    t = title.group(1).strip() if title else ""
    check("title has been set", bool(t) and "REPLACE" not in t.upper(), t or "missing")
    check("title is a name, not a label",
          t.lower() not in {"architecture", "architecture diagram", "codebase map",
                            "system diagram", "overview", "codemap"}, t)

    aria = re.search(r'<svg[^>]*aria-label="([^"]*)"', src)
    a = aria.group(1) if aria else ""
    check("svg description has been written",
          bool(a) and "REPLACE" not in a.upper(), a[:60] or "missing")

    # The template carries an explicit sentinel, which the author deletes along
    # with the example arrays. Grepping for the example's *subject* was the
    # earlier approach and was wrong: it failed a legitimate map of that
    # subject, which happened the first time the shipped example changed.
    check("example data has been replaced", "TEMPLATE-EXAMPLE-DATA" not in src,
          "sentinel comment still present" if "TEMPLATE-EXAMPLE-DATA" in src else "")

    print()
    if FAILED:
        print(f"{len(FAILED)} check(s) failed: {', '.join(FAILED)}")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: verify.py page.html")
    sys.exit(main(sys.argv[1]))
