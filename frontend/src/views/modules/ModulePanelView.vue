<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { BookOpen, CheckCircle2, LockKeyhole } from 'lucide-vue-next';
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
  'Integración de la carpeta de investigación, primer respondiente, retos y cultura de prevención',
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
  <div class="min-h-screen bg-[#f5f5f5] text-[#292928]">
    <InstitutionalHeader :show-logout="true" @logout="logout" />

    <main class="mx-auto max-w-6xl px-5 py-10 md:py-14">
      <p class="text-xs font-bold uppercase tracking-[0.18em] text-[#878787]">Capacitación institucional</p>
      <h1 class="mt-2 text-3xl font-black md:text-4xl">Bienvenido, {{ fullName }}</h1>
      <p class="mt-3 max-w-2xl text-sm leading-6 text-[#878787]">Selecciona un módulo para continuar tu capacitación. Acreditas con una calificación mínima de 70/100.</p>

      <BaseAlert v-if="error" class="mt-6" variant="destructive" title="No se pudieron cargar tus módulos" :description="error">
        <template #action><button type="button" class="min-h-10 rounded-lg border border-[#a3a3a2] bg-white px-3 py-2 text-sm font-semibold hover:bg-[#f2f2f1]" @click="loadStatus">Reintentar</button></template>
      </BaseAlert>

      <div class="mt-8 grid gap-5 md:grid-cols-3">
        <template v-if="loading">
          <div v-for="moduleId in [1, 2, 3]" :key="moduleId" aria-hidden="true" class="h-[320px] animate-pulse rounded-2xl border border-[#dadada] bg-white" />
        </template>
        <div v-if="!loading && !error && !modules.length" class="rounded-2xl border border-[#dadada] bg-white p-8 text-sm text-[#575756]">No hay módulos disponibles en este momento. Intenta recargar el estado.</div>
        <button
          v-for="module in modules"
          :key="module.module_id"
          type="button"
          class="module-card group h-[320px] w-full text-left"
          :disabled="loading"
          @click="emit('select-module', module.module_id)"
        >
          <article class="flex h-full flex-col rounded-2xl border border-[#dadada] bg-white p-6 shadow-sm transition-[transform,border-color,box-shadow] duration-250 group-hover:-translate-y-1 group-hover:border-[#878787] group-hover:shadow-lg group-focus-visible:-translate-y-1">
            <div class="flex items-center justify-between">
              <span class="flex h-11 w-11 items-center justify-center rounded-xl bg-[#575756] text-sm font-black text-white">{{ module.module_id }}</span>
              <CheckCircle2 v-if="module.passed" :size="21" class="text-[#575756]" />
              <LockKeyhole v-else-if="!module.questions_available && module.module_id === 2" :size="21" class="text-[#878787]" />
              <BookOpen v-else :size="21" class="text-[#878787]" />
            </div>
            <p class="mt-6 text-xs font-bold uppercase tracking-widest text-[#878787]">Módulo {{ module.module_id }}</p>
            <h2 class="mt-2 line-clamp-3 min-h-[4.5rem] text-lg font-black leading-6">{{ titleFor(module.module_id) }}</h2>
            <div class="mt-auto min-h-[3.75rem] border-t border-[#e5e5e5] pt-4 text-sm">
              <template v-if="module.passed">
                <p class="font-bold text-[#575756]">Aprobado · {{ module.best_score }}/100</p>
                <p class="mt-1 text-xs text-[#878787]">Constancia disponible</p>
              </template>
              <template v-else-if="module.in_progress">
                <p class="font-bold text-[#575756]">Evaluación en curso</p>
                <p class="mt-1 text-xs text-[#878787]">Selecciona para continuar donde te quedaste</p>
              </template>
              <template v-else-if="module.module_id === 2 && !module.questions_available">
                <p class="font-bold text-[#878787]">Cuestionario pendiente</p>
                <p class="mt-1 text-xs text-[#575756]">Aún no se han cargado preguntas para este módulo.</p>
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

<style scoped>
.module-card{animation:card-enter .45s cubic-bezier(.2,.75,.25,1) both}
.module-card:nth-of-type(2){animation-delay:70ms}.module-card:nth-of-type(3){animation-delay:140ms}
@keyframes card-enter{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
@media(prefers-reduced-motion:reduce){.module-card{animation:none}.module-card :deep(article){transition:none}}
</style>
