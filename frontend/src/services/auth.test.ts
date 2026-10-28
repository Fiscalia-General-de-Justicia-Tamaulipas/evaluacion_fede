import { beforeEach, describe, expect, it, vi } from 'vitest';
import { extractErrorMessage, useAuth } from './auth';

describe('auth service', () => {
  beforeEach(() => {
    localStorage.clear();
    useAuth().logout();
  });

  it('traduce detail de API y validación de FastAPI', () => {
    expect(extractErrorMessage({ detail: 'Credenciales inválidas' }, 'Error')).toBe('Credenciales inválidas');
    expect(extractErrorMessage({ detail: [{ msg: 'Campo requerido' }] }, 'Error')).toBe('Campo requerido');
    expect(extractErrorMessage({}, 'Intenta más tarde')).toBe('Intenta más tarde');
  });

  it('persiste sesión válida y envía bearer al API; limpia la sesión en 401', async () => {
    const user = { id: 5, first_name: 'Ana', paternal_surname: 'López', maternal_surname: 'Ruiz', email: 'ana@example.org', curp: 'X' };
    const fetchMock = vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(new Response(JSON.stringify({ access_token: 'token-123', user }), { status: 200 }))
      .mockResolvedValueOnce(new Response('{}', { status: 200 }))
      .mockResolvedValueOnce(new Response('{}', { status: 401 }));
    const auth = useAuth();
    await auth.login(user.email, 'secret');
    expect(auth.isAuthenticated.value).toBe(true);
    expect(localStorage.getItem('fede_exam_token')).toBe('token-123');
    await auth.apiFetch('/api/modules/status');
    expect(fetchMock.mock.calls[1][1]?.headers).toMatchObject({ Authorization: 'Bearer token-123' });
    await auth.apiFetch('/api/modules/status');
    expect(auth.isAuthenticated.value).toBe(false);
  });
});
