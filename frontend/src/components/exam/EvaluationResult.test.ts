import { describe, expect, it, vi } from 'vitest';
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
  it('acredita solo con calificación de 70 o más y ofrece constancia', async () => {
    const wrapper = mount(EvaluationResult, { props: { ...defaults, score: 70 } });
    expect(wrapper.text()).toContain('Módulo aprobado');
    expect(wrapper.text()).toContain('Acreditado');
    await wrapper.get('button:nth-of-type(2)').trigger('click');
    expect(wrapper.emitted('certificate')).toHaveLength(1);
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
