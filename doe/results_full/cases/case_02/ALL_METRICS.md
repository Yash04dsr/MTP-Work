# All metrics — `case_02`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.00000 | 0.00000 | nan | nan |
| mass | 0.00000 | 0.00000 | nan | nan |
| vol  | 0.00000 | 0.00000 | nan | nan |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.00000 | 0.00000 | nan | nan |
| mass | 0.00000 | 0.00000 | nan | nan |
| vol  | 0.00000 | 0.00000 | nan | nan |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.00000** (n = 27 samples in [0.803, 1.197] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **-2.184 kPa**  (⟨p_rgh⟩_inlet = 6897.8 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 27 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | 10.729 | 10.729 | 10.729 |
| gauge `p_rgh` | 10.729 | 10.731 | 10.731 |
| total `p + ½ρU²` | 11.434 | 11.466 | 11.466 |
| gauge-total `p_rgh + ½ρU²` | 11.434 | 11.468 | 11.468 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+33.2228**  (σ = 6.5070, n = 27 samples, t ∈ [0.803, 1.197] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.6969** kg/s
- ṁ branch_inlet: **-25.9895** kg/s
- ṁ outlet      : **+26.3587** kg/s
- closure error : **-3.3328e+01 kg/s**  (-126.44 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | nan | nan | nan | 10.729 | 11.466 | -126.44 |
| **AVG** | **nan** | **nan** | **nan** | **10.729** | **11.466** | **-126.44** |
