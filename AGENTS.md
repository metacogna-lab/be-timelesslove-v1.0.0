AGENTS.md
Python Backend — Agent Responsibilities and Behaviours
Purpose

This document defines how backend agents should operate in the Timeless Love system. The backend must reliably serve the React Vite frontend, enforce strict data models, provide well-documented APIs, and be ready for future integration with an intelligence system.

1. High-Level Goals

Agents must:

Support secure, scalable, and maintainable backend services.

Maintain strict data models consistent with business rules.

Provide clear and documented API contracts.

Be safe, observable, testable, and production-ready.

Produce outputs that support future intelligence/ML usage.

Agents should never produce ambiguous logic or undocumented behaviors.

2. Core Backend Responsibilities
Data Integrity

Agents must enforce:

Well-defined business entities (users, families, memories, roles).

Immutable audit information (who, when, what).

Validation at every interaction boundary.

Data must be predictable, consistent, and traceable.

API Provision

Agents must:

Expose clearly versioned API endpoints.

Return consistent and documented responses.

Validate all incoming requests.

Provide meaningful errors with clear codes and messages.

APIs must serve the needs of the frontend without assumptions about UI behavior.

Security and Access Control

Agents must:

Assign and enforce roles (Adult, Teen, Grandparent, Child, Pet).

Enforce strict access rules on every endpoint.

Protect sensitive data at rest and in transit.

Security is foundational; never bypass checks for convenience.

3. Agent Behaviour Patterns
Stateless Request Agents

Agents responding to frontend calls must:

Validate input strictly.

Not rely on hidden state.

Log key contextual information for tracing.

Return responses that the frontend can reliably interpret.

Background or Worker Agents

For non-interactive tasks (processing, notifications, cleanup, aggregation):

Jobs must be idempotent.

Must handle failures gracefully with retry/circuit logic.

Emit structured events on completion.

Events are essential for analytics and intelligence systems.

Event Emission

Agents must publish structured events whenever important changes occur:

User created/updated

Memory created/liked/commented

Family unit changes

Events must be consistent across the system and consumable by analytics, logging, and intelligence layers.

4. API Contract Discipline

Agents must adhere to:

Clearly defined API versioning.

Documented input and output schemas.

OpenAPI or equivalent API documentation.

Change control — breaking changes must be versioned.

APIs must never return undocumented fields or unpredictable structures.

5. Observability & Monitoring

Agents must emit:

Structured logs with context (request IDs, user IDs, timestamps).

Metrics on usage, error rates, latencies.

Alerts for unhealthy patterns.

Observability is required for debugging, reliability, and uptime.

6. Testing & Quality Assurance

Agent outputs must be validated by:

Unit tests for logic correctness.

Integration tests with API contracts.

Regression tests before deployment.

Agents must be safe to deploy and update through automated pipelines.

7. Integration Guidelines
Frontend (React Vite)

Agents must support:

CORS-ready endpoints.

JSON response formats that the frontend can interpret directly.

Error formats that enable precise UI messaging.

Future Intelligence System

Agents must produce:

Structured events about business activities.

Metadata and context fields useful for training and analytics.

No assumptions about how intelligence systems will use the data.

8. Agent Reminders

Agents should always prioritize:

Data integrity over convenience

Clarity in API contracts

Security and role enforcement

Observable, traceable behavior

Future readiness for intelligence/ML usage

Agents should never produce behavior without documentation, tests, and clear purpose.