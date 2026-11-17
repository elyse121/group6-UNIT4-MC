# Mobile Communications Mini Projects 4.1 to 4.3: Written Deliverables

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

---

## Mini Project 4.2: Scoring Methodology and Results

**Design.** `iot_selector.py` ranks NB-IoT, LTE-M, LoRaWAN, 5G RedCap and BLE/Zigbee against the six Section 4.3 axes: coverage, mobility, battery life, data rate, infrastructure ownership and cost. Every number lives in a visible table, so any recommendation can be audited line by line.

**Step 1: map requirements to a 0-5 scale.**
- Data rate (peak kbps): ≤10 → 1, ≤100 → 2, ≤1,000 → 3, ≤10,000 → 4, above → 5.
- Battery target (years): ≤1 → 1, ≤3 → 2, ≤5 → 3, ≤10 → 4, above → 5.
- Cost pressure: budget tier (low money = 4, medium = 3, high = 1), +1 if 1,000 or more devices, −1 if fewer than 50.
- Coverage (deep indoor, wide-area cellular, long-range rural, short-range only), mobility (stationary, local, wide-area, global roaming) and ownership (operator, self-owned, no preference) are categories, so each technology has a 0-5 suitability score per category.

**Step 2: per-axis match.** For scalar axes, match = 5 − (2.0 × shortfall + 0.25 × excess), floored at 0, where shortfall and excess compare the technology's capability level with the requirement. Falling short is punished eight times harder than over-delivering, because a link that cannot carry the data or last the battery target is unusable, while spare capability only costs money. Categorical axes use the suitability table directly.

**Step 3: weighted sum.** Default weights: coverage 0.25, mobility 0.20, battery 0.20, data rate 0.15, ownership 0.10, cost 0.10. Coverage and mobility weigh most because they decide whether a technology can work at all; ownership and cost mainly break ties. Weights are a dictionary at the top of the file and can be changed. The weighted mean is rescaled to 0-100.

**Step 4: constraint rules** (cases a plain sum handles poorly):
- **R1 (−20):** LoRaWAN when wide-area or global mobility is needed, since it lacks cellular-style handover.
- **R2 (+8 / −5):** with 1,000 or more devices on a tight budget, favour self-owned, fee-free links (LoRaWAN, BLE/Zigbee) and penalise 5G RedCap.
- **R3 (−40):** BLE/Zigbee when the need is not short-range, because the radio physically cannot reach.
- **R4 (−10):** 5G RedCap for telemetry at or below 100 kbps, where it is over-provisioned.

**Results** (inputs for the four worked scenarios are my reading of their one-line descriptions):

| Scenario | #1 | #2 | #3 | #4 | #5 |
|---|---|---|---|---|---|
| Smart water meter | **NB-IoT (87)** | LoRaWAN (84) | LTE-M (70) | 5G RedCap (42) | BLE/Zigbee (22) |
| Fleet-tracked shipping container | **LTE-M (90)** | NB-IoT (76) | 5G RedCap (64) | LoRaWAN (40) | BLE/Zigbee (3) |
| Factory-floor sensor network | **BLE/Zigbee (97)** | LoRaWAN (70) | 5G RedCap (70) | LTE-M (67) | NB-IoT (64) |
| Wearable health monitor | **BLE/Zigbee (100)** | LoRaWAN (75) | LTE-M (67) | NB-IoT (61) | 5G RedCap (57) |
| NEW: remote-ranch livestock collars | **LoRaWAN (93)** | LTE-M (66) | NB-IoT (62) | 5G RedCap (51) | BLE/Zigbee (27) |

The container ranking carries a warning: no listed technology covers an open-ocean crossing, so the result applies only to the port and land segments and a satellite link is needed for the rest.

**New scenario.** GPS collars on cattle across a remote ranch with no cellular signal: 5 kbps, long-range rural, 3-year battery, animals moving locally, self-owned network, 500 devices, tight budget. LoRaWAN wins on coverage and cost per device, with LTE-M held back by the ownership requirement.

**Limitations.** The capability tables encode standard published characteristics of each technology. They have not been transcribed from your unit's own Section 4.2/4.3 tables, which I did not have, so compare them and adjust any score that differs. Likewise, check the four scenario inputs against the figures in Section 4.3. The factory-floor result is the least certain: I accepted either BLE/Zigbee or 5G RedCap as the expected answer because I could not confirm the unit's reasoning.

---

## Why Publish/Subscribe Scales Better Than Request/Response for Many-to-Many Telemetry

**Decoupling.** In the plant monitor I built, a sensor publishes a reading to a topic such as `plant1/lineA/temperature` and never learns who, if anyone, receives it. The aggregator subscribes once to `plant1/+/+` and receives everything the broker routes to it. The two sides share no addresses, no schedule and no code. Request/response couples them: a consumer must know each sensor's address, ask for each reading, and wait for the answer, and the sensor must be awake and reachable at that moment.

**Scaling with sensors and consumers.** Suppose S sensors must be visible to C consumers (dashboard, alerter, logger, maintenance system). With polling over HTTP or CoAP, every consumer keeps its own relationship with every sensor, so traffic and configuration grow roughly as S × C. Each sensor must also answer every consumer's poll, which costs battery on a constrained device. With a broker, each sensor publishes once and each consumer subscribes once, so the work grows roughly as S + C. The demonstration showed the practical side of this. At 09:17:26 I started a fourth sensor, `plant1/lineB/vibration`, while the system was running. The aggregator logged "NEW TOPIC discovered" and began applying the vibration threshold to it without any edit or restart, because the wildcard subscription already covered it. A polling design would need every consumer's sensor list updated first.

**QoS levels.** MQTT lets each message choose its delivery guarantee: QoS 0 (at most once, no acknowledgement), QoS 1 (at least once, acknowledged, duplicates possible) and QoS 2 (exactly once, at the price of a four-step handshake). I used QoS 1 for readings and status, which suits telemetry where a repeated reading is harmless but a silently lost alert is not. The important point is that this guarantee is negotiated between each client and the broker, so a slow or briefly disconnected consumer does not force the sensor to retry anything. In request/response, reliability is the requester's problem: it must time out and retry, and each consumer repeats that work for each sensor.

**Retained messages.** Every reading was published with the retain flag. When I started a late-joining subscriber at 09:17:21, it received the last known value of all four topics immediately, flagged RETAINED, without waiting for the next sensor cycle and without contacting any sensor. This matters most for sleepy, battery-powered devices: under polling, a consumer joining late would have to wake the device or wait. With retained messages the broker answers on the sensor's behalf. The trade-off is that a retained value may be stale, so a consumer should also look at the timestamp or at the status topic.

**Last Will and Testament.** The `lineA` temperature sensor registered a will on `plant1/lineA/status` before connecting. When I killed that process with `kill -9` at 09:17:36, the broker published the retained "offline" message, and the aggregator showed the status change in the same second, with no code running on the dead sensor. Under polling, a failed sensor is indistinguishable from a slow one: each consumer discovers the failure separately through its own timeouts. One caveat from the run: the notice was near-instant because a killed process closes its TCP socket; for a silent network failure the broker only acts after about one and a half times the keep-alive interval (5 s here), so the detection delay is a tunable trade-off against traffic.

**Where request/response still wins.** The broker becomes a central dependency that must be sized, secured and made redundant, and a failure there affects everyone. Pub/sub is also awkward when the caller needs a direct answer to a specific question, such as sending a command and getting a result back, or a one-off query to a single device. CoAP's Observe option narrows the gap by letting a client register for updates, but each registration is still held on the device itself, so the per-device load still grows with the number of consumers.

**Conclusion.** For many-to-many telemetry, the broker-mediated pattern keeps the sensor's workload constant as consumers are added, lets new sensors appear without touching consumers, and gives three useful behaviours for free: tunable delivery, last-known-state for late joiners, and automatic failure announcements. Request/response remains the better fit for few consumers and for interactions that need a direct reply.
