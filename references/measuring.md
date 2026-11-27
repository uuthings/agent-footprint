# Measuring and deleting safely

## Measure what removal actually frees

- **Allocated, not logical size.** Use `du -sk` (allocated blocks). Sparse files report a logical length far above what they occupy.
- **Units.** Finder and System Settings show decimal gigabytes (1 GB = 10⁹ bytes); `du -h` and `df -h` show binary units. Say which one you report.
- **Clones and hard links.** APFS clones (simulator clones, copied build folders, pnpm installs) share blocks, and hard links share files. Removing one copy frees only what nothing else references. Adding the sizes of all copies counts shared data several times; one cleanup expected about 225 GB back and recovered about 180 GB, mostly for this reason.
- **Virtual mounts.** Some folders, such as `~/Library/Developer/CoreDevice`, are mounts for running devices. Exclude them; they occupy nothing.
- **Before and after.** The only reliable total is free space before and after, measured with `df` once the Trash is empty. Other sessions may write or delete at the same time; mention it when numbers disagree.

## Delete in the safest available way

- **Prefer the Trash.** Move files to the Trash (Finder, or `/usr/bin/trash` where macOS provides it) so the user can restore them until the Trash is emptied. Moving to the Trash frees nothing yet; tell the user.
- **Emptying can stall.** Finder stops when a file is in use, for example while System Settings computes storage or another app reads a file. Quit that app and empty again; files with the same name get a time suffix in the Trash.
- **Irreversible operations need explicit confirmation**, or hand the user the exact command: deleting simulators (`simctl delete`), `docker builder prune`, `pnpm store prune`, and emptying the Trash.
- **Platform tools for managed data.** Remove simulators with `simctl`, Docker data with `docker`, package caches with the tool's own command. Do not delete folders that a service manages.

## Check that nothing still uses it

Re-check right before deleting; a listing can be minutes old.

- Running state: booted devices, running apps, dev servers, build or test commands. Look for the folder path, device UDID, or device name in running processes.
- Activity windows (defaults): temporary leftovers created within 24 hours, agent session folders with a file changed within 3 days, build output, result bundles, and devices used within 7 days.
- Release material, Git data, and user documents stay, whatever their age.

## Present a cleanup list the user can judge

For each item, state what it is, which app, tool, or project it belongs to, its size, what happens after removal (rebuilt locally, downloaded again, or gone for good), and whether it can be restored. Group by owner and consequence. Raw file names alone are not a basis for the user's decision. Ask once for the whole list, then report what was removed, what was kept, and why.
