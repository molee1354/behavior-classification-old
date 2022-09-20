import os
from math import sqrt
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from bed_analysis import RegFile

def main():
    base = Path(os.getcwd())
    base.parent.absolute()

    path = f"{base.parent.absolute()}\\lammps_repeater\\iterations_A90\\iteration_V5.0_A90\\dmp.reg.LIS01_V5.0_A90"
    
    # Path for the big script
    # C:\\Users\\Student\\projects\\pulse_propagation\\surface_pulse_scripts\\dmp.reg.E_2.25e7

    """
    The y-cut value in the "in.*" file for the big script is 0.444.
    --> maybe ignore particles that are higher than 0.4?

    """

    # instantiating a bed object
    pBed = RegFile(path)
    timesteps = pBed.ts

    # getting the initial bed
    initBed = pBed.get_init_bed()

    # picking out specific particles on the surface
    # reduc_idx1 = initBed.is_array_surface(np.linspace(0.15, 0.25, 3)) #type: ignore

    # somewhere below the depth
    # reduc_idx2 = initBed.is_array('h',np.linspace(0.15,0.25,3),0.15) #type: ignore

    # reduc_idx = [*reduc_idx1, *reduc_idx2]
    reduc_idx = initBed.is_array_surface(np.linspace(0.17, 0.25, 5)) 

    # vertical
    # reduc_idx = initBed.is_array('v',np.linspace(0.05,0.15,10),0.18)


    # getting the coordinates for the specific particles over all timesteps

    # initializing the dictionary
    particles = {}
    for pID in reduc_idx:
        particles[pID] = {
            'x' : [],   # empty lists for x and y
            'y' : []
        }

    # getting the coordinate information for each particle, for each timestep
    for t in timesteps:
        bed_reduc = pBed.get_bed(*t, reduc_idx)

        for pID in reduc_idx:
            particles[pID]['x'].append(bed_reduc.get_data('x')[pID])
            particles[pID]['y'].append(bed_reduc.get_data('y')[pID])


    # plotting the extracted data
    fig, ax = plt.subplots(1,3, figsize=(17,6))

    fig.suptitle("Tracked Particle Paths", fontweight = 'bold')

    for key in particles:

        # pos, vel, acc
        pos_x_t = particles[key]['x']
        pos_y_t = particles[key]['y']

        # taking the second time derivative
        acc_x_t = np.gradient(np.gradient(particles[key]['x'],len(timesteps)),len(timesteps))
        acc_y_t = np.gradient(np.gradient(particles[key]['y'],len(timesteps)),len(timesteps))

        ax[0].plot(
            range(len(timesteps)),
            acc_x_t,
            label = f"{str(key)}, (x,y) = ({particles[key]['x'][0] : .2f},{particles[key]['y'][0] : .2f})"
        )
        ax[0].set_title("Particle X vs Time")
        ax[0].set_xlabel("Time")
        ax[0].set_xlim((0,20))
        ax[0].set_ylabel("X")
        ax[0].legend()

        ax[1].plot(
            range(len(timesteps)),
            acc_y_t,
            label = f"{str(key)}, y = {particles[key]['y'][0] : .2f}"
        )
        ax[1].set_title("Particle Y vs Time")
        ax[1].set_xlabel("Time")
        ax[1].set_xlim((0,20))
        ax[1].set_ylabel("Y")

        ax[2].plot(
            range(len(timesteps)),
            [ sqrt(ax**2 + ay**2) for ax,ay in zip(acc_x_t,acc_y_t) ],
            label = f"{str(key)}, x = {particles[key]['x'][0] : .2f}"
        )
        ax[2].set_title("Acceleration Magnitude vs Time")
        ax[2].set_xlabel("Time")
        ax[2].set_ylabel("Acceleration")
        ax[2].set_xlim((0,20))
        # ax[2].set_xlim((0,pBed.box_width))

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
