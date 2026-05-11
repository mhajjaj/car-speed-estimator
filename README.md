# Car Speed Estimator (Dash Cam)

Estimate your vehicle's speed from a front-facing dash camera using **optical flow** and **inverse perspective mapping (IPM)**.

No GPS, no OBD, no AI model — just classic computer vision.

---

## How It Works

1. **Region of Interest (ROI)** — Focus on the road surface, ignore sky/trees/cars.
2. **Feature Tracking (Lucas-Kanade)** — Track texture points on asphalt between frames.
3. **Bird's-Eye Transform (IPM)** — Map the road to a top-down view so pixel motion equals real-world motion.
4. **Speed = Distance / Time** — Convert median displacement to km/h.

The key trick: the road is a flat plane. Once you know your camera height/angle, you can convert pixels to meters.

---

## Project Structure

```
car-speed-estimator/
├── config/
│   ├── family_car.yaml      # Sedan / hatchback profile
│   └── truck.yaml           # Truck / high-mount profile
├── src/
│   ├── calibrate.py         # Interactive calibration tool
│   └── estimate_speed.py    # Main speed estimator
├── videos/                  # Put your dash cam files here
├── outputs/                 # Processed videos saved here
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Choose / calibrate your vehicle profile

**Option A — Quick geometry estimate (rough, no tools needed):**

```bash
python src/calibrate.py --profile config/family_car.yaml --geometry
```

**Option B — Accurate calibration (recommended):**

Park on a flat surface with visible markings (e.g., a 2.5m x 4m parking bay).
Take a still photo from the dash cam and run:

```bash
python src/calibrate.py \
    --profile config/family_car.yaml \
    --image assets/calibrate.jpg \
    --width 2.5 \
    --height 4.0
```

Click the 4 corners on screen in order: top-left, top-right, bottom-right, bottom-left.
The tool saves the homography and `meters_per_pixel` back into the YAML.

### 3. Run speed estimation

```bash
python src/estimate_speed.py \
    --video videos/drive.mp4 \
    --profile config/family_car.yaml \
    --output outputs/result.mp4
```

**Keys during playback:**

| Key | Action |
|-----|--------|
| `Q` / `ESC` | Quit |
| `P` | Pause |
| `R` | Reset tracked points |
| `D` | Toggle IPM debug view |

---

## Truck vs. Family Car — What's Different?

| Parameter | Family Car | Truck |
|-----------|-----------|-------|
| Camera height | ~1.2m | ~3.0m |
| Tilt angle | ~15 deg | ~8 deg (flatter) |
| ROI on screen | Lower 40–85% | Middle 50–75% (hood blocks bottom) |
| Meters per pixel | ~0.035 | ~0.060 |

The estimator uses YAML vehicle profiles so you can switch configs without touching code.
If your vehicle isn't listed, copy `family_car.yaml` to `my_car.yaml` and edit the numbers. Height and tilt are the most important.

---

## Accuracy Notes

- Best on **flat, textured roads** (asphalt, concrete).
- Avoid rain, heavy shadows, and strong lens flare.
- The IPM assumes a flat ground plane. Hills / ramps will bias the reading.
- Calibration is the biggest factor — measure your reference rectangle carefully.
- Expect **±5 km/h** accuracy under good conditions; this is not a replacement for GPS.

---

## TODO / Ideas

- [ ] Lane-detection fallback when optical flow fails (uniform road surface)
- [ ] Kalman filter for smoother speed output
- [ ] Live webcam / RTSP dash cam support
- [ ] Save speed log to CSV alongside video
- [ ] Speed limit sign detection overlay

---

## License

MIT — use at your own risk on the road.
