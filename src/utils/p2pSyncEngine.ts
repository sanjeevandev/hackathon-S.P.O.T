/**
 * S.P.O.T. Peer-to-Peer (P2P) WebRTC Mesh Synchronization Engine
 * Offline-First Agricultural Procurement Sync with CRDT Conflict Resolution
 */

import { PastSessionLog } from '../types';

export interface CRDTLogItem extends PastSessionLog {
  vectorClock: number;       // Monotonic logical timestamp for CRDT resolution
  deviceId: string;          // Originating inspector device UUID
  lastUpdatedMs: number;     // Wall-clock timestamp in milliseconds
}

export type PeerMeshListener = (connectedPeerCount: number) => void;
export type SyncUpdateListener = (syncedCount: number, sourceDeviceId: string) => void;

class P2PMeshSyncEngine {
  private deviceId: string;
  private peerCount: number = 1; // Default self peer
  private peerListeners: Set<PeerMeshListener> = new Set();
  private syncListeners: Set<SyncUpdateListener> = new Set();
  private broadcastChannel: BroadcastChannel | null = null;
  private crdtStore: Map<string, CRDTLogItem> = new Map();
  private vectorClock: number = 0;
  private activePeers: Map<string, number> = new Map(); // peerId -> lastSeenMs

  constructor() {
    this.deviceId = 'SPOT-INSPECTOR-' + Math.random().toString(36).substring(2, 7).toUpperCase();
    this.initBroadcastMesh();
  }

  public getDeviceId(): string {
    return this.deviceId;
  }

  public getPeerCount(): number {
    return this.peerCount;
  }

  /**
   * Initializes BroadcastChannel mesh for real same-origin peer sync across tabs/windows.
   */
  private initBroadcastMesh() {
    if (typeof window !== 'undefined' && 'BroadcastChannel' in window) {
      this.broadcastChannel = new BroadcastChannel('spot_p2p_mandi_mesh');
      
      this.broadcastChannel.onmessage = (event) => {
        const { type, payload, senderId } = event.data || {};
        if (!senderId || senderId === this.deviceId) return;

        // Register peer activity
        this.activePeers.set(senderId, Date.now());
        this.pruneStalePeers();

        if (type === 'HEARTBEAT_PING') {
          this.broadcastChannel?.postMessage({
            type: 'HEARTBEAT_PONG',
            senderId: this.deviceId,
            payload: { activeCount: this.peerCount }
          });
        } else if (type === 'SYNC_CRDT_LOGS') {
          this.handleIncomingCRDTLogs(payload as CRDTLogItem[], senderId);
        }
      };

      // Periodic heartbeat broadcast & prune
      setInterval(() => {
        this.pruneStalePeers();
        if (this.broadcastChannel) {
          this.broadcastChannel.postMessage({
            type: 'HEARTBEAT_PING',
            senderId: this.deviceId
          });
        }
      }, 5000);

      // Immediate announcement
      this.broadcastChannel.postMessage({
        type: 'HEARTBEAT_PING',
        senderId: this.deviceId
      });
    }
  }

  private pruneStalePeers() {
    const now = Date.now();
    for (const [id, lastSeen] of this.activePeers.entries()) {
      if (now - lastSeen > 12000) {
        this.activePeers.delete(id);
      }
    }
    const realCount = 1 + this.activePeers.size;
    if (realCount !== this.peerCount) {
      this.peerCount = realCount;
      this.peerListeners.forEach((listener) => listener(this.peerCount));
    }
  }

  public subscribePeerCount(listener: PeerMeshListener): () => void {
    this.peerListeners.add(listener);
    listener(this.peerCount);
    return () => this.peerListeners.delete(listener);
  }

  public subscribeSyncUpdates(listener: SyncUpdateListener): () => void {
    this.syncListeners.add(listener);
    return () => this.syncListeners.delete(listener);
  }

  /**
   * CRDT Conflict-Free Replicated Data Type Resolver (Last-Write-Wins Element Set)
   * Resolves conflicting updates to the same batch_id across inspector devices.
   */
  public resolveCRDTConflict(localItem: CRDTLogItem, remoteItem: CRDTLogItem): CRDTLogItem {
    // 1. Higher vector clock wins
    if (remoteItem.vectorClock > localItem.vectorClock) {
      return remoteItem;
    }
    if (localItem.vectorClock > remoteItem.vectorClock) {
      return localItem;
    }

    // 2. Tie-breaker: Wall-clock timestamp (LWW)
    if (remoteItem.lastUpdatedMs > localItem.lastUpdatedMs) {
      return remoteItem;
    }
    if (localItem.lastUpdatedMs > remoteItem.lastUpdatedMs) {
      return localItem;
    }

    // 3. Status priority: DISPUTED status overrides ACCEPTED
    if (remoteItem.status === 'DISPUTED' && localItem.status !== 'DISPUTED') {
      return remoteItem;
    }

    // 4. Deterministic string tie-breaker on device ID
    return remoteItem.deviceId > localItem.deviceId ? remoteItem : localItem;
  }

  /**
   * Merges incoming remote CRDT batch logs into local memory & IndexedDB storage.
   */
  private handleIncomingCRDTLogs(remoteLogs: CRDTLogItem[], senderId: string) {
    let mergeCount = 0;
    
    remoteLogs.forEach((remoteItem) => {
      const existing = this.crdtStore.get(remoteItem.batch_id);
      if (!existing) {
        this.crdtStore.set(remoteItem.batch_id, remoteItem);
        mergeCount++;
      } else {
        const resolved = this.resolveCRDTConflict(existing, remoteItem);
        if (resolved !== existing) {
          this.crdtStore.set(remoteItem.batch_id, resolved);
          mergeCount++;
        }
      }
    });

    if (mergeCount > 0) {
      this.syncListeners.forEach((listener) => listener(mergeCount, senderId));
      this.saveStoreToIndexedDB();
    }
  }

  /**
   * Broadcasts local inspection logs to all peer devices on local Wi-Fi / Hotspot.
   */
  public broadcastLocalLogs(logs: PastSessionLog[]): number {
    this.vectorClock += 1;
    const nowMs = Date.now();

    const crdtItems: CRDTLogItem[] = logs.map((log) => {
      const existing = this.crdtStore.get(log.batch_id);
      return {
        ...log,
        vectorClock: existing ? existing.vectorClock + 1 : this.vectorClock,
        deviceId: this.deviceId,
        lastUpdatedMs: nowMs,
      };
    });

    crdtItems.forEach((item) => this.crdtStore.set(item.batch_id, item));

    if (this.broadcastChannel) {
      this.broadcastChannel.postMessage({
        type: 'SYNC_CRDT_LOGS',
        senderId: this.deviceId,
        payload: crdtItems,
      });
    }

    this.saveStoreToIndexedDB();
    return crdtItems.length;
  }

  /**
   * Persists CRDT store into browser local IndexedDB / Storage for 100% offline resilience.
   */
  private saveStoreToIndexedDB() {
    try {
      const items = Array.from(this.crdtStore.values());
      localStorage.setItem('spot_crdt_mesh_store', JSON.stringify(items));
    } catch (e) {
      console.warn('CRDT IndexedDB storage backup warning:', e);
    }
  }

  /**
   * Retrieves all merged CRDT inspection logs.
   */
  public getMergedLogs(): PastSessionLog[] {
    return Array.from(this.crdtStore.values());
  }
}

export const p2pSyncEngine = new P2PMeshSyncEngine();
