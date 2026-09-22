<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { LogIn, Mail, Lock, Eye, EyeOff, ShieldCheck, Loader2 } from 'lucide-vue-next';
import { useAuth } from '../lib/auth';

const emit = defineEmits<{ (e: 'success'): void; (e: 'go-register'): void }>();

const { login } = useAuth();

const email = ref('');
const password = ref('');
const showPassword = ref(false);
const loading = ref(false);
const error = ref('');

async function onSubmit() {
  error.value = '';
  if (!email.value || !password.value) return;

  loading.value = true;
  try {
    await login(email.value, password.value);
    emit('success');
  } catch (e: any) {
    error.value = e.message || 'No se pudo iniciar sesión.';
  } finally {
    loading.value = false;
  }
}

// ------------------------------------------------------------
// Fondo animado de partículas (canvas, sin dependencias externas)
// ------------------------------------------------------------
const canvasRef = ref<HTMLCanvasElement | null>(null);
let ctx: CanvasRenderingContext2D | null = null;
let animationFrame = 0;
let particles: { x: number; y: number; vx: number; vy: number; r: number }[] = [];

function resizeCanvas() {
  const canvas = canvasRef.value;
  if (!canvas) return;
  canvas.width = canvas.clientWidth * window.devicePixelRatio;
  canvas.height = canvas.clientHeight * window.devicePixelRatio;
}

function initParticles() {
  const canvas = canvasRef.value;
  if (!canvas) return;
  const count = Math.min(70, Math.floor((canvas.clientWidth * canvas.clientHeight) / 18000));
  particles = Array.from({ length: count }, () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    vx: (Math.random() - 0.5) * 0.35 * window.devicePixelRatio,
    vy: (Math.random() - 0.5) * 0.35 * window.devicePixelRatio,
    r: (Math.random() * 1.6 + 0.6) * window.devicePixelRatio,
  }));
}

function step() {
  const canvas = canvasRef.value;
  if (!canvas || !ctx) return;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  for (const p of particles) {
    p.x += p.vx;
    p.y += p.vy;

    if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
    if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(218,218,218,0.55)';
    ctx.fill();
  }

  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      const a = particles[i];
      const b = particles[j];
      const dx = a.x - b.x;
      const dy = a.y - b.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const maxDist = 130 * window.devicePixelRatio;

      if (dist < maxDist) {
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.strokeStyle = `rgba(135,135,135,${0.18 * (1 - dist / maxDist)})`;
        ctx.lineWidth = 1;
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
  <div class="relative min-h-screen overflow-hidden bg-[#3d3d3c] text-white">
    <!-- Fondo degradado institucional -->
    <div class="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(87,87,86,0.9),rgba(30,30,30,0.98)_60%)]"></div>
    <canvas ref="canvasRef" class="pointer-events-none absolute inset-0 h-full w-full"></canvas>

    <div class="relative z-10 flex min-h-screen flex-col items-center justify-center px-5 py-10">
      <div class="mb-8 flex flex-col items-center gap-3 text-center animate-fade-in-down">
        <div class="flex items-center gap-5 rounded-2xl bg-white/95 px-6 py-3 shadow-2xl shadow-black/30">
          <img src="/logo_fgjtam.png" alt="Logo FGJ Tamaulipas" class="h-12 w-auto object-contain" />
          <div class="h-8 w-px bg-[#dadada]"></div>
          <img src="/logo_fede.png" alt="Logo FEDE" class="h-12 w-auto object-contain" />
        </div>
        <p class="mt-2 text-xs font-semibold uppercase tracking-[0.3em] text-[#dadada]">
          Fiscalía Especializada en Delitos Electorales
        </p>
      </div>

      <div class="w-full max-w-md animate-fade-in-up">
        <div class="rounded-[28px] border border-white/10 bg-white/95 p-8 shadow-2xl shadow-black/40 backdrop-blur-xl md:p-10">
          <div class="mb-7 flex flex-col items-center text-center">
            <div class="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#575756] text-white shadow-lg">
              <ShieldCheck :size="26" />
            </div>
            <h1 class="mt-4 text-2xl font-black text-[#3d3d3c]">Acceso institucional</h1>
            <p class="mt-1 text-sm text-[#878787]">Ingresa con tu cuenta para continuar con la capacitación.</p>
          </div>

          <form class="space-y-4" @submit.prevent="onSubmit">
            <label class="block">
              <span class="mb-2 block text-sm font-semibold text-[#575756]">Correo electrónico</span>
              <div class="flex items-center gap-3 rounded-xl border border-[#dadada] bg-[#fafafa] px-4 py-3 focus-within:border-[#575756] focus-within:ring-2 focus-within:ring-[#dadada]">
                <Mail :size="18" class="shrink-0 text-[#878787]" />
                <input
                  v-model="email"
                  type="email"
                  required
                  autocomplete="username"
                  placeholder="nombre@tamaulipas.gob.mx"
                  class="w-full bg-transparent text-sm outline-none placeholder:text-[#b3b3b3]"
                />
              </div>
            </label>

            <label class="block">
              <span class="mb-2 block text-sm font-semibold text-[#575756]">Contraseña</span>
              <div class="flex items-center gap-3 rounded-xl border border-[#dadada] bg-[#fafafa] px-4 py-3 focus-within:border-[#575756] focus-within:ring-2 focus-within:ring-[#dadada]">
                <Lock :size="18" class="shrink-0 text-[#878787]" />
                <input
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  required
                  autocomplete="current-password"
                  placeholder="••••••••"
                  class="w-full bg-transparent text-sm outline-none placeholder:text-[#b3b3b3]"
                />
                <button type="button" @click="showPassword = !showPassword" class="shrink-0 text-[#878787] hover:text-[#575756]">
                  <EyeOff v-if="showPassword" :size="18" />
                  <Eye v-else :size="18" />
                </button>
              </div>
            </label>

            <p v-if="error" class="rounded-lg bg-red-50 px-3 py-2 text-sm font-medium text-red-600">
              {{ error }}
            </p>

            <button
              type="submit"
              :disabled="loading"
              class="flex w-full items-center justify-center gap-2 rounded-xl bg-[#575756] py-3.5 text-sm font-bold text-white transition hover:bg-[#454544] disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Loader2 v-if="loading" :size="18" class="animate-spin" />
              <LogIn v-else :size="18" />
              {{ loading ? 'Verificando…' : 'Iniciar sesión' }}
            </button>
          </form>

          <p class="mt-6 text-center text-sm text-[#878787]">
            ¿No tienes cuenta?
            <button type="button" @click="emit('go-register')" class="font-bold text-[#575756] hover:underline">
              Regístrate aquí
            </button>
          </p>
        </div>

        <p class="mt-6 text-center text-xs text-white/60">
          Fiscalía General de Justicia del Estado de Tamaulipas
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes fade-in-down {
  from { opacity: 0; transform: translateY(-16px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in-down { animation: fade-in-down 0.6s ease-out both; }
.animate-fade-in-up { animation: fade-in-up 0.6s 0.15s ease-out both; }
</style>