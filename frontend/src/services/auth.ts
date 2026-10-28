import { ref, computed } from 'vue';

export type Institution = { id: number; name: string };

export type AuthUser = {
  id: number;
  first_name: string;
  paternal_surname: string;
  maternal_surname: string;
  email: string;
  curp: string;
  full_name?: string;
  institution?: Institution;
  sector?: { id: number; name: string } | null;
};

const API = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

const TOKEN_KEY = 'fede_exam_token';
const USER_KEY = 'fede_exam_user';

function readStoredUser(): AuthUser | null {
  try {
    const stored = localStorage.getItem(USER_KEY);
    return stored ? JSON.parse(stored) as AuthUser : null;
  } catch {
    localStorage.removeItem(USER_KEY);
    return null;
  }
}

const token = ref<string | null>(localStorage.getItem(TOKEN_KEY));
const user = ref<AuthUser | null>(readStoredUser());

const isAuthenticated = computed(() => !!token.value);

const fullName = computed(() =>
  user.value
    ? `${user.value.first_name} ${user.value.paternal_surname} ${user.value.maternal_surname}`.trim()
    : ''
);

function persist(nextToken: string, nextUser: AuthUser) {
  token.value = nextToken;
  user.value = nextUser;
  localStorage.setItem(TOKEN_KEY, nextToken);
  localStorage.setItem(USER_KEY, JSON.stringify(nextUser));
}

function clear() {
  token.value = null;
  user.value = null;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

// Convierte el "detail" de una respuesta de error en un mensaje legible.
// Soporta: string normal, array crudo de errores de Pydantic (por si algún
// endpoint no pasa por el exception handler en español), u otros formatos.
export function extractErrorMessage(data: any, fallback: string): string {
  const detail = data?.detail;

  if (!detail) return fallback;

  if (typeof detail === 'string') {
    return detail;
  }

  if (Array.isArray(detail)) {
    const first = detail[0];
    if (typeof first === 'string') return first;
    if (first?.msg) return first.msg;
  }

  return fallback;
}

async function apiFetch(path: string, options: RequestInit = {}) {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  };

  if (token.value) {
    headers['Authorization'] = `Bearer ${token.value}`;
  }

  const response = await fetch(`${API}${path}`, { ...options, headers });

  if (response.status === 401) {
    clear();
  }

  return response;
}

async function login(email: string, password: string) {
  const response = await fetch(`${API}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(extractErrorMessage(data, 'No se pudo iniciar sesión.'));
  }

  persist(data.access_token, data.user);
  return data.user as AuthUser;
}

export type RegisterPayload = {
  first_name: string;
  paternal_surname: string;
  maternal_surname: string;
  email: string;
  password: string;
  curp: string;
  municipality_id?: number | null;
  municipality_other?: string | null;
  municipality_other_state?: string | null;
  gender_id?: number | null;
  gender_other?: string | null;
  age_range_id?: number | null;
  occupation_id?: number | null;
  occupation_other?: string | null;
  sector_id?: number | null;
  indigenous_id?: number | null;
  afro_mexican_id?: number | null;
  disability_id?: number | null;
  lgbtttiq_id?: number | null;
  education_level_id?: number | null;
};

async function register(payload: RegisterPayload) {
  const response = await fetch(`${API}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(extractErrorMessage(data, 'No se pudo completar el registro.'));
  }

  return data.user as AuthUser;
}

async function requestPasswordReset(email: string) {
  const response = await fetch(`${API}/api/auth/password/forgot`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(extractErrorMessage(data, 'No se pudo solicitar la recuperación.'));
  }
  return data as { message: string };
}

async function resetPassword(token: string, newPassword: string) {
  const response = await fetch(`${API}/api/auth/password/reset`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token, new_password: newPassword }),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(extractErrorMessage(data, 'No se pudo cambiar la contraseña.'));
  }
  return data as { message: string };
}


function logout() {
  clear();
}

export function useAuth() {
  return {
    token,
    user,
    isAuthenticated,
    fullName,
    login,
    register,
    requestPasswordReset,
    resetPassword,
    logout,
    apiFetch,
  };
}
