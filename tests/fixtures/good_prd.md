# Widget Login PRD

Owner: Jane Doe
Status: Draft
Date: 2026-08-14

## Problem

Users of the widgets dashboard cannot log in with their company identity provider. Support receives about forty tickets a week from people locked out after password resets, and the onboarding team spends two days per customer configuring local accounts by hand. Every one of those days is a day the customer is not using the product they paid for.

## Goals

- Let every customer sign in through their own identity provider.
- Cut login-related support tickets by half within one quarter.
- Remove the manual account setup step from onboarding.

## Non-goals

- Replacing the existing session store.
- Supporting identity providers that do not speak OIDC or SAML.

## Users

| Persona | Need |
|---|---|
| Admin | Configure the provider once and forget it |
| Employee | Sign in with the same button they use everywhere |

## Requirements

1. The login page shows a single "Continue with SSO" button when a provider is configured.
2. Admins can paste provider metadata and see a validation result within five seconds.
3. Existing local accounts are linked by verified email on first SSO login.
4. A failed provider login shows a message that names the provider and offers the local fallback.

## Success metrics

- Login tickets per week drop from forty to twenty.
- Ninety percent of new customers complete provider setup without a support call.

## Timeline

- September 2026: provider configuration screen.
- October 2026: SSO login and account linking.
- November 2026: rollout to all customers.

## Open questions

- Do we need to support multiple providers per customer?
- Who owns the provider metadata refresh job?

Licensed under CC BY 4.0.
