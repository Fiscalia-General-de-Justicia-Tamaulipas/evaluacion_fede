import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import ExamModuleView from './ExamModuleView.vue';

describe('flujo de evaluación', () => {
  beforeEach(() => {
    localStorage.setItem('fede_exam_token', 'test-token');
    localStorage.setItem('fede_exam_user', JSON.stringify({ id: 1, first_name: 'Ana', paternal_surname: 'López', maternal_surname: 'Ruiz', email: 'ana@test.org', curp: 'X' }));
    vi.stubGlobal('fetch', vi.fn().mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/api/questions')) return new Response(JSON.stringify([{ id: 11, number: 1, text: '¿Respuesta?', options: [{ id: 7, letter: 'A', text: 'Opción A' }] }]), { status: 200 });
      if (url.includes('/api/evaluations/current')) return new Response(JSON.stringify({ has_evaluation: true, evaluation: { id: 24, completed: false, video_completed: true, answers: [], question_order: [11] } }), { status: 200 });
      if (url.includes('/api/evaluations/start')) return new Response(JSON.stringify({ evaluation_id: 24, video_completed: true, question_order: [11], answers: [] }), { status: 200 });
      if (url.includes('/api/evaluations/24/answers')) return new Response('{}', { status: 200 });
      if (url.includes('/api/evaluations/24/finish')) return new Response(JSON.stringify({ score: 70, correct: 1, total: 1, passed: true, attempt_number: 1, certificate_id: 4 }), { status: 200 });
      return new Response('{}', { status: 200 });
    }));
    vi.spyOn(window, 'confirm').mockReturnValue(true);
  });

  afterEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  it('recupera preguntas, registra respuesta, confirma y muestra acreditación', async () => {
    const wrapper = mount(ExamModuleView, { props: { moduleId: 2 } });
    await flushPromises();
    await flushPromises();
    expect(wrapper.text()).toContain('Opción A');
    const option = wrapper.findAll('button').find((button) => button.text().includes('Opción A'));
    expect(option).toBeDefined();
    await option!.trigger('click');
    await flushPromises();
    const finishButton = wrapper.findAll('button').find((button) => button.text().trim() === 'Finalizar');
    expect(finishButton).toBeDefined();
    await finishButton!.trigger('click');
    await flushPromises();
    const dialog = document.body.querySelector('[role="alertdialog"]');
    expect(dialog).not.toBeNull();
    expect(dialog?.textContent).toContain('ya no podrás modificarlas');
    const confirmButton = Array.from(document.body.querySelectorAll('button')).find((button) => button.textContent?.trim() === 'Finalizar evaluación');
    expect(confirmButton).toBeDefined();
    confirmButton!.click();
    await flushPromises();
    expect(wrapper.text()).toContain('Módulo aprobado');
  });
});
