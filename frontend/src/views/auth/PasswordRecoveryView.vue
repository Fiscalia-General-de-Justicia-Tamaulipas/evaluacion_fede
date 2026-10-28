<script setup lang="ts">
import { computed, ref } from 'vue';
import { ArrowLeft, KeyRound, Loader2, Lock, Mail } from 'lucide-vue-next';
import BaseAlert from '../../components/ui/BaseAlert.vue';
import { extractErrorMessage, useAuth } from '../../services/auth';

const props = defineProps<{ resetToken?: string }>();
const emit = defineEmits<{
  (event: 'go-login'): void;
  (event: 'reset-complete'): void;
}>();

const { requestPasswordReset, resetPassword } = useAuth();
const isResetMode = computed(() => !!props.resetToken);
const email = ref('');
const password = ref('');
const confirmPassword = ref('');
const loading = ref(false);
const error = ref('');
const success = ref('');

async function submit() {
  if (loading.value) return;
  error.value = '';
  success.value = '';

  if (isResetMode.value && password.value !== confirmPassword.value) {
    error.value = 'Las contraseñas no coinciden.';
    return;
  }

  loading.value = true;
  try {
    if (isResetMode.value) {
      await resetPassword(props.resetToken!, password.value);
      emit('reset-complete');
    } else {
      const response = await requestPasswordReset(email.value.trim());
      success.value = response.message;
    }
  } catch (cause: any) {
    error.value = cause?.message || extractErrorMessage(cause, 'No se pudo completar la solicitud.');
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <main class="flex min-h-screen items-center justify-center bg-[#f5f5f4] px-4 py-10 text-[#292928]">
    <div class="w-full max-w-md">
      <div class="mb-8 flex flex-col items-center text-center">
        <div class="flex items-center gap-4">
          <img src="/logo_fgjtam.png" alt="Fiscalía General de Justicia de Tamaulipas" class="h-12 w-auto object-contain" />
          <span aria-hidden="true" class="h-10 w-px bg-[#d2d2d1]" />
          <img src="/logo_fede.png" alt="FEDE" class="h-12 w-auto object-contain" />
        </div>
        <p class="mt-4 text-[10px] font-bold uppercase tracking-[0.22em] text-[#999998]">Plataforma de capacitación</p>
      </div>

      <section class="rounded-[28px] border border-black/[0.055] bg-white p-7 shadow-[0_24px_80px_rgba(0,0,0,0.08)] sm:p-9">
        <div class="mb-7 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#292928] text-white shadow-lg shadow-black/10">
          <KeyRound :size="21" />
        </div>
        <h1 class="text-2xl font-semibold tracking-tight text-[#292928]">
          {{ isResetMode ? 'Crea una contraseña nueva' : 'Recupera tu contraseña' }}
        </h1>
        <p class="mt-2 text-sm leading-6 text-[#888887]">
          {{ isResetMode
            ? 'Elige una contraseña de al menos 8 caracteres para volver a ingresar.'
            : 'Te enviaremos un enlace para cambiar la contraseña asociada a tu cuenta.' }}
        </p>

        <form class="mt-7 space-y-5" @submit.prevent="submit">
          <label v-if="!isResetMode" class="block">
            <span class="mb-2 block text-[13px] font-semibold text-[#454544]">Correo electrónico</span>
            <div class="flex h-[52px] items-center gap-3 rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-4 transition focus-within:border-[#a3a3a2]">
              <Mail :size="18" class="shrink-0 text-[#a5a5a4]" />
              <input v-model="email" type="email" required autocomplete="email" placeholder="Tu correo electrónico" :disabled="loading" class="w-full bg-transparent text-sm outline-none placeholder:text-[#b8b8b7] disabled:opacity-50" />
            </div>
          </label>

          <template v-else>
            <label class="block">
              <span class="mb-2 block text-[13px] font-semibold text-[#454544]">Nueva contraseña</span>
              <div class="flex h-[52px] items-center gap-3 rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-4 focus-within:border-[#a3a3a2]">
                <Lock :size="18" class="shrink-0 text-[#a5a5a4]" />
                <input v-model="password" type="password" required minlength="8" maxlength="255" autocomplete="new-password" placeholder="Mínimo 8 caracteres" :disabled="loading" class="w-full bg-transparent text-sm outline-none placeholder:text-[#b8b8b7] disabled:opacity-50" />
              </div>
            </label>
            <label class="block">
              <span class="mb-2 block text-[13px] font-semibold text-[#454544]">Confirma la contraseña</span>
              <div class="flex h-[52px] items-center gap-3 rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-4 focus-within:border-[#a3a3a2]">
                <Lock :size="18" class="shrink-0 text-[#a5a5a4]" />
                <input v-model="confirmPassword" type="password" required minlength="8" maxlength="255" autocomplete="new-password" placeholder="Escríbela nuevamente" :disabled="loading" class="w-full bg-transparent text-sm outline-none placeholder:text-[#b8b8b7] disabled:opacity-50" />
              </div>
            </label>
          </template>

          <BaseAlert v-if="error" variant="destructive" title="No se pudo completar la solicitud" :description="error" />
          <BaseAlert v-if="success" variant="success" title="Revisa tu correo" :description="success" />

          <button type="submit" :disabled="loading || !!success" class="flex h-[54px] w-full items-center justify-center gap-2.5 rounded-2xl bg-[#292928] text-sm font-semibold text-white shadow-[0_10px_25px_rgba(41,41,40,0.16)] transition hover:bg-[#1f1f1e] disabled:cursor-not-allowed disabled:opacity-60">
            <Loader2 v-if="loading" :size="18" class="animate-spin" />
            <span>{{ loading ? 'Procesando…' : isResetMode ? 'Guardar contraseña' : 'Enviar enlace' }}</span>
          </button>
        </form>

        <button type="button" class="mt-6 flex w-full items-center justify-center gap-2 text-sm font-semibold text-[#575756] transition hover:text-[#292928]" @click="emit('go-login')">
          <ArrowLeft :size="16" /> Volver a iniciar sesión
        </button>
      </section>
    </div>
  </main>
</template>
