from dataclasses import dataclass
import json
from statistics import median
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import numpy as np

class Comparer:
    """
    Class to compare and plot the extracted data

    - Args:
        - `data_json` : path to the file that contains the relevant data
        - `human_decision` : the human decision for the specific iteration

    - Returns: 
        - a `_DecisionPackage` object which is pretty much a jumble of data that can be used to compare \
            human and computer behaviors and plot paths. 
            
            class _DecisionPackage:
                computer_decision: str
                human_decision: str
                decisionDict: dict
                airborne: int
                switches: int
                surpasses: bool
                crater_out: bool
                impact_time: int
                reason: list[str]
                datas: dict
                num_timesteps: int

    """

    def __init__(self, data_json: str, human_decision: str) -> None:

        self.filename = data_json
        self.human_decision = human_decision

        self.dataDict = self.__process_file()

        #* the behavior decision will be determined as the Determiner object is instantiated.
        self.behavior_obj = self.determine_behavior()
        
    def __process_file(self):
        #* Making the json input workable

        with open(self.filename, 'r') as file:
            dataDict = json.load(file)

        return dataDict


    def get_data(self, parameter: str, as_array: bool = False):
        """
        Method to retrieve data from the dictionary
        """

        # checking if the input parameter is correct
        # if parameter not in list(next(iter(self.dataDict.items()))[1].keys()):
        if parameter not in self.dataDict:
            raise KeyError("Input parameter was not found.")
        
        if as_array:
            # return [ v[parameter] for v in iter(self.dataDict.values()) ]
            return self.dataDict[parameter]

        # return { k: v[parameter] for k,v in self.dataDict.items() }
        return 1
    
    def determine_behavior(self):
        """
        Method to determine the impact behavior from the input file"""
        
        #todo   Any changes to the behavior-determining method must be implemented here
        #todo   
        #todo   WIP:
        #todo       - getting indices of particles in contact with the disc at a timeframe (hard)
        #todo       - making voting less binary --> changing the voting values based on thresholds
        #todo       - a reasonable tie-breaker algorithm
        #todo   
        #todo   
        
        #* Getting attributes
        num_timesteps = len(self.dataDict[next(iter(self.dataDict.keys()))])
        # num_timesteps = 201

        #* disc data
        disc_xs = np.array(self.get_data('disc_xs', as_array=True))
        disc_ys = np.array(self.get_data('disc_ys', as_array=True))
        try:
            disc_r = np.array(self.get_data('disc_rs', as_array=True))[0]
        except KeyError:
            disc_r = np.array(self.dataDict['disc_r'])
        
        #* disc particles contact
        contact_pIDs = self.dataDict['contact_pIDs']

        #* bed data
        crater_xs = np.array(self.get_data('crater_xs', as_array=True))
        crater_ys = np.array(self.get_data('crater_ys', as_array=True))
        mound_xs = np.array(self.get_data('mound_xs', as_array=True))
        mound_ys = np.array(self.get_data('mound_ys', as_array=True))

        #* finding the peaks of the disc
        peaks, _ = find_peaks(
            disc_ys,
            distance = 40,
        )
        try:
            max_disc_y = disc_ys[peaks][0]
        except IndexError:
            max_disc_y = median(disc_ys)

        #* initializing the decision dictionary
        
        decisionDict = {
            'FS' : 0,
            'RO' : 0, # decisionDict offset
            'RC' : 0
        }
        reasons = [f"{list(decisionDict.values())} : start"]

        #* airborne state analysis
        
        # vel_xs = np.array(self.get_data('disc_vx', as_array=True)) #! not in old datafiles
        try:
            vel_xs = np.array(self.get_data('disc_vx', as_array=True))
        except KeyError:
            vel_xs = np.gradient(disc_xs,num_timesteps)
            self.dataDict['disc_vx'] = vel_xs

        
        #! vx, vyalready inclded in dataDict for new dataset
        #* adding the data to the decisiondict
        acc_xs = np.gradient(vel_xs,num_timesteps)*(1e8)

        self.dataDict['disc_ax'] = acc_xs
        
        length = 0
        length_array = []

        for idx, (acc,vel) in enumerate(zip(acc_xs, vel_xs)):
            
            #ignoring cases where the velocity is effectively zero
            if idx == 0 or ( ( -1e-06 < vel < 1e-06 ) or (vel_xs[0]*0.97 < vel < vel_xs[0]*1.03) ):
                continue
            
            #for cases where acceleration is effectively zero
            if -1e-2 < acc < 1e-2:
                # length += 1
                #! since we are skipping timesteps
                length += 2

            else:
                length_array.append(length)
                length = 0

        #* initializing certain behavior indicators
        switches = ['up']
        impact_time = None
        surpasses = False
        crater_out = False

        for timestep, (mound_h, disc_h, mound_x, disc_x, crater_x, acc_x) in enumerate(zip(mound_ys,disc_ys,mound_xs,disc_xs,crater_xs,acc_xs)):

            # if at any point the difference between the mound height and the disc height is larger than the diameter -> ricochet
            # if (disc_r*(1197+8075)/8075) < disc_h-mound_h:
            if (disc_h - disc_r*(1197+8075)/8075) > mound_h:
                # behavior = "RC"

                # if this never happened then do this
                if (decisionDict["RC"] == 0) and (len(switches) > 1):
                    
                    decisionDict["FS"] -= 1
                    decisionDict["RO"] -= 1
                    decisionDict["RC"] += 1
                    reasons.append(f"{list(decisionDict.values())} : disc_h-mound_h > disc_r")

            #? defining impact time
            if acc_x != 0:
                if impact_time is None:
                    impact_time = timestep
            
            # if the disc gets far away from the crater
            if (disc_x - 3*disc_r) > crater_x and crater_out is False:
                crater_out = True
                crater_comp_x, disc_comp_x = crater_x, disc_x-3*disc_r

            # if at any point the disc surpasses the mound
            if disc_x > mound_x and surpasses is False:
                surpasses = True

            # checking switches in height between the mound and the disc
            if disc_h < mound_h:
                if switches[-1] != 'down':
                    switches.append('down')

            if disc_h > mound_h:
                if switches[-1] != 'up':
                    switches.append('up')
        
        #* voting based on certain conditions
        #* ----------------------------------
        if len(switches) < 3: #* low priority because some lower attack angles don't ever cross paths.
            # behavior = "FS"
            decisionDict["FS"] += 1
            # decisionDict["RO"] -= 1
            # decisionDict["RC"] -= 1
            reasons.append(f"{list(decisionDict.values())} : len(switches) < 3")
        else:
            decisionDict["FS"] -= 1
            reasons.append(f"{list(decisionDict.values())} : len(switches) > 3 (switches: {len(switches)})")

        #* if the impactor moves a significant distance away from the impact crater
        if crater_out is True:
            decisionDict["FS"] -= 1
            reasons.append(f"{list(decisionDict.values())} : crater_out is True (disc_x-3*disc_r/crater_x = {disc_comp_x:.3f}/{crater_comp_x:.3f})")
        else:
            decisionDict["FS"] += 1
            reasons.append(f"{list(decisionDict.values())} : crater_out is False")
        
        #* if the bottom of the impactor is higher than the max height of the mound
        max_mound = max(mound_ys)
        if max_mound < max_disc_y-disc_r:
            # behavior = "RO"
            decisionDict["FS"] -= 1
            decisionDict["RO"] -= 1
            # decisionDict["RC"] += 1 
            decisionDict["RC"] += int(( ((max_disc_y-disc_r)-max_mound)  / max_mound )//0.1)
            reasons.append(f"{list(decisionDict.values())} : max_mound < max_disc_y - disc_r ({max_mound/max_mound} < {(max_disc_y-disc_r)/max_mound:.3f} --> +{int(( ((max_disc_y-disc_r)-max_mound)  / max_mound )//0.1)})")
        else:
            decisionDict["RC"] += int(( ((max_disc_y-disc_r)-max_mound)  / max_mound )//0.1) #(accounting for negative values as well)
            # decisionDict["RO"] -= 1

            reasons.append(f"{list(decisionDict.values())} : max_mound > max_disc_y - disc_r ({max_mound/max_mound} > {(max_disc_y-disc_r)/max_mound:.3f} --> {int(( ((max_disc_y-disc_r)-max_mound)  / max_mound )//0.1)})")


        #* analyzing the airborne case
        try:
            length = max(length_array)
        
        # this usually doesn't happen very often, if ever
        except ValueError:
            length = 0
            decisionDict["FS"] += 1
            decisionDict["RO"] += 1
            decisionDict["RC"] -= 1
            reasons.append(f"{list(decisionDict.values())} : length = 0 (ValueError Raised)")


        #* if the impactor never surpasses the mound
        if surpasses is False:
            # behavior = "FS"
            if len(switches) < 3:
                decisionDict["FS"] += 2
                reasons.append(f"{list(decisionDict.values())} : surpasses is False AND len(switches) < 3")
            
            decisionDict["FS"] += 2
            decisionDict["RO"] -= 1
            decisionDict["RC"] -= 1
            reasons.append(f"{list(decisionDict.values())} : surpasses is False")
        
        #* airborne
        if length > 1: #! starting at just 1% of the total simulation time
            # behavior = 'RC'
            # decisionDict["FS"] -= 1
            # decisionDict["RO"] -= 1
            decisionDict["RC"] += length//6 #* by threshold
            reasons.append(f"{list(decisionDict.values())} : length > 1 (length = {length}) --> +{length//6}")
        else:
            decisionDict["FS"] += 1
            decisionDict["RO"] += 1
            decisionDict["RC"] -= 1
            reasons.append(f"{list(decisionDict.values())} : length < 1 (length = {length})")

        #* implementing stuff using contact pIDs
        # the number of unique particles encountered by the disc
        unique_pIDs = len(contact_pIDs)
        #    reasons.append(f"{list(decisionDict.values())} : unique_pID = {unique_pIDs} > 26 --> -{abs(unique_pIDs - 26)//6}")
        
        # the minimum for RO is at around 25
        min_RO = 25
        if unique_pIDs > min_RO:
            decisionDict["RO"] += abs(unique_pIDs-min_RO)//4
            decisionDict["FS"] -= 1
            decisionDict["RC"] -= 1
            reasons.append(f"{list(decisionDict.values())} : unique_pID = {unique_pIDs} > {min_RO} --> {abs(unique_pIDs - 30)//4}")

        #* behavior is the one with the most votes
        for key, bias in decisionDict.items():
            if bias == max(decisionDict.values()):
                behavior = key
                break

        #* in the case that there is a tie, pick RO
        #todo 
        #todo Implement length of contact as a factor of decision
        #todo 

        if (decisionDict["FS"] == decisionDict["RO"]) and (decisionDict["RO"] > decisionDict["RC"]):
            behavior = "RO"
            reasons.append(f"{list(decisionDict.values())} : tiebreaker FS, RO -> RO")
        if (decisionDict["RO"] == decisionDict["RC"]) and (decisionDict["RO"] > decisionDict["FS"]):
            behavior = "RC"
            reasons.append(f"{list(decisionDict.values())} : tiebreaker RC, RO -> RC")

        #* shifting the votes to make the minimum zero 
        shift_by = min( decisionDict.values() )
        for key in decisionDict:
            decisionDict[key] -= shift_by
        
        # working with only the top 2 choices
        interm = list(decisionDict.values())
        interm.remove(0)         

        return _DecisionPackage(
            iteration=self.filename[-13:-5],
            computer_decision=behavior,

            # computing confidence
            confidence=round( (abs(interm[0]-interm[1])/max(interm) ), 2 ),

            #todo   The problem with this is that this yields values of 100% that seem unreasonable
            #todo       - try changing it so that it is something like-->(current votes)/(total possible votes)

            human_decision=self.human_decision,
            decisionDict=decisionDict,

            # conditional datas
            contact_pIDs=len(self.dataDict['contact_pIDs']),
            airborne=length,
            switches=len(switches),
            surpasses=surpasses,
            crater_out=crater_out,
            impact_time=impact_time,
            reasons=reasons,
            datas=self.dataDict,
            num_timesteps=num_timesteps,
        )


@dataclass(frozen=True)
class _DecisionPackage:
    iteration: str
    computer_decision: str
    confidence: float
    human_decision: str
    decisionDict: dict
    contact_pIDs: int
    airborne: int
    switches: int
    surpasses: bool
    crater_out: bool
    impact_time: int
    reasons: list[str]
    datas: dict
    num_timesteps: int

class Visualizer:

    def __init__(self, data_package: _DecisionPackage) -> None:
        self.data_package = data_package


    def path_plots(self, path: str, format: str):
        #todo   Make this a method within some some other "plotter" class or something.
        #todo

        package = self.data_package
        
        # the timesteps involved
        ts = range(package.num_timesteps)

        #* Plotting
        fig, (
            (ax1, ax2, ax3),
            (ax4, ax5, ax6)
        ) = plt.subplots(2,3, figsize = (14,10))

        fig.suptitle(
            f"{package.iteration}; human/comp: [{package.human_decision}/{package.computer_decision}] (confidence: {package.confidence})",
            fontweight = 'bold'
        )

        fig.patch.set_alpha(1.0)

        #* disc height vs mound height
        ax1.plot(
            ts,
            package.datas['mound_ys'],
            'r-',
            label = "mound height"
        )
        ax1.plot(
            ts,
            package.datas['disc_ys'],
            'b-',
            label = "disc height\nswitches: {}".format(package.switches)
        )
        ax1.grid(visible = True)
        ax1.set_title("Heights vs Time")
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Height")
        ax1.legend()

        #* disc x vs mound x
        ax2.plot(
            ts,
            package.datas['mound_xs'],
            'r-',
            label = "mound x"
        )
        ax2.plot(
            ts,
            package.datas['disc_xs'],
            'b-',
            label = "disc x"
        )
        ax2.grid(visible = True)
        ax2.set_title("X-positions vs Time")
        ax2.set_xlabel("Time")
        ax2.set_ylabel("X-position")
        ax2.legend()

        # Path comparison plot (mound vs disc)
        ax3.plot(
            #mound data before the impact time is not significant
            package.datas['mound_xs'][package.impact_time:],
            package.datas['mound_ys'][package.impact_time:],
            'r-',
            label = "mound pos"
        )
        ax3.plot(
            package.datas['disc_xs'],
            package.datas['disc_ys'],
            'b-',
            label = "disc pos"
        )
        ax3.grid(visible = True)
        ax3.set_title("X and Y positions")
        ax3.set_xlabel("X")
        ax3.set_ylabel("Y")
        ax3.legend()

        # vx vs time
        ax4.plot(
            ts,
            package.datas['disc_vx'],
            'k-',
            label = f"x-velocity (length={package.airborne})",
        )
        ax4.grid(visible = True)
        ax4.set_title("Disc X-Velocity")
        ax4.set_xlabel("Time")
        ax4.set_ylabel("X-Velocity")
        ax4.legend()

        #acc vs time
        ax5.plot(
            ts,
            package.datas['disc_ax'],
            'k-',
            label = f"x-acc (length={package.airborne})",
        )
        ax5.grid(visible = True)
        ax5.set_title("Disc X-Acceleration")
        ax5.set_xlabel("Time")
        ax5.set_ylabel("X-Acceleration")
        ax5.legend()

        #acc vs time
        ax6.plot(
            ts,
            package.datas['crater_ys'],
            '-r',
            label = "Crater Height",
        )
        ax6.plot(
            ts,
            package.datas['disc_ys'],
            '-b',
            label = f"Disc Height\nCrater out: {package.crater_out}",
        )
        ax6.grid(visible = True)
        ax6.set_title("Disc Y vs Crater Y")
        ax6.set_xlabel("Time")
        ax6.set_ylabel("Y-pos")
        ax6.legend()

        plt.savefig(f"{path}/path_{package.iteration}.{format}", format = format)
        plt.close()

        
