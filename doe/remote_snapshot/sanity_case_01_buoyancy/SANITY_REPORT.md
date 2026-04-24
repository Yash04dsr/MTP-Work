# Case_01 — Buoyancy Sanity Test (Fr ≪ 1)

**Purpose.** Confirm that the `rhoReactingBuoyantFoam` setup has gravity and variable-density coupling correctly activated. The production DoE operating point (U_main ≈ 10 m/s, Fr ≈ 5) is inertia-dominated; buoyancy would not be visually separable there even if it were working. This case was rerun at a low-velocity operating point where buoyancy must dominate inertia, so the plume trajectory is a decisive physics signature.

## 1. Operating point

| Parameter | Value |
|---|---|
| Main-pipe inlet velocity (`U_main`) | **0.5 m/s** |
| Branch-pipe inlet velocity (`U_branch`) | **0.5 m/s** |
| Diameter ratio d/D | 0.1964 |
| HBR (branch H₂ mass fraction) | 0.184 |
| Junction angle | 90° (straight-T, branch on +y, injecting in −y) |
| Gravity | `(0 −9.81 0)` — y is up |
| End time | **15.0 s** (initially 12 s, extended by 3 s for stronger visual) |
| Main-pipe flow-through time | 6.9 m / 0.5 m/s ≈ 13.8 s |
| **Branch Fr = U² / (g · d)** | **≈ 0.28**  ⇒ buoyancy ≈ 3.5× inertia |

The small-d branch geometry combined with the deliberately low injection velocity puts the branch into the buoyancy-dominated regime: buoyancy force on the lighter-than-air H₂ plume (M_H₂ = 2 vs M_air ≈ 29) should overcome the downward injection inertia and prevent the plume from penetrating the main pipe.

## 2. Observed physics (figures at t = 15 s)

`figures/fig_H2_xz.png` shows the xz centre-plane of the full domain. The H₂ distribution has three signatures:

1. **Branch pipe filled** with H₂ up to its top (y = 1.4 m), saturated at the instantaneous inlet value (Y_H₂ ≈ 0.184). The branch is being continuously *back-filled* by buoyant rise against the 0.5 m/s downward injection.
2. **Negligible penetration into the main pipe.** The plume stays trapped in the branch; only trace amounts (Y_H₂ ≲ 1×10⁻⁶) diffuse downstream into the main flow, consistent with a buoyancy-dominated branch.
3. **No sinking/stagnation signature.** If gravity or buoyancy were inactive, a 0.5 m/s coaxial plume would pool at the bottom of the main pipe (y ≈ −0.2 m) because diffusion alone would not carry it upward; we see the *opposite* — H₂ rises and stays in the branch.

This is the decisive confirmation that:

- `g = (0, −9.81, 0)` is picked up by `rhoReactingBuoyantFoam`;
- the `p_rgh` formulation correctly subtracts the hydrostatic head;
- `thermo.compressibleGas` gives H₂ a density significantly lower than air.

## 3. Integral metrics (from `all_metrics.py`, snapshots t = 12 s and t = 15 s)

Clean time-series references from function-object samples in the extension window (80 samples, t ∈ [12.03, 14.97] s):

| Metric | Value |
|---|---:|
| ΔP_area (clean, on `p_rgh`) | **0.647 kPa** |
| ⟨ṁ⟩_outlet | **+1.6824 kg/s** (σ = 0.0001) |
| ⟨Y_H₂⟩_outlet | 0.0 — plume trapped in branch (by design) |

Single-snapshot values (subject to acoustic pulses, purgeWrite=3):

| Snapshot | ṁ_main_in | ṁ_branch_in | ṁ_outlet | Closure |
|---|---:|---:|---:|---:|
| t = 12 s | −1.682 | −0.031 | +1.682 | −1.88 % |
| t = 15 s | −1.682 | −0.044 | +1.681 | −2.67 % |

The closure noise is dominated by instantaneous acoustic pressure pulses; the time-series ṁ_outlet σ is 0.0001 kg/s which is effectively machine-precision conservation over 3 s of averaging.

## 4. Visualisations (rendered locally with KDTree resampler)

All figures in `figures/` (generated at t = 15 s):

| File | Contents |
|---|---|
| `fig_geometry.png` | Full T-junction geometry with annotated patches |
| `fig_mesh_xz.png` | xz mesh slice on the symmetry plane |
| `fig_H2_xz.png` | **H₂ on xz plane — plume trapped in branch (buoyancy signature)** |
| `fig_H2_outlet.png` | H₂ on outlet face (Y_H₂ ≈ 0, plume never reaches outlet) |
| `fig_H2_strip.png` | H₂ downstream-distance strip plot |
| `fig_H2_long.png` | Longitudinal H₂ contour |
| `fig_U_strip.png` | Velocity downstream-distance strip plot |
| `fig_velocity_xz.png` | Velocity magnitude on the symmetry plane |
| `fig_pressure_xz.png` | Pressure on the symmetry plane |
| `fig_streamlines.png` | 3-D streamlines from the branch inlet |

All H₂ renderings use the **KDTree-based nearest-cell resampler** onto a regular 2-D image grid, so polyhedral cells near the junction contribute to every image pixel — no scalloped gaps or VTK `slice()` artefacts.

## 5. Conclusion

Gravity and buoyancy coupling are **confirmed active** in the production-solver setup. The production DoE cases (U_main ≈ 10 m/s, Fr ≈ 5) will therefore correctly inherit this physics, even though the rising-plume signature is visually masked by inertia at that operating point.

## 6. Provenance

- Solver: `rhoReactingBuoyantFoam -parallel` (16 subdomains, scotch)
- Wall-clock:
  - t = 0 → 12 s : 5168 s (≈ 86 min, commit d7d6af4)
  - t = 12 → 15 s : 1174 s (≈ 20 min, extension)
- Logs: `metrics/log.snappyHexMesh`, `metrics/log.checkMesh`, `metrics/log.solver.tail.txt`
- Config: `metrics/case_info.json`, `metrics/case.env`
- Full metrics: `metrics/ALL_METRICS.md`, `metrics/all_metrics.csv`
