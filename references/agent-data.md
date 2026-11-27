# Agent data: Codex, Claude Code, worktrees, temporary folders

Agents also keep their own records. These are history, not caches: deleting them can break resuming a conversation. Report sizes and suggest archiving; delete only with the user's consent.

## Codex

- Sessions: `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`; older files are compressed to `.jsonl.zst`. Archived sessions: `~/.codex/archived_sessions`.
- Screenshots and generated prototypes: `~/.codex/visualizations/YYYY/MM`.
- Worktrees created by the app: `~/.codex/worktrees`.
- Growth: on one machine sessions grew by about 1 GB a day during heavy use, and sessions plus screenshots reached about 45 GB in three months. Public issue reports describe hundreds of gigabytes. As of late 2026, public issues report no built-in retention limit; check the current documentation.
- A session keeps appending to the folder of the day it started, so a long-running session keeps an old month active. Treat a folder as active while any file in it changed within 3 days.
- Prefer archiving whole quiet months to external storage over deleting them. Verify the copy before removing the original, and tell the user that those sessions can no longer be resumed from this machine.

## Claude Code

- Transcripts: `~/.claude/projects/<project-path>/<session-id>.jsonl`, plus files for subagents.
- Retention: `cleanupPeriodDays` in `~/.claude/settings.json` (default 30 days) removes old transcripts when Claude Code starts. Public issue reports describe inconsistent behavior, and setting it to 0 has disabled saving transcripts in some versions. On one audited machine, transcripts older than 30 days were still present, so check the actual dates instead of assuming cleanup ran.
- Edit checkpoints: `~/.claude/file-history`.
- Worktrees created by the desktop app: `<repository>/.claude/worktrees/<name>`.
- Per-session scratch folders and task output live under the system temporary folder (`/private/tmp/claude-<uid>/`) and disappear at restart. A build placed there is a per-session copy that rebuilds from scratch each time; delete large ones at the end of the task.
- The desktop app keeps a virtual machine image for its sandboxed features (`~/Library/Application Support/Claude/vm_bundles`, about 10 GB). It is installed once, not per task.

## Worktrees from any agent

Each worktree is a full checkout with its own build folders and dependencies. When its work is merged or abandoned, offer to remove it: `git worktree list`, then `git worktree remove <path>` (it refuses a worktree with uncommitted changes; report those instead of forcing), then `git worktree prune`.

## Temporary folders

- The per-user temporary folder (`$TMPDIR`, also `getconf DARWIN_USER_TEMP_DIR`) collects output from test tools and scripts. macOS does not reliably clean it for you.
- Test tools that keep screenshots or fixtures there should keep only the latest run. Lock the folder of a running check so a finishing run never removes another run's folder.
- Leftovers created more than 24 hours ago (check the creation time, `stat -f %B`) and not used by a running process can be removed. Newer items stay.
