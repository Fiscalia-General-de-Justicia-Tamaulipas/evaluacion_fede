import { describe, expect, it } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import ConfirmDialog from './ConfirmDialog.vue';

describe('ConfirmDialog', () => {
  it('presenta un diálogo accesible, enfoca cancelar y permite cancelar con Escape', async () => {
    const wrapper = mount(ConfirmDialog, {
      props: { title: '¿Finalizar?', description: 'No podrás cambiar respuestas.' },
      attachTo: document.body,
    });
    await flushPromises();
    const dialog = document.body.querySelector('[role="alertdialog"]');
    expect(dialog?.getAttribute('aria-modal')).toBe('true');
    expect(document.activeElement?.textContent).toContain('Cancelar');
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    expect(wrapper.emitted('cancel')).toHaveLength(1);
    wrapper.unmount();
  });
});
