<script setup lang="ts">
import { LoaderCircle } from 'lucide-vue-next';

withDefaults(defineProps<{
  variant?: 'primary' | 'secondary' | 'quiet';
  loading?: boolean;
  type?: 'button' | 'submit' | 'reset';
}>(), { variant: 'primary', loading: false, type: 'button' });
</script>

<template>
  <button
    :type="type"
    :disabled="$attrs.disabled || loading"
    class="base-button inline-flex min-h-11 items-center justify-center gap-2 rounded-[var(--radius-control)] px-4 py-2.5 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-50"
    :class="{
      'base-button--primary': variant === 'primary',
      'base-button--secondary': variant === 'secondary',
      'base-button--quiet': variant === 'quiet',
    }"
    :aria-busy="loading || undefined"
  >
    <LoaderCircle v-if="loading" :size="16" class="base-button__spinner" aria-hidden="true" />
    <slot />
  </button>
</template>

<style scoped>
.base-button {
  border: 1px solid transparent;
  line-height: 1.25;
  transition: color var(--motion-fast) var(--ease-out), background-color var(--motion-fast) var(--ease-out), border-color var(--motion-fast) var(--ease-out), box-shadow var(--motion-fast) var(--ease-out);
}

.base-button--primary {
  background: var(--color-brand-900);
  color: #fff;
}

.base-button--secondary {
  border-color: var(--color-brand-700);
  background: var(--color-surface);
  color: var(--color-brand-900);
}

.base-button--quiet {
  color: var(--color-brand-900);
}

.base-button:active:not(:disabled) {
  box-shadow: inset 0 0 0 999px rgb(0 0 0 / 8%);
}

.base-button__spinner {
  animation: button-spin 900ms linear infinite;
}

@keyframes button-spin {
  to { transform: rotate(360deg); }
}

@media (hover: hover) and (pointer: fine) {
  .base-button--primary:hover:not(:disabled) { background: var(--color-brand-800); }
  .base-button--secondary:hover:not(:disabled) { background: var(--color-brand-100); }
  .base-button--quiet:hover:not(:disabled) { background: var(--color-brand-100); }
}

@media (prefers-reduced-motion: reduce) {
  .base-button { transition: none; }
  .base-button__spinner { animation-duration: 1800ms; }
}
</style>
