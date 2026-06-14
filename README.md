# Obstacle-Avoidance

This repository houses the standalone perception system developed for the Team rover competition. The pipeline is engineered to execute real-time object localized color tracking and noise-filtering using a single-camera architecture. It is specifically optimized to maintain structural target tracking under harsh, dynamic outdoor environmental conditions like direct sunlight and deep shadows.

---

## 1. Architectural Strategy: Separation of Concerns

In autonomous robotics, mixing sensory data collection with low-level motor actuation creates fragile, hard-to-debug code. This project enforces a strict **Separation of Concerns**:

* **The Perception System (This Code):** Acts purely as the vehicle's eyes. It handles pixel matrix math, transforms color spaces, removes light distortion, and compresses a massive 3-channel image array into a single, high-fidelity coordinate metric called **The Error ($e$)**.
* **The Control System (PID Loop):** Acts as the vehicle's muscles. It is entirely blind to raw pixels. It ingests the single error metric produced by the vision pipeline and feeds it into a Proportional-Integral-Derivative (PID) algorithm to dynamically govern differential motor velocities.

---

## 2. Core Computer Vision Techniques

Direct outdoor sunlight is highly destructive to basic color thresholding. It introduces high-frequency background sensor noise, deep shadow contrasts, and bright white specular reflections (glare) that wash out colors. This pipeline employs three advanced computer vision techniques to mitigate these variables:

### A. Color Segmentation via Saturated HSV Space
Standard digital video streams operate in the BGR (Blue, Green, Red) color space, which fundamentally couples color pigment information with light intensity. A passing cloud or a harsh shadow completely alters the BGR pixel values of a red obstacle.

To solve this, the pipeline converts frames into the **HSV (Hue, Saturation, Value)** color space.
* **Hue ($H$):** Represents the pure color pigment wavelength, isolating "redness" entirely from how bright or dark it is.
* **Saturation ($S$):** Measures the purity or intensity of the color. 

By pushing our minimum Saturation threshold up to `150` ($np.array([0, 150, 50])$), the pipeline explicitly orders the camera to ignore white surfaces. Because blinding sun glare has zero saturation (pure white), it is stripped away, allowing the camera to lock exclusively onto the highly saturated red pigment of the structural obstacle.

### B. Dual-Threshold Spectrum Wrapping
In the cylindrical HSV color space, the color red is mathematically unique: it sits at the absolute beginning of the hue spectrum ($0^\circ$ to $10^\circ$) and loops continuously around to finish at the absolute end of the spectrum ($165^\circ$ to $180^\circ$).

To ensure the rover never drops tracking when lighting changes cause the shade of red to shift, the pipeline instantiates two separate color threshold masks:
1. `mask1`: Captures the lower bound red hues.
2. `mask2`: Captures the upper bound red hues.

These matrices are merged into a single binary channel using a bitwise `OR` logical operation (`cv2.bitwise_or()`). If a pixel satisfies either shade of red, it is captured.

### C. Mathematical Morphology (Noise Elimination & Shape Healing)
Even with HSV filtering, outdoor track environments introduce artifacts—dust reflecting sunlight behaves like flickering white pixels, and intense glare cuts holes straight through the middle of the detected obstacle mask. The pipeline heals these frame anomalies using structural pixel kernels:

* **Morphological Opening (`MORPH_OPEN`):** Executes an erosion operation followed by a dilation. This acts as a digital broom, completely erasing tiny, disconnected high-frequency noise clusters (like sun glare bouncing off floor pebbles) from the binary mask.
* **Morphological Closing (`MORPH_CLOSE`):** Executes a dilation operation followed by an erosion. This acts as a structural bridge. If sun glare creates an empty "hole" inside the physical boundary of the red obstacle, closing automatically patches the gap, sealing the mask back into one solid, unfragmented shape.

### D. Contour Boundary Mapping & Centroid Isolation
Once a clean binary mask is achieved, the shape must be converted into a geometric coordinate.
* The pipeline implements `cv2.findContours` using the `RETR_EXTERNAL` retrieval mode to trace only the absolute outermost physical borders of the detected white shapes, saving valuable processing clock cycles.
* An **Area Threshold Gate** (`cv2.contourArea(contour) > 1200`) evaluates the pixel surface area of the shape. Any shape smaller than 1200 total pixels is discarded as a false positive, ensuring the rover never twitches due to minor background objects.
* For verified obstacles, a bounding box calculates the horizontal center of mass—the **Centroid**.

---

## 3. The Vision-to-PID Data Protocol

The ultimate output and payload of this entire script is a live integer metric defining horizontal spatial deviation relative to the camera's fixed optical axis:

$$\text{Error} = \text{Obstacle Center} - \text{Camera Center}$$

The camera width is bisected to find the true midpoint axis. The pipeline constantly evaluates the location of the obstacle's green centroid dot against this baseline:

| Obstacle Location | Output Metric | Resulting Control Action |
| :--- | :--- | :--- |
| **Right Side** | **Positive Error** ($+e$) | PID spins right wheels faster $\rightarrow$ Rover swerves **Left** |
| **Left Side** | **Negative Error** ($-e$) | PID spins left wheels faster $\rightarrow$ Rover swerves **Right** |
| **Clear Track** | **Zero Error** ($0$) | PID maintains equal wheel velocity $\rightarrow$ Rover drives **Straight** |

This real-time error output stream is continuously printed to the terminal feed. The control team's PID script will intercept this variable, treating it as the primary instantaneous error value ($e$) to drive their differential motor loop.

---

## 4. Graphical User Interface (Debugging Windows)

When executed, the pipeline instantiates a split visual interface for developer monitoring:
1. **Primary Feed ("Sun-Proof PID Vision"):** Displays the raw color environment overlaying a vertical **Blue Midpoint Line** (the rover's heading axis), a tracking **Red Bounding Box** (the locked target), and a central **Green Dot** (the calculated obstacle centroid).
2. **Mask Feed ("Healed Mask"):** Displays the underlying binary processing matrix. This allows developers to visually verify that morphological adjustments are cleanly separating the obstacle from outdoor sun noise in real-time.

### Real-Time Detection Demonstration
Below is an in-action example of the primary vision feed locking onto a target slightly to the right of the central axis, yielding a positive steering error calculation:

![Live Obstacle Tracking Demo](<img width="637" height="480" alt="image" src="https://github.com/user-attachments/assets/b4750e93-22e4-4cbe-ae9c-744faf043c8b" />
)
