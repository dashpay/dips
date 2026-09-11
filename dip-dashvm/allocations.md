# DashVM shared allocation register

These are draft proposals for review, not assigned/accepted DIPs or implemented features. Confirmed design decisions are preserved. Sections explicitly marked proposed and the [shared allocation register](allocations.md) contain engineering proposals requiring review and measurement. Exact wire identifiers, the production engine profile, limits and prices remain open. DVM aliases identify this proposal series and are not official DIP numbers. Final authorship and official numbering remain subject to editorial review.

| ID | Allocation | Task owner | Current state / required evidence |
| --- | --- | --- | --- |
| A01 | Protocol/profile and feature generations | [R05-03](https://github.com/dashpay/platform/issues/4676#task-r05-03) | Open; reconcile real PV/model registries, no assumed extra activation |
| A02 | Wire fields, messages and signed hash domains | [R05-03](https://github.com/dashpay/platform/issues/4676#task-r05-03) | Open; inventory actual DPP discriminants and serialize golden vectors |
| A03 | Nonce-family and rejection/paid outcome mapping | [R12-07](https://github.com/dashpay/platform/issues/4689#task-r12-07) | Proposed native reuse; bind every stage to existing native rules |
| A04 | Engine release/lock/config/target profile | [R08-01](https://github.com/dashpay/platform/issues/4683#task-r08-01) | Open; Wasmtime/Cranelift confirmed, exact pin requires current advisories/corpus |
| A05 | Wasm feature allowlist and complete opcode metering | [R03-04](https://github.com/dashpay/platform/issues/4683#task-r03-04) | Proposed first feature profile; scalar floats confirmed, no implicit defaults |
| A06 | Logical stack/memory/compilation limits | [FIX-05](https://github.com/dashpay/platform/issues/4683#task-fix-05) | Provisional values in appendix; measure adversarial/native headroom |
| A07 | ABI signatures, handles, value/manifest encodings | [R08-04](https://github.com/dashpay/platform/issues/4683#task-r08-04) | Semantic schemas drafted; exact bytes/version IDs open |
| A08 | Named-module linking and initialization | [R08-01](https://github.com/dashpay/platform/issues/4683#task-r08-01) | Proposed DAG/separate memories/host-mediated calls and bounded starts |
| A09 | Root and inner storage tags/codecs | [R08-03](https://github.com/dashpay/platform/issues/4684#task-r08-03) | 0/1 and smart 2/3/4 confirmed; new root/inner tags unallocated |
| A10 | Active eligibility/key/report binding | [R08-12](https://github.com/dashpay/platform/issues/4684#task-r08-12) | Whole active set and one vote confirmed; native predicate binding open |
| A11 | Block phases and boundary conventions | [R08-13](https://github.com/dashpay/platform/issues/4684#task-r08-13) | Concrete DVM-03/08/09 convention proposed; source-level ABCI vectors required |
| A12 | Native guard grammar and legacy applicability | [R07-01](https://github.com/dashpay/platform/issues/4685#task-r07-01) | Concrete typed AST and prospective-current-rule proposal; review required |
| A13 | Native capability ABI and operation/proof matrix | [CAP-02](https://github.com/dashpay/platform/issues/4680#task-cap-02) | 110 catalogue rows retained; unsupported/private operations remain gated |
| A14 | Speculative branch and complete observation log | [FIX-01](https://github.com/dashpay/platform/issues/4687#task-fix-01) | New upstream GroveDB work; canonical replay, no physical delta merge |
| A15 | Fee tables and numeric prices | [R12-03](https://github.com/dashpay/platform/issues/4689#task-r12-03) | Provisional rates supplied; actual measured native/opcode tables open |
| A16 | Refund-owner encoding and old fee versions | [FIX-08](https://github.com/dashpay/platform/issues/4689#task-fix-08) | Typed owner semantics confirmed; encoding/history audit open |
| A17 | Upload/transport envelope and staging | [R06-05](https://github.com/dashpay/platform/issues/4684#task-r06-05) | Prototype one bounded upload; chunking only with complete separate design |
| A18 | Receipt codec and retention update behavior | [R10-03](https://github.com/dashpay/platform/issues/4689#task-r10-03) | Default on confirmed; snapshot retention and bounded detail proposed |
| A19 | Time queue/recurrence/retry/terminal failure | [R10-05](https://github.com/dashpay/platform/issues/4688#task-r10-05) | Time-only/live-pay/cancellation confirmed; phase/retry cap/terminal details proposed |
| A20 | Prefunded purpose IDs and metadata | [R12-10](https://github.com/dashpay/platform/issues/4689#task-r12-10) | 40/128 reuse confirmed; preserve voting IDs, derive new job purpose safely |
| A21 | Governance ballots/expiry/application failure | [R11-10](https://github.com/dashpay/platform/issues/4695#task-r11-10) | Strict >2/3 and week confirmed; choice update/phase/failure encoding proposed |
| A22 | Logical wipe/token exclusion/proof mechanism | [FIX-07](https://github.com/dashpay/platform/issues/4695#task-fix-07) | Disposition confirmed; NotSummed/tombstone implementation needs full native matrix |
| A23 | DAPI/proof/client variant identifiers | [CAP-12](https://github.com/dashpay/platform/issues/4692#task-cap-12) | Current-state-only contract confirmed; bytes and parity vectors open |
| A24 | Rust macro grammar and reproducible toolchain | [SDK-01](https://github.com/dashpay/platform/issues/4680#task-sdk-01) | Author API drafted; precise symbols/codegen/toolchain remain implementation |
| A25 | Native ACL full specification | [EXT-ACL](https://github.com/dashpay/platform/issues/4677#task-ext-acl) | Separate external project: policy, delegation, revocation, fees/proofs required |
| A26 | Native randomness full specification | [EXT-RNG](https://github.com/dashpay/platform/issues/4682#task-ext-rng) | Separate external project: source/finality/withholding/binding/proof design required |
| A27 | DIP editor numbering and author attribution | [R05-01](https://github.com/dashpay/platform/issues/4676#task-r05-01) | Unassigned descriptive aliases; do not self-assign official numbers |

## Provisional measurement starting values

These are engineering guesses requested by the owner. Benchmark them before selecting protocol values. They deliberately permit large contract create/update transitions. A contract limit never relaxes a smaller existing native document, query or operation limit.

| Resource | Starting proposal | Rationale / validation needed |
| --- | --- | --- |
| Canonical WASM | 16 MiB per version | Room for large Rust contracts; stress compilation and permanent storage cost. |
| Signed contract create/update transition | 32 MiB total | Includes code, manifest, signatures and envelope; not 32 MiB per field. Keep other transition-family limits. Check DAPI, gRPC, mempool, proposal/block transport and replay all accept the same bounded envelope. |
| Upload form | One bounded create/update transition | Prototype this first; chunking remains an engineering option if transport/compilation measurements require it. |
| Guest linear memory | 128 MiB per instance; 256 MiB across the call tree | Reserve before execution; no machine-dependent `memory.grow` outcomes. Initial logical memory 16 MiB. |
| Memory/table shape | One 32-bit memory and one function table, at most 65,536 entries | Explicit initial profile; no shared memory, threads or memory64. Validate Rust toolchain compatibility. |
| Portable logical stack | 1 MiB total; 512 guest activation frames | Charge locals and operand slots, not only recursion depth; prove native-stack headroom separately. |
| Contract nesting | 8 active contract frames including the root | No repeated active contract ID; ordinary local Rust recursion uses the separate stack bound. |
| Module structure | 50,000 functions; 10,000 types; 128 params and 1,024 locals per function; 1,024 exports | Independent limits for large modules with costly shapes; reduce if adversarial Cranelift tests justify it. |
| Compilation complexity | 2 million decoded operators; 100,000 operators and 4,096 basic blocks per function; structural nesting 512 | Check before full compilation; reject excessive instrumented growth, initially cap instrumented bytes at 64 MiB. |
| Native host calls | 10,000 per outer invocation | One shared budget covers all nested work and predicates. |
| Returned read bytes | 8 MiB total; 1 MiB per query page | Also charge scanned/visited work; output limits alone do not bound query cost. |
| Logical dependency tracking | 100,000 distinct keys/range descriptors | Bound memory; coarsen or execute sequentially when necessary without changing ordered semantics. |
| Logical writes | 1,000 explicit operations and 4 MiB payload total | Meter and bound derived index/reference/cascade work too; native limits still apply. |
| Arguments / return / stored receipt | 256 KiB arguments; 64 KiB return; 64 KiB receipt | Shared nested byte accounting; reserve receipt bound before execution. Failure receipt cannot exceed reserved size. |
| Compute | 25 million units per outer invocation; 250 million contract units per block | Includes scheduled/guard/nested work; separate from existing native event budgets. No measured wall-clock limit decides consensus validity. |
| Readiness messages | 128 reports per batch; one pending executable version per contract | Deduplicate and rate-limit transport; membership sweeps need separate bounded accounting. |
| Scheduled retries | At most 10 attempts, interval at least one later block | Declared Drop/Retry/Skip policy; no same-block retry storm. |

**Provisional computation weights:** simple/control operation 1 unit; integer multiply and floating add/multiply 2; load/store 4; divide/remainder, floating divide/sqrt and conversions 8. Copy/hash work adds units per byte or native measured work. Every admitted Wasm operator must have an explicit weight before launch; this short list is not a complete opcode table. Propose 100 units for host entry plus actual native operation cost, 1 unit per copied byte, and 65,536 units per 64-KiB memory growth page. Never price a complex query as only 100 units.

**Provisional price:** 1 processing credit per computation unit, deployment validation 100,000 processing credits plus 20 per canonical WASM byte and 5 per decoded operator, readiness verification 10,000 processing credits per newly accepted signature plus metered membership lookup work. These are unbenchmarked candidate rates, not existing Platform prices. Add existing versioned native processing and storage charges exactly once; do not double-charge an operation already included in those tables. Permanent code, indexes and receipts pay actual native storage charges; use historical native refund rules with typed recorded owners. Local compilation time, cache misses and internal speculative retries add no fee. Verify admission estimates cover worst-case actual costs, charge only final ordered work, and adjust prices together with compute limits after measurements.

For operations not covered here, reuse existing native fees if available; otherwise keep the allocation explicitly unresolved until a bounded implementation and measured formula exist. Reserve names for ABI/features now, then allocate numeric wire/error/storage IDs from the real registries. No fabricated numeric IDs or exact engine revision are selected here.
