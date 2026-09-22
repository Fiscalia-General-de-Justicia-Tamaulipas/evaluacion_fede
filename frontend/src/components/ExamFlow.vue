<script setup lang="ts">
import {
    computed,
    onMounted,
    onUnmounted,
    ref,
} from 'vue';

import {
    ChevronLeft,
    ChevronRight,
    ChevronDown,
    CheckCircle2,
    PlayCircle,
    ClipboardCheck,
    LockKeyhole,
    RotateCcw,
    LogOut,
    FileText,
    X,
} from 'lucide-vue-next';

import * as pdfjsLib from 'pdfjs-dist';

import { useAuth } from '../lib/auth';


/* =========================================================
   PDF.JS WORKER
========================================================= */

pdfjsLib.GlobalWorkerOptions.workerSrc =
    `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.mjs`;


/* =========================================================
   TYPES
========================================================= */

type Option = {
    id: number;
    letter: string;
    text: string;
};

type Question = {
    id: number;
    number: number;
    text: string;
    options: Option[];
};

type SavedAnswer = {
    question_id: number;
    option_id: number;
};

type SupportDocument = {
    id: number;
    title: string;
    description?: string;
    url: string;
};

type EvaluationStartResponse = {
    evaluation_id: number;
    resumed: boolean;
    video_completed: boolean;
    current_question: number;
    answers: SavedAnswer[];
};

type CurrentEvaluationResponse = {
    has_evaluation: boolean;

    evaluation: {
        id: number;
        video_completed: boolean;
        started_at: string;
        current_question: number;
        answered_count: number;
        total_questions: number;
        answers: SavedAnswer[];
    } | null;
};

type Result = {
    score: number;
    correct: number;
    total: number;
};


/* =========================================================
   AUTH
========================================================= */

const {
    user,
    fullName,
    apiFetch,
    logout,
} = useAuth();


/* =========================================================
   STATE
========================================================= */

const stage = ref<
    'intro' |
    'exam' |
    'result'
>('intro');

const videoDone = ref(false);

const evaluationId = ref<
    number | null
>(null);

const questions = ref<Question[]>([]);

const current = ref(0);

const answers = ref<
    Record<number, number>
>({});

const loading = ref(false);

const savingAnswer = ref(false);

const result = ref<Result>({
    score: 0,
    correct: 0,
    total: 0,
});


/* =========================================================
   SUPPORT DOCUMENTS STATE
========================================================= */

/*
 * Ajusta esta lista con los PDF reales del módulo.
 * Las rutas deben apuntar a archivos servidos por el
 * proyecto (por ejemplo, dentro de /public/docs/...).
 */
const supportDocuments = ref<SupportDocument[]>([
    {
        id: 1,
        title: 'Elecciones y democracia',
        url: '/docs/Elecciones y Democracia.pdf',
    },
    {
        id: 2,
        title: 'Ley de Medios de Impugnacion Electorales',
        url: '/docs/Ley de Medios de Impugnacion Electorales 29-mayo-2025-2.pdf',
    },
    {
        id: 3,
        title: 'Ley Electoral del Estado de Tamaulipas',
        url: '/docs/Ley Electoral del Estado de Tamaulipas 29-mayo-2026-1-.pdf',
    },
    {
        id: 4,
        title: 'Ley General en Materia de Delitos Electorales',
        url: '/docs/LGMDE_200521 (2).pdf',
    },
    {
        id: 5,
        title: 'Constitución Política de los Estados Unidos Mexicanos',
        url: '/docs/CPEUM.pdf',
    },
    {
        id: 6,
        title: 'Ley General de Partidos Politicos',
        url: '/docs/LGPP (1).pdf',
    },
    {
        id: 7,
        title: 'Derecho Electoral Mexicano',
        url: '/docs/derecho electoral mexicano.pdf',
    },
    {
        id: 8,
        title: 'Derecho Humano al Voto',
        url: '/docs/derecho humano al voto.pdf',
    },
]);

const docsMenuOpen = ref(false);

const docsMenuRef = ref<HTMLElement | null>(null);

const viewingDoc = ref<SupportDocument | null>(null);

const thumbnails = ref<
    Record<number, string>
>({});


/* =========================================================
   COMPUTED
========================================================= */

const q = computed(() => {
    return questions.value[
        current.value
    ];
});


const answeredCount = computed(() => {
    return Object.keys(
        answers.value
    ).length;
});


const progress = computed(() => {

    if (!questions.value.length) {
        return 0;
    }

    return (
        (
            (current.value + 1) /
            questions.value.length
        ) * 100
    );
});


const canNext = computed(() => {

    if (!q.value) {
        return false;
    }

    return (
        answers.value[q.value.id] != null
    );
});


const isLastQuestion = computed(() => {

    return (
        questions.value.length > 0 &&
        current.value ===
        questions.value.length - 1
    );
});


const allAnswered = computed(() => {

    return (
        questions.value.length > 0 &&
        answeredCount.value ===
        questions.value.length
    );
});


/* =========================================================
   LOAD QUESTIONS
========================================================= */

async function loadQuestions() {

    try {

        const response = await apiFetch(
            '/api/questions'
        );

        if (!response.ok) {
            throw new Error(
                'No se pudieron cargar las preguntas.'
            );
        }

        questions.value =
            await response.json();

    } catch (error) {

        console.error(
            'Error cargando preguntas:',
            error
        );

        questions.value = [];
    }
}


/* =========================================================
   SUPPORT DOCUMENTS: THUMBNAILS
========================================================= */

async function generateThumbnail(
    doc: SupportDocument
) {

    try {

        const loadingTask =
            pdfjsLib.getDocument(doc.url);

        const pdf =
            await loadingTask.promise;

        const page =
            await pdf.getPage(1);

        const viewport =
            page.getViewport({
                scale: 0.5,
            });

        const canvas =
            document.createElement(
                'canvas'
            );

        canvas.width = viewport.width;
        canvas.height = viewport.height;

        const context =
            canvas.getContext('2d');

        if (!context) {
            return;
        }

        await page.render({
            canvasContext: context,
            viewport,
        }).promise;

        thumbnails.value[doc.id] =
            canvas.toDataURL('image/png');

    } catch (error) {

        console.error(
            `Error generando miniatura de "${doc.title}":`,
            error
        );
    }
}


function generateAllThumbnails() {

    supportDocuments.value.forEach(
        (doc) => generateThumbnail(doc)
    );
}


/* =========================================================
   SUPPORT DOCUMENTS: MENU + VIEWER
========================================================= */

function toggleDocsMenu() {

    docsMenuOpen.value =
        !docsMenuOpen.value;
}


function openDocument(
    doc: SupportDocument
) {

    viewingDoc.value = doc;
    docsMenuOpen.value = false;
}


function closeViewer() {

    viewingDoc.value = null;
}


function handleClickOutside(
    event: MouseEvent
) {

    if (
        docsMenuRef.value &&
        !docsMenuRef.value.contains(
            event.target as Node
        )
    ) {
        docsMenuOpen.value = false;
    }
}


function handleEscape(
    event: KeyboardEvent
) {

    if (event.key === 'Escape') {

        docsMenuOpen.value = false;
        viewingDoc.value = null;
    }
}


/* =========================================================
   RESTORE ANSWERS
========================================================= */

function restoreAnswers(
    savedAnswers: SavedAnswer[]
) {

    const restored:
        Record<number, number> = {};

    for (
        const answer
        of savedAnswers
    ) {

        restored[
            answer.question_id
        ] = answer.option_id;
    }

    answers.value = restored;
}


/* =========================================================
   RESTORE CURRENT EVALUATION
========================================================= */

async function restoreEvaluation() {

    try {

        const response = await apiFetch(
            '/api/evaluations/current'
        );

        if (!response.ok) {
            return;
        }

        const data:
            CurrentEvaluationResponse =
            await response.json();

        if (
            !data.has_evaluation ||
            !data.evaluation
        ) {
            return;
        }

        const evaluation =
            data.evaluation;

        evaluationId.value =
            evaluation.id;

        videoDone.value =
            evaluation.video_completed;

        restoreAnswers(
            evaluation.answers ?? []
        );

        /*
         * Si ya terminó el video,
         * podemos entrar directamente
         * al examen.
         */
        if (
            evaluation.video_completed
        ) {

            stage.value = 'exam';

            if (
                questions.value.length > 0
            ) {

                current.value =
                    Math.min(
                        Math.max(
                            evaluation.current_question ?? 0,
                            0
                        ),
                        questions.value.length - 1
                    );
            }
        }

    } catch (error) {

        console.error(
            'Error recuperando evaluación:',
            error
        );
    }
}


/* =========================================================
   VIDEO
========================================================= */

function videoEnded() {

    videoDone.value = true;
}


/* =========================================================
   START / RESUME EXAM
========================================================= */

async function startExam() {

    if (
        !videoDone.value ||
        loading.value
    ) {
        return;
    }

    loading.value = true;

    try {

        const response =
            await apiFetch(
                '/api/evaluations/start',
                {
                    method: 'POST',
                }
            );

        if (!response.ok) {

            const errorData =
                await response.json()
                    .catch(() => null);

            throw new Error(
                errorData?.detail ||
                'No se pudo iniciar la evaluación.'
            );
        }

        const data:
            EvaluationStartResponse =
            await response.json();

        evaluationId.value =
            data.evaluation_id;

        /*
         * Recuperar respuestas.
         */
        restoreAnswers(
            data.answers ?? []
        );

        /*
         * Recuperar pregunta actual.
         */
        if (
            questions.value.length > 0
        ) {

            current.value =
                Math.min(
                    Math.max(
                        data.current_question ?? 0,
                        0
                    ),
                    questions.value.length - 1
                );
        }

        /*
         * Si el backend todavía no
         * tiene registrado el video,
         * lo marcamos.
         */
        if (!data.video_completed) {

            const videoResponse =
                await apiFetch(
                    `/api/evaluations/${evaluationId.value}/video-completed`,
                    {
                        method: 'POST',
                    }
                );

            if (!videoResponse.ok) {

                throw new Error(
                    'No se pudo registrar el video completado.'
                );
            }
        }

        videoDone.value = true;

        stage.value = 'exam';

    } catch (error) {

        console.error(
            'Error iniciando evaluación:',
            error
        );

    } finally {

        loading.value = false;
    }
}


/* =========================================================
   SAVE ANSWER
========================================================= */

async function selectOption(
    optionId: number
) {

    if (
        !q.value ||
        !evaluationId.value ||
        savingAnswer.value
    ) {
        return;
    }

    const questionId =
        q.value.id;

    /*
     * UI inmediata.
     */
    answers.value[
        questionId
    ] = optionId;

    savingAnswer.value = true;

    try {

        const response =
            await apiFetch(
                `/api/evaluations/${evaluationId.value}/answers`,
                {
                    method: 'PUT',

                    headers: {
                        'Content-Type':
                            'application/json',
                    },

                    body: JSON.stringify({
                        question_id:
                            questionId,

                        option_id:
                            optionId,
                    }),
                }
            );

        if (!response.ok) {

            const errorData =
                await response.json()
                    .catch(() => null);

            throw new Error(
                errorData?.detail ||
                'No se pudo guardar la respuesta.'
            );
        }

    } catch (error) {

        console.error(
            'Error guardando respuesta:',
            error
        );

        /*
         * Si el servidor rechazó
         * la respuesta, quitarla
         * del estado local.
         */
        delete answers.value[
            questionId
        ];

    } finally {

        savingAnswer.value = false;
    }
}


/* =========================================================
   SAVE CURRENT QUESTION
========================================================= */

async function saveCurrentProgress(
    position = current.value
) {

    if (!evaluationId.value) {
        return;
    }

    try {

        const response =
            await apiFetch(
                `/api/evaluations/${evaluationId.value}/progress`,
                {
                    method: 'PUT',

                    headers: {
                        'Content-Type':
                            'application/json',
                    },

                    body: JSON.stringify({
                        current_question:
                            position,
                    }),
                }
            );

        if (!response.ok) {

            console.error(
                'No se pudo guardar la posición.'
            );
        }

    } catch (error) {

        console.error(
            'Error guardando posición:',
            error
        );
    }
}


/* =========================================================
   PREVIOUS
========================================================= */

async function previous() {

    if (current.value <= 0) {
        return;
    }

    current.value--;

    await saveCurrentProgress();
}


/* =========================================================
   NEXT
========================================================= */

async function next() {

    if (
        current.value >=
        questions.value.length - 1
    ) {
        return;
    }

    if (!canNext.value) {
        return;
    }

    current.value++;

    await saveCurrentProgress();
}


/* =========================================================
   DIRECT QUESTION NAVIGATION
========================================================= */

async function goToQuestion(
    index: number
) {

    if (
        index < 0 ||
        index >= questions.value.length
    ) {
        return;
    }

    current.value = index;

    await saveCurrentProgress();
}


/* =========================================================
   FINISH
========================================================= */

async function finish() {

    if (
        !evaluationId.value ||
        !allAnswered.value ||
        loading.value ||
        savingAnswer.value
    ) {
        return;
    }

    loading.value = true;

    try {

        const response =
            await apiFetch(
                `/api/evaluations/${evaluationId.value}/finish`,
                {
                    method: 'POST',

                    headers: {
                        'Content-Type':
                            'application/json',
                    },

                    /*
                     * El backend calcula el resultado
                     * desde las respuestas almacenadas.
                     */
                    body: JSON.stringify({
                        answers: [],
                    }),
                }
            );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail ||
                'No se pudo finalizar la evaluación.'
            );
        }

        result.value = {
            score:
                data.score,

            correct:
                data.correct,

            total:
                data.total,
        };

        stage.value = 'result';

    } catch (error) {

        console.error(
            'Error finalizando evaluación:',
            error
        );

    } finally {

        loading.value = false;
    }
}


/* =========================================================
   RESTART
========================================================= */

function restart() {

    window.location.reload();
}


/* =========================================================
   INITIALIZATION
========================================================= */

onMounted(
    async () => {

        document.addEventListener(
            'click',
            handleClickOutside
        );

        document.addEventListener(
            'keydown',
            handleEscape
        );

        generateAllThumbnails();

        loading.value = true;

        try {

            /*
             * Primero cargar preguntas.
             */
            await loadQuestions();

            /*
             * Después recuperar evaluación.
             */
            await restoreEvaluation();

        } catch (error) {

            console.error(
                'Error inicializando examen:',
                error
            );

        } finally {

            loading.value = false;
        }
    }
);


onUnmounted(() => {

    document.removeEventListener(
        'click',
        handleClickOutside
    );

    document.removeEventListener(
        'keydown',
        handleEscape
    );
});
</script>


<template>

    <div class="min-h-screen bg-[#f4f4f3] text-[#575756]">

        <!-- =====================================================
         HEADER
    ====================================================== -->

        <header class="sticky top-0 z-20 border-b border-[#dadada] bg-white/95 backdrop-blur">

            <div class="mx-auto flex max-w-6xl items-center gap-4 px-5 py-4">

                <div class="flex items-center gap-4">

                    <img src="/logo_fgjtam.png" alt="Logo FGJ Tamaulipas"
                        class="h-14 w-auto object-contain opacity-95" />

                </div>

                <div class="ml-auto flex items-center gap-4">

                    <div class="hidden text-right sm:block">

                        <p class="text-sm font-bold leading-tight">
                            {{ fullName }}
                        </p>

                        <p class="text-xs leading-tight text-[#878787]">
                            {{ user?.sector?.name }}
                        </p>

                    </div>

                    <img src="/logo_fede.png" alt="Logo FEDE" class="h-15 w-auto object-contain opacity-95" />

                    <button @click="logout()" title="Cerrar sesión"
                        class="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-[#dadada] text-[#878787] transition hover:border-[#575756] hover:text-[#575756]">

                        <LogOut :size="16" />

                    </button>

                </div>

            </div>

        </header>


        <!-- =====================================================
         MAIN
    ====================================================== -->

        <main class="mx-auto max-w-6xl px-5 py-8 md:py-6">

            <!-- ===================================================
           INTRO
      ==================================================== -->

            <section v-if="stage === 'intro'" class="flex flex-col items-center">

                <div class="mx-auto max-w-4xl text-center">

                    <span
                        class="inline-flex items-center gap-2 rounded-full bg-[#dadada]/60 px-3 py-1 text-xs font-semibold uppercase tracking-wider">

                        <PlayCircle :size="14" />

                        Material introductorio

                    </span>


                    <h2 class="mt-5 text-4xl font-black tracking-tight md:text-5xl lg:text-4xl">

                        Delitos Electorales y su investigación
                        en el contexto de los Procesos Electorales
                        Locales.

                    </h2>


                    <p class="mx-auto mt-5 max-w-3xl text-base leading-7 text-[#878787] md:text-lg">

                        Visualiza el material completo antes de
                        acceder a la evaluación del

                        <br />

                        <b>
                            Módulo 1: Nociones básicas de derecho
                            electoral.
                        </b>

                    </p>


                    <div class="mt-7 flex items-center justify-center gap-3 text-sm text-[#878787]">

                        <LockKeyhole :size="17" />

                        <span v-if="!videoDone">

                            La evaluación se habilita al concluir
                            el video.

                        </span>

                        <span v-else class="font-bold text-[#575756]">

                            Video completado. Ya puedes continuar
                            con la evaluación.

                        </span>

                    </div>

                </div>


                <!-- VIDEO -->

                <div class="mt-8 w-full max-w-6xl">

                    <div
                        class="mx-auto max-w-5xl rounded-[32px] border border-[#dadada] bg-white p-3 shadow-xl shadow-black/5 md:p-4">

                        <div class="overflow-hidden rounded-[26px] bg-[#575756]">

                            <video class="block aspect-video w-full object-cover" controls playsinline
                                preload="metadata" @ended="videoEnded">

                                <source src="/curso-modulo1.mp4" type="video/mp4" />

                                Tu navegador no soporta video HTML5.

                            </video>

                        </div>


                        <div
                            class="flex flex-col items-center justify-between gap-4 px-2 py-4 text-center sm:flex-row sm:text-left">

                            <div>

                                <p class="text-sm font-bold">
                                    Material de capacitación
                                </p>

                                <p class="text-xs text-[#878787]">
                                    Reproducción completa requerida
                                </p>

                            </div>


                            <button @click="startExam" :disabled="!videoDone ||
                                loading
                                "
                                class="rounded-xl bg-[#575756] px-5 py-3 text-sm font-bold text-white transition hover:bg-[#454544] disabled:cursor-not-allowed disabled:opacity-40">

                                {{
                                    loading
                                        ? 'Preparando evaluación…'
                                        : 'Contestar evaluación'
                                }}

                            </button>

                        </div>

                    </div>


                    <!-- =============================================
               SUPPORT DOCUMENTS DROPDOWN
          ============================================== -->

                    <div v-if="supportDocuments.length" ref="docsMenuRef" class="relative mx-auto mt-4 max-w-5xl">

                        <button @click.stop="toggleDocsMenu"
                            class="flex w-full items-center justify-between gap-4 rounded-2xl border border-[#dadada] bg-white px-5 py-4 text-left shadow-sm transition hover:border-[#878787]">

                            <span class="flex items-center gap-3">

                                <span
                                    class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#f0f0ef] text-[#575756]">

                                    <FileText :size="18" />

                                </span>

                                <span>

                                    <span class="block text-sm font-bold">
                                        Documentos de apoyo
                                    </span>

                                    <span class="block text-xs text-[#878787]">
                                        {{ supportDocuments.length }}
                                        materiales complementarios del módulo
                                    </span>

                                </span>

                            </span>

                            <ChevronDown :size="18" class="shrink-0 text-[#878787] transition-transform duration-200"
                                :class="docsMenuOpen
                                    ? 'rotate-180'
                                    : ''
                                    " />

                        </button>


                        <Transition name="fade">

                            <div v-if="docsMenuOpen"
                                class="absolute left-0 right-0 z-30 mt-2 max-h-96 overflow-y-auto rounded-2xl border border-[#dadada] bg-white p-2 shadow-2xl shadow-black/10">

                                <button v-for="doc in supportDocuments" :key="doc.id" @click="openDocument(doc)"
                                    class="flex w-full items-center gap-4 rounded-xl p-2 text-left transition hover:bg-[#f4f4f3]">

                                    <span
                                        class="flex h-16 w-12 shrink-0 items-center justify-center overflow-hidden rounded-lg border border-[#dadada] bg-[#f4f4f3]">

                                        <img v-if="thumbnails[doc.id]" :src="thumbnails[doc.id]"
                                            :alt="`Portada de ${doc.title}`" class="h-full w-full object-cover" />

                                        <FileText v-else :size="18" class="text-[#878787]" />

                                    </span>


                                    <span class="min-w-0 flex-1">

                                        <span class="block truncate text-sm font-bold">
                                            {{ doc.title }}
                                        </span>
                                    </span>


                                    <ChevronRight :size="16" class="shrink-0 text-[#878787]" />

                                </button>

                            </div>

                        </Transition>

                    </div>

                </div>

            </section>


            <!-- ===================================================
           EXAM
      ==================================================== -->

            <section v-else-if="stage === 'exam'" class="mx-auto max-w-4xl">

                <!-- HEADER -->

                <div class="mb-5 flex items-center justify-between">

                    <div>

                        <p class="text-xs font-bold uppercase tracking-widest text-[#878787]">
                            Módulo 1
                        </p>

                        <h2 class="text-xl font-black">
                            Nociones básicas de derecho electoral
                        </h2>

                    </div>


                    <div class="text-right">

                        <p class="text-sm font-bold">
                            {{ current + 1 }}
                            /
                            {{ questions.length }}
                        </p>

                        <p class="text-xs text-[#878787]">
                            {{ answeredCount }}
                            contestadas
                        </p>

                    </div>

                </div>


                <!-- PROGRESS -->

                <div class="h-2 overflow-hidden rounded-full bg-[#dadada]">

                    <div class="h-full rounded-full bg-[#575756] transition-all duration-500" :style="{
                        width: progress + '%'
                    }" />

                </div>


                <!-- QUESTION CARD -->

                <div v-if="q"
                    class="mt-8 rounded-3xl border border-[#dadada] bg-white p-6 shadow-xl shadow-black/5 md:p-10">

                    <Transition name="fade" mode="out-in">

                        <div :key="q.id">

                            <!-- QUESTION -->

                            <div class="flex items-start gap-4">

                                <span
                                    class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#575756] text-sm font-black text-white">

                                    {{ q.number }}

                                </span>


                                <h3 class="text-xl font-bold leading-8 md:text-2xl">

                                    {{ q.text }}

                                </h3>

                            </div>


                            <!-- OPTIONS -->

                            <div class="mt-8 space-y-3">

                                <button v-for="o in q.options" :key="o.id" @click="selectOption(o.id)"
                                    class="group flex w-full items-start gap-4 rounded-2xl border p-4 text-left transition"
                                    :class="answers[q.id] === o.id
                                        ? 'border-[#575756] bg-[#f0f0ef] shadow-sm'
                                        : 'border-[#dadada] hover:border-[#878787] hover:bg-[#fafafa]'
                                        ">

                                    <span
                                        class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border text-sm font-bold"
                                        :class="answers[q.id] === o.id
                                            ? 'border-[#575756] bg-[#575756] text-white'
                                            : 'border-[#dadada] text-[#878787]'
                                            ">

                                        {{ o.letter.toUpperCase() }}

                                    </span>


                                    <span class="pt-1 text-sm leading-6 md:text-base">

                                        {{ o.text }}

                                    </span>


                                    <CheckCircle2 v-if="
                                        answers[q.id] === o.id
                                    " class="ml-auto mt-1 shrink-0" :size="20" />

                                </button>

                            </div>


                            <!-- SAVE STATUS -->

                            <div class="mt-4 text-right text-xs text-[#878787]">

                                <span v-if="savingAnswer">
                                    Guardando respuesta…
                                </span>

                                <span v-else-if="answers[q.id]" class="font-semibold">
                                    Respuesta guardada
                                </span>

                            </div>

                        </div>

                    </Transition>


                    <!-- NAVIGATION -->

                    <div class="mt-9 flex items-center justify-between border-t border-[#dadada] pt-5">

                        <button @click="previous" :disabled="current === 0 ||
                            savingAnswer
                            "
                            class="inline-flex items-center gap-2 rounded-xl px-4 py-3 text-sm font-bold disabled:opacity-30">

                            <ChevronLeft :size="18" />

                            Anterior

                        </button>


                        <!-- NEXT -->

                        <button v-if="!isLastQuestion" @click="next" :disabled="!canNext ||
                            savingAnswer
                            "
                            class="inline-flex items-center gap-2 rounded-xl bg-[#575756] px-5 py-3 text-sm font-bold text-white disabled:opacity-30">

                            Siguiente

                            <ChevronRight :size="18" />

                        </button>


                        <!-- FINISH -->

                        <button v-else @click="finish" :disabled="!allAnswered ||
                            loading ||
                            savingAnswer
                            "
                            class="inline-flex items-center gap-2 rounded-xl bg-[#575756] px-5 py-3 text-sm font-bold text-white disabled:opacity-30">

                            {{
                                loading
                                    ? 'Guardando…'
                                    : 'Finalizar evaluación'
                            }}

                            <CheckCircle2 :size="18" />

                        </button>

                    </div>

                </div>


                <!-- QUESTION NAVIGATION -->

                <div v-if="questions.length" class="mt-5 flex flex-wrap gap-2">

                    <button v-for="(item, i) in questions" :key="item.id" @click="goToQuestion(i)"
                        class="h-8 w-8 rounded-lg text-xs font-bold" :class="i === current
                            ? 'bg-[#575756] text-white'
                            : answers[item.id]
                                ? 'bg-[#dadada] text-[#575756]'
                                : 'border border-[#dadada] bg-white text-[#878787]'
                            ">

                        {{ i + 1 }}

                    </button>

                </div>

            </section>


            <!-- ===================================================
           RESULT
      ==================================================== -->

            <section v-else class="mx-auto max-w-3xl">

                <div
                    class="overflow-hidden rounded-[32px] border border-[#dadada] bg-white text-center shadow-xl shadow-black/5">

                    <div class="bg-[#575756] px-6 py-14 text-white">

                        <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-white/10">

                            <ClipboardCheck :size="34" />

                        </div>


                        <p class="mt-5 text-xs font-bold uppercase tracking-[.25em] text-white/70">
                            Finalización
                        </p>


                        <h2 class="mt-2 text-3xl font-black md:text-4xl">
                            ¡Evaluación finalizada!
                        </h2>

                    </div>


                    <div class="p-8 md:p-10">

                        <p class="text-lg font-bold text-[#575756]">
                            {{
                                fullName ||
                                'Participante registrado'
                            }}
                        </p>


                        <!-- RESULT -->

                        <div class="mx-auto mt-6 grid max-w-md grid-cols-3 gap-3">

                            <div class="rounded-2xl border border-[#dadada] p-4">

                                <p class="text-2xl font-black text-[#575756]">
                                    {{ result.score }}%
                                </p>

                                <p class="mt-1 text-xs text-[#878787]">
                                    Calificación
                                </p>

                            </div>


                            <div class="rounded-2xl border border-[#dadada] p-4">

                                <p class="text-2xl font-black text-[#575756]">
                                    {{ result.correct }}
                                </p>

                                <p class="mt-1 text-xs text-[#878787]">
                                    Correctas
                                </p>

                            </div>


                            <div class="rounded-2xl border border-[#dadada] p-4">

                                <p class="text-2xl font-black text-[#575756]">
                                    {{ result.total }}
                                </p>

                                <p class="mt-1 text-xs text-[#878787]">
                                    Preguntas
                                </p>

                            </div>

                        </div>


                        <p class="mt-6 text-base leading-7 text-[#878787]">

                            Gracias por completar el módulo de
                            capacitación. Tu participación ha sido
                            registrada de forma exitosa en la
                            plataforma institucional.

                        </p>


                        <button @click="restart"
                            class="mt-8 inline-flex items-center gap-2 rounded-xl bg-[#575756] px-5 py-3 text-sm font-bold text-white hover:bg-[#454544]">

                            <RotateCcw :size="17" />

                            Nueva evaluación

                        </button>

                    </div>

                </div>

            </section>

        </main>


        <!-- =====================================================
         FOOTER
    ====================================================== -->

        <footer class="mx-auto max-w-6xl px-5 pb-8 text-center text-xs text-[#878787]">

            Fiscalía General de Justicia del Estado de Tamaulipas
            · Fiscalía Especializada en Delitos Electorales

        </footer>


        <!-- =====================================================
         PDF VIEWER MODAL
    ====================================================== -->

        <Transition name="fade">

            <div v-if="viewingDoc" @click.self="closeViewer"
                class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm md:p-8">

                <div class="flex h-full w-full max-w-5xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl">

                    <div class="flex items-center justify-between border-b border-[#dadada] px-5 py-3">

                        <div class="flex items-center gap-3 truncate">

                            <span
                                class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#f0f0ef] text-[#575756]">
                                <FileText :size="16" />
                            </span>

                            <p class="truncate text-sm font-bold">
                                {{ viewingDoc.title }}
                            </p>

                        </div>

                        <button @click="closeViewer" title="Cerrar"
                            class="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[#878787] transition hover:bg-[#f4f4f3] hover:text-[#575756]">

                            <X :size="18" />

                        </button>

                    </div>


                    <iframe :src="viewingDoc.url" :title="viewingDoc.title" class="h-full w-full flex-1 bg-[#f4f4f3]" />

                </div>

            </div>

        </Transition>

    </div>

</template>


<style scoped>
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}
</style>