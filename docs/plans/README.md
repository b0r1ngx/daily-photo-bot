# Product & Development Plans

This folder contains the roadmap, current active tasks, and architectural decisions for the project.

## For AI Agents

You **must** consult the plans in this folder before beginning work on a new feature or making architectural changes. If a plan contradicts `AGENTS.md` or other `docs/` files, trust the plan *for the specific feature* or pause and ask a human for clarification.

## Directory Structure

1. **`roadmap.md`**: High-level project goals and upcoming milestones.
2. **`active-tasks/`**: Detailed specs for currently prioritized features.
3. **`arch-decisions/`** (ADRs): Architectural Decision Records. If we decide to use a specific technology or pattern, the "Why" and "How" are documented here.
4. **`garbage-collection.md`**: A backlog of known technical debt and "AI slop" that should be cleaned up proactively.

## Creating a Plan

If you (the Agent) are asked to implement a complex feature, your first step should be to draft a plan in `docs/plans/active-tasks/<feature-name>.md` and ask the human for approval before writing code. A good plan includes:
- **Objective:** What is the feature?
- **Scope:** What is in and out of scope?
- **Architecture Impact:** Which layers (`Types`, `Service`, `Repo`, `UI`) will be modified?
- **Testing Strategy:** How will this feature be verified?