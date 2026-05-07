# All metrics — `case_05`

Snapshots used: **1.2** (n = 1)

> **Note on temporal averaging.** The simulation is a variable-density compressible transient; the three snapshots on disk (purgeWrite=3) are only coarse samples of the stationary window, and instantaneous pressure and mass-flux signals carry acoustic/pressure-pulse oscillations. Metrics below are reported under two conventions:
> 1. **from snapshots** — full menu of weighted metrics, but subject to the 3-sample acoustic noise (use per-snapshot detail in Section 4 for the envelope);
> 2. **from function-object time series** (`postProcessing/*.dat`) — sampled every timestep, noise-free, but limited to the function objects that were configured (here: area-weighted static-gauge `p_rgh` and area-weighted outlet `H2`).

## 1. Mixing at outlet

### 1a. CoV computed on the **time-averaged H₂ field** (preferred — removes acoustic noise)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | **CoV** | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.02209 | 0.02789 | 1.2627 | 0.0360 |
| mass | 0.01935 | 0.02567 | 1.3264 | 0.0347 |
| vol  | 0.02339 | 0.02856 | 1.2210 | 0.0357 |

### 1b. Mean of per-snapshot CoVs (for comparison; includes temporal variance)

| Weighting | ⟨Y_H₂⟩ | σ(Y_H₂) | CoV | Danckwerts I_s |
|---|---:|---:|---:|---:|
| area | 0.02209 | 0.02789 | 1.2627 | 0.0360 |
| mass | 0.01935 | 0.02567 | 1.3264 | 0.0347 |
| vol  | 0.02339 | 0.02856 | 1.2210 | 0.0357 |

### 1c. Reference from function-object time series (area-weighted, every timestep)

- ⟨Y_H₂⟩_area, time-series: **0.01784** (n = 67 samples in [0.802, 1.195] s)

## 2. Pressure drop

### 2a. Clean reference from function-object time series (area-weighted, every timestep)

- ΔP_area_ts on `p_rgh`: **5.297 kPa**  (⟨p_rgh⟩_inlet = 6905.3 kPa, ⟨p_rgh⟩_outlet = 6900.0 kPa, n = 67 samples)

### 2b. From 3 snapshots (noisy due to acoustic pulses; see per-snapshot detail below)

ΔP = ⟨φ⟩_main_inlet − ⟨φ⟩_outlet (kPa)

| Pressure field | Area-weighted | Mass-flux-weighted | Vol-flux-weighted |
|---|---:|---:|---:|
| static `p` | 15.913 | 15.914 | 15.914 |
| gauge `p_rgh` | 15.908 | 15.905 | 15.910 |
| total `p + ½ρU²` | 14.451 | 14.462 | 14.488 |
| gauge-total `p_rgh + ½ρU²` | 14.446 | 14.453 | 14.484 |

## 3. Mass balance

### 3a. Clean reference from outletFlux function object (every timestep)

- ⟨sum(phi)⟩_outlet (ṁ_out, kg/s), time-averaged: **+33.7472**  (σ = 8.2190, n = 67 samples, t ∈ [0.802, 1.195] s)

### 3b. From 3 snapshots (instantaneous, dominated by acoustic pulses)

- ṁ main_inlet  : **-33.7257** kg/s
- ṁ branch_inlet: **-0.4623** kg/s
- ṁ outlet      : **+42.8570** kg/s
- closure error : **+8.6689e+00 kg/s**  (+20.23 % of ṁ_outlet)

## 4. Per-snapshot detail

| time | CoV_area | CoV_mass | CoV_vol | ΔP_static_mass [kPa] | ΔP_total_mass [kPa] | balance [%] |
|---|---:|---:|---:|---:|---:|---:|
| 1.2 | 1.2627 | 1.3264 | 1.2210 | 15.914 | 14.462 | +20.23 |
| **AVG** | **1.2627** | **1.3264** | **1.2210** | **15.914** | **14.462** | **+20.23** |
