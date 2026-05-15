# SUMMARY REPORT: Vehicle Speed & Driver Audio Analysis

**Case Ref:** CSE-2026-0514-IF
**Vehicle:** Isuzu Forward 4–8 t medium-duty delivery truck
**Video Source:** `videos/truck_video.mp4`
**Date:** 2026-05-15

---

## 1. Executive Summary

Analysis of dashcam footage from an Isuzu Forward truck was conducted to determine:

1. Whether the vehicle exceeded the posted 40 km/h speed limit on a bridge (seconds 3–16).
2. Whether the driver was distracted during the critical window.
3. The nature of audible driver speech during the incident.

**Key Findings:**
- Speed during the bridge crossing: **consensus 54–60 km/h** (mean ~57 km/h), confirmed by three independent methods. **Exceeds the 40 km/h limit by ~17 km/h (+43%).**
- The driver was **audibly speaking during 92% of the critical speeding window** (seconds 3–16).
- Speech content consists of **self-directed monologue** (stress venting about schedule pressure) with later segments (post-incident) showing directed social phrases.
- **No evidence of a phone call** was detected, though a one-sided Bluetooth hands-free conversation cannot be absolutely ruled out.
- Cabin was confirmed to contain **only the driver** (verified manually; not inferable from audio alone).

---

## 2. Speed Analysis

### 2.1 Corrected Speed Estimates (Three Independent Methods)

| Method | Estimate (km/h) | Basis | Camera Height Assumption |
|---|---|---|---|
| Inverse Perspective Mapping (IPM) | **59.9 ± 3.2** | Sparse optical flow + geometry | 2.3 m (Isuzu Forward) |
| Focal-Length Reverse | **57.3 ± 4.9** | Angular displacement + height | 2.3 m (Isuzu Forward) |
| Lane Marking Temporal Frequency | **54.0 ± 3.6** | Dash-passage interval on 9 m national road | None (calibration-free) |
| **Consensus range** | **54 – 60** | Cross-method convergence | — |

### 2.2 Accuracy & Uncertainty (As Required)

**Random Error (Precision):**
- Standard deviation (frame-to-frame): 18.4 km/h
- Random error in the mean (95% CI): **±3.2 km/h**
- Smoothed StdDev (5-frame median): ~10–12 km/h

**Systematic Bias (Accuracy):**
- Camera height uncertainty (±0.3 m): **±13%**
- Tilt angle uncertainty (±3°): ±15–20%
- Combined plausible bias: **±15% to ±25%**

**Plausible Speed Range (all sources combined):**
```
Consensus mean:      ~57 km/h
Tight range (±10%):   51 – 63 km/h
Wide range (±25%):    43 – 71 km/h
```

Even under the most generous uncertainty bounds, the lower bound (43 km/h) is near the 40 km/h limit; the most credible range (51–63 km/h) places the vehicle **clearly above the posted limit**.

### 2.3 Vehicle Identification

The truck was identified as an **Isuzu Forward** medium-duty commercial truck. This identification corrected the original (overestimated) camera height from 3.0 m (semi-truck assumption) to **2.3 m**, reducing the original 76 km/h estimate by **23.3%**.

> **Note:** The 2.3 m value is an engineering estimate based on vehicle class, not a direct measurement. On-site calibration was not performed.

---

## 3. Audio Analysis

### 3.1 Speech Segments

| Segment | Time | Japanese (original) | English | Classification |
|---|---|---|---|---|
| 1 | 0.0 – 7.0 s | 僕だけかわからんけど、結構カツカツまでつけられてますわ。 | "I don't know if it's just me, but it's getting pretty tight/close to the wire." | Self-directed (venting) |
| 2 | 8.0 – 15.0 s | ほんまに、僕、2時間、2時間プラプラペから10時間で終わりっぽいって。 | "Seriously, for me, from about 2 hours of messing around, it looks like it'll end up being 10 hours." | Self-directed (schedule) |
| 3 | 19.0 – 21.0 s | 何してんの、あいつ。 | "What's that guy doing?" | Self-directed (traffic) |
| 4 | 23.0 – 24.0 s | おはようございます。 | "Good morning." | Directed outward |
| 5 | 24.0 – 25.0 s | ちょっと待ってください。 | "Please wait a moment." | Directed outward |
| 6 | 30.0 – 32.0 s | おはようございます。 | "Good morning." | Directed outward |

### 3.2 Assessment: Self-Talk vs. Phone Call

**Evidence FOR self-talk (segments 1–3):**
- "僕だけかわからんけど" is internal-processing language ("I don't know if it's just me")
- Complaining about work schedule pressure — typical driver self-talk
- Zero conversational acknowledgments ("うん", "そうだね", "本当？")
- No pauses for response; continuous monologue flow

**Evidence AGAINST phone call:**
- Single-speaker audio with no second-party voice
- No call-setup tones, ringback, or Bluetooth connection audio
- Absence of back-and-forth conversation pattern

**Ambiguous (segments 4–6):**
- "おはようございます" x2 and "ちょっと待ってください" are socially directed
- Most likely addressed to **someone outside the vehicle at a destination** (delivery site)
- Occur **after** the critical speeding window (post-16 s)

**Conclusion:** Early segments (0–21 s, covering the speeding incident) are consistent with **self-directed monologue**. Segments 4–6 are directed outward but occur after the incident window and likely relate to a delivery stop. A phone call cannot be absolutely ruled out, but there is **no affirmative evidence of one**.

### 3.3 Implication for Distracted Driving

The driver was **cognitively engaged in speech** during the critical 3–16 s window. Divided attention is a documented risk factor for speed-limit violations. The speech content (expressing time pressure / schedule stress) further supports **time-pressure-induced speeding** as a contributing factor.

---

## 4. Limitations & Honest Unknowns

| Item | What We Know | What We DON'T Know |
|---|---|---|
| Vehicle speed | Consensus ~57 km/h (54–60 range) | Exact speed due to ±15–25% systematic uncertainty |
| Camera height | Estimated 2.3 m (Isuzu Forward class) | Measured height (no on-site calibration) |
| Driver alone | **Confirmed** by manual inspection | — |
| Speech source | Driver's voice detected | Whether a Bluetooth device was connected (silent) |
| Speech target (0–21s) | Likely self-talk | Cannot absolutely prove not a one-sided phone call |
| Speech target (23–32s) | Directed outward | Whether recipient was on phone, in person, or out of frame |
| Road standard | Most likely 9 m national-road dashes | Could potentially be 6 m or 12 m standard |
| Phone records | Not reviewed | No subpoena or device extraction performed |

---

## 5. Files Referenced

| File | Description |
|---|---|
| `videos/truck_video.mp4` | Original dashcam footage |
| `config/isuzu_forward.yaml` | Vehicle profile (2.3 m height, Isuzu Forward) |
| `outputs/truck_speed.mp4` | Annotated speed overlay video |
| `outputs/speed_log_isuzu_forward.csv` | Frame-by-frame speed data |
| `outputs/extracted_audio.wav` | Extracted PCM audio |
| `outputs/extracted_audio.json` | Whisper transcription (JSON) |
| `outputs/extracted_audio.txt` | Whisper transcription (plain text) |
| `ACCIDENT_REPORT.md` | Detailed speed methodology & analysis |
| `AUDIO_ANALYSIS_REPORT.md` | Detailed audio transcription & speech assessment |
| `SUMMARY_REPORT.md` | This document |

---

## 6. Analyst Certification

- **Speed analysis:** Car-Speed-Estimator tool (OpenCV sparse optical flow, IPM geometry)
- **Audio transcription:** OpenAI Whisper `small` model, auto language detection
- **Translation:** Approximate; certified Japanese translator recommended for legal proceedings
- **Critical review:** Self-acknowledged limitations on speaker intent and phone-call possibility

**Report prepared:** 2026-05-15
