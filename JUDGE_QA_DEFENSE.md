# 🛡️ SIH 2026 Judge Q&A Technical Defense Guide

This guide provides direct, bulleted technical answers to the top 8 questions Smart India Hackathon (SIH 2026) judges will ask during technical evaluation of the **S.P.O.T. (Smart Produce Optimization & Tracking)** platform.

---

### ❓ Q1: How do you handle overlapping onions in high-density procurement trays?
* **Watershed Segmentation Algorithm**: Combines OpenCV distance transform with marker-based Watershed segmentation to separate touching or overlapping onion bulb contours.
* **Tuned Non-Maximum Suppression (NMS)**: Configures YOLOv8 bounding box NMS IoU threshold to `0.45`, eliminating duplicate box proposals while preserving distinct overlapping bulbs.
* **Elliptical Hough Transform**: Detects curved bulb perimeters to isolate individual center centroids when onions lie on top of one another.

---

### ❓ Q2: What if lighting conditions change drastically in open-air agricultural mandis?
* **CLAHE (Contrast Limited Adaptive Histogram Equalization)**: Pre-processes raw camera frames with CLAHE in local tiles to normalize harsh sunlight, shadow casting, and direct glare.
* **HSV & LAB Color Space Normalization**: Converts RGB frames to LAB color space to separate luminance (L channel) from chromaticity (A/B channels), making rot and mold detection immune to light intensity swings.
* **Auto-White Balance Canvas Filter**: Adjusts color temperature dynamically before feeding 640x640 tensors into the ONNX WebAssembly model.

---

### ❓ Q3: How is scale calibration and weight accuracy verified?
* **Web Serial API Direct Hardware Sync**: Connects directly to RS-232 and USB electronic weighing bridges, reading raw ASCII data frames (`ST,NT,+0100.00kg`) with hardware parity bit validation.
* **Visual 45mm Target Guide**: Displays a 45mm scale reference overlay ring on the camera viewport to ensure optimal 15–20 cm camera elevation above the tray.
* **Tare & Zero-Point Validation**: Software checks scale tare status before accepting batch mass inputs, preventing empty container weight fraud.

---

### ❓ Q4: How do you prevent tampering with inspection reports or QR codes?
* **SHA-256 Cryptographic Hash Signatures**: Each inspection payload generates a SHA-256 hash digest combining batch ID, timestamp, grade, score, and weight telemetry.
* **SQLite Anti-Tamper Audit Trail**: Records session logs directly into an SQLite database (`krishi_database.db`) with read-only verification API endpoints (`/verify?batch_id=...`).
* **QR Verification Seal**: Scanning the on-screen QR code fetches the unalterable server record to verify that physical receipt printouts match database records.

---

### ❓ Q5: How does in-browser ONNX inference achieve <1.5s latency on budget mobile devices?
* **WebAssembly (WASM) SIMD 128-bit Vectors**: Uses `onnxruntime-web` with 128-bit SIMD vector instructions for parallelized matrix multiplications.
* **Web Worker Thread Offloading**: Runs inference inside a dedicated background Web Worker thread, keeping the main React UI rendering loop at a butter-smooth 60 FPS.
* **WebGL / WebGPU Hardware Provider**: Automatically uses mobile GPU shaders when WebGL is available, dropping edge latency down to **145ms–185ms**.

---

### ❓ Q6: How does S.P.O.T. calculate URS (Under Relaxed Specifications) vs Grade A payouts?
* **Calibrated Diameter Measurement**: Computes pixel-to-millimeter ratio using the target framing guide, flagging any bulb below 40mm as `undersized`.
* **Defect Ratio Formula**: Quantifies surface defect percentage (`damaged`, `rotten`, `sprouted`) across detected bounding boxes.
* **Automated Tier Payout Schedule**: Automatically calculates 100 kg lot weight distributions (`Grade-A kg`, `Grade-URS kg`, `Rejected kg`), applying NAFED/APMC price deduction tables dynamically.

---

### ❓ Q7: What happens when farmers dispute an automated grade assignment?
* **One-Touch Dispute Trigger**: Tapping **"Flag Dispute (🚩)"** immediately updates the SQLite database record status to `DISPUTED`.
* **Multilingual Audio Confirmation**: Triggers Web Speech API spoken audio in the farmer's native language (Hindi, Marathi, Tamil, English) confirming official arbitration flag.
* **Raw Image Retention**: Preserves high-resolution raw frame capture and telemetry payload for APMC arbitration officers to review during manual dispute resolution.

---

### ❓ Q8: How is S.P.O.T. deployed to rural mandis without app store downloads or internet?
* **Zero-Install Progressive Web App (PWA)**: Built with ServiceWorker asset caching (`sw.js`). First visit caches the full HTML/CSS/JS shell and ONNX WebAssembly binary model.
* **100% Offline Autonomy**: Operates seamlessly without internet; all model execution, charting, receipt formatting, and audio narration run 100% locally.
* **Web Bluetooth POS Printing**: Connects directly to mobile thermal printers (58mm/80mm) via browser Web Bluetooth API using ESC/POS byte streams.
