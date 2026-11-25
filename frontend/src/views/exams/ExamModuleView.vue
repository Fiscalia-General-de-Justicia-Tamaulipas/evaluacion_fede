<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { ArrowLeft, CheckCircle2, ChevronLeft, ChevronRight, LockKeyhole, PlayCircle, X } from 'lucide-vue-next';
import { useAuth } from '../../services/auth';
import EvaluationResult from '../../components/exam/EvaluationResult.vue';
import InstitutionalHeader from '../../components/layout/InstitutionalHeader.vue';
import BaseAlert from '../../components/ui/BaseAlert.vue';
import ConfirmDialog from '../../components/ui/ConfirmDialog.vue';

const props = defineProps<{ moduleId: number }>();
const emit = defineEmits<{ (e: 'back'): void }>();
const { apiFetch, fullName } = useAuth();

type Option = { id: number; letter: string; text: string };
type Question = { id: number; number: number; text: string; options: Option[] };

const names: Record<number, string> = {
  1: 'Generalidades del Derecho Electoral.',
  2: 'Análisis de los Delitos Electorales.',
  3: 'Integración de la Carpeta de Investigación, Primer respondiente, Retos en la Investigación y Cultura de Prevención',
};

const stage = ref<'intro' | 'exam' | 'result'>('intro');
const questions = ref<Question[]>([]);
const current = ref(0);
const answers = ref<Record<number, number>>({});
const evaluationId = ref<number | null>(null);
const videoDone = ref(false);
const videoNonce = ref('');
const videoPlayedSeconds = ref(0);
let lastVideoTime = 0;
const loading = ref(false);
const savingAnswer = ref(false);
const savingProgress = ref(false);
const message = ref('');
const pendingProgressPosition = ref<number | null>(null);
const canRetryFinalization = ref(false);
const showFinishConfirmation = ref(false);
const videoModalOpen = ref(false);
const modalVideoRef = ref<HTMLVideoElement | null>(null);
const result = ref({ score: 0, correct: 0, total: 0, passed: false, attempt: 1 });

const q = computed(() => questions.value[current.value]);
const allAnswered = computed(() => questions.value.length > 0 && questions.value.every(question => answers.value[question.id] != null));
const answeredCount = computed(() => questions.value.filter(question => answers.value[question.id] != null).length);
const progress = computed(() => questions.value.length ? (answeredCount.value / questions.value.length) * 100 : 0);
const maxReachableIndex = computed(() => {
  const nextUnanswered = questions.value.findIndex(question => answers.value[question.id] == null);
  return nextUnanswered === -1 ? Math.max(questions.value.length - 1, 0) : nextUnanswered;
});
const canNext = computed(() => !!q.value && answers.value[q.value.id] != null && current.value < maxReachableIndex.value);
const canContinueAfterVideo = computed(() => videoDone.value && videoPlayedSeconds.value >= 10);

function trackVideoProgress(includeFinalFrame = false) {
  const video = modalVideoRef.value;
  if (!video) return;

  const currentTime = video.currentTime;
  if ((!video.paused || includeFinalFrame) && !video.seeking && currentTime > lastVideoTime) {
    videoPlayedSeconds.value += Math.min(currentTime - lastVideoTime, 1);
  }
  lastVideoTime = currentTime;
}

async function replayVideo() {
  const video = modalVideoRef.value;
  if (!video) return;

  videoDone.value = false;
  lastVideoTime = 0;
  video.currentTime = 0;
  try {
    await video.play();
  } catch (error) {
    message.value = error instanceof Error ? error.message : 'No se pudo reproducir el video nuevamente.';
    videoDone.value = true;
  }
}

async function prepareEvaluation() {
  if (evaluationId.value && videoNonce.value) return;
  const response = await apiFetch(`/api/evaluations/start?module_id=${props.moduleId}`, {
    method: 'POST',
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(data?.detail || 'No se pudo preparar la evaluación.');
  if (!data?.video_session_nonce) throw new Error('No se pudo iniciar una sesión válida de reproducción.');
  await applyStart(data);
}

async function openVideoModal() {
  if (loading.value || videoModalOpen.value) return;
  loading.value = true;
  message.value = '';
  try {
    await prepareEvaluation();
    if (stage.value !== 'intro') return;
  } catch (error) {
    message.value = error instanceof Error ? error.message : 'No se pudo preparar la evaluación.';
    return;
  } finally {
    loading.value = false;
  }
  lastVideoTime = 0;
  videoModalOpen.value = true;
  document.body.style.overflow = 'hidden';
}

function closeVideoModal() {
  videoModalOpen.value = false;
  modalVideoRef.value?.pause();
  lastVideoTime = 0;
  document.body.style.overflow = '';
}

function handleEscape(event: KeyboardEvent) {
  if (event.key === 'Escape') closeVideoModal();
}

async function loadQuestions() {
  const response = await apiFetch(`/api/questions?module_id=${props.moduleId}`);
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(data?.detail || 'No se pudo cargar el cuestionario. Intenta recargar el módulo.');
  questions.value = Array.isArray(data) ? data : [];
}

function applyOrder(order: number[]) {
  if (!order.length) return;

  const byId = new Map(questions.value.map(question => [question.id, question]));
  const ordered = order.map(id => byId.get(id)).filter((item): item is Question => !!item);
  if (ordered.length !== order.length) {
    throw new Error('No se pudieron recuperar todas las preguntas de esta evaluación.');
  }
  questions.value = ordered;
}

async function restore() {
  try {
  await loadQuestions();
  const response = await apiFetch(`/api/evaluations/current?module_id=${props.moduleId}`);
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(data?.detail || 'No se pudo recuperar el estado de la evaluación.');
  if (!data.has_evaluation || !data.evaluation) return;
  if (data.evaluation.completed) {
    result.value = {
      score: data.evaluation.score ?? 0,
      correct: data.evaluation.correct ?? 0,
      total: data.evaluation.total_questions ?? 0,
      passed: !!data.evaluation.passed,
      attempt: data.evaluation.attempt_number ?? 1,
    };
    stage.value = 'result';
    return;
  }
  evaluationId.value = data.evaluation.id;
  videoDone.value = data.evaluation.video_completed;
  videoNonce.value = data.evaluation.video_session_nonce ?? '';
  for (const answer of data.evaluation.answers ?? []) answers.value[answer.question_id] = answer.option_id;
  applyOrder(data.evaluation.question_order ?? []);
  if (videoDone.value) {
    stage.value = 'exam';
    if (questions.value.length > 0) {
      current.value = Math.min(
        Math.max(data.evaluation.current_question ?? 0, 0),
        questions.value.length - 1,
      );
    }
  }
  } catch (error: any) {
    message.value = error?.message || 'No se pudo cargar el módulo. Inténtalo nuevamente.';
  }
}

async function start() {
  if (!canContinueAfterVideo.value || loading.value) return;
  loading.value = true;
  message.value = '';
  try {
    if (!evaluationId.value || !videoNonce.value) {
      throw new Error('Abre el video de capacitación antes de iniciar la evaluación.');
    }
    const response = await apiFetch(`/api/evaluations/${evaluationId.value}/video-completed`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        nonce: videoNonce.value,
        played_seconds: videoPlayedSeconds.value,
      }),
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) throw new Error(data?.detail || 'No se pudo registrar el video completado.');
    closeVideoModal();
    stage.value = 'exam';
    videoDone.value = true;
  } catch (error: any) {
    message.value = error.message;
    closeVideoModal();
  } finally {
    loading.value = false;
  }
}

async function applyStart(data: any) {
  evaluationId.value = data.evaluation_id;
  videoNonce.value = data.video_session_nonce;
  for (const answer of data.answers ?? []) answers.value[answer.question_id] = answer.option_id;
  applyOrder(data.question_order ?? []);
  if (questions.value.length > 0) {
    current.value = Math.min(
      Math.max(data.current_question ?? 0, 0),
      questions.value.length - 1,
    );
  }
  if (data.video_completed) {
    stage.value = 'exam';
    videoDone.value = true;
    return;
  }
}

async function selectOption(optionId: number) {
  if (!q.value || !evaluationId.value || savingAnswer.value) return;
  const questionId = q.value.id;
  const previousOption = answers.value[questionId];
  savingAnswer.value = true;
  message.value = '';
  answers.value[questionId] = optionId;
  try {
    const response = await apiFetch(`/api/evaluations/${evaluationId.value}/answers`, {
      method: 'PUT',
      body: JSON.stringify({ question_id: questionId, option_id: optionId }),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => null);
      throw new Error(data?.detail || 'No se pudo guardar la respuesta. Inténtalo de nuevo.');
    }
  } catch (error: any) {
    message.value = error?.message || 'No fue posible conectar con el servidor.';
    if (previousOption == null) delete answers.value[questionId];
    else answers.value[questionId] = previousOption;
  } finally {
    savingAnswer.value = false;
  }
}

async function saveCurrentProgress(position: number): Promise<boolean> {
  if (!evaluationId.value) {
    message.value = 'No hay una evaluación activa para guardar el avance. Recarga el módulo para recuperar tu progreso.';
    return false;
  }
  if (savingProgress.value) return false;
  savingProgress.value = true;
  try {
    const response = await apiFetch(`/api/evaluations/${evaluationId.value}/progress`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ current_question: position }),
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      const detail = typeof data?.detail === 'string'
        ? data.detail
        : `Error HTTP ${response.status}.`;
      throw new Error(`El servidor rechazó el guardado: ${detail}`);
    }
    pendingProgressPosition.value = null;
    message.value = '';
    return true;
  } catch (error) {
    pendingProgressPosition.value = position;
    message.value = error instanceof TypeError
      ? 'No se pudo conectar con el servidor. Tu respuesta sigue guardada; reintenta el avance.'
      : error instanceof Error
        ? error.message
        : 'No se pudo guardar tu avance. Reintenta el guardado.';
    return false;
  } finally {
    savingProgress.value = false;
  }
}

async function navigateToQuestion(position: number) {
  if (savingProgress.value) return;
  message.value = '';
  if (await saveCurrentProgress(position)) current.value = position;
}

async function retryPendingProgress() {
  const position = pendingProgressPosition.value;
  if (position === null || savingProgress.value) return;
  if (await saveCurrentProgress(position)) current.value = position;
}

async function previous() {
  if (current.value <= 0 || savingProgress.value) return;
  await navigateToQuestion(current.value - 1);
}

async function next() {
  if (!canNext.value || savingProgress.value) return;
  await navigateToQuestion(current.value + 1);
}

async function goToQuestion(index: number) {
  if (
    index < 0 ||
    index > maxReachableIndex.value ||
    index >= questions.value.length ||
    index === current.value ||
    savingProgress.value
  ) return;
  await navigateToQuestion(index);
}

async function finish() {
  if (!allAnswered.value || !evaluationId.value || loading.value) return;
  message.value = '';
  canRetryFinalization.value = false;
  showFinishConfirmation.value = true;
}

async function finishConfirmed() {
  showFinishConfirmation.value = false;
  if (!allAnswered.value || !evaluationId.value || loading.value) return;
  loading.value = true;
  message.value = '';
  try {
    const response = await apiFetch(`/api/evaluations/${evaluationId.value}/finish`, {
      method: 'POST',
      body: JSON.stringify({ answers: [] }),
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      const detail = typeof data?.detail === 'string'
        ? data.detail
        : `El servidor no pudo finalizar la evaluación (HTTP ${response.status}).`;
      throw new Error(detail);
    }
    result.value = {
      score: data.score,
      correct: data.correct,
      total: data.total,
      passed: data.passed,
      attempt: data.attempt_number,
    };
    canRetryFinalization.value = false;
    stage.value = 'result';
  } catch (error: any) {
    canRetryFinalization.value = true;
    message.value = error instanceof TypeError
      ? 'No se pudo conectar con el servidor. Las respuestas siguen guardadas; puedes reintentar la finalización.'
      : error?.message || 'No se pudo finalizar la evaluación. Puedes reintentarlo.';
  } finally {
    loading.value = false;
  }
}

function retryFinalization() {
  if (!canRetryFinalization.value || loading.value) return;
  void finishConfirmed();
}

function retry() {
  if (result.value.passed || result.value.attempt >= 3) return;
  answers.value = {};
  evaluationId.value = null;
  current.value = 0;
  videoDone.value = false;
  message.value = '';
  stage.value = 'intro';
}

onMounted(() => {
  restore();
  window.addEventListener('keydown', handleEscape);
});

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleEscape);
  document.body.style.overflow = '';
});
</script>

<template>
  <div class="min-h-screen bg-[var(--color-paper)] text-[var(--color-ink)]">
    <InstitutionalHeader :show-back="true" :module-label="`Módulo ${moduleId}`" :participant-name="fullName" @back="emit('back')" />

    <main id="main-content" tabindex="-1" class="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
      <BaseAlert v-if="message && stage !== 'result'" floating variant="destructive" title="No se pudo completar la acción" :description="message">
        <template #action>
          <button
            v-if="pendingProgressPosition !== null"
            type="button"
            :disabled="savingProgress"
            class="rounded-md border border-red-800 px-3 py-1.5 font-semibold disabled:opacity-60"
            @click="retryPendingProgress"
          >
            {{ savingProgress ? 'Reintentando…' : 'Reintentar guardado' }}
          </button>
          <button
            v-if="canRetryFinalization"
            type="button"
            :disabled="loading"
            class="rounded-md border border-red-800 px-3 py-1.5 font-semibold disabled:opacity-60"
            @click="retryFinalization"
          >
            {{ loading ? 'Reintentando…' : 'Reintentar finalización' }}
          </button>
        </template>
      </BaseAlert>
      <section v-if="stage === 'intro'" class="mx-auto max-w-4xl">
        <div class="rounded-[var(--radius-card)] border border-[var(--color-line)] bg-[var(--color-surface)] p-5 shadow-[var(--shadow-card)] sm:p-8 lg:p-10">
          <div class="flex items-center gap-2 text-sm font-semibold text-[var(--color-accent)]">
            <PlayCircle :size="18" aria-hidden="true" />
            Material introductorio · Módulo {{ moduleId }}
          </div>
          <h1 class="mt-4 max-w-3xl text-2xl font-bold leading-tight tracking-tight text-[var(--color-brand-950)] sm:text-3xl lg:text-4xl">{{ names[moduleId] }}</h1>
          <p class="mt-4 max-w-2xl text-base leading-7 text-[var(--color-muted)]">Revisa el material del curso antes de iniciar la evaluación. El video debe completarse para habilitar las preguntas.</p>

          <div class="mt-6 flex items-start gap-3 rounded-xl border border-[var(--color-line)] bg-[var(--color-paper)] p-4">
            <LockKeyhole v-if="!videoDone" :size="19" class="mt-0.5 shrink-0 text-[var(--color-brand-700)]" aria-hidden="true" />
            <CheckCircle2 v-else :size="19" class="mt-0.5 shrink-0 text-[var(--color-success)]" aria-hidden="true" />
            <p v-if="!videoDone" class="text-sm leading-6 text-[var(--color-brand-900)]">Completa el video para continuar. Tu avance se guardará al comenzar la evaluación.</p>
            <p v-else class="text-sm font-semibold leading-6 text-[var(--color-success)]">Video completado. Ya puedes continuar con la evaluación.</p>
          </div>

          <div class="mt-7 flex flex-col gap-3 sm:flex-row sm:items-center">
            <button type="button" class="intro-primary page-control inline-flex min-h-12 items-center justify-center gap-2 rounded-[var(--radius-control)] bg-[var(--color-brand-900)] px-5 py-3 text-sm font-semibold text-white [@media(hover:hover)_and_(pointer:fine)]:hover:bg-[var(--color-brand-800)]" aria-label="Ver video de capacitación" @click="openVideoModal">
              <PlayCircle :size="19" aria-hidden="true" /> Ver video de capacitación
            </button>
            <span class="text-sm leading-6 text-[var(--color-muted)]">La evaluación se desbloquea al finalizar la reproducción.</span>
          </div>
        </div>
      </section>

      <Transition name="fade">
        <div v-if="videoModalOpen && stage === 'intro'" class="fixed inset-0 z-[9999] flex min-h-dvh flex-col overflow-y-auto bg-[#20201f] text-white" role="dialog" aria-modal="true" aria-labelledby="video-modal-title" @click.self="closeVideoModal">
          <div class="flex min-h-dvh w-full flex-col">
            <header class="border-b border-white/20 bg-[#292928] px-4 py-4 sm:px-5 md:px-10">
              <div class="mx-auto flex max-w-7xl items-center gap-4">
                <button type="button" title="Regresar al panel de módulos" aria-label="Regresar al panel de módulos" class="page-control inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border border-white/30 text-white [@media(hover:hover)_and_(pointer:fine)]:hover:bg-white/10" @click="emit('back')">
                  <ArrowLeft :size="20" aria-hidden="true" />
                </button>
                <img src="/logo_fgjtam.png" alt="Logo Fiscalía General de Justicia de Tamaulipas" class="h-9 w-auto max-w-[72px] object-contain sm:h-12 sm:max-w-none md:h-16" />
                <div class="h-8 w-px shrink-0 bg-white/40 sm:h-10 md:h-12" />
                <img src="/logo_fede.png" alt="Logo Fiscalía Especializada en Delitos Electorales" class="h-9 w-auto max-w-[72px] object-contain sm:h-12 sm:max-w-none md:h-16" />
                <div class="ml-auto min-w-0 pr-10">
                  <p class="hidden truncate text-xs font-bold uppercase tracking-[0.18em] text-white/75 sm:block">Material introductorio</p>
                  <h2 id="video-modal-title" class="mt-1 text-sm font-black text-white md:text-lg">Delitos Electorales y su investigación</h2>
                </div>
                <button type="button" title="Cerrar video" aria-label="Cerrar video" class="page-control absolute right-3 top-3 inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-white sm:right-5 sm:top-5 md:right-10" @click="closeVideoModal">
                  <X :size="20" aria-hidden="true" />
                </button>
              </div>
            </header>

            <main class="flex flex-1 flex-col items-center justify-center px-4 py-8 md:px-10 md:py-12">
              <div class="mb-6 w-full max-w-6xl text-left md:mb-8">
                <p class="text-xl font-bold leading-tight md:text-3xl">Módulo {{ moduleId }}: {{ names[moduleId] }}</p>
                <p class="mt-2 text-sm leading-6 text-white/75 md:text-base">Reproduce el video completo antes de contestar la evaluación.</p>
              </div>

              <div class="w-full max-w-6xl overflow-hidden rounded-2xl border border-white/10 bg-black shadow-2xl md:rounded-3xl">
                <video
                  ref="modalVideoRef"
                  class="mx-auto block max-h-[68vh] w-full object-contain"
                  controls
                  autoplay
                  playsinline
                  preload="metadata"
                  @timeupdate="trackVideoProgress"
                  @ended="videoDone = true; trackVideoProgress(true)"
                >
                  <source :src="`/curso-modulo${moduleId}.mp4`" type="video/mp4" />
                  Tu navegador no soporta video HTML5.
                </video>
              </div>

              <div class="mt-6 flex w-full max-w-6xl flex-col items-stretch justify-between gap-4 border-t border-white/15 pt-6 sm:flex-row sm:items-center">
                <p class="text-sm leading-6 text-white/75">
                  <span v-if="!videoDone">La evaluación se habilita al terminar el video.</span>
                  <span v-else-if="!canContinueAfterVideo" class="font-bold text-white">Reproduce el video hasta acumular al menos 10 segundos.</span>
                  <span v-else class="font-bold text-white">Video completado. Ya puedes continuar.</span>
                </p>
                <div class="flex flex-col gap-3 sm:flex-row">
                  <button
                    v-if="videoDone && !canContinueAfterVideo"
                    type="button"
                    class="page-control min-h-12 rounded-[var(--radius-control)] border border-white/50 px-5 py-3 text-sm font-semibold text-white [@media(hover:hover)_and_(pointer:fine)]:hover:bg-white/10"
                    @click="replayVideo"
                  >
                    Reproducir nuevamente
                  </button>
                  <button type="button" :disabled="!canContinueAfterVideo || loading || questions.length === 0" class="page-control min-h-12 rounded-[var(--radius-control)] bg-white px-6 py-3 text-sm font-semibold text-[#202020] [@media(hover:hover)_and_(pointer:fine)]:hover:bg-[#eeeeed] disabled:cursor-not-allowed disabled:opacity-50" @click="start">
                    {{ loading ? 'Preparando evaluación…' : questions.length ? 'Contestar evaluación' : 'Cuestionario pendiente' }}
                  </button>
                </div>
              </div>
            </main>
          </div>
        </div>
      </Transition>

      <section v-if="stage === 'exam'" class="mx-auto max-w-4xl">
        <header class="rounded-[var(--radius-card)] border border-[var(--color-line)] bg-[var(--color-surface)] p-4 shadow-[var(--shadow-card)] sm:p-6">
          <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div class="min-w-0 flex-1">
              <p class="text-sm font-semibold text-[var(--color-accent)]">Módulo {{ moduleId }} · Evaluación</p>
              <h1 class="mt-1 max-w-2xl text-lg font-bold leading-6 text-[var(--color-brand-950)] sm:text-xl">{{ names[moduleId] }}</h1>
            </div>
            <p class="self-start shrink-0 rounded-lg bg-[var(--color-paper)] px-3 py-2 text-sm font-semibold tabular-nums text-[var(--color-brand-900)]">Pregunta {{ current + 1 }} de {{ questions.length }}</p>
          </div>
          <div class="mt-5 flex flex-wrap items-center justify-between gap-2 text-sm">
            <span class="font-medium text-[var(--color-brand-900)]">{{ answeredCount }} de {{ questions.length }} contestadas</span>
            <span class="text-[var(--color-muted)]">Avance: {{ Math.round(progress) }}%</span>
          </div>
          <div class="mt-2 h-2.5 overflow-hidden rounded-full bg-[var(--color-brand-100)]" role="progressbar" :aria-valuenow="answeredCount" aria-valuemin="0" :aria-valuemax="questions.length" :aria-valuetext="`${answeredCount} de ${questions.length} preguntas contestadas`" aria-label="Avance de la evaluación">
            <div class="h-full rounded-full bg-[var(--color-accent)] transition-[width] duration-200" :style="{ width: progress + '%' }" />
          </div>
        </header>

        <article v-if="q" class="mt-4 rounded-[var(--radius-card)] border border-[var(--color-line)] bg-[var(--color-surface)] p-5 shadow-[var(--shadow-card)] sm:mt-6 sm:p-8 lg:p-10">
          <div class="flex items-start gap-3 sm:gap-4">
            <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[var(--color-brand-900)] text-sm font-bold tabular-nums text-white" aria-hidden="true">{{ current + 1 }}</span>
            <h2 class="min-w-0 pt-1 text-lg font-semibold leading-7 text-[var(--color-brand-950)] sm:text-xl sm:leading-8">{{ q.text }}</h2>
          </div>

          <fieldset class="mt-6 space-y-3 sm:mt-8" :aria-busy="savingAnswer">
            <legend class="sr-only">Selecciona una respuesta</legend>
            <button
              v-for="option in q.options"
              :key="option.id"
              type="button"
              :disabled="savingAnswer"
              :aria-pressed="answers[q.id] === option.id"
              class="exam-option page-control flex min-h-14 w-full items-start gap-3 rounded-xl border p-4 text-left text-base leading-6 disabled:cursor-wait disabled:opacity-60 sm:gap-4"
              :class="answers[q.id] === option.id ? 'exam-option--selected' : 'exam-option--idle'"
              @click="selectOption(option.id)"
            >
              <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border text-sm font-semibold" :class="answers[q.id] === option.id ? 'border-[var(--color-brand-900)] bg-[var(--color-brand-900)] text-white' : 'border-[var(--color-brand-700)] bg-white text-[var(--color-brand-900)]'">
                {{ option.letter.toUpperCase() }}
              </span>
              <span class="min-w-0 flex-1 pt-0.5 text-[var(--color-brand-950)]">{{ option.text }}</span>
              <CheckCircle2 v-if="answers[q.id] === option.id" aria-hidden="true" class="mt-1 shrink-0 text-[var(--color-success)]" :size="18" />
            </button>
          </fieldset>

          <p v-if="savingAnswer" role="status" aria-live="polite" class="mt-4 text-sm font-medium text-[var(--color-accent)]">Guardando respuesta…</p>
        </article>

        <nav v-if="questions.length" aria-label="Navegación de preguntas" class="mt-4 flex flex-col gap-4 sm:mt-5">
          <div role="group" aria-label="Ir a una pregunta" class="flex flex-wrap items-center justify-center gap-2">
            <button
              v-for="(item, index) in questions"
              :key="item.id"
              type="button"
              :disabled="index > maxReachableIndex || savingAnswer || savingProgress"
              :aria-label="`Pregunta ${index + 1}${answers[item.id] != null ? ', contestada' : ', pendiente'}`"
              :aria-current="index === current ? 'step' : undefined"
              class="question-index min-h-11 min-w-11 rounded-[var(--radius-control)] border px-2 text-sm font-semibold tabular-nums disabled:cursor-not-allowed disabled:opacity-50"
              :class="index === current ? 'question-index--current' : answers[item.id] != null ? 'question-index--answered' : 'question-index--pending'"
              @click="goToQuestion(index)"
            >{{ index + 1 }}</button>
          </div>

          <div class="flex flex-col-reverse gap-3 border-t border-[var(--color-line)] pt-4 sm:flex-row sm:items-center sm:justify-between">
            <button type="button" :disabled="current === 0 || savingAnswer || savingProgress" aria-label="Pregunta anterior" class="page-control inline-flex min-h-11 items-center justify-center gap-2 rounded-[var(--radius-control)] border border-[var(--color-brand-700)] bg-[var(--color-surface)] px-4 py-2 text-sm font-semibold text-[var(--color-brand-900)] disabled:cursor-not-allowed disabled:opacity-50 [@media(hover:hover)_and_(pointer:fine)]:hover:bg-[var(--color-brand-100)]" @click="previous">
              <ChevronLeft :size="18" aria-hidden="true" /> Anterior
            </button>

            <button v-if="canNext" type="button" :disabled="savingAnswer || savingProgress" class="page-control inline-flex min-h-11 items-center justify-center gap-2 rounded-[var(--radius-control)] bg-[var(--color-brand-900)] px-5 py-2 text-sm font-semibold text-white [@media(hover:hover)_and_(pointer:fine)]:hover:bg-[var(--color-brand-800)] disabled:cursor-wait disabled:opacity-50" @click="next">
              Siguiente pregunta <ChevronRight :size="18" aria-hidden="true" />
            </button>
            <button v-else-if="allAnswered && current === maxReachableIndex" type="button" :disabled="loading || savingAnswer || savingProgress" aria-label="Finalizar evaluación" class="page-control inline-flex min-h-11 items-center justify-center gap-2 rounded-[var(--radius-control)] bg-[var(--color-brand-900)] px-5 py-2 text-sm font-semibold text-white [@media(hover:hover)_and_(pointer:fine)]:hover:bg-[var(--color-brand-800)] disabled:cursor-wait disabled:opacity-50" @click="finish">
              {{ loading ? 'Finalizando…' : 'Finalizar' }} <CheckCircle2 :size="18" aria-hidden="true" />
            </button>
            <span v-else class="text-center text-sm text-[var(--color-muted)] sm:text-right">Selecciona una respuesta para avanzar.</span>
          </div>
        </nav>
      </section>

      <EvaluationResult
        v-if="stage === 'result'"
        :module-id="moduleId"
        :module-name="names[moduleId]"
        :score="result.score"
        :correct="result.correct"
        :total="result.total"
        :attempt="result.attempt"
        :attempts-remaining="Math.max(0, 3 - result.attempt)"
        :message="message"
        @retry="retry"
        @back="emit('back')"
      />
    </main>

    <ConfirmDialog
      v-if="showFinishConfirmation"
      title="¿Finalizar evaluación?"
      description="Al finalizar, tus respuestas quedarán registradas y ya no podrás modificarlas. Revisa que todas estén contestadas antes de continuar."
      confirm-label="Finalizar evaluación"
      :busy="loading"
      @cancel="showFinishConfirmation = false"
      @confirm="finishConfirmed"
    />

    <footer class="mx-auto max-w-6xl px-4 pb-8 text-center text-xs text-[var(--color-muted)] sm:px-6 lg:px-8">
      Fiscalía General de Justicia
      del Estado de Tamaulipas
      ·
      Fiscalía Especializada
      en Delitos Electorales
    </footer>
  </div>
</template>

<style scoped>
.exam-option,
.question-index {
  transition: background-color var(--motion-fast) var(--ease-out), border-color var(--motion-fast) var(--ease-out), color var(--motion-fast) var(--ease-out), box-shadow var(--motion-fast) var(--ease-out);
}

.exam-option--idle { border-color: var(--color-brand-700); background: var(--color-surface); }
.exam-option--selected { border-color: var(--color-accent); background: var(--color-accent-soft); box-shadow: inset 0 0 0 1px var(--color-accent); }
.question-index--current { border-color: var(--color-brand-900); background: var(--color-brand-900); color: #fff; }
.question-index--answered { border-color: var(--color-brand-700); background: var(--color-brand-100); color: var(--color-brand-900); }
.question-index--pending { border-color: var(--color-brand-700); background: var(--color-surface); color: var(--color-brand-900); }

@media (hover: hover) and (pointer: fine) {
  .exam-option--idle:hover { border-color: var(--color-brand-700); background: var(--color-paper); }
  .question-index--pending:hover { border-color: var(--color-brand-700); background: var(--color-paper); }
}

@media (prefers-reduced-motion: reduce) {
  .exam-option, .question-index { transition: none; }
}
</style>
