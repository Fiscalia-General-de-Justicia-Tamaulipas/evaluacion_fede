<script setup lang="ts">
import { ArrowLeft, LogOut } from 'lucide-vue-next';

withDefaults(defineProps<{
  showBack?: boolean;
  showLogout?: boolean;
  backLabel?: string;
  moduleLabel?: string;
  participantName?: string;
  sector?: string;
}>(), {
  showBack: false,
  showLogout: false,
  backLabel: 'Panel de módulos',
  moduleLabel: '',
  participantName: '',
  sector: '',
});

const emit = defineEmits<{
  (event: 'back'): void;
  (event: 'logout'): void;
}>();
</script>

<template>
  <header class="institutional-header sticky top-0 z-30 border-b bg-[var(--color-surface)]">
    <div class="mx-auto flex min-h-[68px] max-w-6xl items-center gap-2 px-3 py-3 sm:min-h-[76px] sm:gap-5 sm:px-6">
      <div class="institutional-header__brand flex min-w-0 shrink items-center gap-2 sm:gap-5">
        <img src="/logo_fgjtam.png" alt="Fiscalía General de Justicia del Estado de Tamaulipas" class="h-9 w-auto max-w-[78px] object-contain sm:h-12 sm:max-w-[170px]" />
        <span aria-hidden="true" class="h-8 w-px shrink-0 bg-[var(--color-line)] sm:h-11" />
        <img src="/logo_fede.png" alt="Fiscalía Especializada en Delitos Electorales" class="h-9 w-auto max-w-[78px] object-contain sm:h-12 sm:max-w-[170px]" />
      </div>

      <div class="ml-auto flex min-w-0 shrink-0 items-center justify-end gap-2 sm:gap-4">
        <div v-if="moduleLabel" class="hidden min-w-0 text-right sm:block">
          <p class="max-w-64 truncate text-sm font-bold leading-5 text-[var(--color-brand-900)]">{{ moduleLabel }}</p>
          <p v-if="participantName" class="mt-0.5 max-w-64 truncate text-xs leading-4 text-[var(--color-muted)]">{{ participantName }}<template v-if="sector"> · {{ sector }}</template></p>
        </div>
        <p v-else-if="participantName" class="hidden max-w-56 truncate text-sm font-bold text-[var(--color-brand-900)] md:block">{{ participantName }}</p>

        <button v-if="showBack" type="button" :title="`Regresar a ${backLabel.toLowerCase()}`" :aria-label="`Regresar a ${backLabel.toLowerCase()}`" class="institutional-header__button page-control inline-flex h-11 w-11 shrink-0 items-center justify-center gap-2 rounded-[var(--radius-control)] border bg-[var(--color-surface)] px-2 text-sm font-semibold sm:w-auto sm:px-3" @click="emit('back')">
          <ArrowLeft :size="18" aria-hidden="true" /><span class="hidden sm:inline">{{ backLabel }}</span>
        </button>
        <button v-if="showLogout" type="button" title="Cerrar sesión" aria-label="Cerrar sesión" class="institutional-header__button page-control inline-flex h-11 w-11 shrink-0 items-center justify-center gap-2 rounded-[var(--radius-control)] border bg-[var(--color-surface)] px-2 text-sm font-semibold sm:w-auto sm:px-3" @click="emit('logout')">
          <LogOut :size="18" aria-hidden="true" /><span class="hidden sm:inline">Cerrar sesión</span>
        </button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.institutional-header {
  border-color: var(--color-line);
  box-shadow: 0 1px 3px rgb(32 32 32 / 5%);
}

.institutional-header__button {
  border-color: var(--color-brand-700);
  color: var(--color-brand-900);
  transition: color var(--motion-fast) var(--ease-out), background-color var(--motion-fast) var(--ease-out), border-color var(--motion-fast) var(--ease-out);
}

.institutional-header__button:active {
  background: var(--color-brand-100);
}

@media (hover: hover) and (pointer: fine) {
  .institutional-header__button:hover {
    border-color: var(--color-brand-800);
    background: var(--color-brand-100);
  }
}

@media (prefers-reduced-motion: reduce) {
  .institutional-header__button { transition: none; }
}
</style>
