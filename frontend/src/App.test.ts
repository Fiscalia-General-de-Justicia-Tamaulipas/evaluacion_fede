import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { nextTick } from 'vue';
import App from './App.vue';
import { useAuth } from './services/auth';

vi.mock('./views/auth/LoginView.vue', () => ({
  default: {
    props: ['notice'],
    emits: ['go-register', 'go-forgot'],
    template: '<div data-testid="login"><span>{{ notice }}</span><button @click="$emit(\'go-register\')">Registrarse</button></div>',
  },
}));

vi.mock('./views/auth/RegisterView.vue', () => ({
  default: {
    emits: ['success', 'go-login'],
    template: '<div data-testid="register"><button @click="$emit(\'success\')">Registro exitoso</button></div>',
  },
}));

vi.mock('./views/auth/PasswordRecoveryView.vue', () => ({
  default: { template: '<div />' },
}));

vi.mock('./views/courses/CourseCatalogView.vue', () => ({
  default: { template: '<div data-testid="courses" />' },
}));

vi.mock('./views/exams/ExamFlowView.vue', () => ({
  default: { template: '<div />' },
}));

vi.mock('./views/modules/ModulePanelView.vue', () => ({
  default: { template: '<div />' },
}));

vi.mock('./views/exams/ExamModuleView.vue', () => ({
  default: { template: '<div />' },
}));

describe('App', () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    fetchMock = vi.fn().mockResolvedValue(new Response('{}', { status: 200 }));
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(async () => {
    await useAuth().logout();
    localStorage.clear();
    sessionStorage.clear();
    vi.unstubAllGlobals();
  });

  it('limpia el aviso de registro al cerrar sesión', async () => {
    const wrapper = mount(App);
    await wrapper.find('[data-testid="login"] button').trigger('click');
    await wrapper.find('[data-testid="register"] button').trigger('click');
    expect(wrapper.find('[data-testid="login"]').text()).toContain(
      'Tu registro se completó. Ahora puedes iniciar sesión.',
    );

    const user = {
      id: 1,
      first_name: 'Ana',
      paternal_surname: 'López',
      maternal_surname: 'Ruiz',
      email: 'ana@example.org',
      curp: 'ABCD1234EFGH5678IJ',
    };
    fetchMock.mockResolvedValueOnce(new Response(JSON.stringify({
      access_token: 'test-token',
      user,
    }), { status: 200 }));
    await useAuth().login(user.email, 'secret');
    await flushPromises();
    await nextTick();
    expect(wrapper.find('[data-testid="courses"]').exists()).toBe(true);

    await useAuth().logout();
    await flushPromises();
    await nextTick();
    expect(wrapper.find('[data-testid="login"]').text()).not.toContain(
      'Tu registro se completó. Ahora puedes iniciar sesión.',
    );
  });
});
