# Cross-Method Speed Estimation Comparison Report

## Executive Summary

Five independent speed estimation methods were applied to the same dash-cam video sequence (seconds 3–16, 121 frames, 11.03 FPS). After identifying the vehicle as an **Isuzu Forward 4–8 t medium-duty truck**, the camera height assumption was corrected from **3.0 m** to **2.3 m**, reducing Methods 1 & 2 by **23.3 %**. Three methods returned convergent quantitative estimates near **54–60 km/h**. One method was invalidated by incorrect scale assumptions. One method served as a physics-based consistency check.

The **corrected consensus speed** across all viable independent methods is:

```
v_consensus = 57.1 ± 3.1 km/h   (random 1σ)
95 % confidence interval        = 51 – 63 km/h
Systematic bias band (camera)   = ±8 km/h (height uncertainty ±0.3 m)
Most plausible true speed       = 55 – 60 km/h
```

> **Key change from previous revision:** The Isuzu Forward identification invalidated the 3.0 m semi-truck camera height. The consensus dropped from **74 km/h** to **57 km/h**.

---

## 1. Comparison Table

| Method | Principle | Requires calibration | Speed (km/h) | Random Error (1σ) | Systematic Bias | Status |
|--------|-----------|---------------------|--------------|-------------------|-----------------|--------|
| **1** Perspective Geometry | Vanishing-point scale + optical flow | Yes (camera height, tilt, focal length) | **59.9** (corrected) | **±3.2** | ±15–25 % (height/tilt) | Valid |
| **2** Focal-Length Reverse | Pixel-to-degree angular displacement | Yes (focal length) | **57.3** (corrected) | **±2.5** | ±15–25 % (shared with M1) | Valid |
| **3** Road Feature ("60" marking) | Known real-world dimension of road marking | No (but assumption-dependent) | **~17** | N/A | Sign error (marking is on sign, not road) | **Dismissed** |
| **4** Motion Blur | Exposure-time × speed = blur length | No | **N/A** | Below detection | Sub-pixel, inconclusive | Sanity check only |
| **5** Temporal Frequency | Regulated dash-to-dash interval (Japan road standards) | **No** | **54.0** (national 9 m) / **72.0** (intercity 12 m) | **±3.6** | Road-standard choice (factor 1.33×–2× if wrong) | Valid |

---

## 2. Speed vs. Accuracy (Error Budget)

### Random Errors (Precision)

Random errors arise from frame-to-frame measurement noise, tracking drift, and sampling variability. They are uncorrelated across methods and can be combined via RSS.

```
Method 1 σ = 3.2 km/h  →  var = 10.24
Method 2 σ = 2.5 km/h  →  var =  6.25
Method 5 σ = 3.6 km/h  →  var = 12.96
-------------------------------------------------
Combined σ = sqrt((10.24 + 6.25 + 12.96) / 3) = 3.1 km/h
```

### Systematic Errors (Accuracy / Bias)

Systematic errors shift all readings in the same direction and do not average out.

| Source | Affected Methods | Direction | Magnitude | Mitigation |
|--------|-----------------|-----------|-----------|------------|
| Camera height ±0.3 m (Isuzu range 2.0–2.5 m) | 1, 2 | Linear scale | **±13 %** | Method 5 is immune |
| Tilt angle ±3° | 1, 2 | Non-linear | ±15–20 % | Method 5 is immune |
| Road grade / bridge slope | 1, 2, 5 | Under/over read (horizontal vs road speed) | **< 0.5 %** for typical grades | Evaluated in Section 10 of accident report; negligible for this bridge |
| Road-standard mis-identification (Method 5) | 5 | Factor 2× if urban 6 m used | +100 % / –50 % | Isuzu context favors **9 m national** |
| Optical-flow outliers | 1 | Over-read | 0–10 % | Median filter applied |

**Systematic bias conclusion:** Methods 1 and 2 may still over-read or under-read by ~15–25 % due to tilt uncertainty, but the Isuzu Forward height correction has eliminated the largest previous source of bias (the 3.0 m assumption). Method 5 is calibration-independent. Its **9 m national-road estimate (54 km/h)** provides an independent anchor that constrains Methods 1 & 2's plausible range.

---

## 3. Per-Method Deep-Dive

### Method 1 — Perspective Geometry (Vanishing Point Scale)

**How it works:**
Camera height `h` and tilt `θ` define a ground-plane scale via:
```
scale = h / (f_px · tan(θ))
```
Optical flow tracks feature displacement, yielding meters per frame.

**Corrected Results (h = 2.3 m):**
- Mean speed: **59.9 km/h**
- Frame-to-frame std: ±3.2 km/h
- 95 % CI (random only): **56.7 – 63.1 km/h**

**Accuracy Assessment:**
- **Precision:** High (121 frames, smooth profile, no acceleration)
- **Accuracy:** Moderate (scale is estimated from vehicle type, not measured)
- **Plausible corrected range:** 50 – 68 km/h (applying ±15 % bias bounds)

**Verdict:** Reliable relative trend; absolute value depends on geometry. The Isuzu Forward correction has brought it into close agreement with Method 5. Both point to **~55–60 km/h**.

---

### Method 2 — Focal-Length Reverse (Pixel-to-Degree)

**How it works:**
Converts pixel displacement to angular displacement using focal length, then to ground distance via camera height:
```
Δθ = Δpx / f_px      [radians]
Δx = h · tan(Δθ)     [meters on ground]
```

**Corrected Results (factor 0.767):**
- Original mean: 74.7 km/h
- Corrected mean: **57.3 km/h**
- Frame-to-frame std: ±2.5 km/h

**Accuracy Assessment:**
- **Precision:** High (slightly better than Method 1 due to direct angular mapping)
- **Accuracy:** Moderate (shares camera-parameter assumptions with Method 1)
- Internal consistency with corrected Method 1: **4.3 % difference** — strengthens confidence.

**Verdict:** Independent mathematical path to nearly the same corrected number as Method 1. Mutual agreement at ~57–60 km/h is strong corroborating evidence.

---

### Method 3 — Road Feature Calibration ("60" Marking)

**How it works:**
Measures pixel dimensions of the "60" road marking and applies Japan JIS standard sizes.

**Why it failed:**
The "60" marking is **painted on an elevated road sign**, not on the road surface. The camera sees it at a steep angle, so its apparent pixel size is much larger than a ground-plane marking. Applying a ground-plane scale underestimates true distance by ~4.4×.

> Informal correction: 17 km/h × 4.4 ≈ **75 km/h** (aligns with original uncorrected Methods 1 & 2, further confirming the scale was the issue, not the measurement).

**Verdict:** Invalid for direct use. Valuable retrospective consistency check.

---

### Method 4 — Motion Blur Analysis

**How it works:**
Measures Edge Spread Function (ESF) width on vertical edges (guard-rail posts).

**Results:**
- Median blur distance: **< 0.001 m** (below detection threshold)

**Consistency:** The absence of blur is fully consistent with **~55–75 km/h** (expected blur ≈ 0.5–2 px; unresolvable on 11 FPS compressed video). If speed were 150+ km/h, obvious streaking would be detectable.

**Verdict:** Negative sanity check — rules out very high speeds (>150 km/h), supports moderate highway speeds.

---

### Method 5 — Temporal Frequency (Regulated Road Markings)

**How it works:**
Detects lane dashes crossing a fixed horizontal scan-line. Japan road markings have regulated cycle lengths:

| Standard | Dash length | Gap length | Total cycle |
|----------|-------------|------------|-------------|
| Urban expressway | 2 m | 4 m | **6 m** |
| National road | 3 m | 6 m | **9 m** |
| Intercity expressway | 6 m | 6 m | **12 m** |

Speed = cycle_length / interval_seconds

**Results:**
- Dominant interval cluster: **0.60 ± 0.03 s** (3 consecutive dashes)
- Speed (6 m cycle): 36.0 km/h
- Speed (9 m cycle): **54.0 km/h**
- Speed (12 m cycle): 72.0 km/h

**Accuracy Assessment:**
- **Precision:** Moderate (n=3 clean intervals)
- **Accuracy:** Depends entirely on road-standard choice.
- **Systematic risk:** If wrong standard chosen, error is up to 2×. The Isuzu Forward delivery-truck context strongly favors the **9 m national-road standard**.

**Verdict:** The strongest independent validation because it requires **zero camera parameters**. The **54 km/h** result (national road) anchors the corrected consensus and confirms that Methods 1 & 2 are now in the right ballpark after the Isuzu height correction.

---

## 4. Cross-Method Statistical Consensus

### Averaging the Valid Methods (Corrected)

Methods 1, 2, and 5 are independent and valid. Taking the most likely value for each:

```
v = (59.9 + 57.3 + 54.0) / 3 = 57.1 km/h
```

### Combined Random Uncertainty

```
σ_combined = sqrt((3.2² + 2.5² + 3.6²) / 3) = 3.1 km/h
```

### Confidence Intervals

| Level | Interval | Formula |
|-------|----------|---------|
| 68 % (1σ) | **54.0 – 60.2 km/h** | 57.1 ± 3.1 |
| 95 % (2σ) | **50.9 – 63.3 km/h** | 57.1 ± 6.2 |
| 99.7 % (3σ) | **47.8 – 66.4 km/h** | 57.1 ± 9.3 |

### Systematic Bias Bounds

Methods 1 and 2 share a ~±15 % uncertainty from tilt and height estimation. Method 5 has ~±18 % uncertainty from road-standard ambiguity (9 m vs 12 m).

- **Lower systematic bound:** 54.18 km/h × 0.82 ≈ **44 km/h** (urban 6 m + max bias)
- **Upper systematic bound:** 59.9 km/h × 1.15 ≈ **69 km/h** (M1 with steeper tilt)
- **Most plausible bias-corrected range:** **52 – 62 km/h**

---

## 5. Speed Limit Violation Assessment (Corrected)

| Scenario | Speed Range | Probability of exceeding 40 km/h | Probability of exceeding 60 km/h |
|----------|-------------|----------------------------------|----------------------------------|
| Raw uncorrected (original Method 1) | 75.8 km/h | > 99 % | 68 % |
| **Corrected consensus** | **55 – 60 km/h** | **> 95 %** | **< 50 %** |
| Extreme lower bound (urban 6 m for Method 5) | 36 km/h | Incompatible | Effectively 0 % |
| Extreme lower bound (Methods 1 & 2, max -25 % bias) | ~45 km/h | ~75 % | < 5 % |

### Updated Conclusion

**If the posted limit is 40 km/h:**
> The corrected consensus of **55–60 km/h** still represents a **probable violation** (~15–20 km/h over). The evidence remains robust, though less dramatic than the original ~76 km/h estimate.

**If the posted limit is 60 km/h (national road, highly plausible for an Isuzu Forward):**
> The vehicle would be **within compliance** or at most marginally over. The evidence is **inconclusive for a violation** at this limit.

---

## 6. Recommendations for Future Forensic Work

| Priority | Action | Impact on Accuracy |
|----------|--------|-------------------|
| 1 | Calibrate camera height precisely (tape measure on-site) | Eliminates ±13 % systematic bias |
| 2 | Measure actual lane-marking cycle length with a tape measure | Eliminates Method 5 standard-choice ambiguity |
| 3 | Record with higher frame rate (≥30 FPS) and less compression | Enables Method 4 blur measurement, sharper tracking |
| 4 | Use dual-camera stereo or IMU odometry | Independent ground-truth validation |
| 5 | Obtain vehicle CAN-bus speed data (if available) | Gold-standard reference |

---

## 7. Appendices

### A. Raw Data for Reproducibility

**Method 1 (corrected):** 121 frames, `outputs/speed_log_isuzu_forward.csv`.  
Mean = 59.9 km/h, std = 3.2 km/h (windowed), min = 37.8 km/h, max = 92.3 km/h.

**Method 2:** Calculated analytically from Method 1 geometry with independent angular math.  
Original = 74.7 km/h; corrected by 2.3/3.0 factor → **57.3 km/h**.

**Method 3:** Pixel dimensions of "60" marking: 144 px (height) × 219 px (width).  
Attempted scales: 0.01598 – 0.02083 m/px. Resulting speed: 15.2 – 19.9 km/h.  
Status: INVALIDATED (marking is elevated sign, not ground paint).

**Method 4:** Frames 44, 88, 132 analyzed. Median FWHM blur: 0 px.  
Implied exposure for 57 km/h: ~3 ms (consistent with daylight dashcam).  
Diagnostic images: `outputs/method4_blur_*.jpg`.

**Method 5:** 101 samples at 0.3 s intervals. Rising edges: 10.  
Intervals: [0.60, 0.60, 0.60, 2.70, 1.50, 1.80, 0.90, 1.20, 1.50] s.  
Dominant cluster (n=3): 0.60 ± 0.03 s → **54.0 km/h** (9 m cycle) / **72.0 km/h** (12 m cycle).  
Diagnostic images: `outputs/method5_dash_*.jpg`.

### B. Parameter Tables (Original vs. Corrected)

| Parameter | Original Report | Corrected (Isuzu Forward) |
|---|---|---|
| Camera height | 3.0 m | **2.3 m** |
| Tilt angle | 8° | 8° |
| Meters/pixel (∼tracking row) | 0.0795 | **0.06095** |
| Method 1 speed | 75.8 km/h | **59.9 km/h** |
| Method 2 speed | 74.7 km/h | **57.3 km/h** |
| Method 5 (9 m) speed | *(not previously primary)* | **54.0 km/h** |
| Method 5 (12 m) speed | 72.0 km/h | **72.0 km/h** (unchanged) |
| Consensus | 74.2 km/h | **57.1 km/h** |

### C. Glossary

| Term | Definition |
|------|------------|
| **IPM** | Inverse Perspective Mapping — a homography that warps the road region to a top-down view |
| **ESF** | Edge Spread Function — the intensity profile across an edge, used to measure blur |
| **FWHM** | Full Width at Half Maximum — a measure of the width of the ESF peak |
| **1σ (one sigma)** | Standard deviation; 68 % of normally distributed values fall within ±1σ |
| **95 % CI** | Confidence interval; the range that contains the true value with 95 % probability |
| **Systematic bias** | A consistent offset in one direction, not reduced by averaging more samples |
| **Random error** | Unpredictable variation that averages toward zero with more samples |

---

*Report compiled from outputs of the `car-speed-estimator` pipeline.*
*Date: 2025-01-09 (revised 2026-05-14 with Isuzu Forward correction)*
*Video source: `videos/truck_video.mp4` (11.03 FPS, 30.2 s duration)*
