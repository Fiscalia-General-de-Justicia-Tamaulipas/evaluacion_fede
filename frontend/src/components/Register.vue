```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import {
  UserPlus,
  ArrowLeft,
  ArrowRight,
  Loader2,
  Mail,
  Lock,
  Eye,
  EyeOff,
  User,
  Building2,
  BadgeCheck,
  AlertCircle,
  ShieldCheck,
} from 'lucide-vue-next';

import { useAuth, type Institution } from '../lib/auth';

const emit = defineEmits<{
  (e: 'success'): void;
  (e: 'go-login'): void;
}>();

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

const showPassword = ref(false);
const showConfirmPassword = ref(false);

const curpInputRef = ref<HTMLInputElement | null>(null);

onMounted(async () => {
  try {
    institutions.value = await fetchInstitutions();
  } catch (e: any) {
    error.value =
      e?.message ||
      'No se pudo cargar el catálogo de instituciones.';
  }
});

function normalizeCurp() {
  form.value.curp = form.value.curp
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, '')
    .slice(0, 18);
}

async function onSubmit() {
  if (loading.value) return;

  error.value = '';

  const firstName = form.value.first_name.trim();
  const paternalSurname = form.value.paternal_surname.trim();
  const maternalSurname = form.value.maternal_surname.trim();
  const email = form.value.email.trim();
  const curp = form.value.curp.trim().toUpperCase();

  if (!firstName || !paternalSurname || !maternalSurname) {
    error.value = 'Completa tu nombre y apellidos.';
    return;
  }

  if (!email) {
    error.value = 'Ingresa tu correo electrónico.';
    return;
  }

  if (form.value.password.length < 8) {
    error.value = 'La contraseña debe tener al menos 8 caracteres.';
    return;
  }

  if (form.value.password !== form.value.confirm_password) {
    error.value = 'Las contraseñas no coinciden.';
    return;
  }

  if (!form.value.institution_id) {
    error.value = 'Selecciona tu institución.';
    return;
  }

  if (curp.length !== 18) {
    error.value = 'La CURP debe tener 18 caracteres.';
    return;
  }

  loading.value = true;

  try {
    await register({
      first_name: firstName,
      paternal_surname: paternalSurname,
      maternal_surname: maternalSurname,
      email,
      password: form.value.password,
      institution_id: form.value.institution_id,
      curp,
    });

    emit('success');
  } catch (e: any) {
    error.value =
      e?.message ||
      'No se pudo completar el registro.';
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <main
    class="relative min-h-screen overflow-hidden bg-[#f6f6f5] text-[#292928]"
  >
    <!-- ================================================================
         BACKGROUND
    ================================================================= -->

    <div class="pointer-events-none absolute inset-0 overflow-hidden">
      <div
        class="absolute -left-40 -top-40 h-[520px] w-[520px] rounded-full bg-[#575756]/[0.06] blur-3xl"
      />

      <div
        class="absolute -bottom-48 -right-40 h-[600px] w-[600px] rounded-full bg-[#878787]/[0.07] blur-3xl"
      />
    </div>

    <!-- ================================================================
         HEADER
    ================================================================= -->

    <header
      class="relative z-20 border-b border-black/[0.055] bg-white/80 backdrop-blur-xl"
    >
      <div
        class="mx-auto flex h-[76px] max-w-7xl items-center justify-between px-5 sm:px-8 lg:px-12"
      >
        <div class="flex items-center gap-3">
          <div
            class="flex h-11 items-center rounded-xl bg-white px-3.5 shadow-sm ring-1 ring-black/[0.04]"
          >
            <img
              src="/logo_fgjtam.png"
              alt="Fiscalía General de Justicia de Tamaulipas"
              class="h-7 w-auto object-contain"
            />
          </div>

          <div class="h-6 w-px bg-[#d8d8d7]" />

          <img
            src="/logo_fede.png"
            alt="FEDE"
            class="h-9 w-auto object-contain"
          />
        </div>

        <button
          type="button"
          @click="emit('go-login')"
          class="group inline-flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-semibold text-[#777776] transition hover:bg-black/[0.035] hover:text-[#292928]"
        >
          <ArrowLeft
            :size="15"
            class="transition-transform group-hover:-translate-x-0.5"
          />

          Volver a iniciar sesión
        </button>
      </div>
    </header>

    <!-- ================================================================
         CONTENT
    ================================================================= -->

    <main
      class="relative z-10 mx-auto flex w-full max-w-3xl justify-center px-5 py-10 sm:px-8 lg:py-14"
    >
      <div class="w-full">
        <!-- Intro -->

        <div class="mb-8 text-center">
          <div
            class="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#292928] text-white shadow-lg shadow-black/10"
          >
            <UserPlus
              :size="21"
              stroke-width="1.8"
            />
          </div>

          <p
            class="mb-2 text-[11px] font-bold uppercase tracking-[0.2em] text-[#a0a09f]"
          >
            Plataforma de capacitación
          </p>

          <h1
            class="text-[32px] font-semibold tracking-[-0.035em] text-[#292928] sm:text-[36px]"
          >
            Crear cuenta
          </h1>

          <p
            class="mx-auto mt-2.5 max-w-lg text-sm leading-6 text-[#888887]"
          >
            Registra tus datos para acceder a tu curso y continuar
            con tus actividades de capacitación.
          </p>
        </div>

        <!-- ============================================================
             CARD
        ============================================================= -->

        <div
          class="animate-register overflow-hidden rounded-[28px] border border-black/[0.055] bg-white shadow-[0_24px_80px_rgba(0,0,0,0.08)]"
        >
          <form
            class="p-6 sm:p-8 lg:p-10"
            @submit.prevent="onSubmit"
            novalidate
          >
            <!-- ========================================================
                 SECTION 1 — PERSONAL DATA
            ========================================================= -->

            <section>
              <div class="mb-6 flex items-start gap-4">
                <div
                  class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#f1f1f0] text-[#555554]"
                >
                  <User
                    :size="18"
                    stroke-width="1.8"
                  />
                </div>

                <div>
                  <h2
                    class="text-sm font-bold text-[#363635]"
                  >
                    Datos personales
                  </h2>

                  <p
                    class="mt-1 text-xs leading-5 text-[#999998]"
                  >
                    Ingresa tu nombre tal como aparece en tu documentación.
                  </p>
                </div>
              </div>

              <div class="space-y-5">
                <!-- Nombre -->

                <label class="block">
                  <span
                    class="mb-2 block text-[13px] font-semibold text-[#454544]"
                  >
                    Nombre(s)
                  </span>

                  <input
                    v-model="form.first_name"
                    type="text"
                    required
                    autocomplete="given-name"
                    placeholder="Ingresa tu nombre"
                    :disabled="loading"
                    class="h-[52px] w-full rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-4 text-sm font-medium text-[#292928] outline-none transition-all placeholder:text-[#b8b8b7] hover:border-[#cfcfce] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035] disabled:cursor-not-allowed disabled:opacity-50"
                  />
                </label>

                <!-- Apellidos -->

                <div class="grid gap-5 md:grid-cols-2">
                  <label class="block">
                    <span
                      class="mb-2 block text-[13px] font-semibold text-[#454544]"
                    >
                      Apellido paterno
                    </span>

                    <input
                      v-model="form.paternal_surname"
                      type="text"
                      required
                      autocomplete="family-name"
                      placeholder="Apellido paterno"
                      :disabled="loading"
                      class="h-[52px] w-full rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-4 text-sm font-medium text-[#292928] outline-none transition-all placeholder:text-[#b8b8b7] hover:border-[#cfcfce] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035] disabled:cursor-not-allowed disabled:opacity-50"
                    />
                  </label>

                  <label class="block">
                    <span
                      class="mb-2 block text-[13px] font-semibold text-[#454544]"
                    >
                      Apellido materno
                    </span>

                    <input
                      v-model="form.maternal_surname"
                      type="text"
                      required
                      placeholder="Apellido materno"
                      :disabled="loading"
                      class="h-[52px] w-full rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-4 text-sm font-medium text-[#292928] outline-none transition-all placeholder:text-[#b8b8b7] hover:border-[#cfcfce] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035] disabled:cursor-not-allowed disabled:opacity-50"
                    />
                  </label>
                </div>
              </div>
            </section>

            <!-- Divider -->

            <div class="my-9 h-px bg-[#eeeeed]" />

            <!-- ========================================================
                 SECTION 2 — ACCOUNT
            ========================================================= -->

            <section>
              <div class="mb-6 flex items-start gap-4">
                <div
                  class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#f1f1f0] text-[#555554]"
                >
                  <Lock
                    :size="18"
                    stroke-width="1.8"
                  />
                </div>

                <div>
                  <h2
                    class="text-sm font-bold text-[#363635]"
                  >
                    Datos de acceso
                  </h2>

                  <p
                    class="mt-1 text-xs leading-5 text-[#999998]"
                  >
                    Utilizarás estos datos para ingresar a la plataforma.
                  </p>
                </div>
              </div>

              <div class="space-y-5">
                <!-- Email -->

                <label class="block">
                  <span
                    class="mb-2 block text-[13px] font-semibold text-[#454544]"
                  >
                    Correo electrónico
                  </span>

                  <div
                    class="group flex h-[52px] items-center gap-3 rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-4 transition-all duration-200 hover:border-[#cfcfce] focus-within:border-[#4a4a49] focus-within:bg-white focus-within:ring-4 focus-within:ring-black/[0.035]"
                  >
                    <Mail
                      :size="18"
                      stroke-width="1.8"
                      class="shrink-0 text-[#a5a5a4] transition-colors group-focus-within:text-[#555554]"
                    />

                    <input
                      v-model="form.email"
                      type="email"
                      required
                      autocomplete="email"
                      placeholder="Tu correo electrónico"
                      :disabled="loading"
                      class="w-full bg-transparent text-sm font-medium text-[#292928] outline-none placeholder:text-[#b8b8b7] disabled:opacity-50"
                    />
                  </div>
                </label>

                <!-- Passwords -->

                <div class="grid gap-5 md:grid-cols-2">
                  <label class="block">
                    <span
                      class="mb-2 block text-[13px] font-semibold text-[#454544]"
                    >
                      Contraseña
                    </span>

                    <div
                      class="group flex h-[52px] items-center gap-3 rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-4 transition-all duration-200 hover:border-[#cfcfce] focus-within:border-[#4a4a49] focus-within:bg-white focus-within:ring-4 focus-within:ring-black/[0.035]"
                    >
                      <Lock
                        :size="18"
                        stroke-width="1.8"
                        class="shrink-0 text-[#a5a5a4]"
                      />

                      <input
                        v-model="form.password"
                        :type="showPassword ? 'text' : 'password'"
                        required
                        minlength="8"
                        autocomplete="new-password"
                        placeholder="Mínimo 8 caracteres"
                        :disabled="loading"
                        class="w-full bg-transparent text-sm font-medium text-[#292928] outline-none placeholder:text-[#b8b8b7] disabled:opacity-50"
                      />

                      <button
                        type="button"
                        :disabled="loading"
                        @click="showPassword = !showPassword"
                        :aria-label="
                          showPassword
                            ? 'Ocultar contraseña'
                            : 'Mostrar contraseña'
                        "
                        class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[#a0a09f] transition hover:bg-black/[0.04] hover:text-[#444443]"
                      >
                        <EyeOff
                          v-if="showPassword"
                          :size="18"
                        />

                        <Eye
                          v-else
                          :size="18"
                        />
                      </button>
                    </div>
                  </label>

                  <label class="block">
                    <span
                      class="mb-2 block text-[13px] font-semibold text-[#454544]"
                    >
                      Confirmar contraseña
                    </span>

                    <div
                      class="group flex h-[52px] items-center gap-3 rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-4 transition-all duration-200 hover:border-[#cfcfce] focus-within:border-[#4a4a49] focus-within:bg-white focus-within:ring-4 focus-within:ring-black/[0.035]"
                    >
                      <Lock
                        :size="18"
                        stroke-width="1.8"
                        class="shrink-0 text-[#a5a5a4]"
                      />

                      <input
                        v-model="form.confirm_password"
                        :type="
                          showConfirmPassword
                            ? 'text'
                            : 'password'
                        "
                        required
                        minlength="8"
                        autocomplete="new-password"
                        placeholder="Repite tu contraseña"
                        :disabled="loading"
                        class="w-full bg-transparent text-sm font-medium text-[#292928] outline-none placeholder:text-[#b8b8b7] disabled:opacity-50"
                      />

                      <button
                        type="button"
                        :disabled="loading"
                        @click="
                          showConfirmPassword =
                            !showConfirmPassword
                        "
                        :aria-label="
                          showConfirmPassword
                            ? 'Ocultar contraseña'
                            : 'Mostrar contraseña'
                        "
                        class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[#a0a09f] transition hover:bg-black/[0.04] hover:text-[#444443]"
                      >
                        <EyeOff
                          v-if="showConfirmPassword"
                          :size="18"
                        />

                        <Eye
                          v-else
                          :size="18"
                        />
                      </button>
                    </div>
                  </label>
                </div>

                <p class="text-[11px] leading-5 text-[#aaa9a8]">
                  Tu contraseña debe contener al menos 8 caracteres.
                </p>
              </div>
            </section>

            <!-- Divider -->

            <div class="my-9 h-px bg-[#eeeeed]" />

            <!-- ========================================================
                 SECTION 3 — INSTITUTION
            ========================================================= -->

            <section>
              <div class="mb-6 flex items-start gap-4">
                <div
                  class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#f1f1f0] text-[#555554]"
                >
                  <Building2
                    :size="18"
                    stroke-width="1.8"
                  />
                </div>

                <div>
                  <h2
                    class="text-sm font-bold text-[#363635]"
                  >
                    Información de registro
                  </h2>

                  <p
                    class="mt-1 text-xs leading-5 text-[#999998]"
                  >
                    Completa la información necesaria para tu registro.
                  </p>
                </div>
              </div>

              <div class="space-y-5">
                <!-- Institution -->

                <label class="block">
                  <span
                    class="mb-2 block text-[13px] font-semibold text-[#454544]"
                  >
                    Institución
                  </span>

                  <div class="relative">
                    <Building2
                      :size="18"
                      class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[#a5a5a4]"
                    />

                    <select
                      v-model="form.institution_id"
                      required
                      :disabled="loading"
                      class="h-[52px] w-full appearance-none rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-11 pr-10 text-sm font-medium text-[#292928] outline-none transition-all hover:border-[#cfcfce] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035] disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      <option
                        :value="null"
                        disabled
                      >
                        Selecciona tu institución
                      </option>

                      <option
                        v-for="inst in institutions"
                        :key="inst.id"
                        :value="inst.id"
                      >
                        {{ inst.name }}
                      </option>
                    </select>

                    <ArrowRight
                      :size="16"
                      class="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 rotate-90 text-[#aaa9a8]"
                    />
                  </div>
                </label>

                <!-- CURP -->

                <label class="block">
                  <span
                    class="mb-2 block text-[13px] font-semibold text-[#454544]"
                  >
                    CURP
                  </span>

                  <div
                    class="group flex h-[52px] items-center gap-3 rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-4 transition-all duration-200 hover:border-[#cfcfce] focus-within:border-[#4a4a49] focus-within:bg-white focus-within:ring-4 focus-within:ring-black/[0.035]"
                  >
                    <BadgeCheck
                      :size="18"
                      stroke-width="1.8"
                      class="shrink-0 text-[#a5a5a4]"
                    />

                    <input
                      ref="curpInputRef"
                      v-model="form.curp"
                      type="text"
                      required
                      maxlength="18"
                      minlength="18"
                      autocomplete="off"
                      spellcheck="false"
                      placeholder="XXXX000000XXXXXX00"
                      :disabled="loading"
                      @input="normalizeCurp"
                      class="w-full bg-transparent text-sm font-semibold uppercase tracking-[0.12em] text-[#292928] outline-none placeholder:font-normal placeholder:tracking-normal placeholder:text-[#b8b8b7] disabled:opacity-50"
                    />

                    <span
                      class="shrink-0 text-[10px] font-semibold tabular-nums text-[#aaa9a8]"
                    >
                      {{ form.curp.length }}/18
                    </span>
                  </div>

                  <p
                    class="mt-2 text-[11px] leading-5 text-[#aaa9a8]"
                  >
                    Ingresa los 18 caracteres de tu CURP.
                  </p>
                </label>
              </div>
            </section>

            <!-- ========================================================
                 ERROR
            ========================================================= -->

            <Transition name="fade">
              <div
                v-if="error"
                class="mt-8 flex items-start gap-3 rounded-2xl border border-red-100 bg-red-50 px-4 py-3.5 text-sm text-red-700"
                role="alert"
                aria-live="assertive"
              >
                <AlertCircle
                  :size="17"
                  class="mt-0.5 shrink-0"
                />

                <span class="leading-5">
                  {{ error }}
                </span>
              </div>
            </Transition>

            <!-- ========================================================
                 SUBMIT
            ========================================================= -->

            <div class="mt-8">
              <button
                type="submit"
                :disabled="loading"
                class="group relative flex h-[54px] w-full items-center justify-center gap-2.5 overflow-hidden rounded-2xl bg-[#292928] text-sm font-semibold text-white shadow-[0_10px_25px_rgba(41,41,40,0.16)] transition-all duration-200 hover:-translate-y-0.5 hover:bg-[#1f1f1e] hover:shadow-[0_14px_30px_rgba(41,41,40,0.2)] active:translate-y-0 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
              >
                <span
                  class="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/[0.08] to-transparent transition-transform duration-700 group-hover:translate-x-full"
                />

                <Loader2
                  v-if="loading"
                  :size="18"
                  class="relative animate-spin"
                />

                <UserPlus
                  v-else
                  :size="18"
                  stroke-width="1.9"
                  class="relative transition-transform duration-200 group-hover:-translate-y-0.5"
                />

                <span class="relative">
                  {{
                    loading
                      ? 'Creando cuenta…'
                      : 'Crear cuenta'
                  }}
                </span>

                <ArrowRight
                  v-if="!loading"
                  :size="16"
                  class="relative opacity-50 transition-transform duration-200 group-hover:translate-x-0.5"
                />
              </button>
            </div>

            <!-- Security -->

            <div
              class="mt-6 flex items-center justify-center gap-2 text-center text-[11px] leading-5 text-[#aaa9a8]"
            >
              <ShieldCheck
                :size="14"
                class="shrink-0"
              />

              <span>
                Tu información se mantiene protegida.
              </span>
            </div>
          </form>

          <!-- Bottom -->

          <div
            class="border-t border-[#eeeeed] bg-[#fafafa] px-6 py-5 text-center sm:px-8"
          >
            <p class="text-xs text-[#999998]">
              ¿Ya tienes una cuenta?
            </p>

            <button
              type="button"
              :disabled="loading"
              @click="emit('go-login')"
              class="mt-1.5 inline-flex items-center gap-1.5 text-sm font-semibold text-[#444443] transition hover:text-[#292928] disabled:opacity-50"
            >
              Iniciar sesión

              <ArrowRight
                :size="14"
                class="transition-transform group-hover:translate-x-0.5"
              />
            </button>
          </div>
        </div>

        <!-- Footer -->

        <div
          class="mt-7 flex items-center justify-center gap-3 text-[10px] font-medium uppercase tracking-[0.12em] text-[#b2b2b1]"
        >
          <span>FEDE</span>

          <span class="h-1 w-1 rounded-full bg-[#c8c8c7]" />

          <span>FGJ Tamaulipas</span>
        </div>
      </div>
    </main>
  </main>
</template>

<style scoped>
@keyframes register-in {
  from {
    opacity: 0;
    transform: translateY(18px) scale(0.985);
  }

  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.animate-register {
  animation: register-in 0.55s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.fade-enter-active,
.fade-leave-active {
  transition:
    opacity 0.18s ease,
    transform 0.18s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

@media (prefers-reduced-motion: reduce) {
  .animate-register {
    animation: none;
  }

  .fade-enter-active,
  .fade-leave-active {
    transition: none;
  }
}
</style>
```
