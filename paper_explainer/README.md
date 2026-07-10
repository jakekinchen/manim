# "Attention Is All You Need" — a layman's explainer, made with Manim

This folder contains a self-contained Manim scene that explains the 2017
Transformer paper ([Vaswani et al., *Attention Is All You Need*](https://arxiv.org/abs/1706.03762))
to a general audience — no math, no jargon, ~3.5 minutes, silent with
on-screen captions.

## The story it tells

| Part | What the viewer sees |
|---|---|
| **Title** | The paper's title, with the title's own words *attending* to each other — a visual foreshadow. |
| **1 · How machines read** (background) | Words become lists of numbers → points on a "map of meaning". Similar words cluster. The word *bank* slides toward *river* or *money* depending on its sentence: **meaning comes from context**, so words must share information. |
| **2 · The problem** | Pre-2017 AI (RNNs) read one word at a time, squeezing everything into one small overwritten memory. Two walls: ① distant words fade (a game of telephone shown as decaying hand-offs), ② strictly ordered reading leaves massively parallel chips idle. |
| **3 · The idea** (solution) | Delete sequential reading. Every word looks at every other word directly — *attention*. The paper's famous example: in "The animal didn't cross the street because **it** was too tired", *it* attends to *animal*; change *tired* → *wide* and it re-aims to *street*. A gentle question/answer picture of Query–Key–Value, then the punchline: everyone attends simultaneously, so both walls fall at once. Multi-head attention and stacked layers, then the name: **the Transformer**. |
| **Epilogue** | 2017 → BERT → GPT-3 → ChatGPT → Claude/Gemini. "The T in ChatGPT stands for Transformer." |

## Rendering

From the repository root, with this repo's manim installed
(`uv pip install -e .` — no LaTeX needed, the scene uses only pango `Text`):

```bash
# high quality (1080p60)
manim render -qh paper_explainer/attention_is_all_you_need.py AttentionIsAllYouNeed

# fast draft (480p15)
manim render -ql paper_explainer/attention_is_all_you_need.py AttentionIsAllYouNeed
```

While iterating you can render a subset of chapters (0–4):

```bash
CHAPTERS=3 manim render -ql paper_explainer/attention_is_all_you_need.py AttentionIsAllYouNeed
```

The video is silent by design; captions are timed to reading speed (~3s per
line). It works well with a voice-over reading the captions verbatim.
