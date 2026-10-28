<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { BookOpen, CheckCircle2, LockKeyhole, LogOut } from 'lucide-vue-next';
import { useAuth } from '../lib/auth';

type ModuleStatus = {
  module_id: number;
  name: string;
  attempts: number;
  attempts_remaining: number;
  best_score: number | null;
  passed: boolean;
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

const titles = [
  'Nociones básicas de derecho electoral',
  'Delitos Electorales y su investigación en el Contexto de los Procesos Electorales Locales',
  'Integración de la carpeta de investigación, primer respondiente, retos y cultura de prevención',
];

async function loadStatus() {
  loading.value = true;
  try {
    const response = await apiFetch('/api/modules/status');
    if (response.ok) {
      const data = await response.json();
      modules.value = data.modules;
    }
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
  <div class="min-h-screen bg-[#f5f5f5] text-[#292928]">
    <header class="border-b border-[#dadada] bg-white">
      <div class="mx-auto flex max-w-6xl items-center gap-4 px-5 py-4">
        <img src="/logo_fgjtam.png" alt="FGJ Tamaulipas" class="h-14 w-auto object-contain" />
        <div class="h-10 w-px bg-[#dadada]" />
        <img src="/logo_fede.png" alt="FEDE" class="h-14 w-auto object-contain" />
        <button type="button" class="ml-auto inline-flex items-center gap-2 rounded-lg border border-[#dadada] px-3 py-2 text-sm font-bold text-[#575756] transition hover:bg-[#f0f0ef]" @click="logout">
          <LogOut :size="17" />
          Cerrar sesión
        </button>
      </div>
    </header>

    <main class="mx-auto max-w-6xl px-5 py-10 md:py-14">
      <p class="text-xs font-bold uppercase tracking-[0.18em] text-[#878787]">Capacitación institucional</p>
      <h1 class="mt-2 text-3xl font-black md:text-4xl">Bienvenido, {{ fullName }}</h1>
      <p class="mt-3 max-w-2xl text-sm leading-6 text-[#878787]">Selecciona un módulo para continuar tu capacitación. Cada constancia se genera al aprobar con una calificación mínima de 7.</p>

      <div class="mt-8 grid gap-5 md:grid-cols-3">
        <div v-if="loading" v-for="moduleId in [1, 2, 3]" :key="moduleId" class="h-64 animate-pulse rounded-2xl border border-[#dadada] bg-white" />
        <button
          v-for="module in modules"
          :key="module.module_id"
          type="button"
          class="group text-left"
          :disabled="loading"
          @click="emit('select-module', module.module_id)"
        >
          <article class="min-h-64 rounded-2xl border border-[#dadada] bg-white p-6 shadow-sm transition group-hover:-translate-y-1 group-hover:border-[#878787] group-hover:shadow-xl">
            <div class="flex items-center justify-between">
              <span class="flex h-11 w-11 items-center justify-center rounded-xl bg-[#575756] text-sm font-black text-white">{{ module.module_id }}</span>
              <CheckCircle2 v-if="module.passed" :size="21" class="text-[#575756]" />
              <LockKeyhole v-else-if="!module.questions_available && module.module_id === 2" :size="21" class="text-[#878787]" />
              <BookOpen v-else :size="21" class="text-[#878787]" />
            </div>
            <p class="mt-6 text-xs font-bold uppercase tracking-widest text-[#878787]">Módulo {{ module.module_id }}</p>
            <h2 class="mt-2 text-lg font-black leading-6">{{ titleFor(module.module_id) }}</h2>
            <div class="mt-5 border-t border-[#e5e5e5] pt-4 text-sm">
              <template v-if="module.passed">
                <p class="font-bold text-[#575756]">Aprobado · {{ module.best_score }}/10</p>
                <p class="mt-1 text-xs text-[#878787]">Constancia disponible</p>
              </template>
              <template v-else-if="module.module_id === 2 && !module.questions_available">
                <p class="font-bold text-[#878787]">Cuestionario pendiente</p>
              </template>
              <template v-else>
                <p class="text-[#878787]">{{ module.attempts ?? 0 }} de 3 intentos usados</p>
              </template>
            </div>
          </article>
        </button>
      </div>
    </main>
  </div>
</template>
