import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';
import BaseAlert from './BaseAlert.vue';

describe('BaseAlert', () => {
  it('expone semántica accesible y jerarquía del patrón shadcn', () => {
    const wrapper = mount(BaseAlert, {
      props: { variant: 'destructive', title: 'No se guardó', description: 'Revisa la conexión.' },
    });
    expect(wrapper.attributes('role')).toBe('alert');
    expect(wrapper.attributes('data-slot')).toBe('alert');
    expect(wrapper.get('[data-slot="alert-title"]').text()).toBe('No se guardó');
    expect(wrapper.get('[data-slot="alert-description"]').text()).toBe('Revisa la conexión.');
  });

  it('anuncia estados informativos de forma no interruptiva e incluye acciones', () => {
    const wrapper = mount(BaseAlert, {
      props: { variant: 'success', title: 'Guardado' },
      slots: { default: 'La respuesta quedó registrada.', action: '<button>Continuar</button>' },
    });
    expect(wrapper.attributes('role')).toBe('status');
    expect(wrapper.attributes('aria-live')).toBe('polite');
    expect(wrapper.get('[data-slot="alert-action"]').text()).toBe('Continuar');
  });
});
