import sys
import numpy as np
from ase.build import bulk
from ase.io import read
from ase import units
from ase.md import Langevin
from ase.io.trajectory import Trajectory
from ase.optimize import BFGS
from ase.filters import StrainFilter
from ase.constraints import FixSymmetry

from ase.calculators.emt import EMT

from sevenn.calculator import SevenNetCalculator,SevenNetD3Calculator

atoms = read("se2cl2_60A.xyz")
#atoms = atoms.repeat([4,2,6])
T = 300 # temperature in K
device = "cuda"
# specify universal mlip calculators
calc = SevenNetCalculator(model='7net-omat', device=device)
# attach the calculator to the atoms object
atoms.calc = calc

# MD setup
np.random.seed(42)  # For reproducibility
T_init = 30
atoms.set_momenta(np.random.randn(len(atoms), 3) * np.sqrt(T_init * units.kB * atoms.get_masses()[:, None]))
timestep = 2.4 * units.fs  # Time step of 1 femtosecond
temperature = T * units.kB  # Temperature in Kelvin
dyn = Langevin(atoms, timestep, temperature, friction=0.2)

def print_energy(a=atoms):
    epot = a.get_potential_energy()
    ekin = a.get_kinetic_energy()
    temp = ekin / (1.5 * units.kB * len(a))  # Temperature estimation
    print(f"Step: {dyn.nsteps}, Temp: {temp:.2f} K, Epot: {epot:.6f} eV, Ekin: {ekin:.6f} eV, Etot: {epot+ekin:.6f} eV")
    sys.stdout.flush()

dyn.attach(print_energy, interval=100)

# Save trajectory to a file
traj = Trajectory('md_simulation_nvt.traj', 'w', atoms)
dyn.attach(traj.write, interval=100)

# Run the MD simulation for 1000 steps
dyn.run(1e5)
 
