"""
Method 4: Motion Blur Analysis
Measures horizontal edge-spread-function on vertical structures.
"""
import cv2, numpy as np, json, os

VIDEO = os.path.join(os.getcwd(), "videos/truck_video.mp4")
OUTDIR = os.path.join(os.getcwd(), "outputs")
SCALE = 0.0790

def measure_edge_spread(frame, x, y, window_half=20):
    h, w = frame.shape[:2]
    y0, y1 = max(0, y - window_half), min(h, y + window_half)
    x0, x1 = max(0, x - window_half), min(w, x + window_half)
    patch = frame[y0:y1, x0:x1]
    if patch.size == 0:
        return None
    gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY) if len(patch.shape) == 3 else patch
    profile = np.mean(gray.astype(np.float32), axis=0)
    if profile.max() - profile.min() < 15:
        return None
    profile = (profile - profile.min()) / (profile.max() - profile.min() + 1e-6)
    grad = np.abs(np.diff(profile))
    cx = int(np.argmax(grad))
    if cx < 2 or cx >= len(profile) - 2:
        return None
    half = 0.5
    left_idx = cx
    while left_idx > 0 and profile[left_idx] > half:
        left_idx -= 1
    right_idx = cx
    while right_idx < len(profile) - 1 and profile[right_idx] > half:
        right_idx += 1
    if profile[left_idx] < half < profile[left_idx + 1]:
        t = (half - profile[left_idx]) / (profile[left_idx + 1] - profile[left_idx] + 1e-6)
        left = left_idx + t
    else:
        left = float(left_idx)
    if profile[right_idx - 1] > half > profile[right_idx]:
        t = (half - profile[right_idx]) / (profile[right_idx - 1] - profile[right_idx] + 1e-6)
        right = right_idx - 1 + t
    else:
        right = float(right_idx)
    return float(right - left)

def detect_vertical_edges(frame):
    h, w = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    abs_sx = np.abs(sobelx)
    mask = np.zeros_like(abs_sx, dtype=np.uint8)
    for y in range(h):
        row = abs_sx[y, :]
        for x in range(3, w - 3):
            if row[x] > row[x - 1] and row[x] > row[x + 1] and row[x] > 80:
                mask[y, x] = 255
    candidates = []
    roi_left = mask[:, :int(w * 0.25)]
    roi_right = mask[:, int(w * 0.75):]
    for roi, x_offset in [(roi_left, 0), (roi_right, int(w * 0.75))]:
        ys, xs = np.where(roi > 0)
        for y, x in zip(ys, xs):
            x += x_offset
            if y < h * 0.3:
                continue
            candidates.append((int(x), int(y)))
    return candidates

def analyze_frame(frame, frame_idx):
    candidates = detect_vertical_edges(frame)
    if len(candidates) == 0:
        return None
    if len(candidates) > 500:
        idx = np.random.choice(len(candidates), 500, replace=False)
        candidates = [candidates[i] for i in idx]
    fwhms = []
    for x, y in candidates:
        fwhm = measure_edge_spread(frame, x, y, window_half=12)
        if fwhm is not None:
            fwhms.append(fwhm)
    if len(fwhms) == 0:
        return None
    fwhms = np.array(fwhms)
    blur_m = fwhms * SCALE
    return {
        "frame": int(frame_idx),
        "num_edges": int(len(fwhms)),
        "fwhm_pixels_mean": float(np.mean(fwhms)),
        "fwhm_pixels_std": float(np.std(fwhms)),
        "fwhm_pixels_median": float(np.median(fwhms)),
        "fwhm_pixels_p10": float(np.percentile(fwhms, 10)),
        "fwhm_pixels_p90": float(np.percentile(fwhms, 90)),
        "blur_m_mean": float(np.mean(blur_m)),
        "blur_m_std": float(np.std(blur_m)),
        "blur_m_median": float(np.median(blur_m)),
    }

def main():
    cap = cv2.VideoCapture(VIDEO)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    results = {
        "method": "Motion Blur Analysis (Method 4)",
        "description": (
            "Measures horizontal edge-spread-function (ESF) width on vertical "
            "structures (guardrail posts, barriers). Motion blur length indicates "
            "distance travelled during camera exposure. For a plausible exposure "
            "time, the blur length must be consistent with vehicle speed."
        ),
        "scale_m_per_px": SCALE,
        "video_fps": fps,
        "speed_to_check_kmh": 75.8,
        "speed_to_check_mps": 75.8 / 3.6,
        "frames_analyzed": [],
    }
    timestamps = [4.0, 8.0, 12.0]
    for t in timestamps:
        idx = int(t * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue
        fr = analyze_frame(frame, idx)
        if fr:
            fr["timestamp_s"] = t
            blur_m = fr["blur_m_median"]
            speed_mps = 75.8 / 3.6
            implied_t = blur_m / speed_mps if speed_mps > 0 else None
            fr["implied_exposure_s_for_75kmh"] = float(implied_t) if implied_t else None
            fr["implied_exposure_ms"] = float(implied_t * 1000) if implied_t else None
            results["frames_analyzed"].append(fr)
            debug = frame.copy()
            candidates = detect_vertical_edges(frame)
            if len(candidates) > 500:
                idxs = np.random.choice(len(candidates), 500, replace=False)
                candidates = [candidates[i] for i in idxs]
            for x, y in candidates:
                cv2.circle(debug, (x, y), 2, (0, 0, 255), -1)
            cv2.putText(debug, f"Method 4 | t={t}s | median blur={fr['fwhm_pixels_median']:.1f}px", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            exp_ms = fr['implied_exposure_ms']
            exp_str = f"{exp_ms:.1f}" if exp_ms is not None else "N/A"
            cv2.putText(debug, f"Implied exposure for 75 km/h: {exp_str} ms", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            path = os.path.join(OUTDIR, f"method4_blur_{int(t)}s.jpg")
            cv2.imwrite(path, debug)
            print(f"  Saved {path}")
    cap.release()
    if results["frames_analyzed"]:
        all_blur = [f["blur_m_median"] for f in results["frames_analyzed"]]
        all_t = [f["implied_exposure_ms"] for f in results["frames_analyzed"] if f["implied_exposure_ms"]]
        results["summary"] = {
            "median_blur_m_across_frames": float(np.median(all_blur)),
            "mean_blur_m_across_frames": float(np.mean(all_blur)),
            "implied_exposure_ms_median": float(np.median(all_t)),
            "implied_exposure_ms_mean": float(np.mean(all_t)),
            "plausible_dashcam_exposure_range_ms": [1.0, 16.7],
            "exposure_consistent_with_75kmh": bool(1.0 <= np.median(all_t) <= 16.7),
        }
        print("\nMethod 4 Results:")
        print(f"  Median blur distance: {results['summary']['median_blur_m_across_frames']:.3f} m")
        print(f"  Implied exposure for 75 km/h: {results['summary']['implied_exposure_ms_median']:.2f} ms")
        print(f"  Typical dashcam daylight exposure: 2-8 ms")
        print(f"  Consistent? {results['summary']['exposure_consistent_with_75kmh']}")
    out_path = os.path.join(OUTDIR, "method4_blur_analysis.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved {out_path}")

if __name__ == "__main__":
    main()
