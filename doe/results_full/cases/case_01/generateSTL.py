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


def branch_pt(phi, y):
    """Point on the branch-pipe surface at axial coordinate y."""
    return np.array([R2 * math.cos(phi), y, Z_JCT + R2 * math.sin(phi)])


def y_intersect(phi):
    """y of the branch/main intersection curve at branch angle phi."""
    return math.sqrt(max(R1 * R1 - R2 * R2 * math.cos(phi) ** 2, 0.0))


def vertex_in_hole(theta, z):
    """True if main-pipe vertex lies inside the branch-pipe cylinder."""
    x = R1 * math.cos(theta)
    y = R1 * math.sin(theta)
    return y > 0.0 and x * x + (z - Z_JCT) ** 2 < R2 * R2


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
    out_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "constant", "triSurface"
    )
    os.makedirs(out_dir, exist_ok=True)

    # --- 1. Intersection curve (shared ring) ---------------------------
    phi = np.linspace(0.0, 2.0 * math.pi, N_CIRC, endpoint=False)
    P = np.array([branch_pt(ph, y_intersect(ph)) for ph in phi])

    # --- 2. Main-pipe grid coordinates ---------------------------------
    theta_grid = np.linspace(0.0, 2.0 * math.pi, N_CIRC, endpoint=False)
    z_grid = np.linspace(0.0, L_MAIN, N_AXIAL_MAIN + 1)

    dth = 2.0 * math.pi / N_CIRC
    dz = L_MAIN / N_AXIAL_MAIN

    theta_min_hole = math.acos(R2 / R1)
    theta_max_hole = math.pi - theta_min_hole
    z_min_hole = Z_JCT - R2
    z_max_hole = Z_JCT + R2

    j_lo = max(int(math.floor(theta_min_hole / dth)) - BUFFER_CELLS, 0)
    j_hi = min(int(math.ceil(theta_max_hole / dth)) + BUFFER_CELLS, N_CIRC - 1)
    i_lo = max(int(math.floor(z_min_hole / dz)) - BUFFER_CELLS, 0)
    i_hi = min(int(math.ceil(z_max_hole / dz)) + BUFFER_CELLS, N_AXIAL_MAIN)

    # Safety: expand until every hole vertex is strictly inside the rect.
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
    y_b = np.array([y_intersect(ph) for ph in phi])  # (N_CIRC,)
    cos_phi = np.cos(phi)
    sin_phi = np.sin(phi)
    x_ring = R2 * cos_phi
    z_ring = Z_JCT + R2 * sin_phi

    def branch_ring(t):
        """Branch-pipe ring at parameter t in [0, 1] (t=0 -> intersection
        curve; t=1 -> branch inlet ring at y=L_BRANCH)."""
        y = y_b + (L_BRANCH - y_b) * t
        return np.stack([x_ring, y, z_ring], axis=1)

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
    centre_br = np.array([0.0, L_BRANCH, Z_JCT])
    for k in range(N_CIRC):
        kn = (k + 1) % N_CIRC
        p = branch_pt(phi[k], L_BRANCH)
        pn = branch_pt(phi[kn], L_BRANCH)
        branch_inlet_tris.append([centre_br, pn, p])  # outward = +y

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

    # Expected volume: main pipe minus the branch-pipe "plug" occupying the
    # upper-half region, plus the actual branch pipe above the intersection
    # curve.  For beta = R2/R1 = 0.25, the corrections are small; use the
    # straightforward estimate and allow a 3% tolerance.
    expected_vol = (math.pi * R1 ** 2 * L_MAIN
                    + math.pi * R2 ** 2 * (L_BRANCH - R1))
    ratio = vol / expected_vol
    print(f"  Main pipe wall tris:   {len(main_wall_tris)}")
    print(f"  Branch pipe wall tris: {len(branch_wall_tris)}")
    print(f"  End-cap tris: main_inlet={len(main_inlet_tris)}, "
          f"outlet={len(outlet_tris)}, branch_inlet={len(branch_inlet_tris)}")
    print(f"  Rectangle extent: theta[{j_lo}..{j_hi}], z[{i_lo}..{i_hi}]")
    print(f"  Signed volume:   {vol:.4f} m^3")
    print(f"  Expected volume: {expected_vol:.4f} m^3")
    print(f"  Ratio:           {ratio:.4f} (target 1.00 +/- 0.03)")

    if not (0.97 < ratio < 1.03):
        raise RuntimeError(
            f"STL water-tightness check failed: ratio {ratio:.4f} "
            f"outside [0.97, 1.03]."
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
