"""TWICE — a layman's video explainer of "A Proof of the Cycle Double Cover
Conjecture" (2026).

Story: the double-cover game -> flat maps solve themselves -> bridges are the
only true obstacle (the conjecture) -> snarks are where it gets hard -> the
8-flow theorem -> the paper's move: dress every road in TWO of 8 colors ->
local recipe + handshake system -> the parity miracle (every road has two
ends) -> the machine runs on the Petersen graph.

All examples are computationally verified (see verify_math.py in the PR):
the Petersen flow, the pair labels, and the extracted loops shown in the
finale are the actual output of the paper's construction.

Render (no LaTeX needed — Pango text only):
    manim render -r 1920,1080 --fps 30 cdc_explainer.py Ch0Title Ch1Game ...
"""

from __future__ import annotations

import numpy as np
from manim import *

# ----------------------------------------------------------------- palette
config.background_color = "#0e1116"

INK = "#e9edf5"          # main text
SUB = "#93a "            # placeholder (unused)
MUT = "#8a93a8"          # muted text
NODE_C = "#dfe4ee"
EDGE_C = "#414b60"
ACC = "#f2c94c"          # accent (gold)
BAD = "#f25757"
OK = "#43c464"

# F2^3 elements as colors: bit0 = red, bit1 = green, bit2 = blue light
GAMMA = {
    (0, 0, 0): "#99a3b8",   # gray  (all off)
    (0, 0, 1): "#4e8df5",   # blue
    (0, 1, 0): "#43c464",   # green
    (0, 1, 1): "#35c8c8",   # cyan
    (1, 0, 0): "#f25757",   # red
    (1, 0, 1): "#d45cf0",   # magenta
    (1, 1, 0): "#f2c94c",   # yellow
    (1, 1, 1): "#f4f6fb",   # white
}
BIT_ON = ["#f25757", "#43c464", "#4e8df5"]
BIT_OFF = "#242b3a"

FONT = "DejaVu Sans"
Text.set_default(font=FONT, color=INK)

# ----------------------------------------------------------------- graphs
def sq(cx, cy, h):
    # BL BR TR TL
    return [np.array([cx - h, cy - h, 0]), np.array([cx + h, cy - h, 0]),
            np.array([cx + h, cy + h, 0]), np.array([cx - h, cy + h, 0])]

def cube_layout(cx=0.0, cy=0.5, out=2.05, inn=1.02):
    """Cube graph drawn as square-in-square. ids: outer 0BL 1BR 3TR 2TL,
    inner 4BL 5BR 7TR 6TL (bit convention from the verifier)."""
    ob, ib = sq(cx, cy, out), sq(cx, cy, inn)
    pos = {0: ob[0], 1: ob[1], 3: ob[2], 2: ob[3],
           4: ib[0], 5: ib[1], 7: ib[2], 6: ib[3]}
    horiz = [(0, 1), (2, 3), (4, 5), (6, 7)]
    vert = [(0, 2), (1, 3), (4, 6), (5, 7)]
    spokes = [(0, 4), (1, 5), (2, 6), (3, 7)]
    edges = horiz + vert + spokes
    faces = {"outer": [0, 1, 3, 2], "inner": [4, 5, 7, 6],
             "bottom": [0, 1, 5, 4], "right": [1, 3, 7, 5],
             "top": [3, 2, 6, 7], "left": [2, 0, 4, 6]}
    return pos, edges, (horiz, vert, spokes), faces

def pet_layout(cx=0.0, cy=0.42, R=2.42, r=1.30):
    pos = {}
    for i in range(5):
        a = np.deg2rad(90 + 72 * i)
        pos[i] = np.array([cx + R * np.cos(a), cy + R * np.sin(a), 0])
        pos[5 + i] = np.array([cx + r * np.cos(a), cy + r * np.sin(a), 0])
    edges = [(i, (i + 1) % 5) for i in range(5)] \
          + [(i, i + 5) for i in range(5)] \
          + [(5 + i, 5 + (i + 2) % 5) for i in range(5)]
    return pos, edges

# real data computed by verify_math.py (paper's construction on Petersen)
PET_FLOW = {
    (0, 1): (1, 0, 1), (1, 2): (1, 0, 0), (2, 3): (1, 0, 1), (3, 4): (0, 0, 1),
    (4, 0): (1, 0, 0), (0, 5): (0, 0, 1), (1, 6): (0, 0, 1), (2, 7): (0, 0, 1),
    (3, 8): (1, 0, 0), (4, 9): (1, 0, 1), (5, 7): (1, 1, 1), (6, 8): (0, 1, 0),
    (7, 9): (1, 1, 0), (8, 5): (1, 1, 0), (9, 6): (0, 1, 1),
}
PET_PAIRS = {
    (0, 1): [(0, 0, 1), (1, 0, 0)], (1, 2): [(0, 0, 0), (1, 0, 0)],
    (2, 3): [(0, 0, 0), (1, 0, 1)], (3, 4): [(0, 0, 0), (0, 0, 1)],
    (4, 0): [(0, 0, 1), (1, 0, 1)], (0, 5): [(1, 0, 0), (1, 0, 1)],
    (1, 6): [(0, 0, 0), (0, 0, 1)], (2, 7): [(1, 0, 0), (1, 0, 1)],
    (3, 8): [(0, 0, 1), (1, 0, 1)], (4, 9): [(0, 0, 0), (1, 0, 1)],
    (5, 7): [(0, 1, 1), (1, 0, 0)], (6, 8): [(0, 0, 1), (0, 1, 1)],
    (7, 9): [(0, 1, 1), (1, 0, 1)], (8, 5): [(0, 1, 1), (1, 0, 1)],
    (9, 6): [(0, 0, 0), (0, 1, 1)],
}
PET_MS = {   # color class -> loops (paper construction output)
    (0, 0, 0): [[3, 4, 9, 6, 1, 2]],
    (0, 0, 1): [[3, 4, 0, 1, 6, 8]],
    (0, 1, 1): [[9, 6, 8, 5, 7]],
    (1, 0, 0): [[1, 2, 7, 5, 0]],
    (1, 0, 1): [[2, 3, 8, 5, 0, 4, 9, 7]],
}
HEMI = [[0, 1, 2, 3, 4], [0, 1, 6, 8, 5], [1, 2, 7, 9, 6],
        [2, 3, 8, 5, 7], [3, 4, 9, 6, 8], [4, 0, 5, 7, 9]]

def xor(p, q):
    return tuple(a ^ b for a, b in zip(p, q))

# ----------------------------------------------------------------- widgets
def node_dot(p, r=0.085):
    d = Dot(p, radius=r, color=NODE_C, z_index=6)
    halo = Dot(p, radius=r * 2.1, color=NODE_C, fill_opacity=0.16, z_index=5)
    return VGroup(halo, d)

def base_edge(p, q, color=EDGE_C, w=4.5, op=1.0):
    return Line(p, q, stroke_width=w, color=color, stroke_opacity=op, z_index=1)

def make_graph(pos, edges, edge_color=EDGE_C, w=4.5):
    lines = {e: base_edge(pos[e[0]], pos[e[1]], color=edge_color, w=w) for e in edges}
    dots = {v: node_dot(p) for v, p in pos.items()}
    return VGroup(*lines.values()), VGroup(*dots.values()), lines, dots

def lane_pts(p, q, side, off=0.085, trim=0.17):
    p, q = np.array(p, float), np.array(q, float)
    d = q - p
    L = np.linalg.norm(d)
    u = d / L
    n = np.array([-u[1], u[0], 0.0])
    a = p + u * trim + n * off * side
    b = q - u * trim + n * off * side
    return a, b

def edge_key(u, v):
    return (u, v) if (u, v) in _EDGE_UNIVERSE else (v, u)

_EDGE_UNIVERSE = set()

def set_universe(edges):
    global _EDGE_UNIVERSE
    _EDGE_UNIVERSE = set(edges)

class LaneRegistry:
    """Hands out lane sides so each edge ends with exactly two lanes."""
    def __init__(self):
        self.used = {}
    def side(self, u, v):
        k = edge_key(u, v)
        n = self.used.get(k, 0)
        self.used[k] = n + 1
        return +1 if n == 0 else -1

def loop_mobj(pos, cycle, sides, color, w=5.5, close=True):
    """cycle: [v0..vk-1]; sides: list of +-1 per edge (vi -> vi+1)."""
    pts = []
    n = len(cycle)
    for i in range(n):
        u, v = cycle[i], cycle[(i + 1) % n]
        k = edge_key(u, v)
        s = sides[i] if k == (u, v) else -sides[i]
        a, b = lane_pts(pos[k[0]], pos[k[1]], s)
        if k != (u, v):
            a, b = b, a
        pts += [a, b]
    m = VMobject(stroke_color=color, stroke_width=w, z_index=3)
    m.set_points_as_corners(pts + ([pts[0]] if close else []))
    m.joint_type = LineJointType.ROUND
    return m

def face_loop(pos, cycle, color, outward=False, w=5.5):
    """Loop offset toward (or away from) the cycle's centroid."""
    c = np.mean([pos[v] for v in cycle], axis=0)
    sides = []
    n = len(cycle)
    for i in range(n):
        u, v = cycle[i], cycle[(i + 1) % n]
        p, q = pos[u], pos[v]
        d = q - p
        nn = np.array([-d[1], d[0], 0.0])
        s = 1 if np.dot(nn, c - (p + q) / 2) > 0 else -1
        if outward:
            s = -s
        sides.append(s)
    return loop_mobj(pos, cycle, sides, color, w=w)

def reg_loop(pos, cycle, color, reg: LaneRegistry, w=5.5):
    sides = []
    n = len(cycle)
    for i in range(n):
        u, v = cycle[i], cycle[(i + 1) % n]
        k = edge_key(u, v)
        s = reg.side(u, v)
        sides.append(s if k == (u, v) else -s)
    return loop_mobj(pos, cycle, sides, color, w=w)

def pair_loop(pos, cycle, s, w=6.0):
    """Loop for color class s that rides exactly on the lane carrying s
    (lane +1 holds PET_PAIRS[e][0], lane -1 holds PET_PAIRS[e][1])."""
    sides = []
    n = len(cycle)
    for i in range(n):
        u, v = cycle[i], cycle[(i + 1) % n]
        k = edge_key(u, v)
        side_key = +1 if tuple(PET_PAIRS[k][0]) == s else -1
        sides.append(side_key if k == (u, v) else -side_key)
    return loop_mobj(pos, cycle, sides, GAMMA[s], w=w)

def chip(code, h=0.46, show_bits=True):
    """3-bit code as a rounded chip with 3 'switch' squares, rimmed in its color."""
    col = GAMMA[code]
    box = RoundedRectangle(corner_radius=0.09, width=h * 2.15, height=h,
                           stroke_color=col, stroke_width=3,
                           fill_color="#161b26", fill_opacity=1.0)
    cells = VGroup()
    for i, b in enumerate(code):
        c = Square(side_length=h * 0.44)
        c.set_stroke(width=1.2, color="#39415a")
        c.set_fill(BIT_ON[i] if b else BIT_OFF, opacity=1.0)
        cells.add(c)
    cells.arrange(RIGHT, buff=h * 0.14).move_to(box)
    g = VGroup(box, cells)
    g.code = code
    return g

def swatch(code, r=0.11):
    return Dot(radius=r, color=GAMMA[code], z_index=6)

# ----------------------------------------------------------------- scene base
CAP_Y = -3.35

class CDC(Scene):
    chapter = ""
    def setup(self):
        self._cap = None
        self._chip_label = None
        if self.chapter:
            lab = Text(self.chapter, font_size=23, color=MUT, weight=BOLD)
            lab.to_corner(UL, buff=0.38)
            self.add(lab)
            self._chap = lab

    def say(self, text, extra=0.0, size=29, keep=False, color=INK, t2c=None):
        lines = text.split("\n")
        grp = VGroup(*[Text(l, font_size=size, color=color, t2c=t2c or {})
                       for l in lines])
        grp.arrange(DOWN, buff=0.14)
        if grp.width > 12.6:
            grp.scale_to_fit_width(12.6)
        grp.move_to([0, CAP_Y - (0 if len(lines) == 1 else 0.12), 0])
        grp.set_z_index(20)
        if self._cap is not None:
            self.play(LaggedStart(FadeOut(self._cap, run_time=0.3),
                                  FadeIn(grp, shift=UP * 0.18, run_time=0.4),
                                  lag_ratio=0.55), run_time=0.6)
        else:
            self.play(FadeIn(grp, shift=UP * 0.18), run_time=0.45)
        self._cap = grp
        self.wait(max(2.1, 0.052 * len(text.replace("\n", ""))) + extra)
        return grp

    def clear_cap(self):
        if self._cap is not None:
            self.play(FadeOut(self._cap), run_time=0.35)
            self._cap = None

    def veil(self, opacity=0.94):
        """Clear the caption, then raise a near-opaque veil for card moments."""
        self.clear_cap()
        v = Rectangle(width=15, height=9, fill_color="#0e1116",
                      fill_opacity=opacity, stroke_opacity=0).set_z_index(9)
        return v

    def sweep(self, keep=()):
        keepset = set(keep) | ({self._chap} if hasattr(self, "_chap") else set())
        outs = [m for m in self.mobjects if m not in keepset]
        if outs:
            self.play(*[FadeOut(m) for m in outs], run_time=0.6)
        self._cap = None

# ======================================================================
class Ch0Title(CDC):
    chapter = ""
    def construct(self):
        pos, edges = pet_layout(cy=0.2, R=2.6, r=1.4)
        set_universe(edges)
        eg, ng, lines, dots = make_graph(pos, edges, w=3.5)
        g = VGroup(eg, ng).set_opacity(0.0)
        self.add(g)
        self.play(eg.animate.set_opacity(0.55), ng.animate.set_opacity(0.8),
                  run_time=1.4)
        reg = LaneRegistry()
        tease = ["#8c4b4b", "#8c7a3f", "#4b7a4f", "#3f7a7a", "#4b5f8c", "#7a4b8c"]
        loops = [reg_loop(pos, c, col, reg, w=4)
                 for c, col in zip(HEMI, tease)]
        self.play(LaggedStart(*[Create(l) for l in loops], lag_ratio=0.18),
                  run_time=3.2)
        veil = Rectangle(width=15, height=9, fill_color="#0e1116",
                         fill_opacity=0.82, stroke_opacity=0).set_z_index(9)
        title = Text("TWICE", font_size=96, weight=BOLD, color=INK).set_z_index(10)
        title.move_to(UP * 0.75)
        sub = Text("a fifty-year puzzle about tracing every line twice",
                   font_size=32, color="#b9c2d4").set_z_index(10)
        sub.next_to(title, DOWN, buff=0.5)
        src = Text('an illustrated tour of "A Proof of the Cycle Double Cover Conjecture" (2026)',
                   font_size=22, color=MUT).set_z_index(10)
        src.next_to(sub, DOWN, buff=0.85)
        self.play(FadeIn(veil), FadeIn(title, scale=1.06), run_time=1.1)
        self.play(FadeIn(sub, shift=UP * 0.2), run_time=0.7)
        self.play(FadeIn(src), run_time=0.6)
        self.wait(2.6)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)

# ======================================================================
class Ch1Game(CDC):
    chapter = "1 · THE GAME"
    def construct(self):
        pos, edges, (horiz, vert, spokes), faces = cube_layout()
        set_universe(edges)
        eg, ng, lines, dots = make_graph(pos, edges)
        self.play(LaggedStart(Create(eg), FadeIn(ng), lag_ratio=0.4), run_time=1.6)
        self.say("This is a network: junctions, joined by roads.")
        self.say("The game — draw closed loops. A loop never repeats a road.")

        # demo one loop
        demo = face_loop(pos, faces["bottom"], ACC)
        self.play(Create(demo), run_time=1.6)
        self.say("Like this. And the goal:")
        goal = Text("every road must end up traced exactly TWICE",
                    font_size=34, weight=BOLD, color=INK,
                    t2c={"TWICE": ACC}).move_to([0, CAP_Y, 0]).set_z_index(20)
        self.play(FadeOut(self._cap), FadeIn(goal, scale=1.04), run_time=0.5)
        self._cap = goal
        self.wait(2.4)

        # counter
        cnt = VGroup(Text("roads with 2 passes", font_size=20, color=MUT),
                     Text("0 / 12", font_size=30, weight=BOLD, color=ACC))
        cnt.arrange(DOWN, buff=0.12).to_corner(UR, buff=0.42)
        self.play(FadeIn(cnt), run_time=0.5)

        order = ["bottom", "right", "top", "left", "inner", "outer"]
        colors = ["#f2c94c", "#f25757", "#43c464", "#35c8c8", "#4e8df5", "#d45cf0"]
        done_after = [0, 1, 2, 4, 8, 12]
        loops = [demo]
        self.say("So we keep looping.", extra=-1.0)
        for i, (fname, fc) in enumerate(zip(order, colors)):
            if i == 0:
                self.play(demo.animate.set_stroke(color=fc), run_time=0.4)
            else:
                lp = face_loop(pos, faces[fname], fc, outward=(fname == "outer"))
                loops.append(lp)
                self.play(Create(lp), run_time=1.15)
            new = Text(f"{done_after[i]} / 12", font_size=30, weight=BOLD, color=ACC
                       ).move_to(cnt[1])
            self.play(Transform(cnt[1], new), run_time=0.25)
        self.say("Six loops — and now every road carries exactly two passes.")
        self.say("Two lanes on every road: a DOUBLE COVER.",
                 t2c={"DOUBLE COVER": ACC})

        # why twice? junction parity — animated pass + slot tallies
        self.play(*[l.animate.set_stroke(opacity=0.12) for l in loops],
                  cnt.animate.set_opacity(0.25), run_time=0.6)
        spot = Circle(radius=0.62, color=ACC, stroke_width=3).move_to(pos[1])
        self.play(Create(spot), run_time=0.6)
        self.say("Why twice, not once? Watch a loop visit a junction:",
                 extra=-1.2)
        e_in, e_out = lines[(0, 1)], lines[(1, 3)]
        mid_in = (pos[0] + pos[1]) / 2
        mid_out = (pos[1] + pos[3]) / 2
        w = Dot(radius=0.11, color=ACC, z_index=8).move_to(mid_in)
        self.play(FadeIn(w), e_in.animate.set_stroke(color=ACC, width=7),
                  run_time=0.4)
        self.play(w.animate.move_to(pos[1]), run_time=0.55, rate_func=linear)
        self.play(w.animate.move_to(mid_out),
                  e_out.animate.set_stroke(color=ACC, width=7),
                  run_time=0.55, rate_func=linear)
        self.say("In on one road, out on another —\nevery visit uses roads in PAIRS.", t2c={"PAIRS": ACC})
        self.play(FadeOut(w),
                  e_in.animate.set_stroke(color=EDGE_C, width=4.5),
                  e_out.animate.set_stroke(color=EDGE_C, width=4.5),
                  run_time=0.5)

        def slots(n, filled, fc):
            g = VGroup(*[Square(side_length=0.34)
                         .set_stroke(color="#4a5570", width=2)
                         .set_fill(fc if i < filled else "#1a2030", opacity=1.0)
                         for i in range(n)])
            return g.arrange(RIGHT, buff=0.12)

        panelA = VGroup(
            Text("cover each road once → 3 slots", font_size=22, color=MUT),
            slots(3, 2, ACC)).arrange(DOWN, buff=0.18).move_to([3.9, 2.45, 0])
        self.play(FadeIn(panelA, shift=LEFT * 0.3), run_time=0.7)
        lonely = panelA[1][2]
        x_ = Text("✕", font_size=26, weight=BOLD, color=BAD
                  ).next_to(lonely, RIGHT, buff=0.16)
        self.play(lonely.animate.set_stroke(color=BAD, width=3),
                  FadeIn(x_, scale=1.4), run_time=0.6)
        self.say("Cover each road ONCE: three slots at this junction. Pairs fill\ntwo at a time — one slot is always stranded. Three is odd. Impossible.",
                 t2c={"ONCE": BAD, "odd": BAD})
        panelB = VGroup(
            Text("cover each road twice → 6 slots", font_size=22, color=MUT),
            slots(6, 6, OK)).arrange(DOWN, buff=0.18)
        panelB.next_to(panelA, DOWN, buff=0.6)
        chk = Text("✓", font_size=26, weight=BOLD, color=OK
                   ).next_to(panelB[1], RIGHT, buff=0.16)
        self.play(FadeIn(panelB, shift=LEFT * 0.3), FadeIn(chk), run_time=0.7)
        self.say("Cover each TWICE: six slots — three visits fit perfectly.\n\"Twice\" isn't a quirk of the game. It's forced by the junctions.",
                 t2c={"TWICE": ACC})
        self.sweep()

# ======================================================================
class Ch2Maps(CDC):
    chapter = "2 · MAPS ALREADY KNOW THE ANSWER"
    def construct(self):
        pos, edges, _, faces = cube_layout()
        set_universe(edges)
        eg, ng, lines, dots = make_graph(pos, edges)
        self.add(eg, ng)
        self.say("Our little network has a superpower: it lies FLAT.\nNo two roads cross.", t2c={"FLAT": ACC})

        # regions
        fills = {}
        face_cols = {"bottom": "#f2c94c", "right": "#f25757", "top": "#43c464",
                     "left": "#35c8c8", "inner": "#4e8df5"}
        for f, c in face_cols.items():
            poly = Polygon(*[pos[v] for v in faces[f]], stroke_opacity=0,
                           fill_color=c, fill_opacity=0.22, z_index=0)
            fills[f] = poly
        big = RoundedRectangle(corner_radius=0.25, width=7.5, height=6.6
                               ).move_to([0, 0.5, 0])
        outer_sq = Polygon(*[pos[v] for v in faces["outer"]])
        outside = Difference(big, outer_sq, stroke_opacity=0,
                             fill_color="#d45cf0", fill_opacity=0.13)
        outside.set_z_index(0)
        self.play(LaggedStart(*[FadeIn(p) for p in fills.values()],
                              lag_ratio=0.15), run_time=1.6)
        self.say("A flat network is a map: it slices the world into regions.\nFive rooms here…")
        self.play(FadeIn(outside), run_time=0.9)
        self.say("…plus one more: the endless OUTSIDE. Six regions in all.",
                 t2c={"OUTSIDE": "#d45cf0"})

        # each road borders exactly two regions
        e1 = lines[(4, 5)]
        others1 = [f for k, f in fills.items() if k not in ("bottom", "inner")]
        self.play(e1.animate.set_stroke(color=ACC, width=8),
                  *[f.animate.set_fill(opacity=0.05) for f in others1],
                  outside.animate.set_fill(opacity=0.04), run_time=0.6)
        self.play(fills["bottom"].animate.set_fill(opacity=0.5), run_time=0.5)
        self.play(fills["bottom"].animate.set_fill(opacity=0.22),
                  fills["inner"].animate.set_fill(opacity=0.5), run_time=0.5)
        self.play(fills["inner"].animate.set_fill(opacity=0.22), run_time=0.4)
        self.say("Now the key fact: every road touches exactly TWO regions,\none on each side.", t2c={"TWO": ACC})
        e2 = lines[(0, 1)]
        self.play(e1.animate.set_stroke(color=EDGE_C, width=4.5),
                  e2.animate.set_stroke(color=ACC, width=8),
                  fills["bottom"].animate.set_fill(opacity=0.5),
                  outside.animate.set_fill(opacity=0.32), run_time=0.7)
        self.say("Even the rim roads: one side is a room, the other is the outside.")
        self.play(e2.animate.set_stroke(color=EDGE_C, width=4.5),
                  fills["bottom"].animate.set_fill(opacity=0.22),
                  outside.animate.set_fill(opacity=0.13),
                  *[f.animate.set_fill(opacity=0.22) for f in others1],
                  run_time=0.6)

        # walk all region borders
        loops = []
        for f, c in list(face_cols.items()) + [("outer", "#d45cf0")]:
            loops.append(face_loop(pos, faces[f], c, outward=(f == "outer")))
        self.say("So walk the border of every region — all six…", extra=-1.2)
        self.play(LaggedStart(*[Create(l) for l in loops], lag_ratio=0.2),
                  run_time=3.0)
        self.say("Every road just got walked twice: once from each side.\nFor flat networks, the puzzle solves itself.")
        self.say("(Graph theorists noticed this early — Jaeger's survey calls it\nthe planar case. No mystery there.)", size=26)

        # but not all networks are flat
        pet_pos, pet_edges = pet_layout()
        peg, png_, plines, pdots = make_graph(pet_pos, pet_edges, w=4.0)
        # pentagram crossing marks
        def seg_int(p1, p2, p3, p4):
            a1, a2 = p2 - p1, p4 - p3
            den = a1[0] * a2[1] - a1[1] * a2[0]
            t = ((p3 - p1)[0] * a2[1] - (p3 - p1)[1] * a2[0]) / den
            return p1 + t * a1
        inner = [(5, 7), (7, 9), (9, 6), (6, 8), (8, 5)]
        crosses = []
        for i in range(5):
            for j in range(i + 1, 5):
                a, b = inner[i], inner[j]
                if len({*a, *b}) == 4:
                    p = seg_int(pet_pos[a[0]], pet_pos[a[1]],
                                pet_pos[b[0]], pet_pos[b[1]])
                    if np.linalg.norm(p[:2] - np.array([0, 0.42])) < 1.4:
                        crosses.append(p)
        self.play(*[FadeOut(m) for m in [*fills.values(), outside, *loops, eg, ng]],
                  run_time=0.9)
        self.play(Create(peg), FadeIn(png_), run_time=1.5)
        marks = VGroup(*[Text("✕", font_size=34, weight=BOLD, color="#ff6b6b"
                              ).move_to(p) for p in crosses[:5]])
        self.play(LaggedStart(
            *[AnimationGroup(FadeIn(m, scale=1.7),
                             Flash(m, color=BAD, flash_radius=0.4))
              for m in marks], lag_ratio=0.15), run_time=1.6)
        self.say("But most networks are NOT flat — draw this one and roads cross.\nNo flat drawing of it exists.", t2c={"NOT": BAD})
        self.say("No flat drawing → no regions → the map trick dies.\nDoes a double cover still exist? THAT is the question.",
                 t2c={"THAT": ACC})
        self.sweep()

# ======================================================================
class Ch3Bridges(CDC):
    chapter = "3 · THE ONE TRUE OBSTACLE"
    def construct(self):
        # dumbbell: two triangles + bridge
        L = {(0): np.array([-4.6, 1.15, 0]), 1: np.array([-4.6, -1.15, 0]),
             2: np.array([-2.7, 0.0, 0])}
        Rr = {3: np.array([2.7, 0.0, 0]), 4: np.array([4.6, 1.15, 0]),
              5: np.array([4.6, -1.15, 0])}
        pos = {**L, **Rr}
        for k in pos:
            pos[k] = pos[k] + np.array([0, 0.7, 0])
        edges = [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3), (2, 3)]
        set_universe(edges)
        eg, ng, lines, dots = make_graph(pos, edges)
        self.play(Create(eg), FadeIn(ng), run_time=1.4)
        br = lines[(2, 3)]
        self.play(br.animate.set_stroke(color=ACC, width=8), run_time=0.6)
        lab = Text("a bridge", font_size=26, color=ACC).next_to(
            (pos[2] + pos[3]) / 2, UP, buff=0.25)
        self.play(FadeIn(lab, shift=UP * 0.2))
        self.say("One thing CAN kill the game: a bridge —\nthe only road between two lands.", t2c={"bridge": ACC})

        # attempt a loop across
        walker = Dot(radius=0.11, color="#f4f6fb", z_index=8).move_to(pos[2])
        trail_pts = [pos[2], pos[3], pos[4], pos[5], pos[3]]
        trail = VMobject(stroke_color="#f4f6fb", stroke_width=5, z_index=2)
        trail.set_points_as_corners([pos[2], pos[2]])
        self.add(walker, trail)
        self.say("Try to run a loop across it…", extra=-1.3)
        for pnt in trail_pts[1:]:
            self.play(walker.animate.move_to(pnt), run_time=0.55,
                      rate_func=linear)
            trail.add_points_as_corners([pnt])
        self.say("…the loop must come home. The ONLY way back\nis the bridge itself.", t2c={"ONLY": BAD})
        # crossing back = reuse
        self.play(walker.animate.move_to(pos[2]), run_time=0.7)
        cross = Text("✕", font_size=44, weight=BOLD, color=BAD).move_to(
            (pos[2] + pos[3]) / 2 + UP * 0.02)
        self.play(FadeIn(cross, scale=1.5),
                  br.animate.set_stroke(color=BAD), run_time=0.6)
        self.say("But loops never repeat a road. So NO loop crosses a bridge —\na bridge can't be covered even once. Game over.", t2c={"NO": BAD})
        self.play(FadeOut(walker), FadeOut(trail), FadeOut(cross), run_time=0.5)

        # the conjecture card
        self.say("The conjecture says: bridges are the ONLY obstacle.",
                 t2c={"ONLY": ACC})
        veil = self.veil()
        card1 = Text("THE CYCLE DOUBLE COVER CONJECTURE", font_size=30,
                     weight=BOLD, color=ACC).set_z_index(10).move_to(UP * 1.5)
        card2 = Text("Every network without a bridge\ncan have all its roads covered by loops,\neach road exactly twice.",
                     font_size=36, color=INK, line_spacing=1.1).set_z_index(10)
        card3 = Text("posed in the 1970s · Szekeres — Itai & Rodeh — Seymour — Tutte",
                     font_size=22, color=MUT).set_z_index(10).move_to(DOWN * 1.7)
        self.play(FadeIn(veil), FadeIn(card1, shift=DOWN * 0.2), run_time=0.9)
        self.play(FadeIn(card2), run_time=0.8)
        self.play(FadeIn(card3), run_time=0.6)
        self.wait(4.2)
        hold = Text("Simple to state. Open for half a century.",
                    font_size=28, color="#b9c2d4").set_z_index(10).move_to(DOWN * 2.6)
        self.play(FadeIn(hold))
        self.wait(2.4)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.7)

# ======================================================================
class Ch4Snarks(CDC):
    chapter = "4 · WHERE IT GETS HARD"
    def construct(self):
        # reduction to cubic
        star_c = np.array([-3.4, 1.3, 0])
        leaves = [star_c + 1.35 * np.array([np.cos(a), np.sin(a), 0])
                  for a in np.linspace(0.35, 2 * np.pi + 0.35, 6)[:-1]]
        star = VGroup(*[Line(star_c, l, stroke_width=4.5, color=EDGE_C)
                        for l in leaves],
                      *[node_dot(l) for l in leaves], node_dot(star_c))
        chain = VGroup()
        c1, c2, c3 = [np.array([2.0 + dx, 1.3, 0]) for dx in (-0.9, 0, 0.9)]
        ends = [c1 + np.array([-0.9, 0.8, 0]), c1 + np.array([-0.9, -0.8, 0]),
                c2 + np.array([0, 1.15, 0]),
                c3 + np.array([0.9, 0.8, 0]), c3 + np.array([0.9, -0.8, 0])]
        chain.add(Line(c1, c2, stroke_width=4.5, color=EDGE_C),
                  Line(c2, c3, stroke_width=4.5, color=EDGE_C),
                  Line(c1, ends[0], stroke_width=4.5, color=EDGE_C),
                  Line(c1, ends[1], stroke_width=4.5, color=EDGE_C),
                  Line(c2, ends[2], stroke_width=4.5, color=EDGE_C),
                  Line(c3, ends[3], stroke_width=4.5, color=EDGE_C),
                  Line(c3, ends[4], stroke_width=4.5, color=EDGE_C),
                  *[node_dot(e) for e in ends],
                  node_dot(c1), node_dot(c2), node_dot(c3))
        arrow = Arrow(star_c + RIGHT * 1.8, c1 + LEFT * 1.3, color=MUT,
                      stroke_width=4)
        self.play(FadeIn(star), run_time=0.9)
        self.say("First, a standard simplification. Busy junctions —\nfive roads here — can be split into calm three-way ones.")
        self.play(GrowArrow(arrow), FadeIn(chain), run_time=1.1)
        self.say("Solve the three-way world, and the general puzzle follows.\nSo from now on: every junction meets exactly 3 roads.")
        self.play(FadeOut(star), FadeOut(chain), FadeOut(arrow), run_time=0.6)

        # classic trick: 3-edge-coloring on cube
        pos, edges, (horiz, vert, spokes), faces = cube_layout(cx=0, cy=0.5)
        set_universe(edges)
        eg, ng, lines, dots = make_graph(pos, edges)
        self.play(Create(eg), FadeIn(ng), run_time=1.2)
        self.say("Three roads per junction invites a famous trick:\npaint the roads with 3 colors, all different at every junction.")
        RED, GREEN, BLUE = "#f25757", "#43c464", "#4e8df5"
        self.play(*[lines[e].animate.set_stroke(color=RED, width=6) for e in vert],
                  run_time=0.7)
        self.play(*[lines[e].animate.set_stroke(color=BLUE, width=6) for e in horiz],
                  run_time=0.7)
        self.play(*[lines[e].animate.set_stroke(color=GREEN, width=6) for e in spokes],
                  run_time=0.7)
        self.say("Done: every junction sees one red, one blue, one green.")
        # drop green -> loops
        self.play(*[lines[e].animate.set_stroke(opacity=0.10) for e in spokes],
                  run_time=0.8)
        self.say("Now HIDE green. What's left meets every junction exactly twice —\nso it splits into loops, automatically!", t2c={"HIDE": GREEN})
        l1 = face_loop(pos, faces["outer"], "#d9a5ff", outward=True)
        l2 = face_loop(pos, faces["inner"], "#d9a5ff")
        self.play(Create(l1), Create(l2), run_time=1.3)
        self.say("red + blue → two loops. Same for red + green, and blue + green.")
        self.play(FadeOut(l1), FadeOut(l2),
                  *[lines[e].animate.set_stroke(opacity=1.0) for e in spokes],
                  run_time=0.7)
        self.say("Each road wears 2 of the 3 color-pairs → traced exactly twice.\nPaintable ⇒ double-covered. (Szekeres, 1973.)")

        # Petersen refuses
        self.play(FadeOut(eg), FadeOut(ng), run_time=0.6)
        ppos, pedges = pet_layout()
        set_universe(pedges)
        peg, png_, plines, pdots = make_graph(ppos, pedges)
        self.play(Create(peg), FadeIn(png_), run_time=1.4)
        self.say("Meet the PETERSEN network: 10 junctions, 15 roads,\nand a legendary bad attitude.", t2c={"PETERSEN": ACC})
        spk = [(i, i + 5) for i in range(5)]
        self.say("Try to paint it. Green must grab exactly one road at EVERY junction.\nSay, these five:", extra=-0.8)
        self.play(*[plines[e].animate.set_stroke(color=GREEN, width=6.5)
                    for e in spk], run_time=0.9)
        self.say("The rest must alternate red / blue around each leftover loop.")
        outer_cycle = [(0, 1), (1, 2), (2, 3), (3, 4)]
        cols = [RED, BLUE, RED, BLUE]
        for e, c in zip(outer_cycle, cols):
            self.play(plines[e].animate.set_stroke(color=c, width=6.5),
                      run_time=0.45)
        last = plines[(4, 0)]
        q = Text("?", font_size=40, weight=BOLD, color=ACC).next_to(
            (ppos[4] + ppos[0]) / 2, LEFT, buff=0.18)
        self.play(FadeIn(q, scale=1.4), last.animate.set_stroke(color=ACC, width=6.5))
        self.say("But this loop has FIVE roads. Red, blue, red, blue…\nthe fifth touches BOTH a red and a blue. Odd loops break the pattern.",
                 t2c={"FIVE": BAD, "Odd": BAD})
        x1 = Text("✕", font_size=40, weight=BOLD, color=BAD).move_to(q)
        self.play(Transform(q, x1), Flash(last.get_center(), color=BAD,
                                          flash_radius=0.5),
                  run_time=0.6)
        self.wait(1.2)
        self.say("And in Petersen, EVERY possible green-choice leaves odd loops —\nthere are only six ways, and each strands two 5-road loops. Checked.",
                 t2c={"EVERY": BAD})
        self.say("No 3-painting of this network exists. Ever.")
        self.say("Unpaintable networks earned a name: SNARKS —\nafter Lewis Carroll's uncatchable beast.", t2c={"SNARKS": ACC})
        self.say("Why it matters: a smallest counterexample to the conjecture\nwould have to be a snark. Snarks are where the puzzle hid for 50 years.")
        self.sweep()

# ======================================================================
class Ch5Flow(CDC):
    chapter = "5 · EIGHT COLORS THAT CANCEL"
    def construct(self):
        self.say("The new proof opens with a 1970s gem.\nFirst, meet the cast: 3-bit codes. Three switches — on or off.")
        codes = [(0,0,0),(0,0,1),(0,1,0),(0,1,1),(1,0,0),(1,0,1),(1,1,0),(1,1,1)]
        chips = VGroup(*[chip(c) for c in codes]).arrange(RIGHT, buff=0.32)
        chips.move_to(UP * 2.9)
        self.play(LaggedStart(*[FadeIn(c, shift=DOWN * 0.25) for c in chips],
                              lag_ratio=0.08), run_time=1.6)
        self.say("Eight codes. Read each as a COLOR: switch 1 adds red,\nswitch 2 green, switch 3 blue. All off = gray.")
        # toggle demo
        a, b = chip((1, 0, 1), h=0.6), chip((1, 0, 0), h=0.6)
        plus = Text("⊕", font_size=44, color=INK)
        eq = Text("=", font_size=44, color=INK)
        c_ = chip((0, 0, 1), h=0.6)
        row = VGroup(a, plus, b, eq, c_).arrange(RIGHT, buff=0.4).move_to(UP * 0.9)
        note = Text("⊕  =  toggle the switches", font_size=26, color=MUT
                    ).next_to(row, DOWN, buff=0.5)
        self.play(FadeIn(a), FadeIn(plus), FadeIn(b), FadeIn(note), run_time=0.8)
        self.play(FadeIn(eq), TransformFromCopy(VGroup(a, b), c_), run_time=1.0)
        self.say("Codes combine by TOGGLING: press a switch twice, it's off again.\nmagenta ⊕ red = blue.  And anything ⊕ itself = gray.")
        self.play(FadeOut(row), FadeOut(note), run_time=0.5)

        # 8-flow on Petersen
        ppos, pedges = pet_layout(cy=-0.42, R=1.95, r=1.07)
        set_universe(pedges)
        peg, png_, plines, pdots = make_graph(ppos, pedges)
        self.play(Create(peg), FadeIn(png_), run_time=1.3)
        self.say("THE 8-FLOW THEOREM (Jaeger; Kilpatrick, 1970s):\nevery bridgeless network can label its roads with LIT codes…", extra=-0.6)
        self.play(*[plines[e].animate.set_stroke(color=GAMMA[PET_FLOW[e]], width=6.5)
                    for e in pedges], run_time=1.4)
        self.say("…so that at EVERY junction, the three codes cancel to gray:\nx ⊕ y ⊕ z = 000.", t2c={"cancel": ACC})

        # spot-check junction 0
        spot = Circle(radius=0.5, color=ACC, stroke_width=3).move_to(ppos[0])
        self.play(Create(spot), run_time=0.6)
        e_at0 = [(0, 1), (4, 0), (0, 5)]
        mini = VGroup(*[chip(PET_FLOW[e], h=0.5) for e in e_at0])
        seq = VGroup(mini[0], Text("⊕", font_size=32), mini[1],
                     Text("⊕", font_size=32), mini[2],
                     Text("=", font_size=32), chip((0, 0, 0), h=0.5),
                     Text("✓", font_size=34, color=OK, weight=BOLD))
        seq.arrange(RIGHT, buff=0.22).move_to(UP * 2.2)
        for m, e in zip(mini, e_at0):
            m.save_state()
            m.move_to((ppos[e[0]] + ppos[e[1]]) / 2).scale(0.3)
        self.play(LaggedStart(*[Restore(m) for m in mini], lag_ratio=0.15),
                  run_time=1.1)
        self.play(FadeIn(seq[1]), FadeIn(seq[3]), FadeIn(seq[5]),
                  FadeIn(seq[6], scale=0.7), FadeIn(seq[7], scale=1.4),
                  run_time=0.9)
        self.say("Check this junction: magenta ⊕ red ⊕ blue = gray. ✓\nIt works at all ten. A conservation law for color-flavors.")
        self.play(FadeOut(seq), FadeOut(spot), run_time=0.5)
        self.say("(Even snarks obey it — coloring EDGES with 3 colors fails,\nbut cancelling CODES always succeeds. Deep 1970s magic.)", size=26)
        self.say("But one code per road gives no loops yet.\nThe 2026 move is next — and it's the heart of the proof.")
        self.sweep()

# ======================================================================
class Ch6TwoColors(CDC):
    chapter = "6 · THE MOVE: WEAR TWO COLORS"
    def construct(self):
        rule1 = Text("Dress every road in TWO of the 8 colors — two lanes.",
                     font_size=32, color=INK, t2c={"TWO": ACC}).move_to(UP * 2.2)
        rule2 = Text("RULE: at every junction, each color appears\neither exactly twice — or not at all.",
                     font_size=36, weight=BOLD, color=ACC, line_spacing=1.05
                     ).move_to(UP * 0.6)
        self.play(FadeIn(rule1, shift=UP * 0.2), run_time=0.8)
        self.wait(1.2)
        self.play(FadeIn(rule2, scale=1.03), run_time=0.9)
        self.say("Sounds arbitrary? It's a loop-making machine.")
        pin = Text("rule: each color ×2 or ×0 at every junction",
                   font_size=22, color="#b9c2d4").to_corner(UR, buff=0.4)
        self.play(FadeOut(rule1), ReplacementTransform(rule2, pin),
                  run_time=0.8)

        # cube demo with pair lanes
        pos, edges, (horiz, vert, spokes), faces = cube_layout(cx=-2.6, cy=0.15,
                                                               out=1.75, inn=0.88)
        set_universe(edges)
        eg, ng, lines, dots = make_graph(pos, edges)
        self.play(Create(eg), FadeIn(ng), run_time=1.1)
        GRAY, RED, BLUE = (0, 0, 0), (1, 0, 0), (0, 0, 1)
        assign = {}
        for e in vert:
            assign[e] = (GRAY, RED)
        for e in horiz:
            assign[e] = (GRAY, BLUE)
        for e in spokes:
            assign[e] = (RED, BLUE)
        lanes = {}
        for e, (c1, c2) in assign.items():
            a1, b1 = lane_pts(pos[e[0]], pos[e[1]], +1)
            a2, b2 = lane_pts(pos[e[0]], pos[e[1]], -1)
            lanes[e] = VGroup(
                Line(a1, b1, stroke_width=5, color=GAMMA[c1], z_index=3),
                Line(a2, b2, stroke_width=5, color=GAMMA[c2], z_index=3))
        self.play(*[lines[e].animate.set_stroke(opacity=0.35) for e in edges],
                  LaggedStart(*[FadeIn(lanes[e]) for e in edges],
                              lag_ratio=0.05), run_time=1.6)
        self.say("Here's our flat network dressed with 3 of the 8 colors:\ngray+red, gray+blue, or red+blue on every road.")

        # verify rule at a junction
        spot = Circle(radius=0.5, color=ACC, stroke_width=3).move_to(pos[1])
        tally = VGroup(
            Text("at this junction:", font_size=24, color=MUT),
            VGroup(swatch(GRAY), Text("× 2", font_size=26)).arrange(RIGHT, buff=0.15),
            VGroup(swatch(RED), Text("× 2", font_size=26)).arrange(RIGHT, buff=0.15),
            VGroup(swatch(BLUE), Text("× 2", font_size=26)).arrange(RIGHT, buff=0.15),
        ).arrange(DOWN, buff=0.2, aligned_edge=LEFT).move_to([3.4, 1.6, 0])
        self.play(Create(spot), FadeIn(tally), run_time=0.9)
        self.say("Six lanes meet any junction. Count them here:\ngray twice, red twice, blue twice. The rule holds everywhere.")
        self.play(FadeOut(spot), FadeOut(tally), run_time=0.4)

        # extract a color
        self.say("Now the magic. Pick a color — say RED — and keep only its lanes.",
                 t2c={"RED": GAMMA[RED]}, extra=-0.8)
        red_edges = vert + spokes
        others = [e for e in edges if e not in red_edges]
        self.play(*[lanes[e].animate.set_opacity(0.10) for e in others],
                  *[lanes[e][assign[e].index(RED) ^ 1]     # dim the non-red lane
                    .animate.set_opacity(0.10) for e in red_edges],
                  run_time=1.0)
        self.say("At each junction: exactly two red lanes, or none.\nSo the red lanes CHAIN — they close up into loops. No choices needed.",
                 t2c={"CHAIN": ACC})
        lred1 = face_loop(pos, faces["left"], GAMMA[RED])
        lred2 = face_loop(pos, faces["right"], GAMMA[RED])
        self.play(Create(lred1), Create(lred2), run_time=1.3)
        self.wait(0.8)
        # show all three classes quickly
        self.play(FadeOut(lred1), FadeOut(lred2),
                  *[lanes[e].animate.set_opacity(1.0) for e in edges],
                  run_time=0.7)
        panels = []
        trio = [(GRAY, ["outer", "inner"]), (RED, ["left", "right"]),
                (BLUE, ["bottom", "top"])]
        fpos, fedges, _, ffaces = cube_layout(cx=0.0, cy=0.0, out=2.05, inn=1.02)
        for i, (col, fs) in enumerate(trio):
            g = VGroup(*[Line(fpos[e[0]], fpos[e[1]], stroke_width=3.5,
                              color=EDGE_C, stroke_opacity=0.75)
                         for e in fedges])
            lps = VGroup(*[face_loop(fpos, ffaces[f], GAMMA[col], w=5.5,
                                     outward=(f == "outer")) for f in fs])
            panels.append(VGroup(g, lps).scale(0.40)
                          .move_to([3.15, 2.05 - 2.05 * i, 0]))
        self.play(LaggedStart(*[FadeIn(p, shift=LEFT * 0.3) for p in panels],
                              lag_ratio=0.25), run_time=1.8)
        self.say("Each color's lanes: a family of loops. Three families here —\nand every road wears two colors, so it lies in exactly TWO loops.",
                 t2c={"TWO": ACC})
        self.say("That's a DOUBLE COVER — straight off the rack.\nAnd look closer: these six loops are the six map-regions from before!",
                 t2c={"DOUBLE COVER": ACC})
        self.say("The old map trick was this color trick in disguise.\nBut THIS trick never mentions 'flat'. It runs anywhere — if we can dress.")
        self.say("So fifty years of conjecture shrink to one question:\ncan EVERY bridgeless network be dressed by the rule?", t2c={"EVERY": ACC})
        self.sweep()

# ======================================================================
class Ch7Recipe(CDC):
    chapter = "7 · A LOCAL RECIPE — AND A HANDSHAKE"
    def construct(self):
        self.say("The paper builds the dressing out of the 8-flow labels.\nStep one: a recipe that works at each junction alone.")
        # junction close-up: vertex 0 of Petersen, real values
        C = np.array([-3.4, 0.45, 0])
        dirs = [np.array([np.cos(a), np.sin(a), 0])
                for a in np.deg2rad([90, 210, 330])]
        stubs = [Line(C, C + 1.75 * d, stroke_width=6) for d in dirs]
        fl = [(1, 0, 1), (1, 0, 0), (0, 0, 1)]     # x, y, z at junction 0
        for s, f in zip(stubs, fl):
            s.set_color(GAMMA[f])
        jd = node_dot(C)
        chips_ = [chip(f, h=0.42).next_to(C + 1.75 * d, d, buff=0.12)
                  for d, f in zip(dirs, fl)]
        self.play(*[Create(s) for s in stubs], FadeIn(jd), run_time=1.0)
        self.play(*[FadeIn(c) for c in chips_], run_time=0.7)
        xl = Text("x", font_size=30, color=GAMMA[fl[0]], slant=ITALIC)
        yl = Text("y", font_size=30, color=GAMMA[fl[1]], slant=ITALIC)
        zl = Text("x⊕y", font_size=30, color=GAMMA[fl[2]], slant=ITALIC)
        xl.next_to(chips_[0], UP, buff=0.15)
        yl.next_to(chips_[1], DOWN, buff=0.15)
        zl.next_to(chips_[2], DOWN, buff=0.15)
        self.play(FadeIn(xl), FadeIn(yl), FadeIn(zl), run_time=0.7)
        self.say("Zoom on one junction. Because codes cancel, its three labels\nalways look like x, y, and x⊕y. No exceptions.")

        # palette triangle with real pair values at vertex 0
        tri_c = np.array([3.2, 1.1, 0])
        corners = [(0, 0, 1), (1, 0, 0), (1, 0, 1)]      # blue red magenta
        tp = [tri_c + 1.25 * np.array([np.cos(a), np.sin(a), 0])
              for a in np.deg2rad([90, 210, 330])]
        tri_dots = [swatch(c, r=0.16).move_to(p) for c, p in zip(corners, tp)]
        tri_lines = [Line(tp[i], tp[(i + 1) % 3], stroke_width=5,
                          color="#5b6a8c") for i in range(3)]
        cap_t = Text("a base color t, then  t⊕x, t⊕(x⊕y)", font_size=24,
                     color=MUT).next_to(tri_c + DOWN * 1.6, DOWN, buff=0.1)
        self.play(*[Create(l) for l in tri_lines],
                  *[FadeIn(d, scale=1.3) for d in tri_dots],
                  FadeIn(cap_t), run_time=1.2)
        self.say("The recipe: pick any base color t. Mix three shades —\nt,  t⊕x,  t⊕(x⊕y). They form a little TRIANGLE of colors.",
                 t2c={"TRIANGLE": ACC})
        # pairs = sides
        pair_map = [((0, 0, 1), (1, 0, 0)), ((0, 0, 1), (1, 0, 1)),
                    ((1, 0, 0), (1, 0, 1))]   # real pairs at v0: (0,1),(4,0),(0,5)
        lane_grp = VGroup()
        for s, d, (c1, c2) in zip(stubs, dirs, pair_map):
            a1, b1 = lane_pts(C, C + 1.75 * d, +1, off=0.10, trim=0.14)
            a2, b2 = lane_pts(C, C + 1.75 * d, -1, off=0.10, trim=0.14)
            lane_grp.add(Line(a1, b1, stroke_width=5, color=GAMMA[c1], z_index=4),
                         Line(a2, b2, stroke_width=5, color=GAMMA[c2], z_index=4))
        self.play(*[s.animate.set_opacity(0.25) for s in stubs],
                  FadeIn(lane_grp), run_time=1.1)
        self.say("Each road takes one SIDE of the triangle as its pair.\nEvery corner touches two sides — each color appears exactly twice. ✓")
        self.say("So the junction rule is satisfied — for ANY choice of t.\nThat freedom is about to matter.", t2c={"ANY": ACC})
        self.play(*[FadeOut(m) for m in [*stubs, jd, *chips_, xl, yl, zl,
                                          *tri_lines, *tri_dots, cap_t, lane_grp]],
                  run_time=0.7)

        # the handshake
        self.say("One problem. A road has TWO ends — and each end\nruns its own recipe. Two proposals for the same road.", t2c={"TWO": BAD})
        u, v = np.array([-3.6, 0.9, 0]), np.array([3.6, 0.9, 0])
        road = Line(u, v, stroke_width=6, color=EDGE_C)
        du, dv = node_dot(u), node_dot(v)
        kn_u = Text("junction A", font_size=24, color=MUT).next_to(u, DOWN, buff=0.3)
        kn_v = Text("junction B", font_size=24, color=MUT).next_to(v, DOWN, buff=0.3)
        self.play(Create(road), FadeIn(du), FadeIn(dv), FadeIn(kn_u), FadeIn(kn_v),
                  run_time=0.9)
        # proposals: p = f(e) = 111; left {100,011}, right {001,110}
        Lp = [(1, 0, 0), (0, 1, 1)]
        Rp = [(0, 0, 1), (1, 1, 0)]
        def prop_lanes(frm, to, pair, tint=1.0):
            g = VGroup()
            for s, c in zip((+1, -1), pair):
                a, b = lane_pts(frm, to, s, off=0.11, trim=0.2)
                g.add(Line(a, b, stroke_width=5.5, color=GAMMA[c],
                           stroke_opacity=tint, z_index=4))
            return g
        mid = (u + v) / 2
        lg = prop_lanes(u, mid + LEFT * 0.25, Lp)
        rg = prop_lanes(mid + RIGHT * 0.25, v, Rp)
        self.play(FadeIn(lg, shift=RIGHT * 0.3), FadeIn(rg, shift=LEFT * 0.3),
                  run_time=0.9)
        clash = Text("✕", font_size=40, weight=BOLD, color=BAD).move_to(mid)
        self.play(FadeIn(clash, scale=1.5), run_time=0.5)
        self.say("End A says {red, cyan}. End B says {blue, yellow}. Clash.\nThe dressing only works if every road's two proposals MATCH.")
        # knob
        knob = VGroup(Circle(radius=0.34, color=ACC, stroke_width=3),
                      Line(ORIGIN, 0.30 * UP, stroke_width=4, color=ACC))
        knob.move_to(v + UP * 1.05)
        klab = Text("B's base color t", font_size=22, color=ACC).next_to(
            knob, RIGHT, buff=0.2)
        self.play(FadeIn(knob), FadeIn(klab), run_time=0.6)
        self.say("The fix: turn junction B's knob — change its base color t.",
                 extra=-1.6)
        self.play(Rotate(knob[1], angle=-2 * PI / 3,
                         about_point=knob[0].get_center()), run_time=0.8)
        rg2 = prop_lanes(mid + RIGHT * 0.25, v, Lp)
        ok = Text("✓", font_size=40, weight=BOLD, color=OK).move_to(mid)
        self.play(Transform(rg, rg2), run_time=0.8)
        self.play(Transform(clash, ok), run_time=0.5)
        self.say("Now both ends propose {red, cyan}. Handshake. ✓")
        self.say("But every knob touches THREE roads: fixing this one\ncan break its neighbours. Ten knobs, fifteen handshakes… a web.")
        eqcard = RoundedRectangle(corner_radius=0.12, width=9.4, height=1.0,
                                  stroke_color="#39415a",
                                  fill_color="#141927", fill_opacity=1.0)
        eqtxt = Text("knob(A) ⊕ knob(B) ⊕ flip(road) = offset(road)",
                     font_size=27, color=INK)
        eqg = VGroup(eqcard, eqtxt).move_to(UP * 2.55)
        self.play(FadeIn(eqg, shift=DOWN * 0.2), run_time=0.7)
        self.say("Written down, each handshake is one tiny PARITY equation —\nyes/no arithmetic where 1 ⊕ 1 = 0. One equation per road.",
                 t2c={"PARITY": ACC})
        self.say("The entire fifty-year conjecture is now a single question:\ndoes this pile of tiny equations ALWAYS have a solution?",
                 t2c={"ALWAYS": ACC})
        self.sweep()

# ======================================================================
class Ch8Miracle(CDC):
    chapter = "8 · TWO ENDS — THE PARITY MIRACLE"
    def construct(self):
        self.say("When can a pile of parity equations be unsolvable?\nLinear algebra gives the only failure mode:", extra=-0.6)
        card = Text("some bundle of equations combines into nonsense:  0 = 1",
                    font_size=27, color=BAD, weight=BOLD)
        if card.width > 11.8:
            card.scale_to_fit_width(11.8)
        card.move_to(UP * 2.35)
        self.play(FadeIn(card, scale=1.03), run_time=0.8)
        self.say("No nonsense-bundle → a solution exists. Guaranteed.\nSo the paper hunts for nonsense — to prove there is none.")

        ppos, pedges = pet_layout(cy=0.1, R=2.0, r=1.08)
        set_universe(pedges)
        peg, png_, plines, pdots = make_graph(ppos, pedges)
        self.play(Create(peg), FadeIn(png_), card.animate.set_opacity(0.35),
                  run_time=1.2)
        self.say("Take ANY candidate bundle. The paper totals it up, junction\nby junction: each contributes a single parity bit — 0 or 1.")
        # junction parity badges
        badges = VGroup()
        rng = np.random.default_rng(3)
        ctr = np.array([0.0, 0.1, 0.0])
        for vv in range(10):
            b = Text(str(rng.integers(0, 2)), font_size=24, weight=BOLD,
                     color=ACC)
            out = ppos[vv] - ctr
            u_ = out / np.linalg.norm(out)
            if vv >= 5:      # nudge inner badges off the spokes/chords
                a_ = np.deg2rad(28)
                u_ = np.array([np.cos(a_) * u_[0] - np.sin(a_) * u_[1],
                               np.sin(a_) * u_[0] + np.cos(a_) * u_[1], 0.0])
            b.move_to(ppos[vv] + u_ * 0.42)
            badges.add(b)
        self.play(LaggedStart(*[FadeIn(b, scale=1.4) for b in badges],
                              lag_ratio=0.07), run_time=1.2)
        self.say("Add all the bits: if the total could be 1, nonsense might exist.\nSo — what IS the total?")

        # the double count
        self.say("Here is the miracle. Junction bits come from roads —\nand every single road donates to BOTH of its ends.", t2c={"BOTH": ACC},
                 extra=-0.4)
        sparks = VGroup()
        target = np.array([4.6, 1.2, 0])
        for (a, b) in pedges:
            pa, pb = ppos[a], ppos[b]
            sparks.add(Dot(radius=0.06, color=ACC).move_to(
                pa * 0.8 + pb * 0.2))
            sparks.add(Dot(radius=0.06, color=ACC).move_to(
                pa * 0.2 + pb * 0.8))
        self.play(FadeIn(sparks), FadeOut(badges), run_time=0.8)
        tally = Text("total", font_size=24, color=MUT).move_to(
            target + UP * 0.75)
        self.play(FadeIn(tally),
                  *[s.animate.move_to(target
                                      + np.array([0.32 * (i % 6) - 0.8,
                                                  0.32 * (i // 6) - 1.4, 0]))
                    for i, s in enumerate(sparks)], run_time=1.8)
        self.say("Thirty donations for fifteen roads: every road counted TWICE.",
                 t2c={"TWICE": ACC}, extra=-0.6)
        # annihilate in pairs
        pairs_anim = []
        for i in range(0, 30, 2):
            pairs_anim.append(AnimationGroup(
                sparks[i].animate.move_to(target).set_opacity(0),
                sparks[i + 1].animate.move_to(target).set_opacity(0)))
        zero = Text("0", font_size=64, weight=BOLD, color=OK).move_to(target)
        self.play(LaggedStart(*pairs_anim, lag_ratio=0.06), run_time=2.2)
        self.play(FadeIn(zero, scale=1.4), run_time=0.5)
        self.say("And in parity arithmetic, twice = zero. 1 ⊕ 1 = 0.\nEvery candidate bundle totals 0 — never 1. NO NONSENSE EXISTS.",
                 t2c={"NO NONSENSE EXISTS": OK})
        self.say("So the handshake equations always have a solution.\nThe dressing always exists. The loops always appear.")

        veil = self.veil(0.95)
        qed1 = Text("THEOREM", font_size=30, weight=BOLD, color=ACC
                    ).set_z_index(10).move_to(UP * 1.6)
        qed2 = Text("Every bridgeless network\nhas a cycle double cover.",
                    font_size=40, color=INK, line_spacing=1.1
                    ).set_z_index(10).move_to(UP * 0.3)
        qed3 = Text("The obstacle to tracing every road twice…\ndies because every road has two ends.",
                    font_size=27, color="#b9c2d4", line_spacing=1.1
                    ).set_z_index(10).move_to(DOWN * 1.6)
        self.play(FadeIn(veil), FadeIn(qed1), run_time=0.8)
        self.play(FadeIn(qed2, scale=1.03), run_time=0.8)
        self.wait(1.0)
        self.play(FadeIn(qed3), run_time=0.8)
        self.wait(3.4)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)

# ======================================================================
class Ch9Finale(CDC):
    chapter = "9 · THE MACHINE RUNS"
    def construct(self):
        ppos, pedges = pet_layout(cy=0.35, R=2.5, r=1.35)
        set_universe(pedges)
        peg, png_, plines, pdots = make_graph(ppos, pedges)
        self.play(Create(peg), FadeIn(png_), run_time=1.4)
        self.say("Let's watch the whole machine run — on the snark itself.\n(Everything you'll see was computed, not staged.)", size=27)
        # flow
        self.play(*[plines[e].animate.set_stroke(color=GAMMA[PET_FLOW[e]],
                                                 width=6) for e in pedges],
                  run_time=1.2)
        self.say("Step 1 — the 8-flow: codes on every road, cancelling everywhere.",
                 extra=-0.6)
        # recipe: dissolve into pair lanes (real pairs)
        lanes = {}
        lane_anims = []
        for e in pedges:
            c1, c2 = PET_PAIRS[e]
            a1, b1 = lane_pts(ppos[e[0]], ppos[e[1]], +1)
            a2, b2 = lane_pts(ppos[e[0]], ppos[e[1]], -1)
            lg = VGroup(Line(a1, b1, stroke_width=5, color=GAMMA[c1], z_index=3),
                        Line(a2, b2, stroke_width=5, color=GAMMA[c2], z_index=3))
            lanes[e] = lg
            lane_anims.append(FadeIn(lg))
        self.play(*[plines[e].animate.set_stroke(color=EDGE_C, width=4.5,
                                                 opacity=0.5) for e in pedges],
                  LaggedStart(*lane_anims, lag_ratio=0.04), run_time=2.0)
        self.say("Step 2 — recipes at all ten junctions, knobs tuned,\nhandshakes solved: every road now wears its two colors.")
        spot9 = Circle(radius=0.52, color=ACC, stroke_width=3).move_to(ppos[7])
        self.play(Create(spot9), run_time=0.5)
        self.say("Check any junction: each color there appears exactly twice.",
                 extra=-0.4)
        self.play(FadeOut(spot9), run_time=0.4)
        # extract loops color by color
        cnt = VGroup(Text("roads with 2 passes", font_size=20, color=MUT),
                     Text("0 / 15", font_size=30, weight=BOLD, color=ACC))
        cnt.arrange(DOWN, buff=0.12).to_corner(UR, buff=0.42)
        self.play(FadeIn(cnt), run_time=0.4)
        self.say("Step 3 — pull the loops out, color by color.", extra=-1.0)
        order = [(0, 0, 0), (0, 0, 1), (0, 1, 1), (1, 0, 0), (1, 0, 1)]
        covered = {}
        done = 0
        all_loops = []
        for s in order:
            for cyc in PET_MS[s]:
                lp = pair_loop(ppos, cyc, s, w=6)
                all_loops.append(lp)
                # dim non-s lanes
                dims, undims = [], []
                for e in pedges:
                    for li, c in zip(lanes[e], PET_PAIRS[e]):
                        if c != s:
                            dims.append(li.animate.set_opacity(0.12))
                            undims.append(li.animate.set_opacity(1.0))
                self.play(*dims, run_time=0.45)
                self.play(Create(lp), run_time=1.5)
                n = len(cyc)
                for i in range(n):
                    k = edge_key(cyc[i], cyc[(i + 1) % n])
                    covered[k] = covered.get(k, 0) + 1
                done = sum(1 for v_ in covered.values() if v_ >= 2)
                new = Text(f"{done} / 15", font_size=30, weight=BOLD,
                           color=ACC).move_to(cnt[1])
                self.play(*undims, Transform(cnt[1], new), run_time=0.45)
        self.say("Five loops. Thirty lane-slots. Every road: exactly two passes.\nThe Petersen graph — double covered. ∎", t2c={"∎": OK})
        self.wait(0.6)

        # beauty shot: hemi-dodecahedron
        self.play(*[FadeOut(l) for l in all_loops],
                  *[FadeOut(lanes[e]) for e in pedges], FadeOut(cnt),
                  *[plines[e].animate.set_stroke(color=EDGE_C, width=4.5,
                                                 opacity=1.0) for e in pedges],
                  run_time=0.9)
        self.say("One last treat. Double covers aren't unique — the most symmetric\none for Petersen wears six pentagons. Watch.", extra=-0.8)
        reg2 = LaneRegistry()
        hcols = ["#f25757", "#f2c94c", "#43c464", "#35c8c8", "#4e8df5", "#d45cf0"]
        hloops = [reg_loop(ppos, c, col, reg2, w=5.5)
                  for c, col in zip(HEMI, hcols)]
        self.play(LaggedStart(*[Create(l) for l in hloops], lag_ratio=0.2),
                  run_time=4.0)
        self.say("Six pentagons, each road on exactly two —\nthe ghost of a dodecahedron, folded into the plane.")
        self.wait(0.5)

        # end card
        veil = self.veil(0.95)
        t1 = Text("THE CYCLE DOUBLE COVER CONJECTURE", font_size=28,
                  weight=BOLD, color=ACC).set_z_index(10).move_to(UP * 2.5)
        t2 = Text("posed 1970s — Szekeres · Itai & Rodeh · Seymour · Tutte\nproof claimed July 2026 (the paper credits an AI system)",
                  font_size=24, color=INK, line_spacing=1.2
                  ).set_z_index(10).move_to(UP * 1.2)
        t3 = Text("the route:  cubic networks → 8-flow (Jaeger, Kilpatrick)\n→ dress each road in two of eight colors → loops for free\n→ handshakes = parity equations → solvable, since every road has two ends",
                  font_size=22, color="#b9c2d4", line_spacing=1.25
                  ).set_z_index(10).move_to(DOWN * 0.5)
        t4 = Text("full rigor: three pages of flows, duals and one linear-algebra lemma",
                  font_size=20, color=MUT).set_z_index(10).move_to(DOWN * 2.0)
        t5 = Text("every road · two ends · two passes", font_size=24,
                  color=ACC).set_z_index(10).move_to(DOWN * 2.9)
        self.play(FadeIn(veil), FadeIn(t1), run_time=0.9)
        self.play(FadeIn(t2), run_time=0.7)
        self.play(FadeIn(t3), run_time=0.7)
        self.play(FadeIn(t4), run_time=0.6)
        self.play(FadeIn(t5, scale=1.05), run_time=0.7)
        self.wait(4.5)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.2)
