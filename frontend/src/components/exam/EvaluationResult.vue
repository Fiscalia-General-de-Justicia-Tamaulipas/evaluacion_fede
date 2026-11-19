<script setup lang="ts">
import { Award, ArrowLeft, BadgeCheck, FileText, RotateCcw } from 'lucide-vue-next';
import BaseAlert from '../ui/BaseAlert.vue';

withDefaults(defineProps<{
  moduleId: number;
  moduleName: string;
  score: number;
  correct: number;
  total: number;
  attempt: number;
  attemptsRemaining: number;
  message?: string;
}>(), { message: '' });

const emit = defineEmits<{
  (event: 'retry'): void;
  (event: 'back'): void;
  (event: 'certificate'): void;
}>();
</script>

<template>
  <section class="result-card mx-auto w-full max-w-4xl overflow-hidden rounded-[var(--radius-card)] border border-[var(--color-line)] bg-[var(--color-surface)] shadow-[var(--shadow-card)]" aria-labelledby="result-title">
    <div class="result-card__status h-1.5" :class="score >= 70 ? 'result-card__status--passed' : 'result-card__status--failed'" aria-hidden="true" />

    <div class="p-5 sm:p-8 lg:p-10">
      <header class="flex flex-col gap-5 sm:flex-row sm:items-start">
        <span class="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl border border-[var(--color-line)] bg-[var(--color-paper)] text-[var(--color-brand-900)]" aria-hidden="true">
          <BadgeCheck v-if="score >= 70" :size="30" stroke-width="1.8" />
          <Award v-else :size="30" stroke-width="1.8" />
        </span>

        <div class="min-w-0 flex-1">
          <p class="text-sm font-semibold text-[var(--color-muted)]">Módulo {{ moduleId }} <span aria-hidden="true">·</span> Intento {{ attempt }}</p>
          <h1 id="result-title" class="mt-2 text-2xl font-bold leading-tight tracking-tight text-[var(--color-brand-950)] sm:text-3xl">
            {{ score >= 70 ? 'Módulo aprobado' : 'Evaluación no acreditada' }}
          </h1>
          <p class="mt-2 max-w-2xl text-base leading-7 text-[var(--color-muted)]">{{ moduleName }}</p>
        </div>

        <span class="inline-flex min-h-9 shrink-0 items-center self-start rounded-full px-3 py-1.5 text-sm font-semibold" :class="score >= 70 ? 'result-card__badge--passed' : 'result-card__badge--failed'">
          {{ score >= 70 ? 'Acreditado' : 'No acreditado' }}
        </span>
      </header>

      <dl class="mt-7 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-paper)] p-4 sm:p-5">
          <dt class="text-sm font-medium text-[var(--color-muted)]">Calificación</dt>
          <dd class="mt-2 text-3xl font-bold tabular-nums text-[var(--color-brand-950)]">{{ score }}<span class="ml-1 text-base font-semibold text-[var(--color-muted)]">/100</span></dd>
          <p class="mt-1 text-sm leading-5 text-[var(--color-muted)]">Mínimo para acreditar: 70</p>
        </div>
        <div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-paper)] p-4 sm:p-5">
          <dt class="text-sm font-medium text-[var(--color-muted)]">Respuestas correctas</dt>
          <dd class="mt-2 text-3xl font-bold tabular-nums text-[var(--color-brand-950)]">{{ correct }}<span class="ml-1 text-base font-semibold text-[var(--color-muted)]">/ {{ total }}</span></dd>
          <p class="mt-1 text-sm leading-5 text-[var(--color-muted)]">Preguntas respondidas correctamente</p>
        </div>
        <div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-paper)] p-4 sm:col-span-2 sm:p-5 lg:col-span-1">
          <dt class="text-sm font-medium text-[var(--color-muted)]">Estado del módulo</dt>
          <dd class="mt-2 text-lg font-semibold leading-6" :class="score >= 70 ? 'text-[var(--color-success)]' : 'text-[var(--color-brand-900)]'">
            {{ score >= 70 ? 'Acreditado' : attemptsRemaining ? `${attemptsRemaining} intentos disponibles` : 'Intentos agotados' }}
          </dd>
          <p class="mt-1 text-sm leading-5 text-[var(--color-muted)]">Intento {{ attempt }} de 3</p>
        </div>
      </dl>

      <BaseAlert v-if="score < 70" class="mt-5" variant="warning" title="Puedes continuar tu capacitación">
        <template v-if="attemptsRemaining">No alcanzaste los 70 puntos necesarios. Puedes revisar el material y volver a intentarlo.</template>
        <template v-else>No alcanzaste los 70 puntos y ya utilizaste tus tres intentos. Contacta al área de capacitación para recibir orientación.</template>
      </BaseAlert>
      <BaseAlert v-if="message" class="mt-5" variant="destructive" title="No se pudo mostrar la constancia" :description="message" />

      <div class="mt-7 flex flex-col-reverse gap-3 border-t border-[var(--color-line)] pt-5 sm:flex-row sm:justify-end">
        <button type="button" class="result-button result-button--secondary page-control inline-flex min-h-11 items-center justify-center gap-2 rounded-[var(--radius-control)] border px-4 py-2.5 text-sm font-semibold" @click="emit('back')">
          <ArrowLeft :size="17" aria-hidden="true" /> Regresar al panel
        </button>
        <button v-if="score >= 70" type="button" class="result-button result-button--primary page-control inline-flex min-h-11 items-center justify-center gap-2 rounded-[var(--radius-control)] px-4 py-2.5 text-sm font-semibold" @click="emit('certificate')">
          <FileText :size="17" aria-hidden="true" /> Ver constancia borrador
        </button>
        <button v-else-if="attemptsRemaining > 0" type="button" class="result-button result-button--primary page-control inline-flex min-h-11 items-center justify-center gap-2 rounded-[var(--radius-control)] px-4 py-2.5 text-sm font-semibold" @click="emit('retry')">
          <RotateCcw :size="17" aria-hidden="true" /> Reintentar examen
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.result-card__status--passed { background: var(--color-success); }
.result-card__status--failed { background: var(--color-warning); }
.result-card__badge--passed { background: var(--color-success-soft); color: var(--color-success); }
.result-card__badge--failed { background: var(--color-warning-soft); color: var(--color-warning); }

.result-button {
  transition: color var(--motion-fast) var(--ease-out), background-color var(--motion-fast) var(--ease-out), border-color var(--motion-fast) var(--ease-out);
}

.result-button--primary { background: var(--color-brand-900); color: #fff; }
.result-button--secondary { border-color: var(--color-brand-700); background: var(--color-surface); color: var(--color-brand-900); }

@media (hover: hover) and (pointer: fine) {
  .result-button--primary:hover { background: var(--color-brand-800); }
  .result-button--secondary:hover { background: var(--color-brand-100); }
}

@media (prefers-reduced-motion: reduce) {
  .result-button { transition: none; }
}
</style>
