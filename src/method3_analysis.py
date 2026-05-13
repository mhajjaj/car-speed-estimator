import cv2, numpy as np, json, os

def measure_road_features(img_path, t):
    img = cv2.imread(img_path)
    h, w = img.shape[:2]
    annotated = img.copy()
    
    # Focus on bottom 30% where features are largest
    crop_y = int(h * 0.7)
    roi = img[crop_y:h, :]
    roi_h = roi.shape[0]
    
    # Edge detect in ROI
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    
    # Find lines
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=80,
                            minLineLength=60, maxLineGap=15)
    
    vertical_lines = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            if dx < 5 and dy > 30:  # nearly vertical
                x_avg = int((x1 + x2) / 2)
                y_top = min(y1, y2) + crop_y
                y_bot = max(y1, y2) + crop_y
                vertical_lines.append((x_avg, y_top, y_bot))
                cv2.line(annotated, (x_avg, y_top), (x_avg, y_bot), (0, 255, 0), 2)
    
    # Sort by x position
    vertical_lines.sort(key=lambda v: v[0])
    
    # Measure distances between consecutive vertical features
    gaps = []
    for i in range(len(vertical_lines) - 1):
        gap = vertical_lines[i+1][0] - vertical_lines[i][0]
        if 50 < gap < 500:  # reasonable feature spacing
            gaps.append(gap)
            mid_x = int((vertical_lines[i][0] + vertical_lines[i+1][0]) / 2)
            mid_y = int((vertical_lines[i][1] + vertical_lines[i][2]) / 2)
            cv2.putText(annotated, f"{gap}px", (mid_x - 20, mid_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    
    cv2.imwrite(f"outputs/method3_frame_{t}s.jpg", annotated)
    
    return {
        "time": t,
        "num_vertical_lines": len(vertical_lines),
        "gaps": gaps,
        "mean_gap": float(np.mean(gaps)) if gaps else None,
        "std_gap": float(np.std(gaps)) if gaps else None
    }

results = []
for t in [4, 8, 12]:
    r = measure_road_features(f"outputs/frame_{t}s.jpg", t)
    results.append(r)
    print(f"t={t}s: {r['num_vertical_lines']} lines, gaps={r['gaps']}, mean={r['mean_gap']}")

with open("outputs/method3_results.json", "w") as f:
    json.dump(results, f, indent=2)
