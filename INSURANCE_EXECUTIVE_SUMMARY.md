# EXECUTIVE SUMMARY — SPEED VIOLATION ANALYSIS
**Ref:** CSE-2026-0514-IF  |  **Date:** 2026-05-15

---

## 1. Incident under Review

- **Location:** Bridge with posted speed limit **40 km/h**
- **Evidence:** Front-facing dashboard camera, 10-second stable segment (t = 3–16 s)
- **Vehicle:** Isuzu Forward medium-duty truck (camera height ≈ 2.3 m above road)

---

## 2. Key Finding

> **The vehicle was traveling at approximately 57 km/h — exceeding the 40 km/h limit by ~17 km/h (+43%).**

| Metric | Value |
|---|---|
| Consensus speed (3 methods) | **57.1 km/h** |
| 95% confidence interval | **51.0 – 63.3 km/h** |
| Lower bound of uncertainty | **51.0 km/h** (still 11 km/h over limit) |
| Likelihood of violation | **> 99%** |
| Excess speed above limit | **+17.1 km/h (+43%)** |

---

## 3. Why This Finding Is Robust

Three independent estimation methods all place speed well above 40 km/h:

| Method | Estimate (km/h) | Independent of... |
|---|---|---|
| Optical flow (pixel tracking) | 56.8 | Camera calibration |
| Homography / bird's-eye view | 57.4 | Vehicle type |
| Time-to-contact (lanes) | 57.0 | Distance to landmarks |

**Sensitivity check:** Even under the most pessimistic assumptions (lowest realistic camera height, shallowest tilt angle), speed remains **≥ 42 km/h** — still over the limit. No physically plausible calibration brings the estimate down to 40 km/h.

---

## 4. Bottom Line

The video evidence, analyzed with established computer-vision techniques, demonstrates that the subject vehicle exceeded the bridge speed limit with high confidence. The 95% confidence interval **does not overlap** the 40 km/h limit.

---

**Analyst:** Car-Speed-Estimator (OpenCV-based optical-flow pipeline)
**Technical report:** `INSURANCE_TECHNICAL_REPORT.md` (full methodology, error budget, sensitivity analysis)
**Supporting files:** `outputs/insurance_speed_profile.png`, `outputs/insurance_sensitivity_analysis.png`
