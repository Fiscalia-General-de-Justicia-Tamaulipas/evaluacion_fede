<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { ArrowRight, BookOpen, CheckCircle2 } from 'lucide-vue-next';
import InstitutionalHeader from '../../components/layout/InstitutionalHeader.vue';
import BaseAlert from '../../components/ui/BaseAlert.vue';
import { useAuth } from '../../services/auth';

type ModuleStatus = {
  module_id: number;
  passed: boolean;
};

const emit = defineEmits<{ (event: 'select-course'): void }>();
const { apiFetch, fullName, logout } = useAuth();
const modules = ref<ModuleStatus[]>([]);
const loading = ref(true);
const error = ref('');

const courses = [{
  key: 'delitos-electorales-investigacion-sistema-electoral-mexicano',
  title: 'Delitos Electorales y su investigación en el Sistema Electoral Mexicano',
  description: 'Capacitación sobre el marco electoral, la investigación de delitos y la cultura de prevención.',
  moduleIds: [1, 2, 3],
}];

function completedModules(course: (typeof courses)[number]) {
  return course.moduleIds.filter(moduleId => modules.value.some(module => module.module_id === moduleId && module.passed)).length;
}

function courseProgress(course: (typeof courses)[number]) {
  return Math.round((completedModules(course) / course.moduleIds.length) * 100);
}

async function loadStatus() {
  loading.value = true;
  error.value = '';
  try {
    const response = await apiFetch('/api/modules/status');
    const data = await response.json().catch(() => null);
    if (!response.ok) throw new Error(data?.detail || 'No se pudo consultar el avance de los cursos.');
    modules.value = Array.isArray(data?.modules) ? data.modules : [];
  } catch (cause: unknown) {
    error.value = cause instanceof Error ? cause.message : 'No fue posible conectar con el servidor.';
  } finally {
    loading.value = false;
  }
}

onMounted(loadStatus);
</script>

<template>
  <div class="course-catalog-page relative isolate min-h-dvh overflow-x-clip bg-[var(--color-paper)] text-[var(--color-ink)]">
  <InstitutionalHeader class="relative z-20" :show-logout="true" :participant-name="fullName" @logout="logout" />

    <main id="main-content" tabindex="-1" class="relative z-10 mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-12 lg:px-8">
      <header class="course-catalog-intro max-w-3xl">
        <p class="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.15em] text-[var(--color-muted)]">
          <span aria-hidden="true" class="h-px w-7 bg-[var(--color-brand-900)]" />
          Capacitación institucional
        </p>
        <h1 class="mt-3 text-3xl font-bold leading-tight tracking-tight text-[var(--color-brand-950)] sm:text-4xl">Cursos disponibles</h1>
        <p class="mt-3 max-w-2xl text-base leading-7 text-[var(--color-muted)]">Hola, {{ fullName }}. Elige un curso para consultar sus módulos y continuar tu capacitación.</p>
      </header>

      <BaseAlert v-if="error" class="mt-6" variant="destructive" title="No se pudo consultar tu avance" :description="error">
        <template #action>
          <button type="button" class="page-control min-h-11 rounded-[var(--radius-control)] border border-[var(--color-brand-700)] bg-[var(--color-surface)] px-4 py-2 text-sm font-semibold text-[var(--color-brand-900)] hover:bg-[var(--color-brand-100)]" @click="loadStatus">Reintentar</button>
        </template>
      </BaseAlert>

      <section class="relative mt-8 sm:mt-10" aria-labelledby="courses-heading" :aria-busy="loading">
        <div class="mb-5 flex flex-wrap items-end justify-between gap-3 sm:mb-6">
          <div>
            <p class="text-xs font-bold uppercase tracking-[0.13em] text-[var(--color-muted)]">Formación profesional</p>
            <h2 id="courses-heading" class="mt-1 text-xl font-bold text-[var(--color-brand-950)] sm:text-2xl">Tu catálogo de cursos</h2>
          </div>
          <p class="rounded-full border border-[var(--color-line)] bg-[var(--color-surface)] px-3 py-1.5 text-xs font-semibold text-[var(--color-muted)]">
            {{ courses.length }} {{ courses.length === 1 ? 'curso disponible' : 'cursos disponibles' }}
          </p>
        </div>

        <div class="grid grid-cols-1 items-stretch gap-5 md:grid-cols-2 lg:grid-cols-3">
          <article v-for="course in courses" :key="course.key" class="course-card group flex h-full flex-col overflow-hidden rounded-[var(--radius-card)] border border-[var(--color-line)] bg-[var(--color-surface)] shadow-[var(--shadow-card)]">
            <div class="course-card__hero relative isolate flex h-36 items-end overflow-hidden bg-[var(--color-brand-100)] sm:h-40">
              <img class="course-card__hero-art absolute inset-0 h-full w-full object-cover" src="/course-justice-card.jpg" alt="" aria-hidden="true" />
              <div class="course-card__hero-wash absolute inset-0" aria-hidden="true" />
              <div class="relative z-10 flex w-full items-end justify-between gap-3 px-5 pb-4 sm:px-6">
                <p class="text-[0.68rem] font-bold uppercase tracking-[0.13em] text-[var(--color-brand-900)]">Capacitación · 3 módulos</p>
                <span v-if="!loading && completedModules(course) === course.moduleIds.length" class="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-[var(--color-success)]/20 bg-[var(--color-success-soft)] px-3 py-1.5 text-xs font-semibold text-[var(--color-success)]">
                  <CheckCircle2 :size="15" aria-hidden="true" /> Acreditado
                </span>
                <span v-else-if="!loading && completedModules(course) > 0" class="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-[var(--color-line)] bg-[var(--color-surface)]/90 px-3 py-1.5 text-xs font-semibold text-[var(--color-brand-900)]">
                  <BookOpen :size="14" aria-hidden="true" /> En progreso
                </span>
              </div>
            </div>

            <div class="flex flex-1 flex-col p-5 sm:p-6">
              <div class="flex items-start gap-3">
                <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-[var(--color-line)] bg-[var(--color-paper)] text-[var(--color-brand-900)]" aria-hidden="true">
                  <BookOpen :size="19" />
                </span>
                <div class="min-w-0">
                  <p class="text-xs font-semibold uppercase tracking-[0.1em] text-[var(--color-muted)]">Curso institucional</p>
                  <h3 class="mt-1 text-lg font-bold leading-6 text-[var(--color-brand-950)]">{{ course.title }}</h3>
                </div>
              </div>
              <p class="mt-3 text-sm leading-6 text-[var(--color-muted)]">{{ course.description }}</p>

              <div class="mt-auto pt-7">
                <div class="rounded-lg border border-[var(--color-line)] bg-[var(--color-paper)] p-4">
                  <div class="flex items-center justify-between gap-3">
                    <span class="text-xs font-semibold text-[var(--color-muted)]">{{ loading ? 'Consultando avance…' : `${completedModules(course)} de ${course.moduleIds.length} módulos acreditados` }}</span>
                    <span class="shrink-0 text-sm font-bold tabular-nums text-[var(--color-brand-900)]">{{ loading ? '—' : `${courseProgress(course)}%` }}</span>
                  </div>
                  <div class="mt-3 h-2 overflow-hidden rounded-full bg-[var(--color-line)]" role="progressbar" :aria-label="`Avance de ${course.title}`" :aria-valuenow="loading ? 0 : courseProgress(course)" aria-valuemin="0" aria-valuemax="100">
                    <div class="course-progress__value h-full rounded-full bg-[var(--color-brand-900)]" :style="{ width: `${loading ? 0 : courseProgress(course)}%` }" />
                  </div>
                </div>

                <button type="button" class="course-card__action page-control page-press mt-5 inline-flex min-h-12 w-full items-center justify-between gap-3 rounded-[var(--radius-control)] border border-[var(--color-brand-700)] bg-[var(--color-surface)] px-4 py-3 text-sm font-semibold text-[var(--color-brand-900)] hover:bg-[var(--color-brand-100)]" @click="emit('select-course')">
                  Cursar este curso
                  <ArrowRight :size="17" aria-hidden="true" />
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
.course-catalog-watermark {
  width: min(42rem, 76vw);
  transform: translate(-15%, 14%) rotate(-5deg);
  opacity: 0.13;
  mask-image: linear-gradient(135deg, #000 0%, #000 42%, transparent 92%);
}

.course-catalog-watermark img {
  display: block;
  width: 100%;
  height: auto;
}

.course-card {
  transition: transform 180ms var(--ease-out), border-color 180ms var(--ease-out), box-shadow 180ms var(--ease-out);
}

.course-card__hero-art {
  opacity: 0.9;
  mask-image: linear-gradient(to bottom, #000 0%, #000 40%, transparent 100%);
}

.course-card__hero-wash {
  background: linear-gradient(to bottom, transparent 38%, var(--color-surface) 100%);
}

.course-progress__value {
  transition: width 420ms var(--ease-out);
}

.course-card__action {
  transition: background-color var(--motion-fast) var(--ease-out), border-color var(--motion-fast) var(--ease-out), color var(--motion-fast) var(--ease-out);
}

@media (hover: hover) and (pointer: fine) {
  .course-card:hover {
    transform: translateY(-2px);
    border-color: var(--color-control-border);
    box-shadow: 0 8px 24px rgb(0 0 0 / 8%);
  }
}

@media (prefers-reduced-motion: reduce) {
  .course-card,
  .course-card__action,
  .course-progress__value {
    transition: none;
  }

  .course-card:hover {
    transform: none;
  }
}
</style>
