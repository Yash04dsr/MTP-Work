#!/usr/bin/env python3
"""
Generate a T-junction STL for snappyHexMesh.

Geometry (all dimensions in metres):
  Main pipe:   d1 = 0.460 m, length = 9.200 m, axis along Z
  Branch pipe: d2 = 0.115 m (beta=0.25), 90-deg injection at Z = 4.600 m
               Branch axis along +Y, length = 10*d2 + clearance = 1.380 m

The STL contains three named solid regions:
  main_inlet, branch_inlet, outlet, wall
so that snappyHexMesh can assign boundary patches directly.

Requires: numpy, numpy-stl  (pip install numpy-stl)
"""

import numpy as np
from stl import mesh as stlmesh
import os, math

# ── geometry parameters ──────────────────────────────────────────────
D1 = 0.460           # main pipe diameter [m]
R1 = D1 / 2.0
L_MAIN = 9.200       # main pipe length [m]
Z_JCT = 4.600        # junction location along Z

D2 = 0.115           # branch diameter [m]
R2 = D2 / 2.0
L_BRANCH = 1.380     # branch length along +Y (≥ 10*d2)

N_CIRC = 64          # circumferential facets per circle
N_AXIAL_MAIN = 200   # axial divisions along main pipe
N_AXIAL_BRANCH = 40  # axial divisions along branch


def cylinder_tris(origin, axis, radius, length, n_circ, n_ax,
                  cap_start=False, cap_end=False):
    """Return (N,3,3) array of triangle vertices for a cylinder."""
    tris = []
    ax = np.array(axis, dtype=float)
    ax /= np.linalg.norm(ax)

    if np.allclose(np.abs(ax), [1, 0, 0]):
        perp = np.cross(ax, [0, 1, 0])
    else:
        perp = np.cross(ax, [1, 0, 0])
    perp /= np.linalg.norm(perp)
    perp2 = np.cross(ax, perp)

    o = np.array(origin, dtype=float)

    for i in range(n_ax):
        z0 = length * i / n_ax
        z1 = length * (i + 1) / n_ax
        for j in range(n_circ):
            t0 = 2 * math.pi * j / n_circ
            t1 = 2 * math.pi * (j + 1) / n_circ
            c0, s0 = math.cos(t0), math.sin(t0)
            c1, s1 = math.cos(t1), math.sin(t1)

            p00 = o + ax * z0 + radius * (perp * c0 + perp2 * s0)
            p10 = o + ax * z1 + radius * (perp * c0 + perp2 * s0)
            p01 = o + ax * z0 + radius * (perp * c1 + perp2 * s1)
            p11 = o + ax * z1 + radius * (perp * c1 + perp2 * s1)

            tris.append([p00, p10, p11])
            tris.append([p00, p11, p01])

    if cap_start:
        centre = o.copy()
        for j in range(n_circ):
            t0 = 2 * math.pi * j / n_circ
            t1 = 2 * math.pi * (j + 1) / n_circ
            p0 = o + radius * (perp * math.cos(t0) + perp2 * math.sin(t0))
            p1 = o + radius * (perp * math.cos(t1) + perp2 * math.sin(t1))
            tris.append([centre, p1, p0])

    if cap_end:
        centre = o + ax * length
        for j in range(n_circ):
            t0 = 2 * math.pi * j / n_circ
            t1 = 2 * math.pi * (j + 1) / n_circ
            p0 = centre + radius * (perp * math.cos(t0) + perp2 * math.sin(t0))
            p1 = centre + radius * (perp * math.cos(t1) + perp2 * math.sin(t1))
            tris.append([centre, p0, p1])

    return np.array(tris)


def make_stl_mesh(tris):
    """Convert (N,3,3) vertex array to numpy-stl mesh object."""
    m = stlmesh.Mesh(np.zeros(len(tris), dtype=stlmesh.Mesh.dtype))
    for i, tri in enumerate(tris):
        m.vectors[i] = tri
    return m


def main():
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "constant", "triSurface")
    os.makedirs(out_dir, exist_ok=True)

    # ── main pipe wall (no end caps — those become inlet/outlet) ─────
    wall_main = cylinder_tris(
        origin=[0, 0, 0], axis=[0, 0, 1],
        radius=R1, length=L_MAIN,
        n_circ=N_CIRC, n_ax=N_AXIAL_MAIN)

    # ── branch pipe wall ─────────────────────────────────────────────
    branch_origin = [0, R1, Z_JCT]
    wall_branch = cylinder_tris(
        origin=branch_origin, axis=[0, 1, 0],
        radius=R2, length=L_BRANCH - R1,
        n_circ=N_CIRC, n_ax=N_AXIAL_BRANCH)

    # ── inlet cap (Z = 0) ───────────────────────────────────────────
    inlet_main = cylinder_tris(
        origin=[0, 0, 0], axis=[0, 0, 1],
        radius=R1, length=0,
        n_circ=N_CIRC, n_ax=0,
        cap_start=True)

    # ── outlet cap (Z = L_MAIN) ─────────────────────────────────────
    outlet_cap = cylinder_tris(
        origin=[0, 0, L_MAIN], axis=[0, 0, 1],
        radius=R1, length=0,
        n_circ=N_CIRC, n_ax=0,
        cap_start=True)

    # ── branch inlet cap (Y = R1 + L_BRANCH - R1 = L_BRANCH) ───────
    branch_cap_centre = [0, L_BRANCH, Z_JCT]
    inlet_branch = cylinder_tris(
        origin=branch_cap_centre, axis=[0, 1, 0],
        radius=R2, length=0,
        n_circ=N_CIRC, n_ax=0,
        cap_start=True)

    # ── combine wall surfaces ────────────────────────────────────────
    wall_all = np.concatenate([wall_main, wall_branch])

    # ── write separate STL files per region ──────────────────────────
    for name, tris in [("wall", wall_all),
                       ("main_inlet", inlet_main),
                       ("outlet", outlet_cap),
                       ("branch_inlet", inlet_branch)]:
        m = make_stl_mesh(tris)
        path = os.path.join(out_dir, f"{name}.stl")
        m.save(path)
        print(f"  wrote {path}  ({len(tris)} triangles)")

    # ── also write a single combined STL for snappyHexMesh ───────────
    all_tris = np.concatenate([wall_all, inlet_main, outlet_cap, inlet_branch])
    m_all = make_stl_mesh(all_tris)
    combined_path = os.path.join(out_dir, "tJunction.stl")
    m_all.save(combined_path)
    print(f"  wrote {combined_path}  ({len(all_tris)} triangles, combined)")

    print("\nDone. STL files in:", out_dir)


if __name__ == "__main__":
    main()
