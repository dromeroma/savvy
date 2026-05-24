"""Onboarding module: signup-wizard catalogs (business types, denominations, zones).

Public read-only endpoints that the signup wizard calls before the user has
an account. Custom-denomination creation lives inline in `/auth/register`
because the denomination is owned by the org being created in the same flow.
"""
