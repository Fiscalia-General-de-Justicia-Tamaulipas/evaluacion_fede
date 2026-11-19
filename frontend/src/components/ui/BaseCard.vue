<script setup lang="ts">
withDefaults(defineProps<{ interactive?: boolean }>(), { interactive: false });
</script>

<template>
  <section class="base-card rounded-[var(--radius-card)] border border-[var(--color-line)] bg-[var(--color-surface)] p-6 shadow-[var(--shadow-card)]" :class="{ 'base-card--interactive': interactive }">
    <slot />
  </section>
</template>

<style scoped>
.base-card {
  color: var(--color-ink);
}

.base-card--interactive {
  transition: border-color var(--motion-fast) var(--ease-out), box-shadow var(--motion-fast) var(--ease-out);
}

@media (hover: hover) and (pointer: fine) {
  .base-card--interactive:hover {
    border-color: var(--color-brand-700);
    box-shadow: 0 6px 18px rgb(32 32 32 / 9%);
  }
}

@media (prefers-reduced-motion: reduce) {
  .base-card--interactive { transition: none; }
}
</style>
