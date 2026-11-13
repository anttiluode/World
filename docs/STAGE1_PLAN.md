# World stage 1 — implementation plan

Goal: an inspectable, persistent landscape whose future changes when sound or material changes. Stop before biological/crystal growth and Moon transport.

The user supplied the design and authorized implementation and GitHub Pages publication. Work in this fresh clone of the otherwise empty World repository. One self-contained `index.html`; no libraries, network assets, model downloads or build step. Use WebGL2 RGBA32F ping-pong targets. Fail explicitly if float render targets are unavailable.

## Choices and boundaries

- A finite 2D material grid displayed as a navigable 3D landscape. This makes the first causal loop affordable and measurable. It cannot yet represent caves or volumetric crystals.
- Seed pass supplies bedrock, hardness and resonant frequency. It runs only on reset; the seed audit compares structured vs flat initialization, not a fake animated seed layer.
- Force pass reads terrain and compaction, updates complex damped oscillators by exact rotation, and derives bounded transport velocities.
- Transport flux + deposition passes conservatively move mobile sediment among four neighbors, exchange mobile and resting material, and retain compaction/exposure history. No per-frame random decoration.
- Render reads the stored fields. Temporary surface illumination and a constant environment are explicitly conventional, not Moon transport. No stars, decorative particles, analytic crystal shapes or animated noise.
- Microphone and decoded song input, deterministic built-in weather, pause/reset, seed entry, quality, camera controls, material intervention, band mute, layer freeze/kill, optional state-driven sound.
- Fixed 32 Hz simulation, organ at 8 Hz. Determinism is scoped to identical features/interventions, resolution and browser/GPU; raw live microphone capture is not repeatable. Expose recording/replay of the feature tape.

## Tasks

1. Write failing Node tests for the embedded pure core: ring learns periodic input, mismatch rises at a break, silent input stays silent, deterministic feature schedule, and conservative nonnegative sediment transport. Implement the core and run `node --test tests/core.test.cjs`.
2. Build the GPU fields and renderer, then the audio/control surface. Browser checks must exercise actual shader compilation, layer audit, intervention and error display. Pausing must preserve state; reset must clear history.
3. Implement on-page measured checks on the actual GPU: replay, alternate forcing, mass conservation, freeze/kill, intervention propagation, and matched visible state with different hidden compaction. The last is a stage-1 transport-memory test, not the requested future-growth test.
4. Inspect desktop and narrow layout, run complete checks, review source, record results and limitations in README. Add Pages workflow; commit/push; check deployment. Stop here.

## Review focus

Microphone denied/unavailable; file decoding failure/oversized files; hidden-tab/audio clock drift; context loss/unsupported float buffers; slow GPU and varying display resolution. Report limits rather than silently substituting a painted demo.
