# Independent Verification Report: Audio & Visual Methods

**Project:** `car-speed-estimator`  
**Video:** `videos/truck_video.mp4` (11.02 FPS, AAC mono audio at 11025 Hz)  
**Analysis Window:** 3.0 s – 16.0 s  
**Date:** 2026-05-18  
**Purpose:** Attempt independent speed verification using (1) audio spectral analysis and (2) bridge structural feature counting, without relying on camera height calibration.

---

## Executive Summary

| Method | Data Quality | Speed Estimate | Usable for Verification? |
|---|---|---|---|
| **Audio spectral / rhythmic analysis** | Moderate (mono AAC, noisy) | **Inconclusive** — pulses exist but source unknown | **No** — cannot attribute pulses to known spacing |
| **Bridge barrier post / structural counting** | Low (11 FPS insufficient) | **Inconclusive** — 2m features blur at 11 FPS | **No** — frame rate too low |
| **Lane-marking temporal frequency (M5, prior)** | Good | **54.0 km/h** (9 m national standard) | **Yes — remains best independent method** |

**Bottom line:** The two new independent methods explored here (audio and structural counting) do not strengthen or weaken the existing ~57 km/h consensus. They fail for honest technical reasons that are documented below. The strongest independent validation remains Method 5 (lane marking cycle timing).

---

## 1. Audio Analysis

### 1.1 What was done

- Extracted mono AAC audio track (11025 Hz native, resampled to 16000 Hz for analysis)
- Computed spectrogram, dominant-frequency track, and amplitude envelope for the 3–16 s window
- Searched for:
  1. Tonal tire/road resonance (expected ~800–1500 Hz)
  2. Rhythmic pulses from expansion joints or regular road texture
  3. Doppler-like frequency shifts

### 1.2 Findings

| Feature | Observation | Interpretation |
|---|---|---|
| **Tonal peaks** | Yes — harmonic stack at ~700–1500 Hz with overtones, strongest in 3–7 s and 10–14 s | Consistent with tire cavity resonance or tread-pattern noise |
| **Rhythmic pulses** | Yes — vertical striations on spectrogram at quasi-regular intervals (~0.2–0.5 s spacing in places) | Could be tire tread impacts, road joints, or bridge expansion joints, BUT source cannot be definitively identified |
| **Doppler shift** | **Not observed** — no diagonal frequency sweeps | Microphone is in-cab (no reflected Doppler); or speed is constant |
| **Signal quality** | Low-to-moderate; strong transient at ~15.5 s likely non-road noise (horn, bump, or external event) | Dashboard microphone picks up cabin noise, wind, vibration |

### 1.3 Why it cannot estimate speed

To convert pulse rate to speed, we must know the **physical spacing** of whatever is causing the pulses:

```
speed = spacing / interval
```

But:
- **Tire tread pitch** is unknown (varies by tire model, wear)
- **Expansion joint spacing** is unknown for this bridge
- The pulses could also be wind buffeting, cabin vibration, or audio compression artifacts

Without knowing the source spacing, the pulse rate is just a number. It confirms the vehicle is moving, but not how fast.

### 1.4 Visual Evidence

| File | Description |
|---|---|
| `outputs/audio_analysis.png` | Spectrogram + waveform (3–16 s) |
| `outputs/audio_dominant_freq.png` | Dominant frequency in 500–3000 Hz band over time |
| `outputs/audio_envelope.png` | Amplitude envelope (potential rhythmic impacts) |
| `outputs/spectrogram_static.png` | Full-video static spectrogram (ffmpeg) |

---

## 2. Bridge Structural Feature Counting

### 2.1 What was done

- Extracted 143 frames from the 3–16 s window at native 11.02 FPS
- Defined a right-side ROI (x=30-80%, y=60-95% of image) focusing on bridge barriers
- Applied two detection algorithms:
  1. **Vertical edge strength (Sobel X)** — detects sharp vertical transitions
  2. **Column intensity variation** — detects shadow/post patterns
- Converted detected event intervals to speed using assumed standard spacings

### 2.2 Findings

| Algorithm | Events Detected | Mean Interval | Implied Speed (2m spacing) | Status |
|---|---|---|---|---|
| Sobel X edge peaks | 15 | 0.829 s | **8.7 km/h** | Too few, non-periodic |
| Column variation peaks | 8 | 1.477 s | **4.9 km/h** | Too few, non-periodic |

### 2.3 Why it failed

**Mathematical impossibility at 11 FPS:**

```
Expected post passing interval at ~57 km/h:
  v = 57 km/h = 15.83 m/s
  post spacing (typical) = 2.0 m
  interval = 2.0 / 15.83 = 0.126 s

Frames available per post at 11.02 FPS:
  frames_per_post = 11.02 × 0.126 = 1.39 frames
```

A feature passing every **1.4 frames** is **below the Nyquist limit** and cannot be reliably resolved. Individual posts merge into a continuous blur.

For comparison, lane markings (Method 5) succeed because their cycle is longer:

```
Method 5 interval at 57 km/h with 9m cycle:
  interval = 9.0 / 15.83 = 0.569 s
  frames_per_cycle = 11.02 × 0.569 = 6.27 frames  ← easily resolvable
```

### 2.4 Visual Evidence

| File | Description |
|---|---|
| `outputs/independent_counting_analysis.png` | Event detection + speed estimates under different spacing assumptions |

---

## 3. Honest Conclusion

### What was attempted
Two genuinely independent methods (audio spectral analysis, bridge feature counting) were tested without any camera-height assumptions.

### What was found
- **Audio**: Confirms motion (tonal tire noise, rhythmic pulses) but cannot quantify speed without knowing the physical source of the pulses.
- **Visual counting**: Technically impossible with 11 FPS for 2m-spaced features.

### What this means for the existing consensus

**Nothing changes.** The existing consensus of **~57 km/h** (Methods 1, 2, and 5) stands unchallenged and unconfirmed by these new attempts.

| Method | Status | Estimate |
|---|---|---|
| Method 1 — Perspective geometry (optical flow + IPM) | Valid, primary | 59.9 km/h |
| Method 2 — Focal-length reverse | Valid, cross-check | 57.3 km/h |
| Method 3 — Road feature ("60" sign) | **Dismissed** | — |
| Method 4 — Motion blur | Sanity check only | Rules out >150 km/h |
| **Method 5 — Lane marking temporal frequency** | **Valid, strongest independent** | **54.0 km/h** |
| Audio spectral analysis | **Inconclusive** (this report) | — |
| Structural feature counting | **Inconclusive** (this report) | — |

### What would make these methods work

| Method | Required Improvement | Expected Result |
|---|---|---|
| Audio | Know tire model (tread pitch) + high-pass filter road noise | Estimate tread-impact rate → wheel RPM → speed (±10-15%) |
| Structural counting | **≥30 FPS video** + confirmed barrier spacing (e.g., measured 2.0m on-site) | Count posts in ROI → speed (±5-10%) |

---

## 4. Files Referenced

| File | Role |
|---|---|
| `src/audio_analysis.py` | Script: audio spectrogram, dominant frequency, envelope |
| `src/independent_counting.py` | Script: bridge feature detection and counting |
| `outputs/audio.wav` | Extracted 16kHz mono PCM audio |
| `outputs/audio_analysis.png` | Spectrogram + waveform |
| `outputs/audio_dominant_freq.png` | Dominant frequency track |
| `outputs/audio_envelope.png` | Amplitude envelope |
| `outputs/spectrogram_static.png` | Full-video static spectrogram |
| `outputs/independent_counting_analysis.png` | Structural counting diagnostics |

---

*Report generated during independent verification attempts.*  
*Honest limitation statement: These methods do not strengthen or weaken the existing consensus. They simply cannot resolve speed with the available data.*
