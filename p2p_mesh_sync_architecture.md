# 🌐 S.P.O.T. Peer-to-Peer (P2P) Offline Mesh Synchronization

This document details the software architecture, WebRTC DataChannel / BroadcastChannel fallback mesh, and Conflict-Free Replicated Data Type (CRDT) algorithms powering **S.P.O.T.**'s multi-inspector offline synchronization module.

---

## 📐 P2P Mesh Architecture Overview

```
+-------------------------------------------------------------------------------+
|                       LOCAL WI-FI / HOTSPOT P2P MESH                          |
|                                                                               |
|   +-------------------+      WebRTC / Broadcast      +-------------------+   |
|   | 📱 INSPECTOR 1    | <==========================> | 📱 INSPECTOR 2    |   |
|   | SPOT-INSPECTOR-A1 |                              | SPOT-INSPECTOR-[#]|   |
|   +-------------------+                              +-------------------+   |
|             ^                                                  ^              |
|             |                CRDT Sync Stream                  |              |
|             v                                                  v              |
|   +-----------------------------------------------------------------------+   |
|   |              IndexedDB / Local Storage CRDT Store (LWW)               |   |
|   +-----------------------------------------------------------------------+   |
+-------------------------------------------------------------------------------+
```

---

## ⚡ 1. Local Wi-Fi & Hotspot Peer Discovery

- **Zero-Cellular Requirement**: Inspectors operating in remote APMC procurement hubs connect over local Wi-Fi or mobile hotspot networks without requiring external internet or cell towers.
- **WebRTC DataChannel & Broadcast Mesh**: Establishes peer data channels to broadcast inspection logs (`PastSessionLog`) and dispute overrides (`DISPUTED`) across nearby inspector devices.
- **Real-Time UI Badge**: Renders a live status badge in the header:  
  `🌐 Peer Mesh Connected (3 Devices)`

---

## 🧮 2. CRDT Conflict-Free Resolution Algorithm

When multiple inspector devices modify or record inspections for the same batch ID, S.P.O.T. uses a **Last-Write-Wins (LWW) Element Set** combined with a monotonic vector clock to resolve conflicts automatically:

```typescript
public resolveCRDTConflict(localItem: CRDTLogItem, remoteItem: CRDTLogItem): CRDTLogItem {
  // 1. Monotonic Vector Clock Check
  if (remoteItem.vectorClock > localItem.vectorClock) return remoteItem;
  if (localItem.vectorClock > remoteItem.vectorClock) return localItem;

  // 2. Wall-Clock Timestamp Check (LWW)
  if (remoteItem.lastUpdatedMs > localItem.lastUpdatedMs) return remoteItem;
  if (localItem.lastUpdatedMs > remoteItem.lastUpdatedMs) return localItem;

  // 3. Status Priority (Disputed status overrides Accepted)
  if (remoteItem.status === 'DISPUTED' && localItem.status !== 'DISPUTED') {
    return remoteItem;
  }

  // 4. Deterministic Device Tie-Breaker
  return remoteItem.deviceId > localItem.deviceId ? remoteItem : localItem;
}
```

---

## 💾 3. Offline Resilience & IndexedDB Backup

- **Instant Persistence**: Every merged CRDT item is saved to browser IndexedDB and `localStorage` (`spot_crdt_mesh_store`).
- **Cloud Reconciliation**: Once cellular/internet access is restored, the consolidated CRDT dataset is pushed to the central FastAPI SQLite database (`backend/krishi_database.db`).
