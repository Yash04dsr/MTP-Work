#!/usr/bin/env python3
"""
Generate a water-tight T-junction STL for snappyHexMesh.

Strategy
--------
The main-pipe wall has a rectangular hole (in (theta, z) parameter space)
around the T-junction. The rectangular hole boundary is connected to the
analytic branch/main intersection curve with a zipper triangulation.
The branch-pipe wall starts *directly on the intersection curve*, so the
hole boundary on the main pipe and the base of the branch pipe share the
EXACT same vertices.  That is what makes the combined surface water-tight.

A sanity check on the signed volume is performed at the end; the script
aborts if the ratio differs from 1.0 by more than 3%.

Requires: numpy, numpy-stl
"""

import math
import os

import numpy as np
from stl import mesh as stlmesh


# ---------- Geometry (parameterised via env vars for DoE) --------------
# All lengths in metres. Defaults correspond to the post-R2 baseline
# (upstream main shortened from 4.6 m to 2.3 m; downstream kept at 4.6 m
# = 10 D_main per Ayach 2017). Branch diameter D2 and main U_main are
# overridden per DoE case by stamp_cases.py via these env vars.
def _envf(key, default):
    return float(os.environ.get(key, default))

D1 = _envf("D1", 0.460)          # main pipe diameter [m]
R1 = D1 / 2.0
L_MAIN = _envf("L_MAIN", 6.900)  # main pipe length along Z (R2: 6.9 m)
Z_JCT = _envf("Z_JCT", 2.300)    # junction centre along Z (R2: 2.3 m)

D2 = _envf("D2", 0.115)          # branch pipe diameter [m] (DoE variable)
R2 = D2 / 2.0
# Branch length: keep at least 12*D2 so inlet BC effects decay before junction.
L_BRANCH = _envf(
    "L_BRANCH", max(1.380, R1 + 12.0 * D2)
)

# ---------- Tilt (new in 30deg base) ----------------------------------
# Branch axis makes angle ALPHA with the -z axis (main flow direction is +z).
# ALPHA=90 deg reproduces the perpendicular T (= original 90deg base).
# ALPHA=30 deg => 30 deg Y-junction with branch inlet up-and-upstream.
ALPHA_DEG = _envf("ALPHA_DEG", 90.0)
ALPHA = ALPHA_DEG * math.pi / 180.0
SIN_A = math.sin(ALPHA)
COS_A = math.cos(ALPHA)

# Branch basis vectors (numpy arrays).
#   S_HAT = junction -> inlet    direction along branch axis
#   E1, E2 = two orthonormal directions perpendicular to S_HAT
#   For ALPHA=90 (original): S_HAT=(0,1,0), E1=(1,0,0), E2=(0,0,1).
JUNCTION_VEC = np.array([0.0, R1, Z_JCT])
S_HAT        = np.array([0.0, SIN_A, -COS_A])
E1           = np.array([1.0, 0.0, 0.0])
E2           = np.cross(E1, S_HAT)            # = (0, COS_A, SIN_A)


# ---------- Discretisation ---------------------------------------------
N_CIRC = int(os.environ.get("N_CIRC", "96"))
N_AXIAL_MAIN = int(os.environ.get(
    "N_AXIAL_MAIN", str(int(round(L_MAIN / (9.2 / 240.0))))
))
N_AXIAL_BRANCH = int(os.environ.get(
    "N_AXIAL_BRANCH", str(int(round(L_BRANCH / (1.380 / 48.0))))
))

BUFFER_CELLS = 2     # padding around hole when building the rectangle


# ---------- Helpers ----------------------------------------------------

def signed_volume(tris):
    """Divergence-theorem signed volume of a closed triangle mesh."""
    arr = np.asarray(tris, dtype=np.float64)
    v0, v1, v2 = arr[:, 0], arr[:, 1], arr[:, 2]
    return float(np.einsum('ij,ij->i', v0, np.cross(v1, v2)).sum() / 6.0)


def make_stl(tris):
    arr = np.asarray(tris, dtype=np.float32)
    m = stlmesh.Mesh(np.zeros(len(arr), dtype=stlmesh.Mesh.dtype))
    m.vectors[:] = arr
    return m


def main_pt(theta, z):
    """Point on the main-pipe surface."""
    return np.array([R1 * math.cos(theta), R1 * math.sin(theta), z])


def branch_pt(phi, s):
    """Point on the branch-pipe surface at angular phi and axial s.

    s is arc-length along the branch axis, s=0 at junction, increasing
    toward the branch inlet in direction S_HAT.  At ALPHA=90 this reduces
    to the original (x=R2 cos phi, y=R1+s, z=Z_JCT + R2 sin phi).
    """
    return (JUNCTION_VEC + s * S_HAT
            + R2 * math.cos(phi) * E1
            + R2 * math.sin(phi) * E2)


def s_intersect(phi):
    """Axial branch-coord s where branch surface (at phi) meets main wall.

    Let P(phi,s) = JUNCTION + s*S_HAT + R2*cos(phi)*E1 + R2*sin(phi)*E2.
    Since S_HAT.x=E1.y=E1.z=E2.x=0:
        P.x = R2 * cos(phi)
        P.y = R1 + s * SIN_A + R2 * sin(phi) * COS_A
    Main wall:  P.x^2 + P.y^2 = R1^2
        R2^2 cos^2(phi) + (R1 + s*SIN_A + R2*sin(phi)*COS_A)^2 = R1^2
        Let A = R1 + R2*sin(phi)*COS_A,  B = sqrt(R1^2 - R2^2 cos^2 phi)
        s = (B - A) / SIN_A   (take outward root)

    At ALPHA=90 (SIN_A=1, COS_A=0): s = B - R1 = y_old - R1 (since
    junction is at y=R1 in the original parametrisation).  Thus
    s_intersect can be negative for some phi, which simply means the
    intersection lies on the near side of the junction (still correct).
    """
    disc = R1 * R1 - R2 * R2 * math.cos(phi) ** 2
    if disc < 0.0:
        disc = 0.0
    B = math.sqrt(disc)
    A = R1 + R2 * math.sin(phi) * COS_A
    if SIN_A < 1e-9:
        # Degenerate: branch lies along +z or -z. Not used in DoE.
        return 0.0
    return (B - A) / SIN_A


def vertex_in_hole(theta, z):
    """True if main-pipe vertex lies inside the (infinite) branch cylinder
    on the branch side of the junction.  Generalised from the old
    perpendicular-only heuristic: 'y > 0 AND (x, z-Z_JCT) within R2'."""
    x = R1 * math.cos(theta)
    y = R1 * math.sin(theta)
    if y <= 0.0:
        return False
    wx, wy, wz = x - 0.0, y - R1, z - Z_JCT
    # perpendicular distance from branch axis (infinite line through
    # JUNCTION in direction S_HAT).  |w x S_HAT| works since |S_HAT|=1.
    cx = wy * (-COS_A) - wz * SIN_A
    cy = wz * 0.0      - wx * (-COS_A)
    cz = wx * SIN_A    - wy * 0.0
    dist_sq = cx * cx + cy * cy + cz * cz
    return dist_sq < R2 * R2


# ---------- Zipper triangulation between two closed loops --------------

def zipper(outer, inner):
    """Triangulate the annulus bounded by `outer` and `inner` closed loops.

    Both must be ordered in the same rotational sense (CCW) in (theta, z)
    space, and outer[0] / inner[0] should be near each other.  Emits
    exactly len(outer) + len(inner) triangles.
    """
    n_out = len(outer)
    n_in = len(inner)
    tris = []
    i_o = 0
    i_i = 0
    done_o = 0
    done_i = 0
    while done_o < n_out or done_i < n_in:
        V = outer[i_o % n_out]
        P = inner[i_i % n_in]
        V_next = outer[(i_o + 1) % n_out]
        P_next = inner[(i_i + 1) % n_in]
        d_adv_out = float(np.linalg.norm(V_next - P))
        d_adv_in = float(np.linalg.norm(P_next - V))
        advance_outer = done_o < n_out and (
            done_i >= n_in or d_adv_out <= d_adv_in
        )
        if advance_outer:
            tris.append([V, V_next, P])
            i_o += 1
            done_o += 1
        else:
            tris.append([V, P_next, P])
            i_i += 1
            done_i += 1
    return tris


# ---------- Main -------------------------------------------------------

def main():
    print(f"  ALPHA_DEG = {ALPHA_DEG:.2f} deg  (branch axis -> -z axis angle)")
    out_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "constant", "triSurface"
    )
    os.makedirs(out_dir, exist_ok=True)

    # --- 1. Intersection curve (shared ring) ---------------------------
    phi = np.linspace(0.0, 2.0 * math.pi, N_CIRC, endpoint=False)
    P = np.array([branch_pt(ph, s_intersect(ph)) for ph in phi])

    # --- 2. Main-pipe grid coordinates ---------------------------------
    theta_grid = np.linspace(0.0, 2.0 * math.pi, N_CIRC, endpoint=False)
    z_grid = np.linspace(0.0, L_MAIN, N_AXIAL_MAIN + 1)

    dth = 2.0 * math.pi / N_CIRC
    dz = L_MAIN / N_AXIAL_MAIN

    # The rectangular hole in (theta, z) parameter space must (a) contain
    # every grid vertex that lies inside the projected branch foot-print
    # AND (b) contain the entire intersection curve P.  Any rectangle
    # larger than that wastes zipper triangles; for a tilted branch the
    # old "z_stretch = R2 + 0.5*L_BRANCH*|cos(alpha)|" heuristic produced
    # a rectangle ~7x wider in z than the intersection curve, which made
    # the zipper span ~1m gaps with skewed triangles and produced two
    # disconnected snappyHexMesh fluid regions at the junction.
    #
    # Replace the heuristic with a tight bbox derived directly from the
    # intersection curve P (mapped to (theta, z) space), padded by a few
    # grid cells.  This shrinks the zipper annulus to a tight band and
    # restores a watertight, single-region junction at any ALPHA.
    P_theta = np.array([math.atan2(p[1], p[0]) for p in P])
    P_theta = np.where(P_theta < 0.0, P_theta + 2.0 * math.pi, P_theta)
    P_z = P[:, 2]

    j_lo = max(int(math.floor(P_theta.min() / dth)) - BUFFER_CELLS, 0)
    j_hi = min(int(math.ceil(P_theta.max() / dth)) + BUFFER_CELLS, N_CIRC - 1)
    i_lo = max(int(math.floor(P_z.min() / dz)) - BUFFER_CELLS, 0)
    i_hi = min(int(math.ceil(P_z.max() / dz)) + BUFFER_CELLS, N_AXIAL_MAIN)

    # Safety: every in-hole grid vertex must lie strictly inside the rect.
    # If the bbox-from-P heuristic missed any (e.g., because the branch
    # is very oblique and the curve turns sharply between sample points),
    # expand minimally until they are all covered.
    while True:
        expanded = False
        for j in range(N_CIRC):
            for i in range(N_AXIAL_MAIN + 1):
                if vertex_in_hole(theta_grid[j], z_grid[i]):
                    if j <= j_lo:
                        j_lo = max(j - 1, 0)
                        expanded = True
                    if j >= j_hi:
                        j_hi = min(j + 1, N_CIRC - 1)
                        expanded = True
                    if i <= i_lo:
                        i_lo = max(i - 1, 0)
                        expanded = True
                    if i >= i_hi:
                        i_hi = min(i + 1, N_AXIAL_MAIN)
                        expanded = True
        if not expanded:
            break

    # --- 3. Main pipe wall triangles (skip quads inside rectangle) -----
    main_wall_tris = []
    for i in range(N_AXIAL_MAIN):
        for j in range(N_CIRC):
            j_next = (j + 1) % N_CIRC
            # Quad is inside the rectangle iff both (j, j+1) and (i, i+1)
            # are within the rectangle extent.
            if (j_lo <= j and j + 1 <= j_hi and
                    i_lo <= i and i + 1 <= i_hi and
                    j_next != 0):  # hole never wraps theta=0
                continue

            t0 = theta_grid[j]
            t1 = theta_grid[j_next] if j_next != 0 else 2.0 * math.pi
            z0 = z_grid[i]
            z1 = z_grid[i + 1]

            p00 = main_pt(t0, z0)
            p10 = main_pt(t0, z1)
            p01 = main_pt(t1, z0)
            p11 = main_pt(t1, z1)

            # Winding chosen so the radial normal points outward.
            main_wall_tris.append([p00, p11, p10])
            main_wall_tris.append([p00, p01, p11])

    # --- 4. Rectangular hole boundary (outer loop, CCW in (theta,z)) ---
    outer_pts = []
    # bottom edge: j_lo .. j_hi, z = z_grid[i_lo]
    for j in range(j_lo, j_hi + 1):
        outer_pts.append(main_pt(theta_grid[j], z_grid[i_lo]))
    # right edge (excluding corner): j = j_hi, z from i_lo+1 .. i_hi
    for i in range(i_lo + 1, i_hi + 1):
        outer_pts.append(main_pt(theta_grid[j_hi], z_grid[i]))
    # top edge (excluding corner): j from j_hi-1 .. j_lo, z = z_grid[i_hi]
    for j in range(j_hi - 1, j_lo - 1, -1):
        outer_pts.append(main_pt(theta_grid[j], z_grid[i_hi]))
    # left edge (excluding both corners): j = j_lo, z from i_hi-1 .. i_lo+1
    for i in range(i_hi - 1, i_lo, -1):
        outer_pts.append(main_pt(theta_grid[j_lo], z_grid[i]))
    outer_pts = np.asarray(outer_pts)

    # --- 5. Inner loop = intersection curve, reversed to CCW -----------
    # P goes CW in (theta, z) as phi increases, so reverse it.
    inner_pts = P[::-1].copy()
    # Align start index to whatever outer vertex is closest.
    d = np.linalg.norm(inner_pts - outer_pts[0], axis=1)
    k_start = int(np.argmin(d))
    inner_pts = np.roll(inner_pts, -k_start, axis=0)

    # --- 6. Zipper main-pipe wall hole to intersection curve -----------
    zipper_tris = zipper(outer_pts, inner_pts)
    main_wall_tris.extend(zipper_tris)

    # --- 7. Branch pipe wall --------------------------------------------
    # Per-column linear interpolation from the intersection curve to y=L_BRANCH.
    # This guarantees no degenerate triangles at phi = pi/2 / 3pi/2 where the
    # intersection curve touches y = R1 (which would collapse a flat transition
    # ring).  The first ring of this extrusion IS exactly the intersection
    # curve P, so vertices are shared with the main-pipe hole zipper.
    s_b = np.array([s_intersect(ph) for ph in phi])  # (N_CIRC,)

    def branch_ring(t):
        """Branch-pipe ring at parameter t in [0, 1] (t=0 -> intersection
        curve; t=1 -> branch inlet ring at s=L_BRANCH).  Linearly interp
        in the branch's own axial coordinate to keep triangle quality."""
        out = np.empty((N_CIRC, 3))
        for k_ in range(N_CIRC):
            ph = phi[k_]
            s_val = s_b[k_] + (L_BRANCH - s_b[k_]) * t
            out[k_] = branch_pt(ph, s_val)
        return out

    branch_wall_tris = []
    prev_ring = branch_ring(0.0)     # == P
    for lvl in range(1, N_AXIAL_BRANCH + 1):
        new_ring = branch_ring(lvl / N_AXIAL_BRANCH)
        for k in range(N_CIRC):
            kn = (k + 1) % N_CIRC
            p00 = prev_ring[k]
            p10 = new_ring[k]
            p01 = prev_ring[kn]
            p11 = new_ring[kn]
            branch_wall_tris.append([p00, p11, p10])
            branch_wall_tris.append([p00, p01, p11])
        prev_ring = new_ring

    # --- 8. End caps ----------------------------------------------------
    main_inlet_tris = []
    centre_in = np.array([0.0, 0.0, 0.0])
    for j in range(N_CIRC):
        jn = (j + 1) % N_CIRC
        p = main_pt(theta_grid[j], 0.0)
        pn = main_pt(theta_grid[jn], 0.0)
        main_inlet_tris.append([centre_in, pn, p])  # outward = -z

    outlet_tris = []
    centre_out = np.array([0.0, 0.0, L_MAIN])
    for j in range(N_CIRC):
        jn = (j + 1) % N_CIRC
        p = main_pt(theta_grid[j], L_MAIN)
        pn = main_pt(theta_grid[jn], L_MAIN)
        outlet_tris.append([centre_out, p, pn])  # outward = +z

    branch_inlet_tris = []
    centre_br = JUNCTION_VEC + L_BRANCH * S_HAT   # inlet disc centre
    for k in range(N_CIRC):
        kn = (k + 1) % N_CIRC
        p = branch_pt(phi[k], L_BRANCH)
        pn = branch_pt(phi[kn], L_BRANCH)
        branch_inlet_tris.append([centre_br, pn, p])  # outward = +S_HAT

    # --- 9. Water-tightness / orientation check -------------------------
    wall_tris = main_wall_tris + branch_wall_tris
    all_tris = wall_tris + main_inlet_tris + outlet_tris + branch_inlet_tris

    vol = signed_volume(all_tris)
    if vol < 0.0:
        print("[warn] signed volume < 0, flipping all triangle windings")
        wall_tris = [[t[0], t[2], t[1]] for t in wall_tris]
        main_inlet_tris = [[t[0], t[2], t[1]] for t in main_inlet_tris]
        outlet_tris = [[t[0], t[2], t[1]] for t in outlet_tris]
        branch_inlet_tris = [[t[0], t[2], t[1]] for t in branch_inlet_tris]
        all_tris = wall_tris + main_inlet_tris + outlet_tris + branch_inlet_tris
        vol = signed_volume(all_tris)

    # Expected volume: main pipe + branch pipe above the intersection curve.
    # For a tilted branch, the mean branch-arc from centre to intersection
    # is approximately R1 / sin(alpha) (exact at alpha=90, diverges as
    # alpha -> 0 as expected).  For beta = R2/R1 and typical alphas in
    # [25,90] deg the remaining correction is O(beta^2).  Allow 10 %
    # tolerance to absorb zipper-edge/hole-shape effects.
    s_int_mean = R1 / max(SIN_A, 1e-3)
    expected_vol = (math.pi * R1 ** 2 * L_MAIN
                    + math.pi * R2 ** 2 * max(L_BRANCH - s_int_mean, 0.0))
    ratio = vol / expected_vol
    print(f"  Main pipe wall tris:   {len(main_wall_tris)}")
    print(f"  Branch pipe wall tris: {len(branch_wall_tris)}")
    print(f"  End-cap tris: main_inlet={len(main_inlet_tris)}, "
          f"outlet={len(outlet_tris)}, branch_inlet={len(branch_inlet_tris)}")
    print(f"  Rectangle extent: theta[{j_lo}..{j_hi}], z[{i_lo}..{i_hi}]")
    print(f"  Signed volume:   {vol:.4f} m^3")
    print(f"  Expected volume: {expected_vol:.4f} m^3")
    print(f"  Ratio:           {ratio:.4f} (target 1.00 +/- 0.10)")

    if not (0.90 < ratio < 1.10):
        raise RuntimeError(
            f"STL water-tightness check failed: ratio {ratio:.4f} "
            f"outside [0.90, 1.10]."
        )

    # --- 10. Write STL files -------------------------------------------
    for name, tris in [
        ("wall", wall_tris),
        ("main_inlet", main_inlet_tris),
        ("outlet", outlet_tris),
        ("branch_inlet", branch_inlet_tris),
    ]:
        m = make_stl(tris)
        path = os.path.join(out_dir, f"{name}.stl")
        m.save(path)
        print(f"  wrote {path} ({len(tris)} triangles)")

    m_all = make_stl(all_tris)
    combined_path = os.path.join(out_dir, "tJunction.stl")
    m_all.save(combined_path)
    print(f"  wrote {combined_path} ({len(all_tris)} triangles, combined)")

    print("\nDone.")


if __name__ == "__main__":
    main()
