import { ref, computed } from 'vue';

export type Institution = { id: number; name: string };

export type AuthUser = {
  id: number;
  first_name: string;
  paternal_surname: string;
  maternal_surname: string;
  email: string;
  curp: string;
  institution: Institution;
};

const API = import.meta.env.VITE_API_URL;

const TOKEN_KEY = 'fede_exam_token';
const USER_KEY = 'fede_exam_user';

const token = ref<string | null>(localStorage.getItem(TOKEN_KEY));
const user = ref<AuthUser | null>(
  JSON.parse(localStorage.getItem(USER_KEY) || 'null')
);

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
function extractErrorMessage(data: any, fallback: string): string {
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

async function register(payload: {
  first_name: string;
  paternal_surname: string;
  maternal_surname: string;
  email: string;
  password: string;
  curp: string;
}) {
  const response = await fetch(`${API}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(extractErrorMessage(data, 'No se pudo completar el registro.'));
  }

  persist(data.access_token, data.user);
  return data.user as AuthUser;
}

async function fetchInstitutions(): Promise<Institution[]> {
  const response = await fetch(`${API}/api/institutions`);
  if (!response.ok) throw new Error('No se pudo cargar el catálogo de instituciones.');
  return response.json();
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
    logout,
    fetchInstitutions,
    apiFetch,
  };
}