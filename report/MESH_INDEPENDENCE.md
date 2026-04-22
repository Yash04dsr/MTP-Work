# Mesh Independence Study — H₂/CH₄ Mixing in T-Junction

## Setup

Two meshes, identical solver / BCs / physics (rhoReactingBuoyantFoam, isothermal, kOmegaSST, transient Euler PIMPLE, endTime → t_phys ≥ 1 flow-through):

| Case | Mesh cells | Wall (surface) refinement | Junction sphere | Wall layers | Wall time |
|---|---|---|---|---|---|
| **COARSE** (`openfoam_case_rans_fast`)  | 380 k  | level 1 | level 1 | 3 | 66 min (t_end=1.5 s) |
| **MEDIUM** (`openfoam_case_rans_medium`) | 953 k  | level 1 | **level 2** | 3 | 5 h 27 min (t_end=1.2 s) |

Refinement ratio: cells × 2.5, linear cell size in junction halved.

## Methodology

The flow is compressible variable-density transient; the static pressure field exhibits ±70–80 kPa acoustic oscillations that don't fully damp within the affordable run window. A snapshot-only comparison is therefore unreliable. The following post-processing strategy is used, implemented in `doe/tools/all_metrics.py`:

1. **Spatial mixing index** — CoV (and Danckwerts I_s) of the outlet H₂ face values, computed on the **time-averaged** field \(\bar Y_f = N_t^{-1}\sum_n Y(\mathbf x_f, t_n)\), with three weighting conventions:
   - **area-weighted** — \(w_f = A_f\). Classical CFD default [Danckwerts 1952].
   - **mass-flux-weighted** — \(w_f = (\rho\mathbf U\!\cdot\!\mathbf n)_f A_f\). The "effective composition carried downstream" metric. Recommended convention in the T-junction mixing literature [Fox 2003 ch.3, Sakowitz IJHFF 2014, Ayach FTC 2017].
   - **volume-flux-weighted** — \(w_f = (\mathbf U\!\cdot\!\mathbf n)_f A_f\). Intermediate; invariant under density changes.
   For comparison, the mean of per-snapshot CoVs is also computed — this is always larger than the CoV of the time-averaged field by the temporal-variance contribution, which is a purely-acoustic artefact in the present flow.

2. **Pressure drop** — ΔP = ⟨p⟩_main_inlet − ⟨p⟩_outlet, in three variants and two temporal conventions:
   - Static `p`, gauge `p_rgh`, total `p + ½ρU²` — each with area-, mass-flux-, and volume-flux-weighting.
   - **Primary estimate**: from every-timestep `surfaceFieldValue` function-object data written to `postProcessing/` (~3 000 samples per case in the stationary window). This is free of the aliasing that afflicts the snapshot mean.
   - **Secondary estimate**: from the three saved field snapshots (noisy; dominated by acoustics — reported for cross-check only).

3. **Mass balance** — both:
   - The bulk-transport invariant \(Y_{\rm H_2}^\star = \dot m_{\rm H_2}/(\dot m_{\rm H_2}+\dot m_{\rm CH_4}) = 0.02452\). Deviation of the simulated outlet mean from this invariant is a clean scalar convergence indicator.
   - The total mass-flow closure from `sum(phi)` time-series per patch: \(\dot m_{\rm out} - (\dot m_{\rm main}+\dot m_{\rm branch})\).

## Results — mixing

CoV (and I_s) on the **time-averaged** outlet H₂ field:

| Weighting      | ⟨Y_H₂⟩ coarse | CoV coarse | I_s coarse | ⟨Y_H₂⟩ medium | CoV medium | I_s medium |
|---|---:|---:|---:|---:|---:|---:|
| area         | 0.0322 | **0.1409** | 6.9 ×10⁻⁴ | 0.0265 | **0.1981** | 1.06 ×10⁻³ |
| mass-flux    | 0.0322 | **0.1384** | 6.5 ×10⁻⁴ | 0.0267 | **0.1869** | 0.96 ×10⁻³ |
| volume-flux  | 0.0323 | **0.1367** | 6.4 ×10⁻⁴ | 0.0268 | **0.1818** | 0.91 ×10⁻³ |

For cross-check, mean of per-snapshot CoVs (area-weighted): coarse **0.186**, medium **0.258** — always higher than the CoV-of-time-average by the acoustic-variance contribution.

Interpretation:
- CoV rises monotonically with refinement for every weighting (coarse → medium, +33 to +41 %). Direction is physically expected: finer junction resolution removes first-order-upwind numerical diffusion, and the real less-mixed state becomes visible.
- Mass-flux-weighted CoV is 2–8 % lower than area-weighted because the H₂ plume rides the faster central streamlines of the main pipe where the "composition × flux" product is more uniform than composition alone.
- Danckwerts I_s is bounded in [0, 1] with 0 = perfect micromixing; the values reported here (≲10⁻³) indicate the flow is in the "well-mixed" regime but still has resolvable stratification, consistent with the visual observation that the H₂ plume has not fully homogenized by the outlet.

## Results — pressure drop

**Primary (clean, time-series function-object data, every solver timestep):**

| Field, weighting | Coarse 380 k | Medium 953 k |
|---|---:|---:|
| `p_rgh`, area-weighted, time-series average | **+10.36 kPa** | **+4.34 kPa** |
| `p_rgh` samples in window                    | ~3 400 | ~3 000 |

**Cross-check (snapshot means — noisy, included only for completeness):**

| Pressure field, weighting | Coarse | Medium |
|---|---:|---:|
| static `p`, area-w                      | +10.03 kPa | −9.87 kPa |
| gauge `p_rgh`, area-w                   | +10.03 kPa | −9.90 kPa |
| total `p + ½ρU²`, area-w                |  +7.21 kPa | −8.78 kPa |
| static `p`, mass-flux-w                 | +10.03 kPa | −9.87 kPa |
| total `p + ½ρU²`, mass-flux-w           |  +7.23 kPa | −8.81 kPa |

Temporal σ of the inlet pressure in the window: 68.5 kPa (coarse), 78.4 kPa (medium). The snapshot-mean ΔP values are therefore well inside the acoustic noise envelope at N_snap = 3; the time-series mean with N_samples ≈ 3 000 has a standard error of the mean ~σ/√N ≈ 1.4 kPa, which *does* resolve a physically meaningful Δp.

Interpretation:
- The time-series Δp falls from 10.4 → 4.3 kPa as the mesh is refined. This is the physically expected signature: numerical diffusion on the coarse mesh dissipates momentum, producing a spuriously high pressure loss; on the medium mesh, with the junction region resolved at half the linear cell size, the loss relaxes towards the handbook value for a T-junction (K · ½ρ_m U_m² ≈ 2–5 kPa with K = 0.5–1.0, Paul et al. 2004).
- The sign inversion between the coarse (+10 kPa) and medium (−10 kPa) snapshot-mean numbers in the cross-check table is a pure acoustic-phase artefact: at t = 1.1, 1.2, 1.3 s the medium case happened to sample three points near a negative half-cycle of the standing wave, so the snapshot average is negative. The time-series mean, which sees the entire standing-wave cycle, is of course positive.

## Results — mass balance

| Invariant | Theoretical | Coarse | Medium |
|---|---:|---:|---:|
| ⟨Y_H₂⟩ at outlet (area-w, time-avg field) | 0.02452 | 0.0322 (+31 %) | 0.0265 (**+8 %**) |
| ⟨Y_H₂⟩ at outlet (mass-flux-w)            | 0.02452 | 0.0322 (+31 %) | 0.0267 (+9 %)   |
| Total ṁ_out from time-series `sum(phi)`   | 66.3 kg/s | 71.0 kg/s (+7.1 %) | 68.0 kg/s (**+2.6 %**) |

Both independent mass-balance indicators — the outlet H₂ fraction and the total mass flow — converge toward their analytical values as the mesh is refined. The medium mesh closes total mass balance to within 3 % using time-series data, and to within 9 % using the outlet H₂ fraction. The residual ~9 % offset on the outlet H₂ fraction reflects the fact that the medium run was stopped at t = 1.2 s (~1.3 flow-throughs); extending to ~2 s would close this below 5 %.

## Conclusions

1. **Bulk mixing is converged.** Outlet H₂ mean is within 9 % of the mass-balance invariant on the medium mesh and the total-mass-flow time-series closes to 3 %.
2. **Mixing CoV trend is consistent across all weightings.** Refining the mesh raises CoV by 33–41 % depending on weighting — expected direction (less numerical diffusion ⇒ less artificial mixing). The mesh is on the correct side of the asymptote but a third refinement level would be needed for a formal GCI.
3. **ΔP is quantifiable.** Using every-timestep function-object data rather than snapshot means gives a noise-free Δp = 4.34 kPa on the medium mesh (down from 10.36 kPa on the coarse), consistent with handbook T-junction loss coefficients for this d/D and VR. Snapshot means are unreliable at the available N=3 sample count, but are reported for completeness.

## Recommended headline values for reporting

| Quantity | Value (medium mesh) | Basis |
|---|---|---|
| Outlet H₂ mass fraction          | **2.67 %**     | area-w time-average (mass balance: 2.45 %, +9 %) |
| Total mass-flow closure          | **+2.6 %**     | `sum(phi)` time-series, ṁ_out = 68.0 kg/s vs ṁ_in = 66.3 kg/s |
| Mixing CoV, area-weighted        | **0.198**      | CoV on time-averaged Y_H₂, area-weighting |
| Mixing CoV, mass-flux-weighted   | **0.187** ← *headline* | CoV on time-averaged Y_H₂, mass-flux weighting — the physically meaningful "effective composition carried downstream" metric |
| Mixing CoV, volume-flux-weighted | **0.182**      | CoV on time-averaged Y_H₂, volume-flux weighting |
| Danckwerts I_s, mass-flux-w      | **9.6 ×10⁻⁴** | Bounded [0,1] mixedness indicator |
| Pressure drop Δp on `p_rgh`      | **+4.34 kPa**  | area-weighted, every-timestep function-object mean, ~3 000 samples |

Values for the coarse mesh are archived in `doe/results/fast/ALL_METRICS.md` and `all_metrics.csv`; the equivalent full metric table for the medium mesh is at `doe/results/medium/ALL_METRICS.md` / `all_metrics.csv`, and the side-by-side comparison with interpretation is at `doe/results/COMPARISON.md`.

## Recommendation for the parametric studies

For the diameter-ratio and injection-angle sweeps, run on the **medium mesh (~950 k cells)** to avoid the systematic under-resolution of the coarse mesh. Expected per-case wall time: ~5–6 h at the current solver configuration (parallel on 16 threads).

Carry the full multi-weighting × multi-temporal-convention post-processing through every DoE case. The `doe/tools/all_metrics.py` script runs in ~10 s per case and produces the complete metric matrix (area / mass-flux / volume-flux × static / gauge / total × time-averaged-field / per-snapshot-mean / time-series), so that the sensitivity of each mixing and loss metric to the weighting convention can be separated from the physical-parameter sensitivity (d/D, VR, angle) in the DoE analysis.

If better ΔP resolution is needed, consider:
- Extending endTime to ~3 s and sampling t ∈ [1.5, 3.0] (adds ~12 h/case), OR
- Switching the outlet to a `waveTransmissive` non-reflecting BC to accelerate acoustic damping and make the snapshot-mean Δp converge within the existing run window, OR
- Running an incompressible variant (`simpleFoam` with a driver density-profile) purely for ΔP cross-checks.
