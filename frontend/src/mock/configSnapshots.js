// Mock data for configuration snapshots
export const mockDevices = [
  { id: 1, name: 'router-core-01' },
  { id: 2, name: 'switch-access-10' },
  { id: 3, name: 'firewall-edge-02' },
  { id: 4, name: 'router-branch-05' },
  { id: 5, name: 'switch-dist-03' }
];

export const mockSnapshots = [
  {
    id: 'c123456',
    device_id: 1,
    device_name: 'router-core-01',
    retrieved_at: '2025-05-10T14:30:45.000Z',
    snippet: 'interface GigabitEthernet0/0\n ip address 192.168.1.1 255.255.255.0\n no shutdown\n!'
  },
  {
    id: 'c123457',
    device_id: 1,
    device_name: 'router-core-01',
    retrieved_at: '2025-05-08T09:15:22.000Z',
    snippet: 'interface GigabitEthernet0/0\n ip address 192.168.1.1 255.255.255.0\n shutdown\n!'
  },
  {
    id: 'c223458',
    device_id: 2,
    device_name: 'switch-access-10',
    retrieved_at: '2025-05-12T11:42:17.000Z',
    snippet: 'vlan 10\n name USERS\nvlan 20\n name PRINTERS\nvlan 30\n name SERVERS'
  },
  {
    id: 'c334459',
    device_id: 3,
    device_name: 'firewall-edge-02',
    retrieved_at: '2025-05-11T16:08:33.000Z',
    snippet: 'policy-map PRIORITY-TRAFFIC\n class VOICE\n  priority percent 10\n class VIDEO\n  priority percent 20'
  },
  {
    id: 'c445460',
    device_id: 4,
    device_name: 'router-branch-05',
    retrieved_at: '2025-05-09T08:55:19.000Z',
    snippet: 'ip route 0.0.0.0 0.0.0.0 10.1.1.1\nip route 192.168.100.0 255.255.255.0 10.2.2.2'
  },
  {
    id: 'c556461',
    device_id: 5,
    device_name: 'switch-dist-03',
    retrieved_at: '2025-05-13T15:22:41.000Z',
    snippet: 'spanning-tree mode rapid-pvst\nspanning-tree extend system-id\nspanning-tree vlan 1-4094 priority 4096'
  },
  {
    id: 'c556462',
    device_id: 5,
    device_name: 'switch-dist-03',
    retrieved_at: '2025-05-12T10:17:39.000Z',
    snippet: 'spanning-tree mode pvst\nspanning-tree extend system-id\nspanning-tree vlan 1-4094 priority 8192'
  },
  {
    id: 'c223459',
    device_id: 2,
    device_name: 'switch-access-10',
    retrieved_at: '2025-05-11T09:33:27.000Z',
    snippet: 'vlan 10\n name USERS\nvlan 20\n name PRINTERS'
  }
];

// Helper function to generate paginated response
export function getPaginatedSnapshots({ 
  query = '', 
  deviceId = null, 
  startDate = null, 
  endDate = null,
  page = 1, 
  perPage = 10,
  sortBy = 'retrieved_at',
  sortOrder = 'desc'
}) {
  // Filter snapshots based on criteria
  let filteredSnapshots = [...mockSnapshots];
  
  // Filter by device
  if (deviceId) {
    filteredSnapshots = filteredSnapshots.filter(s => s.device_id === deviceId);
  }
  
  // Filter by text query
  if (query) {
    const lowerQuery = query.toLowerCase();
    filteredSnapshots = filteredSnapshots.filter(s => 
      s.device_name.toLowerCase().includes(lowerQuery) || 
      s.snippet.toLowerCase().includes(lowerQuery)
    );
  }
  
  // Filter by date range
  if (startDate) {
    const startDateObj = new Date(startDate);
    filteredSnapshots = filteredSnapshots.filter(s => new Date(s.retrieved_at) >= startDateObj);
  }
  
  if (endDate) {
    const endDateObj = new Date(endDate);
    endDateObj.setHours(23, 59, 59, 999); // End of day
    filteredSnapshots = filteredSnapshots.filter(s => new Date(s.retrieved_at) <= endDateObj);
  }
  
  // Sort snapshots
  filteredSnapshots.sort((a, b) => {
    let valA = a[sortBy];
    let valB = b[sortBy];
    
    // Handle dates
    if (sortBy === 'retrieved_at') {
      valA = new Date(valA);
      valB = new Date(valB);
    }
    
    if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
    if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
    return 0;
  });
  
  // Calculate pagination
  const totalSnapshots = filteredSnapshots.length;
  const totalPages = Math.ceil(totalSnapshots / perPage) || 1;
  const currentPage = Math.max(1, Math.min(page, totalPages));
  const startIndex = (currentPage - 1) * perPage;
  const paginatedSnapshots = filteredSnapshots.slice(startIndex, startIndex + perPage);
  
  return {
    snapshots: paginatedSnapshots,
    pagination: {
      total: totalSnapshots,
      per_page: perPage,
      current_page: currentPage,
      total_pages: totalPages
    }
  };
}
