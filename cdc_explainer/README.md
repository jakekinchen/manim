# TWICE — the Cycle Double Cover proof, explained for everyone

A ~8-minute, layman-oriented Manim video about the **Cycle Double Cover
Conjecture** — the fifty-year-old puzzle whose proof was announced on
**July 10, 2026** (reported as found by an AI model; under expert review) —
covering the background, the problem, and the announced proof's central
mechanism.

**Watch:** `TWICE_cdc_explainer.mp4` (1080p30, silent by design — the
on-screen captions carry the narration; it works muted and with voice-over).

## The story it tells

| Ch | Title | Idea |
|----|-------|------|
| 0 | Title | The real 5-loop double cover of the Petersen graph draws itself |
| 1 | The game | Round trips; every road exactly twice. Junction close-up: trips use roads in pairs, 3 is odd → once is impossible, twice is the smallest fair ask |
| 2 | Maps already know the answer | Flat networks: every road has two sides; regions walking their borders cover each road exactly twice — the outside counts too. Petersen refuses to lie flat |
| 3 | Fifty years of stuck | Bridges are the one honest obstacle (a round trip that crosses is stranded). The conjecture (Szekeres 1973, Seymour 1979) — and the July 10, 2026 announcement |
| 4 | The easy half — and the snark | Reduce to 3-way junctions; 3-painting wins the game (color-duos chain into loops); the Petersen graph can't be 3-painted (odd ring) — a snark |
| 5 | Eight codes that cancel | Jaeger's 8-flow theorem as light-switch codes: color = mix of lit R/G/B switches, combining = toggling, x⊕y⊕z = OFF at every junction |
| 6 | The move: wear two colors | The paper's reduction: dress each road in a PAIR of colors, each color appearing 0 or 2 times per junction → color classes chain into loops → double cover (Lemma 2.1) |
| 7 | The junction triangle | The local recipe: from stamps x, y, z a closed 3-hop walk in color space — a triangle; each road wears one side; the law holds by design (eq. 2) |
| 8 | The handshake | Both ends of a road must pick the same pair: a web of demands (eq. 4). The parity lemma: any closed chain of demands counts every junction twice — and twice = OFF (Lemma 2.2) |
| 9 | The machine runs | The construction executed on the Petersen graph with real computed data: stamps → triangles → pairs → junction check → 5 loops, every road ×2 |
| 10 | Epilogue | Timeline 1973 → 2026; what the theorem promises; end card |

## Faithfulness

Everything on screen is computed, not staged. `verify_math.py`:

- verifies the cube's map/3-coloring/pair-label double covers (and that all
  three give the same six loops),
- proves Petersen is not 3-edge-colorable (exhaustive) and that each of its
  6 perfect matchings leaves two odd 5-cycles (the on-screen parity clash),
- runs the paper's full construction on Petersen: nowhere-zero F₂³ flow →
  local offsets (junction triangles) → agreement system over F₂ → pair
  labels → local even-ness condition → extraction of the 5-cycle double
  cover shown in chapter 9,
- checks the junction-triangle fact at every vertex (the three pairs at a
  vertex are the sides of a triangle in F₂³),
- stress-tests the pipeline on K₄, K₃,₃, the 3-prism, the Möbius–Kantor
  graph and 300 random bridgeless cubic graphs with random flows and
  scrambled edge orderings — the agreement system solved every time
  (Lemma 2.2 in action),

and dumps `cdc_data.json`, which `scenes.py` loads — so the video's flows,
pairs and loops are the verified ones.

> **Provenance note.** The full text of the announced proof was not publicly
> retrievable when this was made; the construction animated here follows the
> flow→pair-labeling mechanism attributed to it (its Lemmas 2.1/2.2 and
> eqs. 2/4), every instance of which is verified computationally by
> `verify_math.py`. The video flags the announcement as "under expert
> review".

## Rendering

From the repository root, with this repo's manim installed
(`uv sync` — no LaTeX needed; the video uses Pango text only):

```bash
cd cdc_explainer
python verify_math.py       # regenerates cdc_data.json (optional; committed)

# fast draft (480p15)
manim render -ql scenes.py C00Title C01Game C02Maps C03Conjecture C04Snark \
    C05Mixes C06TwoColors C07Triangle C08Handshake C09Machine C10End

# final (1080p30)
manim render -r 1920,1080 --fps 30 scenes.py C00Title C01Game C02Maps \
    C03Conjecture C04Snark C05Mixes C06TwoColors C07Triangle C08Handshake \
    C09Machine C10End
```

Then concatenate the chapter mp4s in order (e.g. ffmpeg concat demuxer; the
video has no audio track).
