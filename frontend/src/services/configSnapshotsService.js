// configSnapshotsService.js
// Service for configuration snapshot API calls
import api from './api';

/**
 * Search configuration snapshots
 * @param {Object} filters - { query, deviceId, startDate, endDate, page, perPage, sort }
 * @returns {Promise<Object>} Paginated snapshot results
 */
export async function searchSnapshots(filters) {
  const params = {
    query: filters.query || '',
    device_id: filters.deviceId || undefined,
    start_date: filters.startDate || undefined,
    end_date: filters.endDate || undefined,
    page: filters.page || 1,
    per_page: filters.perPage || 10,
    sort: filters.sort || undefined
  };
  return api.get('/configs/search', { params });
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
  return api.get(`/configs/${snapshotId}/download`, { responseType: 'blob' });
}

/**
 * Get diff between two snapshots
 * @param {string} deviceId
 * @param {string} v1
 * @param {string} v2
 * @returns {Promise<Object>}
 */
export async function diffSnapshots(deviceId, v1, v2) {
  return api.get(`/configs/${deviceId}/diff/${v1}/${v2}`);
}

// Add more as needed (timeline, etc.)
