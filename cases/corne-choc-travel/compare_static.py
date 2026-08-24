"""Compare the parametric tray pocket against the static Typeractive model.

Two independent checks that do NOT require Fusion:

  1. Extraction fidelity — does typeractive_outline.py's 45-point polygon
     still match the geometry in the static STEP it was traced from?
  2. Fit — does the generated pocket actually accept that real geometry,
     with the clearance PARAMS asks for?

Check 2 is the one the printed tray failed. The static bottom shell and
the travel tray are different parts (132x87 mm vs 213x154 mm), so a
whole-body diff between them is meaningless; the shared contract is the
rim outline, and that is what this compares.

Usage:
    python3 cases/corne-choc-travel/compare_static.py [path/to/static.step]
"""
import math
import os
import re
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_STEP = os.path.join(
    HERE, 'typeractive_case-bottom-3dp-meshopt.step')


def load_generator():
    """Import the Fusion script with adsk stubbed so it works headless."""
    for name in ('adsk', 'adsk.core', 'adsk.fusion'):
        mod = types.ModuleType(name)
        mod.__getattr__ = lambda _n: types.SimpleNamespace()
        sys.modules[name] = mod
    sys.modules['adsk'].core = sys.modules['adsk.core']
    sys.modules['adsk'].fusion = sys.modules['adsk.fusion']
    sys.path.insert(0, HERE)
    import corne_choc_travel_case as gen
    return gen


POINT_RE = re.compile(
    r"CARTESIAN_POINT\s*\(\s*'[^']*'\s*,\s*\(\s*"
    r"([-0-9.E+]+)\s*,\s*([-0-9.E+]+)\s*,\s*([-0-9.E+]+)\s*\)")


def read_step_points(path):
    with open(path, 'r', errors='replace') as fh:
        text = fh.read()
    pts = []
    for m in POINT_RE.finditer(text):
        pts.append((float(m.group(1)), float(m.group(2)), float(m.group(3))))
    return pts


def seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0,
                                        ((px - ax) * dx + (py - ay) * dy) / L))
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


def main():
    step_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_STEP
    gen = load_generator()
    P = gen.PARAMS
    outline = P['half_outline_mm']
    clear = P['pocket_clearance']

    print('static model : %s' % os.path.basename(step_path))
    print('pocket_clearance = %.3f mm' % clear)
    print()

    if not os.path.exists(step_path):
        print('SKIP: static STEP not found (large binary, may be untracked).')
        print('      Pass its path as an argument to run the fidelity check.')
        pts3 = None
    else:
        pts3 = read_step_points(step_path)

    failures = []

    def check(label, ok, detail=''):
        print('  %-50s %s %s' % (label, 'PASS' if ok else 'FAIL', detail))
        if not ok:
            failures.append(label)

    # ---- 1. Extraction fidelity -------------------------------------
    print('1. Outline still matches the static model it was traced from')
    if pts3 is None:
        print('   (skipped, no STEP file)')
    else:
        xs = [p[0] for p in pts3]
        ys = [p[1] for p in pts3]
        zs = [p[2] for p in pts3]
        span = [max(v) - min(v) for v in (xs, ys, zs)]
        print('   STEP vertices: %d' % len(pts3))
        print('   STEP bbox    : %.3f x %.3f x %.3f mm'
              % (span[0], span[1], span[2]))

        ow = max(x for x, _ in outline) - min(x for x, _ in outline)
        oh = max(y for _, y in outline) - min(y for _, y in outline)
        print('   outline bbox : %.3f x %.3f mm' % (ow, oh))

        # The outline is a planar trace, so it should match the two
        # largest spans of the solid to within a wall thickness.
        flat = sorted(span, reverse=True)[:2]
        got = sorted([ow, oh], reverse=True)
        d0 = abs(flat[0] - got[0])
        d1 = abs(flat[1] - got[1])
        check('long axis within 6 mm of solid', d0 <= 6.0,
              'delta %.3f mm' % d0)
        check('short axis within 6 mm of solid', d1 <= 6.0,
              'delta %.3f mm' % d1)
    print()

    # ---- 2. Fit: does the pocket accept the real outline? ------------
    print('2. Generated pocket accepts the outline with full clearance')
    pocket = gen._offset_polygon(outline, clear)

    inside = [point_in_poly(v, pocket) for v in outline]
    check('every outline vertex inside pocket', all(inside),
          '%d/%d' % (sum(inside), len(inside)))

    vclear = [poly_dist(v, pocket) for v in outline]
    check('min vertex clearance >= %.3f' % clear,
          min(vclear) >= clear - 1e-6, 'got %.4f mm' % min(vclear))

    mids = []
    n = len(outline)
    for i in range(n):
        a, b = outline[i], outline[(i + 1) % n]
        mids.append(poly_dist(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), pocket))
    check('min edge clearance >= %.3f' % clear,
          min(mids) >= clear - 1e-6, 'got %.4f mm' % min(mids))
    print('   clearance across all edges: min %.4f  mean %.4f  max %.4f'
          % (min(mids), sum(mids) / len(mids), max(mids)))
    print()

    # ---- 3. Regression: the shipped bug, measured -------------------
    print('3. Regression guard vs the old centroid method')

    def centroid_expand(pts, d):
        cx = sum(x for x, _ in pts) / len(pts)
        cy = sum(y for _, y in pts) / len(pts)
        out = []
        for x, y in pts:
            vx, vy = x - cx, y - cy
            L = math.hypot(vx, vy)
            out.append((x, y) if L == 0
                       else (x + vx / L * d, y + vy / L * d))
        return out

    old_poly = centroid_expand(outline, clear)
    old_mids = []
    for i in range(n):
        a, b = outline[i], outline[(i + 1) % n]
        old_mids.append(
            poly_dist(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), old_poly))
    print('   old method min clearance: %.4f mm (%.0f%% of requested)'
          % (min(old_mids), 100 * min(old_mids) / clear))
    print('   new method min clearance: %.4f mm (%.0f%% of requested)'
          % (min(mids), 100 * min(mids) / clear))
    check('new method delivers full clearance where old did not',
          min(mids) >= clear - 1e-6 > min(old_mids))
    print()

    # ---- 4. Tray envelope ------------------------------------------
    print('4. Tray envelope (parametric part, for reference)')
    lp, rp, lh, rh, (bw, bh) = gen._compute_pocket_polygons(P)
    tray_w = bw + 2 * P['border']
    tray_d = bh + 2 * P['border']
    tray_h = P['stack_height'] + P['floor_thickness']
    print('   tray   : %.2f x %.2f x %.2f mm' % (tray_w, tray_d, tray_h))
    print('   pocket : %.2f x %.2f mm per half' % (bw / 2, bh))
    pw, pd = P['build_plate']
    check('fits build plate %.0f x %.0f' % (pw, pd),
          tray_w <= pw and tray_d <= pd)
    print()

    print('=' * 60)
    if failures:
        print('FAILED: %s' % failures)
        return 1
    print('ALL CHECKS PASSED')
    return 0


if __name__ == '__main__':
    sys.exit(main())
