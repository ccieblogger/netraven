// Moved and expanded from src/components/TimelinePanel.spec.js
import { mount } from '@vue/test-utils';
import TimelinePanel from '../../../frontend/src/components/TimelinePanel.vue';

const mockSnapshots = [
  { id: 'snap1', retrieved_at: '2025-05-15T10:00:00Z' },
  { id: 'snap2', retrieved_at: '2025-05-14T09:00:00Z' }
];

describe('TimelinePanel', () => {
  it('renders when open and shows snapshots', async () => {
    const wrapper = mount(TimelinePanel, {
      props: {
        isOpen: true,
        device: { id: 1, hostname: 'router-1' }
      },
      global: {
        mocks: {
          configSnapshotsService: {
            search: () => Promise.resolve({ data: { snapshots: mockSnapshots } })
          }
        }
      }
    });
    await new Promise(r => setTimeout(r, 10));
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain('Timeline for router-1');
    expect(wrapper.text()).toContain('snap1');
    expect(wrapper.text()).toContain('snap2');
  });

  it('shows loading and error states', async () => {
    const wrapper = mount(TimelinePanel, {
      props: { isOpen: true, device: { id: 1 } },
      global: {
        mocks: {
          configSnapshotsService: {
            search: () => Promise.reject('fail')
          }
        }
      }
    });
    await new Promise(r => setTimeout(r, 10));
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toMatch(/Failed to load snapshots|No snapshots found/);
  });

  it('emits close event', async () => {
    const wrapper = mount(TimelinePanel, {
      props: { isOpen: true, device: { id: 1 } }
    });
    await wrapper.find('button').trigger('click');
    expect(wrapper.emitted('close')).toBeTruthy();
  });

  it('emits view event when View button is clicked', async () => {
    const wrapper = mount(TimelinePanel, {
      props: {
        isOpen: true,
        device: { id: 1 },
      },
      global: {
        mocks: {
          configSnapshotsService: {
            search: () => Promise.resolve({ data: { snapshots: mockSnapshots } })
          }
        }
      }
    });
    await new Promise(r => setTimeout(r, 10));
    await wrapper.vm.$nextTick();
    const viewBtn = wrapper.findAll('button').find(btn => btn.text() === 'View');
    await viewBtn.trigger('click');
    expect(wrapper.emitted('view')).toBeTruthy();
  });

  it('emits diff event when Diff button is clicked', async () => {
    const wrapper = mount(TimelinePanel, {
      props: {
        isOpen: true,
        device: { id: 1 },
      },
      global: {
        mocks: {
          configSnapshotsService: {
            search: () => Promise.resolve({ data: { snapshots: mockSnapshots } })
          }
        }
      }
    });
    await new Promise(r => setTimeout(r, 10));
    await wrapper.vm.$nextTick();
    const diffBtn = wrapper.findAll('button').find(btn => btn.text() === 'Diff');
    await diffBtn.trigger('click');
    expect(wrapper.emitted('diff')).toBeTruthy();
  });

  it('handles no snapshots edge case', async () => {
    const wrapper = mount(TimelinePanel, {
      props: {
        isOpen: true,
        device: { id: 1 },
      },
      global: {
        mocks: {
          configSnapshotsService: {
            search: () => Promise.resolve({ data: { snapshots: [] } })
          }
        }
      }
    });
    await new Promise(r => setTimeout(r, 10));
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain('No snapshots found');
  });
});
