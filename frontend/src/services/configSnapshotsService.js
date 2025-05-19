// configSnapshotsService.js
// Service for configuration snapshot API calls
import api from './api';

/**
 * Search configuration snapshots
 * @param {Object} filters - { query }
 * @returns {Promise<Object>} Array of snapshot results
 */
export async function searchSnapshots(filters) {
  // Always send a non-empty q param for /configs/search
  const q = filters.query && filters.query.trim() ? filters.query : '*';
  return api.get('/configs/search', { params: { q } });
}

/**
 * List all config snapshots (paginated)
 * @param {Object} filters - { deviceId, page, perPage }
 * @returns {Promise<Object>} Array of snapshot results
 */
export async function listSnapshots(filters) {
  const start = ((filters.page || 1) - 1) * (filters.perPage || 10);
  const limit = filters.perPage || 10;
  const params = {
    device_id: filters.deviceId || undefined,
    start,
    limit
  };
  return api.get('/configs/list', { params });
}

/**
 * Get a single snapshot by ID
 * @param {string|number} snapshotId
 * @returns {Promise<Object>}
 */
export async function getSnapshot(snapshotId) {
  return api.get(`/configs/${snapshotId}`);
}

/**
 * Download a snapshot (returns blob)
 * @param {string|number} snapshotId
 * @returns {Promise<Blob>}
 */
export async function downloadSnapshot(snapshotId) {
  // The backend does not support a download endpoint. Use getSnapshot and let the UI handle download if needed.
  return getSnapshot(snapshotId);
}

/**
 * Get diff between two snapshots
 * @param {string|number} v1
 * @param {string|number} v2
 * @returns {Promise<Object>}
 */
export async function diffSnapshots(v1, v2) {
  // The backend expects /configs/diff?config_id_a=...&config_id_b=...
  return api.get(`/configs/diff`, { params: { config_id_a: v1, config_id_b: v2 } });
}

// Add more as needed (timeline, etc.)
