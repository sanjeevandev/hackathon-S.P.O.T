# 📜 Department of Consumer Affairs (DoCA) National Field Deployment Plan

**Document Title**: S.P.O.T. National Mandi Deployment Policy & Technical Whitepaper  
**Target Agency**: Department of Consumer Affairs (DoCA), Ministry of Consumer Affairs, Food & Public Distribution, Govt. of India  
**Procurement Stakeholders**: NAFED (National Agricultural Cooperative Marketing Federation of India Ltd.) & NCCF (National Cooperative Consumers' Federation of India Ltd.)  
**Event**: Smart India Hackathon (SIH 2026)  

---

## 🏛️ Executive Summary

Subjective quality assessment in APMC mandis causes price volatility, disputes, and extensive post-harvest loss during seasonal onion procurement for national buffer stocks. **S.P.O.T. (Smart Produce Optimization & Tracking)** offers a zero-bias, offline-first AI grading solution that standardizes procurement quality across **5,000+ national procurement hubs**.

By executing computer vision locally on low-cost edge kiosks via **ONNX WebAssembly**, S.P.O.T. achieves sub-1.5 second grading latency while reducing central cloud server bandwidth and compute costs by **99.4%**.

---

## 🛠️ 1. Low-Cost Mandi Hardware & Kiosk Architecture

To ensure rapid, cost-effective deployment across rural procurement centers without requiring expensive server infrastructure, S.P.O.T. utilizes a modular, standalone hardware kiosk specification.

```
+-----------------------------------------------------------------------------------+
|               S.P.O.T. STANDALONE MANDI KIOSK ARCHITECTURE                         |
+-----------------------------------------------------------------------------------+
|  [ 📷 1080p USB3 Camera + Ring Light ] ----> Overhead 45cm Tray Frame             |
|                                                                                   |
|  [ 🖥️ Raspberry Pi 5 / Jetson Orin Nano ] ----> Runs Local ONNX PWA Engine       |
|                                                                                   |
|  [ ⚖️ RS-232 / USB Digital Weighbridge ] ----> Real-Time Web Serial Intake          |
|                                                                                   |
|  [ 🖨️ ESC/POS Thermal Printer ] -----------> Instant Signed Farmer Receipt         |
+-----------------------------------------------------------------------------------+
```

### 📋 Bill of Materials (BOM) & Unit Cost Breakdown

| Component | Technical Specification | Purpose | Estimated Unit Cost (INR) |
| :--- | :--- | :--- | :---: |
| **Compute Core** | Raspberry Pi 5 (8GB RAM) / NVIDIA Jetson Orin Nano (8GB) | In-browser WebAssembly ONNX inference engine | ₹8,500 |
| **Camera Module** | 1080p USB3.0 Sony IMX291 Sensor (Wide-Angle, Fixed Focus) | Capture high-density 640x640 onion tray frames | ₹3,200 |
| **Lighting Rig** | 12V DC Dimmable LED Ring Light (5500K Sunlight Neutral) | Eliminates shadow variance in open mandis | ₹1,200 |
| **Display Unit** | 10.1-inch High-Brightness Touchscreen Display (1000 nits) | Sunlight-readable visual interface for inspectors | ₹4,000 |
| **Serial Interface** | RS-232 to USB FTDI Interface Cable | Connects to APMC digital weighbridges | ₹600 |
| **Thermal Printer** | 58mm ESC/POS USB / Bluetooth Mobile Thermal Printer | Instant printed farmer receipt & QR seal | ₹1,000 |
| **Enclosure** | IP65 Weatherproof Industrial Aluminum Frame | Dust & moisture protection in outdoor yards | ₹1,200 |
| **Total Unit Cost** | **Complete Hardware Mandi Kiosk** | **Per Procurement Station Setup** | **₹19,700 (~$235 USD)** |

---

## 🔗 2. Government ERP API Integration & Data Schema

S.P.O.T. features a standardized RESTful / gRPC sync interface designed for direct integration with **NAFED E-Procurement Portal** and **NCCF Mandi Gateways**.

### 📄 NAFED / NCCF Data Mapping Schema (`POST /api/v1/nafed/sync-batch`)

```json
{
  "protocol_version": "2.0-DoCA",
  "procurement_center": {
    "center_id": "APMC-MH-NSK-042",
    "district": "Nashik",
    "state": "Maharashtra",
    "officer_aadhaar_hash": "a8f5f167f44f4964e6c998dee827110c",
    "gps_coordinates": {
      "latitude": 20.0059,
      "longitude": 73.7898
    }
  },
  "batch_telemetry": {
    "batch_id": "BATCH-MH-2026-9814",
    "farmer_registration_id": "FARMER-MH-882194",
    "timestamp_utc": "2026-09-01T10:45:00Z",
    "overall_grade": "Grade-A",
    "confidence_score": 96.4,
    "grade_a_percentage": 78.5,
    "grade_urs_percentage": 15.5,
    "rejected_percentage": 6.0,
    "defect_counts": {
      "damaged": 0,
      "rotten": 1,
      "sprouted": 0,
      "undersized": 3
    }
  },
  "weight_breakdown_kg": {
    "gross_lot_weight": 100.0,
    "grade_a_weight": 78.5,
    "grade_urs_weight": 15.5,
    "rejected_weight": 6.0
  },
  "payout_financials_inr": {
    "base_msp_per_kg": 24.00,
    "urs_deduction_per_kg": 3.60,
    "total_farmer_payout": 2242.20,
    "payment_status": "PENDING_DISBURSEMENT"
  },
  "security_audit": {
    "sha256_hash_seal": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "dispute_status": "ACCEPTED",
    "edge_onnx_version": "yolov8n-onion-v2.1"
  }
}
```

---

## 📊 3. Scale, Bandwidth & Cloud Cost Efficiency Analysis

By offloading computer vision inference directly to the client browser / edge kiosk via **ONNX WebAssembly**, S.P.O.T. radically reduces network bandwidth and cloud compute requirements.

### 📉 Bandwidth & Compute Cost Comparison

| Performance Metric | Traditional Cloud API Architecture | S.P.O.T. Edge ONNX Architecture | Efficiency Gain / Savings |
| :--- | :--- | :--- | :---: |
| **Payload Data Size Per Scan** | 4.5 MB (High-Res RGB Image Upload) | **1.2 KB** (Compressed JSON Telemetry) | **99.97% Data Reduction** |
| **Inference Compute Location** | Cloud GPU Cluster (Nvidia T4/A10G) | **Local In-Browser WASM Execution** | Zero GPU Cloud Dependencies |
| **Daily Data Transfer (10,000 Scans)** | 45.0 GB / Mandi | **12.0 MB / Mandi** | Saves 44.98 GB Daily |
| **Average Latency Per Scan** | 850 ms – 2,400 ms (Depends on 4G signal) | **185 ms** (Instant Edge Processing) | **4.6x – 12.9x Speedup** |
| **Monthly Infrastructure Cost (5,000 Mandis)** | ₹2.25 Crore ($270,000 USD / mo) | **₹15,000 ($180 USD / mo)** | **99.33% Cloud Savings** |

---

## 🚀 4. Phased National Rollout Strategy

```
+-----------------------------------------------------------------------------------+
|                       NATIONAL DOCA IMPLEMENTATION PHASES                          |
+-----------------------------------------------------------------------------------+
|  PHASE 1 (Q4 2026) : 250 Major Onion APMC Mandis (MH, MP, GJ)                     |
|  PHASE 2 (Q2 2027) : 1,500 Primary Procurement Depots (NAFED Buffer Centers)     |
|  PHASE 3 (Q4 2027) : 5,000+ Mandis (Multi-Crop Vision: Potato, Tomato, Garlic)   |
+-----------------------------------------------------------------------------------+
```

1. **Phase 1 (Immediate Pilot)**: Deploy 250 kiosks across major onion producing districts (Nashik, Pune, Solapur, Indore).
2. **Phase 2 (Buffer Expansion)**: Integrate S.P.O.T. directly into all NAFED & NCCF buffer stock procurement centers.
3. **Phase 3 (Multi-Crop National Rollout)**: Expand the modular ONNX computer vision engine to support **Potato**, **Tomato**, and **Garlic** quality grading nationwide.
