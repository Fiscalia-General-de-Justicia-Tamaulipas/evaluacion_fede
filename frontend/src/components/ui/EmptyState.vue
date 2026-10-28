<script setup lang="ts">
import { Inbox } from 'lucide-vue-next';
defineProps<{ title: string; description: string }>();
</script>

<template>
  <div class="rounded-2xl border border-dashed border-[#c7c7c6] bg-white px-6 py-10 text-center">
    <Inbox :size="24" class="mx-auto text-[#575756]" aria-hidden="true" />
    <h2 class="mt-3 text-base font-semibold text-[#202020]">{{ title }}</h2>
    <p class="mx-auto mt-1 max-w-md text-sm leading-6 text-[#575756]">{{ description }}</p>
    <div v-if="$slots.actions" class="mt-5 flex justify-center"><slot name="actions" /></div>
  </div>
</template>
