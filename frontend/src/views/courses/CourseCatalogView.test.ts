import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import CourseCatalogView from './CourseCatalogView.vue';

vi.mock('../../services/auth', () => ({
  useAuth: () => ({
    apiFetch: vi.fn(async () => ({
      ok: true,
      json: async () => ({ modules: [] }),
    })),
    fullName: 'Participante de prueba',
    logout: vi.fn(),
  }),
}));

describe('CourseCatalogView', () => {
  let showModalDescriptor: PropertyDescriptor | undefined;
  let closeDescriptor: PropertyDescriptor | undefined;

  beforeEach(() => {
    showModalDescriptor = Object.getOwnPropertyDescriptor(HTMLDialogElement.prototype, 'showModal');
    closeDescriptor = Object.getOwnPropertyDescriptor(HTMLDialogElement.prototype, 'close');
    Object.defineProperty(HTMLDialogElement.prototype, 'showModal', {
      configurable: true,
      value(this: HTMLDialogElement) {
        this.setAttribute('open', '');
      },
    });
    Object.defineProperty(HTMLDialogElement.prototype, 'close', {
      configurable: true,
      value(this: HTMLDialogElement) {
        this.removeAttribute('open');
        this.dispatchEvent(new Event('close'));
      },
    });
  });

  afterEach(() => {
    if (showModalDescriptor) Object.defineProperty(HTMLDialogElement.prototype, 'showModal', showModalDescriptor);
    else Reflect.deleteProperty(HTMLDialogElement.prototype, 'showModal');
    if (closeDescriptor) Object.defineProperty(HTMLDialogElement.prototype, 'close', closeDescriptor);
    else Reflect.deleteProperty(HTMLDialogElement.prototype, 'close');
  });

  it('abre el plan de estudio desde la tarjeta y permite cerrarlo', async () => {
    const wrapper = mount(CourseCatalogView, {
      attachTo: document.body,
      global: { stubs: { InstitutionalHeader: true, BaseAlert: true } },
    });
    await flushPromises();

    await wrapper.get('button').trigger('click');
    await flushPromises();

    const dialog = document.body.querySelector('dialog');
    expect(dialog?.open).toBe(true);
    expect(dialog?.getAttribute('aria-modal')).toBe('true');
    expect(dialog?.textContent).toContain('Generalidades del Derecho Electoral');
    expect(dialog?.textContent).toContain('1. Introducción');
    expect(dialog?.textContent).toContain('Mecanismos de protección de la democracia en México.');
    expect(dialog?.textContent).toContain('10 temas');
    expect(dialog?.textContent).toContain('Cultura de la Prevención');
    expect(dialog?.textContent).toContain('Reflexionar sobre la importancia del contacto directo con la ciudadanía');

    await wrapper.get('button[aria-label="Cerrar plan de estudio"]').trigger('click');
    await flushPromises();
    expect(document.body.querySelector('dialog')).toBeNull();

    wrapper.unmount();
  });
});
