# Cross-Campaign Analysis: Top vs Bottom Injection

**Date:** 2026-05-07 (updated with LP-filtered ΔP)  
**Campaigns:** 4 completed (40 valid cases with uniform metrics)  
**Metric definitions:** per `report.tex` Sections 3.5–3.6  
**ΔP method:** LP-filtered (moving-average, width 0.10 s, mean on [0.4, 1.2] s window)

---

## 1. Campaign Overview

| Campaign  | Angle | Side | Valid Cases | CoV min | CoV median | CoV max | \|ΔP\| median (kPa) |
|-----------|-------|------|------------|---------|------------|---------|---------------------|
| 90° top   | 90°   | top  | 8          | 0.066   | 0.424      | 0.707   | 1.05                |
| 30° top   | 30°   | top  | 9          | 0.005   | 0.298      | 0.390   | 0.53                |
| 90° bot   | 90°   | bot  | 13         | 0.172   | 0.392      | 1.104   | 1.58                |
| 30° bot   | 30°   | bot  | 10         | 0.232   | 1.048      | 1.343   | 1.02                |

> **CoV** = σ(Y\_H2) / ⟨Y\_H2⟩ at outlet (area-weighted). Lower is better.  
> **|ΔP|** = LP-filtered |p\_rgh,inlet − p\_rgh,outlet|. Lower is cheaper.

---

## 2. Matched-Pair Comparison: Top vs Bottom (Same d/D, VR)

### 90° Injection

| Case | d/D   | VR   | CoV (top) | CoV (bot) | Δ CoV  | \|ΔP\| top (kPa) | \|ΔP\| bot (kPa) |
|------|-------|------|-----------|-----------|--------|-------------------|-------------------|
| 03   | 0.252 | 1.33 | 0.472     | 1.104     | +134%  | 0.49              | 0.58              |
| 04   | 0.252 | 3.81 | 0.066     | 0.271     | +312%  | 1.53              | 0.10              |
| 05   | 0.296 | 1.24 | 0.577     | 0.992     | +72%   | 0.95              | 0.44              |
| 06   | 0.296 | 2.61 | 0.202     | 0.392     | +94%   | 1.06              | 0.81              |
| 07   | 0.382 | 1.14 | 0.440     | 0.954     | +117%  | 1.04              | 2.65              |
| 08   | 0.382 | 0.69 | 0.707     | 0.911     | +29%   | 0.94              | 1.84              |
| 09   | 0.396 | 0.95 | 0.390     | 0.827     | +112%  | 1.30              | 1.58              |
| 10   | 0.396 | 0.81 | 0.407     | 0.835     | +105%  | 1.06              | 1.60              |

**Median CoV change (top→bottom): +109%** (bottom mixes ~2× worse)  
**Median |ΔP| change (top→bottom): +19%** (comparable; ΔP is not a strong differentiator)

### 30° Injection

| Case | d/D   | VR   | CoV (top) | CoV (bot) | Δ CoV   | \|ΔP\| top (kPa) | \|ΔP\| bot (kPa) |
|------|-------|------|-----------|-----------|---------|-------------------|-------------------|
| 01   | 0.196 | 5.84 | 0.005     | 0.232     | +4335%  | 3.92              | 0.46              |
| 02   | 0.196 | 1.64 | 0.390     | 1.189     | +205%   | 0.00              | 0.63              |
| 03   | 0.252 | 1.33 | 0.278     | 1.343     | +384%   | 0.49              | 2.54              |
| 05   | 0.296 | 1.24 | 0.298     | 1.263     | +324%   | 0.00              | 1.15              |
| 06   | 0.296 | 2.61 | 0.088     | 0.734     | +731%   | 0.53              | 0.88              |
| 07   | 0.382 | 1.14 | 0.238     | 1.089     | +358%   | 0.27              | 1.56              |
| 08   | 0.382 | 0.69 | 0.327     | 1.043     | +219%   | 0.81              | 1.34              |
| 09   | 0.396 | 0.95 | 0.307     | 1.053     | +243%   | 0.68              | 2.04              |
| 10   | 0.396 | 0.81 | 0.345     | 0.913     | +165%   | 0.99              | 0.87              |

**Median CoV change (top→bottom): +324%** (bottom mixes ~4× worse)  
**Median |ΔP| change (top→bottom): +132%** (bottom generally has higher ΔP at 30°)

---

## 3. Key Physical Findings

### 3.1 Top injection always mixes better than bottom injection

At **every single matched operating point** (17 out of 17 pairs), the
top-injection case achieves a lower CoV than the bottom-injection case.
The effect is dramatic: median degradation of +109% at 90° and +324% at 30°.

**Physical mechanism:** When H₂ enters from the top, gravity traps the
lighter gas against the upper wall, creating a thin high-concentration
layer. But this layer is thin precisely *because* the jet has already
penetrated into the main flow; buoyancy merely prevents it from
falling further, so it stays mixed in the upper half. When H₂ enters
from the bottom, buoyancy *lifts* the plume upward — but the plume
rises as a coherent low-density column that does not spread laterally.
By the outlet, the H₂ is concentrated in a narrow rising plume rather
than distributed across the cross-section.

### 3.2 Pressure drops are comparable across top/bottom — mixing is the differentiator

After LP-filtering (removing acoustic ringing from the compressible solver),
all campaigns show |ΔP| in the range 0–4 kPa. The median values are:

| Campaign  | Median \|ΔP\| (kPa) |
|-----------|---------------------|
| 90° top   | 1.05                |
| 30° top   | 0.53                |
| 90° bot   | 1.58                |
| 30° bot   | 1.02                |

The differences are modest (within 1 kPa). This means **switching from
top to bottom injection does not save pumping energy** — it only
degrades mixing. The practical implication is that top injection is
strictly dominant over bottom injection in this parameter space.

### 3.3 The 30° tilt effect reverses for bottom injection

For **top injection**, 30° is uniformly better than 90° (median CoV
0.298 vs 0.424, a 30% improvement). For **bottom injection**, this
advantage **reverses catastrophically**:

| Comparison            | 90° bot CoV median | 30° bot CoV median | Change      |
|----------------------|-------------------|-------------------|-------------|
| Bottom injection      | 0.392              | 1.048              | +167% worse |

The 30° bottom campaign produces the worst mixing of all four campaigns.
At 30°, the branch jet enters nearly co-flow with the main stream and
from below; the jet has low shear, low penetration, and buoyancy lifts
it vertically while the main flow sweeps it downstream — the result is
a long, thin, unmixed H₂ streak.

### 3.4 Velocity ratio remains the dominant control variable

Within every campaign, VR is the strongest predictor of CoV. Power-law
fits (CoV = A·VR^b) show:

| Campaign  | Exponent b | R²   |
|-----------|-----------|------|
| 90° top   | −1.16     | 0.80 |
| 30° top   | −1.88     | 0.80 |
| 90° bot   | −0.91     | 0.90 |
| 30° bot   | −0.72     | 0.72 |

Top injection has steeper exponents (CoV drops faster with VR),
confirming that top injection is more responsive to velocity increases.
The 90° bottom supplement cases (11–15, VR = 3.0–5.0) achieve CoV of
0.17–0.32, proving that even for bottom injection, sufficiently high VR
can partially overcome the buoyancy disadvantage.

---

## 4. Practical Recommendation

For hydrogen injection into high-pressure natural gas pipelines:

1. **Always inject from the top**, not the bottom. Bottom injection
   produces CoV values 2–4× worse at every matched operating point,
   with no meaningful pressure-drop benefit.

2. **Use a tilted branch (30°)** rather than 90° for top injection. The
   30° top campaign produced the single best case (CoV = 0.005) and
   the lowest median CoV (0.298).

3. **Maximise VR** (target VR ≥ 2.5). The velocity ratio is the single
   strongest lever on mixing quality across all campaigns.

4. **The d/D effect is secondary** in this parameter range (0.20–0.45).
   It matters mainly through its coupling with VR via the HBR constraint.

---

## 5. Figures

All cross-campaign figures are in `doe/cross_campaign/figures/`:

| File | Description |
|------|-------------|
| `fig1_CoV_vs_VR.png` | CoV vs VR scatter with power-law fits (4 campaigns) |
| `fig2_matched_pairs_top_vs_bottom.png` | Matched-pair arrow plot (top vs bottom, 90° and 30°) |
| `fig3_pareto.png` | Pareto front: CoV vs \|ΔP\| |
| `fig4_heatmap_CoV.png` | 2×2 heatmap of CoV in (d/D, VR) space |
| `fig5_bar_median_CoV.png` | Bar chart of median CoV by campaign |
| `fig6_mechanism_schematic.png` | Physical mechanism schematic (buoyancy effect) |
| `fig7_CoV_vs_dD.png` | CoV vs d/D at low VR |

---

## 6. Data Availability

- Full per-case metrics: `cross_campaign_metrics.csv` (40 rows, all LP-filtered)
- Per-case detailed metrics: `<campaign>/case_XX/all_metrics.csv`
- Excluded campaigns: 150° top, 120° top (field data on unreachable PC)
- Excluded cases: 90° top 01–02 (2-region mesh), 30° top 04 (mesh failure)
