# codemap

This repository holds a skill for turning a codebase into an explorable
isometric diagram. The full instructions are in [SKILL.md](../SKILL.md) — read
that file and follow it when asked to map, diagram or visually explain how a
system fits together.

Two things worth knowing before you start:

**The drawing is already done.** `assets/template.html` is a complete,
self-contained page — isometric projection, panning, zooming, animation and the
side panel all work. Building a map means replacing four data arrays,
`STATS`, `NODES`, `EDGES` and `REGIONS`, plus the `<title>` and the
`<svg aria-label>`. `REGIONS` draws a dashed outline around the parts of the
system the repository does not own, and may be left empty.

**The facts are the work.** A diagram of boxes labelled *Service*, *Database*
and *API* tells a reader nothing the directory listing would not have. Mine the
repository for measured numbers, platform limits worked around, and comments
explaining why a constant is what it is, and put real values on the edges.

Verify and render before handing anything over:

```bash
python3 scripts/verify.py my-map.html
python3 scripts/render.py my-map.html render.png
```

Look at the PNG. Several faults that matter — an empty panel from a bad default
selection, labels clipped by the blocks in front of them — pass every static
check and are obvious the moment the page is rendered.
