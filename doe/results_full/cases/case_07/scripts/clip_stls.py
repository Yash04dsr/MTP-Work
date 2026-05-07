#!/usr/bin/env python3
"""
Clip every *.stl in constant/triSurface/ to the half-space x >= CLIP_X
(default 0.0) so they match a half-domain blockMesh that also starts
at x = CLIP_X.  Without this, snappyHexMesh silently drops patches
whose STL lies outside the background mesh (notably branch_inlet).

Binary STL in, binary STL out.  Idempotent: re-running on an already-
clipped file is a no-op (up to numerical tolerance).
"""
import os
import struct
import sys
from pathlib import Path

import numpy as np

CLIP_X = float(os.environ.get('CLIP_X', '0.0'))
AXIS = 0  # x
EPS = 1e-9


def read_binary_stl(path):
    with open(path, 'rb') as f:
        f.read(80)
        n = struct.unpack('<I', f.read(4))[0]
        tris = np.empty((n, 3, 3), dtype=np.float64)
        for i in range(n):
            f.read(12)
            for j in range(3):
                tris[i, j] = struct.unpack('<3f', f.read(12))
            f.read(2)
    return tris


def write_binary_stl(path, tris):
    n = len(tris)
    with open(path, 'wb') as f:
        f.write(b'clipped x>=%.3f' % CLIP_X + b' ' * 80)
        f.seek(80)
        f.write(struct.pack('<I', n))
        for tri in tris:
            a, b, c = tri
            n_vec = np.cross(b - a, c - a)
            norm = np.linalg.norm(n_vec)
            if norm > EPS:
                n_vec /= norm
            f.write(struct.pack('<3f', *n_vec))
            for v in (a, b, c):
                f.write(struct.pack('<3f', *v))
            f.write(b'\x00\x00')


def clip_triangle(tri, x0):
    d = tri[:, AXIS] - x0
    inside = d >= -EPS
    n_in = int(np.sum(inside))
    if n_in == 3:
        return [tri]
    if n_in == 0:
        return []
    verts = [tri[i] for i in range(3)]
    dists = [d[i] for i in range(3)]

    def interp(pa, pb, da, db):
        t = da / (da - db)
        return pa + t * (pb - pa)

    if n_in == 1:
        i = int(np.argmax(inside))
        vi = verts[i]; vj = verts[(i + 1) % 3]; vk = verts[(i + 2) % 3]
        di = dists[i]; dj = dists[(i + 1) % 3]; dk = dists[(i + 2) % 3]
        pj = interp(vi, vj, di, dj)
        pk = interp(vi, vk, di, dk)
        return [np.array([vi, pj, pk])]
    # n_in == 2
    i = int(np.argmin(inside))  # the single outside vertex
    vi = verts[i]; vj = verts[(i + 1) % 3]; vk = verts[(i + 2) % 3]
    di = dists[i]; dj = dists[(i + 1) % 3]; dk = dists[(i + 2) % 3]
    pij = interp(vj, vi, dj, di)
    pik = interp(vk, vi, dk, di)
    return [np.array([vj, vk, pij]), np.array([vk, pik, pij])]


def clip_stl(path, x0):
    tris = read_binary_stl(path)
    kept = []
    for t in tris:
        kept.extend(clip_triangle(t, x0))
    if not kept:
        print(f'  WARNING {path.name}: empty after clip (nothing at x>={x0}); leaving original')
        return
    kept = np.array(kept)
    write_binary_stl(path, kept)
    bb = kept.reshape(-1, 3)
    print(f'  {path.name:22s} tris {len(tris):5d} -> {len(kept):5d}  '
          f'x=[{bb[:,0].min():+.4f},{bb[:,0].max():+.4f}]  '
          f'y=[{bb[:,1].min():+.4f},{bb[:,1].max():+.4f}]  '
          f'z=[{bb[:,2].min():+.4f},{bb[:,2].max():+.4f}]')


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else 'constant/triSurface')
    if not root.is_dir():
        print(f'ERROR: {root} not found', file=sys.stderr); sys.exit(1)
    print(f'[clip_stls] clipping STLs in {root} to x >= {CLIP_X}')
    for stl in sorted(root.glob('*.stl')):
        clip_stl(stl, CLIP_X)


if __name__ == '__main__':
    main()
