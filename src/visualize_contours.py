import cv2, numpy as np

for t in [4, 8, 12]:
    img = cv2.imread(f"outputs/frame_{t}s.jpg")
    h, w = img.shape[:2]
    crop_y = int(h * 0.4)
    roi = img[crop_y:h, :]
    
    lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)
    l = lab[:, :, 0]
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    l_enhanced = clahe.apply(l)
    blur = cv2.GaussianBlur(l_enhanced, (7, 7), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY, 51, -10)
    
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Draw all contours on the ROI
    contour_img = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 100 or area > 20000:
            continue
        rect = cv2.minAreaRect(cnt)
        width, height = rect[1]
        if width < 1 or height < 1:
            continue
        aspect = max(width, height) / min(width, height)
        if aspect > 0.2 and aspect < 5.0:
            cv2.drawContours(contour_img, [cnt], -1, (0, 255, 0), 2)
    
    # Also save the threshold image
    cv2.imwrite(f"outputs/thresh_{t}s.jpg", thresh)
    cv2.imwrite(f"output/contours_{t}s.jpg", contour_img)
    print(f"Saved thresh and contour images for {t}s")

print("Done")
