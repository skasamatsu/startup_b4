#!/usr/bin/env python3
"""Compute RDF and basic shell metrics using sovapy (sova-cui).

Usage:
    python rdf_sova.py md_simulation_nvt.traj --output-prefix rdf_sova --sample-step 10
"""

import argparse
import os
import tempfile
import numpy as np
import matplotlib.pyplot as plt
from ase.io import iread, write as ase_write

from sovapy.core.file import File
from sovapy.core.analysis import PDFAnalysis


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RDF analysis using sovapy")
    parser.add_argument("structure", help="Input structure/trajectory file (.traj/.extxyz/.exyz/.xyz/.cif/.cfg)")
    parser.add_argument("--output-prefix", default="rdf_sova", help="Prefix of output files")
    parser.add_argument("--dr", type=float, default=0.05, help="Bin width in Angstrom")
    parser.add_argument("--dq", type=float, default=0.05, help="Q-space bin width")
    parser.add_argument("--qmin", type=float, default=0.3, help="Minimum Q")
    parser.add_argument("--qmax", type=float, default=25.0, help="Maximum Q")
    parser.add_argument("--sample-start", type=int, default=0, help="Start frame index (inclusive)")
    parser.add_argument("--sample-stop", type=int, default=-1, help="Stop frame index (exclusive), -1 for end")
    parser.add_argument("--sample-step", type=int, default=10, help="Sampling interval in frames")
    parser.add_argument("--max-samples", type=int, default=200, help="Maximum number of sampled frames")
    parser.add_argument(
        "--peak-rmin",
        type=float,
        default=0.8,
        help="Ignore points below this r when detecting the first peak",
    )
    parser.add_argument(
        "--min-window",
        type=float,
        default=3.0,
        help="Window size [Angstrom] after first peak for first-minimum search",
    )
    return parser.parse_args()


def compute_rdf_one_frame(extxyz_path: str, args: argparse.Namespace) -> tuple[np.ndarray, np.ndarray, float]:
    f = File.open(extxyz_path)
    atoms = f.get_atoms()

    if not atoms.volume.periodic:
        raise RuntimeError("Periodic cell info is required for RDF analysis.")

    pdf = PDFAnalysis(atoms, dr=args.dr, dq=args.dq, qmin=args.qmin, qmax=args.qmax)
    pdf.run()
    if pdf.r is None or pdf.gr_neutron is None:
        raise RuntimeError("sovapy PDFAnalysis failed. Check structure/cell information.")

    r = np.asarray(pdf.r)
    g = np.asarray(pdf.gr_neutron)
    rho = float(atoms.atom_number_density)
    return r, g, rho


def main() -> None:
    args = parse_args()

    if args.sample_step <= 0:
        raise ValueError("--sample-step must be > 0")
    if args.max_samples <= 0:
        raise ValueError("--max-samples must be > 0")
    if args.sample_start < 0:
        raise ValueError("--sample-start must be >= 0")

    stop = None if args.sample_stop < 0 else args.sample_stop

    sampled_indices: list[int] = []
    rho_list: list[float] = []
    r_ref = None
    g_sum = None

    with tempfile.TemporaryDirectory(prefix="rdf_sova_") as tmpdir:
        tmp_extxyz = os.path.join(tmpdir, "frame.extxyz")

        for frame_idx, ase_atoms in enumerate(iread(args.structure, index=":")):
            if frame_idx < args.sample_start:
                continue
            if stop is not None and frame_idx >= stop:
                break
            if (frame_idx - args.sample_start) % args.sample_step != 0:
                continue

            ase_write(tmp_extxyz, ase_atoms, format="extxyz")
            r_i, g_i, rho_i = compute_rdf_one_frame(tmp_extxyz, args)

            if r_ref is None:
                r_ref = r_i
                g_sum = np.zeros_like(g_i)
            else:
                if len(r_ref) != len(r_i) or not np.allclose(r_ref, r_i):
                    raise RuntimeError("RDF grid mismatch among sampled frames.")

            g_sum += g_i
            rho_list.append(rho_i)
            sampled_indices.append(frame_idx)

            if len(sampled_indices) >= args.max_samples:
                break

    if not sampled_indices:
        raise RuntimeError("No frame was sampled. Check --sample-start/--sample-stop/--sample-step.")

    r = r_ref
    g = g_sum / float(len(sampled_indices))
    rho = float(np.mean(rho_list))

    # First peak detection excluding the near-zero region.
    valid = np.where(r > args.peak_rmin)[0]
    if len(valid) == 0:
        raise RuntimeError("No valid points for peak detection. Adjust --peak-rmin.")

    peak_idx = valid[np.argmax(g[valid])]
    dr = r[1] - r[0]

    # Find first minimum after the first peak in a bounded window.
    start = peak_idx + 1
    end = min(len(r), peak_idx + 1 + int(args.min_window / dr))
    if start >= end:
        min_idx = peak_idx
    else:
        min_idx = start + np.argmin(g[start:end])

    r_peak = float(r[peak_idx])
    g_peak = float(g[peak_idx])
    r_min = float(r[min_idx])
    g_min = float(g[min_idx])

    # Use averaged number density over sampled frames for CN estimation.
    cn = float(4.0 * np.pi * rho * np.trapz(g[: min_idx + 1] * r[: min_idx + 1] ** 2, r[: min_idx + 1]))

    txt_path = f"{args.output_prefix}.txt"
    np.savetxt(txt_path, np.column_stack([r, g]), header="r_Angstrom g_r", fmt="%.6f %.6f")

    summary_path = f"{args.output_prefix}_summary.txt"
    with open(summary_path, "w", encoding="utf-8") as fsum:
        fsum.write("RDF analysis summary (sovapy)\n")
        fsum.write(f"Input: {args.structure}\n")
        fsum.write(f"Sample start: {args.sample_start}\n")
        fsum.write(f"Sample stop: {args.sample_stop}\n")
        fsum.write(f"Sample step: {args.sample_step}\n")
        fsum.write(f"Sampled frames: {len(sampled_indices)}\n")
        fsum.write("Sampled indices: " + " ".join(map(str, sampled_indices)) + "\n")
        fsum.write(f"First peak r [A]: {r_peak:.6f}\n")
        fsum.write(f"First peak g(r): {g_peak:.6f}\n")
        fsum.write(f"First minimum r [A]: {r_min:.6f}\n")
        fsum.write(f"First minimum g(r): {g_min:.6f}\n")
        fsum.write(f"Averaged number density [1/A^3]: {rho:.6f}\n")
        fsum.write(f"Coordination number (0->1st min): {cn:.6f}\n")

    fig_path = f"{args.output_prefix}.png"
    plt.figure(figsize=(8, 5))
    plt.plot(r, g, lw=2, label="g(r) [neutron weighted]")
    plt.axvline(r_peak, ls="--", lw=1.2, color="tab:red", label=f"1st peak: {r_peak:.2f} A")
    plt.axvline(r_min, ls="--", lw=1.2, color="tab:green", label=f"1st min: {r_min:.2f} A")
    plt.xlabel("r (Angstrom)")
    plt.ylabel("g(r)")
    plt.title("Radial Distribution Function (sovapy)")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_path, dpi=300)

    print(f"Saved data   : {txt_path}")
    print(f"Saved summary: {summary_path}")
    print(f"Saved plot   : {fig_path}")
    print(f"Sampled frames: {len(sampled_indices)}")
    print(f"Sampled indices: {sampled_indices}")
    print("--- RDF Analysis ---")
    print(f"First peak: r = {r_peak:.3f} A, g(r) = {g_peak:.3f}")
    print(f"First minimum: r = {r_min:.3f} A, g(r) = {g_min:.3f}")
    print(f"Estimated coordination number (0 -> first minimum): {cn:.3f}")


if __name__ == "__main__":
    main()
