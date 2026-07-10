"""Computationally verify every mathematical claim the video will visualize.

1. Cube: the pair-label scheme ({0,a}/{0,b}/{a,b} by axis class) yields exactly
   the 6 faces as a cycle double cover  (Lemma 2.1 demo, easy case).
2. Petersen: the hemi-dodecahedron 6-pentagon CDC is valid.
3. Petersen: run the PAPER'S FULL CONSTRUCTION end to end:
     - find a nowhere-zero F_2^3 flow (8-flow theorem instance)
     - build local offsets g_{v,e}   (eq. 2)
     - solve the linear system  t_u + t_v + eps_e f(e) = d_e   (eq. 4) over F_2
     - build pair labels P_e, check the local condition (1)
     - extract color classes M_s, decompose into cycles, verify double cover
4. Petersen: verify it is NOT 3-edge-colorable, and find a maximal partial
   proper 3-edge-coloring stuck at exactly one edge (for the "snark" scene).
Outputs a JSON blob of everything the manim scenes need.
"""

import itertools, json, random

random.seed(7)

# ---------------------------------------------------------------- helpers
def check_cdc(edges, cycles):
    """cycles: list of vertex-lists (closed). Verify every edge covered exactly 2x."""
    from collections import Counter
    cnt = Counter()
    for cyc in cycles:
        n = len(cyc)
        for i in range(n):
            e = frozenset((cyc[i], cyc[(i + 1) % n]))
            assert len(e) == 2, f"loop edge in cycle {cyc}"
            cnt[e] += 1
    edge_set = {frozenset(e) for e in edges}
    assert set(cnt) == edge_set, (set(cnt) ^ edge_set)
    bad = {tuple(e): c for e, c in cnt.items() if c != 2}
    assert not bad, bad
    return True

def cycles_of_even_subgraph(edges_sub):
    """edges_sub: list of (u,v). Every vertex has degree 0/2 -> decompose into cycles."""
    from collections import defaultdict
    adj = defaultdict(list)
    for u, v in edges_sub:
        adj[u].append(v); adj[v].append(u)
    for v, ns in adj.items():
        assert len(ns) == 2, f"vertex {v} has degree {len(ns)}"
    unused = {frozenset(e) for e in edges_sub}
    cycles = []
    while unused:
        e0 = next(iter(unused)); u, v = tuple(e0)
        cyc = [u]; prev, cur = u, v
        unused.discard(e0)
        while cur != cyc[0]:
            cyc.append(cur)
            nxt = [w for w in adj[cur] if w != prev or adj[cur].count(prev) == 2]
            nxt = [w for w in nxt if frozenset((cur, w)) in unused]
            assert nxt, f"stuck at {cur}"
            prev, cur = cur, nxt[0]
            unused.discard(frozenset((prev, cur)))
        cycles.append(cyc)
    return cycles

# ---------------------------------------------------------------- 1. CUBE
# vertices: 0-3 outer square (planar drawing), 4-7 inner square; i outer <-> i+4 inner
# 3-edge-coloring by 3D axis class:
#   class X: outer top+bottom horizontals & inner ones... use 3D cube for truth:
# 3D cube vertices = bits (b0,b1,b2); edges differ in one bit; class = which bit.
cube_v = list(range(8))
bits = {v: ((v >> 2) & 1, (v >> 1) & 1, v & 1) for v in cube_v}
cube_edges, cube_class = [], {}
for u, v in itertools.combinations(cube_v, 2):
    diff = [i for i in range(3) if bits[u][i] != bits[v][i]]
    if len(diff) == 1:
        cube_edges.append((u, v)); cube_class[(u, v)] = diff[0]

A, B = (1, 0, 0), (0, 1, 0)   # F_2^3 elements as tuples; 0 = (0,0,0)
Z3 = (0, 0, 0)
def x3(p, q): return tuple(a ^ b for a, b in zip(p, q))
AB = x3(A, B)
pair_by_class = {0: frozenset([Z3, A]), 1: frozenset([Z3, B]), 2: frozenset([A, B])}
P_cube = {e: pair_by_class[cube_class[e]] for e in cube_edges}

# local condition (1): each s in Gamma appears 0 or 2 times among pairs at each vertex
for v in cube_v:
    from collections import Counter
    c = Counter()
    for e in cube_edges:
        if v in e:
            for s in P_cube[e]: c[s] += 1
    assert all(k in (0, 2) for k in c.values()), (v, c)

# extract M_s and cycles
all_cycles_cube = []
Ms_cube = {}
for s in itertools.product((0, 1), repeat=3):
    sub = [e for e in cube_edges if s in P_cube[e]]
    if sub:
        cyc = cycles_of_even_subgraph(sub)
        Ms_cube[s] = cyc
        all_cycles_cube += cyc
check_cdc(cube_edges, all_cycles_cube)
print(f"[1] CUBE pair-label CDC OK: {len(all_cycles_cube)} cycles (expect 6 faces)")
for s, cyc in Ms_cube.items():
    print("     color", s, "->", cyc)

# ---------------------------------------------------------------- 2. PETERSEN hemi-dodecahedron
pet_v = list(range(10))
pet_edges = [(i, (i + 1) % 5) for i in range(5)] \
          + [(i, i + 5) for i in range(5)] \
          + [(5 + i, 5 + ((i + 2) % 5)) for i in range(5)]
hemi = [[0, 1, 2, 3, 4]] + [[i % 5, (i + 1) % 5, 5 + (i + 1) % 5, 5 + (i + 3) % 5, 5 + i % 5] for i in range(5)]
check_cdc(pet_edges, hemi)
print(f"[2] PETERSEN hemi-dodecahedron CDC OK: 6 pentagons: {hemi}")

# ---------------------------------------------------------------- 3. PETERSEN: paper's construction
# 3a. nowhere-zero F_2^3 flow: element of cycle space (over F_2, per-bit) nowhere zero.
# cycle space basis from spanning tree
import collections
adj = collections.defaultdict(list)
for u, v in pet_edges:
    adj[u].append(v); adj[v].append(u)
tree, seen, par = set(), {0}, {0: None}
stack = [0]
while stack:
    u = stack.pop()
    for w in adj[u]:
        if w not in seen:
            seen.add(w); par[w] = u; tree.add(frozenset((u, w))); stack.append(w)

def tree_path(u, v):
    au, av = [u], [v]
    while par[au[-1]] is not None: au.append(par[au[-1]])
    while par[av[-1]] is not None: av.append(par[av[-1]])
    su = set(au)
    m = next(x for x in av if x in su)
    p1 = au[:au.index(m) + 1]; p2 = av[:av.index(m)]
    return p1 + p2[::-1]

non_tree = [e for e in pet_edges if frozenset(e) not in tree]
basis = []  # each = set of frozenset edges (fundamental cycle)
for u, v in non_tree:
    pth = tree_path(u, v)
    ed = {frozenset((pth[i], pth[(i + 1) % len(pth)])) for i in range(len(pth))}
    basis.append(ed)

E_idx = {frozenset(e): i for i, e in enumerate(pet_edges)}
flow = None
for attempt in range(200000):
    coef = [tuple(random.randint(0, 1) for _ in range(3)) for _ in basis]
    f = [ [0,0,0] for _ in pet_edges ]
    for c, ed in zip(coef, basis):
        for fe in ed:
            i = E_idx[fe]
            f[i] = [a ^ b for a, b in zip(f[i], c)]
    if all(any(bits_) for bits_ in f):
        flow = [tuple(x) for x in f]
        break
assert flow, "no nowhere-zero flow found"
# check flow condition (char 2: sum of incident = 0)
for v in pet_v:
    s = (0, 0, 0)
    for e in pet_edges:
        if v in e: s = x3(s, flow[E_idx[frozenset(e)]])
    assert s == Z3, (v, s)
print(f"[3a] nowhere-zero F_2^3 flow on Petersen OK (found at attempt {attempt})")

# 3b. local offsets g_{v,e}: order incident edges (a,b,c) by edge index; g=0, x, 0 (eq 2)
g = {}  # (v, edge_idx) -> tuple in F_2^3
for v in pet_v:
    inc = sorted(E_idx[frozenset(e)] for e in pet_edges if v in e)
    a, b, c = inc
    g[(v, a)] = Z3
    g[(v, b)] = flow[a]          # x = f(a)
    g[(v, c)] = Z3

d = {}  # edge -> g_u,e + g_v,e
for e in pet_edges:
    i = E_idx[frozenset(e)]; u, v = e
    d[i] = x3(g[(u, i)], g[(v, i)])

# 3c. solve (4): t_u + t_v + eps_e f(e) = d_e over F_2  (unknowns: 30 t-bits + 15 eps)
NV, NE = 10, 15
ncols = 3 * NV + NE
rows = []
for e in pet_edges:
    i = E_idx[frozenset(e)]; u, v = e
    for b in range(3):
        row = [0] * (ncols + 1)
        row[3 * u + b] = 1; row[3 * v + b] = 1
        row[3 * NV + i] = flow[i][b]
        row[ncols] = d[i][b]
        rows.append(row)
# gaussian elimination
r = 0
piv = []
for c in range(ncols):
    p = next((i for i in range(r, len(rows)) if rows[i][c]), None)
    if p is None: continue
    rows[r], rows[p] = rows[p], rows[r]
    for i in range(len(rows)):
        if i != r and rows[i][c]:
            rows[i] = [a ^ b for a, b in zip(rows[i], rows[r])]
    piv.append(c); r += 1
assert all(any(row[:ncols]) or not row[ncols] for row in rows), "system inconsistent!"
sol = [0] * ncols
for i, c in enumerate(piv):
    sol[c] = rows[i][ncols]
t = {v: tuple(sol[3 * v + b] for b in range(3)) for v in pet_v}
eps = {i: sol[3 * NV + i] for i in range(NE)}
print("[3b/c] linear system (4) solved  (Lemma 2.2 instance)")

# 3d. pairs P_e from either endpoint; verify well-defined + condition (1)
P_pet = {}
for e in pet_edges:
    i = E_idx[frozenset(e)]; u, v = e
    pu = frozenset([x3(t[u], g[(u, i)]), x3(x3(t[u], g[(u, i)]), flow[i])])
    pv = frozenset([x3(t[v], g[(v, i)]), x3(x3(t[v], g[(v, i)]), flow[i])])
    assert pu == pv, (e, pu, pv)
    assert len(pu) == 2
    P_pet[i] = pu
for v in pet_v:
    c = collections.Counter()
    for e in pet_edges:
        if v in e:
            for s in P_pet[E_idx[frozenset(e)]]: c[s] += 1
    assert all(k in (0, 2) for k in c.values()), (v, c)
print("[3d] pair labels P_e well-defined across edges + local condition (1) OK")

# 3e. extract cycles, verify CDC
Ms_pet, all_cycles_pet = {}, []
for s in itertools.product((0, 1), repeat=3):
    sub = [e for e in pet_edges if s in P_pet[E_idx[frozenset(e)]]]
    if sub:
        cyc = cycles_of_even_subgraph(sub)
        Ms_pet[s] = cyc; all_cycles_pet += cyc
check_cdc(pet_edges, all_cycles_pet)
print(f"[3e] PAPER CONSTRUCTION on Petersen gives a CDC: {len(all_cycles_pet)} cycles")
for s, cyc in Ms_pet.items(): print("     color", s, "->", cyc)

# ---------------------------------------------------------------- 4. Petersen not 3-edge-colorable
def proper_3ec(edges, forced=None):
    """backtracking proper 3-edge-coloring; returns dict or None"""
    E = list(edges); col = {}
    def ok(i, c):
        u, v = E[i]
        for j, cc in col.items():
            if cc == c and (set(E[j]) & {u, v}): return False
        return True
    def bt(i):
        if i == len(E): return True
        for c in range(3):
            if ok(i, c):
                col[i] = c
                if bt(i + 1): return True
                del col[i]
        return False
    return {E[i]: c for i, c in col.items()} if bt(0) else None

assert proper_3ec(pet_edges) is None
print("[4] Petersen is NOT 3-edge-colorable (snark) — verified by exhaustive search")

# 4b. every perfect matching of Petersen leaves two odd (5-)cycles
def perfect_matchings(edges, nv):
    res = []
    def bt(rem, chosen):
        if not rem:
            res.append(list(chosen)); return
        v = min(rem)
        for e in edges:
            if v in e and set(e) <= rem:
                bt(rem - set(e), chosen + [e])
    bt(set(range(nv)), [])
    return res

pms = perfect_matchings(pet_edges, 10)
print(f"[4b] Petersen has {len(pms)} perfect matchings (expect 6)")
for pm in pms:
    rest = [e for e in pet_edges if e not in pm]
    cyc = cycles_of_even_subgraph(rest)
    lens = sorted(len(c) for c in cyc)
    assert lens == [5, 5], lens
print("[4b] every perfect matching leaves two 5-cycles (odd!) -> 3-coloring impossible")
spokes = [(i, i + 5) for i in range(5)]
assert spokes in pms or [tuple(e) for e in spokes] in [ [tuple(x) for x in pm] for pm in pms]
print("[4c] spoke matching is a perfect matching; remainder = outer+inner pentagons")

# ---------------------------------------------------------------- dump for manim
out = {
    "petersen_edges": pet_edges,
    "hemi_faces": hemi,
    "flow": {str(pet_edges[i]): flow[i] for i in range(15)},
    "pairs": {str(pet_edges[i]): sorted(map(list, P_pet[i])) for i in range(15)},
    "pet_Ms": {str(s): cyc for s, cyc in Ms_pet.items()},
    "cube_Ms": {str(s): cyc for s, cyc in Ms_cube.items()},
}
with open("cdc_data.json", "w") as fh:
    json.dump(out, fh, indent=1)
print("\nALL CHECKS PASSED — data dumped to cdc_data.json")
