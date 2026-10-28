<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue';
import { AlertTriangle, X } from 'lucide-vue-next';

withDefaults(defineProps<{
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  busy?: boolean;
}>(), { confirmLabel: 'Confirmar', cancelLabel: 'Cancelar', busy: false });

const emit = defineEmits<{ confirm: []; cancel: [] }>();
const dialog = ref<HTMLElement | null>(null);
const cancelButton = ref<HTMLButtonElement | null>(null);
let previousFocus: HTMLElement | null = null;

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && !event.defaultPrevented) {
    event.preventDefault();
    emit('cancel');
    return;
  }
  if (event.key !== 'Tab' || !dialog.value) return;
  const controls = Array.from(dialog.value.querySelectorAll<HTMLElement>('button:not(:disabled)'));
  const first = controls[0];
  const last = controls[controls.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last?.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first?.focus();
  }
}

onMounted(async () => {
  previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  document.addEventListener('keydown', handleKeydown);
  document.body.style.overflow = 'hidden';
  await nextTick();
  cancelButton.value?.focus();
});

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleKeydown);
  document.body.style.overflow = '';
  if (previousFocus?.isConnected) previousFocus.focus();
});
</script>

<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-[100] grid place-items-center bg-black/55 p-4" @mousedown.self="emit('cancel')">
      <section
        ref="dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
        aria-describedby="confirm-dialog-description"
        class="w-full max-w-lg rounded-2xl border border-[#c7c7c6] bg-white p-6 shadow-[0_24px_80px_rgba(0,0,0,.24)] sm:p-7"
      >
        <div class="flex items-start gap-4">
          <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-[#c7c7c6] bg-[#f2f2f1] text-[#292928]">
            <AlertTriangle :size="21" aria-hidden="true" />
          </span>
          <div class="min-w-0 flex-1">
            <h2 id="confirm-dialog-title" class="text-lg font-bold leading-6 text-[#202020]">{{ title }}</h2>
            <p id="confirm-dialog-description" class="mt-2 text-sm leading-6 text-[#575756]">{{ description }}</p>
          </div>
          <button type="button" aria-label="Cerrar confirmación" class="rounded-md p-1 text-[#575756] hover:bg-[#eeeeed] focus-visible:outline" :disabled="busy" @click="emit('cancel')">
            <X :size="18" aria-hidden="true" />
          </button>
        </div>
        <div class="mt-7 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <button ref="cancelButton" type="button" class="min-h-11 rounded-lg border border-[#c7c7c6] bg-white px-4 py-2.5 text-sm font-semibold text-[#292928] transition-colors hover:bg-[#f2f2f1] disabled:opacity-50" :disabled="busy" @click="emit('cancel')">{{ cancelLabel }}</button>
          <button type="button" class="min-h-11 rounded-lg bg-[#292928] px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-[#444443] disabled:cursor-wait disabled:opacity-60" :disabled="busy" @click="emit('confirm')">{{ busy ? 'Enviando…' : confirmLabel }}</button>
        </div>
      </section>
    </div>
  </Teleport>
</template>
