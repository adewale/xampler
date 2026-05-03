# Xampler Docs

Long-term docs are grouped by purpose. Older planning snapshots live in [`archive/`](archive/).

## API design

- [`api/library-surface.md`](api/library-surface.md) — importable library modules and stability levels.
- [`api/reference.md`](api/reference.md) — concise API reference and copyable imports.
- [`api/testability.md`](api/testability.md) — how to write red-green-refactor tests with fake bindings and `Demo*` clients.
- [`api/pipeline-vocabulary.md`](api/pipeline-vocabulary.md) — composition vocabulary.
- [`api/operations.md`](api/operations.md) — progress, checkpoint, retry, DLQ, workflow status, and observability patterns.
- [`api/unified-api-surface.md`](api/unified-api-surface.md) — the shared Xampler API shape.
- [`api/primitives-api-surface.md`](api/primitives-api-surface.md) — primitive coverage and Pythonic API matrix.
- [`api/primitive-test-realism.md`](api/primitive-test-realism.md) — verification honesty matrix.
- [`api/native-python-workers-comparison.md`](api/native-python-workers-comparison.md) — Xampler wrappers vs native Python Workers bindings.
- [`api/pythonic-rubric.md`](api/pythonic-rubric.md) — scoring rubric.

## Runtime and platform grounding

- [`runtime/python-workers-runtime-guidance.md`](runtime/python-workers-runtime-guidance.md)
- [`runtime/pythonic-tooling.md`](runtime/pythonic-tooling.md)
- [`runtime/cloudflare-doc-links.md`](runtime/cloudflare-doc-links.md)
- [`runtime/credentials.md`](runtime/credentials.md)
- [`runtime/remote-verification.md`](runtime/remote-verification.md)
- [`runtime/local-path-development.md`](runtime/local-path-development.md)
- [`runtime/cloudflare-best-practices-alignment.md`](runtime/cloudflare-best-practices-alignment.md)

## Data and streaming

- [`data/datasets.md`](data/datasets.md)
- [`data/streaming-api.md`](data/streaming-api.md)
- [`data/s3-python-library-research.md`](data/s3-python-library-research.md)

## Project direction

These are mostly maintainer-facing. New users should start with the API/runtime/data docs above.

- [`project/example-categories.md`](project/example-categories.md) — user-facing categorization by realism and product family.
- [`project/project-structure-and-naming.md`](project/project-structure-and-naming.md) — folder and naming conventions.
- [`project/complex-example-backlog.md`](project/complex-example-backlog.md) — future app ideas and low-cost abstraction research.

## Maintainer notes and audits

These docs explain why the repo looks the way it does, but they are not the main user journey.

- [`project/competitive-positioning.md`](project/competitive-positioning.md)
- [`project/complex-example-backlog.md`](project/complex-example-backlog.md)
- [`project/duplication-audit.md`](project/duplication-audit.md)
- [`project/experience-assessment.md`](project/experience-assessment.md)
- [`project/unfinished-work.md`](project/unfinished-work.md)
- [`project/lessons-learned.md`](project/lessons-learned.md)
