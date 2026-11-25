<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { X } from 'lucide-vue-next';
import { courseStudyPlan } from './courseStudyPlan';

const props = defineProps<{
  modelValue: boolean;
  courseTitle: string;
}>();

const emit = defineEmits<{ 'update:modelValue': [value: boolean] }>();
const dialog = ref<HTMLDialogElement | null>(null);
const topicCount = computed(() => courseStudyPlan.reduce((total, module) => total + module.topics.length, 0));

function close() {
  if (dialog.value?.open) dialog.value.close();
  emit('update:modelValue', false);
}

watch(() => props.modelValue, isOpen => {
  if (!dialog.value) return;
  if (isOpen && !dialog.value.open) dialog.value.showModal();
  else if (!isOpen && dialog.value.open) dialog.value.close();
});

onMounted(() => {
  if (props.modelValue) dialog.value?.showModal();
});
</script>

<template>
  <dialog
    ref="dialog"
    class="course-study-plan-dialog m-auto w-[calc(100%-2rem)] max-w-5xl overflow-hidden rounded-[var(--radius-card)] border border-[var(--color-line)] bg-[var(--color-surface)] p-0 text-[var(--color-ink)] shadow-[var(--shadow-card)]"
    aria-labelledby="course-study-plan-title"
    aria-describedby="course-study-plan-description"
    aria-modal="true"
    @cancel.prevent="close"
    @click.self="close"
    @close="emit('update:modelValue', false)"
  >
    <div class="flex max-h-[90vh] max-h-[90dvh] flex-col">
      <header class="shrink-0 border-b border-[var(--color-line)] bg-[var(--color-surface)] px-5 py-4 sm:px-7 sm:py-5">
        <div class="flex items-start justify-between gap-4">
          <div class="min-w-0">
            <p class="text-xs font-bold uppercase tracking-[0.13em] text-[var(--color-muted)]">Plan de estudio</p>
            <h2 id="course-study-plan-title" class="mt-1 text-xl font-bold leading-7 text-[var(--color-brand-950)] sm:text-2xl">{{ courseTitle }}</h2>
            <p id="course-study-plan-description" class="mt-2 text-sm leading-6 text-[var(--color-muted)]">
              Contenidos, objetivos generales y objetivos específicos organizados por módulo y tema.
            </p>
            <div class="mt-3 flex flex-wrap gap-2" aria-label="Resumen del plan de estudio">
              <span class="rounded-full border border-[var(--color-line)] bg-[var(--color-paper)] px-3 py-1 text-xs font-semibold text-[var(--color-brand-900)]">{{ courseStudyPlan.length }} módulos</span>
              <span class="rounded-full border border-[var(--color-line)] bg-[var(--color-paper)] px-3 py-1 text-xs font-semibold text-[var(--color-brand-900)]">{{ topicCount }} temas</span>
            </div>
          </div>
          <button
            type="button"
            class="page-control inline-flex min-h-11 min-w-11 shrink-0 items-center justify-center rounded-lg border border-[var(--color-line)] text-[var(--color-brand-900)] hover:bg-[var(--color-paper)]"
            aria-label="Cerrar plan de estudio"
            autofocus
            @click="close"
          >
            <X :size="19" aria-hidden="true" />
          </button>
        </div>
      </header>

      <div class="min-h-0 overflow-y-auto px-4 py-5 sm:px-7 sm:py-6">
        <div class="space-y-7">
          <section
            v-for="(module, moduleIndex) in courseStudyPlan"
            :key="module.title"
            :aria-labelledby="`study-plan-module-${moduleIndex + 1}`"
            class="space-y-4"
          >
            <div class="border-b border-[var(--color-line)] pb-3">
              <p class="text-xs font-bold uppercase tracking-[0.13em] text-[var(--color-muted)]">Módulo {{ moduleIndex + 1 }}</p>
              <h3 :id="`study-plan-module-${moduleIndex + 1}`" class="mt-1 text-lg font-bold leading-6 text-[var(--color-brand-950)] sm:text-xl">{{ module.title }}</h3>
            </div>

            <article
              v-for="topic in module.topics"
              :key="topic.title"
              class="rounded-lg border border-[var(--color-line)] bg-[var(--color-surface)] p-4 sm:p-5"
            >
              <h4 class="text-base font-bold leading-6 text-[var(--color-brand-950)] sm:text-lg">{{ topic.title }}</h4>

              <div class="mt-4 grid gap-5 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
                <div class="space-y-4">
                  <section aria-label="Subtemas">
                    <h5 class="text-xs font-bold uppercase tracking-[0.1em] text-[var(--color-muted)]">Subtemas</h5>
                    <ul class="mt-2 space-y-2">
                      <li v-for="subtopic in topic.subtopics" :key="subtopic" class="flex items-start gap-2 text-sm leading-5 text-[var(--color-ink)]">
                        <span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--color-brand-700)]" aria-hidden="true" />
                        <span>{{ subtopic }}</span>
                      </li>
                    </ul>
                  </section>

                  <section class="rounded-md border-l-2 border-[var(--color-brand-700)] bg-[var(--color-paper)] p-3" aria-label="Objetivo general">
                    <h5 class="text-xs font-bold uppercase tracking-[0.1em] text-[var(--color-muted)]">Objetivo general</h5>
                    <p class="mt-1 text-sm leading-5 text-[var(--color-ink)]">
                      <span class="font-semibold">{{ topic.generalObjective.code }}</span>
                      {{ topic.generalObjective.text }}
                    </p>
                  </section>
                </div>

                <section aria-label="Objetivos específicos">
                  <h5 class="text-xs font-bold uppercase tracking-[0.1em] text-[var(--color-muted)]">Objetivos específicos</h5>
                  <ol class="mt-2 space-y-3">
                    <li v-for="objective in topic.specificObjectives" :key="objective.code" class="flex items-start gap-2 text-sm leading-5 text-[var(--color-ink)]">
                      <span class="shrink-0 font-semibold text-[var(--color-brand-900)]">{{ objective.code }}</span>
                      <span>{{ objective.text }}</span>
                    </li>
                  </ol>
                </section>
              </div>
            </article>
          </section>
        </div>
      </div>
    </div>
  </dialog>
</template>

<style scoped>
.course-study-plan-dialog::backdrop {
  background: rgb(0 0 0 / 55%);
}
</style>
