import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import ModulePanelView from './ModulePanelView.vue';

const moduleStatuses = [
  { module_id: 1, name: 'Módulo 1', attempts: 1, attempts_remaining: 2, best_score: 80, passed: true, in_progress: false, questions_available: true, available: false },
  { module_id: 2, name: 'Módulo 2', attempts: 0, attempts_remaining: 3, best_score: null, passed: false, in_progress: false, questions_available: true, available: true },
  { module_id: 3, name: 'Módulo 3', attempts: 0, attempts_remaining: 3, best_score: null, passed: false, in_progress: false, questions_available: true, available: false },
];

function mockStatus(modules = moduleStatuses) {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({
    modules,
    course: { key: 'course', name: 'Curso', completed: modules.every(module => module.passed) },
  }), { status: 200 })));
}

describe('acceso secuencial a módulos', () => {
  beforeEach(() => {
    localStorage.setItem('fede_exam_token', 'test-token');
    localStorage.setItem('fede_exam_user', JSON.stringify({
      id: 1,
      first_name: 'Ana',
      paternal_surname: 'López',
      maternal_surname: 'Ruiz',
      email: 'ana@test.org',
      curp: 'X',
    }));
    mockStatus();
  });

  afterEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  it('solo permite abrir el siguiente módulo y bloquea los acreditados', async () => {
    const wrapper = mount(ModulePanelView);
    await flushPromises();
    const cards = wrapper.findAll('article');
    const buttons = cards.map(card => card.find('button'));

    expect(wrapper.text()).toContain('Delitos Electorales y su investigación en el Sistema Electoral Mexicano');
    expect(buttons[0].element.disabled).toBe(true);
    expect(buttons[0].text()).toContain('Ya acreditado');
    expect(buttons[1].element.disabled).toBe(false);
    expect(buttons[2].element.disabled).toBe(true);
    expect(cards[2].text()).toContain('Acredita primero el módulo 2.');

    await buttons[1].trigger('click');
    expect(wrapper.emitted('select-module')).toEqual([[2]]);
  });

  it('bloquea los tres módulos al completar el curso', async () => {
    mockStatus(moduleStatuses.map(module => ({
      ...module,
      passed: true,
      available: false,
    })));

    const wrapper = mount(ModulePanelView);
    await flushPromises();

    expect(wrapper.findAll('article').every(card => card.find('button').element.disabled)).toBe(true);
    expect(wrapper.text()).toContain('Curso completo');
  });
});
