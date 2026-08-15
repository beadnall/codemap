# codemap

Turn a codebase into an explorable diagram: isometric blocks on a grid, a
component index, a what-it-does / how-it's-built panel, and the system's own
data moving along the edges as dots the reader can stop and inspect.

**The instructions are in [SKILL.md](SKILL.md). Read that file, then follow it.**
This page exists so that agents which do not read Anthropic's skill format can
still find them.

## If you are Claude

You already have this as a skill if it is installed in `~/.claude/skills/` or
`<repo>/.claude/skills/`. Nothing here to do.

## If you are Grok Build

Install the skill into one of the discovery paths:

```
~/.grok/skills/codemap/          # or <repo>/.grok/skills/codemap/
```

Then ask for a map normally — "map this codebase", "codemap this repo",
"diagram the architecture". Grok Build picks up `SKILL.md` automatically, so
there is no separate instructions file to copy.

**Delivery.** Write the finished HTML to disk, for example `codemap.html`, and
tell the user the path. The page is self-contained and opens in any browser
with no server.

## If you are another agent

Nothing in the method is Claude-specific. The template is plain HTML and
JavaScript, the scripts are Python, and the instructions are markdown. Two
details differ:

- **Triggering.** There is no frontmatter for you to match on, so this only
  runs when the user asks for it and points you here.
- **Delivery.** SKILL.md's last step suggests an artifact or canvas if you have
  one. If you do not, write the file to disk and tell the user the path. It is
  self-contained by design and opens in any browser with no server.

Everything else — mining the repository for facts, choosing nodes and edges,
filling the four arrays, verifying, rendering — applies unchanged.

## The short version

```bash
cp assets/template.html my-map.html
# replace STATS, NODES, EDGES and REGIONS, plus <title> and the <svg aria-label>
python3 scripts/verify.py my-map.html
python3 scripts/render.py my-map.html render.png
```

Then look at `render.png`. Do not skip that: every fault that mattered while
this was being built passed the static checks and was obvious in the render.

## The part that decides whether it is any good

Not the rendering — that is already written. A diagram of boxes labelled
*Service*, *Database* and *API* tells a reader nothing they could not have
guessed from the directory listing.

Spend the effort on mining the repository for the things that are genuinely
hard to find: measured numbers, platform limits the code works around, comments
explaining why a constant is the value it is. Put those in the panel, and put
real values on the edges — `2 OpenWrite 0 2 0 3` teaches, `Instruction` does not.

Two tests before you hand it over:

- Pick any three nodes. What does a reader learn that the file listing would
  not have told them?
- Could this diagram be relabelled for a different project without changing its
  structure?

If the answers are "nothing" and "yes", go back to the repository. No amount of
rendering supplies facts you did not find.
