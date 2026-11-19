<script setup lang="ts">
withDefaults(defineProps<{ label?: string; rows?: number }>(), { label: 'Cargando contenido', rows: 3 });
</script>

<template>
  <div role="status" aria-live="polite" :aria-label="label" class="loading-state space-y-3" aria-busy="true">
    <span class="sr-only">{{ label }}…</span>
    <div
      v-for="row in rows"
      :key="row"
      aria-hidden="true"
      class="loading-state__line h-5 rounded-md bg-[var(--color-brand-100)]"
      :class="row === 1 ? 'w-3/4' : 'w-full'"
    />
  </div>
</template>

<style scoped>
.loading-state {
  min-width: 0;
}

.loading-state__line {
  max-width: 100%;
}
</style>
