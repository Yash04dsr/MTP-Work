# All metrics — `case_09`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.02967 | 0.03125 | 1.0533 | 0.0339 |
| mass | 0.02445 | 0.02853 | 1.1666 | 0.0341 |
| vol  | 0.02929 | 0.03109 | 1.0615 | 0.0340 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.02967 | 0.03125 | 1.0533 | 0.0339 |
| mass | 0.02445 | 0.02853 | 1.1666 | 0.0341 |
| vol  | 0.02929 | 0.03109 | 1.0615 | 0.0340 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.01591** (n = 63 samples in [0.806, 1.196] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **2.322 kPa**  (⟨p_rgh⟩_inlet = 6902.3 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 63 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | 35.505 | 35.506 | 35.506 |
| gauge `p_rgh` | 35.498 | 35.493 | 35.499 |
| total `p + ½ρU²` | 35.283 | 35.252 | 35.307 |
| gauge-total `p_rgh + ½ρU²` | 35.276 | 35.239 | 35.301 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+35.9183**  (σ = 8.8617, n = 63 samples, t ∈ [0.806, 1.196] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.8213** kg/s
- ṁ branch_inlet: **-0.6342** kg/s
- ṁ outlet      : **+33.1537** kg/s
- closure error : **-1.3017e+00 kg/s**  (-3.93 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 1.0533 | 1.1666 | 1.0615 | 35.506 | 35.252 | -3.93 |
| **AVG** | **1.0533** | **1.1666** | **1.0615** | **35.506** | **35.252** | **-3.93** |
