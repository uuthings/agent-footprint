# Apple simulators and Xcode builds

## Simulators

**Devices and runtimes are different things.** A runtime is the iOS (or watchOS, tvOS, visionOS) system image, about 7–8 GB each, downloaded once and shared by all devices of that version. A device is a local folder under `~/Library/Developer/CoreSimulator/Devices/<UDID>` holding that device's data and installed apps. Deleting a device never deletes its runtime.

**New devices cost bandwidth.** On first boot a device downloads system assets (language models, Siri, keyboard suggestions) into `data/private/var/MobileAsset/AssetsV2`. One audit measured about 2.3–2.5 GB per new iOS 26/27 device and about 0.1–1 GB per iOS 17/18 device. A rule of "create a device per task, delete it afterwards" therefore re-downloads those assets every task. Erasing a device has the same effect.

**Use fixed devices.**
- Keep one device per OS version the project supports. Prefer an existing default device; when none suits, create one once and give it a clear name, for example `xcrun simctl rename <UDID> "QA iOS 17.5"`.
- Record the mapping in the always-on rules so every agent uses the same devices.
- For a clean app state, uninstall and reinstall the app: `xcrun simctl uninstall <device> <bundle-id>`, then install the new build.
- Create a temporary device only when a fixed device cannot serve: parallel test runs, a screen size the fixed devices lack (for example store screenshots). Delete it when the task ends.
- Check whether tests or scripts select devices by name before renaming or removing devices; a test that only runs on a device whose name matches a pattern will silently skip or force a new device.

**Find last use and state.** `xcrun simctl list -j devices` reports each device's `state`, `lastUsedAt`, `dataPathSize`, and `isAvailable`. Each device's own `device.plist` holds the same record: `lastUsedAt` (older Xcode versions write `lastBootedAt`), `state` (1 is shut down, 3 is booted), `name`, and `runtime`. Do not use folder modification times; the simulator service touches device folders without anyone using them.

**Check before deleting.** A device is in use when it is not shut down, when a running process names its UDID or its name (for example `xcodebuild -destination 'platform=iOS Simulator,name=…'` or `simctl boot <device>`), or when it was used within the activity window (7 days by default). Re-read the record right before deleting; another session may have booted it.

**Delete only through `simctl`.**
- `xcrun simctl delete <UDID> [<UDID> ...]` removes devices synchronously and cannot be undone; there is no Trash. An unknown UDID fails with "Invalid device".
- `xcrun simctl delete unavailable` removes devices whose runtime is no longer installed.
- Never move or delete device folders directly; the simulator service keeps its own state and the device list breaks.
- Never delete runtimes unless the user asks. They are large downloads, and dropping a supported OS version breaks testing on it.

**Other device sets.** Xcode keeps separate sets for parallel testing (`~/Library/Developer/XCTestDevices`) and SwiftUI previews (`~/Library/Developer/Xcode/UserData/Previews/Simulator Devices`). Include them in audits; use the same rules.

**Clones share space.** Devices cloned from one source, and devices cloned with `simctl clone`, share disk blocks. Deleting one frees much less than its listed size. In one cleanup, 13 devices listed at 33.8 GB freed about 3 GB.

**Ignore `~/Library/Developer/CoreDevice`.** It contains a virtual file system mount for running devices. Tools such as `du` count it as tens of gigabytes that occupy nothing.

## Xcode builds

**One derived data folder per project.** Pass a fixed `-derivedDataPath` (for example `build/DerivedData`, ignored by Git) or use Xcode's default under `~/Library/Developer/Xcode/DerivedData`. Every new folder means a full rebuild and a fresh copy of Swift package checkouts. Two builds sharing one folder at the same time block each other, so a parallel task may use a second folder; it deletes that folder at the end.

**Test result bundles pile up.** Each `.xcresult` holds logs, screenshots, and coverage, often tens to hundreds of megabytes. Scripts that name bundles by timestamp grow without limit; one project accumulated 224 bundles and 18.5 GB. Write to a fixed path and delete the old bundle before the run (`xcodebuild` refuses to overwrite an existing result bundle), or keep only the latest few.

**Swift Package Manager.** `.build` beside `Package.swift` holds build products and dependency checkouts. Each worktree and each extra build folder holds another copy. The shared cache under `~/Library/Caches/org.swift.swiftpm` is reused across projects; leave it alone.

**Keep release material.** Xcode archives (`~/Library/Developer/Xcode/Archives`), exported apps, installers, notarized builds, and release folders are evidence for shipped versions. Do not delete them during cleanup, even when they sit inside a build folder; check a folder's contents before removing it as a whole.
