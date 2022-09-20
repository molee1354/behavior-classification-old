import os
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from bed_analysis import RegFile

# C:\Users\Student\projects\lammps_manager\Output_Refactor
base = Path(os.getcwd())
# path = "C:\\Users\\moosu\\projects\\Research\\lammps_manager\\lammps_repeater\\iterations_A90\\iteration_V5.0_A90\\dmp.reg.LIS01_V5.0_A90"
path = f"{base.parent.absolute()}\\lammps_repeater\\iterations_A90\\iteration_V5.0_A90\\dmp.reg.LIS01_V5.0_A90"

# instantiating a bed object
pBed = RegFile(path)
timesteps = pBed.ts
# box_height = pBed.box_height
# box_width = pBed.box_width

# getting the initial bed
initBed = pBed.get_init_bed()

# picking out specific particles on the surface
# reduc_idx = initBed.is_array_surface(np.linspace(0.15, 0.3, 10))

reduc_idx = initBed.is_array('h',np.linspace(0.15,0.25,10),0.14)

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

# animating the data
t = range(len(timesteps))

ys = [ particles[idx]['y'] for idx in reduc_idx ]
xs = [ particles[idx]['x'] for idx in reduc_idx ]
vx = [np.gradient(x, len(timesteps)) for x in xs]
vy = [np.gradient(y, len(timesteps)) for y in ys]

fig, ax = plt.subplots(1,3, figsize=(17,6))
fig.suptitle("Particle Paths", fontweight = "bold")

# initializing the axis object with however many plots we need
lines0 = [ ax[0].plot( [],[], label = f"x = {particles[i]['x'][0]: .3f}" )[0] for i in reduc_idx ]
lines1 = [ ax[1].plot( [],[], label = f"x = {particles[i]['x'][0]: .3f}" )[0] for i in reduc_idx ]
lines2 = [ ax[2].plot( [],[], label = f"x = {particles[i]['x'][0]: .3f}" )[0] for i in reduc_idx ]

ax[0].set(title = "Y vs Time", xlim=(0,200), 
    # ylim=(0.13,0.15)
)
ax[0].set_xlabel("Time")
ax[0].set_ylabel("Height")
ax[0].legend()

ax[1].set(title = "X vs Time", xlim=(0,200), ylim=(0,0.35))
ax[1].set_xlabel("Time")
ax[1].set_ylabel("X Position")

ax[2].set(title = "X vs Y", xlim=(0,0.35), 
    # ylim=(0.13,0.15)
)
ax[2].set_xlabel("X Position")
ax[2].set_ylabel("Y Position")

# functions to update the data for each timestep
def update(num, domain, ys, lines):
    for line, y in zip(lines, ys):
        line.set_data(domain[:num], y[:num])

    return lines

# xs has "len(reduc_idx)" many points, so it must also be iterated on
def update2(num, domain, ys, lines):
    for line, y, x in zip(lines, ys, domain):
        line.set_data(x[:num], y[:num])
    
    return lines

# calling the animator object
anim1 = animation.FuncAnimation(fig, update, len(t), fargs=(t, vy, lines0), interval=25, blit=True, repeat=False)
anim2 = animation.FuncAnimation(fig, update, len(t), fargs=(t, vx, lines1), interval=25, blit=True, repeat=False)
anim3 = animation.FuncAnimation(fig, update2, len(t), fargs=(xs, ys, lines2), interval=25, blit=True, repeat=False)

plt.tight_layout()
plt.show()
