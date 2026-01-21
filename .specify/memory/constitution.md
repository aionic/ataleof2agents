<!--
=============================================================================
SYNC IMPACT REPORT
=============================================================================
Version: 0.0.0 → 1.0.0
Change Type: MAJOR (Initial constitution for POC project)

Modified Principles:
- NEW: Principle I - POC-First Simplicity
- NEW: Principle II - Documentation-Driven Development
- NEW: Principle III - Rapid Validation

Added Sections:
- Core Principles (3 principles)
- POC Scope & Constraints
- Governance

Templates Requiring Updates:
✅ plan-template.md - Constitution Check section is generic
✅ spec-template.md - Requirements align with POC approach
✅ tasks-template.md - Task organization supports POC principles
✅ All agent files - Generic references maintained

Follow-up Actions: None required
=============================================================================
-->

# Agent Demo POC Constitution

## Core Principles

### I. POC-First Simplicity

**Principle**: This is a proof-of-concept solution designed to showcase technology capabilities, NOT to be enterprise-ready or feature-complete. Every implementation decision must prioritize demonstrating core value over production readiness.

**Rules**:

- MUST focus on essential features that demonstrate the technology's value proposition
- MUST avoid enterprise patterns (complex abstractions, extensive error handling, production-grade security) unless directly relevant to the POC
- MUST document what is intentionally simplified or omitted for POC purposes
- SHOULD prefer inline implementations over architectural patterns when appropriate for demonstration
- SHOULD use in-memory or file-based storage over databases unless data persistence is core to the demonstration

**Rationale**: POC projects must move quickly to validate concepts. Over-engineering at this stage wastes time and obscures the core value being demonstrated. Production concerns can be addressed in later phases if the POC proves successful.

### II. Documentation-Driven Development

**Principle**: Before writing code or making technical decisions, MUST consult authoritative documentation sources to ensure best practices and avoid common pitfalls.

**Rules**:

- MUST check Microsoft Learn documentation for any Azure or Microsoft technology decisions
- MUST check Context7 documentation for any third-party libraries, frameworks, or tools
- MUST document the source of technical decisions in research.md or plan.md
- MUST include links to relevant documentation in code comments for non-obvious implementations
- SHOULD capture key learnings and gotchas discovered during development

**Rationale**: POCs often involve unfamiliar technologies. Consulting authoritative sources prevents time-wasting mistakes, ensures we follow recommended patterns, and documents learning for future reference. This is especially critical in time-constrained POC environments where there's no time to recover from poor foundational choices.

### III. Rapid Validation

**Principle**: Features must be implementable and testable quickly. Testing is OPTIONAL and should be applied only where it accelerates validation or prevents critical failures.

**Rules**:

- MUST prioritize manual testing and visual verification for POC features
- SHOULD write automated tests for complex logic that would be time-consuming to manually verify repeatedly
- SHOULD write tests for integrations with external services where failures are costly or slow to detect manually
- MAY skip tests for simple UI components, straightforward CRUD operations, or one-time demo scripts
- MUST include acceptance criteria in specs that can be manually verified
- MUST document how to manually test each user story

**Rationale**: Test-driven development is valuable for production systems but can slow POC velocity unnecessarily. POCs are exploratory by nature—requirements change frequently, and code may be discarded. Manual testing is often faster and more appropriate. Strategic testing should focus on preventing time waste, not achieving coverage goals.

## POC Scope & Constraints

**Purpose**: Define what is explicitly IN and OUT of scope for this POC.

**In Scope**:

- Demonstrating core technology capabilities and value proposition
- Basic functionality sufficient to validate the approach
- Documentation of technical decisions and learnings
- Manual testing and validation of key scenarios

**Out of Scope** (Intentionally Deferred):

- Production-grade error handling and edge cases
- Comprehensive input validation
- Security hardening (authentication, authorization, encryption beyond basic demos)
- Performance optimization and scalability
- Comprehensive automated test coverage
- CI/CD pipelines and deployment automation
- Multi-environment configuration
- Monitoring, logging, and observability beyond basic debugging
- Code refactoring for maintainability
- Internationalization and accessibility

**Technology Constraints**:

- SHOULD prefer technologies with strong Microsoft Learn or Context7 documentation
- SHOULD prefer managed services over self-hosted when using Azure
- SHOULD use latest stable versions unless POC specifically requires a particular version

## Governance

**Amendment Process**:

- Constitution changes require explicit `/speckit.constitution` command invocation
- Version increment follows semantic versioning (MAJOR.MINOR.PATCH)
- All amendments must be documented in the Sync Impact Report at the top of this file

**Compliance**:

- Constitution principles take precedence over external best practices that conflict with POC goals
- Complexity violations (production patterns in POC code) must be justified in plan.md Complexity Tracking section
- All specifications and plans must pass Constitution Check before implementation begins

**Version Control**:

- MAJOR: Fundamental change in POC approach or removal of core principles
- MINOR: Addition of new principles or substantial expansion of existing ones
- PATCH: Clarifications, wording improvements, or minor updates that don't change intent

**Version**: 1.0.0 | **Ratified**: 2026-01-20 | **Last Amended**: 2026-01-20
