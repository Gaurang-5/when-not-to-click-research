# Live development and calibration checkpoint

**Status:** policy frozen; held-out test split untouched.

Jev 1.14 was queried once for each of 80 development cases and 40 calibration cases. Of 120 HTTP attempts, 119 parsed successfully. One development offscreen case returned HTTP 200 with a zero-width Box (`left == right`); it is retained as an output failure and fails closed. The response consumed 2,289 input tokens and is included in the operational cost. No malformed box was repaired, clipped, or retried.

The collection used 272,481 input tokens and 9,178 output tokens. At the documented input price of $0.042 per million tokens, estimated input cost is **$0.011444**. Mean latency was 530 ms, median 512 ms, and p95 714 ms. This is an estimate from returned usage, not an invoice.

## Frozen operating points

Thresholds were selected using calibration only, targeting the highest attainable total coverage at or below 30%. The logistic gate was fitted on 79 valid development outputs. Failed calls were excluded from fitting because they have no valid feature vector, but remain in all metric denominators and always abstain.

| Policy | Frozen threshold | Calibration accepted | Coverage | Selective risk | Absent false accept | Ambiguous wrong accept |
|---|---:|---:|---:|---:|---:|---:|
| A: every valid Box | 0.00 | 40/40 | 100% | 62.5% | 100% | 100% |
| B: Box confidence | 0.83 | 10/40 | 25% | 50% | 0% | 100% |
| C: presence + Box | 0.83 | 10/40 | 25% | 50% | 0% | 100% |
| D: presence + uniqueness + Box | 0.80 | 12/40 | 30% | 0% | 0% | 0% |
| E: logistic joint gate | 0.761012 | 12/40 | 30% | 0% | 0% | 0% |

On development at these frozen thresholds, D and E each accepted 30/80 cases with zero incorrect accepts. B accepted 49/80, with 38.8% selective risk and 100% ambiguous wrong acceptance. These are development and calibration observations on authored synthetic interfaces; they are neither held-out evidence nor a safety guarantee.

The exact freeze is stored in `results/live_frozen_policy.json`; its SHA-256 digest is stored separately and checked by the test runner. The freeze records source/config hashes and explicitly states that test data were not used for selection.
