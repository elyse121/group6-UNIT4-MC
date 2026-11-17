"""Mini Project 4.1, Part B - LPWAN link-budget and battery-life comparison.

Scenario: 200 soil-moisture/temperature sensors on a 25 km^2 farm, 12-byte reading
every 30 min, max sensor-to-gateway distance 8 km, target 5 years on a 3.6 V
19,000 mAh primary lithium cell, no cellular coverage nearby, and a preference to
avoid per-device fees at 200-unit scale.

Transmit power / sensitivity values are the ones given in the manual. Current and
duration figures for the energy budget are ILLUSTRATIVE ASSUMPTIONS (marked below),
not measurements: change them to match a real module datasheet.

Usage:
    python3 link_budget_compare.py                  # base scenario
    python3 link_budget_compare.py --include-redcap # Lab Task 5
    python3 link_budget_compare.py --sensitivity    # Lab Task 6 (vary exponent n)
"""
import argparse
import math

import numpy as np

# ---- scenario ---------------------------------------------------------------
DISTANCE_KM = 8.0
D0_KM = 1.0
PL_D0_DB = 91.5          # free-space reference at 1 km, ~900 MHz (from manual)
N_EXPONENT = 3.5         # open rural terrain (from manual)
BATTERY_MAH = 19000.0
TARGET_YEARS = 5.0
MESSAGES_PER_DAY = 48    # one every 30 minutes
PAYLOAD_BYTES = 12
HOURS_PER_YEAR = 8760.0
CYCLES_PER_YEAR = MESSAGES_PER_DAY * 365

# ---- radio parameters (tx dBm, sensitivity dBm) from the manual ------------------
RADIO = {
    "NB-IoT":            (23.0, -129.0),
    "LTE-M (CE Mode B)": (23.0, -125.0),
    "LoRaWAN SF12":      (14.0, -137.0),
}
# Lab Task 5: representative values (assumption - wider carrier => worse sensitivity)
REDCAP = {"5G RedCap": (23.0, -118.0)}


def lora_airtime_s(payload_bytes, sf=12, bw_hz=125_000, cr=1, preamble=8,
                   explicit_header=True, crc=True, mac_overhead=13):
    """Semtech SX127x airtime formula. mac_overhead = LoRaWAN MHDR+FHDR+FPort+MIC."""
    pl = payload_bytes + mac_overhead
    de = 1 if (sf >= 11 and bw_hz == 125_000) else 0
    h = 0 if explicit_header else 1
    t_sym = (2 ** sf) / bw_hz
    t_pre = (preamble + 4.25) * t_sym
    num = 8 * pl - 4 * sf + 28 + 16 * (1 if crc else 0) - 20 * h
    n_pay = 8 + max(math.ceil(num / (4 * (sf - 2 * de))) * (cr + 4), 0)
    return t_pre + n_pay * t_sym


# ---- energy model: list of (phase, current_mA, seconds) per cycle + sleep mA ------
LORA_TX_S = lora_airtime_s(PAYLOAD_BYTES)
ENERGY = {
    # ASSUMPTIONS. NB-IoT: long repetition-coded uplink + connected-mode tail.
    "NB-IoT": dict(phases=[("TX (repetitions)", 220.0, 2.5), ("RX / connected tail", 50.0, 3.0)],
                   sleep_mA=0.003),          # PSM
    # ASSUMPTIONS. LTE-M CE Mode B: higher TX current, longer connected tail.
    "LTE-M (CE Mode B)": dict(phases=[("TX (repetitions)", 350.0, 2.0), ("RX / connected tail", 80.0, 4.0)],
                              sleep_mA=0.005),  # PSM/eDRX
    # LoRaWAN class A: TX airtime computed from the SF12 formula; RX1+RX2 windows assumed.
    "LoRaWAN SF12": dict(phases=[("TX 14 dBm", 44.0, LORA_TX_S), ("RX1+RX2 windows", 12.0, 2.0)],
                         sleep_mA=0.002),
    # Lab Task 5 assumption set
    "5G RedCap": dict(phases=[("TX", 400.0, 1.5), ("RX / connected tail", 100.0, 4.0)],
                      sleep_mA=0.01),
}


def mcl_db(tx_dbm, sens_dbm):
    return tx_dbm - sens_dbm


def path_loss_db(d_km, n=N_EXPONENT, pl_d0=PL_D0_DB, d0_km=D0_KM):
    return pl_d0 + 10.0 * n * np.log10(d_km / d0_km)


def battery_years(name):
    e = ENERGY[name]
    active_mah = sum(i * s for _, i, s in e["phases"]) / 3600.0
    active_s = sum(s for _, _, s in e["phases"])
    sleep_s = 30 * 60 - active_s
    sleep_mah = e["sleep_mA"] * sleep_s / 3600.0
    per_cycle = active_mah + sleep_mah
    per_year = per_cycle * CYCLES_PER_YEAR
    return per_cycle, per_year, BATTERY_MAH / per_year


def run(techs, n=N_EXPONENT):
    pl = float(path_loss_db(DISTANCE_KM, n))
    rows = []
    for name, (tx, sens) in techs.items():
        mcl = mcl_db(tx, sens)
        _, per_year, years = battery_years(name)
        rows.append((name, tx, sens, mcl, pl, mcl - pl, per_year, years))
    return pl, rows


def print_table(techs, n=N_EXPONENT):
    pl, rows = run(techs, n)
    print(f"Path loss at {DISTANCE_KM:g} km, n={n}: {pl:.1f} dB")
    hdr = f"{'Technology':<20}{'Tx dBm':>7}{'Sens dBm':>10}{'MCL dB':>8}{'PL dB':>8}{'Margin dB':>11}{'mAh/yr':>9}{'Years':>8}  5-yr?"
    print(hdr)
    print("-" * len(hdr))
    for name, tx, sens, mcl, p, margin, per_year, years in rows:
        ok = "yes" if years >= TARGET_YEARS else "NO"
        print(f"{name:<20}{tx:>7.0f}{sens:>10.0f}{mcl:>8.0f}{p:>8.1f}{margin:>11.1f}{per_year:>9.0f}{years:>8.1f}  {ok}")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--include-redcap", action="store_true")
    ap.add_argument("--sensitivity", action="store_true")
    args = ap.parse_args()

    techs = dict(RADIO)
    if args.include_redcap:
        techs.update(REDCAP)

    print(f"LoRaWAN SF12 airtime for {PAYLOAD_BYTES}-byte payload (+13 B MAC): {LORA_TX_S:.3f} s")
    print(f"Cycles per year: {CYCLES_PER_YEAR}; battery {BATTERY_MAH:.0f} mAh; target {TARGET_YEARS:g} years\n")
    print_table(techs)

    print("\nEnergy per cycle breakdown (ASSUMED currents/durations; edit ENERGY dict):")
    for name in techs:
        e = ENERGY[name]
        per_cycle, _, _ = battery_years(name)
        parts = ", ".join(f"{p} {i:g} mA x {s:.2f} s" for p, i, s in e["phases"])
        print(f"  {name:<20}{per_cycle:.4f} mAh/cycle  [{parts}; sleep {e['sleep_mA']:g} mA]")

    if args.sensitivity:
        print("\nLab Task 6 - sensitivity to path-loss exponent n (margins in dB):")
        ns = [2.5, 3.0, 3.5, 4.0]
        print(f"{'n':>5}{'PL dB':>9}" + "".join(f"{k:>20}" for k in techs))
        for n in ns:
            pl, rows = run(techs, n)
            print(f"{n:>5}{pl:>9.1f}" + "".join(f"{r[5]:>20.1f}" for r in rows))
        # break-even exponent where each technology's margin hits 0 at 8 km
        print("\nBreak-even exponent (margin = 0 at 8 km):")
        for name, (tx, sens) in techs.items():
            n_max = (mcl_db(tx, sens) - PL_D0_DB) / (10 * np.log10(DISTANCE_KM / D0_KM))
            print(f"  {name:<20}n_max = {n_max:.2f}")

    print("\nRecommendation logic (see report): the link budget closes for all three at 8 km,")
    print("but the scenario has NO cellular coverage, so NB-IoT / LTE-M are not available at all,")
    print("and per-device fees favour a self-owned network. LoRaWAN also has the longest battery life.")


if __name__ == "__main__":
    main()
