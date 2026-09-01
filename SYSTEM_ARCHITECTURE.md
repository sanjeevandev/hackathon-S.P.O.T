# 🏗️ S.P.O.T. System Architecture & End-to-End Data Pipeline

This document details the software architecture, hardware integration layers, dual machine learning execution pipelines, and network-resilient offline fallback routes of the **S.P.O.T. (Smart Produce Optimization & Tracking)** agricultural quality grading platform for SIH 2026.

---

## 📐 Visual System Architecture Diagram

```mermaid
graph TD
    %% Define Styles
    classDef hardware fill:#1E3A2B,stroke:#81C784,stroke-width:2px,color:#FFFFFF;
    classDef pwa fill:#0F281E,stroke:#3A7D44,stroke-width:2px,color:#FFFFFF;
    classDef edge fill:#78350F,stroke:#F59E0B,stroke-width:3px,color:#FFFFFF;
    classDef server fill:#1E293B,stroke:#38BDF8,stroke-width:2px,color:#FFFFFF;
    classDef storage fill:#312E81,stroke:#818CF8,stroke-width:2px,color:#FFFFFF;
    classDef fallback fill:#7F1D1D,stroke:#F87171,stroke-width:2px,color:#FFFFFF;

    subgraph HARDWARE ["🔌 Hardware & Sensor Interface Layer"]
        CAM["📷 HTML5 Device Camera Stream"]:::hardware
        SCALE["⚖️ RS-232 / USB Digital Weighing Scale (Web Serial API)"]:::hardware
        PRINTER["🖨️ ESC/POS Thermal Receipt Printer (Web Bluetooth API)"]:::hardware
    end

    subgraph FRONTEND ["📱 React Progressive Web App (Client Layer)"]
        UI["🌿 Forest Green Accessible UI (High Contrast)"]:::pwa
        I18N["🌐 Multilingual Voice Engine (Web Speech API - EN/HI/MR/TA)"]:::pwa
        SW["⚡ PWA Service Worker (Offline Asset Cache)"]:::pwa
        CANVAS["🎯 HTML5 Bounding Box Overlay Canvas"]:::pwa
        RECHARTS["📊 Recharts Data Viz (Grade Distribution Charts)"]:::pwa
    end

    subgraph DUAL_PIPELINE ["🧠 Dual Machine Learning Inference Pipeline"]
        CHECK{"📡 Network Status Check (navigator.onLine)"}:::pwa
        
        subgraph OFFLINE_EDGE ["⚡ OFFLINE ROUTE (Zero Internet Field Usage)"]
            WORKER["🧵 Web Worker Thread"]:::edge
            ORT["⚙️ ONNX Runtime WebAssembly (WASM SIMD + WebGL)"]:::edge
            ONNX_MODEL["📦 onion_yolov8.onnx Local Asset (<185ms Execution)"]:::edge
        end

        subgraph ONLINE_SERVER ["☁️ ONLINE ROUTE (Server Connected)"]
            FASTAPI["🚀 FastAPI Uvicorn Server (Port 8000)"]:::server
            OPENCV["👁️ OpenCV Image Pre-processing Engine"]:::server
            YOLO["🤖 PyTorch / YOLOv8 Onion Defect Classifier"]:::server
        end
    end

    subgraph STORAGE ["💾 Data Verification & Payout Layer"]
        SQLITE[("🗄️ SQLite Database (krishi_database.db)")]:::storage
        DISPUTE["🚩 Farmer Dispute Flagging Registry"]:::storage
        QR["🛡️ Anti-Tamper QR Code Verification Seal"]:::storage
    end

    %% Data Flow Connections
    CAM --> UI
    SCALE --> UI
    UI --> CHECK

    %% Offline Edge Path
    CHECK -- "Offline / Edge Mode" --> WORKER
    WORKER --> ORT
    ORT --> ONNX_MODEL
    ONNX_MODEL --> CANVAS
    ONNX_MODEL --> RECHARTS

    %% Online Server Path
    CHECK -- "Online Mode (HTTP POST /analyze-onion)" --> FASTAPI
    FASTAPI --> OPENCV
    OPENCV --> YOLO
    YOLO --> CANVAS
    YOLO --> RECHARTS
    FASTAPI --> SQLITE

    %% Network Failover
    FASTAPI -- "Network Failover / Timeout" --> WORKER:::fallback

    %% Outputs & Printers
    CANVAS --> UI
    RECHARTS --> UI
    UI --> I18N
    UI --> PRINTER
    UI --> DISPUTE
    DISPUTE --> SQLITE
    SQLITE --> QR
```

---

## 🔄 Data Pipeline & Execution Flow

### 1. Hardware Sensor Acquisition Layer
- **Live Video Capture**: MediaDevices API captures 1280x720 RGB frames with a 45mm scale target calibration overlay.
- **RS-232 / USB Digital Scale Sync**: Reads real-time ASCII streams (`ST,NT,+0100.00kg`) via Web Serial API, automatically parsing gross batch weight.

### 2. Dual Machine Learning Pipeline (Offline Fallback Guarantee)
- **Offline Edge Route (`onnxruntime-web`)**:
  - Activated when `navigator.onLine === false` or when manual Edge ONNX mode is toggled.
  - Offloads tensor matrix transformations to a dedicated Web Worker thread.
  - Leverages WebAssembly SIMD and WebGL hardware acceleration to run `public/models/onion_yolov8.onnx` in **145ms–185ms** (4.6x faster than cloud network latency).
- **Online FastAPI Cloud Route**:
  - Sends multipart file uploads to `POST http://127.0.0.1:8000/api/v1/analyze-onion`.
  - Performs OpenCV contour mapping, defect classification (`damaged`, `rotten`, `sprouted`, `undersized`), and URS percentage calculation.
  - Automatically fails over to the **Offline Edge Route** if the server call times out.

### 3. Verification & Payout Layer
- **SQLite Session Registry**: Saves batch records with timestamp, confidence scores, defect breakdowns, and lot weights.
- **Anti-Tamper QR Code Seal**: Encodes verification URL (`/verify?batch_id=...`) to allow APMC officials to validate audit trails.
- **Web Bluetooth POS Printing**: Outputs ESC/POS thermal receipts to mobile printers in Mandis.
