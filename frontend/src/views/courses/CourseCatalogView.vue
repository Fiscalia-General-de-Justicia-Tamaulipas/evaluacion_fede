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
  <div class="min-h-screen bg-[var(--color-paper)] text-[var(--color-ink)]">
    <InstitutionalHeader :show-logout="true" :participant-name="fullName" @logout="logout" />

    <main id="main-content" tabindex="-1" class="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-12 lg:px-8">
      <header class="max-w-3xl">
        <p class="text-sm font-semibold text-[var(--color-accent)]">Capacitación institucional</p>
        <h1 class="mt-2 text-3xl font-bold leading-tight tracking-tight text-[var(--color-brand-950)] sm:text-4xl">Cursos disponibles</h1>
        <p class="mt-4 text-base leading-7 text-[var(--color-muted)]">Hola, {{ fullName }}. Elige un curso para consultar sus módulos y continuar tu capacitación.</p>
      </header>

      <BaseAlert v-if="error" class="mt-6" variant="destructive" title="No se pudo consultar tu avance" :description="error">
        <template #action>
          <button type="button" class="page-control min-h-11 rounded-[var(--radius-control)] border border-[var(--color-brand-700)] bg-[var(--color-surface)] px-4 py-2 text-sm font-semibold text-[var(--color-brand-900)] hover:bg-[var(--color-brand-100)]" @click="loadStatus">Reintentar</button>
        </template>
      </BaseAlert>

      <section class="mt-8 sm:mt-10" aria-labelledby="courses-heading" :aria-busy="loading">
        <div class="mb-4 flex flex-wrap items-end justify-between gap-2">
          <h2 id="courses-heading" class="text-xl font-bold text-[var(--color-brand-950)] sm:text-2xl">Tu catálogo de cursos</h2>
          <p class="text-sm text-[var(--color-muted)]">{{ courses.length }} {{ courses.length === 1 ? 'curso disponible' : 'cursos disponibles' }}</p>
        </div>

        <div class="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
          <article v-for="course in courses" :key="course.key" class="flex min-h-72 flex-col rounded-[var(--radius-card)] border border-[var(--color-line)] bg-[var(--color-surface)] p-5 shadow-[var(--shadow-card)] sm:p-6">
            <div class="flex items-start justify-between gap-4">
              <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[var(--color-brand-100)] text-[var(--color-brand-900)]">
                <BookOpen :size="21" aria-hidden="true" />
              </span>
              <span v-if="!loading && completedModules(course) === course.moduleIds.length" class="inline-flex items-center gap-1.5 rounded-full bg-[var(--color-success-soft)] px-3 py-1.5 text-xs font-semibold text-[var(--color-success)]">
                <CheckCircle2 :size="15" aria-hidden="true" /> Acreditado
              </span>
            </div>

            <h3 class="mt-5 text-lg font-bold leading-6 text-[var(--color-brand-950)]">{{ course.title }}</h3>
            <p class="mt-2 text-sm leading-6 text-[var(--color-muted)]">{{ course.description }}</p>

            <div class="mt-6">
              <div class="flex items-center justify-between gap-3 text-sm">
                <span class="font-semibold text-[var(--color-brand-900)]">{{ loading ? 'Consultando avance…' : `${completedModules(course)} de ${course.moduleIds.length} módulos acreditados` }}</span>
                <span class="tabular-nums text-[var(--color-muted)]">{{ loading ? '—' : `${courseProgress(course)}%` }}</span>
              </div>
              <div class="mt-2 h-2 overflow-hidden rounded-full bg-[var(--color-brand-100)]" role="progressbar" :aria-label="`Avance de ${course.title}`" :aria-valuenow="loading ? 0 : courseProgress(course)" aria-valuemin="0" aria-valuemax="100">
                <div class="h-full rounded-full bg-[var(--color-brand-900)] transition-[width] duration-300" :style="{ width: `${loading ? 0 : courseProgress(course)}%` }" />
              </div>
            </div>

            <button type="button" class="page-control mt-auto inline-flex min-h-11 w-full items-center justify-between gap-3 rounded-[var(--radius-control)] border border-[var(--color-brand-700)] px-4 py-2.5 text-sm font-semibold text-[var(--color-brand-900)] hover:bg-[var(--color-brand-100)]" @click="emit('select-course')">
              Abrir módulos
              <ArrowRight :size="17" aria-hidden="true" />
            </button>
          </article>
        </div>
      </section>
    </main>
  </div>
</template>
