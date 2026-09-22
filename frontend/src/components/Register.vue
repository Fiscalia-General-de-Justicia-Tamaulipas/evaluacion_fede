<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { UserPlus, ArrowLeft, Loader2 } from 'lucide-vue-next';
import { useAuth, type Institution } from '../lib/auth';

const emit = defineEmits<{ (e: 'success'): void; (e: 'go-login'): void }>();

const { register, fetchInstitutions } = useAuth();

const form = ref({
  first_name: '',
  paternal_surname: '',
  maternal_surname: '',
  email: '',
  password: '',
  confirm_password: '',
  institution_id: null as number | null,
  curp: '',
});

const institutions = ref<Institution[]>([]);
const loading = ref(false);
const error = ref('');

onMounted(async () => {
  try {
    institutions.value = await fetchInstitutions();
  } catch (e: any) {
    error.value = e.message || 'No se pudo cargar el catálogo de instituciones.';
  }
});

async function onSubmit() {
  error.value = '';

  if (form.value.password !== form.value.confirm_password) {
    error.value = 'Las contraseñas no coinciden.';
    return;
  }

  if (form.value.curp.trim().length !== 18) {
    error.value = 'La CURP debe tener 18 caracteres.';
    return;
  }

  if (!form.value.institution_id) {
    error.value = 'Selecciona tu institución.';
    return;
  }

  loading.value = true;
  try {
    await register({
      first_name: form.value.first_name.trim(),
      paternal_surname: form.value.paternal_surname.trim(),
      maternal_surname: form.value.maternal_surname.trim(),
      email: form.value.email.trim(),
      password: form.value.password,
      institution_id: form.value.institution_id,
      curp: form.value.curp.trim().toUpperCase(),
    });
    emit('success');
  } catch (e: any) {
    error.value = e.message || 'No se pudo completar el registro.';
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="min-h-screen bg-[#f4f4f3] text-[#575756]">
    <header class="border-b border-[#dadada] bg-white/95 backdrop-blur sticky top-0 z-20">
      <div class="mx-auto flex max-w-6xl items-center gap-4 px-5 py-4">
        <img src="/logo_fgjtam.png" alt="Logo FGJ Tamaulipas" class="h-14 w-auto object-contain opacity-95" />
        <div class="ml-auto flex items-center gap-3">
          <img src="/logo_fede.png" alt="Logo FEDE" class="h-15 w-auto object-contain opacity-95" />
        </div>
      </div>
    </header>

    <main class="mx-auto flex max-w-2xl flex-col items-center px-5 py-10">
      <button type="button" @click="emit('go-login')" class="mb-6 self-start inline-flex items-center gap-2 text-sm font-bold text-[#878787] hover:text-[#575756]">
        <ArrowLeft :size="16" /> Volver al inicio de sesión
      </button>

      <div class="w-full rounded-3xl border border-[#dadada] bg-white p-7 shadow-xl shadow-black/5 md:p-10">
        <div class="mb-8 flex flex-col items-center text-center">
          <div class="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#575756] text-white shadow-lg">
            <UserPlus :size="24" />
          </div>
          <h2 class="mt-4 text-3xl font-black">Crear cuenta</h2>
          <p class="mt-2 text-sm text-[#878787]">
            Registra tus datos institucionales para acceder a la capacitación.
          </p>
        </div>

        <form class="space-y-5" @submit.prevent="onSubmit">
          <label class="block">
            <span class="mb-2 block text-sm font-semibold">Nombre(s)</span>
            <input v-model="form.first_name" required
              class="w-full rounded-xl border border-[#dadada] bg-[#fafafa] px-4 py-3 outline-none focus:border-[#878787] focus:ring-2 focus:ring-[#dadada]" />
          </label>

          <div class="grid gap-5 md:grid-cols-2">
            <label class="block">
              <span class="mb-2 block text-sm font-semibold">Apellido paterno</span>
              <input v-model="form.paternal_surname" required
                class="w-full rounded-xl border border-[#dadada] bg-[#fafafa] px-4 py-3 outline-none focus:border-[#878787]" />
            </label>
            <label class="block">
              <span class="mb-2 block text-sm font-semibold">Apellido materno</span>
              <input v-model="form.maternal_surname" required
                class="w-full rounded-xl border border-[#dadada] bg-[#fafafa] px-4 py-3 outline-none focus:border-[#878787]" />
            </label>
          </div>

          <label class="block">
            <span class="mb-2 block text-sm font-semibold">Correo electrónico</span>
            <input v-model="form.email" type="email" required autocomplete="username"
              class="w-full rounded-xl border border-[#dadada] bg-[#fafafa] px-4 py-3 outline-none focus:border-[#878787]" />
          </label>

          <div class="grid gap-5 md:grid-cols-2">
            <label class="block">
              <span class="mb-2 block text-sm font-semibold">Contraseña</span>
              <input v-model="form.password" type="password" required minlength="8" autocomplete="new-password"
                class="w-full rounded-xl border border-[#dadada] bg-[#fafafa] px-4 py-3 outline-none focus:border-[#878787]" />
            </label>
            <label class="block">
              <span class="mb-2 block text-sm font-semibold">Confirmar contraseña</span>
              <input v-model="form.confirm_password" type="password" required minlength="8" autocomplete="new-password"
                class="w-full rounded-xl border border-[#dadada] bg-[#fafafa] px-4 py-3 outline-none focus:border-[#878787]" />
            </label>
          </div>

          <label class="block">
            <span class="mb-2 block text-sm font-semibold">Institución</span>
            <select v-model="form.institution_id" required
              class="w-full rounded-xl border border-[#dadada] bg-[#fafafa] px-4 py-3 outline-none focus:border-[#878787]">
              <option :value="null" disabled>Selecciona tu institución</option>
              <option v-for="inst in institutions" :key="inst.id" :value="inst.id">{{ inst.name }}</option>
            </select>
          </label>

          <label class="block">
            <span class="mb-2 block text-sm font-semibold">CURP</span>
            <input v-model="form.curp" required maxlength="18" minlength="18"
              class="w-full rounded-xl border border-[#dadada] bg-[#fafafa] px-4 py-3 uppercase tracking-wider outline-none focus:border-[#878787]"
              placeholder="XXXX000000XXXXXX00" />
          </label>

          <p v-if="error" class="rounded-lg bg-red-50 px-3 py-2 text-sm font-medium text-red-600">
            {{ error }}
          </p>

          <button type="submit" :disabled="loading"
            class="flex w-full items-center justify-center gap-2 rounded-xl bg-[#575756] py-3.5 text-sm font-bold text-white disabled:cursor-not-allowed disabled:opacity-50">
            <Loader2 v-if="loading" :size="18" class="animate-spin" />
            {{ loading ? 'Creando cuenta…' : 'Crear cuenta' }}
          </button>
        </form>
      </div>
    </main>
  </div>
</template>