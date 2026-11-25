<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import {
  UserPlus,
  ArrowLeft,
  ArrowRight,
  Check,
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
import { useAuth, type Institution } from '../../services/auth';
import BaseAlert from '../../components/ui/BaseAlert.vue';

type CatalogItem = {
  id: number;
  name: string;
};

type Municipality = {
  id: number;
  name: string;
  state_id: number;
  code?: string | null;
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

const steps = [
  { title: 'Datos personales', shortTitle: 'Datos' },
  { title: 'Acceso', shortTitle: 'Cuenta' },
  { title: 'Perfil', shortTitle: 'Perfil' },
  { title: 'Auto adscripción', shortTitle: 'Inclusión' },
];

const currentStep = ref(0);
const stepHeadingRef = ref<HTMLElement | null>(null);

const form = ref({
  first_name: '',
  paternal_surname: '',
  maternal_surname: '',
  email: '',
  password: '',
  confirm_password: '',
  curp: '',

  state_id: null as number | null,
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
const loadingMunicipalities = ref(false);
const error = ref('');
const municipalityError = ref('');
const showPassword = ref(false);
const showConfirmPassword = ref(false);

const curpInputRef = ref<HTMLInputElement | null>(null);

const selectedState = computed(() =>
  states.value.find((state) => state.id === form.value.state_id)
);

const selectedMunicipality = computed(() =>
  municipalities.value.find((municipality) => municipality.id === form.value.municipality_id)
);

const municipalityNameCounts = computed(() => {
  const counts = new Map<string, number>();
  for (const municipality of municipalities.value) {
    counts.set(municipality.name, (counts.get(municipality.name) ?? 0) + 1);
  }
  return counts;
});

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
      gendersCatalog,
      ageRangesCatalog,
      occupationsCatalog,
      sectorsCatalog,
      yesNoCatalog,
      educationCatalog,
    ] = await Promise.all([
      fetchJson<StateItem[]>('/api/catalogs/states'),
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
    if (form.value.state_id !== null) {
      await loadMunicipalities(form.value.state_id);
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

function municipalityLabel(municipality: Municipality) {
  return (municipalityNameCounts.value.get(municipality.name) ?? 0) > 1 && municipality.code
    ? `${municipality.name} (clave ${municipality.code})`
    : municipality.name;
}

let municipalityRequestId = 0;

async function loadMunicipalities(stateId: number | null) {
  const requestId = ++municipalityRequestId;
  municipalities.value = [];
  municipalityError.value = '';

  if (stateId === null) {
    loadingMunicipalities.value = false;
    return;
  }

  loadingMunicipalities.value = true;
  try {
    const catalog = await fetchMunicipalities(stateId);
    if (requestId === municipalityRequestId) {
      municipalities.value = catalog;
    }
  } catch (e: unknown) {
    if (requestId === municipalityRequestId) {
      municipalityError.value = e instanceof Error
        ? e.message
        : 'No se pudieron cargar los municipios del estado seleccionado.';
    }
  } finally {
    if (requestId === municipalityRequestId) {
      loadingMunicipalities.value = false;
    }
  }
}

onMounted(loadCatalogs);

watch(
  () => form.value.state_id,
  (stateId) => {
    form.value.municipality_id = null;
    form.value.municipality_other = '';
    form.value.municipality_other_state = '';
    void loadMunicipalities(stateId);
  }
);

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
  clearError();
}

function clearError() {
  error.value = '';
}

function validateEmail(email: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function validateStep(stepIndex: number) {
  if (stepIndex === 0) {
    if (!form.value.first_name.trim() || !form.value.paternal_surname.trim() || !form.value.maternal_surname.trim()) {
      return 'Completa tu nombre y apellidos.';
    }

    if (form.value.curp.trim().length !== 18) {
      return 'La CURP debe tener 18 caracteres.';
    }
  }

  if (stepIndex === 1) {
    const email = form.value.email.trim();
    if (!email) return 'Ingresa tu correo electrónico personal.';
    if (!validateEmail(email)) return 'Ingresa un correo electrónico válido.';
    if (form.value.password.length < 8) return 'La contraseña debe tener al menos 8 caracteres.';
    if (form.value.password !== form.value.confirm_password) return 'Las contraseñas no coinciden.';
  }

  if (stepIndex === 2) {
    if (!form.value.state_id) return 'Selecciona tu estado.';
    if (!form.value.municipality_id) return 'Selecciona tu municipio.';
    if (isOtherMunicipality.value && !form.value.municipality_other.trim()) {
      return 'Escribe el nombre del municipio.';
    }
    if (isOtherMunicipality.value && !form.value.municipality_other_state.trim()) {
      return 'Escribe el nombre del estado.';
    }
    if (!form.value.gender_id) return 'Selecciona tu género.';
    if (isOtherGender.value && !form.value.gender_other.trim()) return 'Especifica tu género.';
    if (!form.value.age_range_id) return 'Selecciona tu rango de edad.';
    if (!form.value.occupation_id) return 'Selecciona tu ocupación.';
    if (isOtherOccupation.value && !form.value.occupation_other.trim()) return 'Especifica tu ocupación.';
    if (!form.value.sector_id) return 'Selecciona la institución o sector al que perteneces.';
    if (!form.value.education_level_id) return 'Selecciona tu grado de estudios.';
  }

  if (stepIndex === 3) {
    if (!form.value.indigenous_id) return 'Indica si te auto adscribes como persona indígena.';
    if (!form.value.afro_mexican_id) return 'Indica si te auto adscribes como persona afromexicana.';
    if (!form.value.disability_id) return 'Indica si tienes alguna discapacidad.';
    if (!form.value.lgbtttiq_id) return 'Indica si te identificas como parte de la comunidad LGBTTTIQ+.';
  }

  return '';
}

function validateForm() {
  for (let stepIndex = 0; stepIndex < steps.length; stepIndex += 1) {
    const validationError = validateStep(stepIndex);
    if (validationError) return validationError;
  }
  return '';
}

async function focusCurrentStep() {
  await nextTick();
  stepHeadingRef.value?.focus();
}

async function goToPreviousStep() {
  if (currentStep.value === 0 || loading.value) return;
  currentStep.value -= 1;
  error.value = '';
  await focusCurrentStep();
}

async function goToNextStep() {
  if (loading.value || currentStep.value === steps.length - 1) return;
  if (currentStep.value === 2 && (loadingCatalogs.value || loadingMunicipalities.value || catalogError.value || municipalityError.value)) return;

  error.value = '';
  const validationError = validateStep(currentStep.value);
  if (validationError) {
    error.value = validationError;
    return;
  }

  currentStep.value += 1;
  await focusCurrentStep();
}

async function onSubmit() {
  if (currentStep.value < steps.length - 1) {
    await goToNextStep();
    return;
  }

  if (loading.value || loadingCatalogs.value) return;

  error.value = '';

  const validationError = validateForm();

  if (validationError) {
    error.value = validationError;
    return;
  }

  const stateId = form.value.state_id;
  const municipalityId = form.value.municipality_id;
  if (stateId === null || municipalityId === null) {
    error.value = 'Selecciona tu estado y municipio.';
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

      state_id: stateId,
      municipality_id: municipalityId,
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
  <div class="relative min-h-dvh overflow-hidden bg-[#f6f6f5] text-[#292928]">
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
          class="page-control page-press group inline-flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-semibold text-[#777776] [@media(hover:hover)_and_(pointer:fine)]:hover:bg-black/[0.035] [@media(hover:hover)_and_(pointer:fine)]:hover:text-[#292928] disabled:opacity-50"
        >
          <ArrowLeft
            :size="15"
          />
          Volver a iniciar sesión
        </button>
      </div>
    </header>

    <!-- Content -->
    <main
      id="main-content"
      tabindex="-1"
      class="relative z-10 mx-auto grid min-h-[calc(100dvh-77px)] w-full max-w-screen-2xl grid-cols-1 items-center gap-8 px-5 py-8 sm:px-8 lg:grid-cols-[minmax(0,0.68fr)_minmax(0,1.32fr)] lg:gap-10 lg:px-12 lg:py-0 xl:gap-14"
    >
      <!-- Intro -->
      <section
        aria-labelledby="registration-title"
        class="mx-auto w-full max-w-sm text-center lg:mx-0 lg:text-left"
      >
        <div
          class="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#292928] text-white shadow-lg shadow-black/10 lg:mx-0"
        >
          <UserPlus :size="21" stroke-width="1.8" />
        </div>

        <p
          class="mb-2 text-[11px] font-bold uppercase tracking-[0.2em] text-[#a0a09f]"
        >
          Plataforma de capacitación
        </p>

        <h1
          id="registration-title"
          class="text-[32px] font-semibold tracking-[-0.035em] text-[#292928] sm:text-[36px] lg:text-[42px]"
        >
          Crear cuenta
        </h1>

        <p
          class="mx-auto mt-3 max-w-lg text-sm leading-6 text-[#888887] lg:mx-0 lg:text-base lg:leading-7"
        >
          Registra tus datos para acceder a tu curso y continuar con tus
          actividades de capacitación.
        </p>

        <div
          class="mt-8 flex items-center justify-center gap-3 text-[10px] font-medium uppercase tracking-[0.12em] text-[#b2b2b1] lg:justify-start"
        >
          <span>FEDE</span>
          <span class="h-1 w-1 rounded-full bg-[#c8c8c7]" />
          <span>FGJ Tamaulipas</span>
        </div>
      </section>

      <div class="w-full max-w-5xl justify-self-center">
        <!-- Card -->
        <div
          class="overflow-hidden rounded-[28px] border border-black/[0.055] bg-white shadow-[0_24px_80px_rgba(0,0,0,0.08)]"
        >
          <form
            class="registration-form p-5 sm:p-6 lg:p-6"
            @submit.prevent="onSubmit"
            novalidate
          >
            <div class="mb-4">
              <div class="mb-3 flex items-center justify-between gap-3" role="status" aria-live="polite">
                <p class="text-xs font-semibold uppercase tracking-[0.12em] text-[#999998]">
                  Paso {{ currentStep + 1 }} de {{ steps.length }}
                </p>
                <p class="text-sm font-bold text-[#454544]">
                  {{ steps[currentStep].title }}
                </p>
              </div>
              <ol class="grid grid-cols-4 gap-2" aria-label="Progreso del registro">
                <li
                  v-for="(step, stepIndex) in steps"
                  :key="step.title"
                  class="min-w-0"
                  :aria-current="stepIndex === currentStep ? 'step' : undefined"
                >
                  <div class="flex items-center gap-2">
                    <span
                      class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold transition-colors"
                      :class="stepIndex <= currentStep ? 'bg-[#292928] text-white' : 'bg-[#f1f1f0] text-[#999998]'"
                    >
                      <Check v-if="stepIndex < currentStep" :size="14" aria-hidden="true" />
                      <span v-else>{{ stepIndex + 1 }}</span>
                    </span>
                    <span
                      class="hidden truncate text-xs font-semibold sm:block"
                      :class="stepIndex <= currentStep ? 'text-[#454544]' : 'text-[#999998]'"
                    >
                      {{ step.shortTitle }}
                    </span>
                  </div>
                  <div class="mt-2 h-1 overflow-hidden rounded-full bg-[#eeeeed]" aria-hidden="true">
                    <div
                      class="h-full rounded-full transition-colors"
                      :class="stepIndex <= currentStep ? 'bg-[#292928]' : 'bg-transparent'"
                    />
                  </div>
                </li>
              </ol>
            </div>

            <Transition name="fade">
            <!-- Personal -->
            <section
              v-if="currentStep === 0"
              key="personal"
              aria-labelledby="personal-step-heading"
            >
              <div class="mb-5 flex items-start gap-4">
                <div
                  class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#f1f1f0] text-[#555554]"
                >
                  <User :size="18" stroke-width="1.8" />
                </div>
                <div>
                  <h2 ref="stepHeadingRef" id="personal-step-heading" tabindex="-1" class="text-lg font-bold text-[#363635] outline-none focus-visible:ring-2 focus-visible:ring-[#878787]">
                    Datos personales
                  </h2>
                  <p class="mt-1 text-xs leading-5 text-[#999998]">
                    Ingresa tu nombre y los datos generales solicitados.
                  </p>
                </div>
              </div>

              <div class="space-y-4">
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
                    class="h-[52px] w-full rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-4 text-sm font-medium text-[#292928] outline-none transition-colors placeholder:text-[#b8b8b7] [@media(hover:hover)_and_(pointer:fine)]:hover:border-[#cfcfce] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035] disabled:cursor-not-allowed disabled:opacity-50"
                  />
                </label>

                <div class="grid gap-4 md:grid-cols-2">
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
                      class="h-[52px] w-full rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-4 text-sm font-medium text-[#292928] outline-none transition-colors placeholder:text-[#b8b8b7] [@media(hover:hover)_and_(pointer:fine)]:hover:border-[#cfcfce] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035] disabled:cursor-not-allowed disabled:opacity-50"
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
                      class="h-[52px] w-full rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-4 text-sm font-medium text-[#292928] outline-none transition-colors placeholder:text-[#b8b8b7] [@media(hover:hover)_and_(pointer:fine)]:hover:border-[#cfcfce] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035] disabled:cursor-not-allowed disabled:opacity-50"
                    />
                  </label>
                </div>

                <label class="block">
                  <span class="mb-2 block text-[13px] font-semibold text-[#454544]">
                    CURP
                  </span>
                  <div
                    class="group flex h-[52px] items-center gap-3 rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-4 [transition:background-color_150ms_var(--ease-out),border-color_150ms_var(--ease-out),color_150ms_var(--ease-out),opacity_150ms_var(--ease-out)] [@media(hover:hover)_and_(pointer:fine)]:hover:border-[#cfcfce] focus-within:border-[#4a4a49] focus-within:bg-white focus-within:ring-4 focus-within:ring-black/[0.035]"
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
              </div>
            </section>

            <!-- Account -->
            <section
              v-else-if="currentStep === 1"
              key="account"
              aria-labelledby="account-step-heading"
            >
              <div class="mb-5 flex items-start gap-4">
                <div
                  class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#f1f1f0] text-[#555554]"
                >
                  <Lock :size="18" stroke-width="1.8" />
                </div>
                <div>
                  <h2 ref="stepHeadingRef" id="account-step-heading" tabindex="-1" class="text-lg font-bold text-[#363635] outline-none focus-visible:ring-2 focus-visible:ring-[#878787]">
                    Datos de acceso
                  </h2>
                  <p class="mt-1 text-xs leading-5 text-[#999998]">
                    Utilizarás estos datos para ingresar a la plataforma.
                  </p>
                </div>
              </div>

              <div class="space-y-4">
                <label class="block">
                  <span class="mb-2 block text-[13px] font-semibold text-[#454544]">
                    Correo electrónico personal
                  </span>
                  <div
                    class="group flex h-[52px] items-center gap-3 rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-4 [transition:background-color_150ms_var(--ease-out),border-color_150ms_var(--ease-out),color_150ms_var(--ease-out),opacity_150ms_var(--ease-out)] [@media(hover:hover)_and_(pointer:fine)]:hover:border-[#cfcfce] focus-within:border-[#4a4a49] focus-within:bg-white focus-within:ring-4 focus-within:ring-black/[0.035]"
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

                <div class="grid gap-4 md:grid-cols-2">
                  <label class="block">
                    <span class="mb-2 block text-[13px] font-semibold text-[#454544]">
                      Contraseña
                    </span>
                    <div
                      class="group flex h-[52px] items-center gap-3 rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-4 [transition:background-color_150ms_var(--ease-out),border-color_150ms_var(--ease-out),color_150ms_var(--ease-out),opacity_150ms_var(--ease-out)] [@media(hover:hover)_and_(pointer:fine)]:hover:border-[#cfcfce] focus-within:border-[#4a4a49] focus-within:bg-white focus-within:ring-4 focus-within:ring-black/[0.035]"
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
                        class="page-control page-press flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[#a0a09f] [@media(hover:hover)_and_(pointer:fine)]:hover:bg-black/[0.04] [@media(hover:hover)_and_(pointer:fine)]:hover:text-[#444443]"
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
                      class="group flex h-[52px] items-center gap-3 rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-4 [transition:background-color_150ms_var(--ease-out),border-color_150ms_var(--ease-out),color_150ms_var(--ease-out),opacity_150ms_var(--ease-out)] [@media(hover:hover)_and_(pointer:fine)]:hover:border-[#cfcfce] focus-within:border-[#4a4a49] focus-within:bg-white focus-within:ring-4 focus-within:ring-black/[0.035]"
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
                        class="page-control page-press flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[#a0a09f] [@media(hover:hover)_and_(pointer:fine)]:hover:bg-black/[0.04] [@media(hover:hover)_and_(pointer:fine)]:hover:text-[#444443]"
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

            <!-- Profile -->
            <section
              v-else-if="currentStep === 2"
              key="profile"
              aria-labelledby="profile-step-heading"
            >
              <div class="mb-5 flex items-start gap-4">
                <div
                  class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#f1f1f0] text-[#555554]"
                >
                  <UsersRound :size="18" stroke-width="1.8" />
                </div>
                <div>
                  <h2 ref="stepHeadingRef" id="profile-step-heading" tabindex="-1" class="text-lg font-bold text-[#363635] outline-none focus-visible:ring-2 focus-visible:ring-[#878787]">
                    Ubicación y perfil
                  </h2>
                  <p class="mt-1 text-xs leading-5 text-[#999998]">
                    Indica dónde vives y comparte tus datos de perfil.
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

              <BaseAlert v-if="catalogError" class="mb-6" variant="destructive" title="No se pudieron cargar los datos de registro" :description="catalogError">
                <template #action><button type="button" class="page-control page-press min-h-10 rounded-lg border border-[#a3a3a2] bg-white px-3 py-2 text-sm font-semibold [@media(hover:hover)_and_(pointer:fine)]:hover:bg-[#f2f2f1]" @click="loadCatalogs">Reintentar</button></template>
              </BaseAlert>

              <BaseAlert v-if="municipalityError" class="mb-6" variant="destructive" title="No se pudieron cargar los municipios" :description="municipalityError">
                <template #action><button type="button" class="page-control page-press min-h-10 rounded-lg border border-[#a3a3a2] bg-white px-3 py-2 text-sm font-semibold [@media(hover:hover)_and_(pointer:fine)]:hover:bg-[#f2f2f1] disabled:cursor-not-allowed disabled:opacity-50" :disabled="loadingMunicipalities || form.state_id === null" @click="loadMunicipalities(form.state_id)">Reintentar</button></template>
              </BaseAlert>

              <div class="space-y-3">
                <!-- Institution -->
                <div class="grid gap-4 md:grid-cols-2">
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
                        class="h-[52px] w-full appearance-none rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-11 pr-10 text-sm font-medium text-[#292928] outline-none transition-colors [@media(hover:hover)_and_(pointer:fine)]:hover:border-[#cfcfce] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035] disabled:cursor-not-allowed disabled:opacity-50"
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
                      Estado
                    </span>
                    <div class="relative">
                      <MapPin
                        :size="18"
                        class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[#a5a5a4]"
                      />
                      <select
                        v-model="form.state_id"
                        required
                        :disabled="loading || loadingCatalogs"
                        class="h-[52px] w-full appearance-none rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-11 pr-10 text-sm font-medium text-[#292928] outline-none transition-colors [@media(hover:hover)_and_(pointer:fine)]:hover:border-[#cfcfce] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035] disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        <option :value="null" disabled>
                          Selecciona tu estado
                        </option>
                        <option
                          v-for="state in states"
                          :key="state.id"
                          :value="state.id"
                        >
                          {{ state.name }}
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
                      :disabled="loading || loadingCatalogs || loadingMunicipalities || form.state_id === null"
                      class="h-[52px] w-full appearance-none rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-11 pr-10 text-sm font-medium text-[#292928] outline-none transition-colors [@media(hover:hover)_and_(pointer:fine)]:hover:border-[#cfcfce] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035] disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      <option :value="null" disabled>
                        {{ loadingMunicipalities ? 'Cargando municipios…' : form.state_id === null ? 'Primero selecciona un estado' : 'Selecciona tu municipio' }}
                      </option>
                      <option
                        v-for="municipality in municipalities"
                        :key="municipality.id"
                        :value="municipality.id"
                      >
                        {{ municipalityLabel(municipality) }}
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
                    class="rounded-2xl border border-[#eeeeed] bg-[#fafafa] p-4"
                  >
                    <div class="grid gap-4 md:grid-cols-2">
                      <label class="block">
                        <span class="mb-2 block text-[12px] font-semibold text-[#555554]">
                          Otro municipio
                        </span>
                        <input
                          v-model="form.municipality_other"
                          type="text"
                          maxlength="150"
                          :disabled="loading"
                          placeholder="Escribe el municipio"
                          class="h-[48px] w-full rounded-xl border border-[#e1e1e0] bg-white px-4 text-sm outline-none [transition:background-color_150ms_var(--ease-out),border-color_150ms_var(--ease-out),color_150ms_var(--ease-out),opacity_150ms_var(--ease-out)] focus:border-[#4a4a49] focus:ring-4 focus:ring-black/[0.035]"
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
                          class="h-[48px] w-full rounded-xl border border-[#e1e1e0] bg-white px-4 text-sm outline-none [transition:background-color_150ms_var(--ease-out),border-color_150ms_var(--ease-out),color_150ms_var(--ease-out),opacity_150ms_var(--ease-out)] focus:border-[#4a4a49] focus:ring-4 focus:ring-black/[0.035]"
                        />
                      </label>
                    </div>
                  </div>
                </Transition>

                <!-- Gender + Age -->
                <div class="grid gap-4 md:grid-cols-2">
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
                        class="h-[52px] w-full appearance-none rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-11 pr-10 text-sm font-medium text-[#292928] outline-none transition-colors [@media(hover:hover)_and_(pointer:fine)]:hover:border-[#cfcfce] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035] disabled:cursor-not-allowed disabled:opacity-50"
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
                        class="h-[52px] w-full appearance-none rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-11 pr-10 text-sm font-medium text-[#292928] outline-none transition-colors [@media(hover:hover)_and_(pointer:fine)]:hover:border-[#cfcfce] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035] disabled:cursor-not-allowed disabled:opacity-50"
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
                      class="h-[48px] w-full rounded-xl border border-[#e1e1e0] bg-[#fafafa] px-4 text-sm outline-none [transition:background-color_150ms_var(--ease-out),border-color_150ms_var(--ease-out),color_150ms_var(--ease-out),opacity_150ms_var(--ease-out)] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035]"
                    />
                  </label>
                </Transition>

                <!-- Occupation + Sector -->
                <div class="grid gap-4 md:grid-cols-2">
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
                        class="h-[52px] w-full appearance-none rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-11 pr-10 text-sm font-medium text-[#292928] outline-none transition-colors [@media(hover:hover)_and_(pointer:fine)]:hover:border-[#cfcfce] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035] disabled:cursor-not-allowed disabled:opacity-50"
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
                        class="h-[52px] w-full appearance-none rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-11 pr-10 text-sm font-medium text-[#292928] outline-none transition-colors [@media(hover:hover)_and_(pointer:fine)]:hover:border-[#cfcfce] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035] disabled:cursor-not-allowed disabled:opacity-50"
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
                      class="h-[48px] w-full rounded-xl border border-[#e1e1e0] bg-[#fafafa] px-4 text-sm outline-none [transition:background-color_150ms_var(--ease-out),border-color_150ms_var(--ease-out),color_150ms_var(--ease-out),opacity_150ms_var(--ease-out)] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035]"
                    />
                  </label>
                </Transition>

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
                      class="h-[52px] w-full appearance-none rounded-2xl border border-[#e4e4e3] bg-[#fafafa] px-11 pr-10 text-sm font-medium text-[#292928] outline-none transition-colors [@media(hover:hover)_and_(pointer:fine)]:hover:border-[#cfcfce] focus:border-[#4a4a49] focus:bg-white focus:ring-4 focus:ring-black/[0.035] disabled:cursor-not-allowed disabled:opacity-50"
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

            <section
              v-else
              key="inclusion"
              aria-labelledby="inclusion-step-heading"
            >
              <div class="mb-5 flex items-start gap-4">
                <div
                  class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#f1f1f0] text-[#555554]"
                >
                  <Accessibility :size="18" stroke-width="1.8" />
                </div>
                <div>
                  <h2 ref="stepHeadingRef" id="inclusion-step-heading" tabindex="-1" class="text-lg font-bold text-[#363635] outline-none focus-visible:ring-2 focus-visible:ring-[#878787]">
                    Auto adscripción e inclusión
                  </h2>
                  <p class="mt-1 text-xs leading-5 text-[#999998]">
                    Tus respuestas nos ayudan a ofrecer una capacitación más incluyente.
                  </p>
                </div>
              </div>

              <div class="rounded-2xl border border-[#eeeeed] bg-[#fafafa] p-5">
                <div class="mb-5">
                  <h3 class="text-[13px] font-bold text-[#454544]">
                    Datos de auto adscripción e inclusión
                  </h3>
                  <p class="mt-1 text-[11px] leading-5 text-[#999998]">
                    Selecciona una respuesta para cada pregunta.
                  </p>
                </div>

                <div class="grid gap-4 md:grid-cols-2">
                  <label class="block">
                    <span class="mb-2 block text-[12px] font-semibold leading-5 text-[#555554]">
                      ¿Te auto adscribes como persona indígena?
                    </span>
                    <select
                      v-model="form.indigenous_id"
                      required
                      :disabled="loading || loadingCatalogs"
                      class="h-[48px] w-full rounded-xl border border-[#e1e1e0] bg-white px-4 text-sm font-medium outline-none [transition:background-color_150ms_var(--ease-out),border-color_150ms_var(--ease-out),color_150ms_var(--ease-out),opacity_150ms_var(--ease-out)] focus:border-[#4a4a49] focus:ring-4 focus:ring-black/[0.035] disabled:opacity-50"
                    >
                      <option :value="null" disabled>Selecciona una opción</option>
                      <option v-for="item in yesNoOptions" :key="item.id" :value="item.id">
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
                      class="h-[48px] w-full rounded-xl border border-[#e1e1e0] bg-white px-4 text-sm font-medium outline-none [transition:background-color_150ms_var(--ease-out),border-color_150ms_var(--ease-out),color_150ms_var(--ease-out),opacity_150ms_var(--ease-out)] focus:border-[#4a4a49] focus:ring-4 focus:ring-black/[0.035] disabled:opacity-50"
                    >
                      <option :value="null" disabled>Selecciona una opción</option>
                      <option v-for="item in yesNoOptions" :key="item.id" :value="item.id">
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
                      class="h-[48px] w-full rounded-xl border border-[#e1e1e0] bg-white px-4 text-sm font-medium outline-none [transition:background-color_150ms_var(--ease-out),border-color_150ms_var(--ease-out),color_150ms_var(--ease-out),opacity_150ms_var(--ease-out)] focus:border-[#4a4a49] focus:ring-4 focus:ring-black/[0.035] disabled:opacity-50"
                    >
                      <option :value="null" disabled>Selecciona una opción</option>
                      <option v-for="item in yesNoOptions" :key="item.id" :value="item.id">
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
                      class="h-[48px] w-full rounded-xl border border-[#e1e1e0] bg-white px-4 text-sm font-medium outline-none [transition:background-color_150ms_var(--ease-out),border-color_150ms_var(--ease-out),color_150ms_var(--ease-out),opacity_150ms_var(--ease-out)] focus:border-[#4a4a49] focus:ring-4 focus:ring-black/[0.035] disabled:opacity-50"
                    >
                      <option :value="null" disabled>Selecciona una opción</option>
                      <option v-for="item in yesNoOptions" :key="item.id" :value="item.id">
                        {{ item.name }}
                      </option>
                    </select>
                  </label>
                </div>
              </div>
            </section>
            </Transition>

            <!-- Error -->
            <Transition name="fade">
              <BaseAlert v-if="error" class="mt-8" variant="destructive" title="Revisa los datos del formulario" :description="error" />
            </Transition>

            <!-- Submit -->
            <div class="mt-6 flex gap-3">
              <button
                v-if="currentStep > 0"
                type="button"
                :disabled="loading"
                @click="goToPreviousStep"
                class="page-control page-press inline-flex min-h-[54px] items-center justify-center gap-2 rounded-2xl border border-[#e4e4e3] bg-white px-5 text-sm font-semibold text-[#555554] transition-colors [@media(hover:hover)_and_(pointer:fine)]:hover:bg-[#f7f7f6] disabled:cursor-not-allowed disabled:opacity-50"
              >
                <ArrowLeft :size="16" aria-hidden="true" />
                Anterior
              </button>

              <button
                v-if="currentStep < steps.length - 1"
                type="button"
                :disabled="loading || (currentStep === 2 && (loadingCatalogs || loadingMunicipalities || Boolean(catalogError) || Boolean(municipalityError)))"
                @click="goToNextStep"
                class="page-control page-press group relative flex min-h-[54px] flex-1 items-center justify-center gap-2.5 overflow-hidden rounded-2xl bg-[#292928] text-sm font-semibold text-white shadow-[0_10px_25px_rgba(41,41,40,0.16)] [@media(hover:hover)_and_(pointer:fine)]:hover:bg-[#1f1f1e] disabled:cursor-not-allowed disabled:opacity-60"
              >
                <span>
                  {{ currentStep === 2 && (loadingCatalogs || loadingMunicipalities) ? 'Cargando información…' : 'Continuar' }}
                </span>
                <Loader2
                  v-if="currentStep === 2 && (loadingCatalogs || loadingMunicipalities)"
                  :size="17"
                  class="animate-spin"
                  aria-hidden="true"
                />
                <ArrowRight v-else :size="16" class="opacity-60" aria-hidden="true" />
              </button>

              <button
                v-else
                type="submit"
                :disabled="loading || loadingCatalogs || loadingMunicipalities"
                class="page-control page-press group relative flex min-h-[54px] flex-1 items-center justify-center gap-2.5 overflow-hidden rounded-2xl bg-[#292928] text-sm font-semibold text-white shadow-[0_10px_25px_rgba(41,41,40,0.16)] [@media(hover:hover)_and_(pointer:fine)]:hover:bg-[#1f1f1e] disabled:cursor-not-allowed disabled:opacity-60"
              >
                <Loader2 v-if="loading" :size="18" class="animate-spin" aria-hidden="true" />
                <UserPlus v-else :size="18" stroke-width="1.9" aria-hidden="true" />
                <span>{{ loading ? 'Creando cuenta…' : 'Crear cuenta' }}</span>
                <ArrowRight v-if="!loading" :size="16" class="opacity-50" aria-hidden="true" />
              </button>
            </div>

            <div class="mt-3 flex items-center justify-center gap-2 text-center text-[11px] leading-5 text-[#aaa9a8]">
              <ShieldCheck :size="14" class="shrink-0" />
              <span>
                Tu información se mantiene protegida.
              </span>
            </div>
          </form>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
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

@media (min-width: 1024px) {
  .registration-form :deep([class~="h-[52px]"]),
  .registration-form :deep([class~="h-[48px]"]) {
    height: 44px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .fade-enter-active,
  .fade-leave-active {
    transition: none;
  }
}
</style>
