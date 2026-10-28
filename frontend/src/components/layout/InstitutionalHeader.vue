<script setup lang="ts">
import { ArrowLeft, LogOut } from 'lucide-vue-next';

withDefaults(defineProps<{
  showBack?: boolean;
  showLogout?: boolean;
  moduleLabel?: string;
  participantName?: string;
  sector?: string;
}>(), {
  showBack: false,
  showLogout: false,
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
  <header class="sticky top-0 z-30 border-b border-[#d2d2d1] bg-white/95 shadow-[0_1px_3px_rgba(0,0,0,.04)] backdrop-blur">
    <div class="mx-auto flex min-h-[76px] max-w-6xl items-center gap-3 px-4 py-3 sm:gap-5 sm:px-6">
      <div class="flex min-w-0 shrink-0 items-center gap-3 sm:gap-5">
        <img src="/logo_fgjtam.png" alt="Fiscalía General de Justicia del Estado de Tamaulipas" class="h-10 w-auto max-w-[130px] object-contain sm:h-12 sm:max-w-[170px]" />
        <span aria-hidden="true" class="h-9 w-px bg-[#d2d2d1] sm:h-11" />
        <img src="/logo_fede.png" alt="Fiscalía Especializada en Delitos Electorales" class="h-10 w-auto max-w-[130px] object-contain sm:h-12 sm:max-w-[170px]" />
      </div>

      <div class="ml-auto flex min-w-0 items-center justify-end gap-2 sm:gap-4">
        <div v-if="moduleLabel" class="hidden min-w-0 text-right sm:block">
          <p class="truncate text-sm font-bold text-[#292928]">{{ moduleLabel }}</p>
          <p v-if="participantName" class="mt-0.5 truncate text-xs text-[#575756]">{{ participantName }}<template v-if="sector"> · {{ sector }}</template></p>
        </div>
        <p v-else-if="participantName" class="hidden max-w-56 truncate text-sm font-bold text-[#292928] md:block">{{ participantName }}</p>

        <button v-if="showBack" type="button" title="Regresar al panel de módulos" aria-label="Regresar al panel de módulos" class="inline-flex h-10 shrink-0 items-center gap-2 rounded-lg border border-[#c7c7c6] bg-white px-3 text-sm font-semibold text-[#292928] transition-colors duration-200 hover:bg-[#f2f2f1] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#575756]" @click="emit('back')">
          <ArrowLeft :size="17" /><span class="hidden sm:inline">Panel de módulos</span>
        </button>
        <button v-if="showLogout" type="button" title="Cerrar sesión" aria-label="Cerrar sesión" class="inline-flex h-10 shrink-0 items-center gap-2 rounded-lg border border-[#c7c7c6] bg-white px-3 text-sm font-semibold text-[#292928] transition-colors duration-200 hover:bg-[#f2f2f1] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#575756]" @click="emit('logout')">
          <LogOut :size="17" /><span class="hidden sm:inline">Cerrar sesión</span>
        </button>
      </div>
    </div>
  </header>
</template>
