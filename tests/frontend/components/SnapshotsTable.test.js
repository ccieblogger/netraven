/**
 * @jest-environment jsdom
 */
import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import SnapshotsTable from '../../frontend/src/components/backups/SnapshotsTable.vue'

// Mock the heroicons components
vi.mock('@heroicons/vue/24/solid', () => ({
  ChevronUpIcon: vi.fn(() => ({
    render: () => {},
    __file: 'node_modules/@heroicons/vue/24/solid/ChevronUpIcon.js'
  })),
  ChevronDownIcon: vi.fn(() => ({
    render: () => {},
    __file: 'node_modules/@heroicons/vue/24/solid/ChevronDownIcon.js'
  })),
  ChevronLeftIcon: vi.fn(() => ({
    render: () => {},
    __file: 'node_modules/@heroicons/vue/24/solid/ChevronLeftIcon.js'
  })),
  ChevronRightIcon: vi.fn(() => ({
    render: () => {},
    __file: 'node_modules/@heroicons/vue/24/solid/ChevronRightIcon.js'
  })),
  ArrowPathIcon: vi.fn(() => ({
    render: () => {},
    __file: 'node_modules/@heroicons/vue/24/solid/ArrowPathIcon.js'
  })),
  ArrowsUpDownIcon: vi.fn(() => ({
    render: () => {},
    __file: 'node_modules/@heroicons/vue/24/solid/ArrowsUpDownIcon.js'
  })),
  EyeIcon: vi.fn(() => ({
    render: () => {},
    __file: 'node_modules/@heroicons/vue/24/solid/EyeIcon.js'
  })),
  ArrowsRightLeftIcon: vi.fn(() => ({
    render: () => {},
    __file: 'node_modules/@heroicons/vue/24/solid/ArrowsRightLeftIcon.js'
  })),
  ArrowDownTrayIcon: vi.fn(() => ({
    render: () => {},
    __file: 'node_modules/@heroicons/vue/24/solid/ArrowDownTrayIcon.js'
  }))
}))

// Mock the headlessui components
vi.mock('@headlessui/vue', () => ({
  Menu: {
    name: 'Menu',
    template: '<div><slot /></div>',
  },
  MenuButton: {
    name: 'MenuButton',
    template: '<button><slot /></button>',
  },
  MenuItem: {
    name: 'MenuItem',
    template: '<div><slot :active="false" /></div>',
  },
  MenuItems: {
    name: 'MenuItems',
    template: '<div><slot /></div>',
  }
}))

describe('SnapshotsTable', () => {
  const mockSnapshots = [
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
    }
  ]
  
  let wrapper
  
  beforeEach(() => {
    wrapper = mount(SnapshotsTable, {
      props: {
        snapshots: mockSnapshots,
        loading: false,
        page: 1,
        perPage: 10,
        totalSnapshots: 2
      }
    })
  })
  
  it('renders correctly with snapshots', () => {
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('table').exists()).toBe(true)
    expect(wrapper.findAll('tbody tr').length).toBe(2) // Should have two rows
  })
  
  it('displays loading state', async () => {
    await wrapper.setProps({ loading: true })
    expect(wrapper.find('.animate-pulse').exists()).toBe(true)
  })
  
  it('shows empty state message when no snapshots', async () => {
    await wrapper.setProps({ snapshots: [] })
    expect(wrapper.text()).toContain('No configuration snapshots found')
  })
  
  it('emits sort event when column header is clicked', async () => {
    // Find the "Device" column header (should be sortable)
    const sortableColumnHeader = wrapper.findAll('th')[0]
    await sortableColumnHeader.trigger('click')
    
    // Check if sort event was emitted
    expect(wrapper.emitted('sort')).toBeTruthy()
    expect(wrapper.emitted('sort')[0][0]).toEqual({ key: 'device_name', order: 'asc' })
  })
  
  it('emits view event when view action is clicked', async () => {
    // Find menu button and click to open actions menu
    const menuButton = wrapper.find('button:first-of-type')
    await menuButton.trigger('click')
    
    // Since we're using mocked components, we need to directly trigger an event
    // Find the view button by text content
    const buttons = wrapper.findAll('button')
    
    // The first action button after the menu button should be View
    // This is somewhat brittle due to the mocking approach
    const viewButton = buttons.find(b => b.text().includes('View'))
    await viewButton.trigger('click')
    
    // Check if view event was emitted with the snapshot
    expect(wrapper.emitted('view')).toBeTruthy()
    expect(wrapper.emitted('view')[0][0]).toEqual(mockSnapshots[0])
  })
  
  it('emits page-change event when pagination buttons are clicked', async () => {
    // First, set totalSnapshots to a number that would create multiple pages
    await wrapper.setProps({ totalSnapshots: 20 })
    
    // Find the "Next" pagination button
    const nextPageButton = wrapper.findAll('button').at(-1)
    await nextPageButton.trigger('click')
    
    // Check if page-change event was emitted
    expect(wrapper.emitted('page-change')).toBeTruthy()
    expect(wrapper.emitted('page-change')[0][0]).toBe(2) // Should navigate to page 2
  })
})
