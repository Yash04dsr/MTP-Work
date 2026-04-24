# case_01 — repurposed as buoyancy sanity test (Fr << 1)

> The original case_01 production run (the 90° DoE operating point with
> U_main = 10 m/s, VR = 5.84) was aborted and **replaced** by a low-velocity
> (U = 0.5 m/s, Fr ≈ 0.06) sanity simulation whose purpose was to verify
> that gravity + variable-density buoyancy coupling are active in
> `rhoReactingBuoyantFoam`.  Stale t = 0 s figures from the aborted
> production run have been overwritten with the t = 15 s sanity figures.

## Why

At the DoE operating point the branch-jet Froude number is ≈ 5 — inertia
dominates buoyancy, so even a correctly-configured solver wouldn't show
a rising plume signature. To verify buoyancy physics is active we need
Fr << 1, which requires a low-velocity rerun.

## Result

At t = 15 s the H₂ plume is trapped inside the branch pipe, rising
against the 0.5 m/s downward injection because buoyancy is ≈ 3.5× the
injection inertia. This is the decisive confirmation that gravity and
the `p_rgh` hydrostatic formulation are working.

Clean time-series references (80 samples in the extension window):

| Metric                           | Value            |
|----------------------------------|-----------------:|
| ΔP_area on `p_rgh`               | **0.647 kPa**    |
| ⟨ṁ⟩_outlet                       | **+1.6824 kg/s** (σ = 1e-4) |
| ⟨Y_H₂⟩_outlet                    | 0 (plume never leaves branch — by design) |

Full write-up + figure key: `../../../remote_snapshot/sanity_case_01_buoyancy/SANITY_REPORT.md`

## Files

- `figures/*` — 10 PNGs at t = 15 s (KDTree resampler, no gap artefacts)
- `ALL_METRICS.md`, `all_metrics.csv` — snapshot and time-series metrics
- `Allrun`, `case.env`, `case_info.json`, `system/`, `0.orig/`, etc —
  configuration used for the sanity rerun
