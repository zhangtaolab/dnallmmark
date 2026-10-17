"""
screens — Textual presentation screens (Phase 8; populated from 08-03).

Contract:

- Screens are presentation ONLY: they render state held by services and post
  user intent back — zero business logic (everything algorithmically
  testable lives in ``tui/services/``; binding constraint 5).
- Screens import textual freely (the ONLY tier allowed to) and receive their
  services via constructor injection, so tier-2 Pilot tests run them against
  deterministic fakes (RESEARCH Pattern 7) and GPU-touching kernels never
  execute in CI (D-03: workers are ``@work(thread=True)`` on screens).
- Every drill-down and confirm surface is a ``ModalScreen`` — modals block
  app-level bindings while on top (RESEARCH Pitfall 11).
- Operator-facing copy comes from ``tui/strings.py`` constants, never inline
  (I18N-01).
"""
