from operator import itemgetter
from statistics import median
from time import perf_counter
import numpy as np
from math import dist


class RegFile:
    """
    Class for just the bed. The disc impactor will be ignored, and will be instantiated in a separate class"""
    # indices for specific things
    DIM_OFFSET = 5
    DATA_OFFSET = 8

    # this changes according to the disc id
    __DISC_ID = 108614

    def __init__(self, filename: str) -> None:
        self.filename = filename

        #* jk this works
        with open(self.filename, 'r') as file:
            lines = file.readlines()
        self.lines = lines

        self.box_width, self.box_height = self.__boxDims()

        self.ts = self.get_timesteps()
        # self.idx0, self.timestep0 = next(iter( self.ts_dict.items() ))
        self.idx0, self.timestep0 = self.ts[0]


    def __boxDims(self):
        return ( float(line.split().pop(1)) for line in self.lines[self.DIM_OFFSET: self.DIM_OFFSET+2] )

    def get_timesteps(self) -> list[tuple[int, int]]:
        """
        Method to get the timesteps as a dictionary with format. Returns tuple (index , timestep)"""

        # return { idx+1 : int(self.lines[idx+1].split()[0])  for idx, line in enumerate(self.lines) if line == "ITEM: TIMESTEP\n" }        
        return [ (idx+1 , int(self.lines[idx+1].split()[0]))  for idx, line in enumerate(self.lines) if line == "ITEM: TIMESTEP\n" ]

    def __get_bed_at(self, idx = None, timestep = None, include_only: list[int] = None):
        """
        Method to get the particles in the initial bed (particle bed at first timestep) 
            - idx: int
                - the index where the data section starts (where the timestep is explicitly set)
            - timestep: int
                - parameter to see if the timestep passed in matches the timestep at the index
        
        Returns dictionary that looks like:
        
                T_dict = {
                    particleID: {
                        x : x_coord,
                        y : y_coord,
                        r : radius
                    }
                }
                
        """

        # checking for default values
        if (idx is None) or (timestep is None):
            idx, timestep = self.idx0, self.timestep0

        #* if the input is empty, get all the pIDs
        if include_only is None:
            
            include_only = list(range(self.__DISC_ID))

        # checking if the timestep is correct
        if timestep != int(self.lines[idx]):
            raise IndexError(f"The TIMESTEP at {idx} does not match the timestep passed in the argument: {timestep}(arg) != {self.lines[idx]}")

        # index where the actual data starts printing
        data_idx = idx + self.DATA_OFFSET

        # initializing the dictionary
        timeDict = {}
        
        # looping through the lines
        try:
            while self.lines[data_idx] != "ITEM: TIMESTEP\n": #looping until the next timestep

                data_line = self.lines[data_idx].split()

                # ignoring the disc data
                if int(data_line[0]) == self.__DISC_ID:
                    data_idx += 1
                    continue
                if int(data_line[0]) in include_only:
                    # data_idx += 1
                    # continue

                    # assigning the values from the line into a dictionary
                    idxDict = {
                        'x' : float(data_line[2])*self.box_width,
                        'y' : float(data_line[3])*self.box_height,
                        # 'r' : float(data_line[-1])
                        'r' : float(data_line[5]) #! this should change accordingly
                    }

                    # assigning the dictionary as a value to a key that's the particle id
                    #* data_line[0] --> pID
                    timeDict[int(data_line[0])] = idxDict
                data_idx += 1

        except IndexError:
            pass

        # print(f"time: {end-start: .4f}   Num Particles: {len(include_only)}")
        return timeDict

    def get_init_bed(self):
        """
        Method to get the bed data at the first timestep"""
        return _InitBed(self.__get_bed_at())

    def get_bed(self, idx: int, timestep: int, include_only: list[int]):
        """
        Method to get the bed data at any given timestep.
        
            - the arguments are mandatory, the bed size is smaller"""
        return _Bed(self.__get_bed_at(idx, timestep, include_only))

        # return timeDict


class DiscFile(RegFile):
    """
    Class to do stuff on the disc file. Inherits things like timesteps and such from its parent class.
    """
    def __init__(self, filename: str):
        super().__init__(filename)
        self.disc_file = filename

        self.dataDict = self.__get_dict()
        
        # timestep for cutoff
        self.ts_cutoff = max([key for key in self.dataDict])
        self.ts = [ key for key in self.dataDict ]
    
    #todo   
    #todo    Cut the data collection when the impactor bounces off of the wall     
    #todo       - communicate this through the Regfile thing as well
    #todo


    def __make_data(self, idx: int, timestep: int) -> dict:
        """
        Method to get the particles in the initial bed (particle bed at first timestep) 
            - idx: int
                - the index where the data section starts (where the timestep is explicitly set)
            - timestep: int
                - parameter to see if the timestep passed in matches the timestep at the index
        
        Returns dictionary that looks like:
        
                disc_dict = {
                    timestep: {
                        m : mass,
                        x : x_coord,
                        y : y_coord,
                        r : radius,
                        vx : vel_x, 
                        vy : vel_y
                    }
                }
                
        """
        # checking for timestep
        if timestep != int(self.lines[idx]):
            raise IndexError(f"The TIMESTEP at {idx} does not match the timestep passed in the argument: {timestep}(arg) != {self.lines[idx]}")

        # the index where the data stream starts
        data_idx = idx + self.DATA_OFFSET

        data_line = self.lines[data_idx].split()

        # returning a key-value pair that contains the disc data
        return {
            timestep: {
                'disc_m' : float(data_line[0]),
                'disc_xs' : float(data_line[1])*self.box_width,
                'disc_ys' : float(data_line[2])*self.box_height,
                'disc_rs' : float(data_line[4]),
                'disc_vx' : float(data_line[5]),
                'disc_vy' : float(data_line[6])
            }
        }
    
    def __get_dict(self):
        """
        Method to initialize the self.dataDict
            - Args: None
            - Returns:
                - `dataDict` : with the appropriate timesteps
        """

        #initializing the dataDict attribute
        dataDict = {}

        # for time in self.ts:
        for idx, time in enumerate(self.ts):

            # reducing the number of timesteps to 0,2,4,...etc
            if idx%2 == 1:
                continue

            dataDict.update(self.__make_data(*time))
            
            #todo   Define cases here for which the loop wil break
            #todo       - if the ball bounces off the wall (if vx goes from + to -)
            #todo       - if the ball stops (if magnitude v is 0 for a good amount of time)
            #todo       - if disc_x is very close to the wall
            
            # the velocity magnitude
            v_magnitude = (dataDict[time[1]]['disc_vx']**2 + dataDict[time[1]]['disc_vy']**2)**(0.5)
            stopped_for = 0
            
            # bouncing off the wall
            #* this mostly seems to cut off the simulation
            if dataDict[time[1]]['disc_vx'] < 0:
                return dataDict

            # if the impactor stops at the bed
            if v_magnitude < 1e-4:
                stopped_for += 1
                if stopped_for > 10: # if the disc stops for at least 5% of the timeframe
                    return dataDict

            # stopping if disc is very close to the wall
            if (dataDict[time[1]]['disc_xs'] + dataDict[time[1]]['disc_rs']) > 0.98*self.box_width:
                return dataDict

        return dataDict

    def get_data(self, parameter: str , as_array: bool = False) -> dict:
        """
        Method to get a dictionary that only includes data of the parameter passed in
        """
        
        # checking if the input parameter is correct
        if parameter not in list(next(iter(self.dataDict.items()))[1].keys()):
            raise KeyError("Input parameter was not found.")
        
        if as_array:
            return [ v[parameter] for v in iter(self.dataDict.values()) ]

        return { k: v[parameter] for k,v in self.dataDict.items() }





class _InitBed:
    """
    Class to apply conditions on the initial particle bed
    """

    def __init__(self, initDict: dict):
        """
        get the timeDict generated by the Bed-ish class
        """
        self.__initDict = initDict

        # self.__Profile = self.__makeProfile() IDK if there's a need for this
        

    def make_profile(self):
        
        """
        Method that returns a profile object based on the conditions passed in.
            - `condition_bed` : a list of indices that satisfy a certain condition
            - Returns : `P_Profile` object
        """
        condition_bed = self.is_greater('y', 0.14)

        return P_Profile(
            np.array([
                [v for k,v in self.get_data('x').items() if k in condition_bed],
                [v for k,v in self.get_data('y').items() if k in condition_bed],
                [v for k,v in self.get_data('r').items() if k in condition_bed]
            ]).T
        )

    def get_input(self):
        """
        Method to get access to the input dictionary
        """
        return self.__initDict

    def get_data(self, parameter: str , as_array: bool = False) -> dict:
        """
        Method to get a dictionary that only includes data of the parameter passed in
        """
        this = self.__initDict.items()
        # checking if the input parameter is correct
        if parameter not in list(next(iter(self.__initDict.items()))[1].keys()):
            raise KeyError("Input parameter was not found.")
        
        if as_array:
            return [ v[parameter] for v in iter(self.__initDict.values()) ]

        return { k: v[parameter] for k,v in self.__initDict.items() }

    def get_surface(self) -> list[int]:
        """
        Returns a list of particle IDs for the surface particles
        """

        #* looking at the particles higher than 80% of the max height --> that is where the surface would be

        profile = self.make_profile()
        
        # looping through the dictionary to find the surface partices
        for key in self.__initDict:
            self.__initDict[key]['surface'] = profile.P_is_surface(self.__initDict[key]['x'], self.__initDict[key]['y'])
        
        
        return [ k for k, v in self.__initDict.items() if v['surface'] == 1 ]


    #* conditionals
    def is_greater(self, parameter: str, val: float) -> list[int]:
        """
        Returns a list of particle IDs for which the values for the specified parameters are 
        greater than the value passed in
        """
        return [ k for k,v in self.__initDict.items() if v[parameter] > val ]

    def is_lesser(self, parameter: str, val: float) -> list[int]:
        """ 
        Returns a list of particle IDs for which the values for the specified parameters are 
        lesser than the value passed in
        """
        return [ k for k,v in self.__initDict.items() if v[parameter] < val ]

    def is_within(self, parameter: str, low: float, high: float) -> list[int]:
        """
        Returns a list of particle IDs for which the values for the specified parameters are 
        within the high and the low values passed in
        """
        return [ k for k,v in self.__initDict.items() if (low < v[parameter] < high) ]

    def is_within_2d(self, left: float, right: float, down: float, up: float) -> list[int]:
        """
        Returns a list of particle IDs for which the values for the specified parameters are 
        within the range of values passed in
        """

        return [ k for k,v in self.__initDict.items() if ((left < v['x'] < right) and (down < v['y'] < up))]

    def is_within_circle(self, origin: tuple[float,float], radius: float) -> list[int]:
        """
        Returns a list of particle IDs within a circular region defined by the arguments
            - Arguments:
                - `origin` : the center point of the circular region. Must be in the form (x,y)
                - `radius` : the radius of the circular region    
        """
        
        return [ k for k,v in self.__initDict.items() if dist([v['x'],v['y']],[*origin]) < radius ]

    def is_within_circle_region(self, origin: tuple[float,float], radius_inner: float, radius_outer: float) -> list[int]:
        """
        Returns a list of particle IDs within a circular region defined by the arguments
            - Arguments:
                - `origin` : the center point of the circular region. Must be in the form (x,y)
                - `radius_outer` : the outer radius of the circular region
                - `radius_inner` : the inner radius of the circular region
        """
        
        return [ k for k,v in self.__initDict.items() if  radius_inner < dist([v['x'],v['y']],[*origin]) < radius_outer ]

    def is_array_surface(self, array: list[float]) -> list[int]:
        """
        Returns a list of particle IDs for which the values of the surface particles are
        closest to the coordinates in the array passed in.
            - Arguments:
                - `array` : a list of coordinate values that the particles should be found in on the surface
        """
        
        # getting a dictionary for the surface particles
        # surfaceDict = { k:v for k,v in self.__initDict.items() if k in self.get_surface()}
        surface_idx = self.get_surface()

        target_idx = []
        for point in array:
            target_idx.append(
                # min( self.get_surface(), key = lambda i: abs(point - self.__initDict[i]['x']) )
                min( surface_idx, key = lambda i: abs(point - self.__initDict[i]['x']) )
            )

        return target_idx

    def is_array(self, direction: str, array: list[float], hold: float) -> list[int]:
        """
        Returns a list of particle IDs for which the values of the particles are
        closest to the coordinates in the array passed in
            - Arguments:
                - `direction` : character argument specifying wheter or not the array of particles is horizontal or vertical
                    - `'h'` for horizontal, `'v'` for vertical
                - `array` : list of coordinate values that the particles should be found in
                - `hold` : the single position that the particles would share
        """

        #todo make this different for different directions
        if direction == 'h':
            reduced_search = self.is_within('y', hold-0.01, hold+0.01)

            mins_idx = []
            for point in array:
                mins_idx.append(
                    min(reduced_search, key = lambda i: dist( (point, hold), (self.__initDict[i]['x'], self.__initDict[i]['y']) ) )
                )
        if direction == 'v':
            reduced_search = self.is_within('x', hold-0.01, hold+0.01)

            mins_idx = []
            for point in array:
                mins_idx.append(
                    min(reduced_search, key = lambda i: dist( (hold, point), (self.__initDict[i]['x'], self.__initDict[i]['y']) ) )
                )

        return mins_idx 


    def is_mesh(self, array_x: list[float], array_y: list[float]) -> list[int]:
        """
        Returns a list of particle IDs for which the values of the particles are
        closest to in the given mesh passed in
        """

        #todo Call the self.is_array function multiple times I guess...

        pass
        


class _Bed(_InitBed):
    """
    An instance of the _Bed class really doesn't have to be a "bed". \
        It is a subset of the total particles in the bed that met certain conditions at the initial bed.

    Just like the _InitBed, the surface is automatically computed.
    """

    #todo Have it make an extended dictionary that has 
    #todo   - dict['is surface']
    #todo   - dict['near particles count']

    def __init__(self, bedDict) -> None:
        super().__init__(bedDict)
        self.__bedDict = self.get_input()

        #* call the profile just at the spot --> the parent class (_InitBed) does not generate a surface upon
        #* instantiation, but the child class (_Bed) does.
        self.profile = self.make_profile()
        self.surface = self.get_surface()

        #* kinda need this i ugess
        self.crater = self.get_crater()

    #* these methods are only in the child class
    def get_mound(self ) -> tuple[float,float]:
        """
        Method to get the mound of the bed
        """

        start = perf_counter()
        for key in self.__bedDict:
            self.__bedDict[key]['near_count'] = self.profile.P_count_near_particle(
                self.__bedDict[key]['x'], self.__bedDict[key]['y'], 4
            )

        mound_y = median(
            sorted(
                [ val['y'] for val in self.__bedDict.values() if val['near_count'] > 6 and val['x'] > self.crater[0] ][-9:]            
            )
        )
        xs = self.get_data('x', as_array=True)

        mound_x = xs[
            min( range(len(xs)) ,
            key = lambda i: abs(xs[i]-mound_y) )
        ]

        end = perf_counter()

        return mound_x, mound_y


    def get_crater(self ) -> tuple[float,float]:
        """
        Method to get the crater of the bed
        """
        possible_crater = sorted(
            [
                [self.__bedDict[key]['x'], self.__bedDict[key]['y']] for key in self.surface
            ],
            key = itemgetter(1)
        )

        surface_xs = [pick[0] for pick in possible_crater[:5]]
        surface_ys = [pick[1] for pick in possible_crater[:5]]

        dip_y = median(surface_ys)        
        
        dip_x = surface_xs[
            min( range(len(surface_xs)), 
            key = lambda i: abs(surface_xs[i] - dip_y) )
        ]

        end = perf_counter()


        return dip_x, dip_y


#* profile
class P_Profile:
    """
    For various operations/analysis on particle profiles

    For initialization, there needs to be an input 2d array that consists of the following:
        - A 2D array with dimensions of at least <number of particles> x 3 where:
            - Column 1 ( array[n][0] ): Particle x coordinate
            - Column 2 ( array[n][0] ): Particle y coordinate
            - Column 3 ( array[n][0] ): Particle radius
    """

    def __init__(self, particle_positions) -> None:

        #particle
        self.particle_positions = particle_positions
        self.num_particles = len(particle_positions)
        

        

    def P_square_count(self, current_x, current_y, side_length) -> int:
        """
        method to find the particle counts per region
        """

        #defining the region
        lower_x = current_x - side_length/2
        upper_x = current_x + side_length/2

        lower_y = current_y - side_length/2
        upper_y = current_y + side_length/2

        #reducing the region to the one
        reduced_positions = [pos for pos in self.particle_positions if (pos[1] < upper_y and pos[1] > lower_y)]

        #the initial count is 0 because it's looking over a specific region not a particle
        count = 0
        for position in reduced_positions:

            #counting particles that are within the box
            if (position[0] < upper_x and position[0] > lower_x):
                count += 1
        
        return count

    def P_circle_count(self, current_x, current_y, radius_multiplier) -> int:
        """
        Method to find the count the number of particles in a region"""
        count = 1

        for params in self.particle_positions:
            
            if (params[0] == current_x and params[1] == current_y):
                continue
            if dist( (current_x, current_y), (params[0], params[1]) ) < radius_multiplier*params[2]:
                count += 1

        return count


    def P_nearest(self, particle_x, particle_y) -> float:
        """
        method to find the distance to the nearest particle"""

        #importing the dist() function

        #for a scale distance, the maximum possible distance between 2 particles.
        MAX_DIST = 1 
        distance = MAX_DIST

        for pos in self.particle_positions:

            #stopping the minimum distance from being zero
            if (pos[0] == particle_x and pos[1] == particle_y):
                continue

            if dist( (pos[0], pos[1]) ,(particle_x, particle_y) ) < distance:
                distance = dist( (pos[0], pos[1]),(particle_x,particle_y) )
        
        # print(distance)
        return distance

    def P_count_near_particle(self, particle_x, particle_y, radius_multiplier) -> int:
        """
        Method to count the number of particles near a given particle
        given a particle's position and a valid radius nearby
        
            - the radius_multiplier argument is the scale factor that multiplies the radius of the particle
            - doesn't count itself as a particle
        """

        #scale factor for radius
        R_SCALEFACTOR = radius_multiplier

        #looping through each particle
        count = 1#counting itself as 1 particle
        for params in self.particle_positions:
            
            #the distance within which to count
            distance = params[2]*R_SCALEFACTOR

            #ignoring itself as a count
            if (params[0] == particle_x and params[1] == particle_y):
                continue
            
            #counting if the particle is within the region
            if dist( (params[0], params[1]) ,(particle_x, particle_y) ) < distance:
                count += 1

        #if there are 2 or less particles (including itself) in the area, it's just set to 1
        if count < 3:
            return 1

        return count
    

    def P_is_surface(self, particle_x, particle_y)->int:
        """
        method that tells whether or not a particle is a surface particle
            - (returns 1 if there are less than 2 particles above a given particle)"""

        above_particles_count = 0
        for params in self.particle_positions:

            #ignoring anything below
            if params[1] < particle_y:
                continue

            #counting the particle if it's x is within the diameter
            if ( params[0] > particle_x-params[2] and params[0] < particle_x+params[2] ):
                above_particles_count += 1

            #if there are 2 or more particles above, it's not a surface particle.
            if above_particles_count > 1:
                return 0

        return 1
    


    #todo   The julia functions would go in here. The arrays would be passed in, and return values would be
    #todo   received in the form of arrays..?
