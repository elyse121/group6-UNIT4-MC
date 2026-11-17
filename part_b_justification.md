## Mini Project 4.1, Part B: Technology Recommendation

**Scenario:** 200 soil-moisture/temperature sensors on a 25 km² farm, 12-byte reading every 30 minutes, up to 8 km to the gateway, 5-year target on a 19,000 mAh cell, no cellular coverage nearby, and a preference to avoid per-device fees.

| Technology | MCL (dB) | Path loss at 8 km (dB) | Margin (dB) | Est. battery life (years) | Meets 5 years? |
|---|---|---|---|---|---|
| NB-IoT | 152 | 123.1 | 28.9 | 5.5 | Yes (barely) |
| LTE-M (CE Mode B) | 148 | 123.1 | 24.9 | 3.8 | No |
| LoRaWAN SF12 | 151 | 123.1 | 27.9 | 42.1* | Yes |

Path loss uses PL(8 km) = 91.5 + 10 × 3.5 × log10(8) = 123.1 dB. *In practice battery shelf life, not radio energy, caps this at roughly 10 to 15 years.

**Recommendation: LoRaWAN (SF12 for the farthest nodes), on a privately owned gateway.**

The link budget alone does not separate the options: all three close the 8 km link with 25 to 29 dB to spare, with NB-IoT and LoRaWAN deepest and LTE-M smallest. Battery life separates them more sharply. LTE-M's higher transmit current and longer connected-mode tail give the shortest life and miss the 5-year target, NB-IoT only just clears it, and LoRaWAN uses about one-eighth of the annual energy of NB-IoT (452 mAh against 3,433 mAh). Two of the Section 4.3 axes then decide the matter. First, there is no cellular coverage nearby, so NB-IoT and LTE-M have no network to attach to however good their margins look. Second, at 200 devices the preference to avoid per-device fees points to infrastructure the farm owns: a small number of LoRaWAN gateways costs a one-off outlay and carries no subscription per sensor. The stationary, low-rate, 12-byte workload suits LoRaWAN well, and airtime is not a concern: 48 messages a day at 1.48 s each is about 71 s per day, roughly 0.08% duty cycle.

**Caveats.** The transmit powers and sensitivities are the values given in the manual. The current and duration figures in the energy model are illustrative assumptions, not datasheet measurements, so the cellular battery estimates in particular could move by tens of percent. The conclusion does not depend on them, because the coverage and fee axes already rule out the cellular options.
