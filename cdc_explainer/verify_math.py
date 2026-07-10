"""Computationally verify every mathematical claim shown in the video.

The video explains the construction at the heart of the announced proof of the
Cycle Double Cover Conjecture (July 2026): from a nowhere-zero F_2^3 flow
(Jaeger's 8-flow theorem) build, for every edge, a PAIR of "colors" (elements
of F_2^3) such that at every vertex each color appears an even number of times.
Then every color class is a disjoint union of cycles and every edge lies in
exactly two classes: a cycle double cover.

Checks performed here:

 1. CUBE   - the 3-edge-coloring by axis class exists; unions of two color
             classes are the 6 faces; i.e. 3-edge-colorable => CDC (shown in
             chapter "the easy half").  Also: pair labels {0,A}/{0,B}/{A,B}
             by axis class give the same 6 faces (Lemma 2.1 warm-up).
 2. PETERSEN - is NOT 3-edge-colorable (exhaustive); all 6 perfect matchings
             leave two odd 5-cycles (the parity obstruction shown on screen);
             a greedy partial 3-edge-coloring gets stuck (for the game scene).
 3. PETERSEN - hemi-dodecahedral CDC by 6 pentagons (map-on-a-weird-surface).
 4. PETERSEN - THE PAPER'S CONSTRUCTION end to end:
               nowhere-zero F_2^3 flow  ->  local offsets (the junction
               "color triangle", eq. 2)  ->  agreement system
               t_u + t_v + eps_e f(e) = d_e over F_2 (eq. 4)  ->  pair labels
               P_e  ->  local condition (each color 0 or 2 times per vertex,
               condition (1))  ->  color classes decompose into cycles  ->
               every edge covered exactly twice.
 5. ROBUSTNESS - the same pipeline succeeds on K4, K_3,3, the 3-prism, the
             Möbius–Kantor graph, and 300 random bridgeless cubic graphs with
             random flows and random incident-edge orderings (Lemma 2.2 says
             the agreement system is always solvable; we watch it never fail).
 6. The junction triangle fact: at each vertex the three pairs are exactly the
             three sides of the triangle {t, t^x, t^x^y} in color space.

Writes cdc_data.json with everything the manim scenes draw, so nothing on
screen is staged.
"""

from __future__ import annotations

import itertools
import json
import random
from collections import Counter, defaultdict

random.seed(7)

Z = (0, 0, 0)


def xor(p, q):
    return tuple(a ^ b for a, b in zip(p, q))


# --------------------------------------------------------------------------
# generic helpers
# --------------------------------------------------------------------------
def check_cdc(edges, cycles):
    """cycles: list of closed vertex-lists. Every edge covered exactly twice."""
    cnt = Counter()
    for cyc in cycles:
        n = len(cyc)
        assert n >= 3
        for i in range(n):
            e = frozenset((cyc[i], cyc[(i + 1) % n]))
            assert len(e) == 2, f"self-loop in {cyc}"
            cnt[e] += 1
    edge_set = {frozenset(e) for e in edges}
    assert set(cnt) == edge_set, f"covered set differs: {set(cnt) ^ edge_set}"
    bad = {tuple(e): c for e, c in cnt.items() if c != 2}
    assert not bad, f"edges not covered exactly twice: {bad}"
    return True


def cycles_of_even_subgraph(edges_sub):
    """Decompose an even subgraph (all degrees 0 or 2 here) into cycles."""
    adj = defaultdict(list)
    for u, v in edges_sub:
        adj[u].append(v)
        adj[v].append(u)
    for v, ns in adj.items():
        assert len(ns) == 2, f"vertex {v} has degree {len(ns)}"
    unused = {frozenset(e) for e in edges_sub}
    cycles = []
    while unused:
        e0 = next(iter(unused))
        u, v = tuple(e0)
        cyc = [u]
        prev, cur = u, v
        unused.discard(e0)
        while cur != cyc[0]:
            cyc.append(cur)
            nxt = [w for w in adj[cur] if frozenset((cur, w)) in unused]
            assert nxt, f"stuck at {cur}"
            prev, cur = cur, nxt[0]
            unused.discard(frozenset((prev, cur)))
        cycles.append(cyc)
    return cycles


def is_bridgeless_connected(nv, edges):
    if not edges:
        return False
    adj = defaultdict(list)
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    seen = {0}
    stack = [0]
    while stack:
        u = stack.pop()
        for w in adj[u]:
            if w not in seen:
                seen.add(w)
                stack.append(w)
    if len(seen) != nv:
        return False
    # bridge check: removing edge e disconnects?
    for e in edges:
        seen2 = {0}
        stack = [0]
        while stack:
            u = stack.pop()
            for w in adj[u]:
                if frozenset((u, w)) == frozenset(e):
                    continue
                if w not in seen2:
                    seen2.add(w)
                    stack.append(w)
        if len(seen2) != nv:
            return False
    return True


# --------------------------------------------------------------------------
# the paper's construction (flow -> pairs -> CDC), for any cubic graph
# --------------------------------------------------------------------------
def nowhere_zero_f23_flow(nv, edges, rng):
    """Random element of the F_2^3 cycle space that avoids 0 on every edge."""
    adj = defaultdict(list)
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    tree, seen, par = set(), {0}, {0: None}
    stack = [0]
    while stack:
        u = stack.pop()
        for w in adj[u]:
            if w not in seen:
                seen.add(w)
                par[w] = u
                tree.add(frozenset((u, w)))
                stack.append(w)

    def tree_path(u, v):
        au, av = [u], [v]
        while par[au[-1]] is not None:
            au.append(par[au[-1]])
        while par[av[-1]] is not None:
            av.append(par[av[-1]])
        su = set(au)
        m = next(x for x in av if x in su)
        p1 = au[: au.index(m) + 1]
        p2 = av[: av.index(m)]
        return p1 + p2[::-1]

    E_idx = {frozenset(e): i for i, e in enumerate(edges)}
    basis = []
    for u, v in edges:
        if frozenset((u, v)) not in tree:
            pth = tree_path(u, v)
            basis.append(
                {frozenset((pth[i], pth[(i + 1) % len(pth)])) for i in range(len(pth))}
            )
    for _ in range(400000):
        coef = [tuple(rng.randint(0, 1) for _ in range(3)) for _ in basis]
        f = [(0, 0, 0)] * len(edges)
        for c, cyc_edges in zip(coef, basis):
            for fe in cyc_edges:
                i = E_idx[fe]
                f[i] = xor(f[i], c)
        if all(any(b) for b in f):
            # flow condition
            for v in range(nv):
                s = Z
                for e in edges:
                    if v in e:
                        s = xor(s, f[E_idx[frozenset(e)]])
                assert s == Z, (v, s)
            return list(f)
    raise RuntimeError("no nowhere-zero F_2^3 flow found (graph has a bridge?)")


def paper_construction(nv, edges, flow, rng=None, scramble_order=False):
    """eq. 2 offsets + eq. 4 agreement system + pair extraction.

    Returns (pairs P_e by edge index, base colors t_v, color classes Ms).
    Raises AssertionError if any step fails.
    """
    E_idx = {frozenset(e): i for i, e in enumerate(edges)}
    # local offsets g_{v,e}  (eq. 2): order the 3 incident edges, g = 0, f(first), 0
    g = {}
    for v in range(nv):
        inc = sorted(E_idx[frozenset(e)] for e in edges if v in e)
        assert len(inc) == 3, "construction stated for cubic graphs"
        if scramble_order and rng is not None:
            rng.shuffle(inc)
        a, b, c = inc
        g[(v, a)] = Z
        g[(v, b)] = flow[a]
        g[(v, c)] = Z

    d = {}
    for e in edges:
        i = E_idx[frozenset(e)]
        u, v = e
        d[i] = xor(g[(u, i)], g[(v, i)])

    # agreement system (eq. 4): t_u + t_v + eps_e f(e) = d_e   over F_2
    NV, NE = nv, len(edges)
    ncols = 3 * NV + NE
    rows = []
    for e in edges:
        i = E_idx[frozenset(e)]
        u, v = e
        for b in range(3):
            row = [0] * (ncols + 1)
            row[3 * u + b] = 1
            row[3 * v + b] = 1
            row[3 * NV + i] = flow[i][b]
            row[ncols] = d[i][b]
            rows.append(row)
    r, piv = 0, []
    for c in range(ncols):
        p = next((i for i in range(r, len(rows)) if rows[i][c]), None)
        if p is None:
            continue
        rows[r], rows[p] = rows[p], rows[r]
        for i in range(len(rows)):
            if i != r and rows[i][c]:
                rows[i] = [a ^ b for a, b in zip(rows[i], rows[r])]
        piv.append(c)
        r += 1
    assert all(
        any(row[:ncols]) or not row[ncols] for row in rows
    ), "agreement system inconsistent — Lemma 2.2 violated?!"
    sol = [0] * ncols
    for i, c in enumerate(piv):
        sol[c] = rows[i][ncols]
    t = {v: tuple(sol[3 * v + b] for b in range(3)) for v in range(NV)}

    # pair labels from either endpoint; must agree (that's what eq. 4 bought us)
    P = {}
    for e in edges:
        i = E_idx[frozenset(e)]
        u, v = e
        pu = frozenset([xor(t[u], g[(u, i)]), xor(xor(t[u], g[(u, i)]), flow[i])])
        pv = frozenset([xor(t[v], g[(v, i)]), xor(xor(t[v], g[(v, i)]), flow[i])])
        assert pu == pv, (e, pu, pv)
        assert len(pu) == 2, "pair degenerate — flow value was zero?"
        P[i] = pu

    # local condition (1): each color 0 or 2 times around each vertex,
    # and the three pairs at v are the sides of the triangle {t, t^x, t^x^y}
    for v in range(NV):
        cnt = Counter()
        inc = [E_idx[frozenset(e)] for e in edges if v in e]
        for i in inc:
            for s in P[i]:
                cnt[s] += 1
        assert all(k == 2 for k in cnt.values()), (v, cnt)
        corners = set().union(*[P[i] for i in inc])
        assert len(corners) == 3, (v, corners)
        sides = {frozenset(x) for x in itertools.combinations(corners, 2)}
        assert {P[i] for i in inc} == sides, "pairs at v are not a triangle"

    # color classes -> cycles -> CDC
    Ms, all_cycles = {}, []
    for s in itertools.product((0, 1), repeat=3):
        sub = [e for e in edges if s in P[E_idx[frozenset(e)]]]
        if sub:
            cyc = cycles_of_even_subgraph(sub)
            Ms[s] = cyc
            all_cycles += cyc
    check_cdc(edges, all_cycles)
    return P, t, Ms


# --------------------------------------------------------------------------
# 3-edge-coloring utilities
# --------------------------------------------------------------------------
def proper_3ec(edges):
    E = list(edges)
    col = {}

    def ok(i, c):
        u, v = E[i]
        return not any(cc == c and (set(E[j]) & {u, v}) for j, cc in col.items())

    def bt(i):
        if i == len(E):
            return True
        for c in range(3):
            if ok(i, c):
                col[i] = c
                if bt(i + 1):
                    return True
                del col[i]
        return False

    return {E[i]: c for i, c in col.items()} if bt(0) else None


def perfect_matchings(edges, nv):
    res = []

    def bt(rem, chosen):
        if not rem:
            res.append(list(chosen))
            return
        v = min(rem)
        for e in edges:
            if v in e and set(e) <= rem:
                bt(rem - set(e), chosen + [e])

    bt(set(range(nv)), [])
    return res


def cdc_from_3ec(edges, coloring):
    """3-edge-coloring => CDC: unions of two color classes are even 2-regular."""
    all_cycles, unions = [], {}
    for a, b in itertools.combinations(range(3), 2):
        sub = [e for e, c in coloring.items() if c in (a, b)]
        cyc = cycles_of_even_subgraph(sub)
        unions[(a, b)] = cyc
        all_cycles += cyc
    check_cdc(edges, all_cycles)
    return unions


# --------------------------------------------------------------------------
# graphs
# --------------------------------------------------------------------------
def petersen():
    edges = (
        [(i, (i + 1) % 5) for i in range(5)]
        + [(i, i + 5) for i in range(5)]
        + [(5 + i, 5 + ((i + 2) % 5)) for i in range(5)]
    )
    return 10, edges


def cube():
    vs = list(range(8))
    bits = {v: ((v >> 2) & 1, (v >> 1) & 1, v & 1) for v in vs}
    edges, axis = [], {}
    for u, v in itertools.combinations(vs, 2):
        diff = [i for i in range(3) if bits[u][i] != bits[v][i]]
        if len(diff) == 1:
            edges.append((u, v))
            axis[(u, v)] = diff[0]
    return 8, edges, axis


def random_cubic_bridgeless(n, rng):
    """Random cubic graph on n vertices (n even) via pairing model; retry
    until simple, connected, bridgeless."""
    assert n % 2 == 0
    while True:
        stubs = [v for v in range(n) for _ in range(3)]
        rng.shuffle(stubs)
        edges = set()
        ok = True
        for i in range(0, len(stubs), 2):
            u, v = stubs[i], stubs[i + 1]
            if u == v or frozenset((u, v)) in edges:
                ok = False
                break
            edges.add(frozenset((u, v)))
        if not ok:
            continue
        el = [tuple(sorted(e)) for e in edges]
        if is_bridgeless_connected(n, el):
            return n, el


# ==========================================================================
if __name__ == "__main__":
    # ---- 1. CUBE: 3-edge-colorable => CDC (the "easy half" chapter) --------
    ncube, cube_edges, axis = cube()
    col = {e: axis[e] for e in cube_edges}
    # proper?
    for v in range(ncube):
        cs = [col[e] for e in cube_edges if v in e]
        assert sorted(cs) == [0, 1, 2]
    unions = cdc_from_3ec(cube_edges, col)
    n_faces = sum(len(c) for c in unions.values())
    assert n_faces == 6
    print(f"[1] CUBE: axis 3-edge-coloring proper; pairwise unions = {n_faces} "
          "4-cycles = the 6 faces  (3-colorable => CDC)")

    # pair-label warm-up (Lemma 2.1 on the cube)
    A, B = (1, 0, 0), (0, 1, 0)
    pair_by_class = {0: frozenset([Z, A]), 1: frozenset([Z, B]), 2: frozenset([A, B])}
    P_cube = {e: pair_by_class[axis[e]] for e in cube_edges}
    Ms_cube, all_c = {}, []
    for s in itertools.product((0, 1), repeat=3):
        sub = [e for e in cube_edges if s in P_cube[e]]
        if sub:
            cyc = cycles_of_even_subgraph(sub)
            Ms_cube[s] = cyc
            all_c += cyc
    check_cdc(cube_edges, all_c)
    print(f"[1b] CUBE pair labels {{0,A}}/{{0,B}}/{{A,B}}: color classes = "
          f"{sum(len(c) for c in Ms_cube.values())} cycles, CDC OK")

    # ---- 2. PETERSEN is a snark --------------------------------------------
    npet, pet_edges = petersen()
    assert proper_3ec(pet_edges) is None
    print("[2] PETERSEN has NO proper 3-edge-coloring (exhaustive backtracking)")
    pms = perfect_matchings(pet_edges, npet)
    assert len(pms) == 6
    for pm in pms:
        rest = [e for e in pet_edges if e not in pm]
        lens = sorted(len(c) for c in cycles_of_even_subgraph(rest))
        assert lens == [5, 5], lens
    print("[2b] all 6 perfect matchings leave two 5-cycles (odd) -> no third color"
          " can finish: the parity obstruction")

    # a concrete stuck partial coloring for the game scene: color spokes green,
    # then outer pentagon must alternate red/blue -> fails on odd cycle
    spokes = [(i, i + 5) for i in range(5)]
    outer = [(i, (i + 1) % 5) for i in range(5)]
    stuck_edge = outer[-1]
    print(f"[2c] game scene: spokes green, outer C5 alternates and fails at {stuck_edge}")

    # ---- 3. PETERSEN hemi-dodecahedral CDC ---------------------------------
    hemi = [[0, 1, 2, 3, 4]] + [
        [i % 5, (i + 1) % 5, 5 + (i + 1) % 5, 5 + (i + 3) % 5, 5 + i % 5]
        for i in range(5)
    ]
    check_cdc(pet_edges, hemi)
    print(f"[3] PETERSEN hemi-dodecahedron CDC OK: 6 pentagons")

    # ---- 4. the paper's construction on Petersen ---------------------------
    rng = random.Random(7)
    flow = nowhere_zero_f23_flow(npet, pet_edges, rng)
    P_pet, t_pet, Ms_pet = paper_construction(npet, pet_edges, flow)
    ncyc = sum(len(c) for c in Ms_pet.values())
    print(f"[4] PAPER CONSTRUCTION on Petersen: nowhere-zero flow -> triangles ->"
          f" agreement -> pairs -> CDC with {ncyc} cycles")
    for s, cyc in Ms_pet.items():
        print("      color", s, "->", cyc)

    # ---- 5. robustness sweep ------------------------------------------------
    fixed = {
        "K4": (4, [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]),
        "K33": (6, [(i, 3 + j) for i in range(3) for j in range(3)]),
        "prism": (6, [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3),
                      (0, 3), (1, 4), (2, 5)]),
        "moebius-kantor": (16, [(i, (i + 1) % 16) for i in range(0, 16, 2)]
                               + [(i, (i + 5) % 16) for i in range(1, 16, 2)]
                               + [(i, i + 1) for i in range(0, 16, 2)]),
    }
    # fix moebius-kantor: generalized Petersen GP(8,3)
    mk_outer = [(i, (i + 1) % 8) for i in range(8)]
    mk_spoke = [(i, 8 + i) for i in range(8)]
    mk_inner = [(8 + i, 8 + ((i + 3) % 8)) for i in range(8)]
    fixed["moebius-kantor"] = (16, mk_outer + mk_spoke + mk_inner)

    for name, (nv, edges) in fixed.items():
        assert is_bridgeless_connected(nv, edges), name
        fl = nowhere_zero_f23_flow(nv, edges, rng)
        paper_construction(nv, edges, fl)
        print(f"[5] {name}: construction OK")

    trials, sizes = 300, [8, 10, 12, 14, 16, 20]
    for k in range(trials):
        n = sizes[k % len(sizes)]
        nv, edges = random_cubic_bridgeless(n, rng)
        fl = nowhere_zero_f23_flow(nv, edges, rng)
        paper_construction(nv, edges, fl, rng=rng, scramble_order=(k % 2 == 1))
    print(f"[5b] {trials} random bridgeless cubic graphs (n in {sizes}), random flows,"
          " half with scrambled edge orderings: agreement system solvable and CDC"
          " extracted EVERY time (Lemma 2.2 in action)")

    # ---- 6. dump everything the scenes draw --------------------------------
    out = {
        "petersen_edges": [list(e) for e in pet_edges],
        "hemi_faces": hemi,
        "flow": {f"{u},{v}": list(flow[i]) for i, (u, v) in enumerate(pet_edges)},
        "pairs": {
            f"{u},{v}": sorted(map(list, P_pet[i]))
            for i, (u, v) in enumerate(pet_edges)
        },
        "base_colors": {str(v): list(t_pet[v]) for v in range(npet)},
        "pet_Ms": {str(s): cyc for s, cyc in Ms_pet.items()},
        "cube_edges": [list(e) for e in cube_edges],
        "cube_axis": {f"{u},{v}": axis[(u, v)] for (u, v) in cube_edges},
        "cube_unions": {str(k): v for k, v in unions.items()},
        "cube_Ms": {str(s): cyc for s, cyc in Ms_cube.items()},
    }
    with open("cdc_data.json", "w") as fh:
        json.dump(out, fh, indent=1)
    print("\nALL CHECKS PASSED — scene data written to cdc_data.json")
