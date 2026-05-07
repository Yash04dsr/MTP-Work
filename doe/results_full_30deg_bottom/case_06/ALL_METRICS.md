# All metrics — `case_06`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.03380 | 0.02480 | 0.7338 | 0.0188 |
| mass | 0.02983 | 0.02325 | 0.7793 | 0.0187 |
| vol  | 0.03295 | 0.02420 | 0.7344 | 0.0184 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.03380 | 0.02480 | 0.7338 | 0.0188 |
| mass | 0.02983 | 0.02325 | 0.7793 | 0.0187 |
| vol  | 0.03295 | 0.02420 | 0.7344 | 0.0184 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.03445** (n = 135 samples in [0.802, 1.198] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **1.883 kPa**  (⟨p_rgh⟩_inlet = 6901.9 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 135 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | -43.217 | -43.217 | -43.217 |
| gauge `p_rgh` | -43.219 | -43.223 | -43.221 |
| total `p + ½ρU²` | -42.637 | -42.644 | -42.616 |
| gauge-total `p_rgh + ½ρU²` | -42.639 | -42.651 | -42.620 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+37.0621**  (σ = 12.1664, n = 135 samples, t ∈ [0.802, 1.198] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.4374** kg/s
- ṁ branch_inlet: **-0.9667** kg/s
- ṁ outlet      : **+25.0813** kg/s
- closure error : **-9.3228e+00 kg/s**  (-37.17 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.7338 | 0.7793 | 0.7344 | -43.217 | -42.644 | -37.17 |
| **AVG** | **0.7338** | **0.7793** | **0.7344** | **-43.217** | **-42.644** | **-37.17** |
