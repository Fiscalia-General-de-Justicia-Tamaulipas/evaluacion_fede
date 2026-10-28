<script setup lang="ts">
withDefaults(defineProps<{ label?: string; rows?: number }>(), { label: 'Cargando contenido', rows: 3 });
</script>

<template>
  <div role="status" :aria-label="label" class="space-y-3" aria-busy="true">
    <span class="sr-only">{{ label }}…</span>
    <div v-for="row in rows" :key="row" class="h-5 animate-pulse rounded-md bg-[#e7e7e6]" :class="row === 1 ? 'w-3/4' : 'w-full'" />
  </div>
</template>
