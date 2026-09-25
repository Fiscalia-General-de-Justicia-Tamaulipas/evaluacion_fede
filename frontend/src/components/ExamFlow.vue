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
    CheckCircle2,
    PlayCircle,
    ClipboardCheck,
    LockKeyhole,
    RotateCcw,
    LogOut,
    FileText,
    X,
} from 'lucide-vue-next';

import { useAuth } from '../lib/auth';


/* =========================================================
   PDF.JS
   ========================================================= */

const PDFJS_VERSION = '4.7.76';

const PDFJS_SCRIPT_URL =
    `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${PDFJS_VERSION}/pdf.min.js`;

const PDFJS_WORKER_URL =
    `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${PDFJS_VERSION}/pdf.worker.min.js`;

let pdfjsLoadPromise: Promise<any> | null = null;

function loadPdfJs(): Promise<any> {

    const existing = (window as any).pdfjsLib;

    if (existing) {
        return Promise.resolve(existing);
    }

    if (pdfjsLoadPromise) {
        return pdfjsLoadPromise;
    }

    pdfjsLoadPromise = new Promise((resolve, reject) => {

        const script = document.createElement('script');

        script.src = PDFJS_SCRIPT_URL;

        script.onload = () => {

            const lib = (window as any).pdfjsLib;

            if (!lib) {
                reject(
                    new Error(
                        'pdf.js no se expuso correctamente en window.'
                    )
                );

                return;
            }

            lib.GlobalWorkerOptions.workerSrc =
                PDFJS_WORKER_URL;

            resolve(lib);
        };

        script.onerror = () => {

            reject(
                new Error(
                    'No se pudo cargar pdf.js desde el CDN.'
                )
            );

        };

        document.head.appendChild(script);
    });

    return pdfjsLoadPromise;
}


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
    question_order: number[];
    answers: SavedAnswer[];
};

type CurrentEvaluationResponse = {
    has_evaluation: boolean;

    evaluation: {
        id: number;
        video_completed: boolean;
        started_at: string;
        current_question: number;
        question_order: number[];
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

const videoModalOpen = ref(false);

const modalVideoRef = ref<HTMLVideoElement | null>(null);

const evaluationId = ref<number | null>(null);

const questions = ref<Question[]>([]);

const current = ref(0);

const answers = ref<Record<number, number>>({});

const loading = ref(false);

const savingAnswer = ref(false);

const result = ref<Result>({
    score: 0,
    correct: 0,
    total: 0,
});


/* =========================================================
   SUPPORT DOCUMENTS
   ========================================================= */

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


/* =========================================================
   PDF SIDEBAR STATE
   ========================================================= */

const docsMenuOpen = ref(false);

const docsMenuRef = ref<HTMLElement | null>(null);

const viewingDoc = ref<SupportDocument | null>(null);

const thumbnails = ref<Record<number, string>>({});

let hoverCloseTimer: ReturnType<typeof setTimeout> | null = null;

const showDocsMenu = computed(() => {

    return (
        stage.value !== 'exam' &&
        supportDocuments.value.length > 0
    );

});


/* =========================================================
   COMPUTED
   ========================================================= */

const q = computed(() => {

    return questions.value[current.value];

});


const answeredCount = computed(() => {

    return Object.keys(answers.value).length;

});


const progress = computed(() => {

    if (!questions.value.length) {
        return 0;
    }

    return (
        (answeredCount.value /
            questions.value.length) *
        100
    );

});


const maxReachableIndex = computed(() => {

    const nextUnanswered = questions.value.findIndex(
        (question) => answers.value[question.id] == null
    );

    return nextUnanswered === -1
        ? Math.max(questions.value.length - 1, 0)
        : nextUnanswered;

});


const canNext = computed(() => {

    if (!q.value) {
        return false;
    }

    return (
        answers.value[q.value.id] != null &&
        current.value < maxReachableIndex.value
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

        const response =
            await apiFetch('/api/questions');

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


function applyQuestionOrder(questionOrder: number[]) {

    const questionsById = new Map(
        questions.value.map((question) => [
            question.id,
            question,
        ])
    );

    const orderedQuestions = questionOrder
        .map((questionId) => questionsById.get(questionId))
        .filter((question): question is Question => Boolean(question));

    questions.value = [
        ...orderedQuestions,
        ...questions.value.filter(
            (question) => !questionOrder.includes(question.id)
        ),
    ];
}


/* =========================================================
   PDF THUMBNAILS
   ========================================================= */

async function generateThumbnail(
    doc: SupportDocument
) {

    try {

        const pdfjsLib =
            await loadPdfJs();

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
            document.createElement('canvas');

        canvas.width =
            viewport.width;

        canvas.height =
            viewport.height;

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
   PDF SIDEBAR
   ========================================================= */

function openDocsMenu() {

    if (hoverCloseTimer) {

        clearTimeout(hoverCloseTimer);

        hoverCloseTimer = null;

    }

    docsMenuOpen.value = true;

}


function closeDocsMenu() {

    if (hoverCloseTimer) {

        clearTimeout(hoverCloseTimer);

    }

    hoverCloseTimer = setTimeout(() => {

        docsMenuOpen.value = false;

        hoverCloseTimer = null;

    }, 150);

}


function toggleDocsMenu() {

    if (hoverCloseTimer) {

        clearTimeout(hoverCloseTimer);

        hoverCloseTimer = null;

    }

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

        closeVideoModal();

    }

}


/* =========================================================
   RESTORE ANSWERS
   ========================================================= */

function restoreAnswers(
    savedAnswers: SavedAnswer[]
) {

    const restored: Record<
        number,
        number
    > = {};

    for (const answer of savedAnswers) {

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

        const response =
            await apiFetch(
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

        applyQuestionOrder(
            evaluation.question_order ?? []
        );

        if (
            evaluation.video_completed
        ) {

            stage.value = 'exam';

            if (questions.value.length > 0) {

                current.value =
                    Math.min(
                        Math.max(
                            evaluation.current_question ??
                            0,
                            0
                        ),
                        questions.value.length -
                        1
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


function openVideoModal() {

    videoModalOpen.value = true;

    document.body.style.overflow = 'hidden';

}


function closeVideoModal() {

    videoModalOpen.value = false;

    modalVideoRef.value?.pause();

    document.body.style.overflow = '';

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

    closeVideoModal();

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
                await response
                    .json()
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

        restoreAnswers(
            data.answers ?? []
        );

        applyQuestionOrder(
            data.question_order ?? []
        );

        if (
            questions.value.length > 0
        ) {

            current.value =
                Math.min(
                    Math.max(
                        data.current_question ??
                        0,
                        0
                    ),
                    questions.value.length -
                    1
                );

        }

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

    const previousOptionId =
        answers.value[questionId];

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
                await response
                    .json()
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

        if (previousOptionId == null) {
            delete answers.value[questionId];
        } else {
            answers.value[questionId] = previousOptionId;
        }

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
   QUESTION PAGINATION
   ========================================================= */

async function previous() {

    if (current.value <= 0) {
        return;
    }

    current.value--;
    await saveCurrentProgress();

}

async function next() {

    if (!canNext.value) {
        return;
    }

    current.value++;
    await saveCurrentProgress();

}

async function goToQuestion(index: number) {

    if (
        index < 0 ||
        index > maxReachableIndex.value ||
        index >= questions.value.length ||
        index === current.value
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
            score: data.score,
            correct: data.correct,
            total: data.total,
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

onMounted(async () => {

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

        await loadQuestions();

        await restoreEvaluation();

    } catch (error) {

        console.error(
            'Error inicializando examen:',
            error
        );

    } finally {

        loading.value = false;

    }

});


onUnmounted(() => {

    document.removeEventListener(
        'click',
        handleClickOutside
    );

    document.removeEventListener(
        'keydown',
        handleEscape
    );

    document.body.style.overflow = '';

    if (hoverCloseTimer) {

        clearTimeout(hoverCloseTimer);

    }

});

</script>


<template>

    <div class="min-h-screen bg-[#f4f4f3] text-[#575756]">

        <!-- =====================================================
             HEADER
        ====================================================== -->

        <header class="sticky top-0 z-20 border-b border-[#dadada]
                   bg-white/95 backdrop-blur">

            <div class="mx-auto flex max-w-6xl items-center
                       gap-4 px-5 py-4">

                <div class="flex items-center gap-4">

                    <img src="/logo_fgjtam.png" alt="Logo FGJ Tamaulipas"
                        class="h-14 w-auto object-contain opacity-95" />
                    <div class="h-7 w-px bg-gray-300" />

                    <img src="/logo_fede.png" alt="Logo FEDE" class="h-15 w-auto object-contain opacity-95" />

                </div>


                <div class="ml-auto flex items-center gap-4">

                    <div class="hidden text-right sm:block">

                        <p class="text-sm font-bold leading-tight">
                            {{ fullName }}
                        </p>

                        <p class="text-xs leading-tight
                                   text-[#878787]">
                            {{ user?.sector?.name }}
                        </p>

                    </div>



                    <button @click="logout()" title="Cerrar sesión" class="inline-flex h-9 w-9
                               items-center justify-center
                               rounded-lg border border-[#dadada]
                               text-[#878787]
                               transition
                               hover:border-[#575756]
                               hover:text-[#575756]">

                        <LogOut :size="16" />

                    </button>

                </div>

            </div>

        </header>


        <!-- =====================================================
             PDF SIDEBAR DERECHO
        ====================================================== -->

        <Transition name="docs-fab">

            <div v-if="showDocsMenu" ref="docsMenuRef" class="fixed right-0 top-1/2 z-40
                       -translate-y-1/2">

                <div class="relative flex items-stretch" @mouseenter="openDocsMenu" @mouseleave="closeDocsMenu">

                    <!-- =================================================
                         PESTAÑA
                    ================================================== -->

                    <button type="button" @click.stop="toggleDocsMenu" title="Documentos de apoyo" class="relative z-20 flex h-80 w-11
                               cursor-pointer items-center
                               justify-center
                               rounded-l-2xl
                               border border-r-0
                               border-[#dadada]
                               bg-white
                               text-[#575756]
                               shadow-[0_8px_30px_rgba(0,0,0,0.08)]
                               transition-all duration-300
                               hover:bg-[#575756]
                               hover:text-white
                               hover:shadow-[0_8px_30px_rgba(0,0,0,0.18)]
                               focus:outline-none
                               focus:ring-2
                               focus:ring-[#878787]/40">

                        <div class="flex flex-col
                                   items-center gap-1.5">

                            <FileText :size="18" />

                            <span class="text-[14px]
                                       font-bold
                                       uppercase
                                       tracking-[0.15em]" style="
                                    writing-mode: vertical-rl;
                                ">
                                DOCUMENTOS DE APOYO
                            </span>

                        </div>

                    </button>


                    <!-- =================================================
                         PANEL
                    ================================================== -->

                    <Transition name="docs-panel">

                        <div v-if="docsMenuOpen" class="absolute right-11 top-1/2
                                   -translate-y-1/2">

                            <aside class="w-[360px]
                                       overflow-hidden
                                       rounded-l-2xl
                                       border border-r-0
                                       border-[#dadada]
                                       bg-white
                                       shadow-[0_20px_60px_-15px_rgba(0,0,0,0.25)]">

                                <!-- HEADER -->

                                <div class="flex items-center
                                           justify-between
                                           border-b
                                           border-[#dadada]
                                           bg-gradient-to-br
                                           from-[#575756]
                                           to-[#3f3f3e]
                                           px-4 py-3.5
                                           text-white">

                                    <div class="flex items-center gap-2.5">

                                        <div class="flex h-9 w-9
                                                   items-center
                                                   justify-center
                                                   rounded-xl
                                                   bg-white/10
                                                   ring-1
                                                   ring-white/15">

                                            <FileText :size="17" />

                                        </div>


                                        <div>

                                            <p class="text-sm
                                                       font-black
                                                       leading-tight">
                                                Documentos de apoyo
                                            </p>

                                            <p class="text-[10px]
                                                       text-white/60
                                                       leading-tight
                                                       mt-0.5">
                                                Material de consulta
                                            </p>

                                        </div>

                                    </div>


                                    <span class="rounded-full
                                               bg-white/10
                                               px-2.5 py-1
                                               text-[10px]
                                               font-bold
                                               ring-1
                                               ring-white/15">
                                        {{ supportDocuments.length }}
                                    </span>

                                </div>


                                <!-- DOCUMENTOS -->

                                <div class="max-h-[70vh]
                                           space-y-1
                                           overflow-y-auto
                                           p-2
                                           [scrollbar-width:thin]
                                           [scrollbar-color:#dadada_transparent]">

                                    <button v-for="doc in supportDocuments" :key="doc.id" type="button"
                                        @click="openDocument(doc)" class="group/doc flex w-full
                                               items-center gap-3
                                               rounded-xl p-2
                                               text-left
                                               transition-all
                                               duration-200
                                               hover:bg-[#f4f4f3]
                                               hover:shadow-sm
                                               focus:outline-none
                                               focus:ring-2
                                               focus:ring-[#878787]/30">

                                        <!-- MINIATURA -->

                                        <span class="flex h-[68px]
                                                   w-12 shrink-0
                                                   items-center
                                                   justify-center
                                                   overflow-hidden
                                                   rounded-lg
                                                   border
                                                   border-[#dadada]
                                                   bg-[#f4f4f3]
                                                   shadow-sm
                                                   transition-all
                                                   duration-200
                                                   group-hover/doc:border-[#878787]
                                                   group-hover/doc:shadow-md">

                                            <img v-if="
                                                thumbnails[doc.id]
                                            " :src="thumbnails[doc.id]
                                                    " :alt="`Portada de ${doc.title}`
                                                    " class="h-full
                                                       w-full
                                                       object-cover" />

                                            <FileText v-else :size="18" class="text-[#878787]" />

                                        </span>


                                        <!-- INFORMACIÓN -->

                                        <span class="min-w-0 flex-1">

                                            <span class="block
                                                       text-xs
                                                       font-bold
                                                       leading-5
                                                       text-[#575756]
                                                       line-clamp-2">
                                                {{ doc.title }}
                                            </span>


                                            <span class="mt-1 flex
                                                       items-center
                                                       gap-1
                                                       text-[10px]
                                                       font-semibold
                                                       text-[#878787]">

                                                <FileText :size="11" />

                                                Consultar documento

                                            </span>

                                        </span>


                                        <!-- FLECHA -->

                                        <ChevronRight :size="15" class="shrink-0
                                                   text-[#b0b0b0]
                                                   transition-all
                                                   duration-200
                                                   group-hover/doc:translate-x-0.5
                                                   group-hover/doc:text-[#575756]" />

                                    </button>

                                </div>

                            </aside>

                        </div>

                    </Transition>

                </div>

            </div>

        </Transition>


        <!-- =====================================================
             MAIN
        ====================================================== -->

        <main class="mx-auto max-w-6xl
                   px-5 py-8 md:py-6">

            <!-- ===================================================
                 INTRO
            ==================================================== -->

            <section v-if="stage === 'intro'" class="flex flex-col items-center">

                <div class="mx-auto max-w-4xl text-center">

                    <span class="inline-flex items-center gap-2
                               rounded-full
                               bg-[#dadada]/60
                               px-3 py-1
                               text-xs
                               font-semibold
                               uppercase
                               tracking-wider">

                        <PlayCircle :size="14" />

                        Material introductorio

                    </span>


                    <h2 class="mt-5 text-4xl
                               font-black
                               tracking-tight
                               md:text-5xl
                               lg:text-4xl">

                        Delitos Electorales y su investigación
                        en el contexto de los Procesos Electorales
                        Locales.

                    </h2>


                    <p class="mx-auto mt-5 max-w-3xl
                               text-base
                               leading-7
                               text-[#878787]
                               md:text-lg">

                        Visualiza el material completo antes de
                        acceder a la evaluación del

                        <br />

                        <b>
                            Módulo 1: Nociones básicas de derecho electoral.
                        </b>

                    </p>


                    <div class="mt-7 flex items-center
                               justify-center gap-3
                               text-sm text-[#878787]">

                        <LockKeyhole :size="17" />

                        <span v-if="!videoDone">

                            La evaluación se habilita al
                            concluir el video.

                        </span>

                        <span v-else class="font-bold text-[#575756]">

                            Video completado.
                            Ya puedes continuar con la evaluación.

                        </span>

                    </div>

                </div>


                <!-- =================================================
                     VIDEO
                ================================================== -->

                <div class="mt-8 flex w-full justify-center">

                    <button
                        type="button"
                        class="inline-flex items-center gap-3 rounded-2xl bg-[#575756] px-8 py-4 text-base font-black text-white shadow-xl shadow-black/10 transition hover:-translate-y-0.5 hover:bg-[#454544] hover:shadow-2xl focus:outline-none focus:ring-2 focus:ring-[#575756] focus:ring-offset-4"
                        aria-label="Ver video de capacitación"
                        @click="openVideoModal"
                    >
                        <PlayCircle :size="23" />
                        Ver video
                    </button>

                </div>


            <Transition name="fade">

                <div
                    v-if="videoModalOpen"
                    class="fixed inset-0 z-[9999] flex min-h-screen flex-col overflow-y-auto bg-[#20201f] text-white"
                    role="dialog"
                    aria-modal="true"
                    aria-labelledby="video-modal-title"
                    @click.self="closeVideoModal"
                >
                    <div class="flex min-h-screen w-full flex-col">
                        <header class="border-b border-white/10 bg-[#292928] px-5 py-4 md:px-10">
                            <div class="mx-auto flex max-w-7xl items-center gap-4">
                                <img
                                    src="/logo_fgjtam.png"
                                    alt="Logo Fiscalía General de Justicia de Tamaulipas"
                                    class="h-12 w-auto object-contain md:h-16"
                                />

                                <div class="h-10 w-px bg-white/20 md:h-12" />

                                <img
                                    src="/logo_fede.png"
                                    alt="Logo Fiscalía Especializada en Delitos Electorales"
                                    class="h-12 w-auto object-contain md:h-16"
                                />

                                <div class="ml-auto min-w-0 pr-10">
                                    <p class="truncate text-xs font-bold uppercase tracking-[0.18em] text-white/55">
                                        Material introductorio
                                    </p>
                                    <h2 id="video-modal-title" class="mt-1 text-sm font-black text-white md:text-lg">
                                        Delitos Electorales y su investigación
                                    </h2>
                                </div>

                            <button
                                type="button"
                                title="Cerrar video"
                                aria-label="Cerrar video"
                                class="absolute right-5 top-5 inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-white/65 transition hover:bg-white/10 hover:text-white md:right-10"
                                @click="closeVideoModal"
                            >
                                <X :size="20" />
                            </button>
                            </div>
                        </header>

                        <main class="flex flex-1 flex-col items-center justify-center px-4 py-8 md:px-10 md:py-12">
                            <div class="mb-6 text-center md:mb-8">
                                <p class="text-2xl font-black md:text-4xl">
                                    Módulo 1: Nociones básicas de derecho electoral
                                </p>
                                <p class="mt-2 text-sm text-white/60 md:text-base">
                                    Reproduce el video completo antes de contestar la evaluación.
                                </p>
                            </div>

                            <div class="w-full max-w-6xl overflow-hidden rounded-2xl border border-white/10 bg-black shadow-2xl md:rounded-3xl">
                            <video
                                ref="modalVideoRef"
                                class="mx-auto block max-h-[68vh] w-full object-contain"
                                controls
                                autoplay
                                playsinline
                                preload="metadata"
                                @ended="videoEnded"
                            >
                                <source src="/curso-modulo1.mp4" type="video/mp4" />
                                Tu navegador no soporta video HTML5.
                            </video>
                            </div>

                            <div class="mt-6 flex w-full max-w-6xl flex-col items-center justify-between gap-4 border-t border-white/10 pt-6 sm:flex-row">
                                <p class="text-sm text-white/60">
                                    <span v-if="!videoDone">La evaluación se habilita al terminar el video.</span>
                                    <span v-else class="font-bold text-emerald-300">Video completado. Ya puedes continuar.</span>
                                </p>

                                <button
                                    type="button"
                                    :disabled="!videoDone || loading"
                                    class="rounded-xl bg-white px-6 py-3 text-sm font-black text-[#292928] transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-40"
                                    @click="startExam"
                                >
                                    {{ loading ? 'Preparando evaluación…' : 'Contestar evaluación' }}
                                </button>
                            </div>
                        </main>
                    </div>
                </div>

            </Transition>

            </section>


            <!-- ===================================================
                 EXAM
            ==================================================== -->

            <section v-else-if="stage === 'exam'" class="mx-auto max-w-4xl">

                <!-- HEADER -->

                <div class="mb-5 flex items-center
                           justify-between">

                    <div>

                        <p class="text-xs
                                   font-bold
                                   uppercase
                                   tracking-widest
                                   text-[#878787]">
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
                            {{ answeredCount }} contestadas
                        </p>

                    </div>

                </div>


                <!-- PROGRESS -->

                <div class="h-2 overflow-hidden
                           rounded-full
                           bg-[#dadada]">

                    <div class="h-full
                               rounded-full
                               bg-[#575756]
                               transition-all
                               duration-500" :style="{
                                width: progress + '%'
                            }" />

                </div>


                <!-- QUESTION CARD -->

                <div v-if="q" class="mt-8 rounded-3xl
                           border border-[#dadada]
                           bg-white p-6
                           shadow-xl
                           shadow-black/5
                           md:p-10">

                    <Transition name="fade" mode="out-in">

                        <div :key="q.id">

                            <!-- QUESTION -->

                            <div class="flex items-start
                                       gap-4">

                                <span class="flex h-10 w-10
                                           shrink-0
                                           items-center
                                           justify-center
                                           rounded-xl
                                           bg-[#575756]
                                           text-sm
                                           font-black
                                           text-white">
                                    {{ current + 1 }}
                                </span>


                                <h3 class="text-xl
                                           font-bold
                                           leading-8
                                           md:text-2xl">
                                    {{ q.text }}
                                </h3>

                            </div>


                            <!-- OPTIONS -->

                            <div class="mt-8 space-y-3">

                                <button v-for="o in q.options" :key="o.id" @click="
                                    selectOption(o.id)
                                    " class="group flex w-full
                                           items-start gap-4
                                           rounded-2xl
                                           border p-4
                                           text-left
                                           transition" :class="answers[q.id] === o.id
                                                ? 'border-[#575756] bg-[#f0f0ef] shadow-sm'
                                                : 'border-[#dadada] hover:border-[#878787] hover:bg-[#fafafa]'
                                            ">

                                    <span class="flex h-8 w-8
                                               shrink-0
                                               items-center
                                               justify-center
                                               rounded-lg
                                               border
                                               text-sm
                                               font-bold" :class="answers[q.id] === o.id
                                                    ? 'border-[#575756] bg-[#575756] text-white'
                                                    : 'border-[#dadada] text-[#878787]'
                                                ">
                                        {{ o.letter.toUpperCase() }}
                                    </span>


                                    <span class="pt-1
                                               text-sm
                                               leading-6
                                               md:text-base">
                                        {{ o.text }}
                                    </span>


                                    <CheckCircle2 v-if="
                                        answers[q.id] === o.id
                                    " class="ml-auto
                                               mt-1
                                               shrink-0" :size="20" />

                                </button>

                            </div>


                            <!-- SAVE STATUS -->

                            <div class="mt-4
                                       text-right
                                       text-xs
                                       text-[#878787]">

                                <span v-if="savingAnswer">
                                    Guardando respuesta…
                                </span>

                                <span v-else-if="
                                    answers[q.id]
                                " class="font-semibold">
                                    Respuesta guardada
                                </span>

                            </div>

                        </div>

                    </Transition>


                    <!-- NAVIGATION -->

                </div>

                <nav v-if="questions.length" aria-label="Paginación de preguntas" class="mt-5 flex flex-wrap items-center justify-between gap-3">

                    <button type="button" @click="previous" :disabled="current === 0 || savingAnswer" aria-label="Pregunta anterior" title="Pregunta anterior" class="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-[#dadada] bg-white text-[#575756] disabled:opacity-35">
                        <ChevronLeft :size="18" />
                    </button>

                    <div class="flex flex-1 flex-wrap items-center justify-center gap-2">

                        <button v-for="(item, index) in questions" :key="item.id" type="button" @click="goToQuestion(index)" :disabled="index > maxReachableIndex || savingAnswer" :aria-label="`Pregunta ${index + 1}${answers[item.id] ? ', respondida' : ', pendiente'}`" :aria-current="index === current ? 'page' : undefined" :title="`Pregunta ${index + 1}`" class="h-9 w-9 rounded-lg border text-sm font-bold transition disabled:cursor-not-allowed disabled:opacity-35" :class="index === current
                            ? 'border-[#575756] bg-[#575756] text-white'
                            : answers[item.id]
                                ? 'border-[#4f7b63] bg-[#e8f0eb] text-[#315a43] hover:bg-[#dce9e0]'
                                : 'border-[#dadada] bg-white text-[#878787] hover:border-[#878787]'">
                            {{ index + 1 }}
                        </button>

                    </div>

                    <button v-if="canNext" type="button" @click="next" :disabled="savingAnswer" aria-label="Pregunta siguiente" title="Pregunta siguiente" class="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-[#dadada] bg-white text-[#575756] disabled:opacity-35">
                        <ChevronRight :size="18" />
                    </button>

                    <button v-else-if="allAnswered && current === maxReachableIndex" type="button" @click="finish" :disabled="loading || savingAnswer" class="inline-flex items-center gap-2 rounded-lg bg-[#575756] px-4 py-2.5 text-sm font-bold text-white disabled:opacity-35">
                        {{ loading ? 'Guardando…' : 'Finalizar' }}
                        <CheckCircle2 :size="18" />
                    </button>

                    <span v-else class="h-10 w-10" aria-hidden="true" />

                </nav>

            </section>


            <!-- ===================================================
                 RESULT
            ==================================================== -->

            <section v-else class="mx-auto max-w-3xl">

                <div class="overflow-hidden
                           rounded-[32px]
                           border border-[#dadada]
                           bg-white
                           text-center
                           shadow-xl
                           shadow-black/5">

                    <div class="bg-[#575756]
                               px-6 py-14
                               text-white">

                        <div class="mx-auto flex
                                   h-16 w-16
                                   items-center
                                   justify-center
                                   rounded-2xl
                                   bg-white/10">

                            <ClipboardCheck :size="34" />

                        </div>


                        <p class="mt-5
                                   text-xs
                                   font-bold
                                   uppercase
                                   tracking-[.25em]
                                   text-white/70">
                            Finalización
                        </p>


                        <h2 class="mt-2
                                   text-3xl
                                   font-black
                                   md:text-4xl">
                            ¡Evaluación finalizada!
                        </h2>

                    </div>


                    <div class="p-8 md:p-10">

                        <p class="text-lg
                                   font-bold
                                   text-[#575756]">
                            {{
                                fullName ||
                                'Participante registrado'
                            }}
                        </p>


                        <div class="mx-auto mt-6
                                   grid max-w-md
                                   grid-cols-3 gap-3">

                            <div class="rounded-2xl
                                       border
                                       border-[#dadada]
                                       p-4">

                                <p class="text-2xl
                                           font-black
                                           text-[#575756]">
                                    {{ result.score }}%
                                </p>

                                <p class="mt-1
                                           text-xs
                                           text-[#878787]">
                                    Calificación
                                </p>

                            </div>


                            <div class="rounded-2xl
                                       border
                                       border-[#dadada]
                                       p-4">

                                <p class="text-2xl
                                           font-black
                                           text-[#575756]">
                                    {{ result.correct }}
                                </p>

                                <p class="mt-1
                                           text-xs
                                           text-[#878787]">
                                    Correctas
                                </p>

                            </div>


                            <div class="rounded-2xl
                                       border
                                       border-[#dadada]
                                       p-4">

                                <p class="text-2xl
                                           font-black
                                           text-[#575756]">
                                    {{ result.total }}
                                </p>

                                <p class="mt-1
                                           text-xs
                                           text-[#878787]">
                                    Preguntas
                                </p>

                            </div>

                        </div>


                        <p class="mt-6
                                   text-base
                                   leading-7
                                   text-[#878787]">

                            Gracias por completar el módulo de
                            capacitación. Tu participación ha sido
                            registrada de forma exitosa en la
                            plataforma institucional.

                        </p>


                        <button @click="restart" class="mt-8 inline-flex
                                   items-center
                                   gap-2
                                   rounded-xl
                                   bg-[#575756]
                                   px-5 py-3
                                   text-sm
                                   font-bold
                                   text-white
                                   hover:bg-[#454544]">

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

        <footer class="mx-auto max-w-6xl
                   px-5 pb-8
                   text-center
                   text-xs
                   text-[#878787]">

            Fiscalía General de Justicia
            del Estado de Tamaulipas

            ·

            Fiscalía Especializada
            en Delitos Electorales

        </footer>


        <!-- =====================================================
             PDF VIEWER MODAL
        ====================================================== -->

        <Transition name="fade">

            <div v-if="viewingDoc" @click.self="closeViewer" class="fixed inset-0 z-50
                       flex items-center
                       justify-center
                       bg-black/60
                       p-4
                       backdrop-blur-sm
                       md:p-8">

                <div class="flex h-full
                           w-full max-w-5xl
                           flex-col
                           overflow-hidden
                           rounded-2xl
                           bg-white
                           shadow-2xl">

                    <!-- HEADER PDF -->

                    <div class="flex items-center
                               justify-between
                               border-b
                               border-[#dadada]
                               px-5 py-3">

                        <div class="flex min-w-0
                                   items-center
                                   gap-3">

                            <span class="flex h-8 w-8
                                       shrink-0
                                       items-center
                                       justify-center
                                       rounded-lg
                                       bg-[#f0f0ef]
                                       text-[#575756]">

                                <FileText :size="16" />

                            </span>


                            <p class="truncate
                                       text-sm
                                       font-bold">
                                {{ viewingDoc.title }}
                            </p>

                        </div>


                        <button @click="closeViewer" title="Cerrar" class="inline-flex
                                   h-8 w-8
                                   shrink-0
                                   items-center
                                   justify-center
                                   rounded-lg
                                   text-[#878787]
                                   transition
                                   hover:bg-[#f4f4f3]
                                   hover:text-[#575756]">

                            <X :size="18" />

                        </button>

                    </div>


                    <!-- PDF -->

                    <iframe :src="viewingDoc.url" :title="viewingDoc.title" class="h-full
                               w-full
                               flex-1
                               bg-[#f4f4f3]" />

                </div>

            </div>

        </Transition>

    </div>

</template>


<style scoped>
/* =========================================================
   FADE GENERAL
   ========================================================= */

.fade-enter-active,
.fade-leave-active {

    transition:
        opacity 0.15s ease;

}

.fade-enter-from,
.fade-leave-to {

    opacity: 0;

}


/* =========================================================
   PDF SIDEBAR - PESTAÑA
   ========================================================= */

.docs-fab-enter-active,
.docs-fab-leave-active {

    transition:
        opacity 0.3s ease,
        transform 0.3s ease;

}

.docs-fab-enter-from,
.docs-fab-leave-to {

    opacity: 0;

    transform:
        translateX(40px) translateY(-50%);

}


/* =========================================================
   PDF SIDEBAR - PANEL
   ========================================================= */

.docs-panel-enter-active {

    transition:
        opacity 0.25s cubic-bezier(0.16, 1, 0.3, 1),
        transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);

}

.docs-panel-leave-active {

    transition:
        opacity 0.15s ease,
        transform 0.15s ease;

}

.docs-panel-enter-from,
.docs-panel-leave-to {

    opacity: 0;

    transform: translateX(20px);

}

.docs-panel-enter-to,
.docs-panel-leave-from {

    opacity: 1;

    transform: translateX(0);

}


/* =========================================================
   SCROLLBAR DEL SIDEBAR
   ========================================================= */

::-webkit-scrollbar {

    width: 6px;

}

::-webkit-scrollbar-track {

    background: transparent;

}

::-webkit-scrollbar-thumb {

    background: #dadada;

    border-radius: 999px;

}

::-webkit-scrollbar-thumb:hover {

    background: #878787;

}
</style>