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
      if (url.includes('/api/evaluations/24/finish')) return new Response(JSON.stringify({ score: 70, correct: 1, total: 1, passed: true, attempt_number: 1 }), { status: 200 });
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

  it('muestra únicamente las diez preguntas seleccionadas de un banco de 22 al reanudar', async () => {
    const bank = Array.from({ length: 22 }, (_, index) => ({
      id: index + 1,
      number: index + 1,
      text: `Pregunta del banco ${index + 1}`,
      options: [{ id: (index + 1) * 10, letter: 'A', text: `Opción ${index + 1}` }],
    }));
    const selectedIds = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20];
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/api/questions')) return new Response(JSON.stringify(bank), { status: 200 });
      if (url.includes('/api/evaluations/current')) {
        return new Response(JSON.stringify({
          has_evaluation: true,
          evaluation: {
            id: 24,
            completed: false,
            video_completed: true,
            current_question: 0,
            question_order: selectedIds,
            answers: [{ question_id: 1, option_id: 10 }],
          },
        }), { status: 200 });
      }
      return new Response('{}', { status: 200 });
    }));

    const firstSession = mount(ExamModuleView, { props: { moduleId: 2 } });
    await flushPromises();
    expect(firstSession.text()).toContain('Pregunta 1 de 10');
    expect(firstSession.text()).toContain('Pregunta del banco 2');
    expect(firstSession.text()).toContain('0 de 10 contestadas');
    expect(firstSession.get('[role="progressbar"]').attributes('aria-valuenow')).toBe('0');
    expect(firstSession.find('[aria-label="Ir a una pregunta"]').findAll('button')).toHaveLength(10);
    firstSession.unmount();

    const resumedSession = mount(ExamModuleView, { props: { moduleId: 2 } });
    await flushPromises();
    expect(resumedSession.text()).toContain('Pregunta 1 de 10');
    expect(resumedSession.text()).toContain('Pregunta del banco 2');
    expect(resumedSession.find('[aria-label="Ir a una pregunta"]').findAll('button')).toHaveLength(10);
  });

  it('mantiene la pregunta actual y permite reintentar si falla el guardado del avance', async () => {
    const bank = Array.from({ length: 22 }, (_, index) => ({
      id: index + 1,
      number: index + 1,
      text: `Pregunta del banco ${index + 1}`,
      options: [{ id: (index + 1) * 10, letter: 'A', text: `Opción ${index + 1}` }],
    }));
    let progressAttempts = 0;
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/api/questions')) return new Response(JSON.stringify(bank), { status: 200 });
      if (url.includes('/api/evaluations/current')) {
        return new Response(JSON.stringify({
          has_evaluation: true,
          evaluation: {
            id: 24,
            completed: false,
            video_completed: true,
            current_question: 0,
            question_order: [2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
            answers: [],
          },
        }), { status: 200 });
      }
      if (url.includes('/api/evaluations/24/answers')) return new Response('{}', { status: 200 });
      if (url.includes('/api/evaluations/24/progress')) {
        progressAttempts++;
        if (progressAttempts === 1) {
          return new Response(JSON.stringify({ detail: 'No puedes avanzar más allá de las preguntas pendientes.' }), { status: 400 });
        }
        return new Response(JSON.stringify({ success: true, current_question: 1 }), { status: 200 });
      }
      return new Response('{}', { status: 200 });
    }));

    const wrapper = mount(ExamModuleView, { props: { moduleId: 2 } });
    await flushPromises();
    await wrapper.findAll('button').find(button => button.text().includes('Opción 2'))!.trigger('click');
    await flushPromises();
    await wrapper.findAll('button').find(button => button.text().includes('Siguiente pregunta'))!.trigger('click');
    await flushPromises();

    expect(wrapper.text()).toContain('Pregunta 1 de 10');
    expect(document.body.textContent).toContain('El servidor rechazó el guardado: No puedes avanzar más allá de las preguntas pendientes.');
    const retryButton = Array.from(document.body.querySelectorAll('button'))
      .find(button => button.textContent?.includes('Reintentar guardado'));
    expect(retryButton).toBeDefined();
    retryButton!.click();
    await flushPromises();
    expect(wrapper.text()).toContain('Pregunta 2 de 10');
    expect(progressAttempts).toBe(2);
  });

  it('muestra la causa del fallo de finalización y permite reintentar', async () => {
    const bank = Array.from({ length: 22 }, (_, index) => ({
      id: index + 1,
      number: index + 1,
      text: `Pregunta del banco ${index + 1}`,
      options: [{ id: (index + 1) * 10, letter: 'A', text: `Opción ${index + 1}` }],
    }));
    const selectedIds = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20];
    let finishAttempts = 0;
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/api/questions')) return new Response(JSON.stringify(bank), { status: 200 });
      if (url.includes('/api/evaluations/current')) {
        return new Response(JSON.stringify({
          has_evaluation: true,
          evaluation: {
            id: 24,
            completed: false,
            video_completed: true,
            current_question: 9,
            question_order: selectedIds,
            answers: selectedIds.map(question_id => ({
              question_id,
              option_id: question_id * 10,
            })),
          },
        }), { status: 200 });
      }
      if (url.includes('/api/evaluations/24/finish')) {
        finishAttempts++;
        if (finishAttempts === 1) {
          return new Response(JSON.stringify({
            detail: 'Debes responder todas las preguntas visibles. Preguntas pendientes: 10',
          }), { status: 400 });
        }
        return new Response(JSON.stringify({
          score: 100,
          correct: 10,
          total: 10,
          passed: true,
          attempt_number: 1,
        }), { status: 200 });
      }
      return new Response('{}', { status: 200 });
    }));

    const wrapper = mount(ExamModuleView, { props: { moduleId: 2 } });
    await flushPromises();
    expect(wrapper.text()).toContain('10 de 10 contestadas');
    expect(wrapper.text()).toContain('Pregunta 10 de 10');

    await wrapper.find('[aria-label="Finalizar evaluación"]').trigger('click');
    const confirmButton = Array.from(document.body.querySelectorAll('button'))
      .find(button => button.textContent?.trim() === 'Finalizar evaluación');
    confirmButton!.click();
    await flushPromises();

    expect(document.body.textContent).toContain(
      'Debes responder todas las preguntas visibles. Preguntas pendientes: 10',
    );
    const retryButton = Array.from(document.body.querySelectorAll('button'))
      .find(button => button.textContent?.includes('Reintentar finalización'));
    expect(retryButton).toBeDefined();
    retryButton!.click();
    await flushPromises();

    expect(finishAttempts).toBe(2);
    expect(wrapper.text()).toContain('Módulo aprobado');
  });
});
