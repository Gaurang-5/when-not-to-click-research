# Live Jev 1.14 smoke test

Execution date: 17 October 2026. This is one development case and must not be generalized into a performance claim.

| Field | Observed value |
|---|---:|
| Case | `sidebar_00_00` |
| Requested/resolved model | `jev-1.14.0` / `jev-1.14.0` |
| HTTP status / attempts | 200 / 1 |
| Presence probability | 0.99 |
| Match Choice | `one` |
| P(none), P(one), P(several) | 0.00, 1.00, 0.00 |
| Choice confidence | 1.00 |
| Box confidence | 0.93 |
| Predicted box (px) | [240, 182, 400, 224] |
| Reference box (px) | [235, 180, 385, 222] |
| IoU | 0.8033 |
| Center inside reference | yes |
| Primary localization event | correct |
| Input/output tokens | 2,288 / 77 |
| Estimated list-price cost | $0.000096096 |
| Latency | 978.65 ms |

The call verifies that the documented parser matches a live response and that the pinned version is currently served. It does not verify absence, ambiguity, calibration or template transfer. At this observed token count, 200 comparable calls would cost approximately $0.0192192; actual cases may vary.
