import { createApp, h } from 'vue';
import { createRouter, createWebHistory, RouterView } from 'vue-router';
import './styles/index.css';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/verificar/:folio',
      component: () => import('./views/certificates/CertificateVerificationView.vue'),
      props: true,
    },
    {
      path: '/:pathMatch(.*)*',
      component: () => import('./App.vue'),
    },
  ],
});

createApp({ render: () => h(RouterView) }).use(router).mount('#app');
