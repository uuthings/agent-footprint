---
name: agent-footprint
description: Keep coding-agent work from filling the disk and re-downloading test resources. Use when a task creates or reuses simulators or emulators, build or DerivedData folders, test result bundles, screenshots or other QA evidence, or session worktrees, and when auditing or cleaning up what agents left on a machine.
---

# Agent Footprint

Agents repeat the same work in every task, so whatever a task creates and leaves behind is multiplied: a new simulator, a fresh build folder, a timestamped test result, another screenshot set. On one developer machine, about 100 GB of simulators created during QA runs, about 120 GB of per-task QA evidence, duplicated build folders, and roughly 45 GB of agent session data filled a 1 TB disk; removing agent leftovers freed more than 200 GB. Recreating instead of reusing also costs bandwidth: a new iOS simulator downloads system assets on first boot, and a new build folder rebuilds and re-fetches dependencies.

Apply five principles:

1. **Reuse before you create.** Use the project's fixed test devices, build folder, and dependency caches. Create something new only when reuse is impossible, and plan its removal when you create it.
2. **Task output is temporary unless it is a deliverable.** Put scratch output in one ignored place and remove it when the task ends.
3. **Keep one copy of repeated output.** When each run writes a new result bundle, screenshot set, or report, keep the latest unless the user needs a comparison.
4. **Do not clean what others rely on.** Shared package caches, simulator runtimes, release archives, and user files stay unless the user explicitly asks.
5. **Leave a trail.** Report what you left behind, where, how large it is, and when it can go.

This skill grants no permission to delete, publish, push, or change global settings. Follow the user's authorization and the project's rules, and ask before anything irreversible.

## Always-on rules

Skills load only when a task looks relevant, but footprint grows during ordinary tasks. These habits hold reliably only when they are in instructions the agent reads every session.

- With the user's approval, add the block in [assets/AGENTS.block.md](assets/AGENTS.block.md) (or the [Chinese version](assets/AGENTS.block.zh-CN.md)) to the always-loaded instruction file: the global or project `AGENTS.md` for Codex and most agents, `CLAUDE.md` for Claude Code (which can import a shared `AGENTS.md`). When several agents work on one machine, keep one shared source instead of copies.
- Fill in the fixed devices and build folders actually in use. Keep credentials, account names, and personal paths out of shared or public rules.

## Before a task

- Read the project's rules for fixed devices, build folders, and temporary locations.
- **Simulators and emulators:** list existing devices and use the fixed device for the OS version the task needs. For a clean state, uninstall and reinstall the app instead of erasing or creating a device.
- **Builds:** use the project's standard build or DerivedData folder. A parallel task that would collide with another build may use its own folder; note it for removal.
- **Dependencies:** use the shared caches as they are. Do not clear them to "start clean".

## During a task

- Write screenshots, recordings, logs, and result bundles to the project's ignored temporary folder or the agent's own scratch area, one folder per task.
- Prefer a fixed output path that each run replaces over timestamped copies.
- Keep evidence that matters in small form: a report, a summary, the few screenshots a reviewer needs.

## At the end of a task

1. Remove what you created and no longer need: temporary devices (through the platform tool, never by deleting their folders), temporary build folders, and evidence that is not a deliverable.
2. Move evidence the user wants to keep (release, store submission, design review) to the location the user designated.
3. Report anything large that remains: what it is, its path and size, why it stays, and when it can be removed.

## Audit and cleanup on request

1. Run `python3 scripts/audit.py` from this skill's folder. It is read-only and targets macOS. Pass `--roots <folder> [<folder> ...]` for project folders (default `~/Developer`), `--quick` to skip the project scan, or `--caches` to also measure shared caches (slow). It lists simulators with last use and size, Xcode derived data, project build output and result bundles, temporary-folder leftovers, agent data, and shared caches.
2. Classify each item:
   - **In use:** booted or running devices, anything inside its activity window, anything a running process refers to.
   - **Safe to remove:** recreatable locally without downloads and not in use, such as old result bundles, stale build folders, temporary devices, and leftovers of uninstalled tools.
   - **Needs a decision:** removal costs a download, a long rebuild, or history, such as runtimes, shared caches, agent sessions, and evidence that reports may still link to.
3. Present the list by what each item is, which tool or project owns it, its size, and the consequence of removing it. Do not ask the user to judge raw file names.
4. After confirmation, move files to the Trash. Delete devices only through the platform tool; that is irreversible, so confirm it separately or give the user the exact command. Never empty the Trash for the user.
5. Measure free space again after the Trash is emptied and explain differences: clones and hard links make listed sizes larger than what is freed, and other sessions may write at the same time.

Default activity windows, unless the user's rules say otherwise: temporary-folder leftovers created within the last 24 hours, agent session folders with any file changed within 3 days, and build output, test results, and devices used within 7 days count as in use.

## Platform guides

Read only what the task involves:

- [Apple simulators and Xcode builds](references/apple.md)
- [Package caches, containers, test browsers, and Android](references/packages.md)
- [Agent data: Codex, Claude Code, worktrees, temporary folders](references/agent-data.md)
- [Measuring and deleting safely](references/measuring.md)
