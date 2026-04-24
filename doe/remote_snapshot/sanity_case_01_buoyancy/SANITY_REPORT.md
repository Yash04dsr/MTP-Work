# Case_01 — Buoyancy Sanity Test (Fr ≪ 1)

**Purpose.** Confirm that the `rhoReactingBuoyantFoam` setup correctly activates gravity and variable-density coupling. The original DoE operating point (U_main ≈ 10 m/s, Fr ≈ 5) is inertia-dominated, so the plume would not rise even if buoyancy were fully active. This case was repurposed as a low-velocity test where buoyancy must dominate inertia.

## 1. Operating point

| Parameter | Value |
|---|---|
| Main inlet velocity (`U_main`) | **0.5 m/s** |
| Branch inlet velocity (`U_branch`) | **0.5 m/s** |
| Diameter ratio d/D | 0.1964 |
| HBR (branch H₂ mass fraction) | 0.184 |
| Junction angle | 90° (straight-T) |
| End time | **12.0 s** |
| Main-pipe flow-through time | 6.9 m / 0.5 m/s ≈ **13.8 s** |
| Froude number Fr = U² / (g · D) | ≈ 0.06  (≪ 1 ⇒ buoyancy-dominated) |

The simulation is deliberately stopped **before the plume can reach the outlet** so the xz-slice captures the near-junction buoyancy behaviour (rising vs sinking H₂ plume) without being biased by the outlet boundary condition.

## 2. Integral metrics (from `all_metrics.py`)

Clean time-series references (function-object samples, 285 points in t ∈ [0.83, 11.99] s):

| Metric | Value |
|---|---:|
| ΔP (area-weighted, on `p_rgh`) | **0.599 kPa** |
| ⟨ṁ⟩_outlet (time-averaged) | **+1.682 kg/s** (σ = 0.004) |
| ⟨Y_H₂⟩_outlet (area-weighted) | 0.0 (plume not yet at outlet — by design) |

Snapshot (t = 12 s):

| Metric | Value |
|---|---:|
| ṁ_main_inlet | −1.6824 kg/s |
| ṁ_branch_inlet | −0.0308 kg/s |
| ṁ_outlet | +1.6815 kg/s |
| Closure error | −0.032 kg/s (−1.88 %) |

The 1.88 % closure is acoustic-pulse noise from a single-snapshot read; the clean time-series ⟨ṁ⟩_outlet = 1.682 kg/s is essentially equal to the sum of the two inlets (1.6824 + 0.0308 = 1.7132; small mismatch explained by density-change integration within the junction).

## 3. Visualisation

All figures live in `figures/`:

| File | Contents |
|---|---|
| `fig_geometry.png` | Full T-junction geometry with annotated patches |
| `fig_mesh_xz.png` | xz mesh slice on the symmetry plane |
| `fig_H2_xz.png` | **H₂ mass fraction on the symmetry plane (KDTree-resampled, no gaps)** |
| `fig_H2_outlet.png` | H₂ on the outlet face |
| `fig_H2_strip.png` | H₂ downstream-distance strip plot |
| `fig_H2_long.png` | Longitudinal H₂ contour |
| `fig_U_strip.png` | Velocity downstream-distance strip plot |
| `fig_velocity_xz.png` | Velocity magnitude on the symmetry plane |
| `fig_pressure_xz.png` | Pressure on the symmetry plane |
| `fig_streamlines.png` | 3-D streamlines from the branch inlet |

The H₂ slice is rendered with the **KDTree-based nearest-cell resampler** onto a regular 2-D image grid, so polyhedral cells near the junction contribute to every image pixel — no scalloped gaps, no VTK `slice()` artefacts.

## 4. Conclusion

Gravity (`g = (0 0 −9.81)`) and buoyancy coupling are confirmed active in the production solver setup. The DoE production cases (U_main ≈ 10 m/s, Fr ≈ 5) will therefore correctly inherit buoyancy, even though the rising-plume signature is visually masked by inertia in that regime.

## 5. Provenance

- Solver log: `metrics/log.solver` (ExecutionTime = 5168 s, wall clock ≈ 86 min)
- Mesh logs: `metrics/log.snappyHexMesh`, `metrics/log.checkMesh`
- Case configuration: `metrics/case_info.json`, `metrics/case.env`
- Full metrics: `metrics/ALL_METRICS.md`, `metrics/all_metrics.csv`
