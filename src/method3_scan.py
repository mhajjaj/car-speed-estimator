import cv2, numpy as np, json

def measure_at_row(img_path, t, scan_y_fraction=0.75):
    '''Measure bright features across a horizontal scan line.'''
    img = cv2.imread(img_path)
    h, w = img.shape[:2]
    scan_y = int(h * scan_y_fraction)
    
    annotated = img.copy()
    cv2.line(annotated, (0, scan_y), (w, scan_y), (0, 255, 255), 2)
    
    # Get pixel intensities along scan line
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    row = gray[scan_y, :]
    
    # Bright road markings stand out against dark asphalt
    # Use local thresholding - find segments where intensity exceeds local mean
    kernel = np.ones(51) / 51
    local_mean = np.convolve(row.astype(float), kernel, mode='same')
    diff = row.astype(float) - local_mean
    bright = diff > 15  # threshold above local background
    
    # Find continuous bright segments
    transitions = np.diff(bright.astype(int))
    starts = np.where(transitions == 1)[0]
    ends = np.where(transitions == -1)[0]
    
    if bright[0]:
        starts = np.concatenate(([0], starts))
    if bright[-1]:
        ends = np.concatenate((ends, [len(bright) - 1]))
    
    segments = []
    for s, e in zip(starts, ends):
        if e - s > 5:  # at least 5px wide
            segments.append((s, e))
            cx = (s + e) // 2
            cv2.circle(annotated, (cx, scan_y), 5, (0, 0, 255), -1)
            cv2.putText(annotated, f"{s}-{e}", (cx - 30, scan_y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
    
    cv2.imwrite(f"outputs/method3_scan_{t}s.jpg", annotated)
    
    # Pair up segments that are roughly symmetric around center -> lane boundaries
    center_x = w // 2
    
    # Measure distances between segments
    distances = []
    for i in range(len(segments) - 1):
        gap = segments[i+1][0] - segments[i][1]
        if gap > 100:  # likely lane width
            distances.append((segments[i][0], segments[i+1][0], gap))
    
    return {
        "time": t,
        "segments": segments,
        "lane_width_candidates": distances
    }

for t in [4, 8, 12]:
    r = measure_at_row(f"outputs/frame_{t}s.jpg", t, scan_y_fraction=0.72)
    print(f"t={t}s: {len(r['segments'])} bright segments")
    if r['lane_width_candidates']:
        for s, e, d in r['lane_width_candidates']:
            print(f"  Lane width candidate: {d}px")
            # If lane width = 3.5m (Japan standard)
            scale = 3.5 / d
            print(f"  Implied scale (3.5m lane): {scale:.5f} m/px")
            print(f"  Implied speed: {75.8 * (scale / 0.0795):.1f} km/h")
