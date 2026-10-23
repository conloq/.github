# Repository guide

## Role

This repository contains Conloq organization profile content, shared GitHub templates/workflows, and automation. It is not part of the Mash HTTP runtime. The `mash-project-notifications.yml` workflow is an automation that reads/writes GitHub operational state; inspect its code and permissions before changing it.

## Global project context

Start with [`PROJECT_CONTEXT.md`](./PROJECT_CONTEXT.md) for the portable Conloq/Mash registry, source hierarchy, and cross-repo boundaries. For live Status, Sprint, PRs, checks, protections, or rulesets, query GitHub; do not copy snapshots into static docs.

## Local sources and boundaries

- `profile/README.md`: public organization/project presentation and contribution guidance.
- `.github/`: shared PR template and reusable workflows.
- `automation/` and `tests/`: notifier implementation and its checks; follow `automation/README.md` for actual commands.
- Project #2 is the canonical board. Automation that reads or updates project fields must use the configured live Project ID and preserve the writer/permission boundaries documented by its procedure.
- Do not treat a shared workflow or profile description as proof that a caller repository currently runs it. Inspect the caller workflow and live Actions run.

## Changes and validation

Before changing a workflow, inspect its callers, triggers, permissions, and current GitHub runs. Before changing a template or policy statement, compare it with current GitHub enforcement and the canonical decision in `conloq/mash#66`.

Run the repository's documented automation tests only when the corresponding automation changes. Do not invent commands, alter Project/Issue state as a side effect of documentation work, or add harness-specific project facts here.

## Contribution

Use a branch and Pull Request; never commit directly to `main`. Human approvals are not a required policy gate. Query current branch protection, organization rulesets, checks, conversation-resolution requirements, and actor permissions before claiming a merge is unblocked.