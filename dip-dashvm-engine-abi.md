<pre>
  DIP: Unassigned (dip-dashvm-engine-abi)
  Title: Deterministic Wasm engine, named bundles and ABI
  Chain: Platform
  Layer: Consensus
  Author(s): To be confirmed
  Comments-Summary: Initial draft; discussion and implementation tracking linked below.
  Status: Draft
  Type: Standard
  Created: 2026-09-11
  License: MIT License
</pre>

These are draft proposals for review, not assigned/accepted DIPs or implemented features. Confirmed design decisions are preserved. Sections explicitly marked proposed and the [shared allocation register](dip-dashvm/allocations.md) contain engineering proposals requiring review and measurement. Exact wire identifiers, the production engine profile, limits and prices remain open. DVM aliases identify this proposal series and are not official DIP numbers. Final authorship and official numbering remain subject to editorial review.

[Parent plan](https://github.com/dashpay/platform/issues/4626) · [Implementation tracking](https://github.com/dashpay/platform/issues/4676) · [Shared allocation register](dip-dashvm/allocations.md)

## Abstract

Specify the Wasmtime/Cranelift execution profile, deterministic validation and instrumentation, immutable multi-module bundles, host ABI, metering and local compiled-artifact lifecycle. Canonical Wasm is consensus state; native compiled artifacts are reproducible local acceleration.

## Motivation

Long-lived contracts need fast execution without depending on a node's CPU, cache state or compiler defaults. Several named modules per version allow large Rust contracts to share unchanged components across versions. This requires explicit linking and shared resource accounting rather than treating each module as an independent allowance.

## Specification

### Engine and validation boundary

Use upstream Wasmtime with Cranelift. Pin its exact release/commit, transitive lockfile, compiler options, target CPU feature policy, memory guards, validation transform and metering generation in the profile. Winch/interpreters may be diagnostic comparison tools; they are not automatic production fallbacks. `rs-dashvm-validation` validates original Wasm, instruments required logical stack/resource checks, validates transformed output and returns metadata. It cannot compile native code or execute initialization. `rs-dashvm` compiles, instantiates and executes the resulting module. Stateful authority/capability validation stays above both.

Scalar f32/f64 are allowed with Cranelift NaN canonicalization. Test NaN reinterpretation, signed zero, subnormals, conversions and trapping instructions on x86_64 and aarch64. NaN canonicalization alone is not a determinism proof. Proposed first feature set excludes threads/shared memory, memory64, SIMD/relaxed SIMD and ambient WASI I/O; every admitted opcode/import is listed and priced before activation. Features are not inherited from changing Wasmtime defaults.

### Immutable bundle schema

`BundleManifest` binds codec/ABI/profile IDs, ordered `Module{name, canonical_hash, interface}`, exact internal bindings, stable contract-wide method/type/index IDs, public routes, capabilities, initialization metadata and aggregate limits. Hash a domain-separated canonical encoding. Names are bounded and canonically encoded; duplicate names/IDs/routes and ambiguous encodings reject the bundle. Hash algorithm, widths and tags are explicit allocation entries, not silently chosen here.

Each binding names a module/export/signature in this exact manifest. Public calls resolve a stable method ID to one module/export. Internal bindings never float to a different contract version. The proposed initial linker requires an acyclic dependency graph, separate instance memories/tables and host-mediated typed internal calls. Reject missing imports, conflicting signatures, cycles and unauthorized shared-memory/global access. No per-function on-chain code archive is created.

Only the selected entry module's dependency closure is instantiated, in deterministic dependency order with canonical-name tie breaking. Proposed initialization permits bounded memory/global/table setup but no external state writes, transfers or nested contract calls before entry dispatch. Reject undeclared side-effectful starts; transformed and toolchain-produced start sections require explicit validation rather than incidental execution. Define data/element segment limits and initialization copy costs. Shared closure initialization runs once per invocation; no instance state survives to the next outer invocation.

### ABI and guest memory

Use versioned typed requests/results defined by `rs-dashvm-abi`. A host function receives a guest-memory range, decodes bounded canonical data, checks the invoked capability and returns a bounded encoded result through an explicitly owned response buffer/handle. Exact import/export names, function signatures and handle layout are allocated in the shared register. Semantic operation families include native document/query/collection/asset operations, nested calls, schedule/receipt policy operations, and gated ACL/randomness requests.

Check pointer plus length for overflow and memory containment before access; cap nesting, collection counts and decoded expansion independently of stored byte size. Do not expose host pointers, OS resources or raw GroveDB paths. Handles are scoped to one invocation/authority context, cannot be forged into another capability, and expire at its end. Copying across separate module memories is metered. Input data is copied or safely borrowed only for a documented lifetime; host reentry cannot retain guest slices across memory growth. Host error variants have fixed bounded encodings.

### Shared resources and metering

An outer invocation owns one computation counter, logical stack/activation counter, memory reservation, host-call count, read/copy budget, proposed-operation budget and receipt bound. Local recursion, internal modules, predicates and cross-contract calls consume this same scope. A module call cannot reset a limit. Logical stack accounting includes locals and operand slots; native-stack headroom must be independently demonstrated so architecture-specific native exhaustion cannot precede the specified logical trap.

Meter admitted Wasm semantics with a versioned schedule whose result is independent of compiler optimization and local cache state. Wasmtime raw fuel may implement only the portion proven equivalent to that schedule. If raw fuel affects consensus fees or limits, exact trapped-case parity is mandatory; otherwise it is diagnostic. Memory growth uses deterministic logical reservation and bounds, with metered initialization/copies. Local allocation failure within admitted resources is a node fault, not a different guest-visible `memory.grow` result. Meter native work exactly once as DVM-07 defines.

### Compiled cache and replay

Cache keys bind canonical hash, prepared hash, bundle binding digest where relevant, ABI/preparation/metering versions, exact engine build/profile, target architecture and CPU/guard configuration. Validate native artifact integrity and origin before unsafe deserialization; network-supplied native code is never trusted as a compiled contract. Store artifacts atomically, discard incompatible/corrupt entries and rebuild from canonical code. Instances and authority state are never shared between invocations.

Maintain runnable supported-version modules, pending compilation and historical replay as distinct sets. Shared artifacts are retained while another executable version still needs them; eviction does not delete canonical state or make execution charge more. Readiness requires all modules compiled and all bindings checked. A node missing artifacts must prepare before validating/executing the affected work; it cannot manufacture a paid contract error. Retain historical profiles for historical replay and plan protocol-upgrade preparation before activation.

## Backward compatibility and deployment

Engine behavior changes use normal protocol upgrades; historical descriptors remain available. Old supported code uses its specified execution compatibility behavior plus current storage/authorization rules. A profile upgrade must state how existing accepted code is transformed/recompiled; it cannot silently invalidate it or freeze contracts. Canonical blobs/manifests stay permanent after cancellation, retirement and wipe.

## Security considerations

Compilation complexity, instrumented growth and aggregate bundle size need independent bounds. Native compilation is attackable even when guest computation is metered. Nodes pay compilation; bounded protocol validation/storage/readiness charges and admission limits must bound deployment spam. An 80% readiness statement proves availability work, not compiler correctness. Keep upstream advisory monitoring and minimal temporary patches with upstream fixes as the maintenance strategy.

## Test vectors and acceptance

Include integer edges, NaN/trap/stack/memory cases, giant functions/types, invalid pointers and handles, cyclic/missing imports, deterministic initialization, two versions reusing one blob, shared-resource exhaustion across modules, cold/warm/recovered cache, corrupted artifacts and historical replay. Compare results, fee/limit counters, trap classes, proposed operations and final roots on both architectures. Reproduce relevant advisories with an affected configuration where feasible; an unaffected default run is not a regression test.

## Reference implementation and open allocations

Owners: rs-dashvm-validation, rs-dashvm, rs-dashvm-abi, rs-platform-version; tooling consumes the same validator. Production engine pin, complete opcode schedule, feature allowlist, exact ABI bytes, initialization restrictions and numeric caps remain explicit engineering review/measurement entries. The provisional resource/price appendix supplies starting values without asserting measured safety.

## Rationale

Cranelift prioritizes long-term execution speed; deterministic preparation and native storage reuse provide the blockchain-specific boundary. Splitting validation from runtime lets DPP/tooling share it without embedding a compiler. Multi-module bundles preserve atomic version activation and allow reuse without a distributed floating linker or per-function lifecycle.

## Related drafts and implementation tracking

[DVM-01](dip-dashvm-protocol.md) · [DVM-03](dip-dashvm-activation.md) · [DVM-04](dip-dashvm-storage.md) · [DVM-05](dip-dashvm-guards.md) · [DVM-06](dip-dashvm-execution.md) · [DVM-07](dip-dashvm-fees.md) · [DVM-08](dip-dashvm-scheduling.md) · [DVM-09](dip-dashvm-governance.md) · [DVM-10](dip-dashvm-proofs-clients.md) · [DVM-11](dip-dashvm-rust-sdk.md) · [DVM-12](dip-dashvm-external-primitives.md)

* [44-CODEC](https://github.com/dashpay/platform/issues/4679): Extract the shared guest value and codec foundation (4.4-dev).
* [44-ENGINE](https://github.com/dashpay/platform/issues/4681): Build a small isolated VM experiment and test foundation (4.4-dev).
* [50-ENGINE](https://github.com/dashpay/platform/issues/4683): Implement the deterministic runtime, validator and compatibility corpus (5.0-dev).
* [50-DEPLOY](https://github.com/dashpay/platform/issues/4684): Implement permanent bundles, registration, readiness and version routing (5.0-dev).
* [50-READS](https://github.com/dashpay/platform/issues/4686): Implement bounded current-state guest reads (5.0-dev).
* [50-AUTHOR](https://github.com/dashpay/platform/issues/4694): Deliver contract SDK, macros, build/test tools and worked example (5.0-dev).
* [50-VERIFY](https://github.com/dashpay/platform/issues/4696): Complete upgrade, sync, recovery and release evidence (5.0-dev).

[Complete storage mapping](https://github.com/dashpay/platform/issues/4626#issuecomment-5634141255) · [Capability catalogue and current amendments](https://github.com/dashpay/platform/issues/4626#issuecomment-5636957194) · [Module architecture](https://github.com/dashpay/platform/issues/4626#issuecomment-5636536959) · [Owner decisions and provisional limits](https://github.com/dashpay/platform/issues/4626#issuecomment-5583771268). These linked appendices retain their stated confirmed/proposed status.

## Copyright

This working proposal is released under the MIT License, following the default license of the Dash DIPs repository.
