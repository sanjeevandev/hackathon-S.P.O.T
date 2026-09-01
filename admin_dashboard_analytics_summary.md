# 👮 Regional Agricultural Officer Admin Dashboard (`/admin`)

This walkthrough documents the implementation of the secure, lightweight **Regional Officer Admin Portal** (`/admin`) designed for APMC and NAFED agricultural procurement officers.

---

## 🌟 1. Overview & Key Capabilities

- **Secure Passcode Access**: Protected by an APMC Officer PIN gate (default: `2026`) with a 1-click Quick Demo Bypass for presentation judges.
- **100% Offline Autonomy**: Operates seamlessly offline by reading telemetry records directly from synchronized local IndexedDB / SQLite database tables.
- **District Telemetry Aggregation**: Aggregates inspection statistics across **18 APMC procurement centers** spanning 4 major districts (**Nashik**, **Pune**, **Solapur**, **Ahmednagar**).

---

## 📊 2. High-Contrast Dashboard Analytics

```
===================================================================================
             S.P.O.T. REGIONAL OFFICER TELEMETRY DASHBOARD
===================================================================================
[TOTAL INSPECTED VOLUME]  : 1,480.5 Metric Tons (MT)
[OVERALL GRADE RATIO]     : 60.6% Grade A (897.5 MT) | 28.3% URS (419 MT) | 11.1% Rejected
[DISPUTE FREQUENCY RATE]  : 3.8% (58 Disputed Lots / 1,520 Total Inspection Lots)
[ACTIVE APMC MANDIS]      : 18 Mandi Procurement Depots
===================================================================================
```

---

## 📐 3. Interactive Data Visualizations (Recharts)

1. **Inspected Metric Tons (MT) by District BarChart**:
   - **Nashik APMC**: 620.5 MT (415 MT Grade A, 155.5 MT URS, 50 MT Rejected)
   - **Pune APMC**: 410.0 MT (246 MT Grade A, 123 MT URS, 41 MT Rejected)
   - **Solapur APMC**: 280.0 MT (126 MT Grade A, 98 MT URS, 56 MT Rejected)
   - **Ahmednagar APMC**: 170.0 MT (110.5 MT Grade A, 42.5 MT URS, 17 MT Rejected)

2. **Overall Quality Ratio PieChart**:
   - High-contrast visual slices displaying Grade-A Export ready vs URS Buffer Stock vs Rejected lots.

3. **Weekly Dispute Frequency LineChart**:
   - Tracks weekly dispute rates (Solapur peak: 7.8% dispute rate) for APMC tribunal arbitration review.

---

## 💾 4. Offline Synchronization & Data Export

- **Sync Button**: 1-click `Sync Tables` trigger that synchronizes local IndexedDB caches with SQLite backend storage when internet connectivity is restored.
- **CSV Export**: Enables officers to download formatted regional APMC procurement data for government NAFED reporting.
