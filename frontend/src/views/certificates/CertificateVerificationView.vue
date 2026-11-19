<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { BadgeCheck, CircleX } from 'lucide-vue-next';
import InstitutionalHeader from '../../components/layout/InstitutionalHeader.vue';

type Verification = {
  valid: boolean;
  message: string;
  folio: string;
  issued_at: string;
  user: {
    full_name: string;
    municipality: string | null;
    sector: string | null;
  };
  course: {
    name: string;
  };
};

const props = defineProps<{ folio: string }>();
const API = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
const state = ref<'loading' | 'valid' | 'invalid' | 'error'>('loading');
const verification = ref<Verification | null>(null);
const error = ref('');
const issuedDate = computed(() => {
  const date = verification.value ? new Date(verification.value.issued_at) : null;
  return date && !Number.isNaN(date.getTime())
    ? date.toLocaleDateString('es-MX', { year: 'numeric', month: 'long', day: 'numeric' })
    : 'Fecha no disponible';
});

async function loadVerification() {
  state.value = 'loading';
  verification.value = null;
  error.value = '';
  try {
    const response = await fetch(`${API}/api/certificates/verify/${encodeURIComponent(props.folio)}`);
    const data = await response.json().catch(() => null);
    if (!response.ok) throw new Error(data?.detail || 'No se pudo consultar la constancia.');
    if (!data?.valid) {
      state.value = 'invalid';
      error.value = data?.message || 'No se encontró una constancia válida con este folio.';
      return;
    }
    verification.value = data as Verification;
    state.value = 'valid';
  } catch (cause: unknown) {
    state.value = 'error';
    error.value = cause instanceof Error ? cause.message : 'No fue posible conectar con el servicio de verificación.';
  }
}

onMounted(loadVerification);
watch(() => props.folio, loadVerification);
</script>

<template>
  <div class="min-h-screen bg-[var(--color-paper)] text-[var(--color-ink)]">
    <a href="#main-content" class="sr-only z-[100] rounded-md bg-white px-4 py-3 font-semibold text-[var(--color-ink)] focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus-visible:outline">Saltar al contenido principal</a>
    <InstitutionalHeader />

    <main id="main-content" tabindex="-1" class="mx-auto max-w-3xl px-4 py-10 sm:px-6 sm:py-14">
      <header class="text-center">
        <p class="text-sm font-semibold text-[var(--color-accent)]">Fiscalía Especializada en Delitos Electorales</p>
        <h1 class="mt-2 text-3xl font-bold leading-tight tracking-tight text-[var(--color-brand-950)] sm:text-4xl">Verificación de constancia</h1>
      </header>

      <section class="mt-8 rounded-[var(--radius-card)] border border-[var(--color-line)] bg-[var(--color-surface)] p-5 shadow-[var(--shadow-card)] sm:mt-10 sm:p-8" aria-live="polite" :aria-busy="state === 'loading'">
        <div v-if="state === 'loading'" class="py-8 text-center">
          <span aria-hidden="true" class="mx-auto block h-8 w-8 animate-spin rounded-full border-2 border-[var(--color-brand-900)] border-r-transparent" />
          <p class="mt-4 font-semibold text-[var(--color-brand-900)]">Verificando folio…</p>
        </div>

        <div v-else-if="state === 'error'" class="py-3 text-center">
          <p class="font-semibold text-[var(--color-brand-950)]">No se pudo completar la verificación</p>
          <p class="mt-2 text-sm leading-6 text-[var(--color-muted)]">{{ error }}</p>
          <button type="button" class="page-control mt-5 min-h-11 rounded-[var(--radius-control)] border border-[var(--color-brand-700)] px-4 py-2 text-sm font-semibold text-[var(--color-brand-900)] hover:bg-[var(--color-brand-100)]" @click="loadVerification">Intentar de nuevo</button>
        </div>

        <div v-else-if="state === 'invalid'" class="py-3 text-center">
          <CircleX :size="36" class="mx-auto text-[var(--color-danger)]" aria-hidden="true" />
          <h2 class="mt-3 text-xl font-bold text-[var(--color-brand-950)]">Constancia no válida</h2>
          <p class="mt-2 text-sm leading-6 text-[var(--color-muted)]">{{ error }}</p>
        </div>

        <template v-else-if="verification">
          <div class="flex items-start gap-3 rounded-[var(--radius-control)] border border-[var(--color-success)] bg-[var(--color-success-soft)] p-4">
            <BadgeCheck :size="23" class="mt-0.5 shrink-0 text-[var(--color-success)]" aria-hidden="true" />
            <div>
              <h2 class="font-bold text-[var(--color-success)]">Constancia válida</h2>
              <p class="mt-1 text-sm leading-6 text-[var(--color-success)]">{{ verification.message }}</p>
            </div>
          </div>

          <dl class="mt-6 divide-y divide-[var(--color-line)]">
            <div class="grid gap-1 py-4 sm:grid-cols-[10rem_1fr] sm:gap-4">
              <dt class="text-sm font-semibold text-[var(--color-muted)]">Folio</dt>
              <dd class="text-sm font-bold text-[var(--color-brand-950)] [overflow-wrap:anywhere]">{{ verification.folio }}</dd>
            </div>
            <div class="grid gap-1 py-4 sm:grid-cols-[10rem_1fr] sm:gap-4">
              <dt class="text-sm font-semibold text-[var(--color-muted)]">Fecha de generación</dt>
              <dd class="text-sm text-[var(--color-brand-950)]">{{ issuedDate }}</dd>
            </div>
            <div class="grid gap-1 py-4 sm:grid-cols-[10rem_1fr] sm:gap-4">
              <dt class="text-sm font-semibold text-[var(--color-muted)]">Nombre</dt>
              <dd class="text-sm text-[var(--color-brand-950)]">{{ verification.user.full_name }}</dd>
            </div>
            <div class="grid gap-1 py-4 sm:grid-cols-[10rem_1fr] sm:gap-4">
              <dt class="text-sm font-semibold text-[var(--color-muted)]">Curso</dt>
              <dd class="text-sm leading-6 text-[var(--color-brand-950)]">{{ verification.course.name }}</dd>
            </div>
            <div v-if="verification.user.municipality" class="grid gap-1 py-4 sm:grid-cols-[10rem_1fr] sm:gap-4">
              <dt class="text-sm font-semibold text-[var(--color-muted)]">Municipio</dt>
              <dd class="text-sm text-[var(--color-brand-950)]">{{ verification.user.municipality }}</dd>
            </div>
            <div v-if="verification.user.sector" class="grid gap-1 py-4 sm:grid-cols-[10rem_1fr] sm:gap-4">
              <dt class="text-sm font-semibold text-[var(--color-muted)]">Sector</dt>
              <dd class="text-sm text-[var(--color-brand-950)]">{{ verification.user.sector }}</dd>
            </div>
          </dl>
        </template>
      </section>

      <p class="mt-6 text-center text-sm text-[var(--color-muted)]">Esta consulta es pública y no requiere iniciar sesión.</p>
    </main>
  </div>
</template>
