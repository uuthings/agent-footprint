# Package caches, containers, test browsers, and Android

## Shared package caches

Package managers keep one cache for all projects, so downloads happen once. Agents must not clear these to "start clean"; that only forces downloads later. Clean them only when the user asks, preferably with the tool's own command:

| Tool | Cache location (macOS) | Tool's own cleanup |
| --- | --- | --- |
| npm | `~/.npm/_cacache` | `npm cache verify` (removes unreferenced data) |
| pnpm | store under `~/Library/pnpm/store` (see `pnpm store path`) | `pnpm store prune` |
| Yarn 1 | `~/Library/Caches/Yarn` | `yarn cache clean` |
| uv | `~/.cache/uv` | `uv cache prune` or `uv cache clean` |
| pip | `~/Library/Caches/pip` | `pip cache purge` |
| Gradle | `~/.gradle/caches` | stop daemons first; remove old versions only |
| Cargo, Go | `~/.cargo/registry`, `~/Library/Caches/go-build` | `cargo cache` (plugin), `go clean -cache` |
| Homebrew | `~/Library/Caches/Homebrew` | `brew cleanup` |
| SwiftPM | `~/Library/Caches/org.swift.swiftpm` | none; removing it re-downloads packages |

A cache that no current project uses (for example a package manager the user stopped using) can be a cleanup candidate. Check recent use before suggesting it.

**pnpm shares files.** pnpm fills project `node_modules` folders with clones or hard links of files in its store. Removing such a folder frees little while the store keeps the files, and size totals that add both count the same data twice.

## Project dependencies

`node_modules`, `.venv`, and similar folders belong to their project. Keep them for active projects. For projects without commits for several months, removing them is a reasonable suggestion: reinstalling costs a download of a few hundred megabytes to a gigabyte unless the shared cache still has the packages. Never remove them inside a running dev server's project.

## Containers

Docker keeps images, containers, volumes, and build cache inside its virtual disk. Build cache is recreatable: `docker builder prune` removes it. Images may be reused deliberately and volumes may hold data; treat both as user decisions. Docker Desktop may take a while to return freed space to macOS, so measure again later.

## Test browsers

Playwright (`~/Library/Caches/ms-playwright`) and Puppeteer (`~/.cache/puppeteer`) download full browsers. Keep the version the projects use; older versions are cleanup candidates. Removing the current one forces a reinstall before tests run.

## Android

The same principles apply: reuse one emulator (AVD) per API level instead of creating one per task, wipe app data rather than the whole emulator, and delete temporary AVDs with `avdmanager delete avd -n <name>`. System images are the counterpart of iOS runtimes; do not delete them unless the user asks. Gradle caches are shared.

## Leftovers of uninstalled apps

Dragging an app to the Trash leaves its data behind: caches, logs, and sometimes large downloads such as local AI models. An audit can point these out, but deciding what to remove belongs to the user, since some folders hold their own documents.
