"""Verify the real generator's geometry math outside Fusion.

adsk.* only exists inside Fusion, so stub it before import.
"""
import sys
import types
import math

for name in ('adsk', 'adsk.core', 'adsk.fusion'):
    mod = types.ModuleType(name)
    mod.__getattr__ = lambda _n: types.SimpleNamespace()
    sys.modules[name] = mod
sys.modules['adsk'].core = sys.modules['adsk.core']
sys.modules['adsk'].fusion = sys.modules['adsk.fusion']

sys.path.insert(0, 'cases/corne-choc-travel')
import corne_choc_travel_case as G

P = G.PARAMS
base = P['half_outline_mm']


def seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def poly_dist(p, poly):
    return min(seg_dist(p, poly[i], poly[(i + 1) % len(poly)])
               for i in range(len(poly)))


def point_in_poly(p, poly):
    x, y = p
    inside = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y):
            if x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
                inside = not inside
    return inside


def edge_mids(poly):
    n = len(poly)
    return [((poly[i][0] + poly[(i + 1) % n][0]) / 2,
             (poly[i][1] + poly[(i + 1) % n][1]) / 2) for i in range(n)]


fails = []


def check(label, cond, detail=""):
    print("  %-52s %s %s" % (label, "PASS" if cond else "FAIL", detail))
    if not cond:
        fails.append(label)


clear = P['pocket_clearance']
print("PARAMS: pocket_clearance=%.2f  border=%.1f  inner_gap=%.1f  "
      "bolt_inset=%.1f  corner_radius=%.1f"
      % (clear, P['border'], P['inner_gap'],
         P['bolt_hole_inset'], P['corner_radius']))
print()

print("1. Offset delivers the requested clearance on EVERY edge")
off = G._offset_polygon(base, clear)
mids = [poly_dist(m, off) for m in edge_mids(base)]
verts = [poly_dist(v, base) for v in off]
check("min edge-midpoint clearance >= %.3f" % clear,
      min(mids) >= clear - 1e-6, "got %.4f" % min(mids))
check("max edge-midpoint clearance <= %.3f (miter cap)" % (clear * 4),
      max(mids) <= clear * 4, "got %.4f" % max(mids))
check("min vertex clearance > 0", min(verts) > 0, "got %.4f" % min(verts))
check("original outline fully inside offset",
      all(point_in_poly(v, off) for v in base))
check("vertex count preserved", len(off) == len(base),
      "%d -> %d" % (len(base), len(off)))
print()

print("2. Old centroid method would have failed the same check")
def old(pts, d):
    cx = sum(x for x, _ in pts) / len(pts)
    cy = sum(y for _, y in pts) / len(pts)
    o = []
    for x, y in pts:
        vx, vy = x - cx, y - cy
        L = math.hypot(vx, vy)
        o.append((x, y) if L == 0 else (x + vx / L * d, y + vy / L * d))
    return o
om = [poly_dist(m, old(base, clear)) for m in edge_mids(base)]
print("  OLD min edge clearance %.4f  (%.0f%% of requested %.2f)"
      % (min(om), 100 * min(om) / clear, clear))
print("  NEW min edge clearance %.4f  (%.0f%% of requested %.2f)"
      % (min(mids), 100 * min(mids) / clear, clear))
check("new method strictly better", min(mids) > min(om))
print()

print("3. Winding-independent (reversed input gives same result)")
rev = G._offset_polygon(list(reversed(base)), clear)
rm = [poly_dist(m, rev) for m in edge_mids(base)]
check("reversed winding still >= %.3f" % clear,
      min(rm) >= clear - 1e-6, "got %.4f" % min(rm))
print()

print("4. Stable across a delta sweep")
for d in (0.25, 0.5, 1.0, 1.5, 2.0, 3.0):
    o = G._offset_polygon(base, d)
    m = min(poly_dist(p, o) for p in edge_mids(base))
    check("delta=%.2f -> min clearance %.4f" % (d, m), m >= d - 1e-6)
print()

print("5. Degenerate inputs do not crash")
check("delta=0 returns input", G._offset_polygon(base, 0.0) == list(base))
check("2-point polygon returns input",
      G._offset_polygon([(0, 0), (1, 1)], 1.0) == [(0, 0), (1, 1)])
sq = [(0, 0), (10, 0), (10, 10), (0, 10)]
so = G._offset_polygon(sq, 1.0)
check("unit square offsets to exactly -1..11",
      all(abs(abs(c) - 1.0) < 1e-9 or abs(abs(c) - 11.0) < 1e-9
          for pt in so for c in pt),
      str([tuple(round(c, 6) for c in p) for p in so]))
dup = [(0, 0), (0, 0), (10, 0), (10, 10), (0, 10)]
check("duplicate vertex tolerated", len(G._offset_polygon(dup, 1.0)) == 4)
print()

print("6. Full pocket pipeline + tray fit")
lp, rp, lh, rh, (bw, bh) = G._compute_pocket_polygons(P)
tray_w = bw + 2 * P['border']
tray_d = bh + 2 * P['border']
tray_h = P['stack_height'] + P['floor_thickness']
print("  tray outer: %.2f x %.2f x %.2f mm" % (tray_w, tray_d, tray_h))
pw, pd = P['build_plate']
check("fits build plate %.0fx%.0f" % (pw, pd), tray_w <= pw and tray_d <= pd)
check("pockets do not overlap",
      min(poly_dist(p, rp) for p in lp) > 0,
      "divider %.2f mm" % min(poly_dist(p, rp) for p in lp))
# Pockets are normalised to start at exactly 0 pre-border, so bounds
# are inclusive. bw is the COMBINED span of both pockets plus the gap.
eps = 1e-9
check("left pocket within combined bbox",
      all(-eps <= x <= bw + eps and -eps <= y <= bh + eps for x, y in lp))
check("right pocket within combined bbox",
      all(-eps <= x <= bw + eps and -eps <= y <= bh + eps for x, y in rp))
check("pockets span the reported bbox exactly",
      abs(min(x for x, _ in lp)) < eps
      and abs(max(x for x, _ in rp) - bw) < eps)
check("mounting holes preserved",
      len(lh) == len(P['mounting_holes_mm']) == len(rh))
print()

print("7. Bolt holes clear the corner fillet")
ins = P['bolt_hole_inset']
r = P['bolt_hole_dia'] / 2
R = P['corner_radius']
diag = ins * math.sqrt(2) - R * (math.sqrt(2) - 1) - r
print("  material outside bolt on diagonal: %.2f mm" % diag)
check("diagonal material >= 2x wall (4.0 mm)", diag >= 4.0)
lpb = [(x + P['border'], y + P['border']) for x, y in lp]
rpb = [(x + P['border'], y + P['border']) for x, y in rp]
for cx, cy in ((ins, ins), (tray_w - ins, ins),
               (ins, tray_d - ins), (tray_w - ins, tray_d - ins)):
    d = min(poly_dist((cx, cy), lpb), poly_dist((cx, cy), rpb)) - r
    check("bolt at (%.1f,%.1f) clears pocket" % (cx, cy), d > 2.0,
          "%.2f mm" % d)

print()
print("=" * 60)
print("FAILED: %s" % fails if fails else "ALL CHECKS PASSED")
sys.exit(1 if fails else 0)
