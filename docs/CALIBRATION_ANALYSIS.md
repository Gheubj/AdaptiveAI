# Calibration Analysis

Calibration uses Brier score, log loss, ten-bin ECE, and validation-fitted scalar temperature.
Across five seeds on ID test, Architecture A ECE decreases from 0.0336 to 0.0290; Architecture B
from 0.0376 to 0.0257. Brier scores change from 0.2207 to 0.2203 (A) and 0.2210 to 0.2202 (B).

Calibration does not change quality-only routing because a single positive temperature preserves
within-query model rankings. It can still improve threshold interpretation. Under ARC-AGI shift,
calibration is poor: calibrated ECE is 0.4176 for A and 0.2950 for B, despite modest improvement
over uncalibrated predictions. ID calibration therefore does not transfer reliably.

Reliability plots are saved in `reports/phase3/reliability_diagrams.png`; aggregate numerical data
are in `calibration_summary.parquet`. Per-model calibration is available from the saved checkpoints
and labels but small OOD sample sizes make many per-model bins unstable.
