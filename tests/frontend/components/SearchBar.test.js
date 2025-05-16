/**
 * @jest-environment jsdom
 */
import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import SearchBar from '../../frontend/src/components/backups/SearchBar.vue'
import { nextTick } from 'vue'

// Mock the heroicons components
vi.mock('@heroicons/vue/24/solid', () => ({
  MagnifyingGlassIcon: vi.fn(() => ({
    render: () => {},
    __file: 'node_modules/@heroicons/vue/24/solid/MagnifyingGlassIcon.js'
  })),
  ChevronDownIcon: vi.fn(() => ({
    render: () => {},
    __file: 'node_modules/@heroicons/vue/24/solid/ChevronDownIcon.js'
  })),
  CheckIcon: vi.fn(() => ({
    render: () => {},
    __file: 'node_modules/@heroicons/vue/24/solid/CheckIcon.js'
  })),
  CalendarIcon: vi.fn(() => ({
    render: () => {},
    __file: 'node_modules/@heroicons/vue/24/solid/CalendarIcon.js'
  }))
}))

// Mock the headlessui components
vi.mock('@headlessui/vue', () => ({
  Listbox: {
    name: 'Listbox',
    template: '<div><slot /></div>',
  },
  ListboxButton: {
    name: 'ListboxButton',
    template: '<button><slot /></button>',
  },
  ListboxOptions: {
    name: 'ListboxOptions',
    template: '<div><slot /></div>',
  },
  ListboxOption: {
    name: 'ListboxOption',
    template: '<div><slot :active="false" :selected="false" /></div>',
  },
  Popover: {
    name: 'Popover',
    template: '<div><slot /></div>',
  },
  PopoverButton: {
    name: 'PopoverButton',
    template: '<button><slot /></button>',
  },
  PopoverPanel: {
    name: 'PopoverPanel',
    template: '<div><slot /></div>',
  }
}))

describe('SearchBar', () => {
  const mockDevices = [
    { id: 1, name: 'Device 1' },
    { id: 2, name: 'Device 2' }
  ]
  
  let wrapper
  
  beforeEach(() => {
    wrapper = mount(SearchBar, {
      props: {
        initialSearchQuery: '',
        initialDeviceId: null,
        initialStartDate: null,
        initialEndDate: null,
        devices: mockDevices
      }
    })
  })
  
  it('renders correctly', () => {
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('input[type="text"]').exists()).toBe(true)
  })
  
  it('emits search event when search button is clicked', async () => {
    // Set search query
    await wrapper.find('input[type="text"]').setValue('test query')
    
    // Click search button
    await wrapper.find('button').trigger('click')
    
    // Check if search event was emitted
    expect(wrapper.emitted('search')).toBeTruthy()
    expect(wrapper.emitted('search')[0][0]).toEqual({
      query: 'test query',
      deviceId: null,
      startDate: null,
      endDate: null
    })
  })
  
  it('updates the date range when applied', async () => {
    // We need to find the start date and end date inputs
    const startDateInput = wrapper.find('input[type="date"]:first-of-type')
    const endDateInput = wrapper.find('input[type="date"]:last-of-type')
    
    // Set values
    await startDateInput.setValue('2025-01-01')
    await endDateInput.setValue('2025-01-31')
    
    // Find and click the Apply button within the date range popover panel
    const applyButton = wrapper.find('button:nth-of-type(2)') // The second button should be Apply
    await applyButton.trigger('click')
    
    // Search to emit the event with the new date range
    await wrapper.find('button:last-of-type').trigger('click') // Last button should be Search
    
    // Check if search event was emitted with the date range
    expect(wrapper.emitted('search')).toBeTruthy()
    expect(wrapper.emitted('search')[0][0]).toEqual({
      query: '',
      deviceId: null,
      startDate: '2025-01-01',
      endDate: '2025-01-31'
    })
  })
  
  it('clears the date range when clear button is clicked', async () => {
    // Set start and end dates first
    const startDateInput = wrapper.find('input[type="date"]:first-of-type')
    const endDateInput = wrapper.find('input[type="date"]:last-of-type')
    await startDateInput.setValue('2025-01-01')
    await endDateInput.setValue('2025-01-31')
    
    // Find and click Apply to set the values
    const applyButton = wrapper.find('button:nth-of-type(2)')
    await applyButton.trigger('click')
    
    // Now find and click Clear button
    const clearButton = wrapper.find('button:nth-of-type(1)') // First button should be Clear
    await clearButton.trigger('click')
    
    // Search to emit the event
    await wrapper.find('button:last-of-type').trigger('click')
    
    // Check that dates were cleared
    expect(wrapper.emitted('search')).toBeTruthy()
    expect(wrapper.emitted('search')[0][0]).toEqual({
      query: '',
      deviceId: null,
      startDate: null,
      endDate: null
    })
  })
})
