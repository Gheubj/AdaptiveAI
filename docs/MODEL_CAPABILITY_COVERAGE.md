# Model Capability Coverage

Bounded live pilot on 2026-11-18:

| Measure | Actual value |
|---|---:|
| Source rows reported by API | 78 |
| Rows accepted under bound | 20 |
| Rejected malformed rows | 0 |
| Unique accepted source model IDs | 20 |
| Exact canonical resolutions | 0 |
| Unresolved identities | 20 |
| Exact revisions | 0 |
| Unknown revisions | 20 |
| Complete record provenance | 20 |
| Independently verified rows | 0 |
| Redistribution-unknown rows | 20 |
| Benchmarks | 1 |
| Metrics | 1 (`resolved`, percent) |

Quantity is not evidence quality. Every capability profile retains unknown context, modalities,
tool/structured-output support, exact revision, and agent scaffold. The benchmark is an agentic
software-engineering construct; it does not cover general QA, math, writing, or isolated model
generation. No committed record-level snapshot is published.
