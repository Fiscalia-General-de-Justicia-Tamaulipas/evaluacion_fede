<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
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
  MapPin,
  VenusAndMars,
  BriefcaseBusiness,
  GraduationCap,
  Accessibility,
  UsersRound,
} from 'lucide-vue-next';
import { useAuth, type Institution } from '../lib/auth';

type CatalogItem = {
  id: number;
  name: string;
};

type Municipality = {
  id: number;
  name: string;
  state_id: number;
  is_other?: boolean;
};

type StateItem = {
  id: number;
  name: string;
};

const emit = defineEmits<{
  (e: 'success'): void;
  (e: 'go-login'): void;
}>();

const {
  register,
} = useAuth();

const form = ref({
  first_name: '',
  paternal_surname: '',
  maternal_surname: '',
  email: '',
  password: '',
  confirm_password: '',
  curp: '',

  municipality_id: null as number | null,
  municipality_other: '',
  municipality_other_state: '',

  gender_id: null as number | null,
  gender_other: '',

  age_range_id: null as number | null,

  occupation_id: null as number | null,
  occupation_other: '',

  sector_id: null as number | null,

  indigenous_id: null as number | null,
  afro_mexican_id: null as number | null,
  disability_id: null as number | null,
  lgbtttiq_id: null as number | null,

  education_level_id: null as number | null,
});

const states = ref<StateItem[]>([]);
const municipalities = ref<Municipality[]>([]);
const genders = ref<CatalogItem[]>([]);
const ageRanges = ref<CatalogItem[]>([]);
const occupations = ref<CatalogItem[]>([]);
const sectors = ref<CatalogItem[]>([]);
const yesNoOptions = ref<CatalogItem[]>([]);
const educationLevels = ref<CatalogItem[]>([]);

const loading = ref(false);
const loadingCatalogs = ref(true);
const error = ref('');
const showPassword = ref(false);
const showConfirmPassword = ref(false);

const curpInputRef = ref<HTMLInputElement | null>(null);

const tamaulipasState = computed(() =>
  states.value.find((state) => state.name.toLowerCase() === 'tamaulipas')
);

const selectedMunicipality = computed(() =>
  municipalities.value.find((municipality) => municipality.id === form.value.municipality_id)
);

const isOtherMunicipality = computed(() =>
  selectedMunicipality.value?.is_other === true
);

const selectedGender = computed(() =>
  genders.value.find((item) => item.id === form.value.gender_id)
);

const isOtherGender = computed(() =>
  selectedGender.value?.name.toLowerCase() === 'otro'
);

const selectedOccupation = computed(() =>
  occupations.value.find((item) => item.id === form.value.occupation_id)
);

const isOtherOccupation = computed(() =>
  selectedOccupation.value?.name.toLowerCase() === 'otro'
);

const catalogError = computed(() =>
  loadingCatalogs.value
    ? ''
    : !states.value.length ||
      !municipalities.value.length ||
      !genders.value.length ||
      !ageRanges.value.length ||
      !occupations.value.length ||
      !sectors.value.length ||
      !yesNoOptions.value.length ||
      !educationLevels.value.length
      ? 'No se pudieron cargar todos los catálogos. Recarga la página e inténtalo nuevamente.'
      : ''
);

async function loadCatalogs() {
  loadingCatalogs.value = true;
  error.value = '';

  try {
    const [
      statesCatalog,
      municipalitiesCatalog,
      gendersCatalog,
      ageRangesCatalog,
      occupationsCatalog,
      sectorsCatalog,
      yesNoCatalog,
      educationCatalog,
    ] = await Promise.all([
      fetchJson<StateItem[]>('/api/catalogs/states'),
      fetchJson<Municipality[]>('/api/catalogs/municipalities'),
      fetchJson<CatalogItem[]>('/api/catalogs/genders'),
      fetchJson<CatalogItem[]>('/api/catalogs/age-ranges'),
      fetchJson<CatalogItem[]>('/api/catalogs/occupations'),
      fetchJson<CatalogItem[]>('/api/catalogs/sectors'),
      fetchJson<CatalogItem[]>('/api/catalogs/yes-no'),
      fetchJson<CatalogItem[]>('/api/catalogs/education-levels'),
    ]);

    //institutions.value = institutionCatalog;
    states.value = statesCatalog;
    genders.value = gendersCatalog;
    ageRanges.value = ageRangesCatalog;
    occupations.value = occupationsCatalog;
    sectors.value = sectorsCatalog;
    yesNoOptions.value = yesNoCatalog;
    educationLevels.value = educationCatalog;

    const tamaulipas = statesCatalog.find(
      (state) => state.name.toLowerCase() === 'tamaulipas'
    );

    if (tamaulipas) {
      municipalities.value = await fetchMunicipalities(tamaulipas.id);
    } else {
      municipalities.value = municipalitiesCatalog.filter(
        (municipality) => municipality.state_id === 0
      );
    }
  } catch (e: any) {
    error.value =
      e?.message ||
      'No se pudieron cargar los catálogos necesarios para el registro.';
  } finally {
    loadingCatalogs.value = false;
  }
}

const API_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

async function fetchJson<T>(url: string): Promise<T> {
  const endpoint = `${API_URL}${url}`;

  const response = await fetch(endpoint, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    let message = `Error ${response.status}`;

    try {
      const body = await response.json();

      message =
        body?.detail ||
        body?.message ||
        body?.error ||
        message;
    } catch {
      // Mantener mensaje HTTP.
    }

    throw new Error(`${message} (${endpoint})`);
  }

  return response.json();
}
async function fetchMunicipalities(stateId: number): Promise<Municipality[]> {
  return fetchJson<Municipality[]>(
    `/api/catalogs/municipalities?state_id=${encodeURIComponent(stateId)}`
  );
}

onMounted(loadCatalogs);

watch(
  () => form.value.municipality_id,
  () => {
    if (!isOtherMunicipality.value) {
      form.value.municipality_other = '';
      form.value.municipality_other_state = '';
    }
  }
);

watch(
  () => form.value.gender_id,
  () => {
    if (!isOtherGender.value) {
      form.value.gender_other = '';
    }
  }
);

watch(
  () => form.value.occupation_id,
  () => {
    if (!isOtherOccupation.value) {
      form.value.occupation_other = '';
    }
  }
);

function normalizeCurp() {
  form.value.curp = form.value.curp
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, '')
    .slice(0, 18);
}

function clearError() {
  error.value = '';
}

function validateEmail(email: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function validateForm() {
  const firstName = form.value.first_name.trim();
  const paternalSurname = form.value.paternal_surname.trim();
  const maternalSurname = form.value.maternal_surname.trim();
  const email = form.value.email.trim();
  const curp = form.value.curp.trim().toUpperCase();

  if (!firstName || !paternalSurname || !maternalSurname) {
    return 'Completa tu nombre y apellidos.';
  }

  if (!email) {
    return 'Ingresa tu correo electrónico personal.';
  }

  if (!validateEmail(email)) {
    return 'Ingresa un correo electrónico válido.';
  }

  if (form.value.password.length < 8) {
    return 'La contraseña debe tener al menos 8 caracteres.';
  }

  if (form.value.password !== form.value.confirm_password) {
    return 'Las contraseñas no coinciden.';
  }
/*
  if (!form.value.institution_id) {
    return 'Selecciona tu institución.';
  }
*/
  if (curp.length !== 18) {
    return 'La CURP debe tener 18 caracteres.';
  }

  if (!form.value.municipality_id) {
    return 'Selecciona tu municipio.';
  }

  if (isOtherMunicipality.value) {
    if (!form.value.municipality_other.trim()) {
      return 'Escribe el nombre del municipio.';
    }

    if (!form.value.municipality_other_state.trim()) {
      return 'Escribe el estado del municipio.';
    }
  }

  if (!form.value.gender_id) {
    return 'Selecciona tu género.';
  }

  if (isOtherGender.value && !form.value.gender_other.trim()) {
    return 'Especifica tu género.';
  }

  if (!form.value.age_range_id) {
    return 'Selecciona tu rango de edad.';
  }

  if (!form.value.occupation_id) {
    return 'Selecciona tu ocupación.';
  }

  if (isOtherOccupation.value && !form.value.occupation_other.trim()) {
    return 'Especifica tu ocupación.';
  }

  if (!form.value.sector_id) {
    return 'Selecciona la institución o sector al que perteneces.';
  }

  if (!form.value.indigenous_id) {
    return 'Indica si te auto adscribes como persona indígena.';
  }

  if (!form.value.afro_mexican_id) {
    return 'Indica si te auto adscribes como persona afromexicana.';
  }

  if (!form.value.disability_id) {
    return 'Indica si tienes alguna discapacidad.';
  }

  if (!form.value.lgbtttiq_id) {
    return 'Indica si te identificas como parte de la comunidad LGBTTTIQ+.';
  }

  if (!form.value.education_level_id) {
    return 'Selecciona tu grado de estudios.';
  }

  return '';
}

async function onSubmit() {
  if (loading.value || loadingCatalogs.value) return;

  error.value = '';

  const validationError = validateForm();

  if (validationError) {
    error.value = validationError;
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
      curp: form.value.curp.trim().toUpperCase(),

      municipality_id: form.value.municipality_id,
      municipality_other: isOtherMunicipality.value
        ? form.value.municipality_other.trim()
        : null,
      municipality_other_state: isOtherMunicipality.value
        ? form.value.municipality_other_state.trim()
        : null,

      gender_id: form.value.gender_id,
      gender_other: isOtherGender.value
        ? form.value.gender_other.trim()
        : null,

      age_range_id: form.value.age_range_id,

      occupation_id: form.value.occupation_id,
      occupation_other: isOtherOccupation.value
        ? form.value.occupation_other.trim()
        : null,

      sector_id: form.value.sector_id,

      indigenous_id: form.value.indigenous_id,
      afro_mexican_id: form.value.afro_mexican_id,
      disability_id: form.value.disability_id,
      lgbtttiq_id: form.value.lgbtttiq_id,

      education_level_id: form.value.education_level_id,
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
  <main class="relative min-h-screen overflow-hidden bg-[#f6f6f5] text-[#292928]">
    <!-- Background -->
    <div class="pointer-events-none absolute inset-0 overflow-hidden">
      <div
        class="absolute -left-40 -top-40 h-[520px] w-[520px] rounded-full bg-[#575756]/[0.06] blur-3xl"
      />
      <div
        class="absolute -bottom-48 -right-40 h-[600px] w-[600px] rounded-full bg-[#878787]/[0.07] blur-3xl"
      />
    </div>

    <!-- Header -->
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
          :disabled="loading"
          @click="emit('go-login')"
          class="group inline-flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-semibold text-[#777776] transition hover:bg-black/[0.035] hover:text-[#292928] disabled:opacity-50"
        >
          <ArrowLeft
            :size="15"
            class="transition-transform group-hover:-translate-x-0.5"
          />
          Volver a iniciar sesión
        </button>
      </div>
    </header>

    <!-- Content -->
    <main
      class="relative z-10 mx-auto flex w-full max-w-4xl justify-center px-5 py-10 sm:px-8 lg:py-14"
    >
      <div class="w-full">
        <!-- Intro -->
        <div class="mb-8 text-center">
          <div
            class="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#292928] text-white shadow-lg shadow-black/10"
          >
            <UserPlus :size="21" stroke-width="1.8" />
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
            Registra tus datos para acceder a tu curso y continuar con tus
            actividades de capacitación.
          </p>
        </div>

        <!-- Card -->
        <div
          class="animate-register overflow-hidden rounded-[28px] border border-black/[0.055] bg-white shadow-[0_24px_80px_rgba(0,0,0,0.08)]"
        >
          <form
            class="p-6 sm:p-8 lg:p-10"
            @submit.prevent="onSubmit"
            novalidate
          >
            <!-- Personal -->
            <section>
              <div class="mb-6 flex items-start gap-4">
                <div
                  class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#f1f1f0] text-[#555554]"
                >
                  <User :size="18" stroke-width="1.8" />
                </div>
                <div>
                  <h2 class="text-sm font-bold text-[#363635]">
                    Datos personales
                  </h2>
                  <p class="mt-1 text-xs leading-5 text-[#999998]">
                    Ingresa tu nombre y los datos generales solicitados.
                  </p>
                </div>
              </div>

              <div class="space-y-5">
                <label class="block">
                  <span class="mb-2 block text-[13px] font-semibold text-[#454544]">
                    Nombre(s)
                  </span>
                  <input
                    v-model="form.first_name"
                    type="text"
                    required
                    autocomplete="given-name"
                    placeholder="Ingresa tu nombre"
                    :disabled="loading"
                    @input="clearError"
                    class="h-[52px] w-full rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-4 text-sm font-medium text-[#292928] outline-none transition-all placeholder:text-[#b8b8b7] hover:border-[#cfcfce] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035] disabled:cursor-not-allowed disabled:opacity-50"
                  />
                </label>

                <div class="grid gap-5 md:grid-cols-2">
                  <label class="block">
                    <span class="mb-2 block text-[13px] font-semibold text-[#454544]">
                      Apellido paterno
                    </span>
                    <input
                      v-model="form.paternal_surname"
                      type="text"
                      required
                      autocomplete="family-name"
                      placeholder="Apellido paterno"
                      :disabled="loading"
                      @input="clearError"
                      class="h-[52px] w-full rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-4 text-sm font-medium text-[#292928] outline-none transition-all placeholder:text-[#b8b8b7] hover:border-[#cfcfce] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035] disabled:cursor-not-allowed disabled:opacity-50"
                    />
                  </label>

                  <label class="block">
                    <span class="mb-2 block text-[13px] font-semibold text-[#454544]">
                      Apellido materno
                    </span>
                    <input
                      v-model="form.maternal_surname"
                      type="text"
                      required
                      placeholder="Apellido materno"
                      :disabled="loading"
                      @input="clearError"
                      class="h-[52px] w-full rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-4 text-sm font-medium text-[#292928] outline-none transition-all placeholder:text-[#b8b8b7] hover:border-[#cfcfce] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035] disabled:cursor-not-allowed disabled:opacity-50"
                    />
                  </label>
                </div>
              </div>
            </section>

            <div class="my-9 h-px bg-[#eeeeed]" />

            <!-- Account -->
            <section>
              <div class="mb-6 flex items-start gap-4">
                <div
                  class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#f1f1f0] text-[#555554]"
                >
                  <Lock :size="18" stroke-width="1.8" />
                </div>
                <div>
                  <h2 class="text-sm font-bold text-[#363635]">
                    Datos de acceso
                  </h2>
                  <p class="mt-1 text-xs leading-5 text-[#999998]">
                    Utilizarás estos datos para ingresar a la plataforma.
                  </p>
                </div>
              </div>

              <div class="space-y-5">
                <label class="block">
                  <span class="mb-2 block text-[13px] font-semibold text-[#454544]">
                    Correo electrónico personal
                  </span>
                  <div
                    class="group flex h-[52px] items-center gap-3 rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-4 transition-all duration-200 hover:border-[#cfcfce] focus-within:border-[#4a4a49] focus-within:bg-white focus-within:ring-4 focus-within:ring-black/[0.035]"
                  >
                    <Mail
                      :size="18"
                      stroke-width="1.8"
                      class="shrink-0 text-[#a5a5a4] group-focus-within:text-[#555554]"
                    />
                    <input
                      v-model="form.email"
                      type="email"
                      required
                      autocomplete="email"
                      placeholder="Tu correo electrónico personal"
                      :disabled="loading"
                      @input="clearError"
                      class="w-full bg-transparent text-sm font-medium text-[#292928] outline-none placeholder:text-[#b8b8b7] disabled:opacity-50"
                    />
                  </div>
                </label>

                <div class="grid gap-5 md:grid-cols-2">
                  <label class="block">
                    <span class="mb-2 block text-[13px] font-semibold text-[#454544]">
                      Contraseña
                    </span>
                    <div
                      class="group flex h-[52px] items-center gap-3 rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-4 transition-all duration-200 hover:border-[#cfcfce] focus-within:border-[#4a4a49] focus-within:bg-white focus-within:ring-4 focus-within:ring-black/[0.035]"
                    >
                      <Lock :size="18" class="shrink-0 text-[#a5a5a4]" />
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
                        :aria-label="showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'"
                        class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[#a0a09f] transition hover:bg-black/[0.04] hover:text-[#444443]"
                      >
                        <EyeOff v-if="showPassword" :size="18" />
                        <Eye v-else :size="18" />
                      </button>
                    </div>
                  </label>

                  <label class="block">
                    <span class="mb-2 block text-[13px] font-semibold text-[#454544]">
                      Confirmar contraseña
                    </span>
                    <div
                      class="group flex h-[52px] items-center gap-3 rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-4 transition-all duration-200 hover:border-[#cfcfce] focus-within:border-[#4a4a49] focus-within:bg-white focus-within:ring-4 focus-within:ring-black/[0.035]"
                    >
                      <Lock :size="18" class="shrink-0 text-[#a5a5a4]" />
                      <input
                        v-model="form.confirm_password"
                        :type="showConfirmPassword ? 'text' : 'password'"
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
                        @click="showConfirmPassword = !showConfirmPassword"
                        :aria-label="showConfirmPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'"
                        class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[#a0a09f] transition hover:bg-black/[0.04] hover:text-[#444443]"
                      >
                        <EyeOff v-if="showConfirmPassword" :size="18" />
                        <Eye v-else :size="18" />
                      </button>
                    </div>
                  </label>
                </div>

                <p class="text-[11px] leading-5 text-[#aaa9a8]">
                  Tu contraseña debe contener al menos 8 caracteres.
                </p>
              </div>
            </section>

            <div class="my-9 h-px bg-[#eeeeed]" />

            <!-- Profile -->
            <section>
              <div class="mb-6 flex items-start gap-4">
                <div
                  class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#f1f1f0] text-[#555554]"
                >
                  <UsersRound :size="18" stroke-width="1.8" />
                </div>
                <div>
                  <h2 class="text-sm font-bold text-[#363635]">
                    Información de registro
                  </h2>
                  <p class="mt-1 text-xs leading-5 text-[#999998]">
                    Completa los datos solicitados para tu registro en el curso.
                  </p>
                </div>
              </div>

              <div
                v-if="loadingCatalogs"
                class="mb-6 flex items-center gap-3 rounded-2xl border border-[#eeeeed] bg-[#fafafa] px-4 py-3 text-xs text-[#777776]"
              >
                <Loader2 :size="16" class="animate-spin" />
                Cargando catálogos...
              </div>

              <div
                v-if="catalogError"
                class="mb-6 flex items-start gap-3 rounded-2xl border border-amber-100 bg-amber-50 px-4 py-3.5 text-sm text-amber-800"
              >
                <AlertCircle :size="17" class="mt-0.5 shrink-0" />
                <span class="leading-5">{{ catalogError }}</span>
              </div>

              <div class="space-y-5">
                <!-- Institution + CURP -->
                <div class="grid gap-5 md:grid-cols-2">
                  <!-- Institution + CURP 
                  <label class="block">
                    <span class="mb-2 block text-[13px] font-semibold text-[#454544]">
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
                        :disabled="loading || loadingCatalogs"
                        class="h-[52px] w-full appearance-none rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-11 pr-10 text-sm font-medium text-[#292928] outline-none transition-all hover:border-[#cfcfce] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035] disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        <option :value="null" disabled>
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
-->
                  <label class="block">
                    <span class="mb-2 block text-[13px] font-semibold text-[#454544]">
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
                      <span class="shrink-0 text-[10px] font-semibold tabular-nums text-[#aaa9a8]">
                        {{ form.curp.length }}/18
                      </span>
                    </div>
                  </label>
                                  <!-- Municipality -->
                <label class="block">
                  <span class="mb-2 block text-[13px] font-semibold text-[#454544]">
                    Municipio
                  </span>
                  <div class="relative">
                    <MapPin
                      :size="18"
                      class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[#a5a5a4]"
                    />
                    <select
                      v-model="form.municipality_id"
                      required
                      :disabled="loading || loadingCatalogs"
                      class="h-[52px] w-full appearance-none rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-11 pr-10 text-sm font-medium text-[#292928] outline-none transition-all hover:border-[#cfcfce] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035] disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      <option :value="null" disabled>
                        Selecciona tu municipio
                      </option>
                      <option
                        v-for="municipality in municipalities"
                        :key="municipality.id"
                        :value="municipality.id"
                      >
                        {{ municipality.name }}
                      </option>
                    </select>
                    <ArrowRight
                      :size="16"
                      class="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 rotate-90 text-[#aaa9a8]"
                    />
                  </div>
                </label>
                </div>
                <Transition name="fade">
                  <div
                    v-if="isOtherMunicipality"
                    class="grid gap-5 rounded-2xl border border-[#eeeeed] bg-[#fafafa] p-4 md:grid-cols-2"
                  >
                    <label class="block">
                      <span class="mb-2 block text-[12px] font-semibold text-[#555554]">
                        Municipio
                      </span>
                      <input
                        v-model="form.municipality_other"
                        type="text"
                        maxlength="150"
                        :disabled="loading"
                        placeholder="Escribe el municipio"
                        class="h-[48px] w-full rounded-xl border border-[#e1e1e0] bg-white px-4 text-sm outline-none transition focus:border-[#4a4a49] focus:ring-4 focus:ring-black/[0.035]"
                      />
                    </label>

                    <label class="block">
                      <span class="mb-2 block text-[12px] font-semibold text-[#555554]">
                        Estado
                      </span>
                      <input
                        v-model="form.municipality_other_state"
                        type="text"
                        maxlength="150"
                        :disabled="loading"
                        placeholder="Escribe el estado"
                        class="h-[48px] w-full rounded-xl border border-[#e1e1e0] bg-white px-4 text-sm outline-none transition focus:border-[#4a4a49] focus:ring-4 focus:ring-black/[0.035]"
                      />
                    </label>
                  </div>
                </Transition>

                <!-- Gender + Age -->
                <div class="grid gap-5 md:grid-cols-2">
                  <label class="block">
                    <span class="mb-2 block text-[13px] font-semibold text-[#454544]">
                      Género
                    </span>
                    <div class="relative">
                      <VenusAndMars
                        :size="18"
                        class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[#a5a5a4]"
                      />
                      <select
                        v-model="form.gender_id"
                        required
                        :disabled="loading || loadingCatalogs"
                        class="h-[52px] w-full appearance-none rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-11 pr-10 text-sm font-medium text-[#292928] outline-none transition-all hover:border-[#cfcfce] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035] disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        <option :value="null" disabled>
                          Selecciona tu género
                        </option>
                        <option
                          v-for="item in genders"
                          :key="item.id"
                          :value="item.id"
                        >
                          {{ item.name }}
                        </option>
                      </select>
                      <ArrowRight
                        :size="16"
                        class="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 rotate-90 text-[#aaa9a8]"
                      />
                    </div>
                  </label>

                  <label class="block">
                    <span class="mb-2 block text-[13px] font-semibold text-[#454544]">
                      Edad
                    </span>
                    <div class="relative">
                      <User
                        :size="18"
                        class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[#a5a5a4]"
                      />
                      <select
                        v-model="form.age_range_id"
                        required
                        :disabled="loading || loadingCatalogs"
                        class="h-[52px] w-full appearance-none rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-11 pr-10 text-sm font-medium text-[#292928] outline-none transition-all hover:border-[#cfcfce] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035] disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        <option :value="null" disabled>
                          Selecciona tu rango de edad
                        </option>
                        <option
                          v-for="item in ageRanges"
                          :key="item.id"
                          :value="item.id"
                        >
                          {{ item.name }}
                        </option>
                      </select>
                      <ArrowRight
                        :size="16"
                        class="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 rotate-90 text-[#aaa9a8]"
                      />
                    </div>
                  </label>
                </div>

                <Transition name="fade">
                  <label v-if="isOtherGender" class="block">
                    <span class="mb-2 block text-[12px] font-semibold text-[#555554]">
                      Especifica tu género
                    </span>
                    <input
                      v-model="form.gender_other"
                      type="text"
                      maxlength="100"
                      :disabled="loading"
                      placeholder="Escribe cómo te identificas"
                      class="h-[48px] w-full rounded-xl border border-[#e1e1e0] bg-[#fafafa] px-4 text-sm outline-none transition focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035]"
                    />
                  </label>
                </Transition>

                <!-- Occupation + Sector -->
                <div class="grid gap-5 md:grid-cols-2">
                  <label class="block">
                    <span class="mb-2 block text-[13px] font-semibold text-[#454544]">
                      Ocupación
                    </span>
                    <div class="relative">
                      <BriefcaseBusiness
                        :size="18"
                        class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[#a5a5a4]"
                      />
                      <select
                        v-model="form.occupation_id"
                        required
                        :disabled="loading || loadingCatalogs"
                        class="h-[52px] w-full appearance-none rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-11 pr-10 text-sm font-medium text-[#292928] outline-none transition-all hover:border-[#cfcfce] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035] disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        <option :value="null" disabled>
                          Selecciona tu ocupación
                        </option>
                        <option
                          v-for="item in occupations"
                          :key="item.id"
                          :value="item.id"
                        >
                          {{ item.name }}
                        </option>
                      </select>
                      <ArrowRight
                        :size="16"
                        class="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 rotate-90 text-[#aaa9a8]"
                      />
                    </div>
                  </label>

                  <label class="block">
                    <span class="mb-2 block text-[13px] font-semibold text-[#454544]">
                      Institución o sector
                    </span>
                    <div class="relative">
                      <Building2
                        :size="18"
                        class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[#a5a5a4]"
                      />
                      <select
                        v-model="form.sector_id"
                        required
                        :disabled="loading || loadingCatalogs"
                        class="h-[52px] w-full appearance-none rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-11 pr-10 text-sm font-medium text-[#292928] outline-none transition-all hover:border-[#cfcfce] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035] disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        <option :value="null" disabled>
                          Selecciona una opción
                        </option>
                        <option
                          v-for="item in sectors"
                          :key="item.id"
                          :value="item.id"
                        >
                          {{ item.name }}
                        </option>
                      </select>
                      <ArrowRight
                        :size="16"
                        class="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 rotate-90 text-[#aaa9a8]"
                      />
                    </div>
                  </label>
                </div>

                <Transition name="fade">
                  <label v-if="isOtherOccupation" class="block">
                    <span class="mb-2 block text-[12px] font-semibold text-[#555554]">
                      Especifica tu ocupación
                    </span>
                    <input
                      v-model="form.occupation_other"
                      type="text"
                      maxlength="200"
                      :disabled="loading"
                      placeholder="Escribe tu ocupación"
                      class="h-[48px] w-full rounded-xl border border-[#e1e1e0] bg-[#fafafa] px-4 text-sm outline-none transition focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035]"
                    />
                  </label>
                </Transition>

                <!-- Self-identification -->
                <div class="rounded-2xl border border-[#eeeeed] bg-[#fafafa] p-5">
                  <div class="mb-5 flex items-start gap-3">
                    <div
                      class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white text-[#555554] ring-1 ring-black/[0.04]"
                    >
                      <Accessibility :size="17" />
                    </div>
                    <div>
                      <h3 class="text-[13px] font-bold text-[#454544]">
                        Datos de auto adscripción e inclusión
                      </h3>
                      <p class="mt-1 text-[11px] leading-5 text-[#999998]">
                        Selecciona una respuesta para cada pregunta.
                      </p>
                    </div>
                  </div>

                  <div class="grid gap-5 md:grid-cols-2">
                    <label class="block">
                      <span class="mb-2 block text-[12px] font-semibold leading-5 text-[#555554]">
                        ¿Te auto adscribes como persona indígena?
                      </span>
                      <select
                        v-model="form.indigenous_id"
                        required
                        :disabled="loading || loadingCatalogs"
                        class="h-[48px] w-full rounded-xl border border-[#e1e1e0] bg-white px-4 text-sm font-medium outline-none transition focus:border-[#4a4a49] focus:ring-4 focus:ring-black/[0.035] disabled:opacity-50"
                      >
                        <option :value="null" disabled>
                          Selecciona una opción
                        </option>
                        <option
                          v-for="item in yesNoOptions"
                          :key="item.id"
                          :value="item.id"
                        >
                          {{ item.name }}
                        </option>
                      </select>
                    </label>

                    <label class="block">
                      <span class="mb-2 block text-[12px] font-semibold leading-5 text-[#555554]">
                        ¿Te auto adscribes como persona afromexicana?
                      </span>
                      <select
                        v-model="form.afro_mexican_id"
                        required
                        :disabled="loading || loadingCatalogs"
                        class="h-[48px] w-full rounded-xl border border-[#e1e1e0] bg-white px-4 text-sm font-medium outline-none transition focus:border-[#4a4a49] focus:ring-4 focus:ring-black/[0.035] disabled:opacity-50"
                      >
                        <option :value="null" disabled>
                          Selecciona una opción
                        </option>
                        <option
                          v-for="item in yesNoOptions"
                          :key="item.id"
                          :value="item.id"
                        >
                          {{ item.name }}
                        </option>
                      </select>
                    </label>

                    <label class="block">
                      <span class="mb-2 block text-[12px] font-semibold leading-5 text-[#555554]">
                        ¿Tienes alguna discapacidad?
                      </span>
                      <select
                        v-model="form.disability_id"
                        required
                        :disabled="loading || loadingCatalogs"
                        class="h-[48px] w-full rounded-xl border border-[#e1e1e0] bg-white px-4 text-sm font-medium outline-none transition focus:border-[#4a4a49] focus:ring-4 focus:ring-black/[0.035] disabled:opacity-50"
                      >
                        <option :value="null" disabled>
                          Selecciona una opción
                        </option>
                        <option
                          v-for="item in yesNoOptions"
                          :key="item.id"
                          :value="item.id"
                        >
                          {{ item.name }}
                        </option>
                      </select>
                    </label>

                    <label class="block">
                      <span class="mb-2 block text-[12px] font-semibold leading-5 text-[#555554]">
                        ¿Te identificas como parte de la comunidad LGBTTTIQ+?
                      </span>
                      <select
                        v-model="form.lgbtttiq_id"
                        required
                        :disabled="loading || loadingCatalogs"
                        class="h-[48px] w-full rounded-xl border border-[#e1e1e0] bg-white px-4 text-sm font-medium outline-none transition focus:border-[#4a4a49] focus:ring-4 focus:ring-black/[0.035] disabled:opacity-50"
                      >
                        <option :value="null" disabled>
                          Selecciona una opción
                        </option>
                        <option
                          v-for="item in yesNoOptions"
                          :key="item.id"
                          :value="item.id"
                        >
                          {{ item.name }}
                        </option>
                      </select>
                    </label>
                  </div>
                </div>

                <!-- Education -->
                <label class="block">
                  <span class="mb-2 block text-[13px] font-semibold text-[#454544]">
                    Grado de estudios
                  </span>
                  <div class="relative">
                    <GraduationCap
                      :size="18"
                      class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[#a5a5a4]"
                    />
                    <select
                      v-model="form.education_level_id"
                      required
                      :disabled="loading || loadingCatalogs"
                      class="h-[52px] w-full appearance-none rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-11 pr-10 text-sm font-medium text-[#292928] outline-none transition-all hover:border-[#cfcfce] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035] disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      <option :value="null" disabled>
                        Selecciona tu grado de estudios
                      </option>
                      <option
                        v-for="item in educationLevels"
                        :key="item.id"
                        :value="item.id"
                      >
                        {{ item.name }}
                      </option>
                    </select>
                    <ArrowRight
                      :size="16"
                      class="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 rotate-90 text-[#aaa9a8]"
                    />
                  </div>
                </label>
              </div>
            </section>

            <!-- Error -->
            <Transition name="fade">
              <div
                v-if="error"
                class="mt-8 flex items-start gap-3 rounded-2xl border border-red-100 bg-red-50 px-4 py-3.5 text-sm text-red-700"
                role="alert"
                aria-live="assertive"
              >
                <AlertCircle :size="17" class="mt-0.5 shrink-0" />
                <span class="leading-5">{{ error }}</span>
              </div>
            </Transition>

            <!-- Submit -->
            <div class="mt-8">
              <button
                type="submit"
                :disabled="loading || loadingCatalogs"
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
                      : loadingCatalogs
                        ? 'Cargando información…'
                        : 'Crear cuenta'
                  }}
                </span>

                <ArrowRight
                  v-if="!loading && !loadingCatalogs"
                  :size="16"
                  class="relative opacity-50 transition-transform duration-200 group-hover:translate-x-0.5"
                />
              </button>
            </div>

            <div
              class="mt-6 flex items-center justify-center gap-2 text-center text-[11px] leading-5 text-[#aaa9a8]"
            >
              <ShieldCheck :size="14" class="shrink-0" />
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
              <ArrowRight :size="14" />
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
