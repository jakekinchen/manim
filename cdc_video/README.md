# TWICE — the Cycle Double Cover proof, explained visually

A ~10-minute layman-oriented Manim video explaining *"A Proof of the Cycle
Double Cover Conjecture"* (2026): the background, the problem, and the
proof's actual mechanism.

**Watch:** `TWICE_cdc_explainer.mp4` (1080p30, no audio — captions carry the
narration).

## Story arc

| Ch | Title | Idea |
|----|-------|------|
| 0 | Twice | Title tease: loops covering the Petersen graph |
| 1 | The game | Trace loops so every road is covered exactly twice; junction parity forces "twice" |
| 2 | Maps already know the answer | Flat networks: regions walk their borders → automatic double cover |
| 3 | The one true obstacle | Bridges can't lie on loops; the conjecture says bridges are the *only* obstacle |
| 4 | Where it gets hard | Reduce to 3-way junctions; 3-edge-coloring solves it; the Petersen graph (snark) refuses — odd loops |
| 5 | Eight colors that cancel | The 8-flow theorem: 3-bit codes on roads, cancelling (XOR) at every junction |
| 6 | The move: wear two colors | The paper's reduction: dress each road in TWO of 8 colors, each color 0/2 at a junction → color classes are loops → double cover (Lemma 2.1) |
| 7 | A local recipe — and a handshake | From flow values x, y, x⊕y build pair-triangles at each junction; ends must agree → parity equations (eq. 4) |
| 8 | Two ends — the parity miracle | Duality: any obstruction totals each road once per end — twice = 0 in F₂ (Lemma 2.2). QED |
| 9 | The machine runs | The paper's construction executed on the Petersen graph: real flow → real pairs → 5 loops; then the six-pentagon (hemi-dodecahedral) double cover |

## Faithfulness

Everything shown is computed, not staged. `verify_math.py`:

- checks the cube's pair-label scheme reproduces its 6 faces,
- checks the six-pentagon CDC of the Petersen graph,
- finds a nowhere-zero F₂³ flow on Petersen, builds the paper's local
  offsets (eq. 2), solves the agreement system (eq. 4) by Gaussian
  elimination over F₂ (Lemma 2.2 in action), builds the pair labels,
  verifies the local condition (1), and extracts the cycle double cover
  shown in chapter 9,
- verifies Petersen is not 3-edge-colorable and that all six of its
  perfect matchings leave two odd 5-cycles (the chapter-4 argument).

## Render

```bash
pip install manim   # >= 0.19 (PyAV writer; no LaTeX needed — Pango text only)
cd cdc_video
manim render -r 1920,1080 --fps 30 cdc_explainer.py \
  Ch0Title Ch1Game Ch2Maps Ch3Bridges Ch4Snarks \
  Ch5Flow Ch6TwoColors Ch7Recipe Ch8Miracle Ch9Finale
```

Concatenate the chapter mp4s in order (any tool; the video has no audio
track).
