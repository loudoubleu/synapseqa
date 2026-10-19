# 3. Use pydantic models for API contract checks

## Status

Accepted

## Context

API tests need to confirm not just that an endpoint returns the expected status code, but that its
response body actually has the shape the rest of the framework assumes (field names, types,
optionality). Without that check, a backend change that silently renames or drops a field would only
surface later as a confusing `KeyError` or `AttributeError` deep inside a test or page object, far from
the actual response that changed.

## Decision

Model every API response the framework depends on as a pydantic v2 model (e.g. `Employee` and
`EmployeeListResponse` in `src/framework/api/models/employee.py`, `BookingIdSummary` in
`src/framework/api/models/booking.py`), and validate the raw JSON against that model inside the API
client (`EmployeeClient.list()`, `BookingClient.list_booking_ids()`) before returning it to a test.
Fields are typed explicitly (`emp_number: int`, `termination_id: int | None`, …) with `Field(alias=...)`
mapping each API's camelCase keys onto idiomatic snake_case attributes.

pydantic was already a required dependency for `Settings` (`pydantic-settings`), so this reuses a
library the project needs anyway rather than adding a second schema/validation dependency
(e.g. `jsonschema` or `marshmallow`).

## Consequences

- **Gains:** a response shape mismatch fails fast and loudly, as a `ValidationError` that names the
  exact field and the exact value that didn't fit — not a vague downstream `KeyError`. Tests get typed,
  autocompleted objects (`employees.data[0].emp_number`) instead of raw `dict`s. The same models double
  as living documentation of each endpoint's contract.
- **Costs:** every field the framework cares about needs a model update when the real API's shape
  changes (confirmed against the running app first — see `CLAUDE.md` §7 — never assumed). Fields the
  framework doesn't use yet are simply omitted from the model rather than modeled speculatively.
