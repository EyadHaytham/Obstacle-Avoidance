import cv2
import numpy as np

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break
        
    height, width, _ = frame.shape
    camera_center = width // 2
    
    cv2.line(frame, (camera_center, 0), (camera_center, height), (255, 0, 0), 2)
    
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    lower_red1, upper_red1 = np.array([0, 150, 50]), np.array([10, 255, 255])
    lower_red2, upper_red2 = np.array([165, 150, 50]), np.array([180, 255, 255])
    
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    color_mask = cv2.bitwise_or(mask1, mask2)
    
    kernel_clean = np.ones((3, 3), np.uint8)
    kernel_heal = np.ones((7, 7), np.uint8)
    
    cleaned_mask = cv2.morphologyEx(color_mask, cv2.MORPH_OPEN, kernel_clean)
    final_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_CLOSE, kernel_heal)
    
    contours, _ = cv2.findContours(final_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    obstacle_detected = False
    error = 0
    
    for contour in contours:
        if cv2.contourArea(contour) > 1200:
            obstacle_detected = True
            x, y, w, h = cv2.boundingRect(contour)
            obstacle_center = x + (w // 2)
            
            # THE PID ERROR CALCULATION LOGIC
            #
            # SCENARIO A: Obstacle is on the RIGHT
            # If camera width is 640, Camera Center is 320.
            # If Obstacle Center is at pixel 450:
            # Error = 450 - 320 = +130 (Positive -> Steer Left to Avoid)
            #
            # SCENARIO B: Obstacle is on the LEFT
            # If Obstacle Center is at pixel 200:
            # Error = 200 - 320 = -120 (Negative -> Steer Right to Avoid)
            #
            # SCENARIO C: No Obstacle Detected
            # Error = 0 (Zero -> Drive Straight)
            
            error = obstacle_center - camera_center
            
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
            cv2.circle(frame, (obstacle_center, y + (h // 2)), 5, (0, 255, 0), -1)
            cv2.putText(frame, f"Error: {error}", (x, y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            break
            
    if obstacle_detected:
        print(f"PID_ERROR:{error}")
    else:
        print("PID_ERROR:0")

    cv2.imshow("Sun-Proof PID Vision", frame)
    cv2.imshow("Healed Mask (No Glare)", final_mask)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()