<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { ChevronLeft, ChevronRight, CheckCircle2, ShieldCheck, PlayCircle, ClipboardCheck, LockKeyhole, RotateCcw } from 'lucide-vue-next';

type Option = { id: number; letter: string; text: string }; type Question = { id: number; number: number; text: string; options: Option[] };
const API = import.meta.env.VITE_API_URL;
const stage = ref<'intro' | 'identity' | 'exam' | 'result'>('intro'); const videoDone = ref(false); const videoStarted = ref(false); const evaluationId = ref<number | null>(null); const questions = ref<Question[]>([]); const current = ref(0); const answers = ref<Record<number, number>>({}); const loading = ref(false); const result = ref({ score: 0, correct: 0, total: 0 });
const form = ref({ first_name: '', paternal_surname: '', maternal_surname: '' });
const q = computed(() => questions.value[current.value]); const answeredCount = computed(() => Object.keys(answers.value).length); const progress = computed(() => questions.value.length ? ((current.value + 1) / questions.value.length) * 100 : 0); const canNext = computed(() => q.value && answers.value[q.value.id] != null); const fullName = computed(() => `${form.value.first_name} ${form.value.paternal_surname} ${form.value.maternal_surname}`.trim());
async function loadQuestions() { questions.value = await (await fetch(`${API}/questions`)).json() }
async function beginIdentity() { if (!videoDone.value) return; stage.value = 'identity' }
async function startExam() { if (!form.value.first_name || !form.value.paternal_surname || !form.value.maternal_surname) return; loading.value = true; const r = await fetch(`${API}/evaluations/start`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form.value) }); const data = await r.json(); evaluationId.value = data.evaluation_id; await loadQuestions(); stage.value = 'exam'; loading.value = false }
async function videoEnded() { videoDone.value = true; if (evaluationId.value) await fetch(`${API}/evaluations/${evaluationId.value}/video-completed`, { method: 'POST' }) }
function selectOption(id: number) { answers.value[q.value.id] = id }
function previous() { if (current.value > 0) current.value-- } function next() { if (current.value < questions.value.length - 1) current.value++ }
async function finish() { if (answeredCount.value !== questions.value.length) return; loading.value = true; const payload = { answers: questions.value.map(x => ({ question_id: x.id, option_id: answers.value[x.id] })) }; const r = await fetch(`${API}/evaluations/${evaluationId.value}/finish`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }); result.value = await r.json(); stage.value = 'result'; loading.value = false }
function restart() { location.reload() }
onMounted(loadQuestions)
</script>
<template>
    <header>
        <title>Evaluación de capacitación - Fiscalía Especializada en Delitos Electorales</title>
    </header>
    <div class="min-h-screen bg-[#f4f4f3] text-[#575756]">
        <header class="border-b border-[#dadada] bg-white/95 backdrop-blur sticky top-0 z-20">
            <div class="mx-auto flex max-w-6xl items-center gap-4 px-5 py-4">
                <div class="flex items-center gap-4">
                    <img src="/logo_fgjtam.png" alt="Logo FGJ Tamaulipas"
                        class="h-14 w-auto object-contain opacity-95" />
                </div>
                <div class="ml-auto flex items-center gap-3">
                    <img src="/logo_fede.png" alt="Logo FEDE" class="h-15 w-auto object-contain opacity-95" />
                </div>
            </div>
        </header>
        <main class="mx-auto max-w-6xl px-5 py-8 md:py-6">
            <section v-if="stage === 'intro'" class="flex flex-col items-center">
                <div class="mx-auto max-w-4xl text-center">
                    <span
                        class="inline-flex items-center gap-2 rounded-full bg-[#dadada]/60 px-3 py-1 text-xs font-semibold uppercase tracking-wider">
                        <PlayCircle :size="14" /> Material introductorio
                    </span>
                    <h2 class="mt-5 text-4xl font-black tracking-tight md:text-5xl lg:text-4xl">
                        Delitos Electorales y su investigación en el contexto de los Procesos Electorales Locales.
                    </h2>
                    <p class="mt-5 mx-auto max-w-3xl text-base leading-7 text-[#878787] md:text-lg">Visualiza el
                        material completo antes de
                        acceder a la evaluación del <br><b>Módulo 1: Nociones básicas de derecho electoral.</b></p>
                    <div class="mt-7 flex items-center justify-center gap-3 text-sm text-[#878787]">
                        <LockKeyhole :size="17" /> La evaluación se habilita al concluir el video.
                    </div>
                </div>

                <div class="mt-8 w-full max-w-6xl">
                    <div
                        class="mx-auto max-w-5xl rounded-[32px] border border-[#dadada] bg-white p-3 shadow-xl shadow-black/5 md:p-4">
                        <div class="overflow-hidden rounded-[26px] bg-[#575756]">
                            <video class="block aspect-video w-full object-cover" controls playsinline
                                preload="metadata" @play="videoStarted = true" @ended="videoEnded">
                                <source src="/curso-modulo1.mp4" type="video/mp4" />Tu navegador no soporta video HTML5.
                            </video>
                        </div>
                        <div
                            class="flex flex-col items-center justify-between gap-4 px-2 py-4 text-center sm:flex-row sm:text-left">
                            <div>
                                <p class="text-sm font-bold">Material de capacitación</p>
                                <p class="text-xs text-[#878787]">Reproducción completa requerida</p>
                            </div>
                            <button @click="beginIdentity" :disabled="!videoDone"
                                class="rounded-xl px-5 py-3 text-sm font-bold text-white transition disabled:cursor-not-allowed disabled:opacity-40 bg-[#575756] hover:bg-[#454544]">
                                Contestar evaluación
                            </button>
                        </div>
                    </div>
                </div>
            </section>
            <section v-else-if="stage === 'identity'" class="mx-auto max-w-2xl">
                <div class="rounded-3xl border border-[#dadada] bg-white p-7 shadow-xl shadow-black/5 md:p-10">
                    <div class="mb-8"><span class="text-xs font-bold uppercase tracking-widest text-[#878787]">Paso 1 de
                            2</span>
                        <h2 class="mt-2 text-3xl font-black">Datos del participante</h2>
                        <p class="mt-2 text-sm text-[#878787]">Captura tu nombre tal como deberá aparecer en el registro
                            de evaluación.</p>
                    </div>
                    <div class="space-y-5"><label class="block"><span
                                class="mb-2 block text-sm font-semibold">Nombre(s)</span><input
                                v-model="form.first_name"
                                class="w-full rounded-xl border border-[#dadada] bg-[#fafafa] px-4 py-3 outline-none focus:border-[#878787] focus:ring-2 focus:ring-[#dadada]"
                                placeholder="Nombre(s)" /></label>
                        <div class="grid gap-5 md:grid-cols-2"><label><span
                                    class="mb-2 block text-sm font-semibold">Apellido paterno</span><input
                                    v-model="form.paternal_surname"
                                    class="w-full rounded-xl border border-[#dadada] bg-[#fafafa] px-4 py-3 outline-none focus:border-[#878787]" /></label><label><span
                                    class="mb-2 block text-sm font-semibold">Apellido materno</span><input
                                    v-model="form.maternal_surname"
                                    class="w-full rounded-xl border border-[#dadada] bg-[#fafafa] px-4 py-3 outline-none focus:border-[#878787]" /></label>
                        </div>
                        <div class="rounded-2xl bg-[#f4f4f3] p-4 text-sm"><b>Participante:</b> {{ fullName || '—' }}
                        </div><button @click="startExam"
                            :disabled="loading || !form.first_name || !form.paternal_surname || !form.maternal_surname"
                            class="w-full rounded-xl bg-[#575756] py-3.5 font-bold text-white disabled:opacity-40">
                            {{ loading ? 'Preparando evaluación…' : 'Iniciar evaluación' }}
                        </button>
                    </div>
                </div>
            </section>
            <section v-else-if="stage === 'exam'" class="mx-auto max-w-4xl">
                <div class="mb-5 flex items-center justify-between">
                    <div>
                        <p class="text-xs font-bold uppercase tracking-widest text-[#878787]">Módulo 1</p>
                        <h2 class="text-xl font-black">Nociones básicas de derecho electoral</h2>
                    </div>
                    <div class="text-right">
                        <p class="text-sm font-bold">{{ current + 1 }} / {{ questions.length }}</p>
                        <p class="text-xs text-[#878787]">{{ answeredCount }} contestadas</p>
                    </div>
                </div>
                <div class="h-2 overflow-hidden rounded-full bg-[#dadada]">
                    <div class="h-full rounded-full bg-[#575756] transition-all duration-500"
                        :style="{ width: progress + '%' }"></div>
                </div>
                <div class="mt-8 rounded-3xl border border-[#dadada] bg-white p-6 shadow-xl shadow-black/5 md:p-10">
                    <Transition name="fade" mode="out-in">
                        <div :key="q.id">
                            <div class="flex items-start gap-4"><span
                                    class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#575756] text-sm font-black text-white">{{
                                        q.number }}</span>
                                <h3 class="text-xl font-bold leading-8 md:text-2xl">{{ q.text }}</h3>
                            </div>
                            <div class="mt-8 space-y-3"> <button v-for="o in q.options" :key="o.id"
                                    @click="selectOption(o.id)"
                                    class="group flex w-full items-start gap-4 rounded-2xl border p-4 text-left transition"
                                    :class="answers[q.id] === o.id ? 'border-[#575756] bg-[#f0f0ef] shadow-sm' : 'border-[#dadada] hover:border-[#878787] hover:bg-[#fafafa]'"><span
                                        class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border text-sm font-bold"
                                        :class="answers[q.id] === o.id ? 'border-[#575756] bg-[#575756] text-white' : 'border-[#dadada] text-[#878787]'">{{
                                            o.letter.toUpperCase() }}</span><span
                                        class="pt-1 text-sm leading-6 md:text-base">{{ o.text }}</span>
                                    <CheckCircle2 v-if="answers[q.id] === o.id" class="ml-auto mt-1 shrink-0"
                                        :size="20" />
                                </button></div>
                        </div>
                    </Transition>
                    <div class="mt-9 flex items-center justify-between border-t border-[#dadada] pt-5"><button
                            @click="previous" :disabled="current === 0"
                            class="inline-flex items-center gap-2 rounded-xl px-4 py-3 text-sm font-bold disabled:opacity-30">
                            <ChevronLeft :size="18" /> Anterior
                        </button><button v-if="current < questions.length - 1" @click="next" :disabled="!canNext"
                            class="inline-flex items-center gap-2 rounded-xl bg-[#575756] px-5 py-3 text-sm font-bold text-white disabled:opacity-30">Siguiente
                            <ChevronRight :size="18" />
                        </button><button v-else @click="finish"
                            :disabled="answeredCount !== questions.length || loading"
                            class="inline-flex items-center gap-2 rounded-xl bg-[#575756] px-5 py-3 text-sm font-bold text-white disabled:opacity-30">
                            {{ loading ? 'Guardando…' : 'Finalizar evaluación' }}
                            <CheckCircle2 :size="18" />
                        </button></div>
                </div>
                <div class="mt-5 flex flex-wrap gap-2"> <button v-for="(item, i) in questions" :key="item.id"
                        @click="current = i" class="h-8 w-8 rounded-lg text-xs font-bold"
                        :class="i === current ? 'bg-[#575756] text-white' : answers[item.id] ? 'bg-[#dadada] text-[#575756]' : 'bg-white border border-[#dadada] text-[#878787]'">{{
                            i + 1 }}</button>
                </div>
            </section>
            <section v-else class="mx-auto max-w-3xl">
                <div
                    class="overflow-hidden rounded-[32px] border border-[#dadada] bg-white text-center shadow-xl shadow-black/5">
                    <div class="bg-[#575756] px-6 py-14 text-white">
                        <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-white/10">
                            <ClipboardCheck :size="34" />
                        </div>
                        <p class="mt-5 text-xs font-bold uppercase tracking-[.25em] text-white/70">Finalización</p>
                        <h2 class="mt-2 text-3xl font-black md:text-4xl">¡Evaluación finalizada!</h2>
                    </div>
                    <div class="p-8 md:p-10">
                        <p class="text-lg font-bold text-[#575756]">{{ fullName || 'Participante registrado' }}</p>
                        <p class="mt-4 text-base leading-7 text-[#878787]">
                            Gracias por completar el módulo de capacitación. Tu participación ha sido registrada de forma
                            exitosa en la plataforma institucional.
                        </p>
                        <button @click="restart"
                            class="mt-8 inline-flex items-center gap-2 rounded-xl bg-[#575756] px-5 py-3 text-sm font-bold text-white hover:bg-[#454544]">
                            <RotateCcw :size="17" /> Nueva evaluación
                        </button>
                    </div>
                </div>
            </section>
        </main>
        <footer class="mx-auto max-w-6xl px-5 pb-8 text-center text-xs text-[#878787]">Fiscalía General de Justicia del
            Estado de Tamaulipas · Fiscalía Especializada en Delitos Electorales</footer>
    </div>
</template>
