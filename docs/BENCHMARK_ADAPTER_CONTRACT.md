# Benchmark Source Adapter Contract

A benchmark adapter exposes a versioned descriptor, validates a payload, and normalizes it to
`EvidenceRecord` objects for an explicit evaluation subject. The descriptor includes source and
adapter versions plus the full permission ledger.

Adapters must:

1. reject malformed or empty inputs;
2. preserve benchmark/version, task distribution, metric, units, scale, sample size, and retrieval
   time;
3. preserve exact model/evaluation configuration supplied by the caller;
4. attach provenance and permissions without elevating reliability;
5. perform no fuzzy model merge and no universal-rank calculation.

Phase 6A implements only `FixtureBenchmarkAdapter` with synthetic in-repository rows. It performs no
network operation. A real-source pilot is deferred to Phase 6B and requires a resolved permission
ledger, tiny bounded snapshot, checksum, parser fixture, and owner approval where publication terms
are uncertain.
