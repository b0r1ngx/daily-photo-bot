# Product & Development Plans

This folder contains plans, logs, and technical debt tracking for the project.

## For AI Agents

You **must** consult the plans in this folder before beginning work on a new feature or making architectural changes. If a plan contradicts `AGENTS.md` or other `docs/` files, trust the plan *for the specific feature* or pause and ask a human for clarification.

## Directory Contents

1. **`agent-log.md`**: AI Agent observability log. Tracks reasoning and autonomous actions taken by agents. Append a new entry when you complete a complex task.
2. **`garbage-collection.md`**: Prioritized backlog of known technical debt. Check this before and after making changes.
3. **`v2-feedback-strategy.md`**: V2 user feedback collection strategy and analytics queries.

## Creating a Plan

If you (the Agent) are asked to implement a complex feature, your first step should be to draft a plan in `docs/plans/<feature-name>.md` and ask the human for approval before writing code. A good plan includes:
- **Objective:** What is the feature?
- **Scope:** What is in and out of scope?
- **Architecture Impact:** Which layers (`types`, `config`, `repo`, `service`, `runtime`) will be modified?
- **Testing Strategy:** How will this feature be verified?
