# Publication-Ready Figure Strategy (ON HOLD)

> Parked for later — revisit after 120deg campaign completes and all 4 angles
> have results. The plan below was drafted on 2026-05-04.

---

## Current Data Reality

| Angle | Cases | Metrics | PostProcessing | Status |
|-------|-------|---------|---------------|--------|
| 30deg | 9/10 (case_04 missing) | Full (33-col summary) | Full plane-z data | Done |
| 90deg | 8/10 (cases 1-2 incomplete) | Sparse (CoV + dP only) | Not available locally | Done |
| 120deg | 10 stamped | None | None | **NOT YET RUN** |
| 150deg | 8/10 (case_01 partial, case_04 missing?) | Full per-case metrics | Compressed .tar.gz | Mostly done |

Cross-campaign analysis (`doe/cross_campaign/`) currently covers **30deg + 90deg only**.

---

## Proposed Figures (Lean & Focused)

### Figure 1: CoV vs Downstream Distance (z/D)
- Line plot showing CoV decay along the pipe for various design points
- Overlay 95% mixing uniformity threshold (CoV < 0.05)
- **Requires:** Computing CoV at intermediate z-stations from field snapshots via PyVista
- **Data needed:** Full field data on remote machines (exists for 30deg and 150deg)

### Figure 2: Annotated Cross-Section Strip Plot
- Existing `fig_H2_strip.png` with CoV values annotated at each station
- **Requires:** Same intermediate-station CoV data as Figure 1

### Figure 3: Trade-Off Bubble Chart (CoV vs dP)
- Dual-axis: mixing quality vs energy penalty
- **Ready for 30+90 now**, needs 150deg aggregation into cross_summary.csv
- Extend `cross_analysis.py` to handle 3+ angles

### Figure 4: Clean Longitudinal Slice
- Already done (interpolation-based `fig_H2_long.png`)

### Summary Dashboard
- Top pane: CoV decay curves for all design points
- Bottom pane: dP bar chart for same design points

---

## Implementation Phases

### Phase 1: Aggregate 150deg + extend cross-campaign analysis
- Build `doe_summary_150deg.csv` from 8 per-case `all_metrics.csv`
- Extend `cross_analysis.py` to load 30+90+150
- Regenerate all 12 cross-campaign figures with 3 angles

### Phase 2: Compute intermediate-station CoV
- New script `tools/extract_station_cov.py`
- Slices volume at z = 2.5, 3, 4, 5, 6, outlet
- Computes mean, std, CoV of H2Mean on each slice
- Run on remote machines for 30deg and 150deg

### Phase 3: Build new summary figures
- CoV vs z/D line plot with 95% threshold
- Annotated strip plots
- Summary dashboard (CoV + dP, all angles)
- Auto-generated summary table

---

## Metrics to Report (per case)

| Metric | Source | Notes |
|--------|--------|-------|
| CoV (outlet) | `all_metrics.csv` | Primary mixing quality |
| dP (kPa) | `all_metrics.csv` | Energy penalty |
| Mass balance error (%) | `all_metrics.csv` | Numerical credibility |
| z95 mixing length | Derived from CoV(z) | Needs Phase 2 data |
| Re_branch | `case_info.json` | Flow regime context |

## What to Deprioritize
- Velocity field figures → appendix
- Streamlines → supplementary
- Pressure slice plots → integrated dP is better
- 3D isosurface/topdown → supplementary material

---

*Revisit this plan once 120deg results are available.*
