<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import {
  BadgeCheck,
  BookOpen,
  CalendarDays,
  Check,
  CircleX,
  Copy,
  Link2,
  MapPin,
  ShieldCheck,
  UserRound,
} from 'lucide-vue-next';
import InstitutionalHeader from '../../components/layout/InstitutionalHeader.vue';
import { formatCertificateFolio, formatCertificateName } from '../../lib/certificate-format';

type Verification = {
  valid: boolean;
  message: string;
  folio: string;
  issued_at: string;
  user_name: string;
  municipality: string | null;
  sector: string | null;
  course: {
    name: string;
  };
};

type CopyTarget = 'folio' | 'link';

const props = defineProps<{ folio: string }>();
const API = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
const state = ref<'loading' | 'valid' | 'invalid' | 'error'>('loading');
const verification = ref<Verification | null>(null);
const error = ref('');
const copyFeedback = ref('');
const copyFeedbackIsError = ref(false);
const copyingTarget = ref<CopyTarget | null>(null);
const copiedTarget = ref<CopyTarget | null>(null);

const issuedDate = computed(() => {
  const date = verification.value ? new Date(verification.value.issued_at) : null;
  return date && !Number.isNaN(date.getTime())
    ? date.toLocaleDateString('es-MX', { year: 'numeric', month: 'long', day: 'numeric' })
    : 'Fecha no disponible';
});

async function loadVerification() {
  state.value = 'loading';
  verification.value = null;
  error.value = '';
  copyFeedback.value = '';
  copiedTarget.value = null;

  try {
    const response = await fetch(`${API}/api/certificates/verify/${encodeURIComponent(props.folio)}`);
    const data = await response.json().catch(() => null);
    if (!response.ok) throw new Error(data?.detail || 'No se pudo consultar la constancia.');
    if (!data?.valid) {
      state.value = 'invalid';
      error.value = data?.message || 'No se encontró una constancia válida con este folio.';
      return;
    }

    verification.value = data as Verification;
    state.value = 'valid';
  } catch (cause: unknown) {
    state.value = 'error';
    error.value = cause instanceof Error
      ? cause.message
      : 'No fue posible conectar con el servicio de verificación.';
  }
}

async function copyValue(value: string, target: CopyTarget) {
  copyFeedback.value = '';
  copiedTarget.value = null;

  if (!navigator.clipboard?.writeText) {
    copyFeedbackIsError.value = true;
    copyFeedback.value = target === 'folio'
      ? 'No se pudo copiar automáticamente. Selecciona el folio y cópialo manualmente.'
      : 'No se pudo copiar automáticamente. Puedes copiar la dirección desde la barra del navegador.';
    return;
  }

  copyingTarget.value = target;
  try {
    await navigator.clipboard.writeText(value);
    copiedTarget.value = target;
    copyFeedbackIsError.value = false;
    copyFeedback.value = target === 'folio' ? 'Folio copiado.' : 'Enlace de verificación copiado.';
  } catch {
    copyFeedbackIsError.value = true;
    copyFeedback.value = target === 'folio'
      ? 'No se pudo copiar. Selecciona el folio y cópialo manualmente.'
      : 'No se pudo copiar. Puedes copiar la dirección desde la barra del navegador.';
  } finally {
    copyingTarget.value = null;
  }
}

function copyVerificationLink() {
  return copyValue(`${window.location.origin}${window.location.pathname}`, 'link');
}

onMounted(loadVerification);
watch(() => props.folio, loadVerification);
</script>

<template>
  <div class="min-h-screen bg-[var(--color-paper)] text-[var(--color-ink)]">
    <a href="#main-content" class="sr-only z-[100] rounded-md bg-white px-4 py-3 font-semibold text-[var(--color-ink)] focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus-visible:outline">
      Saltar al contenido principal
    </a>
    <InstitutionalHeader />

    <main id="main-content" tabindex="-1" class="mx-auto max-w-6xl px-4 py-9 sm:px-6 sm:py-12 lg:px-8 lg:py-16">

      <section
        class="mx-auto mt-8 max-w-5xl sm:mt-10"
        aria-live="polite"
        :aria-busy="state === 'loading'"
        aria-label="Resultado de la verificación"
      >
        <Transition name="verification-state" mode="out-in">
          <div
            v-if="state === 'loading'"
            key="loading"
            class="verification-state-panel rounded-[var(--radius-card)] border border-[var(--color-line)] bg-[var(--color-surface)] p-6 shadow-[var(--shadow-card)] sm:p-10"
          >
            <div class="flex items-center gap-4">
              <span aria-hidden="true" class="verification-spinner h-10 w-10 shrink-0 rounded-full border-[3px] border-[var(--color-line)] border-t-[var(--color-brand-900)]" />
              <div class="min-w-0 flex-1">
                <p class="text-xs font-bold uppercase tracking-[0.14em] text-[var(--color-muted)]">Consulta al registro</p>
                <h2 class="mt-1 text-xl font-bold text-[var(--color-brand-950)]">Verificando el folio</h2>
                <p class="mt-1 text-sm leading-6 text-[var(--color-muted)]">Estamos comprobando los datos de emisión.</p>
              </div>
            </div>
            <div aria-hidden="true" class="mt-8 grid gap-3 sm:grid-cols-2">
              <span class="verification-skeleton h-16 rounded-lg" />
              <span class="verification-skeleton h-16 rounded-lg" />
              <span class="verification-skeleton h-24 rounded-lg sm:col-span-2" />
            </div>
          </div>

          <div
            v-else-if="state === 'error'"
            key="error"
            class="verification-state-panel rounded-[var(--radius-card)] border border-[var(--color-line)] bg-[var(--color-surface)] p-6 text-center shadow-[var(--shadow-card)] sm:p-10"
            role="alert"
          >
            <CircleX :size="38" class="mx-auto text-[var(--color-danger)]" aria-hidden="true" />
            <p class="mt-5 text-xs font-bold uppercase tracking-[0.14em] text-[var(--color-muted)]">Servicio de verificación</p>
            <h2 class="mt-2 text-xl font-bold text-[var(--color-brand-950)]">No fue posible completar la consulta</h2>
            <p class="mx-auto mt-2 max-w-xl text-sm leading-6 text-[var(--color-muted)]">{{ error }}</p>
            <button
              type="button"
              class="page-control mt-6 inline-flex min-h-11 items-center justify-center rounded-[var(--radius-control)] border border-[var(--color-brand-700)] px-5 text-sm font-semibold text-[var(--color-brand-900)] hover:bg-[var(--color-brand-100)]"
              @click="loadVerification"
            >
              Intentar de nuevo
            </button>
          </div>

          <div
            v-else-if="state === 'invalid'"
            key="invalid"
            class="verification-state-panel rounded-[var(--radius-card)] border border-[var(--color-line)] bg-[var(--color-surface)] p-6 text-center shadow-[var(--shadow-card)] sm:p-10"
            role="status"
          >
            <CircleX :size="38" class="mx-auto text-[var(--color-danger)]" aria-hidden="true" />
            <p class="mt-5 text-xs font-bold uppercase tracking-[0.14em] text-[var(--color-muted)]">Resultado de la consulta</p>
            <h2 class="mt-2 text-xl font-bold text-[var(--color-brand-950)]">Constancia no válida</h2>
            <p class="mx-auto mt-2 max-w-xl text-sm leading-6 text-[var(--color-muted)]">{{ error }}</p>
            <p class="mt-5 border-t border-[var(--color-line)] pt-4 text-sm leading-6 text-[var(--color-muted)]">
              Comprueba que el folio se haya copiado completo y vuelve a escanear el código QR de la constancia.
            </p>
          </div>

          <div
            v-else-if="verification"
            key="valid"
            class="verification-state-panel verification-record grid overflow-hidden rounded-[var(--radius-card)] border border-[var(--color-line)] bg-[var(--color-surface)] shadow-[var(--shadow-card)]"
          >
            <aside class="verification-status-panel relative flex flex-col overflow-hidden bg-[var(--color-brand-900)] p-6 text-white sm:p-8 lg:p-10">
              <div class="verification-seal flex h-16 w-16 items-center justify-center rounded-full border border-white/30 bg-white/10">
                <BadgeCheck :size="34" stroke-width="1.7" aria-hidden="true" />
              </div>
              <p class="mt-8 text-xs font-bold uppercase tracking-[0.16em] text-white/75">Resultado de verificación</p>
              <h2 class="mt-2 text-2xl font-bold leading-tight sm:text-3xl">Constancia válida</h2>
              <p class="mt-3 text-sm leading-6 text-white/85">
                {{ verification.message || 'El folio coincide con un registro de emisión institucional.' }}
              </p>

              <div class="mt-8 border-t border-white/20 pt-6">
                <span class="inline-flex items-center gap-2 rounded-full bg-[var(--color-success-soft)] px-3 py-1.5 text-xs font-bold text-[var(--color-success)]">
                  <ShieldCheck :size="15" aria-hidden="true" />
                  Registro confirmado
                </span>
                <p class="mt-4 text-xs leading-5 text-white/75">
                  Consulta realizada en el sistema público de validación de FEDE.
                </p>
              </div>
            </aside>

            <div class="verification-record__details min-w-0 p-5 sm:p-8 lg:p-10">
              <div class="border-b border-[var(--color-line)] pb-5">
                <p class="text-xs font-bold uppercase tracking-[0.14em] text-[var(--color-muted)]">Registro digital</p>
                <h3 class="mt-2 text-xl font-bold text-[var(--color-brand-950)] sm:text-2xl">Datos de la constancia</h3>
              </div>

              <dl class="mt-6 grid gap-3 sm:grid-cols-2">
                <div class="min-w-0 rounded-lg border border-[var(--color-line)] bg-[var(--color-paper)] p-4">
                  <div class="flex items-center justify-between gap-2">
                    <dt class="text-xs font-bold uppercase tracking-[0.1em] text-[var(--color-muted)]">Folio de emisión</dt>
                    <button
                      type="button"
                      class="page-control inline-flex min-h-10 shrink-0 items-center gap-1.5 rounded-[var(--radius-control)] px-2 text-xs font-semibold text-[var(--color-brand-900)] hover:bg-[var(--color-surface)] disabled:cursor-wait disabled:opacity-60"
                      aria-label="Copiar folio de constancia"
                      :disabled="copyingTarget !== null"
                      @click="copyValue(formatCertificateFolio(verification.folio), 'folio')"
                    >
                      <Check v-if="copiedTarget === 'folio'" :size="15" aria-hidden="true" />
                      <Copy v-else :size="15" aria-hidden="true" />
                      <span>{{ copyingTarget === 'folio' ? 'Copiando…' : copiedTarget === 'folio' ? 'Copiado' : 'Copiar' }}</span>
                    </button>
                  </div>
                  <dd class="mt-2 font-mono text-sm font-semibold leading-6 text-[var(--color-brand-950)] [overflow-wrap:anywhere]">
                    {{ formatCertificateFolio(verification.folio) }}
                  </dd>
                </div>

                <div class="rounded-lg border border-[var(--color-line)] bg-[var(--color-paper)] p-4">
                  <dt class="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.1em] text-[var(--color-muted)]">
                    <CalendarDays :size="15" aria-hidden="true" />
                    Fecha de emisión
                  </dt>
                  <dd class="mt-3 text-sm font-semibold leading-6 text-[var(--color-brand-950)]">{{ issuedDate }}</dd>
                </div>
              </dl>

              <section class="mt-4 rounded-lg border border-[var(--color-line)] bg-[var(--color-paper)] p-4 sm:p-5" aria-labelledby="certificate-person">
                <div class="flex items-start gap-3">
                  <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--color-surface)] text-[var(--color-brand-900)]">
                    <UserRound :size="19" aria-hidden="true" />
                  </span>
                  <div class="min-w-0">
                    <p class="text-xs font-bold uppercase tracking-[0.12em] text-[var(--color-muted)]">Persona acreditada</p>
                    <h4 id="certificate-person" class="mt-1 text-lg font-bold leading-6 text-[var(--color-brand-950)] [overflow-wrap:anywhere]">
                      {{ formatCertificateName(verification.user_name) }}
                    </h4>
                    <dl v-if="verification.municipality || verification.sector" class="mt-4 flex flex-wrap gap-x-6 gap-y-3">
                      <div v-if="verification.municipality" class="flex items-start gap-2">
                        <MapPin :size="15" class="mt-0.5 shrink-0 text-[var(--color-muted)]" aria-hidden="true" />
                        <div>
                          <dt class="text-xs font-semibold text-[var(--color-muted)]">Municipio</dt>
                          <dd class="mt-0.5 text-sm font-medium text-[var(--color-brand-950)]">{{ verification.municipality }}</dd>
                        </div>
                      </div>
                      <div v-if="verification.sector" class="flex items-start gap-2">
                        <span class="mt-0.5 h-3.5 w-3.5 shrink-0 rounded-full border border-[var(--color-brand-700)]" aria-hidden="true" />
                        <div>
                          <dt class="text-xs font-semibold text-[var(--color-muted)]">Sector</dt>
                          <dd class="mt-0.5 text-sm font-medium text-[var(--color-brand-950)]">{{ verification.sector }}</dd>
                        </div>
                      </div>
                    </dl>
                  </div>
                </div>
              </section>

              <section class="mt-4 rounded-lg border border-[var(--color-line)] bg-[var(--color-paper)] p-4 sm:p-5" aria-labelledby="certificate-course">
                <div class="flex items-start gap-3">
                  <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--color-surface)] text-[var(--color-brand-900)]">
                    <BookOpen :size="19" aria-hidden="true" />
                  </span>
                  <div class="min-w-0">
                    <p class="text-xs font-bold uppercase tracking-[0.12em] text-[var(--color-muted)]">Curso acreditado</p>
                    <h4 id="certificate-course" class="mt-1 text-sm font-semibold leading-6 text-[var(--color-brand-950)]">
                      {{ verification.course.name }}
                    </h4>
                  </div>
                </div>
              </section>

              <div class="mt-6 flex flex-col items-start gap-3 border-t border-[var(--color-line)] pt-5 sm:flex-row sm:items-center sm:justify-between">
                <p class="text-sm leading-6 text-[var(--color-muted)]">Conserva este enlace para consultar el registro.</p>
                <button
                  type="button"
                  class="page-control page-press inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-[var(--radius-control)] border border-[var(--color-brand-700)] px-4 text-sm font-semibold text-[var(--color-brand-900)] hover:bg-[var(--color-brand-100)] disabled:cursor-wait disabled:opacity-60 sm:w-auto"
                  :disabled="copyingTarget !== null"
                  @click="copyVerificationLink"
                >
                  <Check v-if="copiedTarget === 'link'" :size="16" aria-hidden="true" />
                  <Link2 v-else :size="16" aria-hidden="true" />
                  {{ copyingTarget === 'link' ? 'Copiando…' : copiedTarget === 'link' ? 'Enlace copiado' : 'Copiar enlace' }}
                </button>
              </div>
              <p
                v-if="copyFeedback"
                role="status"
                aria-live="polite"
                class="mt-3 text-sm font-medium"
                :class="copyFeedbackIsError ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'"
              >
                {{ copyFeedback }}
              </p>
            </div>
          </div>
        </Transition>
      </section>

      <footer class="mx-auto mt-6 flex max-w-5xl items-start gap-2 text-sm leading-6 text-[var(--color-muted)] sm:mt-8">
        <ShieldCheck :size="17" class="mt-0.5 shrink-0" aria-hidden="true" />
        <p>La consulta es pública y no requiere iniciar sesión. Solo se muestran los datos necesarios para verificar la emisión.</p>
      </footer>
    </main>
  </div>
</template>

<style scoped>
.verification-intro {
  animation: verification-rise 420ms var(--ease-out) both;
}

.verification-seal {
  animation: seal-arrive 480ms var(--ease-out) 80ms both;
}

.verification-record {
  grid-template-columns: minmax(0, 1fr);
}

@media (min-width: 64rem) {
  .verification-record {
    grid-template-columns: minmax(16rem, 0.78fr) minmax(0, 1.62fr);
  }
}

.verification-state-enter-active,
.verification-state-leave-active {
  transition: opacity 180ms var(--ease-out), transform 180ms var(--ease-out);
}

.verification-state-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.verification-state-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.verification-spinner {
  animation: verification-spin 900ms linear infinite;
}

.verification-skeleton {
  background: linear-gradient(90deg, var(--color-paper), var(--color-surface), var(--color-paper));
  background-size: 200% 100%;
  animation: verification-shimmer 1.4s ease-in-out infinite;
}

.page-control {
  transition: color var(--motion-fast) var(--ease-out), background-color var(--motion-fast) var(--ease-out), border-color var(--motion-fast) var(--ease-out);
}

@keyframes verification-rise {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes seal-arrive {
  from { opacity: 0; transform: scale(0.88); }
  to { opacity: 1; transform: scale(1); }
}

@keyframes verification-spin {
  to { transform: rotate(360deg); }
}

@keyframes verification-shimmer {
  to { background-position: -200% 0; }
}

@media (prefers-reduced-motion: reduce) {
  .verification-intro,
  .verification-seal,
  .verification-spinner,
  .verification-skeleton {
    animation: none;
  }

  .verification-state-enter-active,
  .verification-state-leave-active {
    transition: none;
  }
}
</style>
