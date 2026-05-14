"""
Method 5: Lane Marking Temporal Frequency
"""
import cv2, numpy as np, json, os

VIDEO = os.path.join(os.getcwd(), "videos/truck_video.mp4")
OUTDIR = os.path.join(os.getcwd(), "outputs")

STANDARDS = {
    "standard_6m_cycle": {"paint_m": 2.0, "gap_m": 4.0, "cycle_m": 6.0, "desc": "Urban expressway / approach road (2+4=6 m)"},
    "standard_9m_cycle": {"paint_m": 3.0, "gap_m": 6.0, "cycle_m": 9.0, "desc": "Some national roads (3+6=9 m)"},
    "standard_12m_cycle": {"paint_m": 6.0, "gap_m": 6.0, "cycle_m": 12.0, "desc": "Intercity expressway (6+6=12 m)"},
}


def detect_dash_in_frame(frame, scan_y_ratio=0.85, visualize=False):
    h, w = frame.shape[:2]
    scan_y = int(h * scan_y_ratio)
    roi = frame[max(0, scan_y - 20):min(h, scan_y + 20), :]
    if roi.size == 0:
        return False, None
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    x_start = int(w * 0.20)
    x_end = int(w * 0.80)
    mask[:, :x_start] = 0
    mask[:, x_end:] = 0
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    white_count = np.count_nonzero(mask)
    white_ratio = white_count / mask.size
    dash_present = white_ratio > 0.015
    if visualize:
        vis = roi.copy()
        vis[mask > 0] = vis[mask > 0] * 0.5 + np.array([0, 255, 0], dtype=np.uint8) * 0.5
        cv2.line(vis, (0, 20), (w, 20), (0, 0, 255), 1)
        stat = f"white={white_ratio:.4f} dash={'YES' if dash_present else 'NO'}"
        cv2.putText(vis, stat, (10, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        return dash_present, vis
    return dash_present, None


def analyze_dash_frequency(video_path, scan_y_ratio=0.85, sample_interval=0.5):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total / fps if fps > 0 else 0
    timestamps = np.arange(0, duration, sample_interval)
    dash_states = []
    for t in timestamps:
        idx = int(t * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            dash_states.append((float(t), False))
            continue
        present, _ = detect_dash_in_frame(frame, scan_y_ratio, visualize=False)
        dash_states.append((float(t), bool(present)))
    cap.release()
    rising_edges = []
    for i in range(1, len(dash_states)):
        t_prev, p_prev = dash_states[i - 1]
        t_curr, p_curr = dash_states[i]
        if not p_prev and p_curr:
            rising_edges.append(float(t_curr))
    intervals = []
    for i in range(1, len(rising_edges)):
        intervals.append(float(rising_edges[i] - rising_edges[i - 1]))
    return [float(t) for t in timestamps], dash_states, rising_edges, intervals


def main():
    print("Method 5: Lane Marking Temporal Frequency Analysis")
    print("=" * 55)
    print(f"Video: {VIDEO}")

    cap = cv2.VideoCapture(VIDEO)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = total / fps if fps > 0 else 0
    cap.release()
    print(f"Video FPS: {fps}")
    print(f"Duration: {duration:.1f}s")

    # Try different scan-line heights
    for scan_y in [0.70, 0.75, 0.80, 0.85, 0.90]:
        print(f"\nScan line at y={scan_y*100:.0f}% ...")
        timestamps, dash_states, rising_edges, intervals = analyze_dash_frequency(
            VIDEO, scan_y_ratio=scan_y, sample_interval=0.5
        )
        print(f"  Total samples: {len(timestamps)}, rising edges: {len(rising_edges)}")
        if len(intervals) > 3:
            print(f"  Intervals: {[round(i, 2) for i in intervals[:10]]}")
            print(f"  Mean: {np.mean(intervals):.2f}s, std: {np.std(intervals):.2f}s")

    # Final run at 0.80 with finer sampling
    print(f"\n--- Final analysis at scan_y=80%, interval=0.3s ---")
    timestamps, dash_states, rising_edges, intervals = analyze_dash_frequency(
        VIDEO, scan_y_ratio=0.80, sample_interval=0.3
    )
    print(f"Rising edges: {len(rising_edges)}")

    # Save diagnostic captures
    cap = cv2.VideoCapture(VIDEO)
    for i, t_edge in enumerate(rising_edges[:6]):
        idx = int(t_edge * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            present, vis = detect_dash_in_frame(frame, scan_y_ratio=0.80, visualize=True)
            path = os.path.join(OUTDIR, f"method5_dash_{i+1}_{int(t_edge)}s.jpg")
            cv2.imwrite(path, vis)
            print(f"  Saved: {path}")
    cap.release()

    results = {
        "method": "Lane Marking Temporal Frequency (Method 5)",
        "description": (
            "Detects lane dashes crossing a fixed horizontal scan-line over time. "
            "Japan expressway lane markings have regulated dimensions (cycle lengths "
            "of 6 m, 9 m, or 12 m). Speed is computed as cycle_length / dash_interval. "
            "Requires NO camera calibration."
        ),
        "video_fps": float(fps),
        "video_duration_seconds": float(duration),
        "scan_y_ratio": 0.80,
        "sample_interval_seconds": 0.3,
        "total_samples": len(timestamps),
        "rising_edges": len(rising_edges),
        "intervals_seconds": intervals,
        "statistics": {},
        "speed_estimates_kmh": {},
    }

    if len(intervals) > 0:
        results["statistics"] = {
            "mean_interval_s": float(np.mean(intervals)),
            "median_interval_s": float(np.median(intervals)),
            "std_interval_s": float(np.std(intervals)),
            "min_interval_s": float(np.min(intervals)),
            "max_interval_s": float(np.max(intervals)),
        }
        print(f"\nMean interval: {np.mean(intervals):.2f}s")
        print(f"Median interval: {np.median(intervals):.2f}s")

        for key, std in STANDARDS.items():
            cycle = std["cycle_m"]
            mean_speed = cycle / np.mean(intervals) * 3.6 if np.mean(intervals) > 0 else 0
            median_speed = cycle / np.median(intervals) * 3.6 if np.median(intervals) > 0 else 0
            results["speed_estimates_kmh"][key] = {
                "description": std["desc"],
                "cycle_m": cycle,
                "mean_speed_kmh": float(mean_speed),
                "median_speed_kmh": float(median_speed),
            }
            print(f"  -> {key}: mean {mean_speed:.1f} km/h, median {median_speed:.1f} km/h")

    out_path = os.path.join(OUTDIR, "method5_temporal_frequency.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved {out_path}")


if __name__ == "__main__":
    main()
