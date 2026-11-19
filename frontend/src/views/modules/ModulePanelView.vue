<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { ArrowRight, BookOpen, CheckCircle2 } from 'lucide-vue-next';
import { useAuth } from '../../services/auth';
import InstitutionalHeader from '../../components/layout/InstitutionalHeader.vue';
import BaseAlert from '../../components/ui/BaseAlert.vue';

type ModuleStatus = {
  module_id: number;
  name: string;
  attempts: number;
  attempts_remaining: number;
  best_score: number | null;
  passed: boolean;
  in_progress: boolean;
  questions_available: boolean;
  certificate: { id: number; score: number; issued_at: string } | null;
};

const emit = defineEmits<{
  (e: 'select-module', moduleId: number): void;
  (e: 'back-login'): void;
}>();

const { apiFetch, logout, fullName } = useAuth();
const modules = ref<ModuleStatus[]>([]);
const loading = ref(true);
const error = ref('');

const titles = [
  'Nociones básicas de derecho electoral',
  'Delitos Electorales y su investigación en el Contexto de los Procesos Electorales Locales',
  'Integración de la carpeta de investigación, primer respondiente, retos en la investigación y cultura de prevención',
];

async function loadStatus() {
  loading.value = true;
  error.value = '';
  try {
    const response = await apiFetch('/api/modules/status');
    const data = await response.json().catch(() => null);
    if (!response.ok) throw new Error(data?.detail || 'No se pudo consultar el estado de tus módulos.');
    modules.value = Array.isArray(data?.modules) ? data.modules : [];
  } catch (e: any) {
    error.value = e?.message || 'No fue posible conectar con el servidor.';
  } finally {
    loading.value = false;
  }
}

function titleFor(moduleId: number) {
  return titles[moduleId - 1] ?? '';
}

onMounted(loadStatus);
</script>

<template>
  <div class="min-h-screen bg-[var(--color-paper)] text-[var(--color-ink)]">
    <InstitutionalHeader :show-logout="true" @logout="logout" />

    <main id="main-content" tabindex="-1" class="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-12 lg:px-8">
      <header class="max-w-3xl">
        <p class="text-sm font-semibold text-[var(--color-accent)]">Capacitación institucional</p>
        <h1 class="mt-2 text-3xl font-bold leading-tight tracking-tight text-[var(--color-brand-950)] sm:text-4xl">Bienvenido, {{ fullName }}</h1>
        <p class="mt-4 text-base leading-7 text-[var(--color-muted)]">Selecciona un módulo para continuar tu capacitación. La calificación mínima para acreditar es de <strong class="font-semibold text-[var(--color-brand-900)]">70 de 100 puntos</strong>.</p>
      </header>

      <BaseAlert v-if="error" class="mt-6" variant="destructive" title="No se pudieron cargar tus módulos" :description="error">
        <template #action><button type="button" class="page-control min-h-11 rounded-[var(--radius-control)] border border-[var(--color-brand-700)] bg-[var(--color-surface)] px-4 py-2 text-sm font-semibold text-[var(--color-brand-900)] [@media(hover:hover)_and_(pointer:fine)]:hover:bg-[var(--color-brand-100)]" @click="loadStatus">Reintentar</button></template>
      </BaseAlert>

      <section class="mt-8 sm:mt-10" aria-labelledby="modules-heading" :aria-busy="loading">
        <div class="mb-4 flex flex-wrap items-end justify-between gap-2">
          <h2 id="modules-heading" class="text-xl font-bold text-[var(--color-brand-950)] sm:text-2xl">Tus módulos</h2>
          <p class="text-sm text-[var(--color-muted)]">{{ loading ? 'Consultando avance…' : `${modules.length} ${modules.length === 1 ? 'módulo disponible' : 'módulos disponibles'}` }}</p>
        </div>

      <div class="grid grid-cols-1 items-stretch gap-4 sm:grid-cols-2 sm:gap-5 lg:grid-cols-3">
        <template v-if="loading">
          <div v-for="moduleId in [1, 2, 3]" :key="moduleId" aria-hidden="true" class="min-h-64 rounded-[var(--radius-card)] border border-[var(--color-line)] bg-[var(--color-surface)] p-6 shadow-[var(--shadow-card)]">
            <div class="h-11 w-11 rounded-xl bg-[var(--color-brand-100)]" />
            <div class="mt-7 h-3 w-20 rounded bg-[var(--color-brand-100)]" />
            <div class="mt-3 h-5 w-4/5 rounded bg-[var(--color-brand-100)]" />
            <div class="mt-2 h-5 w-3/5 rounded bg-[var(--color-brand-100)]" />
            <div class="mt-10 h-px bg-[var(--color-line)]" />
          </div>
        </template>
        <div v-if="!loading && !error && !modules.length" class="rounded-[var(--radius-card)] border border-[var(--color-line)] bg-[var(--color-surface)] p-6 text-base leading-7 text-[var(--color-muted)] sm:col-span-2 sm:p-8 lg:col-span-3">
          <h3 class="font-semibold text-[var(--color-brand-900)]">No hay módulos disponibles</h3>
          <p class="mt-1">No encontramos módulos para tu cuenta en este momento. Puedes volver a consultar el estado.</p>
          <button type="button" class="page-control mt-4 min-h-11 rounded-[var(--radius-control)] border border-[var(--color-brand-700)] px-4 py-2 text-sm font-semibold text-[var(--color-brand-900)] [@media(hover:hover)_and_(pointer:fine)]:hover:bg-[var(--color-brand-100)]" @click="loadStatus">Actualizar módulos</button>
        </div>
        <article
          v-for="module in modules"
          :key="module.module_id"
          class="module-card min-h-64 rounded-[var(--radius-card)] border border-[var(--color-line)] bg-[var(--color-surface)] shadow-[var(--shadow-card)]"
        >
          <div class="flex h-full min-h-64 flex-col p-5 sm:p-6">
            <div class="flex items-center justify-between gap-3">
              <span class="flex h-11 w-11 items-center justify-center rounded-xl bg-[var(--color-brand-900)] text-sm font-bold text-white">{{ String(module.module_id).padStart(2, '0') }}</span>
              <span v-if="module.passed" class="inline-flex items-center gap-1.5 rounded-full bg-[var(--color-success-soft)] px-3 py-1.5 text-xs font-semibold text-[var(--color-success)]">
                <CheckCircle2 :size="16" aria-hidden="true" /> Acreditado
              </span>
              <span v-else-if="module.in_progress" class="inline-flex items-center gap-1.5 rounded-full bg-[var(--color-accent-soft)] px-3 py-1.5 text-xs font-semibold text-[var(--color-accent)]">
                <BookOpen :size="16" aria-hidden="true" /> En curso
              </span>
              <BookOpen v-else :size="19" class="text-[var(--color-brand-700)]" aria-hidden="true" />
            </div>
            <p class="mt-6 text-sm font-semibold text-[var(--color-muted)]">Módulo {{ module.module_id }}</p>
            <h3 class="mt-2 text-lg font-bold leading-6 text-[var(--color-brand-950)]">{{ titleFor(module.module_id) }}</h3>
            <div class="mt-auto border-t border-[var(--color-line)] pt-4 text-sm leading-5">
              <template v-if="module.passed">
                <p class="font-semibold text-[var(--color-success)]">Calificación: {{ module.best_score }}/100</p>
                <p class="mt-1 text-[var(--color-muted)]">Constancia disponible</p>
              </template>
              <template v-else-if="module.in_progress">
                <p class="font-semibold text-[var(--color-accent)]">Evaluación en curso</p>
                <p class="mt-1 text-[var(--color-muted)]">Continúa donde te quedaste</p>
              </template>
              <template v-else>
                <p class="text-[var(--color-muted)]">{{ module.attempts ?? 0 }} de 3 intentos usados</p>
              </template>
              <button type="button" class="module-card__action page-control mt-3 inline-flex min-h-11 w-full items-center justify-between gap-2 rounded-[var(--radius-control)] border border-[var(--color-brand-700)] px-3 font-semibold text-[var(--color-brand-900)] [@media(hover:hover)_and_(pointer:fine)]:hover:bg-[var(--color-brand-100)] disabled:cursor-not-allowed disabled:opacity-50" :disabled="loading" @click="emit('select-module', module.module_id)">
                {{ module.passed ? 'Consultar módulo' : module.in_progress ? 'Continuar evaluación' : 'Iniciar módulo' }}
                <ArrowRight :size="16" aria-hidden="true" />
              </button>
            </div>
          </div>
        </article>
      </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
@media (prefers-reduced-motion: reduce) {
  .module-card__action { transition: none; }
}
</style>
