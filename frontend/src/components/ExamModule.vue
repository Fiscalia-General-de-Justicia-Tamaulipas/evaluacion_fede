<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { ArrowLeft, CheckCircle2, LockKeyhole, PlayCircle, RotateCcw, X } from 'lucide-vue-next';
import { useAuth } from '../lib/auth';

const props = defineProps<{ moduleId: number }>();
const emit = defineEmits<{ (e: 'back'): void }>();
const { apiFetch, fullName } = useAuth();

type Option = { id: number; letter: string; text: string };
type Question = { id: number; number: number; text: string; options: Option[] };

const names: Record<number, string> = {
  1: 'Nociones básicas de derecho electoral',
  2: 'Delitos Electorales y su investigación en el Contexto de los Procesos Electorales Locales',
  3: 'Integración de la carpeta de investigación, primer respondiente, retos en la investigación y cultura de prevención',
};

const introTitles: Record<number, string> = {
  1: 'Nociones básicas de derecho electoral.',
  2: 'Delitos Electorales y su investigación en el Contexto de los Procesos Electorales Locales.',
  3: 'Integración de la carpeta de investigación, primer respondiente, retos en la investigación y cultura de prevención.',
};

const stage = ref<'intro' | 'exam' | 'result'>('intro');
const questions = ref<Question[]>([]);
const current = ref(0);
const answers = ref<Record<number, number>>({});
const evaluationId = ref<number | null>(null);
const videoDone = ref(false);
const loading = ref(false);
const message = ref('');
const videoModalOpen = ref(false);
const modalVideoRef = ref<HTMLVideoElement | null>(null);
const result = ref({ score: 0, correct: 0, total: 0, passed: false, attempt: 1, certificateId: null as number | null });

const q = computed(() => questions.value[current.value]);
const allAnswered = computed(() => questions.value.length > 0 && questions.value.every(question => answers.value[question.id] != null));
const progress = computed(() => questions.value.length ? (Object.keys(answers.value).length / questions.value.length) * 100 : 0);

function openVideoModal() {
  videoModalOpen.value = true;
  document.body.style.overflow = 'hidden';
}

function closeVideoModal() {
  videoModalOpen.value = false;
  modalVideoRef.value?.pause();
  document.body.style.overflow = '';
}

function handleEscape(event: KeyboardEvent) {
  if (event.key === 'Escape') closeVideoModal();
}

async function loadQuestions() {
  const response = await apiFetch(`/api/questions?module_id=${props.moduleId}`);
  if (response.ok) questions.value = await response.json();
}

function applyOrder(order: number[]) {
  const byId = new Map(questions.value.map(question => [question.id, question]));
  const ordered = order.map(id => byId.get(id)).filter((item): item is Question => !!item);
  questions.value = [...ordered, ...questions.value.filter(question => !order.includes(question.id))];
}

async function restore() {
  await loadQuestions();
  const response = await apiFetch(`/api/evaluations/current?module_id=${props.moduleId}`);
  if (!response.ok) return;
  const data = await response.json();
  if (!data.has_evaluation || !data.evaluation) return;
  evaluationId.value = data.evaluation.id;
  videoDone.value = data.evaluation.video_completed;
  for (const answer of data.evaluation.answers ?? []) answers.value[answer.question_id] = answer.option_id;
  applyOrder(data.evaluation.question_order ?? []);
  if (videoDone.value) stage.value = 'exam';
}

async function start() {
  if (!videoDone.value || loading.value) return;
  loading.value = true;
  message.value = '';
  try {
    const response = await apiFetch(`/api/evaluations/start?module_id=${props.moduleId}`, {
      method: 'POST',
    });
    if (!response.ok) {
      const data = await response.json().catch(() => null);
      throw new Error(data?.detail || 'No se pudo iniciar la evaluación.');
    } else {
      await applyStart(await response.json());
    }
  } catch (error: any) {
    message.value = error.message;
  } finally {
    loading.value = false;
  }
}

async function applyStart(data: any) {
  evaluationId.value = data.evaluation_id;
  for (const answer of data.answers ?? []) answers.value[answer.question_id] = answer.option_id;
  applyOrder(data.question_order ?? []);
  if (!data.video_completed) {
    await apiFetch(`/api/evaluations/${evaluationId.value}/video-completed`, { method: 'POST' });
  }
  closeVideoModal();
  stage.value = 'exam';
  videoDone.value = true;
}

async function selectOption(optionId: number) {
  if (!q.value || !evaluationId.value) return;
  const questionId = q.value.id;
  answers.value[questionId] = optionId;
  const response = await apiFetch(`/api/evaluations/${evaluationId.value}/answers`, {
    method: 'PUT',
    body: JSON.stringify({ question_id: questionId, option_id: optionId }),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    message.value = data?.detail || 'No se pudo guardar la respuesta.';
    delete answers.value[questionId];
  }
}

async function finish() {
  if (!allAnswered.value || !evaluationId.value || loading.value) return;
  loading.value = true;
  try {
    const response = await apiFetch(`/api/evaluations/${evaluationId.value}/finish`, {
      method: 'POST',
      body: JSON.stringify({ answers: [] }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'No se pudo finalizar la evaluación.');
    result.value = {
      score: data.score,
      correct: data.correct,
      total: data.total,
      passed: data.passed,
      attempt: data.attempt_number,
      certificateId: data.certificate_id,
    };
    stage.value = 'result';
  } catch (error: any) {
    message.value = error.message;
  } finally {
    loading.value = false;
  }
}

async function openCertificate() {
  const response = await apiFetch(`/api/certificates/${props.moduleId}`);
  if (!response.ok) return;
  const data = await response.json();
  const certificateWindow = window.open('', '_blank', 'width=900,height=700');
  if (!certificateWindow) return;
  certificateWindow.document.write(`
    <html><head><title>Constancia - Módulo ${data.module_id}</title></head>
    <body style="font-family:Arial,sans-serif;color:#292928;padding:60px;text-align:center">
      <h1>CONSTANCIA DE APROBACIÓN</h1>
      <p>Se hace constar que</p><h2>${fullName.value}</h2>
      <p>aprobó el Módulo ${data.module_id}: <strong>${data.module_name}</strong></p>
      <p>Calificación: <strong>${data.score}/10</strong></p>
      <p>Fecha de expedición: ${new Date(data.issued_at).toLocaleDateString('es-MX')}</p>
      <script>window.onload=()=>window.print()<\/script>
    </body></html>`);
  certificateWindow.document.close();
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
  <div class="min-h-screen bg-[#f5f5f5] text-[#292928]">
    <header class="border-b border-[#dadada] bg-white px-5 py-4">
      <div class="mx-auto flex max-w-5xl items-center gap-3">
        <button type="button" class="inline-flex h-10 items-center gap-2 rounded-lg border border-[#dadada] px-3 text-sm font-bold text-[#575756] hover:bg-[#f0f0ef]" @click="emit('back')">
          <ArrowLeft :size="17" /> Regresar
        </button>
        <p class="ml-auto text-sm font-bold text-[#878787]">Módulo {{ moduleId }}</p>
      </div>
    </header>

    <main class="mx-auto max-w-6xl px-5 py-8 md:py-6">
      <section v-if="stage === 'intro'" class="flex flex-col items-center">
        <div class="mx-auto max-w-4xl text-center">
          <span class="inline-flex items-center gap-2 rounded-full bg-[#dadada]/60 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-[#575756]">
            <PlayCircle :size="14" />
            Material introductorio
          </span>

          <h1 class="mt-5 max-w-4xl text-4xl font-black leading-tight tracking-tight md:text-5xl lg:text-4xl">
            Delitos Electorales y su investigación
            en el contexto de los Procesos Electorales
            Locales.
          </h1>

          <p class="mx-auto mt-5 max-w-3xl text-base leading-7 text-[#878787] md:text-lg">
            Visualiza el material completo antes de acceder a la evaluación del
            <br />
            <b>Módulo {{ moduleId }}: {{ introTitles[moduleId] }}</b>
          </p>

          <div class="mt-7 flex items-center justify-center gap-3 text-sm text-[#878787]">
            <LockKeyhole :size="17" />
            <span v-if="!videoDone">La evaluación se habilita al concluir el video.</span>
            <span v-else class="font-bold text-[#575756]">Video completado. Ya puedes continuar con la evaluación.</span>
          </div>

          <button type="button" class="mt-8 inline-flex items-center gap-3 rounded-2xl bg-[#575756] px-8 py-4 text-base font-black text-white shadow-xl shadow-black/10 transition hover:-translate-y-0.5 hover:bg-[#454544] hover:shadow-2xl focus:outline-none focus:ring-2 focus:ring-[#575756] focus:ring-offset-4" aria-label="Ver video de capacitación" @click="openVideoModal">
            <PlayCircle :size="23" />
            Ver video
          </button>
        </div>
      </section>

      <Transition name="fade">
        <div v-if="videoModalOpen && stage === 'intro'" class="fixed inset-0 z-[9999] flex min-h-screen flex-col overflow-y-auto bg-[#20201f] text-white" role="dialog" aria-modal="true" aria-labelledby="video-modal-title" @click.self="closeVideoModal">
          <div class="flex min-h-screen w-full flex-col">
            <header class="border-b border-white/10 bg-[#292928] px-5 py-4 md:px-10">
              <div class="mx-auto flex max-w-7xl items-center gap-4">
                <button type="button" title="Regresar al panel de módulos" aria-label="Regresar al panel de módulos" class="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-white/15 text-white/75 transition hover:bg-white/10 hover:text-white" @click="emit('back')">
                  <ArrowLeft :size="20" />
                </button>
                <img src="/logo_fgjtam.png" alt="Logo Fiscalía General de Justicia de Tamaulipas" class="h-12 w-auto object-contain md:h-16" />
                <div class="h-10 w-px bg-white/20 md:h-12" />
                <img src="/logo_fede.png" alt="Logo Fiscalía Especializada en Delitos Electorales" class="h-12 w-auto object-contain md:h-16" />
                <div class="ml-auto min-w-0 pr-10">
                  <p class="truncate text-xs font-bold uppercase tracking-[0.18em] text-white/55">Material introductorio</p>
                  <h2 id="video-modal-title" class="mt-1 text-sm font-black text-white md:text-lg">Delitos Electorales y su investigación</h2>
                </div>
                <button type="button" title="Cerrar video" aria-label="Cerrar video" class="absolute right-5 top-5 inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-white/65 transition hover:bg-white/10 hover:text-white md:right-10" @click="closeVideoModal">
                  <X :size="20" />
                </button>
              </div>
            </header>

            <main class="flex flex-1 flex-col items-center justify-center px-4 py-8 md:px-10 md:py-12">
              <div class="mb-6 text-center md:mb-8">
                <p class="text-2xl font-black md:text-4xl">Módulo {{ moduleId }}: {{ names[moduleId] }}</p>
                <p class="mt-2 text-sm text-white/60 md:text-base">Reproduce el video completo antes de contestar la evaluación.</p>
              </div>

              <div class="w-full max-w-6xl overflow-hidden rounded-2xl border border-white/10 bg-black shadow-2xl md:rounded-3xl">
                <video ref="modalVideoRef" class="mx-auto block max-h-[68vh] w-full object-contain" controls autoplay playsinline preload="metadata" @ended="videoDone = true">
                  <source :src="`/curso-modulo${moduleId}.mp4`" type="video/mp4" />
                  Tu navegador no soporta video HTML5.
                </video>
              </div>

              <div class="mt-6 flex w-full max-w-6xl flex-col items-center justify-between gap-4 border-t border-white/10 pt-6 sm:flex-row">
                <p class="text-sm text-white/60">
                  <span v-if="!videoDone">La evaluación se habilita al terminar el video.</span>
                  <span v-else class="font-bold text-white">Video completado. Ya puedes continuar.</span>
                </p>
                <button type="button" :disabled="!videoDone || loading || questions.length === 0" class="rounded-xl bg-white px-6 py-3 text-sm font-black text-[#292928] transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-40" @click="start">
                  {{ loading ? 'Preparando evaluación…' : questions.length ? 'Contestar evaluación' : 'Cuestionario pendiente' }}
                </button>
              </div>
            </main>
          </div>
        </div>
      </Transition>

      <section v-if="stage === 'exam'" class="rounded-3xl border border-[#dadada] bg-white p-6 shadow-sm md:p-10">
        <div class="flex items-end justify-between">
          <div><p class="text-xs font-bold uppercase tracking-widest text-[#878787]">Módulo {{ moduleId }}</p><h1 class="mt-2 text-xl font-black">{{ names[moduleId] }}</h1></div>
          <p class="text-sm font-bold">{{ current + 1 }} / {{ questions.length }}</p>
        </div>
        <div class="mt-5 h-2 overflow-hidden rounded-full bg-[#e5e5e5]"><div class="h-full rounded-full bg-[#575756]" :style="{ width: progress + '%' }" /></div>
        <article v-if="q" class="mt-8">
          <h2 class="text-xl font-bold leading-8">{{ q.text }}</h2>
          <div class="mt-7 space-y-3">
            <button v-for="option in q.options" :key="option.id" type="button" class="flex w-full items-start gap-4 rounded-xl border p-4 text-left transition hover:border-[#878787] hover:bg-[#fafafa]" :class="answers[q.id] === option.id ? 'border-[#575756] bg-[#f0f0ef]' : 'border-[#dadada]'" @click="selectOption(option.id)">
              <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border text-sm font-black" :class="answers[q.id] === option.id ? 'border-[#575756] bg-[#575756] text-white' : 'border-[#dadada] text-[#878787]'">{{ option.letter }}</span>
              <span class="pt-1 leading-6">{{ option.text }}</span>
              <CheckCircle2 v-if="answers[q.id] === option.id" :size="20" class="ml-auto mt-1 shrink-0" />
            </button>
          </div>
          <p v-if="message" class="mt-4 text-sm font-bold text-[#575756]">{{ message }}</p>
          <div class="mt-8 flex items-center justify-between">
            <button type="button" class="rounded-xl border border-[#dadada] px-4 py-3 text-sm font-bold disabled:opacity-40" :disabled="current === 0" @click="current--">Anterior</button>
            <button v-if="current < questions.length - 1" type="button" class="rounded-xl bg-[#575756] px-5 py-3 text-sm font-bold text-white disabled:opacity-40" :disabled="answers[q.id] == null" @click="current++">Siguiente</button>
            <button v-else type="button" class="rounded-xl bg-[#575756] px-5 py-3 text-sm font-bold text-white disabled:opacity-40" :disabled="!allAnswered || loading" @click="finish">Finalizar</button>
          </div>
        </article>
      </section>

      <section v-if="stage === 'result'" class="rounded-3xl border border-[#dadada] bg-white p-8 text-center shadow-sm md:p-12">
        <p class="text-xs font-bold uppercase tracking-widest text-[#878787]">Resultado · Intento {{ result.attempt }}</p>
        <h1 class="mt-3 text-3xl font-black">{{ result.passed ? '¡Módulo aprobado!' : 'Evaluación registrada' }}</h1>
        <div class="mx-auto mt-8 grid max-w-lg grid-cols-3 gap-3">
          <div class="rounded-xl border border-[#dadada] p-4"><p class="text-2xl font-black">{{ result.score }}/10</p><p class="mt-1 text-xs text-[#878787]">Calificación</p></div>
          <div class="rounded-xl border border-[#dadada] p-4"><p class="text-2xl font-black">{{ result.correct }}</p><p class="mt-1 text-xs text-[#878787]">Correctas</p></div>
          <div class="rounded-xl border border-[#dadada] p-4"><p class="text-2xl font-black">{{ result.total }}</p><p class="mt-1 text-xs text-[#878787]">Preguntas</p></div>
        </div>
        <p v-if="!result.passed" class="mt-6 text-sm leading-6 text-[#878787]">Necesitas una calificación mínima de 7. Puedes realizar hasta 3 intentos.</p>
        <div class="mt-8 flex flex-wrap justify-center gap-3">
          <button v-if="result.passed" type="button" class="rounded-xl bg-[#575756] px-5 py-3 text-sm font-black text-white hover:bg-[#454544]" @click="openCertificate">Ver constancia</button>
          <button type="button" class="inline-flex items-center gap-2 rounded-xl border border-[#dadada] px-5 py-3 text-sm font-bold hover:bg-[#f0f0ef]" @click="emit('back')"><RotateCcw :size="17" /> Volver al panel</button>
        </div>
      </section>
    </main>

    <footer class="mx-auto max-w-6xl px-5 pb-8 text-center text-xs text-[#878787]">
      Fiscalía General de Justicia
      del Estado de Tamaulipas
      ·
      Fiscalía Especializada
      en Delitos Electorales
    </footer>
  </div>
</template>
