"""Savvy Platform module.

Exposes platform-level admin capabilities for super admins:
- platform roles (RBAC above organizations)
- subscription plans, features, and per-org subscriptions
- organization directory (read/edit all orgs without entering them)
- platform users (grant/revoke platform roles)
- audit log of all platform actions

Mounted under `/api/v1/platform/*`. Every endpoint requires a user with
an active `super_admin` (or equivalent) platform role. Super admins do
NOT impersonate or enter organizations — they only parameterize from
their own account.
"""
