<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue';
import { AlertCircle, CheckCircle2, Info, TriangleAlert, X } from 'lucide-vue-next';

const props = withDefaults(defineProps<{
  variant?: 'default' | 'destructive' | 'info' | 'success' | 'warning';
  title?: string;
  description?: string;
  floating?: boolean;
  duration?: number;
}>(), { variant: 'default', title: '', description: '', floating: false, duration: 5000 });

const visible = ref(true);
let timeout: ReturnType<typeof setTimeout> | undefined;
function startTimer() {
  clearTimeout(timeout);
  visible.value = true;
  if (props.floating && props.duration > 0) timeout = setTimeout(() => { visible.value = false; }, props.duration);
}
watch(() => [props.title, props.description, props.variant], startTimer);
if (props.floating) startTimer();
onBeforeUnmount(() => clearTimeout(timeout));

const icons = { default: Info, info: Info, destructive: AlertCircle, success: CheckCircle2, warning: TriangleAlert };
</script>

<template>
  <Teleport v-if="floating" to="body">
  <Transition name="alert-toast">
  <div v-if="visible"
    class="fixed right-4 top-4 z-[10000] w-[min(26rem,calc(100vw-2rem))] shadow-xl"
    :class="{ 'alert-toast-enter': true }"
  >
    <div
    data-slot="alert"
    :data-variant="variant"
    :role="variant === 'destructive' ? 'alert' : 'status'"
    :aria-live="variant === 'destructive' ? 'assertive' : 'polite'"
    class="grid w-full grid-cols-[1.25rem_1fr_auto] items-start gap-x-3 rounded-xl border px-4 py-3.5 text-sm leading-6"
    :class="{
      'border-slate-300 bg-white text-slate-900': variant === 'default',
      'border-blue-300 bg-blue-50 text-blue-950': variant === 'info',
      'border-red-300 bg-red-50 text-red-950': variant === 'destructive',
      'border-green-300 bg-green-50 text-green-950': variant === 'success',
      'border-amber-300 bg-amber-50 text-amber-950': variant === 'warning',
    }"
  >
    <component :is="icons[variant]" aria-hidden="true" :size="18" class="mt-1 shrink-0" />
    <div class="min-w-0">
      <div v-if="title" data-slot="alert-title" class="font-bold text-[#202020]">{{ title }}</div>
      <div data-slot="alert-description" class="opacity-90">
        <slot>{{ description }}</slot>
      </div>
      <div v-if="$slots.action" data-slot="alert-action" class="mt-3 flex flex-wrap items-center gap-2">
        <slot name="action" />
      </div>
    </div>
    <button v-if="floating" type="button" aria-label="Cerrar aviso" class="rounded-md p-1 opacity-70 hover:opacity-100 focus-visible:outline focus-visible:outline-2" @click="visible = false"><X :size="17" /></button>
    </div>
  </div>
  </Transition>
  </Teleport>
  <div v-else
    data-slot="alert"
    :data-variant="variant"
    :role="variant === 'destructive' ? 'alert' : 'status'"
    :aria-live="variant === 'destructive' ? 'assertive' : 'polite'"
    class="grid w-full grid-cols-[1.25rem_1fr] items-start gap-x-3 rounded-xl border px-4 py-3.5 text-sm leading-6"
    :class="{
      'border-[#c7c7c6] bg-white text-[#292928]': variant === 'default',
      'border-[#c7c7c6] bg-[#f2f2f1] text-[#292928]': variant === 'info',
      'border-[#8f8f8e] bg-[#eeeeed] text-[#202020]': variant === 'destructive',
      'border-[#b7b7b6] bg-[#f7f7f6] text-[#292928]': variant === 'success',
      'border-[#a3a3a2] bg-[#f2f2f1] text-[#292928]': variant === 'warning',
    }"
  >
    <component :is="icons[variant]" aria-hidden="true" :size="18" class="mt-1 shrink-0 text-[#575756]" />
    <div class="min-w-0">
      <div v-if="title" data-slot="alert-title" class="font-bold text-[#202020]">{{ title }}</div>
      <div data-slot="alert-description" class="text-[#3e3e3e]"><slot>{{ description }}</slot></div>
      <div v-if="$slots.action" data-slot="alert-action" class="mt-3 flex flex-wrap items-center gap-2"><slot name="action" /></div>
    </div>
  </div>
</template>
