# Agent Footprint

Keep coding agents from filling your disk and re-downloading test resources.

[中文说明](README.zh-CN.md)

Coding agents repeat the same steps in every task: a new simulator for each QA run, a fresh build folder for each task, a timestamped test result for each run, another set of screenshots. Each is small; multiplied by hundreds of tasks, it is not. On one developer's 1 TB Mac, agents left about 100 GB of simulators, about 120 GB of per-task QA evidence, duplicated build folders, and 45 GB of their own session data. A cleanup freed more than 200 GB, and a few always-on rules kept it from coming back: afterwards no per-task simulators were left behind, and the number of build folders one agent used in a week dropped from 39 to 3.

This is not specific to one agent. Session logs from two different coding agents on that machine showed both creating dated QA simulators, per-task build folders, and timestamped result bundles. What differs between agents is their own data: some keep session logs without any retention limit.

## What it provides

- **Always-on rules** for `AGENTS.md` or `CLAUDE.md`: reuse fixed test devices and build folders, keep task output temporary, keep one copy of repeated output, leave shared caches and runtimes alone, and report leftovers.
- **Task guidance**, loaded when a task uses simulators, builds, test results, screenshots, or worktrees.
- **A read-only audit** ([scripts/audit.py](scripts/audit.py), macOS) listing simulators with last use and size, derived data, test result bundles, build folders, stale dependencies, worktrees, temporary-folder leftovers, agent session data, and shared caches.
- **A cleanup procedure** that classifies findings, explains the consequence of each removal, moves files to the Trash, and leaves irreversible steps to your confirmation.

Platform notes cover Apple simulators and Xcode, package caches, Docker, test browsers, Android emulators, and the data Codex and Claude Code keep.

## Install

1. Put this complete folder where your agent loads skills, for example `~/.codex/skills/agent-footprint` for Codex or `~/.claude/skills/agent-footprint` for Claude Code. Agents without skill support can read [SKILL.md](SKILL.md) directly.
2. Add the always-on rules. Skills load only when a task looks relevant, while leftovers pile up during ordinary tasks, so the rules belong in the instructions your agents read every session. Send [the setup prompt](prompts/install.md); the agent proposes the block filled in with your devices and build folders and waits for your approval before editing anything.

## Use

- **Audit and clean up:** send [the audit prompt](prompts/audit.md), or run `python3 scripts/audit.py` yourself (`--quick` skips the project scan, `--caches` also measures shared caches).
- **Day to day:** the always-on rules do most of the work; the skill adds detail when a task involves simulators, builds, or test evidence.

## Safety

- The audit only reads. It never deletes, moves, or changes anything and does not follow symbolic links.
- Cleanup moves files to the Trash after you confirm. Deleting simulators, pruning caches, and emptying the Trash are irreversible and need explicit confirmation.
- Runtimes, shared caches, release archives, Git data, and your documents stay unless you ask.
- The skill does not install itself or edit instruction files without your approval, and grants no permission to push or publish.

## Requirements

The audit script needs macOS, Python 3.9 or later, and Xcode for simulator details. The rules and guidance apply on any platform.

## License

[MIT](LICENSE)
