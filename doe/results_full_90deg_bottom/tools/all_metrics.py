#!/usr/bin/env python3
"""
all_metrics.py
==============
Comprehensive, retro-active post-processor for a T-junction mixing case.

From the reconstructed boundary-field data already on disk, computes at
`main_inlet` and `outlet`:

    Mixing (at outlet)
    ------------------
      - ⟨Y_H2⟩              with area, mass-flux, and volume-flux weights
      - σ_H2                 with the same three weights
      - CoV = σ / ⟨Y_H2⟩     (three weights)
      - Danckwerts intensity of segregation I_s = σ² / (⟨Y⟩ (1-⟨Y⟩))
                             (three weights)

    Pressure drop (inlet − outlet)
    ------------------------------
      - static       p
      - static-gauge p_rgh
      - total        p_tot  = p     + ½ ρ |U|²
      - total-gauge  p_rgh_tot = p_rgh + ½ ρ |U|²
      each with area, mass-flux, and volume-flux weighting → 12 ΔP values

    Mass balance
    ------------
      - ṁ at main_inlet, branch_inlet, outlet (directly integrated)
      - closure error and % deviation

All snapshot rows + a time-averaged row are written to `all_metrics.csv`
in <outdir>; a human-readable Markdown summary goes to `ALL_METRICS.md`.

Usage
-----
    python3 all_metrics.py <case_dir> [--times t1 t2 ...]
                                      [--outdir <dir>]

If --times is omitted, auto-detects all numeric-named snapshot dirs with
t >= 0.8 s and uses them.

Designed to be dependency-light: only numpy required.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

import numpy as np


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MW_H2  = 2.016e-3   # kg/mol
MW_CH4 = 16.043e-3  # kg/mol
R_UNI  = 8.31446    # J/(mol·K)


# ---------------------------------------------------------------------------
# OpenFOAM ASCII parsers
# ---------------------------------------------------------------------------
_HEADER_END = re.compile(r'//[\s\*]+//')


def _strip_header(txt: str) -> str:
    m = _HEADER_END.search(txt)
    return txt[m.end():] if m else txt


def parse_boundary(bdy_path: Path) -> dict[str, tuple[int, int]]:
    """Return {patch_name: (nFaces, startFace)}."""
    raw = _strip_header(bdy_path.read_text())
    m = re.search(r'\d+\s*\(', raw)
    body = raw[m.end():]
    out = {}
    for pm in re.finditer(r'(\w+)\s*\{([^{}]*)\}', body):
        name = pm.group(1)
        block = pm.group(2)
        mn = re.search(r'nFaces\s+(\d+)', block)
        sm = re.search(r'startFace\s+(\d+)', block)
        if mn and sm:
            out[name] = (int(mn.group(1)), int(sm.group(1)))
    return out


def parse_points(pts_path: Path) -> np.ndarray:
    raw = _strip_header(pts_path.read_text())
    m = re.search(r'(\d+)\s*\(', raw)
    n = int(m.group(1))
    body = raw[m.end():]
    # Outer closing paren
    end = body.rfind(')')
    body = body[:end]
    cleaned = body.translate(str.maketrans('()', '  '))
    arr = np.fromstring(cleaned, sep=' ', dtype=np.float64)
    return arr[: n * 3].reshape(n, 3)


def parse_faces_range(faces_path: Path, start: int, count: int) -> list[list[int]]:
    """Parse faces in [start, start+count) from an OpenFOAM ASCII faces file.

    The faces file has format:
        <total>\n(\n
        <K>(v0 v1 ... v_{K-1})\n
        ...
        )\n
    Where the count and opening paren may be on separate lines. We read the
    whole file (usually a few tens of MB), strip the header, and iterate
    face matches with regex until we reach the requested range.
    """
    raw = _strip_header(faces_path.read_text())
    m = re.search(r'(\d+)\s*\(', raw)
    if not m:
        raise ValueError("Could not find faces list opening")
    body = raw[m.end():]
    faces: list[list[int]] = []
    idx = 0
    face_re = re.compile(r'(\d+)\s*\(([^)]+)\)')
    for fm in face_re.finditer(body):
        if idx >= start:
            K = int(fm.group(1))
            verts = [int(x) for x in fm.group(2).split()[:K]]
            faces.append(verts)
            if len(faces) >= count:
                break
        idx += 1
    return faces


def _extract_patch_block(raw: str, patch_name: str) -> str:
    """Return the contents of the named patch block inside boundaryField {...}."""
    m = re.search(r'boundaryField\s*\{', raw)
    if not m:
        raise KeyError(f"boundaryField not found")
    start = m.end()
    pat = re.compile(r'\n\s*' + re.escape(patch_name) + r'\s*\n?\s*\{')
    pm = pat.search(raw, start)
    if not pm:
        raise KeyError(f"patch {patch_name} not found")
    i = pm.end()
    depth = 1
    while i < len(raw) and depth > 0:
        c = raw[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
        i += 1
    return raw[pm.end(): i - 1]


def parse_patch_scalar(field_path: Path, patch_name: str, n_faces: int) -> np.ndarray:
    """Require the `value` keyword specifically, to avoid picking up
    `gradient` / other keywords from BCs such as fixedFluxPressure."""
    raw = field_path.read_text()
    block = _extract_patch_block(raw, patch_name)

    mn = re.search(
        r'\bvalue\s+nonuniform\s+List<scalar>\s+(\d+)\s*\(',
        block,
    )
    if mn:
        n = int(mn.group(1))
        body = block[mn.end():]
        end = body.find(')')
        vals = np.fromstring(body[:end], sep=' ', dtype=np.float64)
        return vals[:n]

    mu = re.search(r'\bvalue\s+uniform\s+([-\d.eE+]+)', block)
    if mu:
        return np.full(n_faces, float(mu.group(1)))

    # BC has no `value` keyword written (e.g. zeroGradient without value).
    # Return NaN and let the caller mark the metric as unavailable.
    return np.full(n_faces, float('nan'))


def parse_patch_vector(field_path: Path, patch_name: str, n_faces: int) -> np.ndarray:
    raw = field_path.read_text()
    block = _extract_patch_block(raw, patch_name)

    mn = re.search(r'\bvalue\s+nonuniform\s+List<vector>\s+(\d+)\s*\(', block)
    if mn:
        n = int(mn.group(1))
        body = block[mn.end():]
        triplets = re.findall(
            r'\(\s*([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s*\)',
            body,
        )
        arr = np.array(triplets[:n], dtype=np.float64)
        return arr

    mu = re.search(
        r'\bvalue\s+uniform\s+\(\s*([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s*\)',
        block,
    )
    if mu:
        v = np.array([float(mu.group(i + 1)) for i in range(3)])
        return np.tile(v, (n_faces, 1))

    return np.full((n_faces, 3), float('nan'))


# ---------------------------------------------------------------------------
# Patch geometry
# ---------------------------------------------------------------------------
def face_geometry(pts: np.ndarray, faces: list[list[int]]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Return (S, A, C) where
      S: (N,3) face area vector (outward normal × area)
      A: (N,)  face area magnitude
      C: (N,3) face centroid
    Uses fan triangulation from vertex 0.
    """
    N = len(faces)
    S = np.zeros((N, 3))
    A = np.zeros(N)
    C = np.zeros((N, 3))
    for i, face in enumerate(faces):
        fp = pts[face]               # (K,3)
        p0 = fp[0]
        acc_s = np.zeros(3)
        acc_a = 0.0
        acc_c = np.zeros(3)
        for j in range(1, len(face) - 1):
            p1 = fp[j]
            p2 = fp[j + 1]
            cross = np.cross(p1 - p0, p2 - p0)
            tri_s = 0.5 * cross
            tri_a = 0.5 * np.linalg.norm(cross)
            acc_s += tri_s
            acc_a += tri_a
            acc_c += tri_a * (p0 + p1 + p2) / 3.0
        S[i] = acc_s
        A[i] = acc_a
        C[i] = acc_c / acc_a if acc_a > 0 else p0
    return S, A, C


# ---------------------------------------------------------------------------
# Per-snapshot metrics
# ---------------------------------------------------------------------------
def weighted_stats(vals: np.ndarray, w: np.ndarray) -> tuple[float, float, float]:
    W = w.sum()
    if W <= 0:
        return float('nan'), float('nan'), float('nan')
    mean = float((vals * w).sum() / W)
    var = float(((vals - mean) ** 2 * w).sum() / W)
    var = max(var, 0.0)
    return mean, var, math.sqrt(var)


def rho_ideal(Y_H2: np.ndarray, Y_CH4: np.ndarray, T: np.ndarray, p: np.ndarray) -> np.ndarray:
    # Mixture molar mass; assume Y_H2 + Y_CH4 sum ≈ 1 (binary mixture in this study).
    denom = np.clip(Y_H2 / MW_H2 + Y_CH4 / MW_CH4, 1e-30, None)
    MW_mix = 1.0 / denom
    R_mix = R_UNI / MW_mix
    return p / (R_mix * T)


def process_snapshot(case: Path, time_dir: str, patches: dict, patch_geom: dict) -> dict:
    results: dict = {}
    tdir = case / time_dir

    # Read all required patch fields for main_inlet and outlet
    data = {}
    for pname, (n, _s) in patches.items():
        if pname not in ('main_inlet', 'outlet', 'branch_inlet'):
            continue
        data[pname] = {
            'H2':    parse_patch_scalar(tdir / 'H2',    pname, n),
            'CH4':   parse_patch_scalar(tdir / 'CH4',   pname, n),
            'T':     parse_patch_scalar(tdir / 'T',     pname, n),
            'p':     parse_patch_scalar(tdir / 'p',     pname, n),
            'p_rgh': parse_patch_scalar(tdir / 'p_rgh', pname, n),
            'U':     parse_patch_vector(tdir / 'U',     pname, n),
        }

    # Build per-patch geometry-derived quantities
    derived = {}
    for pname, d in data.items():
        S, A, _C = patch_geom[pname]
        n_hat = S / np.clip(np.linalg.norm(S, axis=1, keepdims=True), 1e-30, None)
        Un = (d['U'] * n_hat).sum(axis=1)
        Umag = np.linalg.norm(d['U'], axis=1)
        rho = rho_ideal(d['H2'], d['CH4'], d['T'], d['p'])
        mdot = rho * Un * A          # kg/s per face, signed (out of domain = +)
        Qf   = Un * A                # m^3/s per face, signed
        p_tot    = d['p']     + 0.5 * rho * Umag ** 2
        prgh_tot = d['p_rgh'] + 0.5 * rho * Umag ** 2
        derived[pname] = {
            'A': A, 'n': n_hat, 'Un': Un, 'Umag': Umag, 'rho': rho,
            'mdot': mdot, 'Qf': Qf,
            'p_tot': p_tot, 'prgh_tot': prgh_tot,
        }

    # ---- Mixing stats at outlet (3 weightings) ----
    do = derived['outlet']
    do_h2 = data['outlet']['H2']
    weights = {
        'area': do['A'],
        'mass': np.abs(do['mdot']),
        'vol':  np.abs(do['Qf']),
    }
    for wname, w in weights.items():
        m, v, s = weighted_stats(do_h2, w)
        results[f'H2_mean_{wname}']  = m
        results[f'H2_std_{wname}']   = s
        results[f'H2_CoV_{wname}']   = s / m if m > 0 else float('nan')
        results[f'H2_Is_{wname}']    = v / (m * (1 - m)) if 0.0 < m < 1.0 else float('nan')

    # ---- Pressure stats on both patches (4 pressure types × 3 weightings) ----
    for pname in ('main_inlet', 'outlet'):
        d = data[pname]
        dv = derived[pname]
        ws = {
            'area': dv['A'],
            'mass': np.abs(dv['mdot']),
            'vol':  np.abs(dv['Qf']),
        }
        fields = {
            'p':            d['p'],
            'p_rgh':        d['p_rgh'],
            'p_total':      dv['p_tot'],
            'p_rgh_total':  dv['prgh_tot'],
        }
        for pfield, arr in fields.items():
            for wname, w in ws.items():
                mean, _v, _s = weighted_stats(arr, w)
                results[f'{pfield}_{pname}_{wname}'] = mean

    # ---- ΔP (inlet − outlet) for every combination ----
    for pfield in ('p', 'p_rgh', 'p_total', 'p_rgh_total'):
        for wname in ('area', 'mass', 'vol'):
            pin  = results[f'{pfield}_main_inlet_{wname}']
            pout = results[f'{pfield}_outlet_{wname}']
            results[f'dP_{pfield}_{wname}'] = pin - pout

    # ---- Mass balance ----
    mdot_main   = float(derived['main_inlet']['mdot'].sum())    # should be negative
    mdot_out    = float(derived['outlet']['mdot'].sum())        # should be positive
    mdot_branch = float(derived['branch_inlet']['mdot'].sum()) if 'branch_inlet' in derived else 0.0
    results['mdot_main_inlet']   = mdot_main
    results['mdot_branch_inlet'] = mdot_branch
    results['mdot_outlet']       = mdot_out
    results['mdot_balance_err']  = mdot_out + mdot_main + mdot_branch
    results['mdot_balance_pct']  = (
        100.0 * results['mdot_balance_err'] / abs(mdot_out) if mdot_out != 0 else float('nan')
    )

    return results


# ---------------------------------------------------------------------------
# Main driver
# ---------------------------------------------------------------------------
def parse_datfile(path: Path, t_min: float = 0.8) -> tuple[np.ndarray, np.ndarray]:
    """Parse an OpenFOAM function-object .dat file: time, value columns.
    Skips comment lines; returns (t, v) arrays filtered to t >= t_min.
    """
    ts, vs = [], []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            try:
                t = float(parts[0])
                v = float(parts[-1])
            except ValueError:
                continue
            ts.append(t)
            vs.append(v)
    t = np.array(ts)
    v = np.array(vs)
    mask = t >= t_min
    return t[mask], v[mask]


def find_fo_datfile(case: Path, func_name: str) -> Path | None:
    """Find the newest non-empty .dat file under postProcessing/<func_name>/*/.
    File names are usually `surfaceFieldValue.dat` or similar; we just take
    the newest non-empty one."""
    root = case / 'postProcessing' / func_name
    if not root.is_dir():
        return None
    candidates = []
    for t_dir in root.iterdir():
        if not t_dir.is_dir():
            continue
        for f in t_dir.iterdir():
            if f.is_file() and f.suffix == '.dat' and f.stat().st_size > 0:
                candidates.append(f)
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def timeseries_metrics(case: Path, t_min: float = 0.8) -> dict:
    """Extract time-averaged metrics from OpenFOAM function-object .dat files.

    Covers the area-weighted inlet/outlet pressure, outlet H2, and (if
    available) the mass flux at outlet / inlet — sampled every timestep.
    """
    out = {}
    probes = [
        ('p_rgh_inlet',     'p_rgh_inlet'),
        ('p_rgh_outlet',    'p_rgh_outlet'),
        ('H2_outletAvg',    'H2_outletAvg'),
        ('outletFlux',      'outletFlux'),
        ('inletOutletFlux', 'inletOutletFlux'),
    ]
    for key, fo_name in probes:
        fpath = find_fo_datfile(case, fo_name)
        if fpath is None:
            out[f'{key}_ts_n'] = 0
            out[f'{key}_ts_mean'] = float('nan')
            continue
        t, v = parse_datfile(fpath, t_min=t_min)
        if len(v) == 0:
            out[f'{key}_ts_n'] = 0
            out[f'{key}_ts_mean'] = float('nan')
            continue
        out[f'{key}_ts_n'] = int(len(v))
        out[f'{key}_ts_mean'] = float(v.mean())
        out[f'{key}_ts_std']  = float(v.std())
        out[f'{key}_ts_tmin'] = float(t.min())
        out[f'{key}_ts_tmax'] = float(t.max())
    # Clean ΔP from time series (area-weighted static-gauge p_rgh)
    if not math.isnan(out.get('p_rgh_inlet_ts_mean', float('nan'))) and \
       not math.isnan(out.get('p_rgh_outlet_ts_mean', float('nan'))):
        out['dP_prgh_area_ts'] = out['p_rgh_inlet_ts_mean'] - out['p_rgh_outlet_ts_mean']
    return out


def cov_on_timeavg_field(case: Path, times: list[str], patches: dict, patch_geom: dict) -> dict:
    """Compute CoV on the time-averaged H2 face field across snapshots.

    This separates mixing (persistent spatial variance of the mean field)
    from acoustic / turbulent temporal fluctuation, which is the standard
    practice in RANS-derived mixing metrics.
    """
    out_n, _ = patches['outlet']
    S_out, A_out, _ = patch_geom['outlet']
    n_hat = S_out / np.clip(np.linalg.norm(S_out, axis=1, keepdims=True), 1e-30, None)

    # Build time-averaged face arrays
    h2_sum = np.zeros(out_n)
    U_sum  = np.zeros((out_n, 3))
    rho_sum = np.zeros(out_n)
    for t in times:
        tdir = case / t
        h2  = parse_patch_scalar(tdir / 'H2',    'outlet', out_n)
        ch4 = parse_patch_scalar(tdir / 'CH4',   'outlet', out_n)
        T   = parse_patch_scalar(tdir / 'T',     'outlet', out_n)
        p   = parse_patch_scalar(tdir / 'p',     'outlet', out_n)
        U   = parse_patch_vector(tdir / 'U',     'outlet', out_n)
        rho = rho_ideal(h2, ch4, T, p)
        h2_sum  += h2
        U_sum   += U
        rho_sum += rho
    N = len(times)
    h2_avg  = h2_sum  / N
    U_avg   = U_sum   / N
    rho_avg = rho_sum / N
    Un_avg  = (U_avg * n_hat).sum(axis=1)
    mdot_avg = rho_avg * Un_avg * A_out
    Qf_avg   = Un_avg * A_out

    out = {}
    for wname, w in (
        ('area', A_out),
        ('mass', np.abs(mdot_avg)),
        ('vol',  np.abs(Qf_avg)),
    ):
        m, v, s = weighted_stats(h2_avg, w)
        out[f'H2_mean_{wname}_tavg']  = m
        out[f'H2_std_{wname}_tavg']   = s
        out[f'H2_CoV_{wname}_tavg']   = s / m if m > 0 else float('nan')
        out[f'H2_Is_{wname}_tavg']    = v / (m * (1 - m)) if 0.0 < m < 1.0 else float('nan')
    return out


def run(case_dir: str, times: list[str] | None, outdir: str | None) -> None:
    case = Path(case_dir).expanduser().resolve()
    out = Path(outdir).expanduser().resolve() if outdir else case
    out.mkdir(parents=True, exist_ok=True)

    print(f"\n==== all_metrics.py ====")
    print(f"case : {case}")
    print(f"out  : {out}")

    polyMesh = case / 'constant' / 'polyMesh'
    print("Parsing boundary ...")
    patches = parse_boundary(polyMesh / 'boundary')
    print(f"  patches: {list(patches.keys())}")

    # Auto-detect snapshot times
    if not times:
        found = []
        for d in case.iterdir():
            if d.is_dir():
                try:
                    t = float(d.name)
                    if t >= 0.8 and (d / 'U').exists():
                        found.append((t, d.name))
                except ValueError:
                    pass
        found.sort()
        times = [name for _, name in found]
    print(f"  snapshots: {times}")
    if not times:
        print("  no snapshot dirs found")
        sys.exit(1)

    print("Parsing points ...")
    pts = parse_points(polyMesh / 'points')
    print(f"  {len(pts)} points")

    patch_geom = {}
    for pname in ('main_inlet', 'outlet', 'branch_inlet'):
        if pname not in patches:
            continue
        n, s = patches[pname]
        print(f"Parsing faces for {pname}: {n} faces starting at index {s} ...")
        faces = parse_faces_range(polyMesh / 'faces', s, n)
        S, A, C = face_geometry(pts, faces)
        patch_geom[pname] = (S, A, C)
        print(f"  total area = {A.sum():.5f} m²,  mean face area = {A.mean():.3e}")

    rows = []
    for t in times:
        print(f"\n-- time {t} --")
        row = {'time': float(t)}
        row.update(process_snapshot(case, t, patches, patch_geom))
        rows.append(row)

    # Time-averaged row (arithmetic mean of snapshot rows)
    keys = list(rows[0].keys())
    avg = {}
    for k in keys:
        if k == 'time':
            continue
        vals = [r[k] for r in rows if isinstance(r[k], (int, float)) and not math.isnan(r[k])]
        avg[k] = float(np.mean(vals)) if vals else float('nan')
    avg['time'] = 'AVG'

    # Also compute CoV of the time-averaged H2 field (less noisy)
    print("\nComputing CoV on time-averaged H2 field ...")
    tavg = cov_on_timeavg_field(case, times, patches, patch_geom)
    avg.update(tavg)

    # Function-object time-series metrics (clean, sampled every timestep)
    print("\nReading function-object time series from postProcessing ...")
    ts_metrics = timeseries_metrics(case, t_min=0.8)
    avg.update(ts_metrics)
    if 'p_rgh_inlet_ts_n' in ts_metrics:
        print(f"  time-series samples: {ts_metrics.get('p_rgh_inlet_ts_n', 0)} in "
              f"[{ts_metrics.get('p_rgh_inlet_ts_tmin', 0):.3f}, "
              f"{ts_metrics.get('p_rgh_inlet_ts_tmax', 0):.3f}] s")
    if 'dP_prgh_area_ts' in ts_metrics:
        print(f"  clean area-weighted ΔP(p_rgh) = {ts_metrics['dP_prgh_area_ts']/1000:.3f} kPa")

    # ---- Write CSV ----
    csv_path = out / 'all_metrics.csv'
    with csv_path.open('w') as f:
        f.write(','.join(keys) + '\n')
        for r in rows + [avg]:
            cells = []
            for k in keys:
                v = r.get(k, '')
                if isinstance(v, float):
                    cells.append(f"{v:.8g}")
                else:
                    cells.append(str(v))
            f.write(','.join(cells) + '\n')
    print(f"\nWrote {csv_path}")

    # ---- Write Markdown summary ----
    md_path = out / 'ALL_METRICS.md'
    with md_path.open('w') as f:
        f.write(f"# All metrics — `{case.name}`\n\n")
        f.write(f"Snapshots used: **{', '.join(times)}** (n = {len(times)})\n\n")

        f.write("> **Note on temporal averaging.** The simulation is a variable-density "
                "compressible transient; the three snapshots on disk (purgeWrite=3) are "
                "only coarse samples of the stationary window, and instantaneous pressure "
                "and mass-flux signals carry acoustic/pressure-pulse oscillations. "
                "Metrics below are reported under two conventions:\n"
                "> 1. **from snapshots** — full menu of weighted metrics, but subject to "
                "the 3-sample acoustic noise (use per-snapshot detail in Section 4 for "
                "the envelope);\n"
                "> 2. **from function-object time series** (`postProcessing/*.dat`) — "
                "sampled every timestep, noise-free, but limited to the function objects "
                "that were configured (here: area-weighted static-gauge `p_rgh` and "
                "area-weighted outlet `H2`).\n\n")

        # ---- Section 1: Mixing ----
        f.write("## 1. Mixing at outlet\n\n")
        f.write("### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)\n\n")
        f.write("| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |\n")
        f.write("|---|---:|---:|---:|---:|\n")
        for w in ('area', 'mass', 'vol'):
            f.write(
                f"| {w:<4} | "
                f"{avg[f'H2_mean_{w}_tavg']:.5f} | "
                f"{avg[f'H2_std_{w}_tavg']:.5f} | "
                f"{avg[f'H2_CoV_{w}_tavg']:.4f} | "
                f"{avg[f'H2_Is_{w}_tavg']:.4f} |\n"
            )

        f.write("\n### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)\n\n")
        f.write("| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |\n")
        f.write("|---|---:|---:|---:|---:|\n")
        for w in ('area', 'mass', 'vol'):
            f.write(
                f"| {w:<4} | "
                f"{avg['H2_mean_' + w]:.5f} | "
                f"{avg['H2_std_' + w]:.5f} | "
                f"{avg['H2_CoV_' + w]:.4f} | "
                f"{avg['H2_Is_' + w]:.4f} |\n"
            )

        if not math.isnan(avg.get('H2_outletAvg_ts_mean', float('nan'))):
            f.write(f"\n### 1c. Reference from function-object time series (area-weighted, every timestep)\n\n")
            f.write(f"- ⟨Y_H₂⟩_area, time-series: **{avg['H2_outletAvg_ts_mean']:.5f}** "
                    f"(n = {avg['H2_outletAvg_ts_n']} samples in "
                    f"[{avg['H2_outletAvg_ts_tmin']:.3f}, {avg['H2_outletAvg_ts_tmax']:.3f}] s)\n")

        # ---- Section 2: Pressure drop ----
        f.write("\n## 2. Pressure drop\n\n")
        f.write("### 2a. Clean reference from function-object time series (area-weighted, every timestep)\n\n")
        if 'dP_prgh_area_ts' in avg and not math.isnan(avg.get('dP_prgh_area_ts', float('nan'))):
            f.write(f"- ΔP_area_ts on `p_rgh`: **{avg['dP_prgh_area_ts']/1000:.3f} kPa**  "
                    f"(⟨p_rgh⟩_inlet = {avg['p_rgh_inlet_ts_mean']/1000:.1f} kPa, "
                    f"⟨p_rgh⟩_outlet = {avg['p_rgh_outlet_ts_mean']/1000:.1f} kPa, "
                    f"n = {avg['p_rgh_inlet_ts_n']} samples)\n\n")
        else:
            f.write("- time-series data not found in postProcessing/\n\n")

        f.write("### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)\n\n")
        f.write("ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)\n\n")
        f.write("| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |\n")
        f.write("|---|---:|---:|---:|\n")
        labels = {
            'p':           'static `p`',
            'p_rgh':       'gauge `p_rgh`',
            'p_total':     'total `p + ½ρU²`',
            'p_rgh_total': 'gauge-total `p_rgh + ½ρU²`',
        }
        for key, label in labels.items():
            f.write(
                f"| {label} | "
                f"{avg[f'dP_{key}_area'] / 1000:.3f} | "
                f"{avg[f'dP_{key}_mass'] / 1000:.3f} | "
                f"{avg[f'dP_{key}_vol'] / 1000:.3f} |\n"
            )

        f.write("\n## 3. Mass balance\n\n")
        f.write("### 3a. Clean reference from outletFlux function object (every timestep)\n\n")
        if not math.isnan(avg.get('outletFlux_ts_mean', float('nan'))):
            f.write(f"- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: "
                    f"**{avg['outletFlux_ts_mean']:+.4f}**  "
                    f"(σ = {avg['outletFlux_ts_std']:.4f}, "
                    f"n = {avg['outletFlux_ts_n']} samples, "
                    f"t ∈ [{avg['outletFlux_ts_tmin']:.3f}, {avg['outletFlux_ts_tmax']:.3f}] s)\n\n")
        else:
            f.write("- outletFlux function object not found in postProcessing/\n\n")

        f.write("### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)\n\n")
        f.write(f"- ṁ main_inlet  : **{avg['mdot_main_inlet']:+.4f}** kg/s\n")
        f.write(f"- ṁ branch_inlet: **{avg['mdot_branch_inlet']:+.4f}** kg/s\n")
        f.write(f"- ṁ outlet      : **{avg['mdot_outlet']:+.4f}** kg/s\n")
        f.write(
            f"- closure error : **{avg['mdot_balance_err']:+.4e} kg/s**  "
            f"({avg['mdot_balance_pct']:+.2f} % of ṁ_outlet)\n"
        )

        f.write("\n## 4. Per-snapshot detail\n\n")
        f.write("| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |\n")
        f.write("|---|---:|---:|---:|---:|---:|---:|\n")
        for r in rows:
            f.write(
                f"| {r['time']} | "
                f"{r['H2_CoV_area']:.4f} | "
                f"{r['H2_CoV_mass']:.4f} | "
                f"{r['H2_CoV_vol']:.4f} | "
                f"{r['dP_p_mass'] / 1000:.3f} | "
                f"{r['dP_p_total_mass'] / 1000:.3f} | "
                f"{r['mdot_balance_pct']:+.2f} |\n"
            )
        f.write(
            f"| **AVG** | "
            f"**{avg['H2_CoV_area']:.4f}** | "
            f"**{avg['H2_CoV_mass']:.4f}** | "
            f"**{avg['H2_CoV_vol']:.4f}** | "
            f"**{avg['dP_p_mass'] / 1000:.3f}** | "
            f"**{avg['dP_p_total_mass'] / 1000:.3f}** | "
            f"**{avg['mdot_balance_pct']:+.2f}** |\n"
        )

    print(f"Wrote {md_path}")


def main() -> None:
    ap = argparse.ArgumentParser(description='Retro-active full metrics for a T-junction case.')
    ap.add_argument('case_dir', help='path to the OpenFOAM case directory')
    ap.add_argument('--times', nargs='+', default=None,
                    help='snapshot directory names (auto-detect >=0.8 s if omitted)')
    ap.add_argument('--outdir', default=None,
                    help='where to write all_metrics.csv and ALL_METRICS.md (default: case dir)')
    args = ap.parse_args()
    run(args.case_dir, args.times, args.outdir)


if __name__ == '__main__':
    main()
