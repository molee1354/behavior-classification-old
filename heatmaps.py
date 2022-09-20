from statistics import mean, median
import sys
import json
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from pathExtract import TASK_ID, TRIAL_ID

try:
    TASK_ID = sys.argv[1]
except IndexError:
    pass
try:
    TRIAL_ID = sys.argv[2]
except IndexError:
    pass

# setting data to plot as a command line argument
try:
    PLOT_DATA = sys.argv[3]
except IndexError:
    PLOT_DATA = "contact_pIDs"


"""
Script to plot heatmap-style plots for the output datas.
    - 2x2 plot with:
        1. number of contact pIDs
        2. airborne duration
        3. surpasses T/F
        4. crater_out T/F
    - The plot also has the behaviors explicitly labeled as text on the thing
    - color is magnitude or T/F
"""

def processHuman(data_dict: dict) -> list[list[int]]:
    """
    Function to process the input dictionaries to a 2D list for plotting
        - Args
            - `data_dict`: dictionary of behaviors (and confidence)
        - Returns
        - 2-D array for the matshow plot
    """

    # for the normal dictionary 
    # this way the data type of the computer output can be anything other than "str"
    behaviorsList = []
    for angle in np.linspace(20, 70, 11, dtype=int):
        behaviorList_I = []
        for velocity in np.linspace(1.0, 7.0, 13):

            if data_dict[f"V{velocity}_A{angle}"] == "FS":
                behaviorList_I.append(0)
            if data_dict[f"V{velocity}_A{angle}"] == "RO":
                behaviorList_I.append(1)
            if data_dict[f"V{velocity}_A{angle}"] == "RC":
                behaviorList_I.append(2)

        behaviorsList.append(behaviorList_I)

    return behaviorsList

def processData(input_dict: dict, parameter: str) -> list[list[int]]:
    """
    Function to process the data into lists
        - Args:
            - `input_dict` : input dictionary with values of interest
            - `parameter` : the parameter in the dicitonary to focus on
        - Returns:
            - A 2-D list of the values within the dictionary
    """

    return [
        [input_dict[f"V{velocity}_A{angle}"][parameter] for velocity in np.linspace(1.0, 7.0, 13) ] for angle in np.linspace(20, 70, 11, dtype=int)
    ]

def main():

    # loading the data in a dictionary
    with open(f"behaviors/computer/Computer_Behavior_{TASK_ID}_{TRIAL_ID}.json", 'r') as file:
        compDict = json.load(file)

    #! temp human behavior open
    with open(f"behaviors/human/Human_Behavior_{TASK_ID}.json", 'r') as file:
        humanDict = json.load(file)

    humanData = processHuman(humanDict)

    # keys = [ key for key in next(iter(compDict.values())) if (key != "confidence") and (key != "behavior")]
    keys = [ key for key in next(iter(compDict.values())) if (key != "confidence") ]

    # a dictionary of 2d lists for the heatmap
    datas = {key: processData(compDict, key) for key in keys}

    # conversion key
    conversion = {
        'FS': 0,
        'RO': 1,
        'RC': 2
    }

    # a list to convert the strings into the corresponding integers
    compData = [
        [conversion[that] for that in line] for line in datas['behavior']
    ]

    #* finding the average contact particles for FS, RO, RC
    fss, ros, rcs = [],[],[]
    for i, line in enumerate(datas["behavior"]):
        for j, thing in enumerate(line):
            if thing == 'FS':
                fss.append(datas["contact_pIDs"][i][j])
            if thing == 'RO':
                ros.append(datas["contact_pIDs"][i][j])
            if thing == 'RC':
                rcs.append(datas["contact_pIDs"][i][j])

    # examining the maximum and minimum values
    print(f"[{TASK_ID}] - Unique Disc Contact Particles")
    print(f"FSs: min/max = {min(fss)}/{max(fss)}\tmean/median = {mean(fss):.2f}/{(median(fss))}")
    print(f"ROs: min/max = {min(ros)}/{max(ros)}\tmean/median = {mean(ros):.2f}/{(median(ros))}")
    print(f"RCs: min/max = {min(rcs)}/{max(rcs)}\tmean/median = {mean(rcs):.2f}/{(median(rcs))}")

    #* plotting
    fig, ((ax2, ax3),(ax1, ax4)) = plt.subplots(2,2, figsize=(10,9))
    fig.suptitle(f"{TASK_ID} Quantities Comparison", fontsize = 16, fontweight = "bold")

    y_axis = list(np.linspace(20, 70, 11, dtype=int)) # angles
    x_axis = list(np.linspace(1.0, 7.0, 13)) # velocities

    # custom colormap defs
    myColors = (
        (199/255,45/255,34/255,1.0), 
        (224/255,227/255,34/255,1.0), 
        (64/255,133/255,27/255,1.0)
    )
    colors = LinearSegmentedColormap.from_list('Custom', myColors, len(myColors))
    binColors = (
        (0.8, 0.8, 0.8, 1),
        (0,0,0,1)
    )
    BW = LinearSegmentedColormap.from_list("Custom", binColors, len(binColors))

    # Particle Contact Length Heatmaps
    ax1.set_title("Unique Contact Particles")
    ax1 = sns.heatmap(
        ax = ax1,
        data = datas[PLOT_DATA],
        yticklabels = y_axis, 
        linewidths = 2, 
        cmap = "Blues",
        annot = np.array(datas['behavior']), 
        fmt = ""

    )
    ax1.invert_yaxis()
    ax1.set_xticklabels(x_axis, rotation = 45)
    ax1.set_xlabel("Velocities")
    ax1.set_ylabel("Angles")
    colorabar1 = ax1.collections[0].colorbar

    # particle Contact Length with Annotation
    ax4.set_title("Unique Contact Particles (Mag)")
    ax4 = sns.heatmap(
        ax = ax4, 
        data = datas[PLOT_DATA], 
        yticklabels = y_axis,
        linewidths = 2, 
        cmap = "Blues", 
        annot = True
    )
    ax4.invert_yaxis()
    ax4.set_xticklabels(x_axis, rotation = 45)
    ax4.set_xlabel("Velocities")
    ax4.set_ylabel("Angles")
    colorbar4 = ax4.collections[0].colorbar
    
    # Computer Behavior Plot
    ax2.set_title("Computer Plot")
    ax2 = sns.heatmap(
        ax = ax2,
        data =compData,
        yticklabels=y_axis,
        linewidths=2,
        cmap=colors,
        vmax=2, vmin=0
    )
    ax2.invert_yaxis()
    ax2.set_xticklabels(x_axis, rotation=45)
    ax2.set_xlabel("Velocities")
    ax2.set_ylabel("Angles")
    ax2.margins(1)

    colorbar2 = ax2.collections[0].colorbar
    colorbar2.set_ticks([0.33,1.0,1.66])
    colorbar2.set_ticklabels(["FS","RO","RC"])
    
    # Human Behavior Plot
    ax3.set_title("Human Plot")
    ax3 = sns.heatmap(
        ax = ax3,
        data = humanData,
        yticklabels=y_axis,
        linewidths=2,
        cmap=colors,
        vmax=2, vmin=0
    )
    ax3.invert_yaxis()
    ax3.set_xticklabels(x_axis, rotation=45)
    ax3.set_xlabel("Velocities")
    ax3.set_ylabel("Angles")
    ax3.margins(1)

    colorbar3 = ax3.collections[0].colorbar
    colorbar3.set_ticks([0.33,1.0,1.66])
    colorbar3.set_ticklabels(["FS","RO","RC"])

    # plt.subplots_adjust(bottom=0.21)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
