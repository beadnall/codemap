---
name: codemap
description: Turns a codebase into an explorable isometric architecture diagram — a self-contained HTML artifact with blocks on a grid, a component index, a what-it-does/how-it's-built panel, and real data snippets travelling along the edges that the reader can stop and inspect. Use this whenever someone asks for a codemap by name — "create a codemap", "codemap this repo", "make a codemap of github.com/owner/name" — and equally when they want to see, map, diagram or visually explain how a system fits together: "diagram this codebase", "show me the architecture", "map how this works", "visualise the data flow", "something I can walk a new engineer through". It works on a local checkout or on a remote repository read through the GitHub API. Reach for it on any request for an architecture overview, even when the word diagram never appears, since a map is almost always a better answer to that question than prose.
---

# Codemap

A diagram of a system that someone can actually explore: isometric blocks on a
grid, an index of components down the left, an explanatory panel on the right,
and the system's own data moving along the edges as dots you can stop and read.

The point is not decoration. A map like this earns its place when it answers
questions faster than reading the source would — which means it lives or dies on
the **facts you put in it**, not on the rendering. A diagram of boxes labelled
"Service", "Database" and "API" tells a reader nothing they could not have
guessed, and takes an afternoon to produce. Budget your effort accordingly: most
of it goes into mining the repository, and very little into drawing.

## The shape of the work

1. Mine the repository for facts.
2. Choose the nodes and the edges.
3. Copy `assets/template.html`, replace four arrays.
4. Verify it, since you cannot see it.
5. Publish as an artifact.

## 1. Mine the repository for facts

Do this before you think about layout. You are looking for the things a reader
could not get from the file listing:

- **Measured numbers.** Anything the project established by running rather than
  by assuming — throughput, hit rates, limits, counts. `git log`, test files and
  long code comments are where these hide.
- **Failures and their causes.** Comments explaining why something is the way it
  is, commits that say "fix", constants with a paragraph above them. A constant
  with an explanation attached is almost always worth a node or a fact.
- **Real values in flight.** An actual payload, identifier, key format or
  message body from a fixture, a test, a log sample or a doc.
- **Platform limits the code works around.** These are usually the most
  interesting thing in any codebase and are almost never in the README.

`git log --oneline`, `grep` for long comment blocks, and read the docs
directory. If the project has a design document, read it fully — it will name
the tensions the architecture exists to resolve, which is exactly what the right
panel should carry.

If you come up with nothing specific in this pass, say so plainly rather than
proceeding to draw a generic diagram. Offer the reader something else — a
written overview, or a narrower map of one subsystem you *can* speak about
precisely.

### A repository you do not have locally

"Codemap github.com/owner/name" is a normal request, and cloning is not
required — the GitHub API serves the tree and the file contents, which is all
the mining in this section needs, and it downloads nothing and executes
nothing.

```bash
gh api repos/OWNER/NAME --jq '{stars:.stargazers_count, lang:.language, license:.license.name}'
gh api "repos/OWNER/NAME/git/trees/HEAD?recursive=1" \
  --jq '.tree[] | select(.type=="blob") | "\(.size)\t\(.path)"' | sort -rn | head -40
gh api "repos/OWNER/NAME/contents/PATH" -H "Accept: application/vnd.github.raw"
```

Sorting the tree by size finds the substance quickly: the largest source files
are where the logic is, and a `DESIGN.md` or an `ARCHITECTURE.md` is worth more
than all of them together.

Two things to note when the code is not yours. Check the licence — absent means
all rights reserved, so describe the architecture rather than reproducing code,
which is what this format does anyway. And say plainly in your summary that one
pass over an unfamiliar repository can produce confident statements that are
subtly wrong; the failure mode of doing this well is sounding authoritative.

## 2. Choose the nodes and edges

Aim for **15–20 nodes**. Fewer and it is a sketch; more and the labels collide
and nobody reads it.

Group them into four or five stages that read left to right along the data's
path — where things enter, what interprets them, what derives meaning, what the
user sees. Group names should be plain and specific to the domain ("What
arrives", "The measurements") rather than the architecture-astronaut vocabulary
("Ingestion layer", "Domain services").

Block **height carries weight**: give the parts that hold the most logic taller
blocks. A reader scanning the diagram should be able to see where the mass of
the system is without reading a word.

### Several of a kind

Where a block is really *n* variants of one thing — two implementations of an
interface, the table and index forms of one structure, four parsers with the
same shape — set `stack: n` and it draws as that many plates rather than one
solid block.

```js
{c:"O", id:"vfs", name:"OS interface", gx:4, gy:1, h:26, stack:2, …}
```

The plates **split** the height rather than adding to it, so the two encodings
stay independent: height still says how much logic is here, and the plate count
says how many things of one kind it is. A stack of four never outweighs a taller
neighbour just for being subdivided.

Keep `n` between 2 and 5, and keep it *true*. If something is seven files of one
kind, don't draw five plates and hope nobody counts — stack at the number of
genuine variants, or leave it solid and put the figure in `facts`. The plate
count is a claim like every other number in the diagram.

Stacking is also a reason to **merge nodes**. If you find yourself drawing three
near-identical blocks side by side, they are usually one stacked block with the
differences described in the panel — and merging buys back a node to spend on
something that isn't a repetition.

For each node write three things:

- **`does`** — what it is for, in the reader's terms. This is where a measured
  fact belongs: not "chooses the join order" but "chooses the join order — and
  its predecessor, taking the cheapest table at each step, picked a plan
  *roughly 750× slower* than the best one on an eight-way join."
- **`built`** — the file, the API, and ideally the mistake. The most valuable
  sentence in a diagram is often "this was wrong twice, and here is why."
- **`facts`** — two or three label/value pairs. Thresholds, rates, measured
  ratios.

For each edge, write the **datum that crosses it** — a real value, not a type
name. `2 OpenWrite 0 2 0 3` teaches; `BytecodeInstruction` does not. Add a
one-line `whence` explaining what the reader is looking at.

### What is not yours

Draw a **dashed outline** around anything the repository does not own: a
vendored dataset, a dependency you only call, a service another team runs, a
binary blob nobody has the source for. This is worth doing even when it is only
one block, because "who would I have to ask to change this?" is the question a
new engineer asks third, after what it does and what talks to it, and a
codemap that answers it saves a conversation.

```js
const REGIONS = [
  {label:"Not in the tree", of:["th3","fuzz"],
   note:"TH3 and dbsqlfuzz belong to SQLite's authors but are not distributed
         with it. The coverage figures everyone quotes are TH3's."},
];
```

`of` is a list of node ids and the outline is the box that contains them, drawn
flat on the floor so the blocks stand up out of it. **The blocks themselves are
drawn with dashed edges too**, which is what makes the treatment survive being
read: a reader who has panned away from the boundary, or zoomed past it, still
has the cube in front of them telling them whose code it is. The outline says
where the border runs; the dashes say which blocks it is about. Both keep the
dashing when selected, so it never reads as a highlight state.

Two things follow from the outline being a box. **Lay the members next to each
other on the grid** — it is a box in grid space, so a region naming two nodes at
opposite corners will quietly enclose everything between them. And **give it an
edge of the grid if you can**:
the outline reaches about half a cell beyond its members, and a region wedged
into the middle of a dense map has its caption fighting the node names around
it.

`label` is drawn on the canvas, so keep it to about 16 characters and let it
say the *relationship* — "Vendored", "Upstream", "Platform", "Another team" —
rather than repeating the block's own name. `note` appears only in the right
panel, when the reader clicks a block inside the outline, so it can be a full
sentence: the repository, the licence, who maintains it, when it was last
pulled. That is the sentence that actually answers the question, and putting it
on the canvas would only crowd the drawing.

Regions are optional. `const REGIONS = [];` is a perfectly good answer for a
system that is all its own code, and inventing one to use the feature is worse
than leaving it out.

## 3. Build it

Copy `assets/template.html` and replace `STATS`, `NODES`, `EDGES` and
`REGIONS`, plus two strings outside them that are easy to miss: the `<title>`
and the `aria-label` on the `<svg>`. Both are marked `REPLACE`. The chrome, the
isometric projection, the panning, zooming and animation all work already —
reinventing them wastes the effort that should go into content.

The `aria-label` is the only description a screen-reader user gets of the whole
diagram, since the blocks themselves are shapes. Write it as a sentence naming
the system and the path through it, not as "architecture diagram".

Node positions are grid coordinates, projected with

```
x = (gx - gy) * 78        y = (gx + gy) * 39
```

so `gx` is the stage along the flow and `gy` the row within it. Keep `gx` in
0–4 and `gy` in 0–4 and the layout resolves itself.

Set the `<title>` to a name for the *system's story*, not a description of the
page — "The Signal Path", not "Architecture Diagram". It is what the reader sees
in a gallery beside a dozen others.

### Palette

The template ships a dark instrument face: a near-black ground with a faint
isometric grid, structure in a deep blue, and the moving data in orange. The
single warm colour is doing the work — it means the data reads as the one live
thing on an otherwise static drawing, and everything else recedes.

Keep the orange for the dots whatever else changes. If the subject has colours
of its own worth using — a product's brand, a language's syntax convention —
shift the blue toward them rather than replacing the scheme, and leave the data
alone. Deriving that shift from the subject is most of what stops the result
looking generated.

Keep it a single committed theme with every colour painted explicitly;
artifacts render against a ground you do not control, so nothing may rely on
inheriting a background.

The artifact CSP blocks every external request. No font CDNs, no image hosts,
no script tags pointing outward. The template is already self-contained; keep it
that way.

## 4. Render it and look at it

You can render this locally, and you should. Everything below was found by
looking at a page that had already passed every static check.

```bash
python3 scripts/verify.py <your-page.html>
python3 scripts/render.py <your-page.html> render.png 1600 1000
```

Both work on macOS, Linux and Windows. `render.py` drives Chrome, Chromium,
Edge or Brave headless, and falls back to `render.swift` and the system WebKit
on a Mac with none of them. The syntax check needs node, bun or deno off a Mac,
and skips rather than failing when there is no engine to run.

`verify.py` compiles the script with the first JavaScript engine it finds —
node, bun, deno, or JavaScriptCore on a Mac. A syntax error is reported; a `ReferenceError:
Can't find variable: document` means the script is **valid** — it compiled and
then failed on the DOM it does not have. It also checks that every edge names a
real node, that every region encloses real nodes, that a stacked node's plates
are thick enough to see, that the default selection resolves, that node names
and region labels fit under a block, and that nothing external is referenced.

A region with a mistyped id is the one to watch for: unknown ids are dropped
when the page builds, so the outline silently shrinks around the members that
did resolve — or disappears entirely — rather than failing. It looks like a
layout decision, which is why `verify.py` checks it rather than the render.

`render.swift` loads the page in an offscreen WKWebView, runs its JavaScript,
waits two seconds for the layout and the animation to settle, and writes a PNG
you can actually open. Do this before publishing. Three faults got through
static analysis and were obvious in the render:

- **An empty right-hand panel**, because the default selection named a node
  from a different project. `render()` threw on an undefined lookup before
  drawing anything. The page looked structurally perfect.
- **Names clipped by neighbouring blocks**, because labels were drawn inside
  each node's group and blocks are painted back to front. It reads as a
  truncated string, not as a z-order problem, so it is easy to misdiagnose as
  a name being too long. Labels now live in their own layer above everything.
- **Mojibake** — em dashes as `a€`. WKWebView assumes Latin-1 for a `file://`
  document with no charset, so this one is the renderer's fault rather than the
  page's, and `render.swift` now loads the string as UTF-8. Worth knowing
  because it looks exactly like a broken page.

Keep node names to about **16 characters**. They are centred under the block,
and longer ones crowd their neighbours even with the label layer.

## 5. Hand it over

The page is one self-contained file, so how it reaches the reader depends on
where you are running. If an artifact or canvas tool is available, publish it
there and give it a favicon and a one-sentence description. Otherwise write it
somewhere sensible and say where — the file opens in any browser with no
server, which is the reason it was built self-contained.

Either way, tell the reader what to do with it: which block to click first, and
that the dots can be stopped and inspected. Nobody guesses that unprompted, and
it is the part that makes the diagram worth more than a picture. If the map has
anything dashed on it, say in one clause what that means — "the dashed blocks
are code we don't own" — because it is a convention and the reader has no way
to know it.

## What makes these good or bad

The failure mode is a diagram that is pretty and says nothing. It happens when
the nodes are named after architectural roles instead of after what they do, and
when the edges carry type names instead of values. Both are easy to slip into,
because both can be produced without understanding the system — which is the
tell.

The test to apply before publishing: **pick any three nodes and ask what a
reader learns from them that they could not have guessed from the directory
listing.** If the answer is nothing, go back to step 1. You do not have enough
facts yet, and no amount of rendering will supply them.

The second test: **could this diagram be relabelled for a different project
without changing its structure?** If yes, it is a template with a subject
sprinkled on, not a map of this system.
