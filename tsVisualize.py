# visualizing the bed at specific timesteps
import sys
import numpy as np
from matplotlib.widgets import TextBox
from matplotlib import pyplot as plt
import bed_analysis

# setting the command line arguments
from pathExtract import TASK_ID, get_points, get_path

try:
    TASK_ID = sys.argv[1]
except IndexError:
    pass

# angle and velocity
try:
    angle = int(sys.argv[2])
except IndexError:
    angle = 20
try:
    velocity = float(sys.argv[3])
except IndexError:
    velocity = 1.0
try:
    timestep = int(sys.argv[4])
except IndexError:
    # setting default values
    timestep = 0 # initial timestep for no timestep input

# setting up the figure in the global context
fig, ax = plt.subplots(figsize = (15,6))

# input parameter information
print("Timestep Visualization with parameters:")
print(f"A  :  {angle}\nV  :  {velocity}\nts :  {timestep}\n")

def plotter(time_rel: int) -> None:
    """
    Function to visualize the bed at a specific timestep
        - Args:
            - `time_rel`: relative time in range (0,200) that serves as the timestep index
        - Plots a scatter plot that includes the following:
            - particle bed
            - mound height
            - crater height
            - disc location
            - particles in contact
    """
    # specifying the timestep
    ax.set_title(f"(timestep: {time_rel})")

    Bed = bed_analysis.RegFile( get_path("bed", angle, velocity) )
    Disc = bed_analysis.DiscFile( get_path("disc", angle, velocity) )
    
    # the timestep to examine
    time = [(t,b) for t,b in Bed.ts][time_rel]

    # getting the disc data at the specified timestep
    this = Disc.dataDict
    discDatas = Disc.dataDict[time[1]]
    
    # getting the initial/reduced bed
    initBed = Bed.get_init_bed()
    reduc_idx = initBed.is_greater('y', 0.14)

    # getting the coordinate points for mound/crater
    (crater_x, crater_y), (mound_x, mound_y), touch_idx = get_points(
        time, 
        Bed, 
        reduc_idx, # making this the same with pathExtract
        (
            discDatas['disc_xs'],
            discDatas['disc_ys'],
            discDatas['disc_rs']
        )
    )
    

    particle_bed = Bed.get_bed(*time, reduc_idx)
    
    #* Plotting
    fig.suptitle(
        f"{TASK_ID}: V = {velocity}, A = {angle}",
        fontsize = 20, 
        fontweight = "bold"
    )
    ax.set_facecolor("white")

    # adding space to the bottom for the button
    plt.subplots_adjust(bottom = 0.2)

    

    # scatter plot radius scaling
    R_SCALE = 25000
    # plotting the bed
    ax.scatter(
        particle_bed.get_data('x', as_array=True),
        particle_bed.get_data('y', as_array=True),

        #change the colormap profile
        c = 'w',
        s = np.multiply(particle_bed.get_data('r', as_array=True),R_SCALE),

        # cmap = 'PuBu',
        edgecolors='k',
        linewidth = 0.5,
    )
    
    # plotting the disc
    ax.scatter(
        discDatas['disc_xs'],
        discDatas['disc_ys'],
        c = "orange",
        s = discDatas['disc_rs']*R_SCALE*7,
        edgecolors = 'k',
        linewidth = 1.0
    )
    ax.set_ylim( (0.13, 0.25) )
    ax.set_xlim( (-0.01, Bed.box_width) )
    
    # plotting the surface
    bed_asDict = particle_bed.get_input()
    ax.scatter(
        [ bed_asDict[key]['x'] for key in particle_bed.surface ],
        [ bed_asDict[key]['y'] for key in particle_bed.surface ],
        
        c = "cyan",
        s = np.multiply([ bed_asDict[key]['r'] for key in particle_bed.surface ], R_SCALE),
        edgecolors = 'k',
        linewidth = 0.5,

        label = "Surface"
    )

    # plotting if contact particles exist
    #? can track the mound/crater only after the particle is in contact with the bed !
    if len(touch_idx) != 0:
        particles_contact = Bed.get_bed(*time, touch_idx)
        
        ax.scatter(
            particles_contact.get_data('x', as_array=True),
            particles_contact.get_data('y', as_array=True),
            
            c = "magenta",
            s = np.multiply( particles_contact.get_data('r', as_array=True), R_SCALE ),
            edgecolors='k',
            linewidth = 0.5,
            
            label = "Contact Particles"
        )
        
        # crater arrow
        ax.annotate(
            f"Crater\n({crater_x:.4f},{crater_y:.4f})",
            xy = (crater_x, crater_y), xycoords = "data",
            xytext = (crater_x-0.05, crater_y+0.03), textcoords = "data",
            arrowprops = dict( arrowstyle = "->" )
        )
        ax.annotate(
            f"Mound\n({mound_x:.4f},{mound_y:.4f})",
            xy = (mound_x, mound_y), xycoords = "data",
            xytext = (mound_x-0.03, mound_y+0.01), textcoords = "data",
            arrowprops = dict( arrowstyle = "->" )
        )
        
        # adding the crater/mound labels to the legend
        ax.scatter(
            [0.15],
            [0.15],
            s = 0.00001,
            label = f"Crater: ({crater_x:.4f},{crater_y:.4f})\nMound: ({mound_x:.4f},{mound_y:.4f})"
        )


    ax.legend()
    plt.show()

def submit(text):
    try:
        ax.cla()
        plotter(int(text))
    except IndexError:
        pass

axbox = plt.axes( [0.2, 0.1, 0.05, 0.03] )
text_box = TextBox(axbox, 'Timestep (0-200):   ', initial = '0', textalignment = 'center')
text_box.on_submit(submit)


def main():
    plotter(timestep)

if __name__ == "__main__":
    main()


