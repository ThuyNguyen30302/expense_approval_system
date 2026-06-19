# Product Guidelines

## Product Voice

Use clear, professional language. This is a backend portfolio project, so documentation should sound precise, practical, and engineering-focused.

Avoid marketing copy. Prefer concrete descriptions of behavior, rules, and tradeoffs.

## Documentation Style

- Write in concise Markdown.
- Use headings and short sections.
- Prefer explicit workflow rules over vague descriptions.
- Document assumptions when scope is not final.
- Keep product decisions traceable to requirements.

## API Experience Principles

- APIs should be predictable and boring in the best way.
- Error messages should help developers understand what went wrong without exposing internals.
- Response shapes should be consistent across endpoints.
- Authorization behavior should be strict and unsurprising.
- Workflow endpoints should make state transitions obvious.

## Domain Language

Use these terms consistently:

- Expense request
- Requester
- Manager approval
- Accountant review
- Payment tracking
- Audit log
- Status transition

Avoid mixing synonyms unless there is a specific reason. For example, do not alternate between "claim", "reimbursement", and "expense request" in API names.

## Portfolio Presentation Principles

- Make backend design decisions visible.
- Prefer simple, inspectable architecture over over-engineered patterns.
- Include tests that demonstrate real workflow behavior.
- Use project documents to show planning discipline before implementation.
- Keep future enhancements clearly separated from initial scope.

