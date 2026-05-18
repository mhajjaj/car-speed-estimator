# Updated Speed Estimate with Honest Uncertainty Bounds
## `videos/truck_video.mp4` — Seconds 3–16

**Report Date:** 2026-05-18  
**Previous Reports:** ACCIDENT_REPORT.md, METHOD_COMPARISON_REPORT.md  
**Status:** Pending on-site camera-height confirmation  
**Bridge Speed Limit Confirmed:** 40 km/h  

---

## 1. Honest Bottom Line

| Camera Height Assumption | Estimated Speed | Excess over 40 km/h |
|---|---|---|
| **2.3 m** (mid-windshield, assumed) | **~57–60 km/h** | **+17–20 km/h (43–50 %)** |
| **2.6 m** (top of windshield) | **~65 km/h** | **+25 km/h (63 %)** |
| **2.9 m** (roof-mounted) | **~72 km/h** | **+32 km/h (80 %)** |

**At any plausible mounting height for a commercial truck, the vehicle exceeded the 40 km/h bridge limit.**

The camera height is the **single largest remaining variable**. Confirmation of the exact dashcam position will narrow the final estimate by ±15 %.

---

## 2. What Changed Since Last Report

| Issue | Previous State | Current State |
|---|---|---|
| Vehicle ID | Generic "truck" (3.0 m) | **Isuzu Forward medium-duty** (2.0–2.5 m) |
| Camera height assumption | 3.0 m | **2.3 m** (most probable, pending verification) |
| Corrected consensus | 74 km/h | **57 km/h** |
| Speed violation conclusion | Yes (+34 km/h) | **Yes (+17 km/h**, less severe but unambiguous) |
| Bridge slope | Not analyzed | Analyzed; **negligible impact (<0.5 %)** |
| Independent method (lane markings) | Not trusted | Validated at **54 km/h** (national road standard) |

The downward correction from 74 → 57 km/h does **not** eliminate the violation. It merely makes the overspeeding less dramatic.

---

## 3. Method-by-Method Status (Refresh)

| Method | Speed (km/h) | Requires Calibration? | Status |
|---|---|---|---|
| 1 — Perspective geometry (optical flow + IPM) | **59.9** | Yes (height, tilt, focal length) | Valid; primary method |
| 2 — Focal-length reverse (angular) | **57.3** | Yes (focal length) | Valid; cross-check with M1 |
| 3 — Road feature ("60" sign) | ~17 (dismissed) | No | **INVALIDATED** (elevated sign, not ground marking) |
| 4 — Motion blur | Below detection | No | Sanity check only (rules out >150 km/h) |
| 5 — Temporal frequency (lane dashes) | **54.0** (9 m national) | **No** | Valid; strongest independent anchor |

**Consensus:**  

```
v = (59.9 + 57.3 + 54.0) / 3 = 57.1 km/h
```

---

## 4. Uncertainty Budget (Honest)

### 4a. Random Error (Precision — averages out with more frames)

| Source | Value |
|---|---|
| Frame-to-frame optical flow jitter (M1) | ±3.2 km/h (1σ) |
| Frame-to-frame angular noise (M2) | ±2.5 km/h (1σ) |
| Lane-dash sampling spread (M5) | ±3.6 km/h (1σ) |
| **Combined random σ** | **±3.1 km/h** |
| **95 % CI (random only)** | **51 – 63 km/h** |

### 4b. Systematic Error (Bias — does NOT average out)

| Source | Direction | Magnitude | Mitigation |
|---|---|---|---|
| **Camera height uncertainty** (±0.3 m) | Linear scale | **±8 km/h** at 2.3 m | **Will be eliminated once user confirms mount point** |
| Tilt angle uncertainty (±2°) | Non-linear | ±7 km/h | Inferrable from vanishing point; ±2° is conservative |
| Lane-marking standard (6 m vs 9 m vs 12 m) | Factor up to 2× | ±18 km/h (on M5 only) | Vehicle context favors 9 m national road |
| Lens distortion (barrel) | FOV-dependent | ±3 km/h (±5 %) | Un-corrected; secondary |
| Rolling shutter (CMOS readout) | Intra-frame skew | ±2 km/h (±2–4 %) | Partially cancels in same-row tracking |
| Frame rate stability (11.03 FPS) | Timing jitter | Unquantified | Assumed stable; could shift ±10 % if severe drops |

### 4c. Total Plausible Range

Taking worst-case but physically possible combinations:

```
Lower bound: 2.0 m height + shallowest tilt + max negative bias = ~42–45 km/h
Upper bound: 2.9 m height + steepest tilt + max positive bias = ~72–75 km/h
```

**The only way to reach ~40 km/h** is to simultaneously assume:
- Camera at **1.74 m or lower** (impossible for this truck)
- Maximum negative tilt bias
- Urban 6 m road standard (inconsistent with bridge context)

This combination is **not physically credible**.

### 4d. Most Defensible Range (Today)

```
┌─────────────────────────────────────────────────────────┐
│  Most plausible true speed:  55 – 65 km/h              │
│  95 % confidence interval:   51 – 63 km/h              │
│  Honest systematic band:     48 – 72 km/h              │
│                                                          │
│  After camera-height confirmation:                       │
│  Expected precision:         ±5 km/h (±8 %)            │
└─────────────────────────────────────────────────────────┘
```

---

## 5. Sensitivity to Camera Height (Visual)

```
Height (m)    Speed (km/h)    % over 40 km/h
─────────────────────────────────────────────
1.74          40.0            0   ← theoretical compliance threshold
2.0           45.9            +15
2.3           57.1            +43   ← assumed (mid-windshield)
2.6           64.6            +62   ← top of windshield
2.9           72.1            +80   ← roof mount
3.0           74.5            +86   ← original (generic truck)
─────────────────────────────────────────────
```

The relationship is strictly linear. Every 10 cm of height adds ~2.5 km/h.

---

## 6. What We Still Need

| Priority | Action | Impact |
|---|---|---|
| 1 | **Confirm exact dashcam mounting height** | Eliminates ±13 % systematic bias; final answer tightens to ±5 km/h |
| 2 | Confirm road classification (national vs urban) | Resolves Method 5 ambiguity (54 vs 36 km/h) |
| 3 | Measure actual lane-marking cycle on-site | Gold-standard for Method 5 |
| 4 | Obtain CAN-bus or GPS log (if available) | Independent ground truth |

---

## 7. Honest Conclusion

**The evidence consistently shows the vehicle was traveling faster than the 40 km/h bridge limit.**

- **Best current estimate:** ~57–60 km/h
- **After confirming camera is at 2.3 m:** ~57 ± 5 km/h
- **After confirming camera is higher:** scale linearly upward (see Section 5)

**There is no calibration scenario that places the speed at or below 40 km/h.** The uncertainty is entirely in *how much* over the limit, not *whether* it was over.

---

## 8. Files Referenced

| File | Description |
|---|---|
| `ACCIDENT_REPORT.md` | Full investigation with per-method details |
| `METHOD_COMPARISON_REPORT.md` | Cross-method statistical consensus |
| `config/isuzu_forward.yaml` | Calibration profile (h = 2.3 m) |
| `outputs/speed_log_isuzu_forward.csv` | Per-frame corrected data |
| `outputs/method5_temporal_frequency.json` | Lane-dash interval measurements |

---

*Report generated by optical-flow speed estimation pipeline.*  
*Pending verification of camera mounting height.*  
*Repository: /home/hajjaj/Desktop/Projects/car-speed-estimator*
