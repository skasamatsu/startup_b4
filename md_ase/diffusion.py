"""
Calculate diffusion coefficient from MD trajectory using MDAnalysis.

Reference:
  Einstein relation: D = lim(t->inf) [ <|r(t) - r(0)|^2> / (6*t) ]
  
Usage:
  python diffusion.py <trajectory_file> <skip_frames> <output_prefix>
  
Example:
  python diffusion.py md_simulation_nvt.extxyz 10 diffusion
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
from MDAnalysis import Universe
from MDAnalysis.analysis.msd import EinsteinMSD

def calculate_diffusion(traj_file, skip_frames=0, output_prefix='diffusion'):
    """
    Calculate diffusion coefficient from trajectory.
    
    Args:
        traj_file (str): Path to trajectory file (e.g., .extxyz, .traj)
        skip_frames (int): Number of frames to skip at the beginning
        output_prefix (str): Prefix for output files
    """
    
    print(f"Loading trajectory: {traj_file}")
    u = Universe(traj_file)
    
    n_frames = len(u.trajectory)
    print(f"Total frames: {n_frames}")
    
    # Skip equilibration frames
    start_frame = skip_frames
    if start_frame > 0:
        print(f"Skipping first {skip_frames} frames for equilibration")
    
    # Calculate MSD using MDAnalysis
    print("Calculating MSD...")
    msd = EinsteinMSD(u, select='all', msd_type='xyz', start=start_frame)
    msd.run()
    
    # Extract MSD and time data
    msd_data = msd.results.msd
    time_fs = msd.results.timeseries  # in fs
    time_ps = time_fs / 1000.0  # convert to ps
    
    print(f"MSD data shape: {msd_data.shape}")
    print(f"Time range: {time_ps[0]:.2f} - {time_ps[-1]:.2f} ps")
    
    # Fit linear region to extract diffusion coefficient
    # Use second half of trajectory for better statistics
    fit_start = len(time_ps) // 2
    fit_end = len(time_ps)
    
    time_fit = time_ps[fit_start:fit_end]
    msd_fit = msd_data[fit_start:fit_end]
    
    # Linear fit: y = slope * x + intercept
    coeffs = np.polyfit(time_fit, msd_fit, 1)
    slope = coeffs[0]  # This is 6*D in Angstrom^2/ps
    
    # Convert to SI units (cm^2/s)
    # 1 Angstrom^2/ps = 1e-8 cm^2 / 1e-12 s = 1e-4 cm^2/s
    D_angstrom2_ps = slope / 6.0
    D_cm2_s = D_angstrom2_ps * 1e-4
    
    print(f"\n--- Diffusion Coefficient ---")
    print(f"D = {D_angstrom2_ps:.4e} Angstrom^2/ps")
    print(f"D = {D_cm2_s:.4e} cm^2/s")
    print(f"D = {D_cm2_s*1e5:.4e} x 10^-5 cm^2/s")
    
    # Plot and save
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(time_ps, msd_data, 'b-', linewidth=2, label='MSD')
    ax.plot(time_fit, np.polyval(coeffs, time_fit), 'r--', linewidth=2, 
            label=f'Fit (second half), D={D_cm2_s:.2e} cm²/s')
    ax.set_xlabel('Time (ps)', fontsize=12)
    ax.set_ylabel('MSD (Angstrom^2)', fontsize=12)
    ax.set_title('Mean Squared Displacement', fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_prefix}_msd.png', dpi=300)
    print(f"\nSaved plot: {output_prefix}_msd.png")
    
    # Save data
    np.savetxt(f'{output_prefix}_msd.txt', 
               np.column_stack([time_ps, msd_data]),
               header='Time_ps  MSD_Angstrom2',
               fmt='%.6f  %.6f')
    print(f"Saved data: {output_prefix}_msd.txt")
    
    return D_cm2_s, D_angstrom2_ps

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        print("Example:")
        print("  python diffusion.py md_simulation_nvt.extxyz 100 diffusion")
        sys.exit(1)
    
    traj_file = sys.argv[1]
    skip_frames = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    output_prefix = sys.argv[3] if len(sys.argv) > 3 else 'diffusion'
    
    calculate_diffusion(traj_file, skip_frames, output_prefix)
