import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import ExamFlowView from './ExamFlowView.vue';

describe('flujo del módulo 1', () => {
  const requests: Array<{ path: string; init?: RequestInit }> = [];
  let currentTime = 0;

  beforeEach(() => {
    requests.length = 0;
    sessionStorage.setItem('fede_exam_token', 'test-token');
    sessionStorage.setItem('fede_exam_user', JSON.stringify({
      id: 1,
      first_name: 'Ana',
      paternal_surname: 'López',
      maternal_surname: 'Ruiz',
    }));

    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const path = String(input);
      requests.push({ path, init });
      if (path.endsWith('/api/questions')) {
        return new Response(JSON.stringify([{
          id: 11,
          number: 1,
          text: '¿Respuesta?',
          options: [{ id: 7, letter: 'A', text: 'Opción A' }],
        }]), { status: 200 });
      }
      if (path.endsWith('/api/evaluations/current')) {
        return new Response(JSON.stringify({ has_evaluation: false, evaluation: null }), { status: 200 });
      }
      if (path.endsWith('/api/evaluations/start')) {
        return new Response(JSON.stringify({
          evaluation_id: 24,
          resumed: false,
          video_completed: false,
          video_session_nonce: 'nonce-for-video-session-123456',
          current_question: 0,
          question_order: [11],
          answers: [],
        }), { status: 200 });
      }
      if (path.endsWith('/api/evaluations/24/video-completed')) {
        return new Response(JSON.stringify({ success: true, video_completed: true }), { status: 200 });
      }
      return new Response('{}', { status: 200 });
    }));
  });

  afterEach(() => {
    sessionStorage.clear();
    vi.unstubAllGlobals();
  });

  it('inicia la sesión antes de reproducir y permite completar un clip corto acumulando tiempo', async () => {
    const wrapper = mount(ExamFlowView);
    await flushPromises();

    const openVideo = wrapper.find('button[aria-label="Ver video de capacitación"]');
    await openVideo.trigger('click');
    await flushPromises();

    const video = wrapper.find('video');
    let playing = true;
    currentTime = 0;
    Object.defineProperty(video.element, 'currentTime', {
      configurable: true,
      get: () => currentTime,
      set: value => { currentTime = Number(value); },
    });
    Object.defineProperty(video.element, 'paused', {
      configurable: true,
      get: () => !playing,
    });
    Object.defineProperty(video.element, 'play', {
      configurable: true,
      value: vi.fn(async () => { playing = true; }),
    });
    Object.defineProperty(video.element, 'pause', {
      configurable: true,
      value: vi.fn(() => { playing = false; }),
    });

    const playFiveSeconds = async () => {
      playing = true;
      for (let time = 0.5; time <= 5; time += 0.5) {
        currentTime = time;
        await video.trigger('timeupdate');
      }
      playing = false;
      await video.trigger('ended');
    };

    await playFiveSeconds();
    let continueButton = wrapper.findAll('button').find(button => button.text().includes('Contestar evaluación'));
    expect(continueButton?.attributes('disabled')).toBeDefined();

    await wrapper.findAll('button').find(button => button.text().includes('Reproducir nuevamente'))!.trigger('click');
    await playFiveSeconds();
    await flushPromises();

    continueButton = wrapper.findAll('button').find(button => button.text().includes('Contestar evaluación'));
    expect(continueButton?.attributes('disabled')).toBeUndefined();
    await continueButton!.trigger('click');
    await flushPromises();

    const completionRequest = requests.find(request => request.path.endsWith('/api/evaluations/24/video-completed'));
    expect(completionRequest).toBeDefined();
    expect(requests.findIndex(request => request.path.endsWith('/api/evaluations/start')))
      .toBeLessThan(requests.findIndex(request => request.path.includes('/video-completed')));
    expect(JSON.parse(String(completionRequest?.init?.body))).toMatchObject({
      nonce: 'nonce-for-video-session-123456',
      played_seconds: 10,
    });
    expect(wrapper.text()).toContain('Opción A');
  });

  it('muestra correctamente los acentos en los títulos de apoyo', async () => {
    const wrapper = mount(ExamFlowView);
    await flushPromises();
    await wrapper.find('button[aria-label="Abrir documentos de apoyo"]').trigger('click');
    expect(wrapper.text()).toContain('Ley de Medios de Impugnación Electorales');
    expect(wrapper.text()).toContain('Ley General de Partidos Políticos');
  });
});
