import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';
import EvaluationResult from './EvaluationResult.vue';

const defaults = {
  moduleId: 1,
  moduleName: 'Nociones básicas de derecho electoral',
  correct: 4,
  total: 10,
  attempt: 1,
  attemptsRemaining: 2,
};

describe('EvaluationResult', () => {
  it('acredita con calificación mínima y no ofrece constancia de un módulo individual', () => {
    const wrapper = mount(EvaluationResult, { props: { ...defaults, score: 70 } });
    expect(wrapper.text()).toContain('Módulo aprobado');
    expect(wrapper.text()).toContain('Acreditado');
    expect(wrapper.text()).not.toContain('constancia');
    expect(wrapper.emitted('certificate')).toBeUndefined();
  });

  it('permite reintentar mientras existan intentos y emite el evento', async () => {
    const wrapper = mount(EvaluationResult, { props: { ...defaults, score: 40 } });
    const retry = wrapper.findAll('button').find((button) => button.text().includes('Reintentar examen'));
    expect(retry).toBeDefined();
    await retry!.trigger('click');
    expect(wrapper.emitted('retry')).toHaveLength(1);
  });

  it('oculta reintento al agotar los tres intentos', () => {
    const wrapper = mount(EvaluationResult, { props: { ...defaults, score: 40, attemptsRemaining: 0 } });
    expect(wrapper.text()).toContain('Intentos agotados');
    expect(wrapper.text()).not.toContain('Reintentar examen');
  });
});
