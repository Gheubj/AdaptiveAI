# Phase 4 Research Design (Not Implemented)

Phase 4 would collect controlled local hardware measurements before training any hardware-aware
policy: cold/warm latency, time-to-first-token, tokens/s, RAM/VRAM, energy proxy, queue depth,
thermal state, quantization, batch size, and failure rate. Measurements require repeated randomized
blocks on declared hardware and separate calibration/test days.

A future router should use Sparse A as the neural quality predictor, Best Single and TF-IDF as
mandatory controls, and a transparent constrained optimizer before another learned gate. Hardware
features would enter a multi-objective policy only after cost/latency predictors pass calibration and
shift checks. Phase 4 should preregister quality non-inferiority margins and resource budgets.

Entry criteria are not met: neural ID improvement is absent, C underperforms its deterministic
control, OOD remains below Best Single, and no request-level hardware table exists. Therefore this
document is a design only.
