# Conductor Workflow

## Workflow Philosophy

This project follows a Conductor-inspired context-driven workflow:

```text
Context -> Spec & Plan -> Implement -> Verify -> Review -> Sync Context
```

No implementation work should start until the relevant context, feature spec, and implementation plan exist.

## Project Context Files

The project context lives in:

- `product-requirements.md`
- `backend-architecture.md`
- `coding-rules.md`
- `api-design.md`
- `conductor/product.md`
- `conductor/product-guidelines.md`
- `conductor/tech-stack.md`
- `conductor/workflow.md`
- `conductor/tracks.md`
- `conductor/code_styleguides/`

These files are the source of truth for agent-assisted work.

## Track Lifecycle

Each feature, bug fix, refactor, or documentation task should be represented as a track.

Track directory pattern:

```text
conductor/tracks/<track-id>/
  metadata.json
  spec.md
  plan.md
```

## Track Statuses

- `proposed`: Track exists but is not ready.
- `planned`: Spec and plan are ready for review.
- `approved`: User approved the plan.
- `in_progress`: Implementation has started.
- `blocked`: Work cannot continue without input or external change.
- `implemented`: Code changes are complete.
- `verified`: Tests and manual checks passed.
- `reviewed`: Final review completed.
- `done`: Track is complete and context is synchronized.

## Required Track Artifacts

### metadata.json

Stores machine-readable track metadata:

- track ID
- title
- type
- status
- created date
- owner
- related docs

### spec.md

Defines:

- problem statement
- goals
- non-goals
- users affected
- functional requirements
- API behavior
- data model implications
- authorization rules
- acceptance criteria

### plan.md

Defines:

- phases
- tasks
- test strategy
- verification checklist
- rollback notes if relevant

Tasks should use checkbox syntax:

```markdown
- [ ] Write service tests for manager approval.
- [ ] Implement manager approval service method.
- [ ] Add API endpoint.
- [ ] Run test suite.
```

## Implementation Rules

- Read relevant context files before coding.
- Update the active track plan as tasks are completed.
- Follow the coding rules in `coding-rules.md`.
- Add or update tests alongside implementation.
- Add migrations with SQLAlchemy model changes.
- Do not silently expand scope beyond the approved track.

## Verification Rules

Each implementation phase should include verification:

- Run relevant tests.
- Confirm API behavior against `api-design.md`.
- Confirm authorization behavior.
- Confirm status transitions and audit entries.
- Update the track plan with verification results.

## Review Rules

Before a track is marked done:

- Compare implementation against the spec.
- Check coding rules.
- Check API consistency.
- Check security and authorization.
- Check missing tests.
- Record any follow-up work in `conductor/tracks.md`.

## Context Sync Rules

At the end of meaningful work:

- Update project docs if behavior changed.
- Update `conductor/tracks.md`.
- Keep specs and plans aligned with actual implementation.
- Record deferred work as a new proposed track.

