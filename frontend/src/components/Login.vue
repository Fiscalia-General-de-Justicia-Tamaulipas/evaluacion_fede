```vue
<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue';
import {
  LogIn,
  Mail,
  Lock,
  Eye,
  EyeOff,
  ShieldCheck,
  Loader2,
  AlertCircle,
  ArrowRight,
  UserPlus,
} from 'lucide-vue-next';

import { useAuth } from '../lib/auth';

const emit = defineEmits<{
  (e: 'success'): void;
  (e: 'go-register'): void;
}>();

const { login } = useAuth();

const email = ref('');
const password = ref('');
const showPassword = ref(false);
const loading = ref(false);
const error = ref('');
const capsLockOn = ref(false);

const emailInputRef = ref<HTMLInputElement | null>(null);

onMounted(() => {
  nextTick(() => {
    emailInputRef.value?.focus();
  });
});

function handlePasswordKeydown(e: KeyboardEvent) {
  capsLockOn.value = e.getModifierState?.('CapsLock') ?? false;
}

async function onSubmit() {
  if (loading.value) return;

  error.value = '';

  const trimmedEmail = email.value.trim();

  if (!trimmedEmail || !password.value) {
    error.value = 'Ingresa tu correo electrónico y contraseña.';
    return;
  }

  loading.value = true;

  try {
    await login(trimmedEmail, password.value);

    emit('success');
  } catch (e: any) {
    if (
      e?.message?.toLowerCase().includes('fetch') ||
      e?.message?.toLowerCase().includes('network')
    ) {
      error.value =
        'No fue posible conectar con el servidor. Verifica tu conexión e inténtalo nuevamente.';
    } else {
      error.value =
        e?.message ||
        'El correo electrónico o la contraseña no son correctos.';
    }
  } finally {
    loading.value = false;
  }
}

/*
|--------------------------------------------------------------------------
| Fondo animado
|--------------------------------------------------------------------------
*/

const canvasRef = ref<HTMLCanvasElement | null>(null);

let ctx: CanvasRenderingContext2D | null = null;
let animationFrame = 0;

let particles: {
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
}[] = [];

function resizeCanvas() {
  const canvas = canvasRef.value;

  if (!canvas) return;

  const dpr = Math.min(window.devicePixelRatio || 1, 2);

  canvas.width = canvas.clientWidth * dpr;
  canvas.height = canvas.clientHeight * dpr;

  ctx?.setTransform(dpr, 0, 0, dpr, 0, 0);
}

function initParticles() {
  const canvas = canvasRef.value;

  if (!canvas) return;

  const area = canvas.clientWidth * canvas.clientHeight;

  const count = Math.min(
    42,
    Math.max(16, Math.floor(area / 22000))
  );

  particles = Array.from({ length: count }, () => ({
    x: Math.random() * canvas.clientWidth,
    y: Math.random() * canvas.clientHeight,
    vx: (Math.random() - 0.5) * 0.16,
    vy: (Math.random() - 0.5) * 0.16,
    r: Math.random() * 1.2 + 0.5,
  }));
}

function step() {
  const canvas = canvasRef.value;

  if (!canvas || !ctx) return;

  if (
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
  ) {
    return;
  }

  const width = canvas.clientWidth;
  const height = canvas.clientHeight;

  ctx.clearRect(0, 0, width, height);

  for (const p of particles) {
    p.x += p.vx;
    p.y += p.vy;

    if (p.x < -10 || p.x > width + 10) {
      p.vx *= -1;
    }

    if (p.y < -10 || p.y > height + 10) {
      p.vy *= -1;
    }

    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);

    ctx.fillStyle = 'rgba(255,255,255,0.20)';
    ctx.fill();
  }

  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      const a = particles[i];
      const b = particles[j];

      const dx = a.x - b.x;
      const dy = a.y - b.y;

      const dist = Math.sqrt(dx * dx + dy * dy);
      const maxDist = 110;

      if (dist < maxDist) {
        ctx.beginPath();

        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);

        ctx.strokeStyle = `rgba(255,255,255,${
          0.045 * (1 - dist / maxDist)
        })`;

        ctx.lineWidth = 0.7;
        ctx.stroke();
      }
    }
  }

  animationFrame = requestAnimationFrame(step);
}

function handleResize() {
  resizeCanvas();
  initParticles();
}

onMounted(() => {
  const canvas = canvasRef.value;

  if (canvas) {
    ctx = canvas.getContext('2d');

    resizeCanvas();
    initParticles();
    step();
  }

  window.addEventListener('resize', handleResize);
});

onBeforeUnmount(() => {
  cancelAnimationFrame(animationFrame);
  window.removeEventListener('resize', handleResize);
});
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
         MAIN LAYOUT
    ================================================================= -->

    <div
      class="relative z-10 min-h-screen lg:grid lg:grid-cols-[1.05fr_0.95fr]"
    >
      <!-- ============================================================
           LEFT
      ============================================================= -->

      <section
        class="relative hidden min-h-screen overflow-hidden bg-[#292928] lg:flex lg:flex-col lg:justify-between"
      >
        <!-- Background -->

        <div
          class="absolute inset-0 bg-[radial-gradient(circle_at_20%_15%,rgba(135,135,135,0.20),transparent_34%),radial-gradient(circle_at_80%_85%,rgba(255,255,255,0.06),transparent_32%),linear-gradient(145deg,#363635_0%,#252524_55%,#1e1e1d_100%)]"
        />

        <canvas
          ref="canvasRef"
          class="pointer-events-none absolute inset-0 h-full w-full"
          aria-hidden="true"
        />

        <!-- Subtle grid -->

        <div
          class="pointer-events-none absolute inset-0 opacity-[0.025]"
          style="
            background-image:
              linear-gradient(rgba(255,255,255,.5) 1px, transparent 1px),
              linear-gradient(90deg, rgba(255,255,255,.5) 1px, transparent 1px);
            background-size: 52px 52px;
          "
        />

        <!-- Logos -->

        <div class="relative z-10 px-12 pt-12 xl:px-16">
          <div class="flex items-center gap-4">
            <div
              class="flex h-12 items-center rounded-xl bg-white px-4 shadow-2xl shadow-black/20"
            >
              <img
                src="/logo_fgjtam.png"
                alt="Fiscalía General de Justicia de Tamaulipas"
                class="h-8 w-auto object-contain"
              />
            </div>

            <div class="h-7 w-px bg-white/15" />

            <img
              src="/logo_fede.png"
              alt="FEDE"
              class="h-10 w-auto object-contain brightness-0 invert opacity-90"
            />
          </div>
        </div>

        <!-- Course information -->

        <div class="relative z-10 max-w-xl px-12 pb-20 xl:px-16">
          <p
            class="mb-5 text-[11px] font-bold uppercase tracking-[0.24em] text-white/45"
          >
            Plataforma de capacitación
          </p>

          <h2
            class="max-w-lg text-4xl font-semibold leading-[1.08] tracking-[-0.03em] text-white xl:text-[52px]"
          >
            Fiscalía Especializada
            <br />
            en Delitos Electorales
          </h2>

          <p
            class="mt-7 max-w-md text-base leading-7 text-white/50"
          >
            Accede a los contenidos, actividades y evaluaciones
            correspondientes a tu curso.
          </p>

          <div class="mt-9 h-px w-16 bg-white/20" />
        </div>

        <!-- Footer -->

        <div
          class="relative z-10 border-t border-white/[0.07] px-12 py-6 text-[11px] text-white/30 xl:px-16"
        >
          Fiscalía General de Justicia del Estado de Tamaulipas
        </div>
      </section>

      <!-- ============================================================
           RIGHT
      ============================================================= -->

      <section
        class="relative flex min-h-screen items-center justify-center px-5 py-8 sm:px-8 lg:px-12 xl:px-20"
      >
        <div class="w-full max-w-[460px]">
          <!-- Mobile logos -->

          <div
            class="mb-10 flex flex-col items-center text-center lg:hidden"
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

            <p
              class="mt-4 text-[10px] font-bold uppercase tracking-[0.22em] text-[#999998]"
            >
              Plataforma de capacitación
            </p>
          </div>

          <!-- Login -->

          <div
            class="animate-login rounded-[28px] border border-black/[0.055] bg-white p-7 shadow-[0_24px_80px_rgba(0,0,0,0.08)] sm:p-9"
          >
            <!-- Heading -->

            <div>
              <div
                class="mb-6 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#292928] text-white shadow-lg shadow-black/10"
              >
                <LogIn
                  :size="21"
                  stroke-width="1.8"
                />
              </div>

              <h1
                class="text-[32px] font-semibold tracking-[-0.035em] text-[#292928]"
              >
                Bienvenido
              </h1>

              <p
                class="mt-2.5 max-w-sm text-sm leading-6 text-[#888887]"
              >
                Ingresa a tu cuenta para continuar con tu curso.
              </p>
            </div>

            <!-- Form -->

            <form
              class="mt-8 space-y-5"
              @submit.prevent="onSubmit"
              novalidate
            >
              <!-- Email -->

              <label class="block">
                <span
                  class="mb-2 block text-[13px] font-semibold text-[#454544]"
                >
                  Correo electrónico
                </span>

                <div
                  class="group flex h-[52px] items-center gap-3 rounded-2xl border bg-[#fafafa] px-4 transition-all duration-200"
                  :class="
                    error
                      ? 'border-red-200 bg-red-50/30 focus-within:border-red-400 focus-within:ring-4 focus-within:ring-red-500/5'
                      : 'border-[#e4e4e3] hover:border-[#cfcfce] focus-within:border-[#4a4a49] focus-within:bg-white focus-within:ring-4 focus-within:ring-black/[0.035]'
                  "
                >
                  <Mail
                    :size="18"
                    stroke-width="1.8"
                    class="shrink-0 text-[#a5a5a4] transition-colors group-focus-within:text-[#555554]"
                  />

                  <input
                    ref="emailInputRef"
                    v-model="email"
                    type="email"
                    required
                    autocomplete="username"
                    placeholder="Tu correo electrónico"
                    :disabled="loading"
                    :aria-invalid="!!error"
                    aria-describedby="login-error"
                    class="w-full bg-transparent text-sm font-medium text-[#292928] outline-none placeholder:text-[#b8b8b7] disabled:cursor-not-allowed disabled:opacity-50"
                  />
                </div>
              </label>

              <!-- Password -->

              <label class="block">
                <span
                  class="mb-2 block text-[13px] font-semibold text-[#454544]"
                >
                  Contraseña
                </span>

                <div
                  class="group flex h-[52px] items-center gap-3 rounded-2xl border bg-[#fafafa] px-4 transition-all duration-200"
                  :class="
                    error
                      ? 'border-red-200 bg-red-50/30 focus-within:border-red-400 focus-within:ring-4 focus-within:ring-red-500/5'
                      : 'border-[#e4e4e3] hover:border-[#cfcfce] focus-within:border-[#4a4a49] focus-within:bg-white focus-within:ring-4 focus-within:ring-black/[0.035]'
                  "
                >
                  <Lock
                    :size="18"
                    stroke-width="1.8"
                    class="shrink-0 text-[#a5a5a4] transition-colors group-focus-within:text-[#555554]"
                  />

                  <input
                    v-model="password"
                    :type="showPassword ? 'text' : 'password'"
                    required
                    autocomplete="current-password"
                    placeholder="Ingresa tu contraseña"
                    :disabled="loading"
                    :aria-invalid="!!error"
                    aria-describedby="login-error"
                    @keyup="handlePasswordKeydown"
                    @keydown="handlePasswordKeydown"
                    class="w-full bg-transparent text-sm font-medium tracking-wide text-[#292928] outline-none placeholder:text-[#b8b8b7] disabled:cursor-not-allowed disabled:opacity-50"
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
                    class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[#a0a09f] transition hover:bg-black/[0.04] hover:text-[#444443] disabled:pointer-events-none"
                  >
                    <EyeOff
                      v-if="showPassword"
                      :size="18"
                      stroke-width="1.8"
                    />

                    <Eye
                      v-else
                      :size="18"
                      stroke-width="1.8"
                    />
                  </button>
                </div>

                <Transition name="fade">
                  <p
                    v-if="capsLockOn"
                    class="mt-2.5 flex items-center gap-1.5 text-xs font-medium text-amber-600"
                  >
                    <AlertCircle :size="13" />
                    Bloq Mayús está activado
                  </p>
                </Transition>
              </label>

              <!-- Error -->

              <Transition name="fade">
                <div
                  v-if="error"
                  id="login-error"
                  role="alert"
                  aria-live="assertive"
                  class="flex items-start gap-3 rounded-2xl border border-red-100 bg-red-50 px-4 py-3.5 text-sm text-red-700"
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

              <!-- Submit -->

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

                <LogIn
                  v-else
                  :size="18"
                  stroke-width="2"
                  class="relative"
                />

                <span class="relative">
                  {{ loading ? 'Verificando…' : 'Iniciar sesión' }}
                </span>
              </button>
            </form>

            <!-- Register -->

            <div class="mt-7 border-t border-[#eeeeed] pt-7">
              <p class="mb-3 text-center text-xs text-[#999998]">
                ¿Aún no tienes una cuenta?
              </p>

              <button
                type="button"
                :disabled="loading"
                @click="emit('go-register')"
                class="group flex w-full items-center justify-center gap-2.5 rounded-2xl border border-[#dededd] bg-white py-3.5 text-sm font-semibold text-[#444443] transition-all duration-200 hover:border-[#bdbdbc] hover:bg-[#fafafa] hover:text-[#292928] disabled:pointer-events-none disabled:opacity-50"
              >
                <UserPlus
                  :size="17"
                  stroke-width="1.8"
                />

                <span>
                  Crear una cuenta
                </span>
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
      </section>
    </div>
  </main>
</template>

<style scoped>
@keyframes login-in {
  from {
    opacity: 0;
    transform: translateY(16px) scale(0.985);
  }

  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.animate-login {
  animation: login-in 0.55s cubic-bezier(0.22, 1, 0.36, 1) both;
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
  .animate-login {
    animation: none;
  }

  .fade-enter-active,
  .fade-leave-active {
    transition: none;
  }
}
</style>

