
import cv2, numpy as np, json, os, statistics

VIDEO = os.path.join(os.getcwd(), "videos/truck_video.mp4")
OUTDIR = os.path.join(os.getcwd(), "outputs")

STANDARDS = {
    "urban_6m": {"cycle_m": 6.0, "desc": "Urban expressway (2+4 m)"},
    "national_9m": {"cycle_m": 9.0, "desc": "National road (3+6 m)"},
    "intercity_12m": {"cycle_m": 12.0, "desc": "Intercity expressway (6+6 m)"},
}

def detect_dash(frame, scan_y_ratio=0.70):
    h, w = frame.shape[:2]
    scan_y = int(h * scan_y_ratio)
    roi = frame[max(0, scan_y-25):min(h, scan_y+25), int(w*0.15):int(w*0.85)]
    if roi.size == 0:
        return False
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    # Otsu thresholding for adaptive detection
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    _, mask = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Morphological opening to remove noise
    kernel = np.ones((3,3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    white_ratio = np.count_nonzero(mask) / mask.size
    return white_ratio > 0.008

def analyze(video_path, scan_y_ratio=0.70, sample_interval=0.1):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total / fps if fps > 0 else 0
    timestamps = np.arange(0, duration, sample_interval)
    states = []
    for t in timestamps:
        idx = int(t * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            states.append((float(t), False))
            continue
        states.append((float(t), detect_dash(frame, scan_y_ratio)))
    cap.release()
    edges = []
    for i in range(1, len(states)):
        if not states[i-1][1] and states[i][1]:
            edges.append(float(states[i][0]))
    intervals = [edges[i]-edges[i-1] for i in range(1, len(edges))]
    return edges, intervals

def main():
    print("Method 5 (Improved): Lane Marking Temporal Frequency")
    cap = cv2.VideoCapture(VIDEO)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = total/fps if fps>0 else 0
    cap.release()
    print(f"Video: {VIDEO}, {fps:.2f} fps, {duration:.1f} s")
    best = {"scan_y": None, "intervals": [], "edges": 0}
    for sy in [0.60, 0.65, 0.70, 0.75, 0.80]:
        edges, intervals = analyze(VIDEO, scan_y_ratio=sy, sample_interval=0.1)
        print(f"  y={sy:.0%}: {len(edges)} edges, intervals={[round(i,2) for i in intervals[:12]]}, median={statistics.median(intervals) if intervals else 'N/A'}")
        if len(intervals) >= 4:
            if best["scan_y"] is None or len(intervals) > len(best["intervals"]):
                best = {"scan_y": sy, "intervals": intervals, "edges": len(edges)}
    print(f"\nBest scan_y = {best['scan_y']:.0%} with {best['edges']} edges")
    intervals = best["intervals"]
    if not intervals:
        print("No usable intervals found.")
        return
    # Robust interval: use median or mode cluster
    med = statistics.median(intervals)
    print(f"Intervals: {[round(i,2) for i in intervals]}")
    print(f"Median interval: {med:.2f}s")
    # Try to find tight cluster
    clusters = []
    for i in intervals:
        c = [x for x in intervals if abs(x-i) < 0.3]
        if len(c) >= 2:
            clusters.append((len(c), statistics.mean(c), c))
    clusters.sort(reverse=True)
    if clusters:
        best_cluster_mean = clusters[0][1]
        print(f"Best cluster (n={clusters[0][0]}): mean={best_cluster_mean:.2f}s")
    else:
        best_cluster_mean = med

    results = {"method5_improved": {},"fps": float(fps), "duration": float(duration)}
    for key, val in STANDARDS.items():
        cycle = val["cycle_m"]
        s_median = cycle / med * 3.6 if med > 0 else 0
        s_cluster = cycle / best_cluster_mean * 3.6 if best_cluster_mean > 0 else 0
        print(f"  {key} ({val['desc']}): median={s_median:.1f} km/h, cluster={s_cluster:.1f} km/h")
        results["method5_improved"][key] = {"cycle_m": cycle, "median_speed": s_median, "cluster_speed": s_cluster}
    out = os.path.join(OUTDIR, "method5_improved.json")
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved {out}")

if __name__ == "__main__":
    main()
