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
  <Transition name="result" appear>
    <section class="result-card mx-auto w-full max-w-4xl overflow-hidden rounded-2xl border border-[#d2d2d1] bg-white shadow-[0_16px_48px_rgba(0,0,0,.08)]">
      <div class="h-1.5 bg-[#575756]" />
      <div class="px-6 py-8 sm:px-10 sm:py-10">
        <div class="flex flex-col gap-6 sm:flex-row sm:items-start">
          <div class="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl border border-[#d2d2d1] bg-[#f5f5f4] text-[#292928]">
            <BadgeCheck v-if="score >= 70" :size="30" stroke-width="1.8" />
            <Award v-else :size="30" stroke-width="1.8" />
          </div>
          <div class="min-w-0 flex-1">
            <p class="text-xs font-bold uppercase tracking-[.16em] text-[#575756]">Módulo {{ moduleId }} · intento {{ attempt }}</p>
            <h1 class="mt-2 text-2xl font-bold tracking-tight text-[#202020] sm:text-3xl">
              {{ score >= 70 ? 'Módulo aprobado' : 'Evaluación no acreditada' }}
            </h1>
            <p class="mt-2 max-w-2xl text-sm leading-6 text-[#575756]">{{ moduleName }}</p>
          </div>
          <span class="inline-flex shrink-0 items-center gap-2 self-start rounded-full border border-[#c7c7c6] bg-[#f5f5f4] px-3 py-1.5 text-xs font-bold text-[#292928]">
            <span class="h-1.5 w-1.5 rounded-full bg-[#575756]" />
            {{ score >= 70 ? 'Acreditado' : 'No acreditado' }}
          </span>
        </div>

        <dl class="mt-8 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div class="rounded-xl border border-[#d2d2d1] bg-[#fafafa] p-4">
            <dt class="text-xs font-semibold text-[#575756]">Calificación</dt>
            <dd class="mt-1 text-2xl font-bold tabular-nums text-[#202020]">{{ score }}<span class="text-sm font-medium text-[#575756]">/100</span></dd>
          </div>
          <div class="rounded-xl border border-[#d2d2d1] bg-[#fafafa] p-4">
            <dt class="text-xs font-semibold text-[#575756]">Respuestas correctas</dt>
            <dd class="mt-1 text-2xl font-bold tabular-nums text-[#202020]">{{ correct }}<span class="text-sm font-medium text-[#575756]"> / {{ total }}</span></dd>
          </div>
          <div class="rounded-xl border border-[#d2d2d1] bg-[#fafafa] p-4">
            <dt class="text-xs font-semibold text-[#575756]">Estado del módulo</dt>
            <dd class="mt-1 text-base font-bold text-[#202020]">{{ score >= 70 ? 'Aprobado' : attemptsRemaining ? `${attemptsRemaining} intentos disponibles` : 'Intentos agotados' }}</dd>
          </div>
        </dl>

        <BaseAlert v-if="score < 70" class="mt-5" variant="warning" title="Evaluación no acreditada">
          <template v-if="attemptsRemaining">No alcanzaste la calificación mínima de 70. Puedes volver a revisar el video y realizar otro intento.</template>
          <template v-else>No alcanzaste la calificación mínima de 70 y agotaste tus tres intentos. Contacta al área de capacitación para recibir orientación.</template>
        </BaseAlert>
        <BaseAlert v-if="message" class="mt-5" variant="destructive" title="No se pudo mostrar la constancia" :description="message" />

        <div class="mt-8 flex flex-col-reverse gap-3 border-t border-[#e5e5e5] pt-6 sm:flex-row sm:justify-end">
          <button type="button" class="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-[#c7c7c6] bg-white px-4 py-2.5 text-sm font-semibold text-[#292928] transition-colors duration-200 hover:bg-[#f3f3f2] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#575756]" @click="emit('back')">
            <ArrowLeft :size="17" /> Regresar al panel
          </button>
          <button v-if="score >= 70" type="button" class="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-[#292928] px-4 py-2.5 text-sm font-semibold text-white transition-[background-color,transform] duration-200 hover:-translate-y-0.5 hover:bg-[#444443] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#575756]" @click="emit('certificate')">
            <FileText :size="17" /> Ver constancia borrador
          </button>
          <button v-else-if="attemptsRemaining > 0" type="button" class="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-[#292928] px-4 py-2.5 text-sm font-semibold text-white transition-[background-color,transform] duration-200 hover:-translate-y-0.5 hover:bg-[#444443]" @click="emit('retry')">
            <RotateCcw :size="17" /> Reintentar examen
          </button>
        </div>
      </div>
    </section>
  </Transition>
</template>

<style scoped>
.result-enter-active,.result-leave-active{transition:opacity .28s ease,transform .32s cubic-bezier(.2,.75,.25,1)}
.result-enter-from,.result-leave-to{opacity:0;transform:translateY(12px)}
@media(prefers-reduced-motion:reduce){.result-enter-active,.result-leave-active{transition:none}}
</style>
