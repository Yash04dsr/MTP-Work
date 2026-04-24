#!/usr/bin/env python3
"""
Compute mixing CoV (Coefficient of Variation) at outlet patch
and pressure drop from the reconstructed OpenFOAM fields.

Reads:
  - 1.5/H2     (volScalarField with boundary H2 values on outlet)
  - 1.5/p      (volScalarField)
  - 1.5/p_rgh  (volScalarField)
  - constant/polyMesh/{faces,points,boundary}

Outputs:
  - Mean H2 at outlet
  - StdDev H2 at outlet
  - CoV = StdDev/Mean  -> key mixing metric
  - dP = p_inlet - p_outlet
"""
import os, re, struct, sys, math
from pathlib import Path

case = Path(os.environ.get('CASE', '.'))
timeDir = case / '1.2'
polyMesh = case / 'constant/polyMesh'

def stripHeader(text):
    # OpenFOAM ASCII file: strip FoamFile header + initial comment
    m = re.search(r'\}\s*//\s*\*+\s*//\s*', text)
    if m: return text[m.end():]
    m = re.search(r'\}\s*\n\s*\n', text)
    if m: return text[m.end():]
    return text

def parseNonUniformList(text):
    """Parse 'nonuniform List<scalar> N ( v1 v2 ... vN )' -> list of floats."""
    m = re.search(r'nonuniform\s+List<scalar>\s+(\d+)\s*\(\s*([^)]*)\)', text, re.DOTALL)
    if m:
        n = int(m.group(1))
        vals = m.group(2).split()
        return [float(v) for v in vals[:n]]
    # uniform
    m = re.search(r'uniform\s+([-\d.eE+]+)', text)
    if m:
        return None, float(m.group(1))  # (None, uniform_val)
    return []

def readPatchFaceValues(fieldPath, patchName):
    """Return list of face values for scalar field on named patch."""
    with open(fieldPath) as f: raw = f.read()
    # Find boundaryField
    m = re.search(r'boundaryField\s*\{', raw)
    if not m: return None
    start = m.end()
    # Find the patch
    pat = re.compile(r'\s*'+re.escape(patchName)+r'\s*\{', re.DOTALL)
    pm = pat.search(raw, start)
    if not pm: return None
    # match braces to find end of patch dict
    i = pm.end()
    depth = 1
    while i < len(raw) and depth > 0:
        if raw[i] == '{': depth += 1
        elif raw[i] == '}': depth -= 1
        i += 1
    block = raw[pm.end():i-1]
    # look for 'value nonuniform List<scalar> N ( ... );' OR 'value uniform V;'
    mn = re.search(r'value\s+nonuniform\s+List<scalar>\s+(\d+)\s*\(\s*([^)]*)\)', block, re.DOTALL)
    if mn:
        n = int(mn.group(1))
        vals = mn.group(2).split()
        return [float(v) for v in vals[:n]]
    mu = re.search(r'value\s+uniform\s+([-\d.eE+]+)', block)
    if mu:
        # All faces have same value; need to know patch size
        return ('UNIFORM', float(mu.group(1)))
    return None

def readPatchList():
    """Return list of (name, nFaces, startFace) from boundary file."""
    with open(polyMesh/'boundary') as f: raw = f.read()
    # Support binary header but ASCII body (in this case body is ASCII based on earlier foamDictionary view)
    m = re.search(r'(\d+)\s*\(', raw)
    patches = []
    txt = raw[m.end():]
    for pm in re.finditer(r'([\w]+)\s*\{([^{}]*)\}', txt):
        name = pm.group(1)
        body = pm.group(2)
        mn = re.search(r'nFaces\s+(\d+)', body)
        ms = re.search(r'startFace\s+(\d+)', body)
        if mn and ms:
            patches.append((name, int(mn.group(1)), int(ms.group(1))))
    return patches

def readPointsBinary(path):
    """Read points (ASCII or binary) -> list of tuples (x,y,z). Only need ASCII here."""
    with open(path) as f: raw = f.read()
    m = re.search(r'^\s*(\d+)\s*\(', raw, re.MULTILINE)
    if not m: return None
    n = int(m.group(1))
    txt = raw[m.end():]
    pts = []
    for pm in re.finditer(r'\(\s*([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s*\)', txt):
        pts.append((float(pm.group(1)), float(pm.group(2)), float(pm.group(3))))
        if len(pts) == n: break
    return pts

def readFaces(path):
    """Parse faces file (labelList). Each line like '3(a b c)' or '4(a b c d)'."""
    with open(path) as f: raw = f.read()
    m = re.search(r'^\s*(\d+)\s*\(', raw, re.MULTILINE)
    if not m: return None
    n = int(m.group(1))
    txt = raw[m.end():]
    faces = []
    for pm in re.finditer(r'(\d+)\(([^)]+)\)', txt):
        nv = int(pm.group(1))
        ids = [int(x) for x in pm.group(2).split()[:nv]]
        faces.append(ids)
        if len(faces) == n: break
    return faces

def faceAreaCentroid(pts, face):
    """Compute triangulated face area (magnitude) and centroid for a polygon."""
    n = len(face)
    if n < 3: return 0.0, (0,0,0)
    total_area = 0.0
    cx = cy = cz = 0.0
    p0 = pts[face[0]]
    for i in range(1, n-1):
        p1 = pts[face[i]]
        p2 = pts[face[i+1]]
        # triangle area = 0.5 * |(p1-p0) x (p2-p0)|
        ax = p1[0]-p0[0]; ay = p1[1]-p0[1]; az = p1[2]-p0[2]
        bx = p2[0]-p0[0]; by = p2[1]-p0[1]; bz = p2[2]-p0[2]
        nx = ay*bz - az*by
        ny = az*bx - ax*bz
        nz = ax*by - ay*bx
        a = 0.5 * math.sqrt(nx*nx + ny*ny + nz*nz)
        # centroid of triangle
        gx = (p0[0]+p1[0]+p2[0])/3
        gy = (p0[1]+p1[1]+p2[1])/3
        gz = (p0[2]+p1[2]+p2[2])/3
        total_area += a
        cx += a*gx; cy += a*gy; cz += a*gz
    if total_area > 0:
        return total_area, (cx/total_area, cy/total_area, cz/total_area)
    return 0.0, (0,0,0)

# ---- Main ----
patches = readPatchList()
print("Patches:", [(n,f,s) for n,f,s in patches])

outlet = next((p for p in patches if p[0]=='outlet'), None)
main_inlet = next((p for p in patches if p[0]=='main_inlet'), None)
assert outlet and main_inlet

print(f"\nReading mesh (this may take 10-30s for 1.17M faces)...")
print("Points...")
pts = readPointsBinary(polyMesh/'points')
print(f"  {len(pts)} points")
print("Faces...")
faces = readFaces(polyMesh/'faces')
print(f"  {len(faces)} faces")

# Compute outlet face areas
print("\nComputing outlet face areas...")
out_name, out_nFaces, out_startFace = outlet
areas = []
for i in range(out_nFaces):
    a, c = faceAreaCentroid(pts, faces[out_startFace + i])
    areas.append(a)
totalArea_out = sum(areas)
print(f"  outlet: {out_nFaces} faces, total area = {totalArea_out:.6f} m^2")

# ---- H2 on outlet ----
print("\nReading H2 field values on outlet...")
h2_vals = readPatchFaceValues(timeDir/'H2', 'outlet')
if isinstance(h2_vals, tuple) and h2_vals[0]=='UNIFORM':
    print(f"  H2 uniform {h2_vals[1]} on outlet")
    h2_mean = h2_vals[1]
    h2_std = 0.0
else:
    print(f"  {len(h2_vals)} H2 face values")
    # Area-weighted mean and stddev
    num = sum(h2_vals[i]*areas[i] for i in range(len(h2_vals)))
    h2_mean = num / totalArea_out
    var_num = sum(((h2_vals[i]-h2_mean)**2)*areas[i] for i in range(len(h2_vals)))
    h2_var = var_num / totalArea_out
    h2_std = math.sqrt(h2_var)

cov = (h2_std / h2_mean) if h2_mean > 0 else float('nan')

# Expected mean from mass balance
rho_H2   = 6.9e6*2.016e-3 / (8.314*288)
rho_CH4  = 6.9e6*16.043e-3 / (8.314*288)
# mass flow rates (assuming pipe r=0.23, branch r=0.0575)
mdot_main   = rho_CH4 * 10.0 * math.pi*0.23**2
# Branch inlet power-law not used; just uniform 32 m/s over r=0.0575
mdot_branch = rho_H2 * 32.0 * math.pi*0.0575**2
Y_H2_expected = mdot_branch / (mdot_main + mdot_branch)

print(f"\n====  MIXING METRICS  ====")
print(f"  H2 area-avg at outlet    = {h2_mean:.6f}")
print(f"  H2 area-stddev at outlet = {h2_std:.6f}")
print(f"  Mixing CoV (SD/mean)     = {cov:.4f}")
print(f"  Expected Y_H2 (mass bal) = {Y_H2_expected:.6f}")
print(f"  Deviation from balance   = {(h2_mean-Y_H2_expected)/Y_H2_expected*100:+.1f} %")

# ---- Pressure drop ----
# Use p (absolute) - more physical than p_rgh for reported dP
p_inlet_vals  = readPatchFaceValues(timeDir/'p', 'main_inlet')
p_outlet_vals = readPatchFaceValues(timeDir/'p', 'outlet')
prgh_inlet_vals  = readPatchFaceValues(timeDir/'p_rgh', 'main_inlet')
prgh_outlet_vals = readPatchFaceValues(timeDir/'p_rgh', 'outlet')

def areaAvg(vals, areas, nFaces):
    if isinstance(vals, tuple) and vals[0]=='UNIFORM':
        return vals[1]
    num = sum(vals[i]*areas[i] for i in range(len(vals)))
    den = sum(areas[:len(vals)])
    return num/den if den>0 else 0.0

# main_inlet areas
main_areas = []
for i in range(main_inlet[1]):
    a, c = faceAreaCentroid(pts, faces[main_inlet[2] + i])
    main_areas.append(a)

p_in = areaAvg(p_inlet_vals, main_areas, main_inlet[1])
p_out = areaAvg(p_outlet_vals, areas, out_nFaces)
prgh_in = areaAvg(prgh_inlet_vals, main_areas, main_inlet[1])
prgh_out = areaAvg(prgh_outlet_vals, areas, out_nFaces)

print(f"\n====  PRESSURE METRICS  ====")
print(f"  p      @ main_inlet = {p_in:.2f} Pa")
print(f"  p      @ outlet     = {p_out:.2f} Pa")
print(f"  dP (p)              = {p_in - p_out:.2f} Pa = {(p_in-p_out)/1000:.3f} kPa")
print(f"  p_rgh  @ main_inlet = {prgh_in:.2f} Pa")
print(f"  p_rgh  @ outlet     = {prgh_out:.2f} Pa")
print(f"  dP (p_rgh)          = {prgh_in - prgh_out:.2f} Pa = {(prgh_in-prgh_out)/1000:.3f} kPa")
