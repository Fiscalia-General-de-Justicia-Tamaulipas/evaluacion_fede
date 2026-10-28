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
    class="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold transition-[background-color,border-color,color,transform] duration-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#575756] disabled:cursor-not-allowed disabled:opacity-55"
    :class="{
      'bg-[#292928] text-white hover:-translate-y-0.5 hover:bg-[#444443]': variant === 'primary',
      'border border-[#c7c7c6] bg-white text-[#292928] hover:bg-[#f2f2f1]': variant === 'secondary',
      'text-[#444443] hover:bg-[#eeeeed]': variant === 'quiet',
    }"
  >
    <LoaderCircle v-if="loading" :size="16" class="animate-spin" aria-hidden="true" />
    <slot />
  </button>
</template>
