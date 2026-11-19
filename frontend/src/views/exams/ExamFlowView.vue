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
    LockKeyhole,
    FileText,
    X,
    ArrowLeft,
} from 'lucide-vue-next';

import { useAuth } from '../../services/auth';
import EvaluationResult from '../../components/exam/EvaluationResult.vue';
import InstitutionalHeader from '../../components/layout/InstitutionalHeader.vue';
import BaseAlert from '../../components/ui/BaseAlert.vue';
import ConfirmDialog from '../../components/ui/ConfirmDialog.vue';

const emit = defineEmits<{
    (e: 'back'): void;
}>();


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
        completed?: boolean;
        completed_at?: string;
        score?: number | null;
        correct?: number | null;
        attempt_number?: number;
        attempts_remaining?: number;
        passed?: boolean;
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
    attempt: number;
    attemptsRemaining: number;
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

const message = ref('');
const showFinishConfirmation = ref(false);

const result = ref<Result>({
    score: 0,
    correct: 0,
    total: 0,
    attempt: 0,
    attemptsRemaining: 3,
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
        message.value = error instanceof Error
            ? error.message
            : 'No se pudieron cargar las preguntas. Intenta recargar el módulo.';
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

        if (evaluation.completed) {
            result.value = {
                score: evaluation.score ?? 0,
                correct: evaluation.correct ?? 0,
                total: evaluation.total_questions ?? 0,
                attempt: evaluation.attempt_number ?? 1,
                attemptsRemaining: evaluation.attempts_remaining ?? 0,
            };
            stage.value = 'result';
            return;
        }

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
        message.value = error instanceof Error
            ? error.message
            : 'No se pudo recuperar el avance de tu evaluación. Intenta recargar el módulo.';

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

    message.value = '';

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

        message.value = error instanceof Error
            ? error.message
            : 'No se pudo guardar tu respuesta. Verifica tu conexión e inténtalo de nuevo.';

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

            message.value = 'No se pudo guardar tu avance. Comprueba tu conexión e inténtalo de nuevo.';

        }

    } catch (error) {

        console.error(
            'Error guardando posición:',
            error
        );
        message.value = error instanceof Error
            ? error.message
            : 'No se pudo guardar tu avance. Comprueba tu conexión e inténtalo de nuevo.';

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

function finish() {

    if (
        !evaluationId.value ||
        !allAnswered.value ||
        loading.value ||
        savingAnswer.value
    ) {
        return;
    }

    showFinishConfirmation.value = true;
}

async function finishConfirmed() {
    showFinishConfirmation.value = false;
    if (!evaluationId.value || !allAnswered.value || loading.value || savingAnswer.value) return;

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
            attempt: data.attempt_number,
            attemptsRemaining: Math.max(0, 3 - data.attempt_number),
        };

        stage.value = 'result';

    } catch (error: any) {

        console.error(
            'Error finalizando evaluación:',
            error
        );
        message.value = error?.message || 'No se pudo finalizar la evaluación. Revisa tu conexión e inténtalo de nuevo.';

    } finally {

        loading.value = false;

    }
}

/* =========================================================
   RESTART
   ========================================================= */

function restart() {
    current.value = 0;
    answers.value = {};
    evaluationId.value = null;
    videoDone.value = false;
    result.value = { score: 0, correct: 0, total: 0, attempt: 0, attemptsRemaining: 3 };
    stage.value = 'intro';
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

    <div class="min-h-screen bg-[var(--color-paper)] text-[var(--color-ink)]">

        <!-- =====================================================
             HEADER
        ====================================================== -->

        <InstitutionalHeader
            :show-back="true"
            :show-logout="true"
            module-label="Módulo 1"
            :participant-name="fullName"
            :sector="user?.sector?.name"
            @back="emit('back')"
            @logout="logout()"
        />


        <!-- =====================================================
             PDF SIDEBAR DERECHO
        ====================================================== -->

        <div v-if="showDocsMenu" ref="docsMenuRef" class="docs-drawer fixed right-0 top-1/2 z-40
                       -translate-y-1/2">

                <div class="relative flex items-stretch" @mouseenter="openDocsMenu" @mouseleave="closeDocsMenu">

                    <!-- =================================================
                         PESTAÑA
                    ================================================== -->

                    <button type="button" @click.stop="toggleDocsMenu" title="Documentos de apoyo" aria-label="Abrir documentos de apoyo" :aria-expanded="docsMenuOpen" class="docs-drawer__tab page-control relative z-20 flex h-80 w-11
                               cursor-pointer items-center
                               justify-center
                               rounded-l-2xl
                               border border-r-0
                               border-[#dadada]
                               bg-white
                               text-[#575756]
                               shadow-[0_8px_30px_rgba(0,0,0,0.08)]
                               ease-[var(--ease-out)]
                               [@media(hover:hover)_and_(pointer:fine)]:hover:bg-[#575756]
                               [@media(hover:hover)_and_(pointer:fine)]:hover:text-white
                               [@media(hover:hover)_and_(pointer:fine)]:hover:shadow-[0_8px_30px_rgba(0,0,0,0.18)]
                               focus-visible:outline
                               focus-visible:outline-3
                               focus-visible:outline-offset-2
                               focus-visible:outline-[var(--color-focus)]">

                        <div class="flex flex-col
                                   items-center gap-1.5">

                            <FileText :size="18" aria-hidden="true" />

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

                        <div v-if="docsMenuOpen" class="docs-drawer__panel absolute right-11 top-1/2
                                   -translate-y-1/2">

                            <aside class="docs-drawer__surface w-[360px]
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
                                           bg-[var(--color-brand-800)]
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

                                            <FileText :size="17" aria-hidden="true" />

                                        </div>


                                        <div>

                                            <p class="text-sm
                                                       font-black
                                                       leading-tight">
                                                Documentos de apoyo
                                            </p>

                                            <p class="text-[10px]
                                                       text-white/75
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
                                        @click="openDocument(doc)" class="page-control group/doc flex w-full
                                               items-center gap-3
                                               rounded-xl p-2
                                               text-left
                                               transition-colors
                                               duration-200 ease-[var(--ease-out)]
                                               [@media(hover:hover)_and_(pointer:fine)]:hover:bg-[#f4f4f3]
                                               [@media(hover:hover)_and_(pointer:fine)]:hover:shadow-sm
                                               focus-visible:outline
                                               focus-visible:outline-3
                                               focus-visible:outline-offset-2
                                               focus-visible:outline-[var(--color-focus)]">

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
                                                   transition-colors
                                                   duration-200 ease-[var(--ease-out)]
                                                   group-hover/doc:border-[#878787]
                                                   group-hover/doc:shadow-md">

                                            <img v-if="
                                                thumbnails[doc.id]
                                            " :src="thumbnails[doc.id]
                                                    " :alt="`Portada de ${doc.title}`
                                                    " class="h-full
                                                       w-full
                                                       object-cover" />

                                            <FileText v-else :size="18" aria-hidden="true" class="text-[var(--color-brand-700)]" />

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
                                                       text-[var(--color-muted)]">

                                                <FileText :size="11" aria-hidden="true" />

                                                Consultar documento

                                            </span>

                                        </span>


                                        <!-- FLECHA -->

                                                    <ChevronRight :size="15" class="shrink-0
                                                   text-[var(--color-brand-700)]
                                                   transition-colors
                                                   duration-200 ease-[var(--ease-out)]
                                                   group-hover/doc:text-[var(--color-brand-900)]" aria-hidden="true" />

                                    </button>

                                </div>

                            </aside>

                        </div>

                    </Transition>

                </div>

            </div>


        <!-- =====================================================
             MAIN
        ====================================================== -->

        <main id="main-content" tabindex="-1" class="mx-auto w-full max-w-6xl
                   px-4 py-6 sm:px-6 sm:py-8 lg:px-8">

            <BaseAlert v-if="message && stage !== 'result'" floating variant="destructive" title="No se pudo guardar o completar la acción" :description="message" />

            <!-- ===================================================
                 INTRO
            ==================================================== -->

            <section v-if="stage === 'intro'" class="mx-auto max-w-4xl">

                <div class="mx-auto rounded-[var(--radius-card)] border border-[var(--color-line)] bg-[var(--color-surface)] p-5 shadow-[var(--shadow-card)] sm:p-8 lg:p-10">

                    <span class="inline-flex items-center gap-2 text-sm font-semibold text-[var(--color-accent)]">

                        <PlayCircle :size="18" aria-hidden="true" />

                        Material introductorio · Módulo 1

                    </span>


                    <h1 class="mt-4 max-w-3xl text-2xl font-bold leading-tight tracking-tight text-[var(--color-brand-950)] sm:text-3xl lg:text-4xl">
                        Nociones básicas de derecho electoral

                    </h1>


                    <p class="mt-4 max-w-2xl text-base leading-7 text-[var(--color-muted)]">
                        Revisa el material del curso antes de iniciar la evaluación. El video debe completarse para habilitar las preguntas.

                    </p>


                    <div class="mt-6 flex items-start gap-3 rounded-xl border border-[var(--color-line)] bg-[var(--color-paper)] p-4">

                        <LockKeyhole v-if="!videoDone" :size="19" class="mt-0.5 shrink-0 text-[var(--color-brand-700)]" aria-hidden="true" />
                        <CheckCircle2 v-else :size="19" class="mt-0.5 shrink-0 text-[var(--color-success)]" aria-hidden="true" />

                        <p v-if="!videoDone" class="text-sm leading-6 text-[var(--color-brand-900)]">Completa el video para continuar. Tu avance se guardará al comenzar la evaluación.</p>

                        <p v-else class="text-sm font-semibold leading-6 text-[var(--color-success)]">Video completado. Ya puedes continuar con la evaluación.</p>

                    </div>

                </div>


                <!-- =================================================
                     VIDEO
                ================================================== -->

                <div class="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center">

                    <button
                        type="button"
                        class="intro-primary page-control inline-flex min-h-12 items-center justify-center gap-2 rounded-[var(--radius-control)] bg-[var(--color-brand-900)] px-5 py-3 text-sm font-semibold text-white [@media(hover:hover)_and_(pointer:fine)]:hover:bg-[var(--color-brand-800)]"
                        aria-label="Ver video de capacitación"
                        @click="openVideoModal"
                    >
                        <PlayCircle :size="19" aria-hidden="true" />
                        Ver video de capacitación
                    </button>
                    <span class="text-sm leading-6 text-[var(--color-muted)]">La evaluación se desbloquea al finalizar la reproducción.</span>
                </div>


            <Transition name="modal-fade">

                <div
                    v-if="videoModalOpen"
                    class="fixed inset-0 z-[9999] flex min-h-dvh flex-col overflow-y-auto bg-[#20201f] text-white"
                    role="dialog"
                    aria-modal="true"
                    aria-labelledby="video-modal-title"
                    @click.self="closeVideoModal"
                >
                    <div class="flex min-h-dvh w-full flex-col">
                        <header class="border-b border-white/10 bg-[#292928] px-5 py-4 md:px-10">
                            <div class="mx-auto flex max-w-7xl items-center gap-4">
                                <button
                                    type="button"
                                    title="Regresar al panel de módulos"
                                    aria-label="Regresar al panel de módulos"
                                    class="page-control inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border border-white/30 text-white [@media(hover:hover)_and_(pointer:fine)]:hover:bg-white/10"
                                    @click="emit('back')"
                                >
                                    <ArrowLeft :size="20" aria-hidden="true" />
                                </button>
                                <img
                                    src="/logo_fgjtam.png"
                                    alt="Logo Fiscalía General de Justicia de Tamaulipas"
                                    class="h-9 w-auto max-w-[72px] object-contain sm:h-12 sm:max-w-none md:h-16"
                                />

                                <div class="h-8 w-px shrink-0 bg-white/40 sm:h-10 md:h-12" />

                                <img
                                    src="/logo_fede.png"
                                    alt="Logo Fiscalía Especializada en Delitos Electorales"
                                    class="h-9 w-auto max-w-[72px] object-contain sm:h-12 sm:max-w-none md:h-16"
                                />

                                <div class="ml-auto min-w-0 pr-10">
                                    <p class="hidden truncate text-xs font-bold uppercase tracking-[0.18em] text-white/75 sm:block">
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
                                class="page-control absolute right-3 top-3 inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-white sm:right-5 sm:top-5 md:right-10"
                                @click="closeVideoModal"
                            >
                                <X :size="20" aria-hidden="true" />
                            </button>
                            </div>
                        </header>

                        <main class="flex flex-1 flex-col items-center justify-center px-4 py-8 md:px-10 md:py-12">
                            <div class="mb-6 w-full max-w-6xl text-left md:mb-8">
                                <p class="text-xl font-bold leading-tight md:text-3xl">
                                    Módulo 1: Nociones básicas de derecho electoral
                                </p>
                                <p class="mt-2 text-sm leading-6 text-white/75 md:text-base">
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

                            <div class="mt-6 flex w-full max-w-6xl flex-col items-stretch justify-between gap-4 border-t border-white/15 pt-6 sm:flex-row sm:items-center">
                                <p class="text-sm leading-6 text-white/75">
                                    <span v-if="!videoDone">La evaluación se habilita al terminar el video.</span>
                                    <span v-else class="font-bold text-white">Video completado. Ya puedes continuar.</span>
                                </p>

                                <button
                                    type="button"
                                    :disabled="!videoDone || loading"
                                    class="page-control min-h-12 rounded-[var(--radius-control)] bg-white px-6 py-3 text-sm font-semibold text-[#202020] [@media(hover:hover)_and_(pointer:fine)]:hover:bg-[#eeeeed] disabled:cursor-not-allowed disabled:opacity-50"
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

                <header class="rounded-[var(--radius-card)] border border-[var(--color-line)] bg-[var(--color-surface)] p-4 shadow-[var(--shadow-card)] sm:p-6">

                    <div class="flex flex-wrap items-start justify-between gap-x-6 gap-y-3">

                        <div class="min-w-0 flex-1">
                        <p class="text-sm font-semibold text-[var(--color-accent)]">Módulo 1 · Evaluación</p>
                        <h1 class="mt-1 max-w-2xl text-lg font-bold leading-6 text-[var(--color-brand-950)] sm:text-xl">
                            Nociones básicas de derecho electoral
                        </h1>
                        </div>

                        <p class="shrink-0 rounded-lg bg-[var(--color-paper)] px-3 py-2 text-sm font-semibold tabular-nums text-[var(--color-brand-900)]">
                            Pregunta {{ current + 1 }} de {{ questions.length }}
                        </p>
                    </div>

                    <div class="mt-5 flex flex-wrap items-center justify-between gap-2 text-sm">
                      <span class="font-medium text-[var(--color-brand-900)]">{{ answeredCount }} de {{ questions.length }} contestadas</span>
                      <span class="text-[var(--color-muted)]">Avance: {{ Math.round(progress) }}%</span>
                    </div>
                    <div class="mt-2 h-2.5 overflow-hidden rounded-full bg-[var(--color-brand-100)]" role="progressbar" :aria-valuenow="answeredCount" aria-valuemin="0" :aria-valuemax="questions.length" :aria-valuetext="`${answeredCount} de ${questions.length} preguntas contestadas`" aria-label="Avance de la evaluación">
                      <div class="h-full rounded-full bg-[var(--color-accent)] transition-[width] duration-200" :style="{ width: progress + '%' }" />
                    </div>
                </header>


                <!-- QUESTION CARD -->

                <article v-if="q" class="mt-4 rounded-[var(--radius-card)] border border-[var(--color-line)]
                           bg-[var(--color-surface)] p-5 shadow-[var(--shadow-card)] sm:mt-6 sm:p-8 lg:p-10">

                        <div :key="q.id">

                            <!-- QUESTION -->

                            <div class="flex items-start gap-3 sm:gap-4">

                                <span aria-hidden="true" class="flex h-10 w-10
                                           shrink-0
                                           items-center
                                           justify-center
                                           rounded-xl
                                           bg-[var(--color-brand-900)]
                                           text-sm
                                           font-bold
                                           text-white">
                                    {{ current + 1 }}
                                </span>


                                <h2 class="min-w-0 pt-1 text-lg font-semibold leading-7 text-[var(--color-brand-950)] sm:text-xl sm:leading-8">
                                    {{ q.text }}
                                </h2>

                            </div>


                            <!-- OPTIONS -->

                            <fieldset class="mt-6 space-y-3 sm:mt-8" :aria-busy="savingAnswer">
                                <legend class="sr-only">Selecciona una respuesta</legend>

                                <button v-for="o in q.options" :key="o.id" type="button" :disabled="savingAnswer" :aria-pressed="answers[q.id] === o.id" @click="
                                    selectOption(o.id)
                                    " class="exam-option page-control group flex min-h-14 w-full items-start gap-3 rounded-xl border p-4 text-left text-base leading-6 disabled:cursor-wait disabled:opacity-60 sm:gap-4" :class="answers[q.id] === o.id
                                                ? 'exam-option--selected'
                                                : 'exam-option--idle'
                                            ">

                                    <span class="flex h-8 w-8
                                               shrink-0
                                               items-center
                                               justify-center
                                               rounded-lg
                                               border
                                               text-sm
                                               font-semibold" :class="answers[q.id] === o.id
                                                    ? 'border-[var(--color-brand-900)] bg-[var(--color-brand-900)] text-white'
                                                    : 'border-[var(--color-brand-700)] bg-white text-[var(--color-brand-900)]'
                                                ">
                                        {{ o.letter.toUpperCase() }}
                                    </span>


                                    <span class="min-w-0 flex-1 pt-0.5 text-[var(--color-brand-950)]">
                                        {{ o.text }}
                                    </span>


                                    <CheckCircle2 v-if="answers[q.id] === o.id" aria-hidden="true" class="mt-1 shrink-0 text-[var(--color-success)]" :size="18" />

                                </button>

                            </fieldset>


                            <!-- SAVE STATUS -->

                            <p v-if="savingAnswer" role="status" aria-live="polite" class="mt-4 text-sm font-medium text-[var(--color-accent)]">Guardando respuesta…</p>

                        </div>



                    <!-- NAVIGATION -->

                </article>

                <nav v-if="questions.length" aria-label="Navegación de preguntas" class="mt-4 flex flex-col gap-4 sm:mt-5">

                    <div role="group" aria-label="Ir a una pregunta" class="flex flex-wrap items-center justify-center gap-2">

                        <button v-for="(item, index) in questions" :key="item.id" type="button" @click="goToQuestion(index)" :disabled="index > maxReachableIndex || savingAnswer" :aria-label="`Pregunta ${index + 1}${answers[item.id] != null ? ', contestada' : ', pendiente'}`" :aria-current="index === current ? 'step' : undefined" class="question-index min-h-11 min-w-11 rounded-[var(--radius-control)] border px-2 text-sm font-semibold tabular-nums disabled:cursor-not-allowed disabled:opacity-50" :class="index === current
                            ? 'question-index--current'
                            : answers[item.id] != null
                                ? 'question-index--answered'
                                : 'question-index--pending'">
                            {{ index + 1 }}
                        </button>

                    </div>

                    <div class="flex flex-col-reverse gap-3 border-t border-[var(--color-line)] pt-4 sm:flex-row sm:items-center sm:justify-between">
                      <button type="button" @click="previous" :disabled="current === 0 || savingAnswer" aria-label="Pregunta anterior" class="page-control inline-flex min-h-11 items-center justify-center gap-2 rounded-[var(--radius-control)] border border-[var(--color-brand-700)] bg-[var(--color-surface)] px-4 py-2 text-sm font-semibold text-[var(--color-brand-900)] disabled:cursor-not-allowed disabled:opacity-50 [@media(hover:hover)_and_(pointer:fine)]:hover:bg-[var(--color-brand-100)]">
                        <ChevronLeft :size="18" aria-hidden="true" /> Anterior
                      </button>

                      <button v-if="canNext" type="button" @click="next" :disabled="savingAnswer" class="page-control inline-flex min-h-11 items-center justify-center gap-2 rounded-[var(--radius-control)] bg-[var(--color-brand-900)] px-5 py-2 text-sm font-semibold text-white [@media(hover:hover)_and_(pointer:fine)]:hover:bg-[var(--color-brand-800)] disabled:cursor-wait disabled:opacity-50">
                        Siguiente pregunta <ChevronRight :size="18" aria-hidden="true" />
                      </button>

                      <button v-else-if="allAnswered && current === maxReachableIndex" type="button" @click="finish" :disabled="loading || savingAnswer" class="page-control inline-flex min-h-11 items-center justify-center gap-2 rounded-[var(--radius-control)] bg-[var(--color-brand-900)] px-5 py-2 text-sm font-semibold text-white [@media(hover:hover)_and_(pointer:fine)]:hover:bg-[var(--color-brand-800)] disabled:cursor-wait disabled:opacity-50">
                        {{ loading ? 'Finalizando…' : 'Finalizar evaluación' }} <CheckCircle2 :size="18" aria-hidden="true" />
                      </button>

                      <span v-else class="text-center text-sm text-[var(--color-muted)] sm:text-right">Selecciona una respuesta para avanzar.</span>
                    </div>

                </nav>

            </section>


            <!-- ===================================================
                 RESULT
            ==================================================== -->

            <EvaluationResult v-else module-id="1" module-name="Nociones básicas de derecho electoral" :score="result.score" :correct="result.correct" :total="result.total" :attempt="result.attempt" :attempts-remaining="result.attemptsRemaining" :message="message" @retry="restart" @back="emit('back')" />

        </main>

        <ConfirmDialog
            v-if="showFinishConfirmation"
            title="¿Finalizar evaluación?"
            description="Al finalizar, tus respuestas quedarán registradas y ya no podrás modificarlas. Revisa que todas estén contestadas antes de continuar."
            confirm-label="Finalizar evaluación"
            :busy="loading"
            @cancel="showFinishConfirmation = false"
            @confirm="finishConfirmed"
        />


        <!-- =====================================================
             FOOTER
        ====================================================== -->

        <footer class="mx-auto max-w-6xl
                   px-5 pb-8
                   text-center
                   text-xs
                   text-[var(--color-muted)]">

            Fiscalía General de Justicia
            del Estado de Tamaulipas

            ·

            Fiscalía Especializada
            en Delitos Electorales

        </footer>


        <!-- =====================================================
             PDF VIEWER MODAL
        ====================================================== -->

        <Transition name="modal-fade">

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

                                <FileText :size="16" aria-hidden="true" />

                            </span>


                            <p class="truncate
                                       text-sm
                                       font-bold">
                                {{ viewingDoc.title }}
                            </p>

                        </div>


                        <button @click="closeViewer" title="Cerrar" aria-label="Cerrar documento" class="page-control inline-flex
                                   h-11 w-11
                                   shrink-0
                                   items-center
                                   justify-center
                                   rounded-lg
                                   text-[var(--color-brand-700)]
                                   transition
                                   [@media(hover:hover)_and_(pointer:fine)]:hover:bg-[#f4f4f3]
                                   [@media(hover:hover)_and_(pointer:fine)]:hover:text-[#575756]">

                            <X :size="18" aria-hidden="true" />

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
.exam-option,
.question-index {
    transition:
        background-color var(--motion-fast) var(--ease-out),
        border-color var(--motion-fast) var(--ease-out),
        color var(--motion-fast) var(--ease-out),
        box-shadow var(--motion-fast) var(--ease-out);
}

.exam-option--idle { border-color: var(--color-brand-700); background: var(--color-surface); }
.exam-option--selected { border-color: var(--color-accent); background: var(--color-accent-soft); box-shadow: inset 0 0 0 1px var(--color-accent); }
.question-index--current { border-color: var(--color-brand-900); background: var(--color-brand-900); color: #fff; }
.question-index--answered { border-color: var(--color-brand-700); background: var(--color-brand-100); color: var(--color-brand-900); }
.question-index--pending { border-color: var(--color-brand-700); background: var(--color-surface); color: var(--color-brand-900); }

@media (hover: hover) and (pointer: fine) {
    .exam-option--idle:hover { border-color: var(--color-brand-700); background: var(--color-paper); }
    .question-index--pending:hover { border-color: var(--color-brand-700); background: var(--color-paper); }
}

.docs-drawer__tab,
.docs-drawer__panel,
.docs-drawer__surface {
    transition:
        background-color var(--motion-fast) var(--ease-out),
        border-color var(--motion-fast) var(--ease-out),
        color var(--motion-fast) var(--ease-out),
        box-shadow var(--motion-fast) var(--ease-out);
}

@media (max-width: 639px) {
    .docs-drawer {
        top: auto !important;
        right: 12px !important;
        bottom: 12px !important;
        transform: none !important;
    }

    .docs-drawer__tab {
        width: auto !important;
        height: 48px !important;
        padding: 0 14px !important;
        gap: 8px !important;
        border: 1px solid var(--color-brand-700) !important;
        border-radius: 999px !important;
        background: var(--color-surface) !important;
        color: var(--color-brand-900) !important;
        box-shadow: 0 4px 16px rgb(32 32 32 / 14%) !important;
    }

    .docs-drawer__tab > div { flex-direction: row !important; gap: 8px !important; }
    .docs-drawer__tab span { writing-mode: horizontal-tb !important; font-size: 12px !important; letter-spacing: 0.02em !important; }

    .docs-drawer__panel {
        top: auto !important;
        right: 0 !important;
        bottom: 56px !important;
        width: min(360px, calc(100vw - 24px)) !important;
        transform: none !important;
    }

    .docs-drawer__surface {
        display: flex !important;
        flex-direction: column !important;
        width: 100% !important;
        max-height: min(70dvh, 560px) !important;
        border: 1px solid var(--color-line) !important;
        border-radius: var(--radius-card) !important;
        box-shadow: var(--shadow-dialog) !important;
    }

    .docs-drawer__surface > div:last-child {
        max-height: calc(70dvh - 64px) !important;
    }
}

.docs-panel-enter-active,
.docs-panel-leave-active,
.modal-fade-enter-active,
.modal-fade-leave-active,
.intro-primary {
    transition-duration: var(--motion-standard);
}

@media (prefers-reduced-motion: reduce) {
    .exam-option,
    .question-index,
    .docs-drawer__tab,
    .docs-drawer__panel,
    .docs-drawer__surface,
    .intro-primary {
        transition: none !important;
    }
}

/* One shared entrance per full-screen viewer; its content arrives with it. */
.modal-fade-enter-active,
.modal-fade-leave-active {
    transition: opacity 180ms var(--ease-out);
}

.modal-fade-leave-active { transition-duration: 140ms; }

.modal-fade-enter-from,
.modal-fade-leave-to { opacity: 0; }


/* =========================================================
   PDF SIDEBAR - PANEL
   ========================================================= */

.docs-panel-enter-active {

    transition:
        opacity 180ms var(--ease-out),
        transform 180ms var(--ease-out);
    transform-origin: right center;

}

.docs-panel-leave-active {

    transition:
        opacity 140ms var(--ease-out),
        transform 140ms var(--ease-out);
    transform-origin: right center;

}

.docs-panel-enter-from,
.docs-panel-leave-to {

    opacity: 0;

    transform: translateX(12px) scale(0.97);

}

@media (prefers-reduced-motion: reduce) {
    .modal-fade-enter-active,
    .modal-fade-leave-active {
        transition-duration: 120ms !important;
    }

    .docs-panel-enter-active,
    .docs-panel-leave-active {
        transition-duration: 120ms !important;
    }

    .docs-panel-enter-from,
    .docs-panel-leave-to {
        transform: none;
    }
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
