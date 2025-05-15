// Configuration snapshots API service
import api from './api';

export const configSnapshotsService = {
  /**
   * Search for configuration snapshots with filters
   * @param {Object} filters - Filter parameters
   * @param {String} filters.query - Text to search for in configs
   * @param {String|Number} filters.deviceId - Filter by device ID
   * @param {String} filters.startDate - Filter by start date (YYYY-MM-DD)
   * @param {String} filters.endDate - Filter by end date (YYYY-MM-DD)
   * @param {Number} page - Page number
   * @param {Number} perPage - Items per page
   * @param {Object} sort - Sort parameters
   * @param {String} sort.key - Field to sort by
   * @param {String} sort.order - Sort order ('asc' or 'desc')
   * @returns {Promise} Promise resolving to the search results
   */
  search(filters = {}, page = 1, perPage = 10, sort = { key: 'retrieved_at', order: 'desc' }) {
    return api.get('/configs/search', {
      params: {
        query: filters.query || '',
        device_id: filters.deviceId || '',
        start_date: filters.startDate || '',
        end_date: filters.endDate || '',
        page,
        per_page: perPage,
        sort_by: sort.key,
        sort_order: sort.order
      }
    });
  },

  /**
   * Get a specific configuration snapshot
   * @param {String} deviceId - Device ID
   * @param {String} snapshotId - Snapshot ID
   * @returns {Promise} Promise resolving to the snapshot data
   */
  getSnapshot(deviceId, snapshotId) {
    return api.get(`/configs/${deviceId}/${snapshotId}`);
  },

  /**
   * Get a diff between two configuration snapshots
   * @param {String} deviceId - Device ID
   * @param {String} snapshotId1 - First snapshot ID
   * @param {String} snapshotId2 - Second snapshot ID
   * @returns {Promise} Promise resolving to the diff data
   */
  getDiff(deviceId, snapshotId1, snapshotId2) {
    return api.get(`/configs/${deviceId}/${snapshotId1}/diff/${snapshotId2}`);
  },

  /**
   * Download a configuration snapshot
   * @param {String} deviceId - Device ID
   * @param {String} snapshotId - Snapshot ID
   * @returns {Promise} Promise resolving to the file data
   */
  downloadSnapshot(deviceId, snapshotId) {
    return api.get(`/configs/${deviceId}/${snapshotId}/download`, {
      responseType: 'blob'
    });
  }
};

export default configSnapshotsService;
