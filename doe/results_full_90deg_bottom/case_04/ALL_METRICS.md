# All metrics — `case_04`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.03860 | 0.01046 | 0.2709 | 0.0029 |
| mass | 0.03830 | 0.01045 | 0.2728 | 0.0030 |
| vol  | 0.03890 | 0.01023 | 0.2631 | 0.0028 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.03860 | 0.01046 | 0.2709 | 0.0029 |
| mass | 0.03830 | 0.01045 | 0.2728 | 0.0030 |
| vol  | 0.03890 | 0.01023 | 0.2631 | 0.0028 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.03264** (n = 158 samples in [0.801, 1.199] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **0.268 kPa**  (⟨p_rgh⟩_inlet = 6900.3 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 158 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | -35.815 | -35.815 | -35.815 |
| gauge `p_rgh` | -35.813 | -35.811 | -35.813 |
| total `p + ½ρU²` | -35.000 | -34.963 | -34.962 |
| gauge-total `p_rgh + ½ρU²` | -34.998 | -34.959 | -34.960 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+36.3474**  (σ = 12.7896, n = 158 samples, t ∈ [0.801, 1.199] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.4718** kg/s
- ṁ branch_inlet: **-1.0180** kg/s
- ṁ outlet      : **+22.1095** kg/s
- closure error : **-1.2380e+01 kg/s**  (-56.00 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.2709 | 0.2728 | 0.2631 | -35.815 | -34.963 | -56.00 |
| **AVG** | **0.2709** | **0.2728** | **0.2631** | **-35.815** | **-34.963** | **-56.00** |
