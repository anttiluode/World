# Stage 1 build ledger

- Source code inspected before implementation; see SOURCE_NOTES.md. Fresh World clone initially contained only LICENSE.
- User's staged specification is the design authority. Stage 1 stops at layers 1–3.
- Ruling: fixed 2D material grid with 3D height-field view — bounds GPU cost and permits conservative tests; cannot represent volumetric crystals or caves.
- Ruling: conventional material-derived renderer for this checkpoint — allows inspection before stage 5; does not satisfy full Moon-transport/pixel-residue ambition.
- Core tests first failed because core did not exist; implemented and passed. Spectrum/recording tests and decoded-audio score test were added red then passed.
- Browser fallback correctly reported unavailable WebGL/float targets. No alternate painted demo or browser-performance claim substituted.
- EGL harness reads production shader strings directly, translates version/precision only, and reuses the real JS organ-generated input. Final 13 checks pass, including outside-brush propagation and a 192² stress run.
- Fresh independent source review identified five issues: song feature-name shadowing, mutable replay controls, visible compaction in hidden-history test, audio left active after context loss, and audits measuring weaker claims. All five addressed. Numerical audit repeated after shader/audit changes.
- Remaining verification limits: working-browser UI/audio/WebGL, narrow-screen interaction and RTX 3060 FPS. No growth or light stage attempted.
