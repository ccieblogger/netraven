import { mount, flushPromises } from '@vue/test-utils';
import ConfigRawView from '../../src/pages/ConfigRawView.vue';

// Mock fetch
global.fetch = jest.fn();

describe('ConfigRawView', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  it('fetches and displays config', async () => {
    fetch.mockResolvedValueOnce({ ok: true, text: () => Promise.resolve('raw config text') });
    const $route = { params: { device: 'dev1', snapshotId: 'snap1' }, query: {} };
    const wrapper = mount(ConfigRawView, {
      global: {
        mocks: { $route }
      }
    });
    await flushPromises();
    expect(wrapper.text()).toContain('raw config text');
  });

  it('shows error on fetch failure', async () => {
    fetch.mockResolvedValueOnce({ ok: false });
    const $route = { params: { device: 'dev1', snapshotId: 'snap1' }, query: {} };
    const wrapper = mount(ConfigRawView, {
      global: {
        mocks: { $route }
      }
    });
    await flushPromises();
    expect(wrapper.text()).toMatch(/failed to fetch/i);
  });

  it('fetches diff config if diffWith param is present', async () => {
    fetch
      .mockResolvedValueOnce({ ok: true, text: () => Promise.resolve('main config') })
      .mockResolvedValueOnce({ ok: true, text: () => Promise.resolve('diff config') });
    const $route = { params: { device: 'dev1', snapshotId: 'snap1' }, query: { diffWith: 'snap2' } };
    const wrapper = mount(ConfigRawView, {
      global: {
        mocks: { $route }
      }
    });
    await flushPromises();
    expect(wrapper.text()).toContain('main config');
    expect(wrapper.text()).toContain('diff config');
  });
});
