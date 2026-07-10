"""
"Attention Is All You Need" (Vaswani et al., 2017) — explained for laymen.

A single self-contained Manim scene that tells the story of the Transformer
paper in three acts: the background (how machines read), the problem
(sequential reading), and the solution (self-attention).

Render (from the repo root, with manim installed):

    manim render -qh paper_explainer/attention_is_all_you_need.py AttentionIsAllYouNeed

The video is silent; all narration is carried by timed on-screen captions.
Set the environment variable CHAPTERS (e.g. CHAPTERS=3 or CHAPTERS=1,3) to
render a subset of chapters while iterating.
"""

from __future__ import annotations

import os

from manim import *

# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------

FONT = "Liberation Sans"
MONO = "DejaVu Sans Mono"

BG = "#0d1117"        # page background
INK = "#e6edf3"       # primary text
MUT = "#8b949e"       # muted text
FAINT = "#30363d"     # hairlines / token strokes
CARD = "#161b22"      # token / card fill

BLUE = "#58a6ff"      # attention / solution
YELLOW = "#e3b341"    # highlight / focus word
ORANGE = "#f0883e"    # the old way (RNN)
RED = "#f85149"       # problems
GREEN = "#3fb950"     # solved / good
PURPLE = "#bc8cff"    # secondary accent
TEAL = "#39c5cf"      # tertiary accent

CAPTION_Y = -3.42     # fixed caption baseline
MAX_CAPTION_W = 12.6

config.background_color = BG


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


# ---------------------------------------------------------------------------
# Small builders
# ---------------------------------------------------------------------------

def make_token(word: str, font_size: int = 28, pad: float = 0.14,
               height: float | None = None, fill: str = CARD,
               stroke: str = FAINT, text_color: str = INK) -> VGroup:
    """A word in a rounded box. tok[0] is the box, tok[1] the text."""
    txt = Text(word, font=FONT, font_size=font_size, color=text_color)
    h = height if height is not None else font_size / 28 * 0.58
    box = RoundedRectangle(
        corner_radius=0.08,
        width=txt.width + 2 * pad,
        height=h,
        fill_color=fill, fill_opacity=1.0,
        stroke_color=stroke, stroke_width=1.6,
    )
    txt.move_to(box.get_center())
    return VGroup(box, txt)


def token_row(words, font_size=28, gap=0.11, **kw) -> VGroup:
    row = VGroup(*[make_token(w, font_size=font_size, **kw) for w in words])
    row.arrange(RIGHT, buff=gap)
    return row


def attn_arc(src: Mobject, dst: Mobject, weight: float,
             color=BLUE, below: bool = False) -> ArcBetweenPoints:
    """An attention arc between two tokens, weight in [0, 1]."""
    a, b = src.get_top(), dst.get_top()
    if below:
        a, b = src.get_bottom(), dst.get_bottom()
    # order endpoints left -> right so one angle sign always bulges the same way
    if a[0] > b[0]:
        a, b = b, a
    dist = abs(b[0] - a[0])
    ang = -clamp(1.7 - 0.09 * dist, 0.7, 1.6)
    if below:
        ang = -ang
    arc = ArcBetweenPoints(a, b, angle=ang, color=color)
    arc.set_stroke(width=1.0 + 6.0 * weight, opacity=0.16 + 0.84 * weight)
    return arc


def labeled_dot(label: str, color, font_size=22) -> VGroup:
    d = Dot(radius=0.075, color=color)
    t = Text(label, font=FONT, font_size=font_size, color=INK)
    t.next_to(d, UR, buff=0.04)
    return VGroup(d, t)


def gpu_grid(rows=5, cols=9, s=0.36, buff=0.10) -> VGroup:
    cells = VGroup(*[
        Square(s, fill_color="#1a2333", fill_opacity=1.0,
               stroke_color="#2c3a50", stroke_width=1.2)
        for _ in range(rows * cols)
    ])
    cells.arrange_in_grid(rows=rows, cols=cols, buff=buff)
    return cells


def card(lines, color=RED, w=4.6) -> VGroup:
    txts = VGroup(*[
        Text(s, font=FONT, font_size=26, color=INK) for s in lines
    ]).arrange(DOWN, buff=0.14)
    box = RoundedRectangle(corner_radius=0.14, width=w,
                           height=txts.height + 0.7,
                           fill_color=CARD, fill_opacity=1.0,
                           stroke_color=color, stroke_width=2.2)
    txts.move_to(box.get_center())
    return VGroup(box, txts)


# ---------------------------------------------------------------------------
# The scene
# ---------------------------------------------------------------------------

class AttentionIsAllYouNeed(Scene):
    """~3.5 minute layman's tour of the Transformer paper."""

    # ---------------- caption / chapter machinery ----------------

    def setup(self):
        self._caption: Mobject | None = None
        self._kicker: Mobject | None = None

    def say(self, text: str, t: float | None = None, color=INK):
        """Show a caption at the bottom and hold long enough to read it."""
        m = Text(text, font=FONT, font_size=30, color=color,
                 line_spacing=0.9, disable_ligatures=True)
        if m.width > MAX_CAPTION_W:
            m.scale_to_fit_width(MAX_CAPTION_W)
        m.move_to([0, CAPTION_Y, 0])
        # swap in two phases so the old and new caption never superimpose
        if self._caption is not None:
            self.play(FadeOut(self._caption, shift=DOWN * 0.08), run_time=0.22)
        self.play(FadeIn(m, shift=UP * 0.12), run_time=0.3)
        self._caption = m
        dur = t if t is not None else clamp(0.30 * len(text.split()) + 1.0, 2.4, 7.0)
        self.wait(dur)

    def drop_caption(self):
        if self._caption is not None:
            self.play(FadeOut(self._caption), run_time=0.35)
            self._caption = None

    def chapter(self, kicker: str):
        m = Text(kicker, font=FONT, font_size=21, color=MUT, weight=BOLD)
        m.to_corner(UL, buff=0.42)
        anims = [FadeIn(m, shift=RIGHT * 0.15)]
        if self._kicker is not None:
            anims.append(FadeOut(self._kicker))
        self.play(*anims, run_time=0.5)
        self._kicker = m

    def clear_stage(self, *keep, run_time=0.6):
        keepset = {self._caption, self._kicker, *keep} - {None}
        doomed = [m for m in self.mobjects if m not in keepset]
        if doomed:
            self.play(*[FadeOut(m) for m in doomed], run_time=run_time)

    # ---------------- construct ----------------

    def construct(self):
        want = os.environ.get("CHAPTERS", "all")
        chapters = [self.ch0_title, self.ch1_background,
                    self.ch2_problem, self.ch3_solution, self.ch4_legacy]
        if want != "all":
            idx = {int(i) for i in want.split(",")}
            chapters = [c for n, c in enumerate(chapters) if n in idx]
        for c in chapters:
            c()

    # ---------------- chapter 0 : title ----------------

    def ch0_title(self):
        words = VGroup(*[
            Text(w, font=FONT, font_size=58, weight=BOLD, color=INK)
            for w in ["Attention", "Is", "All", "You", "Need"]
        ]).arrange(RIGHT, buff=0.42).move_to(UP * 0.9)

        byline = Text("Vaswani et al.  ·  Google  ·  2017",
                      font=FONT, font_size=26, color=MUT)
        byline.next_to(words, DOWN, buff=0.55)

        self.play(LaggedStart(*[FadeIn(w, shift=UP * 0.25) for w in words],
                              lag_ratio=0.18), run_time=1.6)
        self.play(FadeIn(byline), run_time=0.7)

        # foreshadow: the title itself attends to the word "Attention"
        arcs = VGroup(*[
            attn_arc(words[0], words[j], w, color=BLUE)
            for j, w in [(1, 0.25), (2, 0.45), (3, 0.3), (4, 0.85)]
        ])
        self.play(LaggedStart(*[Create(a) for a in arcs], lag_ratio=0.15),
                  run_time=1.4)

        self.say("The 15-page paper that created modern AI —", t=2.6)
        self.say("explained simply, with no math.", t=2.6)

        self.clear_stage()

    # ---------------- chapter 1 : background ----------------

    def ch1_background(self):
        self.chapter("PART 1  ·  HOW MACHINES READ")

        # --- beat 1: words become numbers -------------------------------
        tok = make_token("cat", font_size=44, pad=0.22)
        tok.move_to(LEFT * 3.6 + UP * 0.8)
        arrow = Arrow(tok.get_right(), tok.get_right() + RIGHT * 1.5,
                      buff=0.15, color=MUT, stroke_width=3)
        vec = Text("[ 0.62,  −1.03,  0.41,  2.27,  … ]",
                   font=MONO, font_size=30, color=TEAL)
        vec.next_to(arrow, RIGHT, buff=0.25)

        self.play(FadeIn(tok, scale=0.8), run_time=0.6)
        self.say("Computers can't read words. They can only crunch numbers.")
        self.play(GrowArrow(arrow), FadeIn(vec, shift=RIGHT * 0.2), run_time=0.9)
        self.say("So the first step of reading is a swap: every word becomes a list of numbers.")

        # --- beat 2: the map of meaning ---------------------------------
        self.play(FadeOut(tok), FadeOut(arrow), FadeOut(vec), run_time=0.5)

        panel = RoundedRectangle(corner_radius=0.2, width=10.8, height=4.7,
                                 fill_color="#10161f", fill_opacity=1.0,
                                 stroke_color=FAINT, stroke_width=1.5)
        panel.move_to(UP * 0.25)
        panel_title = Text("the map of meaning", font=FONT, font_size=22,
                           color=MUT, slant=ITALIC)
        panel_title.next_to(panel.get_top(), DOWN, buff=0.18)

        P = panel.get_center()
        animals = VGroup(
            labeled_dot("cat", GREEN).move_to(P + LEFT * 3.6 + UP * 0.9),
            labeled_dot("kitten", GREEN).move_to(P + LEFT * 2.7 + UP * 1.3),
            labeled_dot("dog", GREEN).move_to(P + LEFT * 2.9 + UP * 0.45),
        )
        vehicles = VGroup(
            labeled_dot("car", PURPLE).move_to(P + RIGHT * 2.6 + UP * 1.2),
            labeled_dot("truck", PURPLE).move_to(P + RIGHT * 3.5 + UP * 0.75),
        )
        nature = VGroup(
            labeled_dot("river", TEAL).move_to(P + LEFT * 3.4 + DOWN * 1.05),
            labeled_dot("water", TEAL).move_to(P + LEFT * 2.3 + DOWN * 1.5),
        )
        money = VGroup(
            labeled_dot("money", YELLOW).move_to(P + RIGHT * 2.7 + DOWN * 1.2),
            labeled_dot("loan", YELLOW).move_to(P + RIGHT * 3.6 + DOWN * 1.55),
        )

        self.play(FadeIn(panel), FadeIn(panel_title), run_time=0.7)
        self.play(LaggedStart(
            *[FadeIn(d, scale=0.5) for grp in (animals, vehicles, nature, money)
              for d in grp], lag_ratio=0.1), run_time=2.0)
        self.say("Those numbers work like coordinates: they place every word on a huge map of meaning.")
        self.say("Words that mean similar things land close together.")

        # --- beat 3: 'bank' needs its neighbours -------------------------
        bank = labeled_dot("bank", INK, font_size=24)
        bank.move_to(P + RIGHT * 0.1 + DOWN * 0.3)
        qmark = Text("?", font=FONT, font_size=30, color=RED, weight=BOLD)
        qmark.next_to(bank, UP, buff=0.12)
        self.play(FadeIn(bank, scale=0.5), FadeIn(qmark), run_time=0.8)
        self.say("But where does “bank” go?  Alone, it is ambiguous.")

        s1 = Text("“I sat on the bank of the river.”",
                  font=FONT, font_size=28, color=INK, t2c={"bank": TEAL})
        s1.to_edge(UP, buff=0.35).shift(RIGHT * 1.2)
        self.play(FadeIn(s1, shift=DOWN * 0.15), FadeOut(qmark), run_time=0.7)
        self.play(bank.animate.move_to(P + LEFT * 3.2 + DOWN * 0.35),
                  run_time=1.3)
        self.say("Next to “river”, it slides toward the water…")

        s2 = Text("“The bank raised the interest rate.”",
                  font=FONT, font_size=28, color=INK, t2c={"bank": YELLOW})
        s2.move_to(s1.get_center())
        self.play(FadeOut(s1, shift=UP * 0.15), FadeIn(s2, shift=DOWN * 0.15),
                  run_time=0.7)
        self.play(bank.animate.move_to(P + RIGHT * 3.0 + DOWN * 0.55),
                  run_time=1.3)
        self.say("…next to “interest rate”, toward the money.")
        self.say("Meaning comes from context. So words must share information with their neighbours.")
        self.say("HOW they share it is the whole game — and where our story begins.")

        self.clear_stage()

    # ---------------- chapter 2 : the problem ----------------

    def ch2_problem(self):
        self.chapter("PART 2  ·  THE PROBLEM")

        # --- beat 1: the one-word-at-a-time reader ----------------------
        sentence = ["The", "cat", "sat", "on", "the", "mat"]
        colors = [BLUE, GREEN, YELLOW, PURPLE, TEAL, ORANGE]
        row = token_row(sentence, font_size=28)
        row.move_to(LEFT * 3.4 + UP * 0.6)

        machine = RoundedRectangle(corner_radius=0.18, width=3.1, height=1.7,
                                   fill_color=CARD, fill_opacity=1.0,
                                   stroke_color=ORANGE, stroke_width=2.5)
        machine.move_to(RIGHT * 3.6 + UP * 0.6)
        mlabel = Text("the reader", font=FONT, font_size=24, color=ORANGE)
        mlabel.move_to(machine.get_center() + DOWN * 0.45)

        mem_frame = Rectangle(width=2.4, height=0.42, stroke_color=MUT,
                              stroke_width=1.8)
        mem_frame.move_to(machine.get_center() + UP * 0.25)
        mem_label = Text("its one small memory", font=FONT, font_size=19,
                         color=MUT)
        mem_label.next_to(mem_frame, UP, buff=0.5)

        self.play(FadeIn(row), FadeIn(machine), FadeIn(mlabel),
                  FadeIn(mem_frame), FadeIn(mem_label), run_time=0.9)
        self.say("Before 2017, the best AI read like this:", t=2.2)

        segs: list[Mobject] = []

        def mem_target(cols):
            """Segments squeezed into the frame, newest widest."""
            W, H = mem_frame.width - 0.06, mem_frame.height - 0.06
            weights = [0.62 ** (len(cols) - 1 - i) for i in range(len(cols))]
            total = sum(weights)
            group, x = VGroup(), mem_frame.get_left()[0] + 0.03
            for wgt, c in zip(weights, cols):
                w = W * wgt / total
                r = Rectangle(width=w, height=H, fill_color=c,
                              fill_opacity=0.92, stroke_width=0)
                r.move_to([x + w / 2, mem_frame.get_center()[1], 0])
                group.add(r)
                x += w
            return group

        used_colors = []
        for i, tok in enumerate(row):
            used_colors.append(colors[i])
            target = mem_target(used_colors)
            ghost = tok.copy()
            anims = [
                ghost.animate.move_to(machine.get_center()).scale(0.25).set_opacity(0),
                tok.animate.set_opacity(0.28),
                Indicate(machine, scale_factor=1.02, color=ORANGE),
            ]
            if segs:
                anims.append(Transform(segs[0], target))
            self.add(ghost)
            self.play(*anims, run_time=0.55)
            self.remove(ghost)
            if not segs:
                segs.append(target)
                self.add(target)

        self.say("One word at a time, in order — squeezing everything so far into one small memory.")
        self.say("Every new word overwrites a little of what came before.")

        self.clear_stage()

        # --- beat 2: distance = decay ------------------------------------
        long_words = ["The", "cat,", "after", "a", "long", "afternoon",
                      "on", "the", "windowsill,", "was", "____"]
        lrow = token_row(long_words, font_size=25, gap=0.1)
        lrow.move_to(UP * 1.3)
        cat_i, blank_i = 1, len(long_words) - 1
        lrow[cat_i][1].set_color(GREEN)
        lrow[blank_i][0].set_stroke(color=YELLOW, width=2.4)

        self.play(FadeIn(lrow), run_time=0.8)
        self.say("Now a test.  Fill in the blank — what was the cat?", t=3.0)
        self.say("The answer lives 9 words back.  In this design, it must be passed hand-to-hand:")

        hops = VGroup()
        strengths = []
        for k in range(cat_i, blank_i):
            fade = 0.82 ** (k - cat_i + 1)
            strengths.append(fade)
            a = CurvedArrow(lrow[k].get_top() + UP * 0.03,
                            lrow[k + 1].get_top() + UP * 0.03,
                            angle=-1.5, color=GREEN, tip_length=0.12)
            a.set_stroke(width=3.0, opacity=fade)
            a.tip.set_opacity(fade)
            hops.add(a)
        self.play(LaggedStart(*[Create(h) for h in hops], lag_ratio=0.5),
                  run_time=4.0)

        meter_label = Text("how much of “cat” survives the trip:",
                           font=FONT, font_size=26, color=MUT)
        pct = Text("17%", font=FONT, font_size=34, weight=BOLD, color=RED)
        meter = VGroup(meter_label, pct).arrange(RIGHT, buff=0.3)
        meter.move_to(DOWN * 0.35)
        self.play(FadeIn(meter), run_time=0.7)
        self.say("Each hand-off loses a little.  Like a game of telephone, distant words fade.")
        self.say("The longer the sentence, the worse it gets.  This is problem number one.")

        self.clear_stage()

        # --- beat 3: no parallelism --------------------------------------
        grid = gpu_grid()
        grid.move_to(RIGHT * 3.3 + UP * 0.55)
        gtitle = Text("a modern chip: thousands of tiny workers",
                      font=FONT, font_size=22, color=MUT)
        gtitle.next_to(grid, UP, buff=0.3)

        queue = token_row(["The", "cat", "sat", "on", "the", "mat"],
                          font_size=24, gap=0.1)
        queue.arrange(DOWN, buff=0.14).move_to(LEFT * 4.2 + UP * 0.55)
        qtitle = Text("words wait in line", font=FONT, font_size=22, color=MUT)
        qtitle.next_to(queue, UP, buff=0.3)

        self.play(FadeIn(grid), FadeIn(gtitle), FadeIn(queue), FadeIn(qtitle),
                  run_time=0.9)
        self.say("Problem number two: order means waiting.  Word 5 cannot be read before word 4.")

        for i, tok in enumerate(queue):
            cell = grid[7 * i + 3]
            self.play(tok[0].animate.set_stroke(color=ORANGE, width=2.5),
                      cell.animate.set_fill("#f0883e", opacity=1.0),
                      run_time=0.28)
            self.play(tok.animate.set_opacity(0.3),
                      cell.animate.set_fill("#1a2333", opacity=1.0),
                      run_time=0.22)

        # keep one lonely worker lit while the caption lands
        busy = grid[22]
        self.play(busy.animate.set_fill("#f0883e", opacity=1.0), run_time=0.3)
        self.say("One worker works.  Thousands sit idle.  Training the best models took weeks.")

        self.clear_stage()

        # --- beat 4: the two walls ----------------------------------------
        c1 = card(["①  distant words fade"], color=RED)
        c2 = card(["②  reading can't be parallel"], color=RED)
        cards = VGroup(c1, c2).arrange(RIGHT, buff=0.7).move_to(UP * 0.6)
        self.play(FadeIn(c1, shift=UP * 0.2), FadeIn(c2, shift=UP * 0.2),
                  run_time=0.9)
        self.say("By 2017, these two walls were holding all of AI back.", t=3.2)
        self.say("Then eight researchers at Google asked: what if we just… stopped reading in order?")

        self.clear_stage()

    # ---------------- chapter 3 : the solution ----------------

    def ch3_solution(self):
        self.chapter("PART 3  ·  THE IDEA")

        # --- beat 1: the famous sentence ---------------------------------
        words = ["The", "animal", "didn't", "cross", "the", "street",
                 "because", "it", "was", "too", "tired"]
        row = token_row(words, font_size=25, gap=0.1)
        row.move_to(UP * 0.4)
        it_i, animal_i, street_i, tired_i = 7, 1, 5, 10

        self.play(FadeIn(row), run_time=0.9)
        self.say("Their answer: let every word look at every other word.  Directly.  All at once.")
        self.say("Take this sentence.  What does “it” refer to?", t=3.0)

        self.play(row[it_i][0].animate.set_stroke(color=YELLOW, width=3.0)
                  .set_fill("#2d2a1b"), run_time=0.5)

        weights = {animal_i: 0.92, street_i: 0.30, 3: 0.16, 0: 0.07,
                   2: 0.07, 4: 0.07, 6: 0.10, 8: 0.07, 9: 0.07, 10: 0.22}
        arcs = VGroup(*[attn_arc(row[it_i], row[j], w) for j, w in weights.items()])
        tag = Text("attention", font=FONT, font_size=24, color=BLUE,
                   slant=ITALIC)
        tag.next_to(row, UP, buff=1.55)

        self.play(LaggedStart(*[Create(a) for a in arcs], lag_ratio=0.06),
                  FadeIn(tag), run_time=1.8)
        self.play(row[animal_i][0].animate.set_stroke(color=BLUE, width=3.2),
                  Flash(row[animal_i], color=BLUE, flash_radius=0.75),
                  run_time=0.8)
        self.say("“it” reaches out to every word and weighs each one.  “animal” wins.")
        self.say("This lookup is called attention.  Stronger line = more attention.")

        # --- beat 2: change one word, attention re-aims -------------------
        wide = make_token("wide", font_size=25)
        wide.move_to(row[tired_i].get_center())
        wide[1].set_color(TEAL)
        self.say("Now watch.  Change just the last word:", t=2.4)

        new_weights = dict(weights)
        new_weights[animal_i], new_weights[street_i] = 0.25, 0.92
        new_arcs = VGroup(*[attn_arc(row[it_i], row[j] if j != tired_i else wide, w)
                            for j, w in new_weights.items()])
        self.play(Transform(row[tired_i], wide), run_time=0.7)
        self.play(Transform(arcs, new_arcs),
                  row[animal_i][0].animate.set_stroke(color=FAINT, width=1.6),
                  row[street_i][0].animate.set_stroke(color=BLUE, width=3.2),
                  Flash(row[street_i], color=BLUE, flash_radius=0.75),
                  run_time=1.3)
        self.say("“The street was too wide” — so “it” now attends to “street”.")
        self.say("Nobody programmed that rule.  The weights are learned, and they follow meaning.")

        # --- beat 3: how it decides (Q / K / V, gently) --------------------
        self.play(FadeOut(arcs), FadeOut(tag),
                  row[street_i][0].animate.set_stroke(color=FAINT, width=1.6),
                  run_time=0.6)

        q = Text("asks:  “who am I about?”", font=FONT, font_size=24,
                 color=YELLOW)
        q.next_to(row[it_i], UP, buff=0.9).shift(RIGHT * 0.4)
        qline = Line(row[it_i].get_top(), q.get_bottom() + DOWN * 0.05,
                     color=YELLOW, stroke_width=2)
        self.play(FadeIn(q), Create(qline), run_time=0.8)
        self.say("How does it decide?  Each word broadcasts a tiny question…")

        offers = VGroup()
        for j, s in [(animal_i, "“a creature”"), (street_i, "“a place”"),
                     (3, "“an action”")]:
            o = Text(s, font=FONT, font_size=20, color=MUT)
            o.next_to(row[j], DOWN, buff=0.35)
            offers.add(o)
        self.play(LaggedStart(*[FadeIn(o, shift=DOWN * 0.1) for o in offers],
                              lag_ratio=0.2), run_time=1.0)
        self.say("…and every word advertises an answer.  Matching pairs score high.")

        # arc endpoints are ordered left->right, so the path runs animal -> it
        pulse_arc = attn_arc(row[it_i], row[animal_i], 0.95, color=GREEN)
        dotp = Dot(color=GREEN, radius=0.09).move_to(row[animal_i].get_top())
        self.play(Create(pulse_arc), run_time=0.5)
        self.add(dotp)
        self.play(MoveAlongPath(dotp, pulse_arc), run_time=1.0)
        self.play(dotp.animate.scale(0.2).set_opacity(0),
                  row[it_i][1].animate.set_color(GREEN), run_time=0.5)
        self.say("High scores get blended in.  “it” literally absorbs some of “animal”’s meaning.")
        self.say("Remember “bank” sliding on the map?  This is the machinery that moves it.")

        # --- beat 4: everyone, everywhere, all at once ---------------------
        self.play(FadeOut(q), FadeOut(qline), FadeOut(offers),
                  FadeOut(pulse_arc), row[it_i][1].animate.set_color(INK),
                  row[it_i][0].animate.set_stroke(color=FAINT, width=1.6).set_fill(CARD),
                  run_time=0.6)

        mesh = VGroup()
        n = len(row)
        hues = color_gradient([BLUE, TEAL, PURPLE], n)
        for i in range(n):
            for j in range(i + 1, n):
                a = attn_arc(row[i], row[j], 0.14, color=hues[i],
                             below=(i + j) % 2 == 0)
                mesh.add(a)
        self.play(LaggedStart(*[Create(a) for a in mesh], lag_ratio=0.01),
                  run_time=2.2)
        self.say("And here is the trick that changed everything: every word does this at the same time.")
        self.say("Not a chain of hand-offs — one single, simultaneous step.")

        # pre-empt the smart viewer's objection: what about word order?
        pos_tags = VGroup(*[
            Text(str(k + 1), font=FONT, font_size=19, color=MUT)
            .next_to(row[k], DOWN, buff=0.18)
            for k in range(n)
        ])
        self.play(LaggedStart(*[FadeIn(p, shift=UP * 0.08) for p in pos_tags],
                              lag_ratio=0.06), run_time=1.0)
        self.say("(And order isn't lost — every word carries a little tag saying where it sits.)")

        # callbacks: both walls fall
        self.play(FadeOut(mesh), FadeOut(pos_tags), run_time=0.6)
        c1 = card(["①  distant words fade"], color=RED, w=5.2)
        c2 = card(["②  reading can't be parallel"], color=RED, w=5.2)
        cards = VGroup(c1, c2).arrange(RIGHT, buff=0.6).move_to(DOWN * 1.4)
        self.play(FadeOut(row), FadeIn(cards), run_time=0.8)

        fix1 = Text("any word is one hop away", font=FONT, font_size=24,
                    color=GREEN)
        fix1.move_to(c1[1].get_center())
        fix2 = Text("all words processed at once", font=FONT, font_size=24,
                    color=GREEN)
        fix2.move_to(c2[1].get_center())

        grid = gpu_grid(rows=4, cols=8, s=0.28, buff=0.08)
        grid.move_to(UP * 0.9)
        self.play(FadeIn(grid), run_time=0.6)
        self.play(*[c.animate.set_fill(GREEN, opacity=0.85) for c in grid],
                  Transform(c1[1], fix1), c1[0].animate.set_stroke(color=GREEN),
                  Transform(c2[1], fix2), c2[0].animate.set_stroke(color=GREEN),
                  run_time=1.4)
        self.say("Distance?  Any word reaches any other in one hop — nothing fades.")
        self.say("Waiting?  Gone.  The whole chip lights up, and training drops from weeks to days.")

        self.clear_stage()

        # --- beat 5: heads + layers ---------------------------------------
        mini_words = ["it", "was", "too", "wide"]
        # each head gets a genuinely different pattern of arcs
        head_specs = [
            ("one head tracks grammar", BLUE,
             [(0, 1, 0.8, False), (2, 3, 0.6, False), (1, 3, 0.3, True)]),
            ("another, who did what", PURPLE,
             [(0, 3, 0.85, False), (0, 2, 0.3, True)]),
            ("another, tone", TEAL,
             [(2, 3, 0.8, False), (1, 2, 0.45, True), (0, 3, 0.25, True)]),
        ]
        panels = VGroup()
        for label, col, spec in head_specs:
            r = token_row(mini_words, font_size=22, gap=0.09)
            arcs = VGroup(*[attn_arc(r[i], r[j], w, color=col, below=b)
                            for i, j, w, b in spec])
            t = Text(label, font=FONT, font_size=20, color=col)
            t.next_to(r, DOWN, buff=0.62)
            panels.add(VGroup(r, arcs, t))
        panels.arrange(RIGHT, buff=0.75).move_to(UP * 0.7)

        self.play(LaggedStart(*[FadeIn(p, shift=UP * 0.2) for p in panels],
                              lag_ratio=0.25), run_time=1.6)
        self.say("The paper runs several attentions side by side — “heads”, each noticing different things.")

        # give the layer stack a clean stage of its own
        self.play(FadeOut(panels), run_time=0.5)
        stack = VGroup(*[
            RoundedRectangle(corner_radius=0.1, width=4.2, height=0.44,
                             fill_color=CARD, fill_opacity=1.0,
                             stroke_color=BLUE, stroke_width=1.8)
            for _ in range(5)
        ]).arrange(UP, buff=0.12).move_to(UP * 0.55)
        for k, s in enumerate(stack):
            s.set_stroke(opacity=0.45 + 0.14 * k)
        up_arrow = Arrow(stack.get_bottom() + DOWN * 0.55 + LEFT * 2.7,
                         stack.get_top() + UP * 0.25 + LEFT * 2.7,
                         color=MUT, stroke_width=3, buff=0)
        stack_label = Text("rough sense  →  rich understanding",
                           font=FONT, font_size=22, color=MUT)
        stack_label.next_to(stack, DOWN, buff=0.45)
        self.play(LaggedStart(*[FadeIn(s, shift=UP * 0.15) for s in stack],
                              lag_ratio=0.15), GrowArrow(up_arrow),
                  FadeIn(stack_label), run_time=1.4)
        self.say("Then stack the whole thing in layers — like re-reading a sentence again and again.")

        self.clear_stage()

        name = Text("the Transformer", font=FONT, font_size=54, weight=BOLD,
                    gradient=(BLUE, PURPLE))
        name.move_to(UP * 0.6)
        self.play(Write(name), run_time=1.4)
        self.say("They called the architecture the Transformer — built from attention alone.")
        self.say("Hence the title: attention is all you need.", t=3.0)

        self.clear_stage()

    # ---------------- chapter 4 : legacy ----------------

    def ch4_legacy(self):
        self.chapter("EPILOGUE  ·  WHAT IT BECAME")

        line = Line(LEFT * 5.5, RIGHT * 5.5, color=FAINT, stroke_width=3)
        line.move_to(UP * 0.4)
        events = [
            (0.00, "2017", "Transformer", BLUE),
            (0.18, "2018", "BERT → Google Search", TEAL),
            (0.40, "2020", "GPT-3", PURPLE),
            (0.62, "2022", "ChatGPT", YELLOW),
            (0.80, "2023", "Claude · Gemini", GREEN),
            (1.00, "today", "nearly all of AI", INK),
        ]
        marks = VGroup()
        for k, (f, yr, what, col) in enumerate(events):
            x = interpolate(line.get_start(), line.get_end(), f)
            d = Dot(x, radius=0.07, color=col)
            y = Text(yr, font=FONT, font_size=22, color=col, weight=BOLD)
            w = Text(what, font=FONT, font_size=21, color=MUT)
            if k % 2 == 0:
                y.next_to(d, UP, buff=0.22)
                w.next_to(y, UP, buff=0.10)
            else:
                y.next_to(d, DOWN, buff=0.22)
                w.next_to(y, DOWN, buff=0.10)
            marks.add(VGroup(d, y, w))

        self.play(Create(line), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(m, scale=0.7) for m in marks],
                              lag_ratio=0.25), run_time=3.0)
        self.say("Within five years, nearly every AI you've heard of was rebuilt on this paper.")
        self.say("The “T” in ChatGPT stands for Transformer.", t=3.2)

        self.clear_stage()

        words = VGroup(*[
            Text(w, font=FONT, font_size=50, weight=BOLD, color=INK)
            for w in ["Attention", "was", "all", "we", "needed."]
        ]).arrange(RIGHT, buff=0.38).move_to(UP * 0.5)
        arcs = VGroup(*[
            attn_arc(words[0], words[j], w, color=BLUE)
            for j, w in [(1, 0.3), (2, 0.5), (3, 0.35), (4, 0.9)]
        ])
        self.play(LaggedStart(*[FadeIn(w, shift=UP * 0.2) for w in words],
                              lag_ratio=0.15), run_time=1.4)
        self.play(LaggedStart(*[Create(a) for a in arcs], lag_ratio=0.15),
                  run_time=1.2)
        self.say("Nearly a decade on, it still runs every AI you talk to.", t=3.4)

        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.2)
        self.wait(0.5)
