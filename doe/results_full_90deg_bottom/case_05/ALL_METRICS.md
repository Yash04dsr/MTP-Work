# All metrics — `case_05`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01889 | 0.01874 | 0.9924 | 0.0190 |
| mass | 0.01675 | 0.01769 | 1.0564 | 0.0190 |
| vol  | 0.01870 | 0.01846 | 0.9870 | 0.0186 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.01889 | 0.01874 | 0.9924 | 0.0190 |
| mass | 0.01675 | 0.01769 | 1.0564 | 0.0190 |
| vol  | 0.01870 | 0.01846 | 0.9870 | 0.0186 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.01283** (n = 61 samples in [0.804, 1.199] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **4.676 kPa**  (⟨p_rgh⟩_inlet = 6904.7 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 61 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | 20.593 | 20.593 | 20.593 |
| gauge `p_rgh` | 20.589 | 20.585 | 20.589 |
| total `p + ½ρU²` | 19.160 | 19.142 | 19.182 |
| gauge-total `p_rgh + ½ρU²` | 19.156 | 19.134 | 19.177 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+34.3043**  (σ = 8.8240, n = 61 samples, t ∈ [0.804, 1.199] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.7469** kg/s
- ṁ branch_inlet: **-0.4620** kg/s
- ṁ outlet      : **+42.8842** kg/s
- closure error : **+8.6753e+00 kg/s**  (+20.23 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 0.9924 | 1.0564 | 0.9870 | 20.593 | 19.142 | +20.23 |
| **AVG** | **0.9924** | **1.0564** | **0.9870** | **20.593** | **19.142** | **+20.23** |
