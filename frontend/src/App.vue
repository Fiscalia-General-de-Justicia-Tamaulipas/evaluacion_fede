<script setup lang="ts">
import { ref } from 'vue';
import Login from './components/Login.vue';
import Register from './components/Register.vue';
import ExamFlow from './components/ExamFlow.vue';
import { useAuth } from './lib/auth';

const { isAuthenticated } = useAuth();
const authView = ref<'login' | 'register'>('login');
</script>

<template>
  <head>
    <title>Evaluación de Capacitación - Fiscalía Especializada en Delitos Electorales</title>
  </head>  
  <ExamFlow v-if="isAuthenticated" />
  <Login v-else-if="authView === 'login'" @go-register="authView = 'register'" />
  <Register v-else @go-login="authView = 'login'" @success="authView = 'login'" />
</template>