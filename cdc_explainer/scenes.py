"""TWICE — a layman's video tour of the announced proof of the
Cycle Double Cover Conjecture (July 2026), built with Manim.

Every graph, flow value, color pair and loop shown on screen is loaded from
cdc_data.json, which is produced and checked by verify_math.py.  Nothing is
staged.

Render (fast draft):
    manim render -ql scenes.py C00Title C01Game C02Maps C03Conjecture \
        C04Snark C05Mixes C06TwoColors C07Triangle C08Handshake \
        C09Machine C10End
"""

from __future__ import annotations

import json
import os
from collections import defaultdict

import numpy as np
from manim import *

# ---------------------------------------------------------------- palette
BG = "#0b0e14"
TEXT_C = "#e8eaf0"
MUTED = "#939db0"
FAINT = "#5b6474"
EDGE_C = "#4d5870"
NODE_C = "#f2f4f8"
ACCENT = "#ffd166"
BAD = "#ff5d5d"
GOOD = "#3ddc84"

# the 8 codes: color = additive mix of the lit R/G/B switches
CODE_COLOR = {
    (0, 0, 0): "#aab4c4",   # OFF -> worn as a plain light-gray vest
    (1, 0, 0): "#ff5d5d",
    (0, 1, 0): "#3ddc84",
    (0, 0, 1): "#4ea1ff",
    (1, 1, 0): "#ffb020",
    (1, 0, 1): "#e06bff",
    (0, 1, 1): "#2fd3c8",
    (1, 1, 1): "#f2f4f8",
}
CODE_NAME = {
    (0, 0, 0): "off",
    (1, 0, 0): "red",
    (0, 1, 0): "green",
    (0, 0, 1): "blue",
    (1, 1, 0): "amber",
    (1, 0, 1): "magenta",
    (0, 1, 1): "cyan",
    (1, 1, 1): "white",
}
SWITCH_ON = {0: "#ff5d5d", 1: "#3ddc84", 2: "#4ea1ff"}
SWITCH_OFF = "#242b3a"

FONT = "DejaVu Sans"
CAP_Y = -3.3
SAFE_W = 12.9

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cdc_data.json")
with open(DATA_PATH) as _fh:
    DATA = json.load(_fh)

PET_EDGES = [tuple(e) for e in DATA["petersen_edges"]]
CUBE_EDGES = [tuple(e) for e in DATA["cube_edges"]]
PET_FLOW = {tuple(map(int, k.split(","))): tuple(v) for k, v in DATA["flow"].items()}
PET_PAIRS = {
    tuple(map(int, k.split(","))): [tuple(p) for p in v]
    for k, v in DATA["pairs"].items()
}
PET_BASE = {int(k): tuple(v) for k, v in DATA["base_colors"].items()}
PET_MS = {eval(k): v for k, v in DATA["pet_Ms"].items()}
CUBE_AXIS = {tuple(map(int, k.split(","))): v for k, v in DATA["cube_axis"].items()}
HEMI = DATA["hemi_faces"]


def xor(p, q):
    return tuple(a ^ b for a, b in zip(p, q))


def fit(m, max_w=SAFE_W):
    if m.width > max_w:
        m.scale_to_fit_width(max_w)
    return m


# ---------------------------------------------------------------- layouts
def pet_layout(cx=0.0, cy=0.5, R=2.35, r=1.27):
    pos = {}
    for i in range(5):
        a = PI / 2 + i * TAU / 5
        pos[i] = np.array([cx + R * np.cos(a), cy + R * np.sin(a), 0])
        pos[5 + i] = np.array([cx + r * np.cos(a), cy + r * np.sin(a), 0])
    return pos


def cube_layout(cx=0.0, cy=0.45, out=2.0, inn=1.0):
    # planar drawing of Q3; vertex ids are the 3-bit ints from verify_math
    sq = lambda h: [
        np.array([cx - h, cy + h, 0]),
        np.array([cx + h, cy + h, 0]),
        np.array([cx + h, cy - h, 0]),
        np.array([cx - h, cy - h, 0]),
    ]
    o, i_ = sq(out), sq(inn)
    return {0: o[0], 1: o[1], 3: o[2], 2: o[3], 4: i_[0], 5: i_[1], 7: i_[2], 6: i_[3]}


CUBE_FACES = [  # bounded faces of that drawing (ccw vertex lists)
    [0, 1, 5, 4],
    [1, 3, 7, 5],
    [3, 2, 6, 7],
    [2, 0, 4, 6],
    [4, 5, 7, 6],
]
FACE_FILLS = ["#1f6f64", "#6e2f3f", "#4c5e2a", "#2b3a67", "#54486e"]
OUTSIDE_FILL = "#141a28"


def k4_layout(cx=0.0, cy=0.35, R=2.2):
    ang = [PI / 2, PI / 2 + TAU / 3, PI / 2 + 2 * TAU / 3]
    pos = {i: np.array([cx + R * np.cos(a), cy + R * np.sin(a), 0]) for i, a in enumerate(ang)}
    pos[3] = np.array([cx, cy, 0])
    return pos


K4_EDGES = [(0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3)]
K4_LOOPS = [[0, 1, 3], [1, 2, 3], [2, 0, 3], [0, 1, 2]]  # faces: each edge twice


# ---------------------------------------------------------------- widgets
def node_dot(p, r=0.085, halo=0.18):
    return VGroup(
        Circle(radius=halo, fill_color=NODE_C, fill_opacity=0.13, stroke_width=0).move_to(p),
        Dot(p, radius=r, color=NODE_C, z_index=3),
    )


def edge_line(P, Q, color=EDGE_C, w=5.0, opacity=1.0):
    return Line(
        P, Q, stroke_color=color, stroke_width=w, stroke_opacity=opacity,
        cap_style=CapStyleType.ROUND,
    )


def make_graph(pos, edges, edge_color=EDGE_C, w=5.0):
    e_ms = {e: edge_line(pos[e[0]], pos[e[1]], edge_color, w) for e in edges}
    n_ms = {v: node_dot(p) for v, p in pos.items()}
    return VGroup(*e_ms.values()), VGroup(*n_ms.values()), e_ms, n_ms


def seg_lane(pos, u, v, side, off=0.11, trim=0.0):
    """Offset segment along edge (u,v). side +1/-1 relative to canonical dir."""
    a, b = (u, v) if u < v else (v, u)
    P, Q = pos[a], pos[b]
    d = Q - P
    L = np.linalg.norm(d)
    d = d / L
    n = np.array([-d[1], d[0], 0]) * off * side
    P2, Q2 = P + d * trim + n, Q - d * trim + n
    if u > v:
        P2, Q2 = Q2, P2
    return P2, Q2


def loop_lane_poly(pos, cycle, side_of_edge, color, w=5.5, off=0.11):
    """Closed lane polyline for a cycle; side_of_edge: {frozenset: +1/-1}."""
    pts = []
    n = len(cycle)
    for i in range(n):
        u, v = cycle[i], cycle[(i + 1) % n]
        s = side_of_edge[frozenset((u, v))]
        P, Q = seg_lane(pos, u, v, s, off=off)
        pts += [P, Q]
    poly = Polygon(
        *pts, stroke_color=color, stroke_width=w, fill_opacity=0,
        joint_type=LineJointType.ROUND,
    )
    return poly


def face_loop(pos, cycle, color, inward=True, w=5.5, off=0.11):
    """Loop hugging one side of each road: toward (or away from) face centroid."""
    C = np.mean([pos[v] for v in cycle], axis=0)
    side = {}
    n = len(cycle)
    for i in range(n):
        u, v = cycle[i], cycle[(i + 1) % n]
        a, b = (u, v) if u < v else (v, u)
        P, Q = pos[a], pos[b]
        d = (Q - P) / np.linalg.norm(Q - P)
        nrm = np.array([-d[1], d[0], 0])
        mid = (P + Q) / 2
        toward = 1 if np.dot(C - mid, nrm) > 0 else -1
        side[frozenset((u, v))] = toward if inward else -toward
    return loop_lane_poly(pos, cycle, side, color, w=w, off=off)


class LaneBook:
    """Hands out lane sides per edge: first request gets +1, second -1 —
    also queryable by color so static pair-lanes and loops agree."""

    def __init__(self):
        self.byedge = defaultdict(list)  # frozenset -> [color keys]

    def side(self, u, v, key):
        e = frozenset((u, v))
        if key not in self.byedge[e]:
            self.byedge[e].append(key)
        return +1 if self.byedge[e].index(key) == 0 else -1


def pair_lanes(pos, edge, pair, book: LaneBook, w=5.0, off=0.11, trim=0.14):
    """Two colored lanes on one road, one per code in its pair."""
    u, v = edge
    out = VGroup()
    for code in sorted(pair):
        s = book.side(u, v, code)
        P, Q = seg_lane(pos, u, v, s, off=off, trim=trim)
        out.add(
            Line(P, Q, stroke_color=CODE_COLOR[code], stroke_width=w,
                 cap_style=CapStyleType.ROUND)
        )
    return out


def class_loops(pos, code, cycles, book: LaneBook, w=6.0, off=0.11):
    """Loops of one color class, laid on the lanes LaneBook assigned to it."""
    polys = VGroup()
    for cyc in cycles:
        side = {}
        n = len(cyc)
        for i in range(n):
            u, v = cyc[i], cyc[(i + 1) % n]
            side[frozenset((u, v))] = book.side(u, v, code)
        polys.add(loop_lane_poly(pos, cyc, side, CODE_COLOR[code], w=w, off=off))
    return polys


def chip(code, w=0.60, show_dots=True, label=None):
    """A code as a physical chip: 3 R/G/B switch dots, tinted by the mix."""
    col = CODE_COLOR[code]
    box = RoundedRectangle(
        width=w, height=w * 0.55, corner_radius=0.09,
        stroke_color=col, stroke_width=2.4,
        fill_color=col, fill_opacity=0.13,
    )
    g = VGroup(box)
    if show_dots:
        for i in range(3):
            c = SWITCH_ON[i] if code[i] else SWITCH_OFF
            g.add(Dot(radius=w * 0.085, color=c).move_to(
                box.get_center() + RIGHT * (i - 1) * w * 0.26))
    if label:
        g.add(Text(label, font=FONT, font_size=17, color=col).next_to(box, DOWN, buff=0.08))
    return g


def swatch(code, r=0.10):
    return Dot(radius=r, color=CODE_COLOR[code], stroke_color="#0b0e14", stroke_width=1.5)


def stamp_point(pos, e):
    """Chip anchor for edge e; star edges anchor off-center to avoid pile-up."""
    u, v = e
    t = 0.30 if (u >= 5 and v >= 5) else 0.5
    return pos[u] + (pos[v] - pos[u]) * t


def cross_mark(p, s=0.14, color=BAD, w=6):
    return VGroup(
        Line(p + s * (UL), p + s * (DR), stroke_color=color, stroke_width=w,
             cap_style=CapStyleType.ROUND),
        Line(p + s * (UR), p + s * (DL), stroke_color=color, stroke_width=w,
             cap_style=CapStyleType.ROUND),
    )


def check_mark(p, s=0.16, color=GOOD, w=6):
    a = p + np.array([-s, 0.1 * s, 0])
    b = p + np.array([-0.25 * s, -0.7 * s, 0])
    c = p + np.array([s, 0.8 * s, 0])
    m = VMobject(stroke_color=color, stroke_width=w, cap_style=CapStyleType.ROUND,
                 joint_type=LineJointType.ROUND)
    m.set_points_as_corners([a, b, c])
    return m


# ---------------------------------------------------------------- scene base
class CDC(Scene):
    KICK = None

    def setup(self):
        self.camera.background_color = BG
        self._cap = None
        self._cap_need = 0.0
        self._cap_spent = 0.0

    # -------- captions ----------------------------------------------------
    def _caption(self, lines, size):
        rows = [fit(Text(ln, font=FONT, font_size=size, color=TEXT_C)) for ln in lines]
        g = VGroup(*rows).arrange(DOWN, buff=0.15)
        dy = 0.19 if len(rows) == 1 else (0.30 if len(rows) >= 3 else 0.0)
        g.move_to([0, CAP_Y + dy, 0])
        return g

    def say(self, *lines, hold=True, extra=0.0, size=31):
        """Swap the caption. If hold, wait out its reading time; otherwise the
        chapter plays animations and calls self.pad() when done."""
        new = self._caption(lines, size)
        if self._cap is not None:
            self.play(FadeOut(self._cap, run_time=0.22))
        self.play(FadeIn(new, shift=UP * 0.12, run_time=0.3))
        self._cap = new
        chars = sum(len(l) for l in lines)
        self._cap_need = max(2.15, 0.8 + 0.047 * chars) + extra
        self._cap_spent = 0.52
        if hold:
            self.pad()

    def pad(self, extra=0.0):
        rem = self._cap_need - self._cap_spent + extra
        if rem > 0:
            self.wait(rem)
        self._cap_spent = self._cap_need

    def play(self, *args, **kwargs):
        super().play(*args, **kwargs)
        rt = kwargs.get("run_time")
        if rt is None:
            rts = [getattr(a, "run_time", 1.0) for a in args if isinstance(a, Animation)]
            rt = max(rts) if rts else 1.0
        self._cap_spent += rt

    def wait(self, duration=1.0, **kw):
        super().wait(duration, **kw)
        self._cap_spent += duration

    # -------- chrome ------------------------------------------------------
    def kick(self, txt):
        k = Text(txt.upper(), font=FONT, font_size=25, color=MUTED, weight=BOLD)
        k.to_corner(UL, buff=0.42)
        rule = Line(ORIGIN, RIGHT * k.width, stroke_color=FAINT, stroke_width=2)
        rule.next_to(k, DOWN, buff=0.09, aligned_edge=LEFT)
        self.play(FadeIn(k, shift=RIGHT * 0.2), Create(rule), run_time=0.5)
        return VGroup(k, rule)

    def counter(self, label, total):
        lab = Text(label, font=FONT, font_size=20, color=MUTED)
        den = Text(f"/ {total}", font=FONT, font_size=27, color=MUTED)
        num = Text("0", font=FONT, font_size=38, weight=BOLD, color=ACCENT)
        den.to_corner(UR, buff=0.42).shift(DOWN * 0.42)
        num.next_to(den, LEFT, buff=0.14, aligned_edge=DOWN)
        lab.next_to(den, UP, buff=0.14, aligned_edge=RIGHT)
        self._ctr_num, self._ctr_den = num, den
        self.play(FadeIn(lab), FadeIn(num), FadeIn(den), run_time=0.4)
        return VGroup(lab, num, den)

    def set_count(self, n, rt=0.3):
        new = Text(str(n), font=FONT, font_size=38, weight=BOLD, color=ACCENT)
        new.next_to(self._ctr_den, LEFT, buff=0.14, aligned_edge=DOWN)
        self.play(ReplacementTransform(self._ctr_num, new), run_time=rt)
        self._ctr_num = new

    def clear_all(self):
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        self.wait(0.25)

    # -------- shared set pieces -------------------------------------------
    def trace_loop(self, poly, run_time=2.0, walker=True):
        if not walker:
            self.play(Create(poly), run_time=run_time, rate_func=linear)
            return
        dot = Dot(radius=0.075, color=WHITE, z_index=6)
        dot.move_to(poly.point_from_proportion(0))
        self.play(FadeIn(dot, run_time=0.12))
        self.play(Create(poly), MoveAlongPath(dot, poly),
                  run_time=run_time, rate_func=linear)
        self.play(FadeOut(dot, run_time=0.12))


# ======================================================================
# 0 · TITLE
# ======================================================================
class C00Title(CDC):
    def construct(self):
        pos = pet_layout(cy=0.1, R=2.75, r=1.5)
        edges_g, nodes_g, _, _ = make_graph(pos, PET_EDGES, w=4.0)
        edges_g.set_stroke(opacity=0.5)
        self.play(Create(edges_g), FadeIn(nodes_g), run_time=1.6)

        # the real 5-loop double cover, drawn vividly
        book = LaneBook()
        loops = VGroup()
        for code_s, cycles in PET_MS.items():
            loops.add(*class_loops(pos, tuple(code_s), cycles, book, w=5.0, off=0.12))
        self.play(LaggedStart(*[Create(l) for l in loops], lag_ratio=0.12),
                  run_time=3.4)
        self.wait(0.4)

        ctr = np.array([0, 0.1, 0])
        self.play(
            edges_g.animate.set_stroke(opacity=0.08).scale(1.18, about_point=ctr),
            loops.animate.set_stroke(opacity=0.13).scale(1.18, about_point=ctr),
            nodes_g.animate.set_fill(opacity=0.1).scale(1.18, about_point=ctr),
            run_time=0.9,
        )

        title = Text("TWICE", font=FONT, font_size=112, weight=BOLD, color=TEXT_C)
        title.move_to([0, 0.75, 0])
        sub = Text("a fifty-year puzzle about walking every road twice",
                   font=FONT, font_size=34, color=TEXT_C)
        sub.next_to(title, DOWN, buff=0.42)
        tag = Text("the proof announced July 10, 2026 — explained in pictures",
                   font=FONT, font_size=26, color=MUTED)
        tag.next_to(sub, DOWN, buff=0.32)
        prom = Text("(no equations, promise)", font=FONT, font_size=22, color=FAINT)
        prom.next_to(tag, DOWN, buff=0.28)
        for m in (title, sub, tag, prom):
            fit(m)
        self.play(Write(title), run_time=1.1)
        self.play(FadeIn(sub, shift=UP * 0.15), run_time=0.7)
        self.play(FadeIn(tag), FadeIn(prom), run_time=0.7)
        self.wait(2.6)
        self.clear_all()


# ======================================================================
# 1 · THE GAME
# ======================================================================
class C01Game(CDC):
    def construct(self):
        self.kick("1 · the game")
        pos = k4_layout()
        edges_g, nodes_g, e_ms, _ = make_graph(pos, K4_EDGES)

        self.say("Here is a road network: junctions, and roads between them.",
                 hold=False)
        self.play(Create(edges_g), FadeIn(nodes_g), run_time=1.4)
        self.pad()

        self.say("The game: plan round trips — walks that end where they began",
                 "and never repeat a road.", hold=False)
        book = LaneBook()
        loop_colors = ["#4ea1ff", "#ff5d5d", "#3ddc84", "#ffb020"]
        polys = []
        for cyc, col in zip(K4_LOOPS, loop_colors):
            side = {}
            for i in range(len(cyc)):
                u, v = cyc[i], cyc[(i + 1) % len(cyc)]
                side[frozenset((u, v))] = book.side(u, v, col)
            polys.append(loop_lane_poly(pos, cyc, side, col))
        self.trace_loop(polys[0], run_time=2.4)
        self.pad()

        self.say("When all trips are done, every road must have been",
                 "walked exactly TWICE — that is the whole game.", hold=False)
        self.counter("roads walked twice", 6)
        passes = defaultdict(int)
        done = 0
        for cyc in K4_LOOPS[:1]:
            for i in range(len(cyc)):
                passes[frozenset((cyc[i], cyc[(i + 1) % len(cyc)]))] += 1
        for k, (cyc, poly) in enumerate(zip(K4_LOOPS[1:], polys[1:]), start=1):
            self.trace_loop(poly, run_time=1.7, walker=(k == 1))
            for i in range(len(cyc)):
                passes[frozenset((cyc[i], cyc[(i + 1) % len(cyc)]))] += 1
            new_done = sum(1 for v in passes.values() if v == 2)
            if new_done != done:
                done = new_done
                self.set_count(done, rt=0.25)
        self.pad()

        self.say("Four round trips — and each of the six roads is used",
                 "exactly twice. This network wins the game.", extra=0.4)

        # ---- why twice, not once ------------------------------------------
        self.say("But why ask for twice, and not once?", hold=False)
        ctr_grp = VGroup(self._ctr_num, self._ctr_den)
        lab_hits = [m for m in self.mobjects if isinstance(m, Text)
                    and m.text == "roads walked twice"]
        self.play(
            edges_g.animate.set_stroke(opacity=0.06),
            nodes_g.animate.set_fill(opacity=0.06),
            *[p.animate.set_stroke(opacity=0.05) for p in polys],
            FadeOut(ctr_grp), *[FadeOut(m) for m in lab_hits],
            run_time=0.6,
        )
        self.pad()

        # junction cam: 3 roads at 120 degrees
        C = np.array([0, 0.5, 0])
        arms = [C + 1.55 * np.array([np.cos(a), np.sin(a), 0])
                for a in (PI / 2, PI / 2 + TAU / 3, PI / 2 + 2 * TAU / 3)]
        roads = VGroup(*[edge_line(C, A, w=6) for A in arms])
        jnode = node_dot(C, r=0.1)
        self.say("Watch one trip pass any junction: it arrives on one road",
                 "and leaves on another — it uses roads in PAIRS.", hold=False)
        self.play(Create(roads), FadeIn(jnode), run_time=0.8)
        w = Dot(radius=0.08, color=WHITE, z_index=6).move_to(arms[0])
        path = VMobject().set_points_as_corners([arms[0], C, arms[1]])
        trail = VMobject(stroke_color="#4ea1ff", stroke_width=7,
                         cap_style=CapStyleType.ROUND,
                         joint_type=LineJointType.ROUND)
        trail.set_points_as_corners([arms[0], C, arms[1]])
        self.play(FadeIn(w, run_time=0.15))
        self.play(MoveAlongPath(w, path), Create(trail), run_time=1.6,
                  rate_func=linear)
        self.play(FadeOut(w, run_time=0.15))
        self.pad()

        self.say("Three roads meet here. Once each would be three slots —",
                 "and pairs can never fill an odd number.", hold=False)
        lone = cross_mark(arms[2] * 0.55 + C * 0.45, s=0.17)
        self.play(roads[2].animate.set_stroke(color=BAD), FadeIn(lone, scale=0.6),
                  run_time=0.7)
        self.pad()

        self.say("Twice each gives SIX slots: three tidy in-and-out pairs.",
                 "Twice is the smallest fair ask at a 3-way junction.", hold=False)
        trail2 = VMobject(stroke_color="#ffb020", stroke_width=7,
                          cap_style=CapStyleType.ROUND, joint_type=LineJointType.ROUND)
        trail2.set_points_as_corners([arms[1], C, arms[2]])
        trail3 = VMobject(stroke_color="#3ddc84", stroke_width=7,
                          cap_style=CapStyleType.ROUND, joint_type=LineJointType.ROUND)
        trail3.set_points_as_corners([arms[2], C, arms[0]])
        for t in (trail2, trail3):
            t.shift((C - t.get_center()) * 0.12)
        self.play(roads[2].animate.set_stroke(color=EDGE_C), FadeOut(lone),
                  run_time=0.4)
        self.play(Create(trail2), run_time=0.9)
        self.play(Create(trail3), run_time=0.9)
        ok = check_mark(C + RIGHT * 2.6 + UP * 0.4)
        self.play(FadeIn(ok, scale=0.6), run_time=0.4)
        self.pad()

        self.say("So the real question: can EVERY road network be",
                 "double-walked? That innocent riddle is 50 years old.",
                 extra=0.5)
        self.clear_all()


# ======================================================================
# 2 · MAPS ALREADY KNOW THE ANSWER
# ======================================================================
class C02Maps(CDC):
    def construct(self):
        self.kick("2 · maps already know the answer")
        pos = cube_layout()
        edges_g, nodes_g, e_ms, _ = make_graph(pos, CUBE_EDGES)

        self.say("Some networks lie flat: you can draw them with no roads",
                 "crossing. A flat network is secretly a MAP.", hold=False)
        self.play(Create(edges_g), FadeIn(nodes_g), run_time=1.3)
        self.pad()

        # region fills
        fills = VGroup()
        for face, col in zip(CUBE_FACES, FACE_FILLS):
            poly = Polygon(*[pos[v] for v in face], stroke_width=0,
                           fill_color=col, fill_opacity=0.5, z_index=-2)
            fills.add(poly)
        big = Rectangle(width=15, height=9, stroke_width=0,
                        fill_color=OUTSIDE_FILL, fill_opacity=0.9, z_index=-3)
        big.move_to([0, 0.45, 0])
        outer_sq = Polygon(*[pos[v] for v in [0, 1, 3, 2]], stroke_width=0)
        outside = Difference(big, outer_sq, stroke_width=0,
                             fill_color=OUTSIDE_FILL, fill_opacity=0.85)
        outside.set_z_index(-3)

        self.say("Its regions are countries — five of them here…", hold=False)
        self.play(LaggedStart(*[FadeIn(f) for f in fills], lag_ratio=0.15),
                  run_time=1.6)
        self.pad()
        self.say("…plus one more country: the endless OUTSIDE. Six regions.",
                 hold=False)
        self.play(FadeIn(outside), run_time=0.9)
        self.pad()

        self.say("The key fact about maps: every road has exactly two sides —",
                 "one region touching it on the left, one on the right.",
                 hold=False)
        e = e_ms[(0, 1)]  # top road: face 0 below, outside above
        self.play(Indicate(e, color=ACCENT, scale_factor=1.05), run_time=0.9)
        p1 = Dot(e.get_center() + DOWN * 0.45, radius=0.09, color=ACCENT)
        p2 = Dot(e.get_center() + UP * 0.45, radius=0.09, color=ACCENT)
        self.play(FadeIn(p1, scale=0.5), FadeIn(p2, scale=0.5), run_time=0.6)
        self.play(FadeOut(p1), FadeOut(p2), run_time=0.4)
        self.pad()

        self.say("Now let every region walk its own border, once around.",
                 hold=False)
        self.counter("roads walked twice", 12)
        loop_cols = ["#2fd3c8", "#ff5d5d", "#3ddc84", "#4ea1ff", "#e06bff"]
        passes = defaultdict(int)
        done = 0

        def bump(cyc):
            nonlocal done
            for i in range(len(cyc)):
                passes[frozenset((cyc[i], cyc[(i + 1) % len(cyc)]))] += 1
            nd = sum(1 for v in passes.values() if v == 2)
            if nd != done:
                done = nd
                self.set_count(done, rt=0.25)

        for k, (face, col) in enumerate(zip(CUBE_FACES, loop_cols)):
            loop = face_loop(pos, face, col, inward=True)
            self.trace_loop(loop, run_time=1.6 if k == 0 else 1.0, walker=(k == 0))
            bump(face)
        self.say("…and the outside walks its border too.", hold=False)
        out_loop = face_loop(pos, [0, 1, 3, 2], ACCENT, inward=False)
        self.trace_loop(out_loop, run_time=1.4, walker=True)
        bump([0, 1, 3, 2])
        self.pad()

        self.say("Each road was walked once from each side: exactly twice.",
                 "Flat networks win the game automatically.", extra=0.4)

        self.say("But not every network lies flat.", hold=False)
        self.play(*[FadeOut(m) for m in self.mobjects if m is not self._cap],
                  run_time=0.7)
        self.pad()

        ppos = pet_layout()
        pedges_g, pnodes_g, pe_ms, _ = make_graph(ppos, PET_EDGES)
        self.kick("2 · maps already know the answer")
        self.say("This is the Petersen network — 10 junctions, 15 roads.",
                 "Draw it on paper and roads always cross.", hold=False)
        self.play(Create(pedges_g), FadeIn(pnodes_g), run_time=1.4)
        # mark the 5 crossings of the inner pentagram
        inner = [(5 + i, 5 + ((i + 2) % 5)) for i in range(5)]

        def x_point(e1, e2):
            p1, p2 = ppos[e1[0]], ppos[e1[1]]
            p3, p4 = ppos[e2[0]], ppos[e2[1]]
            a1 = np.array([p2[0] - p1[0], p2[1] - p1[1]])
            a2 = np.array([p4[0] - p3[0], p4[1] - p3[1]])
            M = np.array([a1, -a2]).T
            if abs(np.linalg.det(M)) < 1e-9:
                return None
            t, s = np.linalg.solve(M, np.array([p3[0] - p1[0], p3[1] - p1[1]]))
            if 0.05 < t < 0.95 and 0.05 < s < 0.95:
                return p1 + t * (p2 - p1)
            return None

        marks = VGroup()
        for i in range(5):
            for j in range(i + 1, 5):
                if set(inner[i]) & set(inner[j]):
                    continue
                p = x_point(inner[i], inner[j])
                if p is not None:
                    marks.add(cross_mark(p, s=0.12, w=5))
        self.play(LaggedStart(*[FadeIn(m, scale=0.5) for m in marks],
                              lag_ratio=0.1), run_time=1.2)
        self.pad()
        self.say("That is a theorem, not a lack of skill: NO flat drawing",
                 "of it exists. So: no regions, no free answer.", extra=0.3)
        self.say("Does the game still have a solution here?", extra=0.5)
        self.clear_all()


# ======================================================================
# 3 · THE CONJECTURE (bridges + the announcement)
# ======================================================================
class C03Conjecture(CDC):
    def construct(self):
        self.kick("3 · fifty years of stuck")

        # two islands and a bridge
        cL, cR = np.array([-3.1, 0.6, 0]), np.array([3.1, 0.6, 0])
        ringL = [cL + 1.15 * np.array([np.cos(a), np.sin(a), 0])
                 for a in np.linspace(0, TAU, 6, endpoint=False)]
        ringR = [cR + 1.15 * np.array([np.cos(a), np.sin(a), 0])
                 for a in np.linspace(PI, PI + TAU, 6, endpoint=False)]
        edgesL = VGroup(*[edge_line(ringL[i], ringL[(i + 1) % 6]) for i in range(6)])
        edgesR = VGroup(*[edge_line(ringR[i], ringR[(i + 1) % 6]) for i in range(6)])
        bridge = edge_line(ringL[0], ringR[0], color="#8fa0bd", w=7)
        nodes = VGroup(*[node_dot(p) for p in ringL + ringR])
        blabel = Text("a bridge", font=FONT, font_size=24, color=MUTED)
        blabel.next_to(bridge, UP, buff=0.15)

        self.say("One thing genuinely kills the game: a BRIDGE —",
                 "the only road connecting two parts of a network.",
                 hold=False)
        self.play(Create(edgesL), Create(edgesR), FadeIn(nodes), run_time=1.1)
        self.play(Create(bridge), FadeIn(blabel), run_time=0.8)
        self.pad()

        self.say("A round trip that crosses a bridge is stranded:",
                 "the only road home is the one it already used.", hold=False)
        w = Dot(radius=0.08, color=WHITE, z_index=6).move_to(ringL[0])
        path = VMobject().set_points_as_corners(
            [ringL[0], ringR[0], ringR[1], ringR[2]])
        trail = VMobject(stroke_color="#4ea1ff", stroke_width=6.5,
                         cap_style=CapStyleType.ROUND,
                         joint_type=LineJointType.ROUND)
        trail.set_points_as_corners([ringL[0], ringR[0], ringR[1], ringR[2]])
        self.play(FadeIn(w, run_time=0.15))
        self.play(MoveAlongPath(w, path), Create(trail), run_time=1.8,
                  rate_func=linear)
        q = Text("?", font=FONT, font_size=44, color=BAD, weight=BOLD)
        q.next_to(w, UR, buff=0.1)
        xm = cross_mark(bridge.get_center(), s=0.17)
        self.play(FadeIn(q, scale=0.6), FadeIn(xm, scale=0.6), run_time=0.6)
        self.pad()

        self.say("So networks with bridges are out — fair enough.",
                 "The conjecture says bridges are the ONLY obstacle.",
                 extra=0.3)

        self.play(*[FadeOut(m) for m in self.mobjects if m is not self._cap],
                  run_time=0.6)
        self.kick("3 · fifty years of stuck")

        card = VGroup(
            Text("THE CYCLE DOUBLE COVER CONJECTURE", font=FONT, font_size=33,
                 weight=BOLD, color=ACCENT),
            Text("Szekeres 1973  ·  Seymour 1979", font=FONT, font_size=24,
                 color=MUTED),
            Text("Every bridgeless network can be walked in round trips",
                 font=FONT, font_size=29, color=TEXT_C),
            Text("so that every road is used exactly twice.",
                 font=FONT, font_size=29, color=TEXT_C),
        ).arrange(DOWN, buff=0.3).move_to([0, 0.9, 0])
        for m in card:
            fit(m)
        box = SurroundingRectangle(card, corner_radius=0.16, buff=0.42,
                                   stroke_color=FAINT, stroke_width=2)
        self.say("Here it is — one of graph theory's most famous open problems.",
                 hold=False)
        self.play(FadeIn(card, shift=UP * 0.2), Create(box), run_time=1.2)
        self.pad(extra=1.2)

        self.say("For fifty years it refused to fall. Then —", extra=0.2)
        news = VGroup(
            Text("July 10, 2026", font=FONT, font_size=27, color=MUTED),
            Text("A PROOF IS ANNOUNCED", font=FONT, font_size=40, weight=BOLD,
                 color=TEXT_C),
            Text("reportedly found by an AI model — now under expert review",
                 font=FONT, font_size=24, color=MUTED),
        ).arrange(DOWN, buff=0.26).move_to([0, -1.55, 0])
        for m in news:
            fit(m)
        self.play(FadeIn(news, shift=UP * 0.25), run_time=1.0)
        self.wait(2.2)
        self.say("This video walks through the announced proof's central idea —",
                 "and runs its machinery, for real, on the Petersen network.",
                 extra=0.4)
        self.clear_all()


# ======================================================================
# 4 · THE EASY HALF, AND THE SNARK
# ======================================================================
class C04Snark(CDC):
    def construct(self):
        self.kick("4 · the easy half — and the snark")

        # --- reduce to 3-way junctions -------------------------------------
        self.say("First, a classic simplification: a busy junction can be",
                 "split into 3-way junctions without changing the game.",
                 hold=False)
        c1 = np.array([-3.4, 0.7, 0])
        arms1 = [c1 + 1.25 * np.array([np.cos(a), np.sin(a), 0])
                 for a in np.linspace(PI / 2, PI / 2 + TAU, 5, endpoint=False)]
        star = VGroup(*[edge_line(c1, a) for a in arms1],
                      *[node_dot(a, r=0.07) for a in arms1], node_dot(c1))
        spineL = np.array([1.6, 0.7, 0])
        spine = [spineL + RIGHT * 1.1 * i for i in range(3)]
        tips = [spine[0] + UL * 0.95, spine[0] + DL * 0.95,
                spine[1] + UP * 1.05,
                spine[2] + UR * 0.95, spine[2] + DR * 0.95]
        cat = VGroup(
            edge_line(spine[0], spine[1]), edge_line(spine[1], spine[2]),
            *[edge_line(spine[0], tips[0]), edge_line(spine[0], tips[1]),
              edge_line(spine[1], tips[2]), edge_line(spine[2], tips[3]),
              edge_line(spine[2], tips[4])],
            *[node_dot(p, r=0.07) for p in tips],
            *[node_dot(p) for p in spine],
        )
        arrow = Arrow(c1 + RIGHT * 1.7, spineL + LEFT * 1.3, color=MUTED,
                      stroke_width=5, buff=0.1)
        self.play(Create(star), run_time=0.9)
        self.play(GrowArrow(arrow), Create(cat), run_time=1.1)
        self.pad()
        self.say("So we only need to win the game on networks where",
                 "every junction is a 3-way. Those are the battleground.",
                 extra=0.2)
        self.play(*[FadeOut(m) for m in self.mobjects if m is not self._cap],
                  run_time=0.5)

        # --- 3-edge-coloring => CDC on the cube -----------------------------
        self.kick("4 · the easy half — and the snark")
        pos = cube_layout(cx=0, cy=0.5)
        edges_g, nodes_g, e_ms, _ = make_graph(pos, CUBE_EDGES)
        self.say("For many 3-way networks there is a lovely shortcut.",
                 "Try painting every road red, green or blue…", hold=False)
        self.play(Create(edges_g), FadeIn(nodes_g), run_time=1.0)
        AXIS_COL = {0: "#ff5d5d", 1: "#3ddc84", 2: "#4ea1ff"}
        paint = [e_ms[e].animate.set_stroke(color=AXIS_COL[CUBE_AXIS[e]], width=6.5)
                 for e in CUBE_EDGES]
        self.play(LaggedStart(*paint, lag_ratio=0.06), run_time=1.8)
        self.pad()
        self.say("…so that all three colors meet at every junction.",
                 hold=False)
        ring = Circle(radius=0.42, color=ACCENT, stroke_width=4).move_to(pos[5])
        self.play(Create(ring), run_time=0.5)
        self.play(ring.animate.move_to(pos[0]), run_time=0.8)
        self.play(ring.animate.move_to(pos[7]), run_time=0.8)
        self.play(FadeOut(ring), run_time=0.3)
        self.pad()

        self.say("Suppose you succeed. Keep only RED and BLUE: every junction",
                 "touches exactly one of each — so these roads chain into loops.",
                 hold=False)
        dim = [e_ms[e].animate.set_stroke(opacity=0.13)
               for e in CUBE_EDGES if CUBE_AXIS[e] == 1]
        self.play(*dim, run_time=0.8)
        # the two red-blue loops (top face + bottom face in axis terms)
        rb_cycles = DATA["cube_unions"]["(0, 2)"]
        loops = VGroup(*[
            face_loop(pos, cyc, ACCENT, inward=(set(cyc) != {0, 1, 3, 2}),
                      w=6.0, off=0.14)
            for cyc in rb_cycles
        ])
        self.trace_loop(loops[0], run_time=1.6)
        self.trace_loop(loops[1], run_time=1.2, walker=False)
        self.pad()
        self.say("Every color-duo makes loops: red+blue, red+green, green+blue.",
                 "A red road sits in exactly two duos — so it lands in exactly",
                 "two loops. Paint 3 colors and the game is won.", hold=False)
        undim = [e_ms[e].animate.set_stroke(opacity=1.0)
                 for e in CUBE_EDGES if CUBE_AXIS[e] == 1]
        self.play(*undim, run_time=0.7)
        self.pad()

        self.play(*[FadeOut(m) for m in self.mobjects if m is not self._cap],
                  run_time=0.6)
        self.kick("4 · the easy half — and the snark")

        # --- Petersen refuses ------------------------------------------------
        ppos = pet_layout()
        pedges_g, pnodes_g, pe_ms, _ = make_graph(ppos, PET_EDGES)
        self.say("Back to the Petersen network. Paint its five spokes green…",
                 hold=False)
        self.play(Create(pedges_g), FadeIn(pnodes_g), run_time=1.1)
        spokes = [(i, i + 5) for i in range(5)]
        self.play(*[pe_ms[e].animate.set_stroke(color="#3ddc84", width=6.5)
                    for e in spokes], run_time=1.0)
        self.pad()
        self.say("…then the outer ring may use only red and blue,",
                 "alternating: red, blue, red, blue…", hold=False)
        outer = [(i, (i + 1) % 5) for i in range(5)]
        seq = ["#ff5d5d", "#4ea1ff", "#ff5d5d", "#4ea1ff"]
        for e, c in zip(outer[:4], seq):
            self.play(pe_ms[e].animate.set_stroke(color=c, width=6.5),
                      run_time=0.45)
        self.pad()
        self.say("…but the ring has FIVE roads. The last one touches red",
                 "on one side and blue on the other. Odd rings break it.",
                 hold=False)
        last = pe_ms[outer[4]]
        self.play(last.animate.set_stroke(color="#e8eaf0", width=6.5), run_time=0.4)
        xm = cross_mark(last.get_center() + 0.28 * normalize(
            last.get_center() - np.array([0, 0.5, 0])), s=0.16)
        self.play(Wiggle(last), FadeIn(xm, scale=0.5), run_time=0.9)
        self.pad()
        self.say("No clever reshuffle escapes: every one of the",
                 "millions of paint jobs fails — all were checked.", extra=0.2)
        self.say("Networks like this are called SNARKS. They are exactly",
                 "where the conjecture is hard: crack them, crack everything.",
                 hold=False)
        snark = Text("a  SNARK", font=FONT, font_size=30, weight=BOLD,
                     color=ACCENT).to_corner(UR, buff=0.5)
        self.play(FadeIn(snark, shift=LEFT * 0.2), run_time=0.6)
        self.pad(extra=0.4)
        self.clear_all()


# ======================================================================
# 5 · EIGHT CODES THAT CANCEL
# ======================================================================
class C05Mixes(CDC):
    def construct(self):
        self.kick("5 · eight codes that cancel")

        codes = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1),
                 (1, 1, 0), (1, 0, 1), (0, 1, 1), (1, 1, 1)]
        chips = VGroup(*[chip(c, w=0.86, label=CODE_NAME[c]) for c in codes])
        chips.arrange(RIGHT, buff=0.42).move_to([0, 2.35, 0])
        fit(chips, 12.6)

        self.say("Now for the fifty-year-old tool the new proof stands on.",
                 "Meet eight CODES: three switches — red, green, blue.",
                 hold=False)
        self.play(LaggedStart(*[FadeIn(c, shift=DOWN * 0.2) for c in chips],
                              lag_ratio=0.08), run_time=1.8)
        self.pad()
        self.say("A code's color is just its lit switches, mixed —",
                 "red+green glows amber; all three make white; none: OFF.",
                 extra=0.2)

        self.say("Codes COMBINE BY TOGGLING: hit a switch twice,",
                 "it's off again. So red ⊕ green = amber…", hold=False)
        a1 = chip((1, 0, 0), w=0.95).move_to([-2.4, 0.35, 0])
        plus = Text("⊕", font=FONT, font_size=44, color=TEXT_C).move_to([-1.2, 0.35, 0])
        a2 = chip((0, 1, 0), w=0.95).move_to([0, 0.35, 0])
        eq = Text("=", font=FONT, font_size=44, color=TEXT_C).move_to([1.2, 0.35, 0])
        a3 = chip((1, 1, 0), w=0.95).move_to([2.5, 0.35, 0])
        self.play(FadeIn(a1), FadeIn(plus), FadeIn(a2), run_time=0.7)
        self.play(FadeIn(eq), FadeIn(a3, scale=0.6), run_time=0.7)
        self.pad()
        self.say("…and anything ⊕ itself = OFF. Toggling erases in pairs —",
                 "remember that; it is the engine of the whole proof.",
                 hold=False)
        b1 = chip((1, 0, 1), w=0.95).move_to([-2.4, -1.15, 0])
        plus2 = Text("⊕", font=FONT, font_size=44, color=TEXT_C).move_to([-1.2, -1.15, 0])
        b2 = chip((1, 0, 1), w=0.95).move_to([0, -1.15, 0])
        eq2 = Text("=", font=FONT, font_size=44, color=TEXT_C).move_to([1.2, -1.15, 0])
        b3 = chip((0, 0, 0), w=0.95).move_to([2.5, -1.15, 0])
        self.play(FadeIn(b1), FadeIn(plus2), FadeIn(b2), FadeIn(eq2), run_time=0.7)
        self.play(FadeIn(b3, scale=0.6), run_time=0.5)
        self.pad(extra=0.3)

        self.play(*[FadeOut(m) for m in self.mobjects if m is not self._cap],
                  run_time=0.6)
        self.kick("5 · eight codes that cancel")

        # Jaeger stamping on Petersen
        ppos = pet_layout(cy=0.35)
        pedges_g, pnodes_g, pe_ms, _ = make_graph(ppos, PET_EDGES)
        self.say("The 8-FLOW THEOREM (Jaeger, 1976): on every bridgeless",
                 "network you can stamp a non-OFF code on each road…",
                 hold=False)
        self.play(Create(pedges_g), FadeIn(pnodes_g), run_time=1.0)
        stamps = VGroup()
        for e in PET_EDGES:
            s = chip(PET_FLOW[e], w=0.4, show_dots=False)
            s.move_to(stamp_point(ppos, e))
            stamps.add(s)
        self.play(LaggedStart(*[FadeIn(s, scale=0.5) for s in stamps],
                              lag_ratio=0.05), run_time=1.9)
        self.pad()

        self.say("…so that at EVERY junction the three codes toggle to OFF.",
                 hold=False)
        v = 0
        inc = [e for e in PET_EDGES if v in e]
        ring = Circle(radius=0.42, color=ACCENT, stroke_width=4).move_to(ppos[v])
        self.play(Create(ring), run_time=0.5)
        minis = VGroup(*[chip(PET_FLOW[e], w=0.8) for e in inc])
        minis.arrange(RIGHT, buff=0.35).move_to([4.55, 2.5, 0])
        fit(minis, 3.6)
        panel = SurroundingRectangle(minis, corner_radius=0.12, buff=0.22,
                                     stroke_color=FAINT, stroke_width=1.8)
        self.play(FadeIn(panel), *[FadeIn(m, scale=0.6) for m in minis],
                  run_time=0.8)
        offc = chip((0, 0, 0), w=0.8, label="off").move_to(minis.get_center() + DOWN * 1.0)
        self.play(*[m.animate.move_to(offc[0].get_center()).set_opacity(0.0)
                    for m in minis.copy()],
                  FadeIn(offc, scale=0.7), run_time=1.0)
        self.pad()
        self.say("Such cancelling stamps exist on every bridgeless network —",
                 "snarks included. Proven fifty years ago.", extra=0.2)
        self.say("Stamps are not loops... yet. Here comes the new idea.",
                 extra=0.4)
        self.clear_all()


# ======================================================================
# 6 · THE MOVE: WEAR TWO COLORS
# ======================================================================
class C06TwoColors(CDC):
    def construct(self):
        self.kick("6 · the move — wear two colors")

        pos = cube_layout(cx=-2.2, cy=0.5)
        edges_g, nodes_g, e_ms, _ = make_graph(pos, CUBE_EDGES)

        self.say("The proof's central move. Forget one label per road:",
                 "give every road a PAIR of colors — two painted lanes.",
                 hold=False)
        self.play(Create(edges_g), FadeIn(nodes_g), run_time=1.0)
        A, B, Zc = (1, 0, 0), (0, 1, 0), (0, 0, 0)
        pair_by_axis = {0: (Zc, A), 1: (Zc, B), 2: (A, B)}
        book = LaneBook()
        lanes = VGroup()
        for e in CUBE_EDGES:
            lanes.add(pair_lanes(pos, e, pair_by_axis[CUBE_AXIS[e]], book))
        self.play(edges_g.animate.set_stroke(opacity=0.28), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(l) for l in lanes], lag_ratio=0.06),
                  run_time=1.8)
        self.pad()

        self.say("One LAW: around any junction, every color that appears",
                 "must appear exactly TWICE. Count them here:", hold=False)
        v = 5
        ring = Circle(radius=0.4, color=ACCENT, stroke_width=4).move_to(pos[v])
        rows = VGroup()
        for code in (Zc, A, B):
            rows.add(VGroup(
                swatch(code, r=0.11),
                Text("× 2", font=FONT, font_size=30, color=TEXT_C),
            ).arrange(RIGHT, buff=0.22))
        rows.arrange(DOWN, buff=0.3, aligned_edge=LEFT).move_to([3.4, 1.6, 0])
        head = Text("at this junction:", font=FONT, font_size=25, color=MUTED)
        head.next_to(rows, UP, buff=0.3, aligned_edge=LEFT)
        self.play(Create(ring), FadeIn(head), run_time=0.6)
        for r in rows:
            self.play(FadeIn(r, shift=LEFT * 0.2), run_time=0.45)
        chk = check_mark(rows.get_right() + RIGHT * 0.7)
        self.play(FadeIn(chk, scale=0.6), run_time=0.4)
        self.pad()

        self.say("Why is that law magic? Pick ONE color — say green —",
                 "and keep only its lanes.", hold=False)
        keepB = VGroup()
        fadeanims = []
        for lg, e in zip(lanes, CUBE_EDGES):
            for ln, code in zip(lg, sorted(pair_by_axis[CUBE_AXIS[e]])):
                if code == B:
                    keepB.add(ln)
                else:
                    fadeanims.append(ln.animate.set_stroke(opacity=0.1))
        self.play(*fadeanims, FadeOut(ring), FadeOut(head), FadeOut(rows),
                  FadeOut(chk), run_time=0.9)
        self.pad()

        self.say("Every junction meets green twice or not at all — so green",
                 "lanes have no loose ends. They CHAIN INTO CLOSED LOOPS.",
                 hold=False)
        b_cycles = DATA["cube_Ms"][str(B)]
        loopsB = VGroup(*[
            loop_lane_poly(pos, cyc,
                           {frozenset((cyc[i], cyc[(i + 1) % len(cyc)])):
                            book.side(cyc[i], cyc[(i + 1) % len(cyc)], B)
                            for i in range(len(cyc))},
                           CODE_COLOR[B], w=7.0)
            for cyc in b_cycles
        ])
        self.play(*[Create(l) for l in loopsB], run_time=1.8)
        self.play(FadeOut(loopsB), run_time=0.4)
        self.pad()

        self.say("That works for EVERY color at once. And each road wears",
                 "two colors — so it lies in exactly two loops. Double cover!",
                 hold=False)
        restore = []
        for lg in lanes:
            for ln in lg:
                restore.append(ln.animate.set_stroke(opacity=1.0))
        self.play(*restore, run_time=0.7)
        self.counter("roads walked twice", 12)
        passes = defaultdict(int)
        done = 0
        for code in (Zc, A, B):
            cycs = DATA["cube_Ms"][str(code)]
            lps = VGroup(*[
                loop_lane_poly(pos, cyc,
                               {frozenset((cyc[i], cyc[(i + 1) % len(cyc)])):
                                book.side(cyc[i], cyc[(i + 1) % len(cyc)], code)
                                for i in range(len(cyc))},
                               CODE_COLOR[code], w=7.0)
                for cyc in cycs
            ])
            self.play(*[Create(l) for l in lps], run_time=1.0)
            for cyc in cycs:
                for i in range(len(cyc)):
                    passes[frozenset((cyc[i], cyc[(i + 1) % len(cyc)]))] += 1
            nd = sum(1 for v_ in passes.values() if v_ == 2)
            if nd != done:
                done = nd
                self.set_count(done, rt=0.3)
        self.pad()

        self.say("So the fifty-year problem shrinks to one question:",
                 "does a LEGAL two-color dressing always exist?", extra=0.6)
        self.clear_all()


# ======================================================================
# 7 · THE JUNCTION TRIANGLE
# ======================================================================
class C07Triangle(CDC):
    def construct(self):
        self.kick("7 · the junction triangle")

        # real data at Petersen vertex 0
        v = 0
        E_sorted = sorted([e for e in PET_EDGES if v in e],
                          key=lambda e: PET_EDGES.index(e))
        ea, eb, ec = E_sorted
        x, y = PET_FLOW[ea], PET_FLOW[eb]
        t = PET_BASE[v]
        c1, c2, c3 = t, xor(t, x), xor(xor(t, x), y)

        # left: the junction with its three stamped roads
        C = np.array([-3.5, 0.4, 0])
        angs = [PI / 2, PI / 2 + TAU / 3, PI / 2 + 2 * TAU / 3]
        arms = [C + 1.55 * np.array([np.cos(a), np.sin(a), 0]) for a in angs]
        roads = VGroup(*[edge_line(C, A, w=6) for A in arms])
        jnode = node_dot(C, r=0.1)
        stamps = VGroup(*[
            chip(f, w=0.52).move_to(C + (A - C) * 0.62 +
                                    normalize(rotate_vector(A - C, PI / 2)) * 0.34)
            for A, f in zip(arms, (x, y, xor(x, y)))
        ])
        names = VGroup(*[
            Text(s, font=FONT, font_size=24, color=MUTED).move_to(
                C + (A - C) * 1.18)
            for A, s in zip(arms, ("road x", "road y", "road z"))
        ])

        self.say("Here is the announced proof's recipe, one junction at a",
                 "time. A junction's three roads carry cancelling stamps:",
                 hold=False)
        self.play(Create(roads), FadeIn(jnode), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(s, scale=0.6) for s in stamps],
                              lag_ratio=0.2),
                  LaggedStart(*[FadeIn(n) for n in names], lag_ratio=0.2),
                  run_time=1.2)
        self.pad()
        self.say("x ⊕ y ⊕ z = OFF — that is what Jaeger guarantees.",
                 extra=0.2)

        # right: color space walk
        Tc = np.array([3.3, 0.4, 0])
        tri = [Tc + 1.5 * np.array([np.cos(a), np.sin(a), 0]) for a in angs]
        corner_chips = VGroup(*[chip(c, w=0.62).move_to(p)
                                for c, p in zip((c1, c2, c3), tri)])
        clabels = VGroup(
            Text("t", font=FONT, font_size=26, color=MUTED).next_to(
                corner_chips[0], UP, buff=0.12),
            Text("t⊕x", font=FONT, font_size=26, color=MUTED).next_to(
                corner_chips[1], DL, buff=0.12),
            Text("t⊕x⊕y", font=FONT, font_size=26, color=MUTED).next_to(
                corner_chips[2], DR, buff=0.12),
        )
        self.say("Now take a walk through COLOR SPACE. Start at any base",
                 "color t. Toggle by x. Then by y. Then by z…", hold=False)
        self.play(FadeIn(corner_chips[0], scale=0.6), FadeIn(clabels[0]),
                  run_time=0.6)
        s1 = Line(tri[0], tri[1], stroke_color=CODE_COLOR[c1], stroke_width=6,
                  cap_style=CapStyleType.ROUND)
        s1.set_stroke(color=[CODE_COLOR[c1], CODE_COLOR[c2]])
        self.play(Create(s1), FadeIn(corner_chips[1], scale=0.6),
                  FadeIn(clabels[1]), run_time=0.8)
        s2 = Line(tri[1], tri[2], stroke_width=6, cap_style=CapStyleType.ROUND)
        s2.set_stroke(color=[CODE_COLOR[c2], CODE_COLOR[c3]])
        self.play(Create(s2), FadeIn(corner_chips[2], scale=0.6),
                  FadeIn(clabels[2]), run_time=0.8)
        self.pad()
        self.say("…and z brings you HOME — because the three stamps cancel.",
                 "Three hops, three stops: a closed TRIANGLE of colors.",
                 hold=False)
        s3 = Line(tri[2], tri[0], stroke_width=6, cap_style=CapStyleType.ROUND)
        s3.set_stroke(color=[CODE_COLOR[c3], CODE_COLOR[c1]])
        self.play(Create(s3), run_time=0.8)
        self.play(Indicate(VGroup(*corner_chips), scale_factor=1.06), run_time=0.8)
        self.pad()

        self.say("Dress each road in the hop its stamp powered:",
                 "road x wears {t, t⊕x} — the side it walked. And so on.",
                 hold=False)
        book = LaneBook()
        pos_local = {9: C, 0: arms[0], 1: arms[1], 2: arms[2]}
        pairs_local = [(c1, c2), (c2, c3), (c3, c1)]
        lane_grps = VGroup()
        for i, pr in enumerate(pairs_local):
            lg = pair_lanes(pos_local, (9, i), pr, book, w=6, trim=0.1)
            lane_grps.add(lg)
        sides = [s1, s2, s3]
        for i in range(3):
            self.play(sides[i].copy().animate.set_opacity(0.0).move_to(
                (C + arms[i]) / 2), FadeIn(lane_grps[i]), run_time=0.75)
        self.pad()

        self.say("Check the law at this junction: each corner color touches",
                 "exactly two triangle sides — every color here appears twice.",
                 hold=False)
        rows = VGroup(*[
            VGroup(swatch(c, r=0.1),
                   Text("× 2", font=FONT, font_size=27, color=TEXT_C)).arrange(
                RIGHT, buff=0.2)
            for c in (c1, c2, c3)
        ]).arrange(DOWN, buff=0.2, aligned_edge=LEFT).move_to([0.0, -1.72, 0])
        chk = check_mark(rows.get_right() + RIGHT * 0.6)
        self.play(FadeIn(rows, shift=UP * 0.15), FadeIn(chk, scale=0.6),
                  run_time=0.9)
        self.pad()

        self.say("The law holds BY DESIGN — no luck involved. Every junction",
                 "can dress its own three roads this way.", extra=0.2)
        self.say("One catch: a road has TWO ends. Both ends must",
                 "hand it the SAME pair of colors…", extra=0.5)
        self.clear_all()


# ======================================================================
# 8 · THE HANDSHAKE AND THE PARITY MIRACLE
# ======================================================================
class C08Handshake(CDC):
    def construct(self):
        self.kick("8 · the handshake")

        # two junction triangles negotiating over a shared road
        L, R = np.array([-2.9, 0.6, 0]), np.array([2.9, 0.6, 0])
        road = edge_line(L, R, w=7)
        nL, nR = node_dot(L, r=0.1), node_dot(R, r=0.1)
        labL = Text("junction u", font=FONT, font_size=24, color=MUTED)
        labL.next_to(L, DOWN, buff=0.3)
        labR = Text("junction v", font=FONT, font_size=24, color=MUTED)
        labR.next_to(R, DOWN, buff=0.3)
        # little side roads
        sideL = VGroup(*[edge_line(L, L + 1.1 * np.array(
            [np.cos(a), np.sin(a), 0]), w=4, opacity=0.5)
            for a in (PI * 0.75, PI * 1.25)])
        sideR = VGroup(*[edge_line(R, R + 1.1 * np.array(
            [np.cos(a), np.sin(a), 0]), w=4, opacity=0.5)
            for a in (PI * 0.25, -PI * 0.25)])

        self.say("Junction u dresses this road with a pair. Junction v,",
                 "at the other end, dresses it too. They must MATCH.",
                 hold=False)
        self.play(Create(road), FadeIn(nL), FadeIn(nR), FadeIn(labL),
                  FadeIn(labR), Create(sideL), Create(sideR), run_time=1.1)
        pA = VGroup(swatch((1, 0, 0)), swatch((0, 0, 1))).arrange(RIGHT, buff=0.14)
        pA.next_to(L, UP, buff=0.45).shift(RIGHT * 0.8)
        pB = VGroup(swatch((1, 0, 0)), swatch((0, 1, 1))).arrange(RIGHT, buff=0.14)
        pB.next_to(R, UP, buff=0.45).shift(LEFT * 0.8)
        qm = Text("≠ ?", font=FONT, font_size=34, color=BAD, weight=BOLD)
        qm.move_to((pA.get_center() + pB.get_center()) / 2)
        self.play(FadeIn(pA, scale=0.6), FadeIn(pB, scale=0.6), FadeIn(qm),
                  run_time=0.9)
        self.pad()

        self.say("Each junction has freedom — its base color t can be",
                 "re-chosen. A handshake: shift one t until the pairs agree.",
                 hold=False)
        pB2 = VGroup(swatch((1, 0, 0)), swatch((0, 0, 1))).arrange(RIGHT, buff=0.14)
        pB2.move_to(pB)
        agree = check_mark(qm.get_center(), s=0.15)
        self.play(Transform(pB, pB2), FadeOut(qm), run_time=0.8)
        self.play(FadeIn(agree, scale=0.6), run_time=0.4)
        self.pad()

        self.play(*[FadeOut(m) for m in self.mobjects if m is not self._cap],
                  run_time=0.6)
        self.kick("8 · the handshake")

        ppos = pet_layout(cy=0.35)
        pedges_g, pnodes_g, pe_ms, _ = make_graph(ppos, PET_EDGES)
        tdots = VGroup(*[swatch(PET_BASE[v], r=0.13).move_to(ppos[v])
                         for v in range(10)])
        self.say("But on the whole network every junction shakes hands with",
                 "three neighbors: 10 base colors, 15 roads — a web of demands.",
                 hold=False)
        self.play(Create(pedges_g), FadeIn(pnodes_g), run_time=1.0)
        self.play(LaggedStart(*[FadeIn(d, scale=0.5) for d in tdots],
                              lag_ratio=0.07), run_time=1.1)
        self.pad()
        self.say("Webs of demands can be impossible — unless every potential",
                 "contradiction secretly cancels itself out.", extra=0.2)

        self.say("The paper's PARITY LEMMA: chase any closed chain of demands.",
                 "Every junction on it is pulled by its two chain-roads…",
                 hold=False)
        chain = [0, 1, 2, 3, 4]
        chain_edges = [(chain[i], chain[(i + 1) % 5]) for i in range(5)]
        glow = VGroup(*[
            Line(ppos[u], ppos[v], stroke_color=ACCENT, stroke_width=9,
                 stroke_opacity=0.85, cap_style=CapStyleType.ROUND)
            for u, v in chain_edges
        ])
        self.play(Create(glow), run_time=1.2)
        tokens = VGroup()
        for u, v in chain_edges:
            P, Q = ppos[u], ppos[v]
            tokens.add(Dot(radius=0.085, color=ACCENT).move_to(P + (Q - P) * 0.22))
            tokens.add(Dot(radius=0.085, color=ACCENT).move_to(P + (Q - P) * 0.78))
        self.play(LaggedStart(*[FadeIn(tk, scale=0.4) for tk in tokens],
                              lag_ratio=0.06), run_time=1.1)
        self.pad()

        self.say("…so along the chain, every pull lands TWICE — once from",
                 "each side. And in toggle-arithmetic, twice = OFF.", hold=False)
        merges = []
        for i, vtx in enumerate(chain):
            a = tokens[(2 * i - 1) % 10]
            b = tokens[2 * i]
            merges.append(AnimationGroup(
                a.animate.move_to(ppos[vtx]), b.animate.move_to(ppos[vtx])))
        self.play(LaggedStart(*merges, lag_ratio=0.1), run_time=1.4)
        pops = []
        for i, vtx in enumerate(chain):
            a = tokens[(2 * i - 1) % 10]
            b = tokens[2 * i]
            pops.append(AnimationGroup(FadeOut(a, scale=2.2), FadeOut(b, scale=0.3)))
        self.play(LaggedStart(*pops, lag_ratio=0.12), run_time=1.3)
        self.pad()

        self.say("Every would-be contradiction annihilates itself. The web of",
                 "handshakes ALWAYS has a solution — that is the paper's Lemma 2.2.",
                 extra=0.3)
        self.say("The number TWO — the whole point of the game —",
                 "is exactly what rescues the proof. Poetic justice.",
                 extra=0.5)
        self.clear_all()


# ======================================================================
# 9 · THE MACHINE RUNS
# ======================================================================
class C09Machine(CDC):
    def construct(self):
        self.kick("9 · the machine runs")

        ppos = pet_layout(cy=0.35)
        pedges_g, pnodes_g, pe_ms, _ = make_graph(ppos, PET_EDGES)

        self.say("Time to run the whole machine — for real — on the",
                 "unpaintable snark. Everything you'll see was computed.",
                 hold=False)
        self.play(Create(pedges_g), FadeIn(pnodes_g), run_time=1.2)
        self.pad()

        self.say("Step 1 — cancelling stamps on all fifteen roads",
                 "(they exist: 1976).", hold=False)
        stamps = VGroup()
        for e in PET_EDGES:
            s = chip(PET_FLOW[e], w=0.36, show_dots=False)
            s.move_to(stamp_point(ppos, e))
            stamps.add(s)
        self.play(LaggedStart(*[FadeIn(s, scale=0.5) for s in stamps],
                              lag_ratio=0.04), run_time=1.6)
        self.pad()

        self.say("Step 2 — every junction builds its color triangle;",
                 "the parity lemma settles all fifteen handshakes at once.",
                 hold=False)
        tris = VGroup()
        for v in range(10):
            tri = RegularPolygon(3, radius=0.36, stroke_color=ACCENT,
                                 stroke_width=3.5).move_to(ppos[v])
            tris.add(tri)
        self.play(LaggedStart(*[FadeIn(t, scale=0.4) for t in tris],
                              lag_ratio=0.06), run_time=1.2)
        book = LaneBook()
        lane_grps = VGroup()
        for e in PET_EDGES:
            lane_grps.add(pair_lanes(ppos, e, PET_PAIRS[e], book, w=5.2))
        self.play(FadeOut(tris), FadeOut(stamps),
                  pedges_g.animate.set_stroke(opacity=0.25), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(lg) for lg in lane_grps],
                              lag_ratio=0.05), run_time=2.0)
        self.pad()

        self.say("Every road now wears its two colors. Spot-check the law",
                 "at a junction: each color present appears exactly twice.",
                 hold=False)
        v = 0
        ring = Circle(radius=0.45, color=ACCENT, stroke_width=4).move_to(ppos[v])
        colors_at_v = []
        for e in PET_EDGES:
            if v in e:
                colors_at_v += list(PET_PAIRS[e])
        uniq = sorted(set(colors_at_v))
        rows = VGroup(*[
            VGroup(swatch(c, r=0.1),
                   Text("× 2", font=FONT, font_size=26, color=TEXT_C)).arrange(
                RIGHT, buff=0.2)
            for c in uniq
        ]).arrange(DOWN, buff=0.22, aligned_edge=LEFT).move_to([5.0, 1.8, 0])
        chk = check_mark(rows.get_bottom() + DOWN * 0.45)
        self.play(Create(ring), FadeIn(rows, shift=LEFT * 0.2), run_time=0.9)
        self.play(FadeIn(chk, scale=0.6), run_time=0.4)
        self.pad()
        self.play(FadeOut(ring), FadeOut(rows), FadeOut(chk), run_time=0.4)

        self.say("Step 3 — pull the loops out, color by color.", hold=False)
        self.counter("roads walked twice", 15)
        passes = defaultdict(int)
        done = 0
        order = sorted(PET_MS.keys())
        first = True
        for code_s in order:
            code = tuple(code_s)
            cycles = PET_MS[code_s]
            lps = class_loops(ppos, code, cycles, book, w=6.5)
            for cyc, lp in zip(cycles, lps):
                self.trace_loop(lp, run_time=2.0 if first else 1.3,
                                walker=first)
                first = False
                for i in range(len(cyc)):
                    passes[frozenset((cyc[i], cyc[(i + 1) % len(cyc)]))] += 1
                nd = sum(1 for k in passes.values() if k == 2)
                if nd != done:
                    done = nd
                    self.set_count(done, rt=0.3)
        self.pad()

        self.say("Five round trips. Every road walked exactly twice.",
                 "The snark — where 3-painting failed — is double-covered.",
                 extra=0.4)
        self.say("And nothing here needed flat paper: only cancelling stamps,",
                 "which every bridgeless network has. That is the proof.",
                 extra=0.6)
        self.clear_all()


# ======================================================================
# 10 · EPILOGUE
# ======================================================================
class C10End(CDC):
    def construct(self):
        self.kick("epilogue")

        # timeline
        y0 = 1.7
        line = Line([-6.0, y0, 0], [6.0, y0, 0], stroke_color=FAINT,
                    stroke_width=3)
        events = [
            (-5.4, "1973", "Szekeres asks\nthe question"),
            (-2.8, "1976", "Jaeger: the\n8-flow theorem"),
            (-0.4, "1979", "Seymour asks\nit again"),
            (2.0, "1980s–2020s", "snarks resist\nevery attack"),
            (5.0, "July 10, 2026", "a proof is\nannounced"),
        ]
        dots, labs = VGroup(), VGroup()
        for i, (x, yr, txt) in enumerate(events):
            d = Dot([x, y0, 0], radius=0.09,
                    color=ACCENT if i == len(events) - 1 else NODE_C)
            yr_t = Text(yr, font=FONT, font_size=24, weight=BOLD,
                        color=TEXT_C).next_to(d, UP, buff=0.18)
            lines = txt.split("\n")
            body = VGroup(*[Text(l, font=FONT, font_size=20, color=MUTED)
                            for l in lines]).arrange(DOWN, buff=0.07)
            body.next_to(d, DOWN, buff=0.22)
            dots.add(d)
            labs.add(VGroup(yr_t, body))

        self.say("Fifty-three years, in one line:", hold=False)
        self.play(Create(line), run_time=0.8)
        for d, l in zip(dots, labs):
            self.play(FadeIn(d, scale=0.5), FadeIn(l, shift=UP * 0.1),
                      run_time=0.55)
        self.pad(extra=0.8)

        self.say("If it holds up under review, the promise is total: EVERY",
                 "bridgeless network can be toured in loops, each road twice.",
                 extra=0.8)

        self.play(*[FadeOut(m) for m in self.mobjects if m is not self._cap],
                  run_time=0.7)

        pos = pet_layout(cy=0.2, R=2.3, r=1.25)
        edges_g, nodes_g, _, _ = make_graph(pos, PET_EDGES, w=4)
        edges_g.set_stroke(opacity=0.4)
        book = LaneBook()
        loops = VGroup()
        for code_s, cycles in PET_MS.items():
            loops.add(*class_loops(pos, tuple(code_s), cycles, book, w=4.5,
                                   off=0.1))
        grp = VGroup(edges_g, nodes_g, loops).scale(0.85).shift(UP * 0.75)
        self.say("A fifty-year-old promise — kept twice over.", hold=False)
        self.play(Create(edges_g), FadeIn(nodes_g), run_time=0.9)
        self.play(LaggedStart(*[Create(l) for l in loops], lag_ratio=0.1),
                  run_time=2.4)
        big = Text("TWICE", font=FONT, font_size=64, weight=BOLD, color=TEXT_C)
        big.move_to([0, -2.1, 0])
        self.play(Write(big), run_time=0.9)
        self.pad(extra=0.5)

        credits = VGroup(
            Text("based on the proof of the Cycle Double Cover Conjecture",
                 font=FONT, font_size=20, color=MUTED),
            Text("announced July 10, 2026 (reported as found by an AI model;"
                 " under expert review)", font=FONT, font_size=20, color=MUTED),
            Text("every flow, pairing and loop shown was computed and verified"
                 " — see verify_math.py", font=FONT, font_size=20, color=MUTED),
            Text("made with Manim", font=FONT, font_size=20, color=FAINT),
        ).arrange(DOWN, buff=0.16)
        credits.move_to([0, -3.05, 0])
        for m in credits:
            fit(m)
        self.play(FadeOut(self._cap), FadeIn(credits), run_time=0.8)
        self._cap = None
        self.wait(3.0)
        self.clear_all()
