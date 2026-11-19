# Oracle and Cost Headroom

Oracle quality is a post-hoc upper bound: for each fully matched query it takes the maximum compatible
candidate score. Oracle gain is Oracle minus the best fixed candidate on the declared panel. It is
not a learnable-policy estimate.

Cost analysis uses only stored historical per-outcome costs with a named price source. If any price
is missing, analysis returns infeasible and explicitly refuses to substitute current prices. The
implemented cheapest-success oracle is labeled post-hoc and may not be operationally attainable.

Because external row-level ingestion was blocked, Phase 6B.5 reports no new empirical Oracle or cost
headroom. The synthetic test values verify arithmetic only and must never be cited as research data.
