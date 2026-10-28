<script setup lang="ts">
import { ref, watch } from 'vue';
import Login from './views/auth/LoginView.vue';
import Register from './views/auth/RegisterView.vue';
import PasswordRecovery from './views/auth/PasswordRecoveryView.vue';
import ExamFlow from './views/exams/ExamFlowView.vue';
import ModulePanel from './views/modules/ModulePanelView.vue';
import ExamModule from './views/exams/ExamModuleView.vue';
import { useAuth } from './services/auth';

const { isAuthenticated } = useAuth();
const resetToken = ref(new URLSearchParams(window.location.search).get('reset_token') || '');
const authView = ref<'login' | 'register' | 'forgot' | 'recovery'>(resetToken.value ? 'recovery' : 'login');
const selectedModule = ref<number | null>(null);
const authNotice = ref('');

function registrationSucceeded() {
  authNotice.value = 'Tu registro se completó. Ahora puedes iniciar sesión.';
  authView.value = 'login';
}

function clearResetLink() {
  const url = new URL(window.location.href);
  url.searchParams.delete('reset_token');
  window.history.replaceState({}, document.title, `${url.pathname}${url.search}${url.hash}`);
  resetToken.value = '';
}

function returnToLogin() {
  clearResetLink();
  authView.value = 'login';
}

function passwordResetCompleted() {
  clearResetLink();
  authNotice.value = 'Tu contraseña se actualizó. Ya puedes iniciar sesión.';
  authView.value = 'login';
}

watch(isAuthenticated, (authenticated) => {
  if (authenticated) {
    selectedModule.value = null;
  }
});
</script>

<template>
  <a href="#main-content" class="sr-only z-[100] rounded-md bg-white px-4 py-3 font-semibold text-[#202020] focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus-visible:outline">Saltar al contenido principal</a>
  <Transition name="page" mode="out-in">
    <ModulePanel
      v-if="!resetToken && isAuthenticated && selectedModule === null"
      key="modules"
      @select-module="selectedModule = $event"
    />
    <ExamFlow
      v-else-if="!resetToken && isAuthenticated && selectedModule === 1"
      key="exam-1"
      @back="selectedModule = null"
    />
    <ExamModule
      v-else-if="!resetToken && isAuthenticated && selectedModule !== null"
      :key="`exam-${selectedModule}`"
      :module-id="selectedModule"
      @back="selectedModule = null"
    />
    <Login v-else-if="authView === 'login'" key="login" :notice="authNotice" @go-register="authView = 'register'; authNotice = ''" @go-forgot="authView = 'forgot'; authNotice = ''" />
    <Register v-else-if="authView === 'register'" key="register" @go-login="authView = 'login'" @success="registrationSucceeded" />
    <PasswordRecovery v-else key="password-recovery" :reset-token="authView === 'recovery' ? resetToken : ''" @go-login="returnToLogin" @reset-complete="passwordResetCompleted" />
  </Transition>
</template>
