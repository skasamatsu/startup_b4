#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract instantaneous temperature from md_run.log and plot vs time."
    )
    parser.add_argument("--log", default="md_run.log", help="Path to MD log file")
    parser.add_argument(
        "--output", default="temperature_vs_time.png", help="Output image filename"
    )
    parser.add_argument(
        "--dt-fs",
        type=float,
        default=2.4,
        help="MD timestep in femtoseconds used in md.py",
    )
    parser.add_argument(
        "--target-temp",
        type=float,
        default=300.0,
        help="Target temperature [K] shown as dashed guide line",
    )
    parser.add_argument(
        "--save-dat",
        default="temp_vs_step.dat",
        help="Output text data file (step temp[K])",
    )
    return parser.parse_args()


def extract_step_temp(log_path: Path) -> tuple[np.ndarray, np.ndarray]:
    pattern = re.compile(r"Step:\s*(\d+),\s*Temp:\s*([0-9]*\.?[0-9]+)\s*K")
    steps: list[float] = []
    temps: list[float] = []

    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            m = pattern.search(line)
            if m:
                steps.append(float(m.group(1)))
                temps.append(float(m.group(2)))

    if not steps:
        raise ValueError(
            f"No Step/Temp records found in {log_path}. Check log format or file path."
        )

    return np.asarray(steps), np.asarray(temps)


def main() -> None:
    args = parse_args()
    log_path = Path(args.log)

    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")

    steps, temps_k = extract_step_temp(log_path)
    time_ps = steps * args.dt_fs * 1.0e-3

    dat = np.column_stack([steps, temps_k])
    np.savetxt(args.save_dat, dat, fmt=["%.0f", "%.6f"], header="step temp_K")

    plt.figure(figsize=(7, 4))
    plt.plot(time_ps, temps_k, lw=1.5, label="Instantaneous T")
    plt.axhline(
        args.target_temp,
        ls="--",
        lw=1.0,
        c="gray",
        label=f"Target T = {args.target_temp:g} K",
    )
    plt.xlabel("Time (ps)")
    plt.ylabel("Temperature (K)")
    plt.title("MD Instantaneous Temperature vs Time")
    plt.legend()
    plt.tight_layout()
    plt.savefig(args.output, dpi=200)

    print(f"saved plot: {args.output}")
    print(f"saved data: {args.save_dat}")


if __name__ == "__main__":
    main()
