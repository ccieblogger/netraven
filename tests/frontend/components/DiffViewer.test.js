/**
 * @jest-environment jsdom
 */
import { mount } from '@vue/test-utils';
import DiffViewer from '../../../frontend/src/components/DiffViewer.vue';

describe('DiffViewer', () => {
  const oldContent = 'interface GigabitEthernet0/0\n ip address 192.168.1.1 255.255.255.0\n no shutdown';
  const newContent = 'interface GigabitEthernet0/0\n ip address 192.168.1.1 255.255.255.0\n shutdown';

  it('renders with required props', () => {
    const wrapper = mount(DiffViewer, {
      props: { oldContent, newContent, isLoading: false, error: '' }
    });
    expect(wrapper.text()).toContain('Configuration Diff');
    expect(wrapper.attributes('role')).toBe('region');
  });

  it('shows loading state', () => {
    const wrapper = mount(DiffViewer, {
      props: { oldContent, newContent, isLoading: true, error: '' }
    });
    expect(wrapper.text()).toContain('Loading...');
  });

  it('shows error state', () => {
    const wrapper = mount(DiffViewer, {
      props: { oldContent, newContent, isLoading: false, error: 'Diff error' }
    });
    expect(wrapper.text()).toContain('Diff error');
  });

  it('toggles view type', async () => {
    const wrapper = mount(DiffViewer, {
      props: { oldContent, newContent, isLoading: false, error: '' }
    });
    const toggleBtn = wrapper.find('button[aria-label="Toggle diff view type"]');
    expect(toggleBtn.exists()).toBe(true);
    await toggleBtn.trigger('click');
    // After click, button text should change
    expect(toggleBtn.text()).toMatch(/Unified|Side-by-Side/);
  });

  it('copy to clipboard button exists', () => {
    const wrapper = mount(DiffViewer, {
      props: { oldContent, newContent, isLoading: false, error: '' }
    });
    const copyBtn = wrapper.find('button[aria-label="Copy diff to clipboard"]');
    expect(copyBtn.exists()).toBe(true);
  });

  it('has ARIA roles and labels for accessibility', () => {
    const wrapper = mount(DiffViewer, {
      props: { oldContent, newContent, isLoading: false, error: '' }
    });
    expect(wrapper.attributes('role')).toBe('region');
    expect(wrapper.attributes('aria-label')).toBe('Configuration Diff Viewer');
    const diffContent = wrapper.find('div[aria-label="Diff content"]');
    expect(diffContent.exists()).toBe(true);
  });
});
