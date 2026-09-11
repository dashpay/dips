<pre>
  DIP: Unassigned (dip-dashvm-rust-sdk)
  Title: Rust authoring and reproducible packages
  Chain: Platform
  Layer: Applications
  Author(s): To be confirmed
  Comments-Summary: Initial draft; discussion and implementation tracking linked below.
  Status: Draft
  Type: Informational
  Created: 2026-09-11
  License: MIT License
</pre>

These are draft proposals for review, not assigned/accepted DIPs or implemented features. Confirmed design decisions are preserved. Sections explicitly marked proposed and the [shared allocation register](dip-dashvm/allocations.md) contain engineering proposals requiring review and measurement. Exact wire identifiers, the production engine profile, limits and prices remain open. DVM aliases identify this proposal series and are not official DIP numbers. Final authorship and official numbering remain subject to editorial review.

[Parent plan](https://github.com/dashpay/platform/issues/4626) · [Implementation tracking](https://github.com/dashpay/platform/issues/4676) · [Shared allocation register](dip-dashvm/allocations.md)

## Abstract

Describe the proposed Rust developer experience: ordinary free functions and impl methods, annotated persistent structs, native index/rule declarations, generated dispatch and typed capabilities. This is an Informational DIP draft; macro spelling and crate-file organization are developer conventions, while emitted manifest/ABI behavior is governed by the consensus DIPs.

## Motivation

Developers should write Rust while retaining Drive's document storage, indexing and validation. Persistence must be explicit enough to avoid hidden writes and expensive whole-state serialization, and tooling must reveal incompatible schema/version changes before deployment.

## Specification

### Author model

The guest SDK directory is `packages/rs-dash-sdk-contract`, Cargo package `dash-sdk-contract`, import `dash_sdk_contract`. Keep it distinct from the application/client `dash-sdk`. Use ordinary modules, structs, free functions, trait impls and multiple impl blocks. Only annotated entries are externally callable; Rust `pub` alone is not a contract method.

Proposed syntax:

```rust
use dash_sdk_contract::prelude::*;

#[persistent(collection = "scores", schema = 1, write = "contract")]
#[index(name = "by_class", fields(class = "asc"), count, sum = "points")]
pub struct Score {
    #[document_id]
    pub id: DocumentId,
    #[field(position = 0, max_chars = 64)]
    pub class: String,
    #[field(position = 1, min = 0, max = 1_000_000)]
    pub points: i64,
}

impl Score {
    #[entry(name = "score.add")]
    pub fn add(&mut self, _ctx: &mut Context, delta: i64) -> Result<()> {
        self.points = checked_add(self.points, delta)?;
        Ok(())
    }
}

fn checked_add(value: i64, delta: i64) -> Result<i64> {
    value.checked_add(delta).ok_or(Error::Arithmetic)
}
```

This sketch does not compile against a released SDK today. Native schema/rule validation still checks the candidate and actual authority; the helper does not replace those checks. A free `#[entry]` may coordinate multiple records/contracts. A singleton is a native document with a declared stable key/schema, not an opaque alternative storage engine.

### Persistence contract

Constructing or mutating a detached Rust value is transient. `get(id)` loads current ordered state and records dependencies. `insert(value)` stages a native create. `edit(id, closure)` loads, invokes and stages the native update only on successful return. An exported `&mut self` wrapper loads exactly the addressed record, supplies authentic Context, invokes the method and stages the receiver update on success. It never commits independently or loads the whole collection. IDs, revisions, owners and storage flags remain host controlled.

No persistence on Drop, no escaping mutable database references and no ambient global persistent singleton. A caught actual host/nested failure still poisons the outer invocation. Generated wrappers and hand-written Wasm have the same native checks. A direct unmarked helper invocation does not magically save its receiver.

### Declarations and code generation

Attributes handle common schemas/indexes/rules; typed `IndexSpec`, `CollectionSpec` and `RuleSpec` builders handle advanced native features. Merge both into one canonical manifest and reject duplicate/conflicting/unknown declarations. Stable serialized property, method, type and index identities survive Rust/module refactors. Bound every variable-length field. The complete capability catalogue must map to a declaration, typed operation or explicit unavailable boundary; no unsupported option is silently dropped.

Generate native count/sum/ranked/compound queries rather than computing secondary indexes in guest code. A count-and-sum query returns one consistent native result. Require bounded pagination, preserve empty-population semantics and use checked arithmetic for averages. Advanced collection handles refer only to authorized declared templates. Runtime instance creation is a bounded native operation; build-time schema generation does not create chain data.

Expose native bounded rules and read-only Wasm predicates with explicit action scopes. Native contested awards remain parameterized native behavior, never a callback. ACL calls require the gated native capability; private Rust fields are not private chain data. Randomness uses request/result handles with `NotReady`, never an ambient `rand()` fallback.

### Named modules and generated clients

A contract package may contain several deployable Wasm module targets. Build one version manifest with exact bindings and stable contract-wide public routes, even when a method moves between Rust modules. Unchanged blobs may be referenced in the next version. Produce an interface/binding report, per-module and aggregate sizes, supported-profile check and schema compatibility report. Do not add a code archive per function.

Generated cross-contract clients target latest stable methods and explicit delegated rights without an old-version parameter. Direct application clients may select supported older versions. Deprecation warnings, missing methods, freeze/wipe and receipt policy are visible. Current native schema/index update validation applies; generation cannot promise automatic index migrations or backfills.

### Toolchain artifacts and ownership

The nine proposed reusable crates are ABI, validation, runtime, Drive integration, contract SDK, proc macros, build support, test support and CLI; one unpublished example demonstrates the system. The architecture appendix names exact directories/modules and dependency arrows. ABI/value codecs and guest SDK stay no_std/Wasm compatible where designed; Drive, ABCI and Wasmtime do not leak into the guest dependency graph.

`cargo dash-contract` is the proposed command family for build/check/inspect/cost/deploy and local fixtures. Emit canonical Wasm blobs, canonical manifest, generated typed clients and readable schema/ABI/change reports. Use pinned toolchain/target/link flags and deterministic manifest ordering. Hash canonical output and compare repeat builds. Host admission independently validates it; a build attestation grants no extra authority.

## Testing and compatibility

Native reference tests compare application behavior; exact-engine Wasm tests establish metering, traps and runtime parity. Include compile-pass/compile-fail macro diagnostics, no_std builds, stable generated metadata, detached versus staged updates, repeated impl/free functions, multi-module reuse, queries/index updates and failure rollback. The worked sum/count example must run on the actual runtime and through native storage; a sketch or stub is insufficient for task completion.

Keep shared wire/error/proof/fee vectors for application SDKs and mobile examples. Match accepted old modules to historical profiles while using current storage/authorization. No network preflight, SDK funding sign-off or deployer allowlist is added. Normal package release automation and install/use checks remain required.

## Security, rationale and open allocations

The native host is the security boundary; macros provide ergonomics and errors. Annotated native documents were selected over one serialized root blob to preserve granular queries/indexes/proofs. Exact attribute grammar, generated symbol naming, package versions and toolchain pin remain reviewed implementation choices. The complete existing Rust API sketch is linked as an appendix, explicitly labeled future API.

## Related drafts and implementation tracking

[DVM-01](dip-dashvm-protocol.md) · [DVM-02](dip-dashvm-engine-abi.md) · [DVM-03](dip-dashvm-activation.md) · [DVM-04](dip-dashvm-storage.md) · [DVM-05](dip-dashvm-guards.md) · [DVM-06](dip-dashvm-execution.md) · [DVM-07](dip-dashvm-fees.md) · [DVM-08](dip-dashvm-scheduling.md) · [DVM-09](dip-dashvm-governance.md) · [DVM-10](dip-dashvm-proofs-clients.md) · [DVM-12](dip-dashvm-external-primitives.md)

* [43-PLAN](https://github.com/dashpay/platform/issues/4676): Establish specifications and implementation tracking (4.3-dev).
* [44-CODEC](https://github.com/dashpay/platform/issues/4679): Extract the shared guest value and codec foundation (4.4-dev).
* [44-AUTHOR](https://github.com/dashpay/platform/issues/4680): Settle contract declarations and the Rust author API (4.4-dev).
* [50-CLIENTS](https://github.com/dashpay/platform/issues/4693): Deliver DAPI, Rust, Wasm/JS and mobile parity (5.0-dev).
* [50-AUTHOR](https://github.com/dashpay/platform/issues/4694): Deliver contract SDK, macros, build/test tools and worked example (5.0-dev).
* [50-DOCS](https://github.com/dashpay/platform/issues/4697): Maintain public documentation and protocol-change checklist (5.0-dev).

[Complete storage mapping](https://github.com/dashpay/platform/issues/4626#issuecomment-5634141255) · [Capability catalogue and current amendments](https://github.com/dashpay/platform/issues/4626#issuecomment-5636957194) · [Module architecture](https://github.com/dashpay/platform/issues/4626#issuecomment-5636536959) · [Owner decisions and provisional limits](https://github.com/dashpay/platform/issues/4626#issuecomment-5583771268). These linked appendices retain their stated confirmed/proposed status.

## Copyright

This working proposal is released under the MIT License, following the default license of the Dash DIPs repository.
