# 001 — Unify page and layout control motion

- **Status**: TODO
- **Commit**: `f1e26c4`
- **Severity**: MEDIUM
- **Category**: Cohesion & tokens
- **Estimated scope**: 7 Vue files and shared CSS; class and small scoped-style changes only

## Problem

The base controls now use `--ease-out: cubic-bezier(0.23, 1, 0.32, 1)`, press feedback, pointer-gated hover, and reduced-motion rules. Main pages and the institutional layout still contain one-off controls with Tailwind's default `ease`, generic `transition`, or hover movement and colors without the same motion contract. This makes the login, registration, recovery, exam, and header controls feel different from the shared base button. The exam answer controls are used repeatedly, so their motion should stay limited to color and border changes.

Confirmed examples:

```html
<!-- frontend/src/components/layout/InstitutionalHeader.vue:40 -->
class="... transition-colors duration-200 hover:bg-[#f2f2f1] ..."

<!-- frontend/src/views/auth/PasswordRecoveryView.vue:103 -->
class="... transition hover:bg-[#1f1f1e] ..."

<!-- frontend/src/views/exams/ExamModuleView.vue:421 -->
class="... rounded-2xl border p-4 text-left transition disabled:opacity-60"

<!-- frontend/src/views/exams/ExamFlowView.vue:1804 -->
class="... rounded-2xl border p-4 text-left transition disabled:opacity-60"
```

The related controls are in `frontend/src/views/auth/LoginView.vue`, `frontend/src/views/auth/RegisterView.vue`, `frontend/src/views/modules/ModulePanelView.vue`, `frontend/src/views/exams/ExamModuleView.vue`, `frontend/src/views/exams/ExamFlowView.vue`, `frontend/src/components/layout/InstitutionalHeader.vue`, and `frontend/src/views/auth/PasswordRecoveryView.vue`.

## Target

- Reuse the shared `--ease-out` token (`cubic-bezier(0.23, 1, 0.32, 1)`) for page and layout control transitions.
- Keep button press feedback at `scale(0.97)` with `160ms`; keep the module-card press feedback subtle at `scale(0.99)` and `140ms`.
- Keep ordinary control color, border, and opacity transitions at `150–200ms`; never use `transition`/`transition-all` when an exact property list is available.
- Gate hover-only visual changes behind `@media (hover: hover) and (pointer: fine)`. Preserve keyboard focus styles and do not add movement to exam answers, question navigation, or data displays.
- Preserve the established reduced-motion behavior: remove transform changes, retain color/opacity feedback at `120ms`.
- Keep page transitions and exam question changes immediate; they were deliberately removed for frequent navigation.

## Repo conventions to follow

- Motion tokens and the global reduced-motion fallback live in `frontend/src/styles/index.css`.
- `frontend/src/components/ui/BaseButton.vue` is the reference for button timing, curve, press feedback, hover gating, and reduced motion.
- `frontend/src/components/ui/ConfirmDialog.vue` is the reference for scoped pointer gating and custom transitions.
- `frontend/src/views/modules/ModulePanelView.vue` is the reference for card press feedback and reduced motion.

## Steps

1. In `frontend/src/components/layout/InstitutionalHeader.vue` and `frontend/src/views/auth/PasswordRecoveryView.vue`, replace generic/default-easing transitions on action buttons with explicit color transitions using `150ms var(--ease-out)`. Add `scale(0.97)` press feedback with `160ms var(--ease-out)` only to enabled pointer-pressable actions. Gate hover color changes behind the fine-pointer media query.
2. In `frontend/src/views/auth/LoginView.vue` and `frontend/src/views/auth/RegisterView.vue`, align page-level buttons, password visibility controls, and field wrappers with the same explicit properties and `var(--ease-out)` curve. Retain existing field state changes and error/conditional-content fades; do not add entrance motion to forms.
3. In `frontend/src/views/exams/ExamModuleView.vue` and `frontend/src/views/exams/ExamFlowView.vue`, replace bare `transition` classes on answer options and question navigation with explicit color/border properties at `150ms var(--ease-out)`. Do not animate question content or answer text. Align major exam actions and document controls with the base timing, and gate their hover-only colors.
4. In `frontend/src/views/modules/ModulePanelView.vue`, keep the existing card `140ms` press and border feedback, verify hover is fine-pointer-only, and preserve reduced-motion removal of scale.
5. Make reduced-motion behavior consistent for every newly added transform: force no transform while preserving color and opacity feedback at `120ms var(--ease-out)`. Do not change modal, document-panel, toast, or form-content transitions that already use shared tokens.

## Boundaries

- Do not add animation to route changes, question changes, keyboard navigation, or data updates.
- Do not add dependencies, new dropdowns, or tooltip components.
- Do not change application behavior, markup semantics, layout, or focus management.
- Preserve existing shared base-component behavior and motion tokens.
- If a cited control no longer has the generic transition when executing, leave it unchanged and report the drift instead of broadening scope.

## Verification

- **Mechanical**: run `git diff --check`; search the seven scoped files for bare `transition`, `transition-all`, and ungated `hover:` controls; confirm no motion duration is `300ms` or longer.
- **Feel check**: open login, registration, recovery, module panel, and exam views. Press and release primary and secondary controls; confirm press returns immediately and never looks like a card lift. Hover controls with a mouse and tap with a touch emulator; confirm touch does not retain a hover state. Select answers and navigate questions repeatedly; confirm content does not animate between questions.
- Enable `prefers-reduced-motion`; confirm button/card transforms are removed while useful color and opacity feedback remains.
- **Done when**: page/layout control transitions use the shared curve and sub-300ms values, hover changes are fine-pointer-gated, and frequent exam navigation remains immediate.
