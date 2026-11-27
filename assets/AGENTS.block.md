## Test resources and agent leftovers (save disk and bandwidth)

- Simulators and emulators: reuse one fixed test device per OS version ({{fixed devices, for example "QA iOS 17.5" for iOS 17.5 and the default iPhone for the latest iOS}}); do not create one per task. For a clean state, uninstall and reinstall the app instead of erasing the device, which downloads system assets again. Delete any device you had to create (parallel runs, special screen sizes) when the task ends. Never delete simulator runtimes or system images.
- Builds: each project uses one fixed build or DerivedData folder ({{for example build/DerivedData}}); do not create one per task. A parallel task that needs its own folder deletes it at the end. Do not clean shared caches (SwiftPM, npm, pnpm, uv, Gradle, Docker and similar) unless the user asks.
- Evidence: screenshots, recordings, and test result bundles go in the project's ignored temporary folder and are deleted when the task ends. Move what must be kept (release, store submission, design review) to {{the product archive folder}}. When each run writes a new copy, keep only the latest.
- End of task: list anything large you left behind and where it is.
