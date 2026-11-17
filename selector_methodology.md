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
