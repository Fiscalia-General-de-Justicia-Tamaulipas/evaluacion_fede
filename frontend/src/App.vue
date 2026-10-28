<script setup lang="ts">
import { ref, watch } from 'vue';
import Login from './components/Login.vue';
import Register from './components/Register.vue';
import ExamFlow from './components/ExamFlow.vue';
import ModulePanel from './components/ModulePanel.vue';
import ExamModule from './components/ExamModule.vue';
import { useAuth } from './lib/auth';

const { isAuthenticated } = useAuth();
const authView = ref<'login' | 'register'>('login');
const selectedModule = ref<number | null>(null);

watch(isAuthenticated, (authenticated) => {
  if (authenticated) {
    selectedModule.value = null;
  }
});
</script>

<template>
  <head>
    <title>Evaluación de Capacitación - Fiscalía Especializada en Delitos Electorales</title>
  </head>  
  <ModulePanel
    v-if="isAuthenticated && selectedModule === null"
    @select-module="selectedModule = $event"
    @back-login="null"
  />
  <ExamFlow
    v-else-if="isAuthenticated && selectedModule === 1"
    @back="selectedModule = null"
  />
  <ExamModule
    v-else-if="isAuthenticated && selectedModule !== null"
    :module-id="selectedModule"
    @back="selectedModule = null"
  />
  <Login v-else-if="authView === 'login'" @go-register="authView = 'register'" />
  <Register v-else @go-login="authView = 'login'" @success="authView = 'login'" />
</template>