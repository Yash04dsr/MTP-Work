# 90° DoE — Full Campaign Summary

| case | d/D | VR | HBR | CoV (outlet, area) | ΔP_p_rgh (snapshot) |
|------|-----|----|-----|--------------------|---------------------|
| case_01 | 0.1964 | 5.842 | 0.184 | IC-only | — |
| case_02 | 0.1964 | 1.643 | 0.060 | IC-only | +10728.8 Pa |
| case_03 | 0.2518 | 1.330 | 0.078 | 0.4723 | -28596.1 Pa |
| case_04 | 0.2518 | 3.807 | 0.195 | 0.0658 | +23598.6 Pa |
| case_05 | 0.2963 | 1.241 | 0.098 | 0.5770 | -27056.0 Pa |
| case_06 | 0.2963 | 2.614 | 0.187 | 0.2016 | -19253.6 Pa |
| case_07 | 0.3815 | 1.137 | 0.142 | 0.4404 | -32469.2 Pa |
| case_08 | 0.3815 | 0.693 | 0.092 | 0.7066 | -7835.5 Pa |
| case_09 | 0.3957 | 0.953 | 0.130 | 0.3896 | -17819.7 Pa |
| case_10 | 0.3957 | 0.806 | 0.112 | 0.4073 | -4203.7 Pa |

Notes:
- case_01 crashed at t≈0.946 s (FPE in yPlus wall function), only IC snapshot remained locally → no CoV/ΔP. Its postProcessing.tar.gz *does* retain plane-averaged H2 up to 0.946 s if needed.
- CoV is outlet H2 mass-fraction, area-weighted, time-averaged over [0.8, 1.2] s.
- ΔP is p_rgh inlet − outlet at snapshot t=1.2 s (raw CSV value). Sign convention differs from the 'clean' time-averaged ΔP printed in logs.
