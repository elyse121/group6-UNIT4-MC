"""Mini Project 4.2 - Rule-based IoT connectivity technology selector.

Scores NB-IoT, LTE-M, LoRaWAN, 5G RedCap and BLE/Zigbee against the six Section 4.3
axes (data rate, coverage, battery life, mobility, infrastructure ownership, cost) and
prints a ranked, justified recommendation.

HOW THE SCORE IS BUILT (every number is in the tables below, nothing is hidden):
 1. Each requirement input is mapped onto a 0-5 scale (REQ_* functions / tables).
 2. Each technology has a 0-5 capability score per axis (CAP_* tables).
 3. Per-axis match (0-5):
      scalar axes (data rate, battery, cost): 5 - (2.0 * shortfall + 0.25 * excess),
        where shortfall = max(req - cap, 0), excess = max(cap - req, 0), floor 0.
        Falling short is punished 8x harder than over-delivering.
      categorical axes (coverage, mobility, ownership): the capability table is already
        a suitability score (0-5) for each category, so match = table value.
 4. Overall = weighted mean of the six matches, rescaled to 0-100.
 5. Constraint rules (R1-R4) add/subtract points for cases a plain sum handles poorly.

Usage:
    python3 iot_selector.py --all                # four worked scenarios + student scenario
    python3 iot_selector.py --interactive        # enter a new scenario
    python3 iot_selector.py --all --markdown results_table.md
NOTE: capability scores encode standard published characteristics of each technology.
Re-check them against your unit's own Section 4.2/4.3 comparison tables before submitting.
"""
import argparse
from dataclasses import dataclass

TECHS = ["NB-IoT", "LTE-M", "LoRaWAN", "5G RedCap", "BLE/Zigbee"]
AXES = ["coverage", "mobility", "battery", "data_rate", "ownership", "cost"]

# Adjustable weights (sum need not be 1; they are normalised).
WEIGHTS = {"coverage": 0.25, "mobility": 0.20, "battery": 0.20,
           "data_rate": 0.15, "ownership": 0.10, "cost": 0.10}

# ---- categorical suitability tables (0-5) ------------------------------------------
CAP_COVERAGE = {   # category -> {tech: suitability}
    "deep_indoor":        {"NB-IoT": 5, "LTE-M": 4, "LoRaWAN": 3, "5G RedCap": 2, "BLE/Zigbee": 1},
    "wide_area_cellular": {"NB-IoT": 4, "LTE-M": 5, "LoRaWAN": 2, "5G RedCap": 4, "BLE/Zigbee": 0},
    "long_range_rural":   {"NB-IoT": 2, "LTE-M": 2, "LoRaWAN": 5, "5G RedCap": 1, "BLE/Zigbee": 0},
    "short_range_only":   {"NB-IoT": 1, "LTE-M": 1, "LoRaWAN": 2, "5G RedCap": 2, "BLE/Zigbee": 5},
}
CAP_MOBILITY = {
    "stationary":      {"NB-IoT": 5, "LTE-M": 5, "LoRaWAN": 5, "5G RedCap": 5, "BLE/Zigbee": 5},
    "local":           {"NB-IoT": 3, "LTE-M": 5, "LoRaWAN": 4, "5G RedCap": 5, "BLE/Zigbee": 4},
    "wide_area":       {"NB-IoT": 2, "LTE-M": 5, "LoRaWAN": 1, "5G RedCap": 5, "BLE/Zigbee": 0},
    "global_roaming":  {"NB-IoT": 2, "LTE-M": 5, "LoRaWAN": 1, "5G RedCap": 3, "BLE/Zigbee": 0},
}
CAP_OWNERSHIP = {
    "operator":      {"NB-IoT": 5, "LTE-M": 5, "LoRaWAN": 2, "5G RedCap": 5, "BLE/Zigbee": 1},
    "self_owned":    {"NB-IoT": 1, "LTE-M": 1, "LoRaWAN": 5, "5G RedCap": 2, "BLE/Zigbee": 5},
    "no_preference": {t: 5 for t in TECHS},
}

# ---- scalar capability levels (0-5) --------------------------------------------------
CAP_DATA_RATE = {"NB-IoT": 2, "LTE-M": 3, "LoRaWAN": 1, "5G RedCap": 5, "BLE/Zigbee": 3}
CAP_BATTERY = {"NB-IoT": 4, "LTE-M": 3, "LoRaWAN": 5, "5G RedCap": 2, "BLE/Zigbee": 4}
CAP_COST = {"NB-IoT": 3, "LTE-M": 2, "LoRaWAN": 4, "5G RedCap": 1, "BLE/Zigbee": 5}  # higher = cheaper per device


def req_data_rate(kbps):
    """Peak required rate (kbps) -> level. <=10:1, <=100:2, <=1000:3, <=10000:4, else 5."""
    for limit, lvl in ((10, 1), (100, 2), (1000, 3), (10000, 4)):
        if kbps <= limit:
            return lvl
    return 5


def req_battery(years):
    """Battery-life target (years) -> level. <=1:1, <=3:2, <=5:3, <=10:4, else 5."""
    for limit, lvl in ((1, 1), (3, 2), (5, 3), (10, 4)):
        if years <= limit:
            return lvl
    return 5


def req_cost(devices, budget):
    """Cost pressure level 0-5 from budget tier and fleet size (higher = more cost-sensitive)."""
    lvl = {"low": 4, "medium": 3, "high": 1}[budget]   # 'low' budget = tight money
    if devices >= 1000:
        lvl += 1
    elif devices < 50:
        lvl -= 1
    return max(0, min(5, lvl))


def scalar_match(req, cap):
    shortfall, excess = max(req - cap, 0), max(cap - req, 0)
    return max(0.0, 5.0 - (2.0 * shortfall + 0.25 * excess))


@dataclass
class Scenario:
    name: str
    data_rate_kbps: float
    coverage: str
    battery_years: float
    mobility: str
    ownership: str
    devices: int
    budget: str                      # tight budget = "low"
    no_terrestrial_coverage: bool = False   # e.g. open ocean (warning only)


def score(sc: Scenario, weights=WEIGHTS):
    req = {"data_rate": req_data_rate(sc.data_rate_kbps), "battery": req_battery(sc.battery_years),
           "cost": req_cost(sc.devices, sc.budget)}
    out = {}
    wsum = sum(weights.values())
    for t in TECHS:
        m = {
            "coverage": CAP_COVERAGE[sc.coverage][t],
            "mobility": CAP_MOBILITY[sc.mobility][t],
            "ownership": CAP_OWNERSHIP[sc.ownership][t],
            "data_rate": scalar_match(req["data_rate"], CAP_DATA_RATE[t]),
            "battery": scalar_match(req["battery"], CAP_BATTERY[t]),
            "cost": scalar_match(req["cost"], CAP_COST[t]),
        }
        base = sum(weights[a] * m[a] for a in AXES) / wsum * 20.0
        adj, notes = 0.0, []
        # R1: LoRaWAN has no cellular-style handover.
        if t == "LoRaWAN" and sc.mobility in ("wide_area", "global_roaming"):
            adj -= 20; notes.append("R1 -20: LoRaWAN lacks cellular handover for wide-area mobility")
        # R2: severe cost pressure at scale favours networks with no per-device airtime fee.
        if sc.devices >= 1000 and sc.budget == "low":
            if t in ("LoRaWAN", "BLE/Zigbee"):
                adj += 8; notes.append("R2 +8: severe cost pressure at scale favours self-owned, fee-free links")
            if t == "5G RedCap":
                adj -= 5; notes.append("R2 -5: highest per-device cost under severe cost pressure")
        # R3: short-range radios physically cannot serve wide-area needs.
        if t == "BLE/Zigbee" and (sc.coverage != "short_range_only" or sc.mobility in ("wide_area", "global_roaming")):
            adj -= 40; notes.append("R3 -40: short-range radio cannot meet the coverage/mobility need")
        # R4: RedCap is over-provisioned for low-rate telemetry.
        if t == "5G RedCap" and req["data_rate"] <= 2:
            adj -= 10; notes.append("R4 -10: RedCap over-provisioned for <=100 kbps telemetry")
        total = max(0.0, min(100.0, base + adj))
        out[t] = dict(total=total, base=base, adj=adj, match=m, notes=notes)
    ranked = sorted(out.items(), key=lambda kv: -kv[1]["total"])
    return ranked, req


LABEL = {"coverage": "coverage", "mobility": "mobility", "battery": "battery life",
         "data_rate": "data rate", "ownership": "infrastructure ownership", "cost": "cost per device"}


def justify(tech, d, ranked, weights=WEIGHTS):
    """Name the axes that DIFFERENTIATE this technology: its match minus the mean match of
    the other technologies, weighted. Axes where everyone scores the same are not reasons."""
    others = [x for t, x in ranked if t != tech]
    edge = {a: weights[a] * (d["match"][a] - sum(o["match"][a] for o in others) / len(others)) for a in AXES}
    strong = [a for a in sorted(AXES, key=lambda a: -edge[a]) if edge[a] > 0.05 and d["match"][a] >= 3.5][:2]
    weak = min(AXES, key=lambda a: edge[a])
    s = (f"Ahead of the field on {' and '.join(f'{LABEL[a]} ({d['match'][a]:.1f}/5)' for a in strong)}"
         if strong else "No axis clearly ahead of the field")
    if d["match"][weak] < 3 and edge[weak] < -0.05:
        s += f"; held back by {LABEL[weak]} ({d['match'][weak]:.1f}/5)"
    s += "."
    if d["notes"]:
        s += " " + "; ".join(n.split(":")[0] for n in d["notes"]) + " applied."
    return s


def report(sc, ranked, req):
    lines = [f"\n=== {sc.name} ===",
             f"Inputs: {sc.data_rate_kbps:g} kbps, {sc.coverage}, {sc.battery_years:g} y battery, "
             f"{sc.mobility}, {sc.ownership}, {sc.devices} devices, budget={sc.budget}"]
    for i, (t, d) in enumerate(ranked, 1):
        lines.append(f"{i}. {t:<11}{d['total']:5.1f}/100  {justify(t, d, ranked)}")
    if sc.no_terrestrial_coverage:
        lines.append("WARNING: part of this route has no terrestrial coverage (open ocean); none of the five "
                     "technologies can serve it. A satellite link is required there, so this ranking only "
                     "applies to the port/land segments.")
    return "\n".join(lines)


# ---- scenarios -------------------------------------------------------------------------
# NOTE: the four worked scenarios are defined from their one-line descriptions in the manual;
# adjust the inputs to match the exact figures given in your unit's Section 4.3.
SCENARIOS = [
    (Scenario("Smart water meter", 5, "deep_indoor", 15, "stationary", "operator", 10000, "medium"),
     ["NB-IoT"]),
    (Scenario("Fleet-tracked shipping container", 5, "wide_area_cellular", 3, "global_roaming", "operator",
              5000, "medium", no_terrestrial_coverage=True), ["LTE-M"]),
    (Scenario("Factory-floor sensor network", 500, "short_range_only", 3, "stationary", "self_owned", 300, "medium"),
     ["BLE/Zigbee", "5G RedCap"]),
    (Scenario("Wearable health monitor", 50, "short_range_only", 1, "local", "no_preference", 100000, "low"),
     ["BLE/Zigbee"]),
    # Student-designed scenario: GPS collars on cattle across a remote ranch with no cellular signal.
    (Scenario("NEW: Remote-ranch livestock collars", 5, "long_range_rural", 3, "local", "self_owned", 500, "low"),
     []),
]


def interactive():
    def ask(prompt, choices=None, cast=str):
        while True:
            v = input(prompt + (f" {choices}" if choices else "") + ": ").strip()
            try:
                v = cast(v)
            except ValueError:
                continue
            if not choices or v in choices:
                return v
    sc = Scenario(
        ask("Scenario name"),
        ask("Required peak data rate (kbps)", cast=float),
        ask("Coverage", list(CAP_COVERAGE)),
        ask("Battery-life target (years)", cast=float),
        ask("Mobility", list(CAP_MOBILITY)),
        ask("Infrastructure ownership", list(CAP_OWNERSHIP)),
        ask("Device count", cast=int),
        ask("Budget (low = tight)", ["low", "medium", "high"]),
    )
    ranked, req = score(sc)
    print(report(sc, ranked, req))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--interactive", action="store_true")
    ap.add_argument("--markdown", help="write results table to this file")
    args = ap.parse_args()
    if args.interactive:
        interactive()
        return
    rows = []
    print("Weights:", WEIGHTS)
    for sc, expected in SCENARIOS:
        ranked, req = score(sc)
        print(report(sc, ranked, req))
        top = ranked[0][0]
        status = "n/a (student scenario)" if not expected else ("MATCH" if top in expected else "DIVERGES")
        print(f"Top pick: {top}   expected: {' / '.join(expected) or '-'}   -> {status}")
        rows.append((sc, ranked, expected, status))
    if args.markdown:
        with open(args.markdown, "w") as f:
            f.write("| Scenario | #1 | #2 | #3 | #4 | #5 | Expected | Check |\n|---|---|---|---|---|---|---|---|\n")
            for sc, ranked, expected, status in rows:
                cells = " | ".join(f"{t} ({d['total']:.0f})" for t, d in ranked)
                f.write(f"| {sc.name} | {cells} | {' / '.join(expected) or '-'} | {status} |\n")
        print(f"\nResults table written to {args.markdown}")


if __name__ == "__main__":
    main()
