import cv2

for t in [4, 8, 12]:
    orig = cv2.imread(f"outputs/frame_{t}s.jpg")
    thresh = cv2.imread(f"outputs/thresh_{t}s.jpg")
    
    # Crop bottom 60% of original
    h = orig.shape[0]
    crop_y = int(h * 0.4)
    orig_crop = orig[crop_y:h, :]
    
    # Resize threshold to match
    target_h = orig_crop.shape[0]
    scale = target_h / thresh.shape[0]
    thresh_resized = cv2.resize(thresh, (int(thresh.shape[1] * scale), target_h))
    
    combined = cv2.hconcat([orig_crop, thresh_resized])
    cv2.imwrite(f"outputs/compare_{t}s.jpg", combined)
    print(f"Saved compare_{t}s.jpg, shape: {combined.shape}")

print("Done")
