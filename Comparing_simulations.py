# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 15:53:43 2020

@author: josec
"""

#Import relevant libraries
import pandas as pd
import numpy as np
import random
import string
import matplotlib.pylab as plt
import matplotlib.patches as patches
import matplotlib as mpl
import pyclipper
import seaborn as sns
mpl.style.use(['seaborn-white'])

#Create filenames
drywalls_filename = 'df_drywalls.csv'
walls_filename = 'df_walls_height_8.csv'
studs_filename = 'df_studs_new.csv'
plates_filename = 'df_plates.csv'
doors_filename = 'df_doors_new.csv'
windows_filename = 'df_windows_new.csv'

#Read files
df_walls = pd.read_csv(walls_filename)
df_studs = pd.read_csv(studs_filename)
df_plates = pd.read_csv(plates_filename)
df_drywalls = pd.read_csv(drywalls_filename)
df_doors = pd.read_csv(doors_filename)
df_windows = pd.read_csv(windows_filename)

# Create class Position
class Position(object):
    """
    A Position represents a location in a two-dimensional wall.
    """
    def __init__(self, x, y):
        """
        Initializes a position with coordinates (x, y).
        """
        self.x = x
        self.x = round(x, 4)
        self.y = round(y, 4)
    def getX(self):
        """
        Returns position coordinate in the X axis.
        """
        return self.x  
    def getY(self):
        """
        Returns position coordinate in the Y axis.
        """
        return self.y
    def getNewPosition(self, delta_x, delta_y):
        """
        Computes and returns the new Position after a single clock-tick has
        passed with this object as the current position.
        
        Does NOT test whether the returned position fits inside the wall.
        
        delta_x: delta in the X axis.
        delta_y: delta in the y axis.
        
        Returns: a Position object representing the new position.
        """
        old_x, old_y = self.getX(), self.getY()
        
        # Calculate new coordinates
        new_x = np.round(float(old_x + delta_x), 4)
        new_y = np.round(float(old_y + delta_y), 4)
        
        return Position(new_x, new_y)
    def __str__(self):  
        return "(%0.2f, %0.2f)" % (self.x, self.y)


class Drywall(object):
    def __init__(self, name, height, width):
        self.name = name
        self.height = height
        self.width = width
        self.position = Position(0,0)
        self.ID = generateID(name + '_')
        self.vertical_cut = 0
        self.horizontal_cut = 0
        self.door_clipper = 0
        self.window_clipper = 0
        self.no_cuts = 0
        self.cutting_losses=[]
        self.cutting_loss_position = Position(0, 0)
        self.cutting_loss_width = 0
        self.cutting_loss_height = 0
    def getName(self):
        return self.name    
    def getHeight(self):
        return self.height    
    def getWidth(self):
        return self.width        
    def getArea(self):
        return self.height * self.width
    def getNominalArea(self):
        if '4x8' in self.name:
            return float(4*8)
        if '4x10' in self.name:
            return float(4*10)
        if '4x12' in self.name:
            return float(4*12)
    def getID(self):
        return self.ID
    def getNoCuts(self):
        return self.no_cuts        
    def setNoCuts(self, number):
        self.no_cuts = number
    def setDrywallWidth(self, width):
        self.width = width
    def setDrywallHeight(self, height):
        self.height = height
    def getPosition(self):
        return self.position
    def setPosition(self, position):
        self.position = position
    def getVerticalCut(self):
        return self.vertical_cut
    def getHorizontalCut(self):
        return self.horizontal_cut
    def getDoorClipper(self):
        return self.door_clipper
    def getWindowClipper(self):
        return self.window_clipper
    def setVerticalCut(self, vertical_cut):
        '''
        Parameters
        ----------
        vertical_cut : a list which contains [PositionX, PostionY, width, height]

        Returns
        A list
        -------
        '''
        if vertical_cut.getArea() != 0:
            self.vertical_cut = vertical_cut
        
    def setHorizontalCut(self, horizontal_cut):
        if horizontal_cut.getArea() != 0:
            self.horizontal_cut = horizontal_cut
    def setDoorCut(self, door_clipper):
        self.door_clipper = door_clipper
    def setWindowCut(self, window_clipper):
        self.window_clipper = window_clipper
        
    def setCuttingLosses(self, cutting_losses):
        self.cutting_losses.append(cutting_losses)
    def getCuttingLosses(self):
        return self.cutting_losses
    def getCuttingLossPosition(self):
        return self.cutting_loss_position
    def getCuttingLossWidth(self):
        return self.cutting_loss_width
    def getCuttingLossHeight(self):
        return self.cutting_loss_height    
   
    def __str__(self):
        return self.name + ' ' 

class Cut(object):
    def __init__(self, drywall, width, height, cut_type):
        self.drywall = drywall
        self.drywall_ID = drywall.getID()
        self.cname = generateID( self.drywall.getID() + '_' + 'Cut')
        self.height = height
        self.width = width
        self.cut_type = cut_type #Ex. Vertical cut, Horizontal cut, Door clipper, Window clipper
        self.position = Position(0,0)  
        self.no_cuts = 0
        self.wall_name = 0
    def getName(self):
        return self.cname    
    def getHeight(self):
        return self.height    
    def getWidth(self):
        return self.width        
    def getArea(self):
        return self.height * self.width
    def getType(self):
        return self.cut_type
    def getDrywall(self):
        return self.drywall
    def getID(self):
        return self.drywall_ID
    def getNoCuts(self):
        return self.no_cuts
    def setNoCuts(self, robot):
        self.no_cuts = self.no_cuts + 1
        robot.wall.changeCuts(self)
                
    def setWidth(self, width):
        self.width = width
    def setHeight(self, height):
        self.height = height
    def getPosition(self):
        return self.position
    def setPosition(self, position):
        self.position = position
    def getWallName(self):
        return self.wall_name
    def setWallName(self, wall_name):
        self.wall_name = wall_name
    def compliesArea(self, min_allowed_area, nominal_area):
        #print(self.getArea())
        #print(nominal_area)
        if (self.getArea() / nominal_area) >= min_allowed_area:
            return True
        else:
            return False
    def __str__(self):
        return self.cname + ' ' 

def CreateDrywallInstances(df_drywalls):
    '''
    Generate drywall instances on the class Drywall to easily access
    drywall properties.
    
    df_drywalls: complete drywall dataframe.
    
    Returns: a drywall_list which contains each drywall element as an
    #instance of the class Drywall.
    '''    
    drywall_list=[]
    for index, value in df_drywalls.iterrows():
        name = df_drywalls.loc[index, 'drywall_name']
        height = df_drywalls.loc[index, 'drywall_height']
        width = df_drywalls.loc[index, 'drywall_width']
        drywall_list.append(Drywall(name, height, width))
    return drywall_list


class Stud(object):
    def __init__(self, name, locationX, function):
        self.name = name
        self.locationX = locationX
        self.function = function
    def getName(self):
        return self.name
    def getFunction(self):
        return self.function
    def getLocationX(self):
        return self.locationX 
    def getLocationRange(self):
        '''
        stud_location_range: stud position (x +- 0.0625').
        stud_width: 1.5" (0.125')
        '''
        min_value = self.locationX - 0.0625
        max_value = self.locationX + 0.0625
        stud_location_range = np.arange(min_value, max_value)
        #print(stud_location_range)
        return stud_location_range
    def __str__(self):
        return self.name + self.function + ' <LocationX: ' + str(self.locationX) + '>'


#Generate Stud Instances
def CreateStudInstances(df_grouped):
    '''
    Generate stud instances on the class Stud to easily access
    stud properties.
    
    df_studs: complete stud dataframe.
    
    Returns: a stud_list which contains each stud element as an
    #instance of the class Stud.
    '''
    studs_list=[]
    
    for index, value in df_grouped.iterrows():
        name = df_grouped.loc[index, 'Studs.Stud.Attribute:ID']
        locationX = df_grouped.loc[index, 'Studs.Stud.InsertLocation.Attribute:X']
        function = df_grouped.loc[index, 'Studs.Stud.Attribute:Function']
    studs_list.append(Stud(name, locationX, function))
    return studs_list
    

class Wall(dict):
    '''
    A wall represents a rectangular grid made of studs and plates. It contains 
    drywall sheets located over studs and plates. It could be represented as a dictionary
    with Drywall Sheets as Keys and Stud Position / Stud ID as Values.
    Example: wall_M1 = {'Drywall_4x10':'Stud_68005'}
    
    A wall has a width and a height. At any particular time, a wall has certain number of 
    drywall sheets.
    '''
    def __init__(self, wall_name, length, height, studs_df, doors_df, windows_df):
        """
        Initializes a wall with the specified width and height.

        Initially, no drywall sheets have been placed on the wall.

        width: an integer > 0
        height: an integer > 0
        """
        self.wall_name = wall_name
        self.length = length
        self.height = height
        self.studs_df = studs_df
        self.doors_df = doors_df
        self.windows_df = windows_df
        self.joints = {}
        self.df_joints = pd.DataFrame(columns=['simulation', 'wall', 'x', 'y', 'length'])
        self.cutting_losses = []
        self.drywall_dataframe = pd.DataFrame(columns=['simulation', 'wall', 'drywall_ID', 'name', 'start_point_x', 'start_point_y', 'height', 'width', 'vertical_cut', 'horizontal_cut', 'door_clipper', 'window_clipper', 'no_cuts'])
        self.waste_dataframe = pd.DataFrame(columns=['simulation', 'wall', 'drywall_ID', 'drywall_object', 'cut_object','name', 'start_point_x', 'start_point_y', 'height', 'width', 'area_ft2', 'type_of_cut', 'no_cuts'])
        self.backup_waste = pd.DataFrame(columns=['simulation', 'wall', 'drywall_ID', 'drywall_object', 'cut_object','name', 'start_point_x', 'start_point_y', 'height', 'width', 'area_ft2', 'type_of_cut', 'no_cuts'])
        self.waste = pd.DataFrame(columns=['simulation', 'wall', 'drywall_ID', 'drywall_object', 'cut_object','name', 'start_point_x', 'start_point_y', 'height', 'width', 'area_ft2', 'type_of_cut', 'no_cuts'])
        #self.plates_list = plates_list
        
    def getJoints(self):
        return self.joints
    def getJointsDF(self):
        return self.df_joints
    def setJoints(self, row, joints):
        self.joints[row] = joints
    def setJointsDF(self, robot):
        columns=['simulation', 'wall', 'x', 'y', 'length']
        df = pd.DataFrame(np.array([[robot.getSimulationNumber(), self.wall_name, robot.getRobotPosition().getX(), robot.getRobotPosition().getY(), robot.getRowHeight()]]), columns=columns)
        self.df_joints = self.df_joints.append(df, ignore_index=True)
    def getCuttingLosses(self):
        return self.cutting_losses
    def setCuttingLosses(self, cutting_loss_area):
        self.cutting_losses.append(cutting_loss_area)
    def getName(self):
        return self.wall_name
    def getLength(self):
        return self.length
    def getHeight(self):
        return self.height
    def getStuds(self):
        return self.studs_df
    def getDoors(self):
        return self.doors_df
    def getWindows(self):
        return self.windows_df
    def getWaste(self):
        return self.waste_dataframe
    def getBackupWaste(self):
        return self.backup_waste
    def changeCuts(self, cut):
        df_drywall = self.getWallDataframe()
        index = df_drywall.index[df_drywall['drywall_ID'] == cut.getDrywall().getID()]
        self.drywall_dataframe.loc[index, 'no_cuts'] = self.drywall_dataframe.loc[index, 'no_cuts'] + 1
        # print('CHANGE CUTS NO')
        # print(index)
        # print(cut.getID())
        # #print(self.drywall_dataframe)
        # print(self.drywall_dataframe.iloc[index])
        cut.getDrywall().setNoCuts(self.drywall_dataframe.loc[index, 'no_cuts'].values)
        
    def placeDrywallAtPosition(self, position, drywall):
        """
        Mark the drywall under the position 'position' as nailed.

        Assumes that 'position' represents a valid position on the wall.

        position: a Position
        drywall: a Drywall
        
        Returns: 
            dictionary wih Positions as keys and drywall properties as values
        """
        point = (position.getX(), position.getY())
        if point not in self.keys():
            self[point] = drywall.getWidth(), drywall.getHeight(), drywall.getCuttingLosses()
    
    def getWallDataframe(self):
        return self.drywall_dataframe
    
    def updateDrywallDataframe(self, position, drywall, simulation_number):
        """
        Mark the drywall under the position 'position' as nailed. Assumes that 
        'position' represents a valid position on the wall.

        position: a Position
        drywall: a Drywall
        
        Returns:
            drywall dataframe
        """
        #Set column labels
        columns=['simulation', 'wall', 'drywall_ID', 'name', 'start_point_x', 'start_point_y', 'height', 'width', 'vertical_cut', 'horizontal_cut', 'door_clipper', 'window_clipper', 'no_cuts']
        #Create new dataframe to append
        df2 = pd.DataFrame(np.array([[simulation_number, self.wall_name, drywall.getID(), drywall.getName(), position.getX(), position.getY(), drywall.getHeight(), drywall.getWidth(), drywall.getVerticalCut(), drywall.getHorizontalCut(), drywall.getDoorClipper(), drywall.getWindowClipper(), drywall.getNoCuts()]]), columns=columns)
        #Append dataframe to self(wall)
        self.drywall_dataframe = self.drywall_dataframe.append(df2, ignore_index=True)
        
    def backup_WasteDF(self, df_waste):
        """
        Mark the drywall under the position 'position' as nailed. Assumes that 
        'position' represents a valid position on the wall.

        position: a Position class object
        cut: a Cut class object
        
        Returns:
            waste dataframe
        """
        self.backup_waste = self.backup_waste.append(df_waste, ignore_index=True)
        self.backup_waste = self.backup_waste.drop_duplicates(subset='name', keep='last') 
    
    def saveWasteDF(self):
        """
        Mark the drywall under the position 'position' as nailed. Assumes that 
        'position' represents a valid position on the wall.

        position: a Position class object
        cut: a Cut class object
        
        Returns:
            waste dataframe
        """
        self.waste = self.waste.append(self.backup_waste, ignore_index=True)
    
    def getWasteDF(self):
        return self.waste
        
    def updateWasteDF(self, cut, simulation_number):
        """
        Mark the drywall under the position 'position' as nailed. Assumes that 
        'position' represents a valid position on the wall.

        position: a Position class object
        cut: a Cut class object
        
        Returns:
            waste dataframe
        """
        #Set column labels
        columns=['simulation', 'wall', 'drywall_ID', 'drywall_object', 'cut_object','name', 'start_point_x', 'start_point_y', 'height', 'width', 'area_ft2', 'type_of_cut', 'no_cuts']
                
        #Append to dataframe if not empty
        if cut.getArea() != 0:
            df1 = pd.DataFrame(np.array([[simulation_number, cut.getWallName(), cut.getID(), cut.getDrywall(), cut, cut.getName(), cut.getPosition().getX(), cut.getPosition().getY(), cut.getHeight(), cut.getWidth(), cut.getArea(), cut.getType(), cut.getNoCuts()]]), columns=columns)
            self.waste_dataframe = self.waste_dataframe.append(df1, ignore_index=True)
            
    def updateWasteDF_VC_HC(self, drywall, simulation_number):
        """
        Mark the drywall under the position 'position' as nailed. Assumes that 
        'position' represents a valid position on the wall.

        position: a Position class object
        cut: a Cut class object
        
        Returns:
            waste dataframe
        """
        #Set column labels
        columns=['simulation', 'wall', 'drywall_ID', 'drywall_object', 'cut_object','name', 'start_point_x', 'start_point_y', 'height', 'width', 'area_ft2', 'type_of_cut', 'no_cuts']
        
        #Import cuts
        vc = drywall.getVerticalCut() #vertical cut
        hc = drywall.getHorizontalCut() #horizontal cut
        
        #Append to dataframe if not empty
        if vc != 0:
            if vc.getArea() != 0:
                df1 = pd.DataFrame(np.array([[simulation_number, self.wall_name, vc.getID(), vc.getDrywall(), vc, vc.getName(), vc.getPosition().getX(), vc.getPosition().getY(), vc.getHeight(), vc.getWidth(), vc.getArea(), vc.getType(), vc.getNoCuts()]]), columns=columns)
                self.waste_dataframe = self.waste_dataframe.append(df1, ignore_index=True)
        
        if hc != 0:
            if hc.getArea() != 0:
                df2 = pd.DataFrame(np.array([[simulation_number, self.wall_name, hc.getID(), hc.getDrywall(), hc, hc.getName(), hc.getPosition().getX(), hc.getPosition().getY(), hc.getHeight(), hc.getWidth(), hc.getArea(), hc.getType(), hc.getNoCuts()]]), columns=columns)
                self.waste_dataframe = self.waste_dataframe.append(df2, ignore_index=True)

    def getWallArea(self):
        """
        Return the total area of the wall.

        returns: an integer
        """
        return self.length * self.height
            
    def getNumDrywallSheets(self):
        """
        Return the total number of Drywall Sheets in the wall.

        returns: an integer
        """
        return len(self.values())
    
    def getDrywallArea(self):
        """
        Return the total area of Drywall Sheets in the wall.

        returns: an integer
        """        
        total_area = 0 
        for name, area in self.values():
            total_area += area 
        return total_area
    
    def isPositionInWall(self, position):
        """
        Return True if position is inside the wall.

        position: a Position object.
        returns: True if pos is in the room, False otherwise.
        """
        if position.getX() >= 0 and position.getX() < self.length and position.getY() >= 0 and position.getY() < self.height:
            return True
        else:
            return False
    
    def visualization(self, simulation_number, total_cutting_loss_area):
        
        sns_colors = sns.hls_palette(10, h=.5)
        #qualitative_colors = sns.color_palette("Set3", 10)
        #sns_color = sns.color_palette("husl", 8)
        #colors = sns.light_palette((210, 90, 60), input="husl")
        #blues = sns.color_palette("Blues")
        
        #plt.clf()
        fig = plt.figure(figsize=(20, 20))
        ax1 = fig.add_subplot(aspect='equal')
        
        #Plot Wall
        ax1.set_title(str(self.getName())+ ' - Simulation #' + str(simulation_number) + ' - Loss area: ' + str(total_cutting_loss_area) + 'ft2')
        ax1.set_ylim(0, self.getHeight() + 5) #self.getHeight()
        ax1.set_xlim(0, self.getLength() + 10) #self.getLength()
        
                 
        #Plot Studs
        studs_df = self.getStuds()
        #studs_list = CreateStudInstances(studs_df)
        studs_locationX_list = studs_df['Studs.Stud.InsertLocation.Attribute:X'].tolist()
        
        for locationX in studs_locationX_list:
            ax1.add_patch(patches.Rectangle((locationX - 0.0625, 0), 0.125, self.getHeight(), color='brown', alpha=1, linewidth=1))
        
        #Plot Drywalls
        for key, value  in self.items():
            ax1.add_patch(patches.Rectangle(key, value[0], value[1], alpha=0.7, color=random.choice(sns_colors), edgecolor='black', linewidth=2))
        
               
        #Plot doors
        doors_df = self.getDoors()
        for index, value in doors_df.iterrows():
            start_point_x = doors_df.loc[index, 'Doors.Openning.StartPoint.Attribute:X']
            start_point_y = doors_df.loc[index, 'Doors.Openning.StartPoint.Attribute:Y']
            end_point_x = doors_df.loc[index, 'Doors.Openning.EndPoint.Attribute:X']
            end_point_y = doors_df.loc[index, 'Doors.Openning.EndPoint.Attribute:Y']
            door_width = end_point_x - start_point_x 
            door_height = end_point_y - start_point_y
            ax1.add_patch(patches.Rectangle((start_point_x, start_point_y), door_width, door_height, color='white', alpha=0.7, edgecolor='black', linewidth=3))

        #Plot windows
        windows_df = self.getWindows()
        for index, value in windows_df.iterrows():
            start_point_x = windows_df.loc[index, 'Windows.Openning.StartPoint.Attribute:X']
            start_point_y = windows_df.loc[index, 'Windows.Openning.StartPoint.Attribute:Y']
            end_point_x = windows_df.loc[index, 'Windows.Openning.EndPoint.Attribute:X']
            end_point_y = windows_df.loc[index, 'Windows.Openning.EndPoint.Attribute:Y']
            window_width = end_point_x - start_point_x 
            window_height = end_point_y - start_point_y
            ax1.add_patch(patches.Rectangle((start_point_x, start_point_y), window_width, window_height, color='white', alpha=0.7, edgecolor='black', linewidth=3))
        
        #Plot Cutting Losses
        df_waste = self.getBackupWaste()
        simulation_number = 'Simulation_' + str(simulation_number)
        df_waste = df_waste[(df_waste['simulation']==simulation_number) & (df_waste['wall']==self.getName())]
        df_waste = df_waste[['start_point_x', 'start_point_y', 'width', 'height']].astype('float')
        for index, value in df_waste.iterrows():
            x = df_waste.loc[index, 'start_point_x']
            y = df_waste.loc[index, 'start_point_y']
            width = df_waste.loc[index, 'width']
            height = df_waste.loc[index, 'height']
            # print(x)
            # print(y)
            # print(width)
            # print(height)
            ax1.add_patch(patches.Rectangle((x, y), width, height, alpha=0.3, color='black', edgecolor='black', linewidth=1))
        
        # #Plot Cutting Losses
        # for w, h, c  in self.values():
        #     for i in c:
        #         x=i[0]
        #         y=i[1]
        #         ax1.add_patch(patches.Rectangle((x, y), i[2], i[3], alpha=0.3, color='black', edgecolor='black', linewidth=1))

        #plt.close(fig)
        
#studs_list = CreateStudInstances(studs_M1)
#wall_M1 = Wall('M1', 19.4792, 15, studs_list)

#Design Rules / Helper Functions

def isEdgeOnStud(next_position, stud_location_X):
    '''
    Check if drywall edge is on a stud position.
    Creat getStudRange method in Stud Class.
    
    next_position: drywall edge position (x, y).
    stud_range: stud position (x +- 0.0625').
    Stud_width: 1.5" (0.125')
                               
    Returns
    True if drywall edge is on stud position, 
    False otherwise.

    '''
    min_value = stud_location_X - 0.0625
    max_value = stud_location_X + 0.0625
    if  min_value <= stud_location_X <= max_value and round(stud_location_X, 4) == stud_location_X:
        return True
    else:
        return False

def staggerJoints(robot, position):
    
    joints = robot.wall.getJoints()
    row_number = robot.getRowNumber()
    
    if (len(joints)!=0) and ((row_number-1)>=0) and (position.getX() in joints[row_number-1]):
        #print('PROBLEM - Select different drywall size')
        return True
            
    else:
        #print('No need to stagger joints')
        return False
    
def isEdgeAroundDoorOpeningCorner(robot, position):
  
    doors_df = robot.wall.getDoors()
    #print(doors_df)
    if len(doors_df)==0:
        return False
    
    else:
        for index, value in doors_df.iterrows():
            d_start_point_x = doors_df.loc[index, 'Doors.Openning.StartPoint.Attribute:X']
            #d_start_point_y = doors_df.loc[index, 'Doors.Openning.StartPoint.Attribute:Y']
            d_end_point_x = doors_df.loc[index, 'Doors.Openning.EndPoint.Attribute:X']
            #d_end_point_y = doors_df.loc[index, 'Doors.Openning.EndPoint.Attribute:Y']
            #door_width = end_point_x - start_point_x 
            #door_height = end_point_y - start_point_y    
                        
            if (((d_start_point_x - 0.125) <= position.getX()) and (position.getX() <= (d_start_point_x + 0.125))) or \
                (((d_end_point_x - 0.125) <= position.getX()) and (position.getX() <= (d_end_point_x + 0.125))):
                    #print('Edge is around Door Opening Corner')
                    return True
            else:
                #print('Edge is NOT around Door Opening Corner')
                return False


def isEdgeAroundWindowOpeningCorner(robot, position):    
    
    windows_df = robot.wall.getWindows()
    
    if len(windows_df)==0:
        return False
    
    else:
    
        for index, value in windows_df.iterrows():
            w_start_point_x = windows_df.loc[index, 'Windows.Openning.StartPoint.Attribute:X']
            #w_start_point_y = windows_df.loc[index, 'Windows.Openning.StartPoint.Attribute:Y']
            w_end_point_x = windows_df.loc[index, 'Windows.Openning.EndPoint.Attribute:X']
            #w_end_point_y = windows_df.loc[index, 'Windows.Openning.EndPoint.Attribute:Y']
            #window_width = end_point_x - start_point_x 
            #window_height = end_point_y - start_point_y
        
            if (((w_start_point_x - 0.125) <= position.getX()) and (position.getX() <= (w_start_point_x + 0.125))) or \
            (((w_end_point_x - 0.125) <= position.getX()) and (position.getX() <= (w_end_point_x + 0.125))): 
                #print('Edge is around Window Opening Corner')
                return True
                break
            
            else:
                #print('Edge is NOT at Window Opening Corner')
                return False
               

def verticalOrientation(wall_length, wall_height, drywall_width, drywall_height):
    if wall_length <= drywall_height and wall_height <= drywall_width:
        #print('Place Drywall Sheet on a Vertical Orientation')
        return True
        
    
def verticalPossibility(wall_length, wall_height):
    
    drywall_list = CreateDrywallInstances(df_drywalls)
    
    for drywall in drywall_list:
        drywall_width = drywall.getWidth()
        #print('d_width: ' + str(drywall_width))
        drywall_height = drywall.getHeight()  
        #print('d_height: ' + str(drywall_height))
        #print('wall_length: ' + str(wall_length))
        #print('wall_height: ' + str(wall_height))
   
        if wall_length <= drywall_height and wall_height <= drywall_width:
            #print('Place Drywall Sheet on a Vertical Orientation')
            return True
            break

        
def clipper(subject, clip):
    '''
    Parameters:
    subject : list of coordinates (x, y) representing a polygon. Ex. drywall = [(x1, y1), (x2, y2), (x3, y3), (x4, y4)].
    clip : list of tuples (x, y) representing a polygon. Ex. Window = [(x1, y1), (x2, y2), (x3, y3), (x4, y4)].

    Returns
    intersection (i.e. cutting loss) = list of lists

    '''
    subject = pyclipper.scale_to_clipper(subject)
    clip = pyclipper.scale_to_clipper(clip)
    
    pc = pyclipper.Pyclipper()
    pc.AddPath(clip, pyclipper.PT_CLIP, True)
    pc.AddPath(subject, pyclipper.PT_SUBJECT, True)
    
    intersection = pyclipper.scale_from_clipper(pc.Execute(pyclipper.CT_INTERSECTION))
    
    return intersection

            
def getFourCoordinates(origin, width, height):
    
    c_1 = origin
    c_2 = origin.getNewPosition(width, 0)
    c_3 = c_2.getNewPosition(0, height)
    c_4 = c_1.getNewPosition(0, height)
    
    c_1 = origin.getX(), origin.getY()
    c_2 = c_2.getX(), c_2.getY()
    c_3 = c_3.getX(), c_3.getY()
    c_4 = c_4.getX(), c_4.getY()
    
    coordinates = [c_1, c_2, c_3, c_4]
    
    return coordinates

def clipperAtDoor(robot, drywall):
    
    doors_df = robot.wall.getDoors()
    #print(doors_df)
    #doors_df.fillna(0, inplace=True)
    cutting_losses=[]
    #print(doors_df.empty)
    #print(doors_df['Doors.Openning.StartPoint.Attribute:X'])
    if doors_df['Doors.Openning.StartPoint.Attribute:X'].isnull().values.any()==False:
        for index, value in doors_df.iterrows():
            d_start_point_x = doors_df.loc[index, 'Doors.Openning.StartPoint.Attribute:X']
            d_start_point_y = doors_df.loc[index, 'Doors.Openning.StartPoint.Attribute:Y']
            d_end_point_x = doors_df.loc[index, 'Doors.Openning.EndPoint.Attribute:X']
            d_end_point_y = doors_df.loc[index, 'Doors.Openning.EndPoint.Attribute:Y']
            door_width = d_end_point_x - d_start_point_x 
            door_height = d_end_point_y - d_start_point_y    
            
            subject = getFourCoordinates(drywall.getPosition(), drywall.getWidth(), drywall.getHeight())
            clip = getFourCoordinates(Position(d_start_point_x, d_start_point_y), door_width, door_height)
            #print(subject)
            #print(clip)
            
            cutting_loss_coordinates = clipper(subject, clip)
            #print(cutting_loss_coordinates)
            
            if len(cutting_loss_coordinates) != 0:
                
                origin = np.round(cutting_loss_coordinates[0][2][0], 4), np.round(cutting_loss_coordinates[0][2][1], 4)
                width = np.round((cutting_loss_coordinates[0][0][0] - cutting_loss_coordinates[0][2][0]), 4)
                height = np.round((cutting_loss_coordinates[0][0][1] - cutting_loss_coordinates[0][2][1]), 4)
                cutting_loss = Cut(drywall, width, height, 'door_clipper')
                cutting_loss.setPosition(Position(origin[0],origin[1]))
                
                #cutting_losses.append(cutting_loss)
                cutting_loss_area = width*height
                #print('CLIPPER_DOOR: ', cutting_loss)
                drywall.setCuttingLosses(cutting_loss)
                drywall.setDoorCut(cutting_loss)
                #print(drywall.getDoorClipper())
                robot.wall.setCuttingLosses(cutting_loss_area)
                simulation_number = 'Simulation_' + str(robot.getSimulationNumber())
                cutting_loss.setWallName(robot.wall.getName())
                robot.wall.updateWasteDF(cutting_loss, simulation_number)
                #print(robot.wall.getWaste())

def clipperAtWindow(robot, drywall):
    
    windows_df = robot.wall.getWindows()

    #print(windows_df.empty)
    #print(windows_df['Windows.Openning.StartPoint.Attribute:X'])
    #print(windows_df)
    if windows_df['Windows.Openning.StartPoint.Attribute:X'].isnull().values.any()==False:
        for index, value in windows_df.iterrows():
            w_start_point_x = windows_df.loc[index, 'Windows.Openning.StartPoint.Attribute:X']
            w_start_point_y = windows_df.loc[index, 'Windows.Openning.StartPoint.Attribute:Y']
            w_end_point_x = windows_df.loc[index, 'Windows.Openning.EndPoint.Attribute:X']
            w_end_point_y = windows_df.loc[index, 'Windows.Openning.EndPoint.Attribute:Y']
            window_width = w_end_point_x - w_start_point_x 
            window_height = w_end_point_y - w_start_point_y   
            
            #print(drywall.getWidth())
            #print(drywall.getHeight())
            
            subject = getFourCoordinates(drywall.getPosition(), drywall.getWidth(), drywall.getHeight())
            clip = getFourCoordinates(Position(w_start_point_x, w_start_point_y), window_width, window_height)
            #print(subject)
            #print(clip)
            
            if drywall.getWidth()!=0:
                cutting_loss_coordinates = clipper(subject, clip)
                #print(cutting_loss_coordinates)
                
                if len(cutting_loss_coordinates) != 0:
                    
                    #print(cutting_loss_coordinates)
                    origin = np.round(cutting_loss_coordinates[0][2][0], 4), np.round(cutting_loss_coordinates[0][2][1], 4)
                    width = np.round((cutting_loss_coordinates[0][0][0] - cutting_loss_coordinates[0][2][0]), 4)
                    height = np.round((cutting_loss_coordinates[0][0][1] - cutting_loss_coordinates[0][2][1]), 4)
                    
                    cutting_loss = Cut(drywall, width, height, 'window_clipper')
                    cutting_loss.setPosition(Position(origin[0],origin[1]))
                    
                    cutting_loss_area = width*height
                    #print('CLIPPER_WINDOW: ', cutting_loss)
                    #print(cutting_loss.getPosition())
                    #print(width)
                    #print(cutting_loss.getWidth())
                    drywall.setCuttingLosses(cutting_loss)
                    drywall.setWindowCut(cutting_loss)
                    robot.wall.setCuttingLosses(cutting_loss_area)
                    simulation_number = 'Simulation_' + str(robot.getSimulationNumber())
                    cutting_loss.setWallName(robot.wall.getName())
                    robot.wall.updateWasteDF(cutting_loss, simulation_number)
    
def generateID(name):
    name = name + '_'
    alphabet = string.digits
    return name + ''.join(random.choices(alphabet, k=6)) 
    
 
class Robot(object):
    """
    Represents a robot cutting and placing drywall sheets on a particular wall.

    Subclasses of Robot should provide movement strategies by implementing
    updatePositionAndNail(), which simulates a single time-step. 
    
    At each time-step, a robot attempts to place a randomly selected drywall 
    sheet; if drywall edge position does not comply with design rules,  then it 
    looks for the next stud and "cuts" the drywall. Keeps track of new coordinates
    in the wall. Keeps track of drywall cuts.
    """
    def __init__(self, wall):
        """
        Initializes a Robot in the specified wall. The robot initially is at coordinates
        (x=0, y=0) in the specified wall. The robot "nails" the stud it is on.

        wall:  a Wall object.
        """
        self.wall = wall
        self.position = Position(0, 0)
        self.row_height = 0
        self.row_number = 0
        self.simulation_number = 0
        self.drywall = 0
        
    def getRobotPosition(self):
        """
        Return the position of the robot.

        returns: a Position object giving the robot's position.
        """
        return self.position
    
    def setRobotPosition(self, position):
        """
        Set the position of the robot to POSITION.

        position: a Position object.
        """
        #raise NotImplementedError
        self.position = position
    
    def getRowHeight(self):
        return self.row_height
    
    def setRowHeight(self, row_height):
        self.row_height = row_height
        
    def getRowNumber(self):
        return self.row_number
    
    def setRowNumber(self, row_number):
        self.row_number = row_number
    
    def getSimulationNumber(self):
        return self.simulation_number
    
    def setSimulationNumber(self, simulation_number):
        self.simulation_number = simulation_number
        
    def getDrywall(self):
        return self.drywall
    
    def setDrywall(self, drywall):
        self.drywall = drywall
        
    def staggerJoints(self, position):
    
        joints = self.wall.getJoints()
        row_number = self.getRowNumber()
    
        if (len(joints)!=0) and ((row_number-1)>=0) and (position.getX() in joints[row_number-1]):
            #print('PROBLEM - Select different drywall size')
            return True
                
        else:
            #print('No need to stagger joints')
            return False
                 
    def NailOnVerticalOrientation(self, drywall):
        """
        Simulate the passage of a single time-step.

        Move the robot to a new position and mark the stud it is on as having
        been placed if complies with design rules. Keeps track of drywall cuts.
        """
        
        #Calculate possible next_position
        delta_X = drywall.getWidth()
        #print('Drywall_Width: ' + str(delta_X))
        delta_Y = 0
        next_position = self.getRobotPosition().getNewPosition(delta_X, delta_Y)
        
        #Get studs and instanciate them
        studs_df = self.wall.getStuds()
      
        studs_locationX_list = studs_df['Studs.Stud.InsertLocation.Attribute:X'].tolist()
        #studs_locationX_list.sort(reverse=False)
        studs_locationX_array = np.array(studs_locationX_list)
        
        #Locate closest stud
        position_X = drywall.getHeight()
        min_distance_next_stud = position_X - studs_locationX_array
        
        #Calculate cutting losses
        
        #Cutting loss VC (Vertical cut)
        cutting_loss_VC_width = min_distance_next_stud[min_distance_next_stud > 0].min()
        #cutting_loss_VC_width = drywall.getHeight() - self.wall.getLength()
        cutting_loss_VC_height = drywall.getWidth()
        
        #Cutting loss HC (Horizontal cut)
        cutting_loss_HC_width = round(drywall.getHeight() - cutting_loss_VC_width, 4)
        cutting_loss_HC_height = round(drywall.getWidth() - self.wall.getHeight(), 4)       
        
        #Calculate new drywall width and height
        new_drywall_width = round(drywall.getHeight() - cutting_loss_VC_width, 4)
        new_drywall_height = round(drywall.getWidth() - cutting_loss_HC_height, 4)            
        
        #Set new drywall width and height
        drywall.setDrywallWidth(new_drywall_width)
        drywall.setDrywallHeight(new_drywall_height)
        
        #Append cutting losses to list
        cutting_loss_VC = Cut(drywall, cutting_loss_VC_width, cutting_loss_VC_height, 'vertical_cut')
        cutting_loss_VC.setPosition(Position(new_drywall_width, next_position.getY()))
        
        cutting_loss_HC = Cut(drywall, cutting_loss_HC_width, cutting_loss_HC_height, 'horizontal_cut')
        cutting_loss_HC.setPosition(Position(0, new_drywall_height))
            
        drywall.setCuttingLosses(cutting_loss_VC)
        drywall.setCuttingLosses(cutting_loss_HC)
        drywall.setVerticalCut(cutting_loss_VC)
        drywall.setHorizontalCut(cutting_loss_HC)
        
        #Append area of cutting losses to wall
        cutting_loss_VC_area = cutting_loss_VC_width * cutting_loss_VC_height
        cutting_loss_HC_area = cutting_loss_HC_width * cutting_loss_HC_height
        total_cutting_loss_area = cutting_loss_VC_area + cutting_loss_HC_area
        total_cutting_loss_area = round(total_cutting_loss_area, 4)
        #print("Cutting loss area: " + str(total_cutting_loss_area) + " ft2")
        self.wall.setCuttingLosses(total_cutting_loss_area)                    

        #Place drywall at position
        drywall_position = Position(0, 0)
        self.wall.placeDrywallAtPosition(drywall_position, drywall)
        simulation_number = 'Simulation_' + str(self.getSimulationNumber())
        position = Position(0, 0)
        drywall.setPosition(drywall_position)
        self.setDrywall(drywall)
        #self.wall.updateDrywallDataframe(position, drywall, simulation_number)
    

    def updatePositionAndNail(self):
        """
        Simulate the passage of a single time-step.

        Move the robot to a new position and mark the stud it is on as having
        been placed if complies with design rules. Keep track of drywall cuts.
        """
        
        drywall_list = CreateDrywallInstances(df_drywalls)
        #print(drywall_list)
        
        #Randomly select a drywall sheet
        random_drywall = random.choice(drywall_list)
        #print(random_drywall)
        #print(random_drywall.getArea())
        
        #Calculate possible next_position
        delta_X = random_drywall.getWidth()
        #print('Random_Drywall_Width: ' + str(delta_X))
        delta_Y = 0
        next_position = self.getRobotPosition().getNewPosition(delta_X, delta_Y)
        
        #Get studs and instanciate them
        studs_df = self.wall.getStuds()
        studs_locationX_list = studs_df['Studs.Stud.InsertLocation.Attribute:X'].tolist()
        #studs_locationX_list.sort(reverse=False)
        studs_locationX_array = np.array(studs_locationX_list)
        
        
        print('Use nominal drywall sheets')
        
        #Is the next_position inside the wall?
        #print("Is the next_position inside the wall?")
         
        if self.wall.isPositionInWall(next_position) == False:
            
            #print('No, it is outside the wall')
                        
            #Locate closest stud
            position_X = next_position.getX()
            distances = position_X - studs_locationX_array 
            
            #Calculate cutting losses
                
            #Cutting loss VC (Vertical cut)
            cutting_loss_VC_width = distances[distances > 0].min()
            cutting_loss_VC_width = round(cutting_loss_VC_width, 4)
            cutting_loss_VC_height = random_drywall.getHeight()
            
            #Cutting loss HC (Horizontal cut)
            cutting_loss_HC_width = round(delta_X - cutting_loss_VC_width, 4)
            cutting_loss_HC_height = round(random_drywall.getHeight() - self.getRowHeight(), 4)
            
            #Calculate new drywall width and height
            new_drywall_width = round(random_drywall.getWidth() - cutting_loss_VC_width, 4)
            new_drywall_height = round(random_drywall.getHeight() - cutting_loss_HC_height, 4)
            
            # If new_drywall_width == 0, 
            # it means the drywall edge fits on the edge of the wall.
            # Add some distance to break the loop in Simulation
            if new_drywall_width == 0:
                self.setRobotPosition(next_position.getNewPosition(1, 0))
                #print('Row Done!!')
                return False
            
            else:
   
                #Set new drywall width and height
                random_drywall.setDrywallWidth(new_drywall_width)
                random_drywall.setDrywallHeight(new_drywall_height)            
                
                #Calculate new position
                new_position = self.getRobotPosition().getNewPosition(round((delta_X-cutting_loss_VC_width), 4), delta_Y)
                self.setRobotPosition(next_position)
                
                #Append cutting losses to each drywall
                cutting_loss_VC = Cut(random_drywall, cutting_loss_VC_width, cutting_loss_VC_height, 'vertical_cut')
                cutting_loss_VC.setPosition(Position(new_position.getX(), new_position.getY()))
                
                cutting_loss_HC = Cut(random_drywall, cutting_loss_HC_width, cutting_loss_HC_height, 'horizontal_cut')
                cutting_loss_HC.setPosition(Position(new_position.getX() - new_drywall_width, new_position.getY() + random_drywall.getHeight()))
                
                random_drywall.setCuttingLosses(cutting_loss_VC)
                random_drywall.setCuttingLosses(cutting_loss_HC)
                random_drywall.setVerticalCut(cutting_loss_VC)
                random_drywall.setHorizontalCut(cutting_loss_HC)
               
                #Append area of cutting losses to wall
                cutting_loss_VC_area = cutting_loss_VC.getArea()
                cutting_loss_HC_area = cutting_loss_HC.getArea()
                total_cutting_loss_area = round(cutting_loss_VC_area + cutting_loss_HC_area, 4)
                #print("Cutting loss area: " + str(total_cutting_loss_area) + " ft2")
                self.wall.setCuttingLosses(total_cutting_loss_area)
                
                #Place drywall at position
                self.wall.placeDrywallAtPosition(new_position.getNewPosition(-new_drywall_width, 0), random_drywall)
                simulation_number = 'Simulation_' + str(self.getSimulationNumber())
                drywall_position = new_position.getNewPosition(-new_drywall_width, 0)
                #self.wall.updateDrywallDataframe(drywall_position, random_drywall, simulation_number)
                random_drywall.setPosition(drywall_position)
                self.setDrywall(random_drywall)
                return True
            
        else:
            #print("Yes, it is inside the wall")
            
            #Now check design rules

            #Case 1: Is edge of drywall on Stud?
            #print('Is the edge of the drywall Located on a Stud?')
            #print(next_position.getX())
            #print(studs_locationX_array)
            if np.any(((studs_locationX_array - 0.0625) <= next_position.getX()) & (next_position.getX() <=(studs_locationX_array + 0.0625))) == True:
                #mask = ((studs_locationX_array -1)<= 8.5) & (8.5 <=(studs_locationX_array + 1))
                #print("Stud location X: " + str(studs_locationX_array[mask]))
                #print('Yes, it is located on a Stud')
                
                #Is Edge around an Opening Corner?
                #print('Is Edge around an Opening Corner?')
                
                if isEdgeAroundDoorOpeningCorner(self, next_position) == True or \
                    isEdgeAroundWindowOpeningCorner(self, next_position) == True:
                        #print('PROBLEM - Select different drywall size')
                        return False
                
                else:    
                
                    #print('Need to stagger joints?')
                    
                    if staggerJoints(self, next_position)==True:
                        #print('PROBLEM - Yes, select different drywall size')
                        return False
                    
                    else:
                        #print('No need to stagger joints')
                        
                        self.setRobotPosition(next_position)
                        
                        #Check if robot position is at the edge of the wall (to include joint or not)
                        wall_edge = self.wall.getLength()
                        if (wall_edge - 0.0625 ) <= self.getRobotPosition().getX() <= (wall_edge + 0.0625):
                            self.wall.setJointsDF(self)
                        
                        #Calculate cutting losses
                        #Cutting loss HC (Horizontal cut)
                        cutting_loss_HC_width = delta_X
                        cutting_loss_HC_height = round(random_drywall.getHeight() - self.getRowHeight(), 4)
                        #print('Wall Height: ' + str(self.wall.getHeight()))
                        #print('Row Height: ' + str(self.getRowHeight()))
                        #Calculate new drywall height
                        new_drywall_height = round(random_drywall.getHeight() - cutting_loss_HC_height, 4)
                        
                        #Set new drywall height
                        random_drywall.setDrywallHeight(new_drywall_height)
   
                        #Append cutting losses to list
                        cutting_loss_HC_position = Position(round((next_position.getX()-random_drywall.getWidth()), 4), next_position.getY()+random_drywall.getHeight())
                        cutting_loss_HC = Cut(random_drywall, cutting_loss_HC_width, cutting_loss_HC_height, 'horizontal_cut')
                        cutting_loss_HC.setPosition(cutting_loss_HC_position)

                        random_drywall.setCuttingLosses(cutting_loss_HC)       
                        random_drywall.setHorizontalCut(cutting_loss_HC)
                        
                        #Append area of cutting losses to wall
                        cutting_loss_HC_area = cutting_loss_HC_width * cutting_loss_HC_height
                        total_cutting_loss_area = cutting_loss_HC_area
                        total_cutting_loss_area = round(total_cutting_loss_area, 4)
                        #print("Cutting loss area: " + str(total_cutting_loss_area) + " ft2")
                        self.wall.setCuttingLosses(total_cutting_loss_area)
                        
                        #Place drywall at position
                        x = random_drywall.getWidth()
                        drywall_position = next_position.getNewPosition(-x, 0)
                        self.wall.placeDrywallAtPosition(drywall_position, random_drywall)
                        simulation_number = 'Simulation_' + str(self.getSimulationNumber())
                        #self.wall.updateDrywallDataframe(drywall_position, random_drywall, simulation_number)
                        random_drywall.setPosition(drywall_position)
                        self.setDrywall(random_drywall)
                        return True
                        
            #Case 2: Edge of drywall not on stud
            else:
                #print('No, it is not Located on a Stud')
                
                #Locate closest stud
                position_X = next_position.getX()
                min_distance_next_stud = position_X - studs_locationX_array
                
                #Calculate cutting losses
                
                #Cutting loss VC (Vertical cut)
                cutting_loss_VC_width = round((min_distance_next_stud[min_distance_next_stud > 0].min()), 4)
                cutting_loss_VC_height = random_drywall.getHeight()
                
                #Cutting loss HC (Horizontal cut)
                cutting_loss_HC_width = round((delta_X - cutting_loss_VC_width), 4)
                cutting_loss_HC_height = round(random_drywall.getHeight() - self.getRowHeight(), 4)
                
                #Calculate new drywall width and height
                new_drywall_width = (random_drywall.getWidth() - cutting_loss_VC_width)
                new_drywall_height = (random_drywall.getHeight() - cutting_loss_HC_height).round(4)
                
                #Set new drywall width and height
                random_drywall.setDrywallWidth(new_drywall_width)
                random_drywall.setDrywallHeight(new_drywall_height)  
                
                #Calculate new robot position
                new_position = self.getRobotPosition().getNewPosition(round((delta_X-cutting_loss_VC_width), 4), delta_Y)
                
                
                #Is Edge around an Opening Corner?
                #print('Is Edge around an Opening Corner?')
                
                if isEdgeAroundDoorOpeningCorner(self, new_position) == True or \
                    isEdgeAroundWindowOpeningCorner(self, new_position) == True:
                        #print('PROBLEM - Select different drywall size')
                        return False
                
                else:
                   
                    #Do we need to stagger Joints?
                    #joints = self.wall.getJoints()
                    #print('Joints: ', joints)
                    
                    if staggerJoints(self, new_position)==True:
                        #print('PROBLEM - Select different drywall size')
                        return False
                    
                    else:
                        #print('No need to stagger joints')
                        self.setRobotPosition(new_position)
                        #print('Robot Position: ' + str(self.getRobotPosition()))
                        
                        #Check if robot position is at the edge of the wall (to include joint or not)
                        wall_edge = self.wall.getLength()
                        if (wall_edge - 0.0625 ) <= self.getRobotPosition().getX() <= (wall_edge + 0.0625):
                            self.wall.setJointsDF(self)
              
                        #Append cutting losses to list
                        cutting_loss_VC = Cut(random_drywall, cutting_loss_VC_width, cutting_loss_VC_height, 'vertical_cut')
                        cutting_loss_VC.setPosition(new_position)
                        
                        cutting_loss_HC_position = Position(round((new_position.getX() - new_drywall_width), 4), round((new_position.getY()+random_drywall.getHeight()), 4)) 
                        cutting_loss_HC = Cut(random_drywall, cutting_loss_HC_width, cutting_loss_HC_height, 'horizontal_cut')
                        cutting_loss_HC.setPosition(cutting_loss_HC_position)
                
                        random_drywall.setCuttingLosses(cutting_loss_VC)
                        random_drywall.setCuttingLosses(cutting_loss_HC)
                        random_drywall.setVerticalCut(cutting_loss_VC)
                        random_drywall.setHorizontalCut(cutting_loss_HC)
                        
                        #Append area of cutting losses to wall
                        cutting_loss_VC_area = cutting_loss_VC_width * cutting_loss_VC_height
                        cutting_loss_HC_area = cutting_loss_HC_width * cutting_loss_HC_height
                        total_cutting_loss_area = cutting_loss_VC_area + cutting_loss_HC_area
                        total_cutting_loss_area = round(total_cutting_loss_area, 4)
                        #print("Cutting loss area: " + str(total_cutting_loss_area) + " ft2")
                        self.wall.setCuttingLosses(total_cutting_loss_area)                    
    
                        #Place drywall at position
                        drywall_position = new_position.getNewPosition(-new_drywall_width, 0)
                        self.wall.placeDrywallAtPosition(drywall_position, random_drywall)
                        simulation_number = 'Simulation_' + str(self.getSimulationNumber())
                        #self.wall.updateDrywallDataframe(drywall_position, random_drywall, simulation_number)
                        random_drywall.setPosition(drywall_position)
                        self.setDrywall(random_drywall)
                        return True
                    
    def reuseCuttingLosses_Greedy(self, df_waste, max_cuts, min_area): # max_cuts_allowed, min_area_allowed
        """
        Simulate the passage of a single time-step.

        Move the robot to a new position and mark the stud it is on as having
        been placed if complies with design rules. Keeps track of drywall cuts.
        """
        #Sort Waste dataframe by area on descending order.
        df_waste = df_waste.sort_values(by='area_ft2', ascending=False)
           
        #Get studs and instanciate them
        studs_df = self.wall.getStuds()
        studs_locationX_list = studs_df['Studs.Stud.InsertLocation.Attribute:X'].tolist()
        studs_locationX_array = np.array(studs_locationX_list)
        
        # Greedy approach to check if any of the cuts fits on a stud, 
        # break out of loop if True
        
        for index, value in df_waste.iterrows():
            
            cut = df_waste.loc[index, 'cut_object']
            delta_X = cut.getWidth() # cut_width is equivalent to the possible next position in X
            wall_name = df_waste.loc[index, 'wall']
            
            #print(delta_X)
            delta_Y = 0 
            next_position = self.getRobotPosition().getNewPosition(delta_X, delta_Y)
            #print(self.getRobotPosition())
            #print(next_position)
            # DONT FORGET TO ADD CONDITIONALS TO CHECK CUTS_ALLOWED AND AREA_ALLOWED
            #Check row height
            #print(cut.getWidth())
            no_cuts = cut.getDrywall().getNoCuts() #total no. of times the drywall has been cut
            #print(no_cuts)
            nominal_area = cut.getDrywall().getNominalArea()            
            #print(cut.getArea()/nominal_area)
            if cut.getHeight() >= self.getRowHeight() and cut.getWidth() >= 1.33333 and no_cuts < max_cuts and cut.compliesArea(min_area, nominal_area): #1.33333 == 16in (Min stud frame spacing)
                print('Reuse cutting losses')    
                #print('Height OK & Width OK') 
                
                if self.wall.isPositionInWall(next_position) == False:
                    print('No, it is outside the wall')
                                
                    #Locate closest stud
                    position_X = next_position.getX()
                    distances = position_X - studs_locationX_array # array of distances (position_X - each stud location x) 
                    
                    #Calculate cutting losses
                    #Cutting loss VC (Vertical cut)
                    cutting_loss_VC_width = distances[distances > 0].min() # exclude negative distances and pick min (closest)
                    cutting_loss_VC_width = round(cutting_loss_VC_width, 4)
                    cutting_loss_VC_height = cut.getHeight()
                    #Cutting loss HC (Horizontal cut)
                    cutting_loss_HC_width = round(delta_X - cutting_loss_VC_width, 4)
                    cutting_loss_HC_height = round(cut.getHeight() - self.getRowHeight(), 4)
                    #print(cutting_loss_VC_width)
                    #print(cutting_loss_HC_width)
                    
                    #Calculate new Cut width and height
                    new_cut_width = round(cut.getWidth() - cutting_loss_VC_width, 4)
                    new_cut_height = round(cut.getHeight() - cutting_loss_HC_height, 4)
                    #print(new_cut_width)
                    #print(new_cut_height)
                    #If new_drywall_width == 0, 
                    #it means the drywall edge fits on the edge of the wall.
                    #Add some distance to break the loop in Simulation
                    if new_cut_width == 0:
                        self.setRobotPosition(next_position.getNewPosition(1, 0))
                        #print('Row Done!!')
                        return False
                    
                    else:
                            #Set new cut width, height and No_cuts
                            cut.setWidth(new_cut_width)
                            cut.setHeight(new_cut_height)
                            cut.setNoCuts(self)
                            
                            #Calculate new position (Edge of drywall after cut)
                            new_position = self.getRobotPosition().getNewPosition(round((delta_X-cutting_loss_VC_width), 4), delta_Y)
                            self.setRobotPosition(next_position) # Robot is set at next_position to break while loop in simulation
                            
                            #Set cutting losses
                            cutting_loss_VC_position = Position(new_position.getX(), new_position.getY())
                            cutting_loss_VC = Cut(cut.getDrywall(), cutting_loss_VC_width, cutting_loss_VC_height, 'vertical_cut')
                            cutting_loss_VC.setPosition(cutting_loss_VC_position)
                            
                            cutting_loss_HC_position = Position(new_position.getX() - new_cut_width, new_position.getY() + cut.getHeight())
                            cutting_loss_HC = Cut(cut.getDrywall(), cutting_loss_HC_width, cutting_loss_HC_height, 'horizontal_cut')
                            cutting_loss_HC.setPosition(cutting_loss_HC_position)
                                                      
                            #Transform Cut object to Drywall Class Object and append losses
                            cut_as_drywall = Drywall(cut.getName(), cut.getHeight(), cut.getWidth())
                            cut_as_drywall.setVerticalCut(cutting_loss_VC)
                            cut_as_drywall.setHorizontalCut(cutting_loss_HC)
                            
                            #Place drywall at position and set position and add to robot
                            x = cut.getWidth()
                            cut_position = new_position.getNewPosition(-x, 0)
                            self.wall.placeDrywallAtPosition(cut_position, cut_as_drywall)
                            cut_as_drywall.setPosition(cut_position)
                            self.setDrywall(cut_as_drywall)
                            
                            # if cutting_losses height or width are 0, drop row from waste df
                            # print(self.wall.getWaste())
                            if cutting_loss_VC_width == 0 or cutting_loss_HC_height == 0:
                                print('FULL CUT')
                                self.wall.getBackupWaste().drop(index, axis=0, inplace=True)
                            
                            else:
                                print('Adjust new size of cut & Add extra losses')
                                #Update Waste Dataframe
                                simulation_number = 'Simulation_' + str(self.getSimulationNumber())
                                #cut.setWallName(wall_name)
                                #self.wall.updateWasteDF(cut, simulation_number) # Keep cut in previous wall
                                self.wall.getBackupWaste().drop(index, axis=0, inplace=True)
                                self.wall.updateWasteDF_VC_HC(self.getDrywall(), simulation_number)
                            
                            # print('CUT WAS PLACED ON THE WALL!!')
                            # print('Iteration: ' + str(index))
                            
                            return True
                            break
                        
                else:
                    print("Yes, it is inside the wall")
                    
                    #Now check design rules
                    #Case 1: Is edge of drywall on Stud?
                    # print('Is the edge of the drywall Located on a Stud?')
                    #print(next_position.getX())
                    #print(studs_locationX_array)
                    if np.any(((studs_locationX_array - 0.0625) <= next_position.getX()) & (next_position.getX() <=(studs_locationX_array + 0.0625))) == True:
                        print('Yes, it is located on a Stud')
                        
                        #Is Edge around an Opening Corner?
                        # print('Is Edge around an Opening Corner?')
                        if isEdgeAroundDoorOpeningCorner(self, next_position) == True or \
                            isEdgeAroundWindowOpeningCorner(self, next_position) == True:
                                #print('PROBLEM - Select different drywall size')
                                return False
                        else:    
                            # print('Need to stagger joints?')
                            
                            if staggerJoints(self, next_position)==True:
                                # print('PROBLEM - Yes, select different drywall size')
                                return False
                            
                            else:
                                #print('No need to stagger joints')
                                
                                self.setRobotPosition(next_position)
                            
                                #Check if robot position is at the edge of the wall (to include joint or not)
                                wall_edge = self.wall.getLength()
                                if (wall_edge - 0.0625 ) <= self.getRobotPosition().getX() <= (wall_edge + 0.0625):
                                    self.wall.setJointsDF(self)
                                
                                #Calculate cutting losses
                                #Cutting loss HC (Horizontal cut)
                                cutting_loss_HC_width = delta_X
                                cutting_loss_HC_height = round(cut.getHeight() - self.getRowHeight(), 4)
                                #print('Wall Height: ' + str(self.wall.getHeight()))
                                #print('Row Height: ' + str(self.getRowHeight()))
                                
                                #Calculate new cut height
                                new_cut_height = round(cut.getHeight() - cutting_loss_HC_height, 4)
                                #Set new cut height and no_cuts
                                cut.setHeight(new_cut_height)
                                cut.setNoCuts(self)
                                                                 
                                #Set cutting losses
                                cutting_loss_HC_position = Position(round((next_position.getX()-cut.getWidth()), 4), next_position.getY() + cut.getHeight())
                                cutting_loss_HC = Cut(cut.getDrywall(), cutting_loss_HC_width, cutting_loss_HC_height, 'horizontal_cut')
                                cutting_loss_HC.setPosition(cutting_loss_HC_position)
                                
                                #Transform Cut object into Class Object
                                cut_as_drywall = Drywall(cut.getName(), cut.getHeight(), cut.getWidth())
                                cut_as_drywall.setHorizontalCut(cutting_loss_HC)
                                                              
                                #Place drywall at position
                                x = cut.getWidth()
                                print('Cut width: ' + str(x))
                                cut_position = next_position.getNewPosition(-x, 0)
                                self.wall.placeDrywallAtPosition(cut_position, cut_as_drywall)
                                
                                #self.wall.updateDrywallDataframe(drywall_position, random_drywall, simulation_number)
                                cut_as_drywall.setPosition(cut_position)
                                self.setDrywall(cut_as_drywall)
                                
                                # if cutting_loss height is 0, drop row from waste df. 
                                # In other words, the Cut_as_drywall was used entirely.
                                #print(self.wall.getWaste())
                                print(cutting_loss_HC_height)
                                if cutting_loss_HC_height == 0:
                                    print('FULL CUT')
                                    self.wall.getBackupWaste().drop(index, axis=0, inplace=True)
                                    print(self.wall.getBackupWaste())
                                else:
                                    print('Adjust new size of cut & Add extra losses')
                                    #Update Waste Dataframe
                                    simulation_number = 'Simulation_' + str(self.getSimulationNumber())
                                    #cut.setWallName(wall_name)
                                    #self.wall.updateWasteDF(cut, simulation_number)
                                    self.wall.getBackupWaste().drop(index, axis=0, inplace=True)
                                    self.wall.updateWasteDF_VC_HC(self.getDrywall(), simulation_number)
                                # print('CUT WAS PLACED ON THE WALL!!')
                                # print('Iteration: ' + str(index))
                                
                                return True
                                break
                               
                    #Case 2: Edge of drywall not on stud
                    else:
                        print('No, it is not Located on a Stud')
                        
                        #Locate closest stud
                        position_X = next_position.getX()
                        #print(position_X)
                        distances = position_X - studs_locationX_array
                        #print(distances)
                        #Calculate cutting losses
                        #Cutting loss VC (Vertical cut)
                        cutting_loss_VC_width = round(distances[distances > 0].min(), 4)
                        cutting_loss_VC_height = cut.getHeight()
                        
                        #Cutting loss HC (Horizontal cut)
                        cutting_loss_HC_width = round((delta_X - cutting_loss_VC_width), 4)
                        cutting_loss_HC_height = round(cut.getHeight() - self.getRowHeight(), 4)
                        #print(cutting_loss_HC_height)
                        #Calculate new drywall width and height
                        
                        new_cut_width = (cut.getWidth() - cutting_loss_VC_width)
                        #print(cut.getWidth())
                        #print(cutting_loss_VC_width)
                        #print(new_cut_width)
                        new_cut_height = (cut.getHeight() - cutting_loss_HC_height).round(4)
                        
                        #Set new cut width, height and No_cuts
                        cut.setWidth(new_cut_width)
                        cut.setHeight(new_cut_height)
                        cut.setNoCuts(self)
                        #print('Drywall No Cuts')
                        #print(cut.getDrywall().getNoCuts())
                        
                        #Calculate new robot position
                        new_position = self.getRobotPosition().getNewPosition(round((delta_X-cutting_loss_VC_width), 4), delta_Y)
                         
                        #Is Edge around an Opening Corner?
                        # print('Is Edge around an Opening Corner?')
                        
                        if isEdgeAroundDoorOpeningCorner(self, new_position) == True or \
                            isEdgeAroundWindowOpeningCorner(self, new_position) == True:
                                # print('PROBLEM - Select different drywall size')
                                return False
                        else:
                            #Do we need to stagger Joints?
                            #joints = self.wall.getJoints()
                            #print('Joints: ', joints)
                            
                            if staggerJoints(self, new_position)==True:
                                # print('PROBLEM - Select different drywall size')
                                return False
                            else:
                                # print('No need to stagger joints')
                                self.setRobotPosition(new_position)
                                #print('Robot Position: ' + str(self.getRobotPosition()))
                                
                                #Check if robot position is at the edge of the wall (to include joint or not)
                                wall_edge = self.wall.getLength()
                                if (wall_edge - 0.0625 ) <= self.getRobotPosition().getX() <= (wall_edge + 0.0625):
                                    self.wall.setJointsDF(self)
                      
                                #Set cutting losses
                                cutting_loss_VC = Cut(cut.getDrywall(), cutting_loss_VC_width, cutting_loss_VC_height, 'vertical_cut')
                                cutting_loss_VC.setPosition(new_position)
                                
                                cutting_loss_HC_position = Position(new_position.getX() - new_cut_width, new_position.getY() + cut.getHeight())
                                cutting_loss_HC = Cut(cut.getDrywall(), cutting_loss_HC_width, cutting_loss_HC_height, 'horizontal_cut')
                                cutting_loss_HC.setPosition(cutting_loss_HC_position)
                                                          
                                #Transform Cut object to Drywall Class Object and append losses
                                cut_as_drywall = Drywall(cut.getName(), cut.getHeight(), cut.getWidth())
                                cut_as_drywall.setVerticalCut(cutting_loss_VC)
                                cut_as_drywall.setHorizontalCut(cutting_loss_HC)
                            
                                #Place drywall at position
                                x = cut.getWidth()
                                print('Cut width: ' + str(x))
                                print('Loss_width: ' + str(cutting_loss_VC_width))
                                if x == 0: # it means the sheet's width is less than the stud spacing
                                    return False
                                
                                else:
                                    cut_position = new_position.getNewPosition(-x, 0)
                                    self.wall.placeDrywallAtPosition(cut_position, cut_as_drywall)
                                    
                                    #self.wall.updateDrywallDataframe(drywall_position, random_drywall, simulation_number)
                                    cut_as_drywall.setPosition(cut_position)
                                    self.setDrywall(cut_as_drywall)
                                    
                                    # if new cut HC height OR cut VC width is  0, drop row from waste df
                                    #print(self.wall.getWaste())
                                    if cutting_loss_VC_width == 0 and cutting_loss_HC_height == 0:
                                        print('FULL CUT')
                                        #print(self.wall.getBackupWaste())
                                        self.wall.getBackupWaste().drop(index, axis=0, inplace=True)
                                    else:
                                        print('Adjust new size of cut & Add extra losses')
                                        #Update Waste Dataframe
                                        simulation_number = 'Simulation_' + str(self.getSimulationNumber())
                                        #cut.setWallName(wall_name)
                                        #self.wall.updateWasteDF(cut, simulation_number)
                                        self.wall.getBackupWaste().drop(index, axis=0, inplace=True)
                                        self.wall.updateWasteDF_VC_HC(self.getDrywall(), simulation_number)
                                    # print('CUT WAS PLACED ON THE WALL!!')
                                    # print('Iteration: ' + str(index))
                                    
                                    return True
                                    break
                                
    def reuseCuttingLosses_BestFit(self, df_waste): #, cuts_allowed, area_allowed
        """
        Simulate the passage of a single time-step.

        Move the robot to a new position and mark the stud it is on as having
        been placed if complies with design rules. Keeps track of drywall cuts.
        """
        #Sort Waste dataframe by area on descending order.
        df_waste = df_waste.sort_values(by='area_ft2', ascending=False)
           
        #Get studs and instanciate them
        studs_df = self.wall.getStuds()
        studs_locationX_list = studs_df['Studs.Stud.InsertLocation.Attribute:X'].tolist()
        studs_locationX_array = np.array(studs_locationX_list)
        
        # Greedy approach to try to fit the cuts on a stud, 
        # break out of loop if True
        
        for index, value in df_waste.iterrows():
            
            cut = df_waste.loc[index, 'cut_object']
            delta_X = cut.getWidth() # cut_width is equivalent to the possible next position in X
            delta_Y = 0
            next_position = self.getRobotPosition().getNewPosition(delta_X, delta_Y)
            
            # DONT FORGET TO ADD CONDITIONALS TO CHECK CUTS_ALLOWED AND AREA_ALLOWED
            #Check row height
            
            if cut.getHeight() >= self.getRowHeight():
                
                # Check if the cut is aligned with a stud
                if np.any(((studs_locationX_array - 0.0625) <= next_position.getX()) & (next_position.getX() <=(studs_locationX_array + 0.0625))) == True:
                    print('A perfect CUT MATCH was found!!')
                    
                    #Is Edge around an Opening Corner?
                    print('Is Edge around an Opening Corner?')
                    
                    if isEdgeAroundDoorOpeningCorner(self, next_position) == True or \
                        isEdgeAroundWindowOpeningCorner(self, next_position) == True:
                            print('PROBLEM - Select different drywall size')
                            return False
                    
                    else:
                        print('Need to stagger joints?')
                        
                        if staggerJoints(self, next_position)==True:
                            print('PROBLEM - Yes, select different cut size')
                            return False
                        
                        else:
                            print('No need to stagger joints')
                            
                            self.setRobotPosition(next_position)
                            
                            #Check if robot position is at the edge of the wall (to include joint or not)
                            wall_edge = self.wall.getLength()
                            if (wall_edge - 0.0625 ) <= self.getRobotPosition().getX() <= (wall_edge + 0.0625):
                                self.wall.setJointsDF(self)
                            
                            #Calculate cutting losses
                            
                            #Cutting loss HC (Horizontal cut)
                            cutting_loss_HC_width = delta_X
                            cutting_loss_HC_height = round(cut.getHeight() - self.getRowHeight(), 4)
                            #print('Wall Height: ' + str(self.wall.getHeight()))
                            #print('Row Height: ' + str(self.getRowHeight()))
                            
                            #Calculate new cut height
                            new_cut_height = round(cut.getHeight() - cutting_loss_HC_height, 4)
                            
                            #Set new cut height
                            cut.setHeight(new_cut_height)
                            cut.setNoCuts(self)
                                                     
                            #Set cutting losses
                            cutting_loss_HC_position = Position(round((next_position.getX()-cut.getWidth()), 4), next_position.getY() + cut.getHeight())
                            cutting_loss_HC = Cut(cut.getDrywall(), cutting_loss_HC_width, cutting_loss_HC_height, 'horizontal_cut')
                            cutting_loss_HC.setPosition(cutting_loss_HC_position)
                            
                            #Transform Cut object into Class Object
                            cut_as_drywall = Drywall(cut.getName(), cut.getHeight(), cut.getWidth())
                            cut_as_drywall.setHorizontalCut(cutting_loss_HC)
                            
                            #Place drywall at position
                            x = cut.getWidth()
                            cut_position = next_position.getNewPosition(-x, 0)
                            self.wall.placeDrywallAtPosition(cut_position, cut_as_drywall)
                            
                            #self.wall.updateDrywallDataframe(drywall_position, random_drywall, simulation_number)
                            cut_as_drywall.setPosition(cut_position)
                            self.setDrywall(cut_as_drywall)
                            
                            # if cutting_loss height is 0, drop row from waste df. 
                            # In other words, the Cut_as_drywall was used entirely.
                            print(self.wall.getWaste())
                            if cutting_loss_HC_height == 0:
                                self.wall.getBackupWaste().drop(index, axis=0, inplace=True)
                            else:
                                #Update Waste Dataframe
                                simulation_number = 'Simulation_' + str(self.getSimulationNumber())
                                cut.setWallName(self.wall.getName())
                                self.wall.updateWasteDF(cut, simulation_number)
                            
                            print('CUT WAS PLACED ON THE WALL!!')
                            print('Iteration: ' + str(index))
                            
                            return True
                            break                    

def runSimulationOneWall_Greedy(num_trials, wall_name, wall_length, wall_height, unique_stud_df, unique_door_df, unique_window_df, max_cuts, min_area):
    
    random.seed(0)
    #Instanciate the wall
    wall = Wall(wall_name, wall_length, wall_height, unique_stud_df, unique_door_df, unique_window_df)
    #Instanciate the robot:
    robot = Robot(wall)    
    #Create drywall instances as a list
    drywall_list = CreateDrywallInstances(df_drywalls)    
    
    #Verify drywall orientation    
    #If Vertical Orientation,
    if verticalPossibility(wall_length, wall_height) == True:
        
        #Iterate through drywall list and nail best possible option
        for drywall in drywall_list:
            drywall_width = drywall.getWidth()
            drywall_height = drywall.getHeight()
        
            if verticalOrientation(robot.wall.getLength(), robot.wall.getHeight(), drywall_width, drywall_height) == True:
                # print('Vertical Orientation')
                
                #Set new drywall width and height
                drywall.setDrywallWidth(drywall_width)
                drywall.setDrywallHeight(drywall_height)                
                
                #Add drywall to the wall
                robot.NailOnVerticalOrientation(drywall)
                
                #Check cutting losses from doors and windows
                clipperAtDoor(robot, drywall) 
                #clipperAtWindow(robot, drywall)
                
                #Update Wall Dataframe
                simulation_number = 'Simulation_' + str(robot.getSimulationNumber())
                robot.wall.updateDrywallDataframe(robot.getDrywall().getPosition(), robot.getDrywall(), simulation_number)
                robot.wall.updateWasteDF_VC_HC(robot.getDrywall(), simulation_number)
                #print(robot.wall.getWaste())
                robot.wall.backup_WasteDF(robot.wall.getWaste())
                
                cutting_losses = wall.getCuttingLosses()
                total_cutting_loss_area = round(np.sum(cutting_losses), 4)
                #print('Total cutting loss area: ' + str(total_cutting_loss_area))
                
                wall.saveWasteDF()
                wall.visualization(0, total_cutting_loss_area)
                
                return wall
    
    #Else, place drywalls in Horizontal Orientation
    else:
        print('Horizontal Orientation')
        
        #Calculate number of rows
        drywall_height = 4  #sometimes 5
        rows = wall_height / drywall_height 
        rows_floor = int(np.floor(rows))
        dif = (rows-rows_floor)*drywall_height #last row height
        
        rows_height=[]
        for i in range(rows_floor):
            rows_height.append(drywall_height)
        if dif != 0:
            rows_height.append(dif)    
        #print(rows_height)
        
        #Run simulation over num_trials
        for t in range(num_trials):
            temp_time_steps = 0
            #Clear dataframes at the beginning of each simulation
            wall.clear()
            wall.waste_dataframe.drop(wall.waste_dataframe.index, inplace=True)
            wall.backup_waste.drop(wall.backup_waste.index, inplace=True)
            wall.cutting_losses.clear()
            delta_X = 0
            delta_Y = 0
            
            robot.setSimulationNumber(t)
            simulation_number = 'Simulation_' + str(robot.getSimulationNumber())
            
            #Iterate through number of rows
            for row in range(len(rows_height)):
                robot.setRowHeight(rows_height[row])
                robot.setRowNumber(row)
                new_origin = robot.getRobotPosition().getNewPosition(delta_X, delta_Y)
                robot.setRobotPosition(new_origin)
                
                print('Row: ' + str(row))
                print('Origin: ' + str(new_origin))
                print(" ")
    
                joints = []
                
                # Iterate through while loop until row is complete, 
                # keep track of time_steps every time the robot function is called.
                while True:
                    # Clear temporary waste dataframe after each time-step. This df helps 
                    # to add aditional info without interference with complete waste_df
                    wall.waste_dataframe.drop(wall.waste_dataframe.index, inplace=True)
                    
                    temp_time_steps += 1
                    print('')
                    print("Time Step #" + str(temp_time_steps))
                                        
                    # if waste dataframe is not empty, try to reuse cutting losses,
                    # else, try to place a drywall sheet of nominal size
                    df_drywall = robot.wall.getWallDataframe()
                    df_waste = robot.wall.getBackupWaste()
                    # print('Drywall DF')
                    # print(df_drywall[['drywall_ID','name', 'height', 'width', 'no_cuts']])
                    # print('Backup Waste DF: ')
                    # print(df_waste[['simulation', 'name','width', 'area_ft2', 'type_of_cut', 'no_cuts']])
                    if df_waste.empty == False and robot.reuseCuttingLosses_Greedy(df_waste, max_cuts, min_area) == True:
                        clipperAtDoor(robot, robot.getDrywall()) 
                        clipperAtWindow(robot, robot.getDrywall())
                        
                        robot.wall.updateDrywallDataframe(robot.getDrywall().getPosition(), robot.getDrywall(), simulation_number)
                        robot.wall.updateWasteDF_VC_HC(robot.getDrywall(), simulation_number)
                        # print('Temp. Waste DF: ') 
                        # print(robot.wall.getWaste())
                        robot.wall.backup_WasteDF(robot.wall.getWaste())
                        #print('df_waste')
                        #print(robot.wall.getBackupWaste()
                        
                        #Add joint to Joints DataFrame
                        robot_position = robot.getRobotPosition()
                        joints.append(robot_position.getX())                       
                     
                    else:
                        
                        # if current simulation complies with all design rules,
                        # update drywall and waste dataframe
                        if robot.updatePositionAndNail() == True:
                            clipperAtDoor(robot, robot.getDrywall()) 
                            clipperAtWindow(robot, robot.getDrywall())
                            
                            robot.wall.updateDrywallDataframe(robot.getDrywall().getPosition(), robot.getDrywall(), simulation_number)
                            robot.wall.updateWasteDF_VC_HC(robot.getDrywall(), simulation_number)
                            robot.wall.backup_WasteDF(robot.wall.getWaste())
                            
                            #Add joint to Joints DataFrame
                            robot_position = robot.getRobotPosition()
                            joints.append(robot_position.getX())
                        
                            #print('Row Joints: ', joints)
                    
                    #print("Wall: " + str(wall))
                    #print("")
                    
                    #print(wall.isPositionInWall(robot.getRobotPosition()))
                    
                    if wall.isPositionInWall(robot.getRobotPosition()) == False:
                        print(robot.getRobotPosition())
                        #print("Row " + str(row) + " complete.")
                        delta_X = -robot.getRobotPosition().getX()
                        delta_Y = 4
                        break
                    
                wall.setJoints(row, joints)
                
                #print('Wall Joints: ', wall.getJoints())
            
            origin = Position(0, 0)
            robot.setRobotPosition(origin)     
            
            print(' ')
            
            print("End of simulation #" + str(t))        
            
            cutting_losses = wall.getCuttingLosses()
            total_cutting_loss_area = round(np.sum(cutting_losses), 4)
            
            wall.saveWasteDF()
            wall.visualization(t, total_cutting_loss_area)
                    
        return wall

                        
def runSimulationOneWall(num_trials, wall_name, wall_length, wall_height, unique_stud_df, unique_door_df, unique_window_df):
    
    random.seed(0)
    #Instanciate wall & robot
    wall = Wall(wall_name, wall_length, wall_height, unique_stud_df, unique_door_df, unique_window_df)
    robot = Robot(wall)    
    
    #Create drywall instances as a list
    drywall_list = CreateDrywallInstances(df_drywalls)    
    
    #Verify drywall orientation    
    #If Vertical Orientation...
    if verticalPossibility(wall_length, wall_height) == True:
        
        #Run simulation over num_trials
        for t in range(num_trials):
            
            #Iterate through drywall list and nail best possible option
    
            for drywall in drywall_list:
                drywall_width = drywall.getWidth()
                drywall_height = drywall.getHeight()
            
                if verticalOrientation(robot.wall.getLength(), robot.wall.getHeight(), drywall_width, drywall_height) == True:
                    print('Vertical Orientation')
                    
                    #Set new drywall width and height
                    drywall.setDrywallWidth(drywall_width)
                    drywall.setDrywallHeight(drywall_height)                
                    
                    #Add drywall to the wall
                    robot.NailOnVerticalOrientation(drywall)
                    
                    #Check cutting losses from doors and windows
                    clipperAtDoor(robot, drywall) 
                    #clipperAtWindow(robot, drywall)
                    
                    #Update Wall Dataframe
                    simulation_number = 'Simulation_' + str(t)
                    robot.wall.updateDrywallDataframe(robot.getDrywall().getPosition(), robot.getDrywall(), simulation_number)
                    robot.wall.updateWasteDF_VC_HC(robot.getDrywall(), simulation_number)
                    robot.wall.backup_WasteDF(robot.wall.getWaste())
                    
                    cutting_losses = wall.getCuttingLosses()
                    total_cutting_loss_area = round(np.sum(cutting_losses), 4)
                    #print('Total cutting loss area: ' + str(total_cutting_loss_area))
                    
                    wall.visualization(0, total_cutting_loss_area)
                    
                    return wall
    
    #Else, place drywalls in Horizontal Orientation
    else:
        print('Horizontal Orientation')
        
        #Calculate number of rows
        drywall_height = 4  #sometimes 5
        rows = wall_height / drywall_height 
        rows_floor = int(np.floor(rows))
        dif = (rows-rows_floor)*drywall_height #last row height
        
        rows_height=[]
        for i in range(rows_floor):
            rows_height.append(drywall_height)
        if dif != 0:
            rows_height.append(dif)     
       
        #Run simulation over num_trials
        for t in range(num_trials):
            temp_time_steps = 0
            wall.clear()
            wall.waste_dataframe.drop(wall.waste_dataframe.index, inplace=True)
            wall.backup_waste.drop(wall.backup_waste.index, inplace=True)
            wall.cutting_losses.clear()
            delta_X = 0
            delta_Y = 0
            
            robot.setSimulationNumber(t)
        
            #Iterate through number of rows
            
            for row in range(len(rows_height)):
                
                robot.setRowHeight(rows_height[row])
                robot.setRowNumber(row)
                new_origin = robot.getRobotPosition().getNewPosition(delta_X, delta_Y)
                robot.setRobotPosition(new_origin)
                
                print('Row: ' + str(row))
                print('Origin: ' + str(new_origin))
                print(" ")
    
                joints = []
                
                
                #time_steps for each simulation
                while True:
                    wall.waste_dataframe.drop(wall.waste_dataframe.index, inplace=True)
                    
                    temp_time_steps += 1
                    print(" ")
                    print("Time Step #" + str(temp_time_steps))
                                        
                    #print(robot.getRobotPosition())
                    
                    # if waste dataframe is not empty, try to reuse cutting losses,
                    # else, try to place a drywall sheet of nominal size
                    df_drywall = robot.wall.getWallDataframe()
                    df_waste = robot.wall.getBackupWaste()
                    #print(df_drywall['drywall_ID','name', 'area_ft2',])
                    #print(df_waste[['simulation', 'drywall_ID','name', 'area_ft2', 'type_of_cut', 'no_cuts']])
                    if df_waste.empty == False and robot.reuseCuttingLosses_BestFit(df_waste) == True:
                        clipperAtDoor(robot, robot.getDrywall()) 
                        clipperAtWindow(robot, robot.getDrywall())
                        
                        simulation_number = 'Simulation_' + str(robot.getSimulationNumber())
                        robot.wall.updateDrywallDataframe(robot.getDrywall().getPosition(), robot.getDrywall(), simulation_number)
                        robot.wall.updateWasteDF_VC_HC(robot.getDrywall(), simulation_number)
                        #print(robot.wall.getWaste())
                        robot.wall.backup_WasteDF(robot.wall.getWaste())
                        #print('df_waste')
                        #print(robot.wall.getBackupWaste()
                        
                        #Add joint to Joints DataFrame
                        robot_position = robot.getRobotPosition()
                        joints.append(robot_position.getX())                       
                     
                    else:
                        
                        # if current simulation complies with all design rules,
                        # update drywall and waste dataframe
                        if robot.updatePositionAndNail() == True:
                            clipperAtDoor(robot, robot.getDrywall()) 
                            clipperAtWindow(robot, robot.getDrywall())
                            
                            simulation_number = 'Simulation_' + str(robot.getSimulationNumber())
                            robot.wall.updateDrywallDataframe(robot.getDrywall().getPosition(), robot.getDrywall(), simulation_number)
                            robot.wall.updateWasteDF_VC_HC(robot.getDrywall(), simulation_number)
                            robot.wall.backup_WasteDF(robot.wall.getWaste())
                            
                            #Add joint to Joints DataFrame
                            robot_position = robot.getRobotPosition()
                            joints.append(robot_position.getX())
                        
                            #print('Row Joints: ', joints)
                    
                    #print("Wall: " + str(wall))
                    #print("")
                    
                    #print(wall.isPositionInWall(robot.getRobotPosition()))
                    
                    if wall.isPositionInWall(robot.getRobotPosition()) == False:
                        #print(robot.getRobotPosition())
                        #print("Row " + str(row) + " complete.")
                        delta_X = -robot.getRobotPosition().getX()
                        delta_Y = 4
                        break
                    
                wall.setJoints(row, joints)
                
                #print('Wall Joints: ', wall.getJoints())
            
            origin = Position(0, 0)
            robot.setRobotPosition(origin)     
            
            print(' ')
            
            print("End of simulation #" + str(t))        
            
            cutting_losses = wall.getCuttingLosses()
            total_cutting_loss_area = round(np.sum(cutting_losses), 4)
            #print('Total cutting loss area: ' + str(total_cutting_loss_area))
            
            wall.saveWasteDF()
            wall.visualization(t, total_cutting_loss_area)
                    
        return wall

class Floor(object):
    def __init__(self, floor_name):
        self.floor_name = floor_name
        self.drywallDF = pd.DataFrame()
        self.wasteDF = pd.DataFrame() 
    def getDrywallDF(self):
        return self.drywallDF
    def saveDrywallDF(self, df_drywall):
        self.drywallDF = self.drywallDF.append(df_drywall, ignore_index=True)
    def getWasteDF(self):
        return self.wasteDF
    def saveWasteDF(self, df_waste):
        self.wasteDF = self.wasteDF.append(df_waste, ignore_index=True)
    def visual(self, name, df1, df2):

        sns_colors = sns.hls_palette(10, h=.5)
        
        fig = plt.figure(figsize=(20, 20))
        ax1 = fig.add_subplot(aspect='equal')
        
        #Plot Wall
        ax1.set_title(str(name))
        ax1.set_ylim(0, 9.09375 + 5) #self.getHeight()
        ax1.set_xlim(0, 19.9375 + 10) #self.getLength()
    
        #Plot Drywalls
        for index, value  in df1.iterrows():
            x = df1.loc[index, 'start_point_x']
            y = df1.loc[index, 'start_point_y']
            width = df1.loc[index, 'width']
            height = df1.loc[index, 'height']
            ax1.add_patch(patches.Rectangle((x, y), width, height, alpha=0.7, color=random.choice(sns_colors), edgecolor='black', linewidth=2))
    
        #Plot Cutting Losses
        #df_waste = self.getBackupWaste()
        #df_waste = df_waste[['start_point_x', 'start_point_y', 'width', 'height']].astype('float')
        for index, value in df2.iterrows():
            x = df2.loc[index, 'start_point_x']
            y = df2.loc[index, 'start_point_y']
            width = df2.loc[index, 'width']
            height = df2.loc[index, 'height']
            # print(x)
            # print(y)
            # print(width)
            # print(height)
            ax1.add_patch(patches.Rectangle((x, y), width, height, alpha=0.3, color='black', edgecolor='black', linewidth=1))
     

def runSimulationOneFloor(num_trials, floor_name, df_walls, df_studs, df_doors, df_windows, opt_approach, max_cuts, min_area):
    
    #columns=['simulation', 'wall', 'name', 'start_point_x', 'start_point_y', 'height', 'width', 'vertical_cut', 'horizontal_cut', 'door_clipper', 'window_clipper']
    #floor = pd.DataFrame(columns=columns)
    floor = Floor(floor_name)
    #print(floor)
    #Loop through each wall in the corresponding house floor
    for index, value in df_walls.iterrows():
        
        wall_name = df_walls.loc[index, 'Attribute:Name']
        print('Start Simulation for Wall: ' + str(wall_name))
        
        wall_length = df_walls.loc[index, 'Attribute:Length']
        wall_height = df_walls.loc[index, 'Attribute:Height']
        
        unique_stud_df = np.round(df_studs.loc[df_studs['Attribute:Name']== wall_name], 4)
        unique_door_df = np.round(df_doors.loc[df_doors['Attribute:Name']== wall_name], 4)
        
        unique_window_df = np.round(df_windows.loc[df_windows['Attribute:Name']== wall_name], 4)
        
        if opt_approach == 'BestFit':
            wall = runSimulationOneWall(num_trials, wall_name, wall_length, wall_height, unique_stud_df, unique_door_df, unique_window_df)
        if opt_approach == 'Greedy':
            wall = runSimulationOneWall_Greedy(num_trials, wall_name, wall_length, wall_height, unique_stud_df, unique_door_df, unique_window_df, max_cuts, min_area)
        
        #print(wall)
        
        floor.saveDrywallDF(wall.getWallDataframe())
        floor.saveWasteDF(wall.getWasteDF())
        
        print('End Simulation for Wall: ' + str(wall_name))
        print(' ')
    
    return floor


class House(object):
    def __init__(self, house_name):
        self.house_name = house_name
        self.drywallDF = pd.DataFrame()
        self.wasteDF = pd.DataFrame() 
    def getDrywallDF(self):
        return self.drywallDF
    def saveDrywallDF(self, df_drywall):
        self.drywallDF = self.drywallDF.append(df_drywall, ignore_index=True)
    def getWasteDF(self):
        return self.wasteDF
    def saveWasteDF(self, df_waste):
        self.wasteDF = self.wasteDF.append(df_waste, ignore_index=True)

def runSimulationForHouse(num_trials, house_name, df_walls, df_studs, df_doors, df_windows, opt_approach, max_cuts, min_area):
    
    #Initialize an empty house list
    #columns=['simulation', 'wall', 'name', 'start_point_x', 'start_point_y', 'height', 'width', 'vertical_cut', 'horizontal_cut', 'door_clipper', 'window_clipper']
    #house = pd.DataFrame(columns=columns)
    house = House(house_name)
    
    #Get list of floors in the house
    floors = df_walls['Attribute:Level'].unique().tolist()
    
    #Loop through each floor in the house
    for floor_name in floors:
        
        print('Start Simulation for Floor: ' + str(floor_name))
        
        #Get wall dataframe associated to each floor in the house
        df_walls_floor = df_walls.loc[df_walls['Attribute:Level']== floor_name]
        
        #Run Simulation for each floor accordingly
        floor = runSimulationOneFloor(num_trials, floor_name, df_walls_floor, df_studs, df_doors, df_windows, opt_approach, max_cuts, min_area)
        
        #Append the results from each floor simulation to the house list
        house.saveDrywallDF(floor.getDrywallDF())
        house.saveWasteDF(floor.getWasteDF())
        
        print('End Simulation for Floor: ' + str(floor_name))
        print(' ')
        
        #print(wall.getWallDataframe())
    
    return house
                
# house = runSimulationForHouse(1, 'Residential House Prototype', df_walls, df_studs, df_doors, df_windows, 'Greedy', 0, 1)
# house.getDrywallDF().to_csv(r'C:\Users\josec\Desktop\Python Prototype\test_scenario_1_greedy_Drywall.csv', index = None, header=True)
# house.getWasteDF().to_csv(r'C:\Users\josec\Desktop\Python Prototype\test_scenario_1_greedy_Waste.csv', index = None, header=True)

def runSimulation_Wall_to_Wall(trial, wall_name, wall_length, wall_height, unique_stud_df, unique_door_df, unique_window_df, df_waste, max_cuts, min_area):
    
    
    #Instanciate the wall
    wall = Wall(wall_name, wall_length, wall_height, unique_stud_df, unique_door_df, unique_window_df)
    #Instanciate the robot:
    robot = Robot(wall)
    robot.setSimulationNumber(trial)
    simulation_number = 'Simulation_' + str(robot.getSimulationNumber())   
    robot.wall.backup_WasteDF(df_waste)    
    #Create drywall instances as a list
    drywall_list = CreateDrywallInstances(df_drywalls)    
    
    #Verify drywall orientation    
    #If Vertical Orientation,
    if verticalPossibility(wall_length, wall_height) == True:
        
        #Iterate through drywall list and nail best possible option
        for drywall in drywall_list:
            drywall_width = drywall.getWidth()
            drywall_height = drywall.getHeight()
        
            if verticalOrientation(robot.wall.getLength(), robot.wall.getHeight(), drywall_width, drywall_height) == True:
                print('Vertical Orientation')
                
                #Set new drywall width and height
                drywall.setDrywallWidth(drywall_width)
                drywall.setDrywallHeight(drywall_height)                
                
                #Add drywall to the wall
                robot.NailOnVerticalOrientation(drywall)
                
                #Check cutting losses from doors and windows
                clipperAtDoor(robot, drywall) 
                #clipperAtWindow(robot, drywall)
                
                #Update Wall Dataframe
                #simulation_number = 'Simulation_' + str(robot.getSimulationNumber())
                robot.wall.updateDrywallDataframe(robot.getDrywall().getPosition(), robot.getDrywall(), simulation_number)
                robot.wall.updateWasteDF_VC_HC(robot.getDrywall(), simulation_number)
                #print(robot.wall.getWaste())
                robot.wall.backup_WasteDF(robot.wall.getWaste())
                
                cutting_losses = wall.getCuttingLosses()
                total_cutting_loss_area = round(np.sum(cutting_losses), 4)
                #print('Total cutting loss area: ' + str(total_cutting_loss_area))
                
                wall.saveWasteDF()
                wall.visualization(trial, total_cutting_loss_area)
                
                return wall
    
    #Else, place drywalls in Horizontal Orientation
    else:
        print('Horizontal Orientation')
        
        #Calculate number of rows
        drywall_height = 4  #sometimes 5
        rows = wall_height / drywall_height 
        rows_floor = int(np.floor(rows))
        dif = (rows-rows_floor)*drywall_height #last row height
        
        rows_height=[]
        for i in range(rows_floor):
            rows_height.append(drywall_height)
        if dif!=0:
            rows_height.append(dif)    
            print(rows_height)
       
        #Clear dataframes at the beginning of each simulation
        #wall.clear()
        #wall.drywall_dataframe.drop(wall.drywall_dataframe.index, inplace=True)
        #wall.waste_dataframe.drop(wall.waste_dataframe.index, inplace=True)
        #wall.backup_waste.drop(wall.backup_waste.index, inplace=True)
        #wall.cutting_losses.clear()
        delta_X = 0
        delta_Y = 0
        
        #df_waste = df_waste[df_waste['simulation'] == simulation_number]
        #print(robot.wall.getBackupWaste())
        #robot.wall.backup_WasteDF(df_waste)
        #print(robot.wall.getBackupWaste())
        
        #Iterate through number of rows
        for row in range(len(rows_height)):
            # Set New Robot attributes
            robot.setRowNumber(row)
            robot.setRowHeight(rows_height[row])
            new_origin = robot.getRobotPosition().getNewPosition(delta_X, delta_Y)
            robot.setRobotPosition(new_origin)
            
            print(" ")
            print('Row: ' + str(row))
            print('Origin: ' + str(new_origin))
            print(" ")

            joints = []
            
            # Iterate through while loop until row is complete, 
            # keep track of time_steps every time the robot function is called.
            
            temp_time_steps = 0
            while True:
                temp_time_steps += 1
                print('')
                print("Time Step #" + str(temp_time_steps))
                                
                # Clear temporary waste dataframe on each time-step. This df helps 
                # to add aditional info without interference with complete waste_df
                wall.waste_dataframe.drop(wall.waste_dataframe.index, inplace=True)
                
                #df_drywall = robot.wall.getWallDataframe()
                #print('Drywall DF')
                #print(df_drywall[['simulation', 'wall', 'drywall_ID', 'name', 'no_cuts']])
                
                df_waste = robot.wall.getBackupWaste()
                #print('Backup Waste DF: ')
                #print(df_waste[['simulation', 'wall', 'name', 'type_of_cut', 'no_cuts']])
              
                if df_waste.empty == False and robot.reuseCuttingLosses_Greedy(df_waste, max_cuts, min_area) == True:
                    
                    clipperAtDoor(robot, robot.getDrywall()) 
                    clipperAtWindow(robot, robot.getDrywall())
                    
                    robot.wall.updateDrywallDataframe(robot.getDrywall().getPosition(), robot.getDrywall(), simulation_number)
                    
                    
                    print(robot.wall.getWaste()[['simulation', 'wall', 'name', 'width','type_of_cut']])
                    robot.wall.backup_WasteDF(robot.wall.getWaste())
                    print('Temp. Waste DF: ') 
                    print(robot.wall.getBackupWaste()[['simulation', 'wall', 'name', 'width','type_of_cut']])
                    print('Drywall DF: ')
                    print(robot.wall.getWallDataframe()[['simulation', 'wall', 'name', 'no_cuts']])
                    
                    #Add joint to Joints DataFrame
                    robot_position = robot.getRobotPosition()
                    joints.append(robot_position.getX())                       
                 
                else:
                    
                    # if current simulation complies with all design rules,
                    # update drywall and waste dataframe
                    if robot.updatePositionAndNail() == True:
                        clipperAtDoor(robot, robot.getDrywall()) 
                        clipperAtWindow(robot, robot.getDrywall())
                        
                        robot.wall.updateDrywallDataframe(robot.getDrywall().getPosition(), robot.getDrywall(), simulation_number)
                        robot.wall.updateWasteDF_VC_HC(robot.getDrywall(), simulation_number)
                        robot.wall.backup_WasteDF(robot.wall.getWaste())
                        
                        print('Temp. Waste DF: ') 
                        print(robot.wall.getBackupWaste()[['simulation', 'wall', 'name', 'type_of_cut', 'no_cuts']])
                        print('Drywall DF: ')
                        print(robot.wall.getWallDataframe()[['simulation', 'wall', 'name', 'no_cuts']])
                        #Add joint to Joints DataFrame
                        robot_position = robot.getRobotPosition()
                        joints.append(robot_position.getX())
                    
                        #print('Row Joints: ', joints)
                
                #print("Wall: " + str(wall))
                #print("")
                
                #print(wall.isPositionInWall(robot.getRobotPosition()))
                
                if wall.isPositionInWall(robot.getRobotPosition()) == False:
                    # print(robot.getRobotPosition())
                    #print("Row " + str(row) + " complete.")
                    delta_X = -robot.getRobotPosition().getX()
                    delta_Y = 4
                    break
                
            wall.setJoints(row, joints)
            
            #print('Wall Joints: ', wall.getJoints())
        
        origin = Position(0, 0)
        robot.setRobotPosition(origin)     
        
        print(' ')
        
        print("End of simulation #" + str(trial))        
        
        cutting_losses = wall.getCuttingLosses()
        total_cutting_loss_area = round(np.sum(cutting_losses), 4)
        
        wall.saveWasteDF()
        #print(wall.getWasteDF())
        
        wall.visualization(trial, total_cutting_loss_area)
                
    return wall

def runSimulation_House(num_trials, floor_name, df_walls, df_studs, df_doors, df_windows, opt_approach, max_cuts, min_area):
    
    random.seed(0)
    
    floor = Floor(floor_name)
    
    # Loop through num_trials
    for trial in range(num_trials):
        
        df_waste = pd.DataFrame()
        
        #Loop through each wall in the corresponding house floor
        for index, value in df_walls.iterrows():
            
            wall_name = df_walls.loc[index, 'Attribute:Name']
            print('Start Simulation for Wall: ' + str(wall_name))
            
            wall_length = df_walls.loc[index, 'Attribute:Length']
            wall_height = df_walls.loc[index, 'Attribute:Height']
            unique_stud_df = np.round(df_studs.loc[df_studs['Attribute:Name']== wall_name], 4)
            unique_door_df = np.round(df_doors.loc[df_doors['Attribute:Name']== wall_name], 4)
            unique_window_df = np.round(df_windows.loc[df_windows['Attribute:Name']== wall_name], 4)
            
            if opt_approach == 'BestFit':
                wall = runSimulationOneWall(num_trials, wall_name, wall_length, wall_height, unique_stud_df, unique_door_df, unique_window_df)
                floor.saveWasteDF(wall.getWasteDF())
            if opt_approach == 'Greedy':
                wall = runSimulationOneWall_Greedy(trial, wall_name, wall_length, wall_height, unique_stud_df, unique_door_df, unique_window_df, max_cuts, min_area)
                floor.saveWasteDF(wall.getWasteDF())
            if opt_approach == 'Wall_to_Wall':
                wall = runSimulation_Wall_to_Wall(trial, wall_name, wall_length, wall_height, unique_stud_df, unique_door_df, unique_window_df, df_waste, max_cuts, min_area)
                df_waste = wall.getWasteDF()
                #print(df_waste)
                print('----------------------------------------')
                #print(df_waste)
                #wall.backup_WasteDF()
            
            #print(wall)
            #print(wall.getWallDataframe())
            floor.saveDrywallDF(wall.getWallDataframe())
        
        #print(wall.getWasteDF())
        if opt_approach == 'Wall_to_Wall':
            floor.saveWasteDF(wall.getWasteDF())
            
        print('End Simulation for Wall: ' + str(wall_name))
        print(' ')
    
    return floor


def visual(name, df1, df2):

    sns_colors = sns.hls_palette(10, h=.5)
    
    fig = plt.figure(figsize=(20, 20))
    ax1 = fig.add_subplot(aspect='equal')
    
    #Plot Wall
    ax1.set_title(str(name))
    ax1.set_ylim(0, 9.09375 + 5) #self.getHeight()
    ax1.set_xlim(0, 19.9375 + 10) #self.getLength()

    #Plot Drywalls
    df1 = df1[['start_point_x', 'start_point_y', 'width', 'height']].astype('float')
    for index, value  in df1.iterrows():
        x = df1.loc[index, 'start_point_x']
        y = df1.loc[index, 'start_point_y']
        width = df1.loc[index, 'width']
        height = df1.loc[index, 'height']
        ax1.add_patch(patches.Rectangle((x, y), width, height, alpha=0.7, color=random.choice(sns_colors), edgecolor='black', linewidth=2))

    #Plot Cutting Losses
    #df_waste = self.getBackupWaste()
    #df_waste = df_waste[['start_point_x', 'start_point_y', 'width', 'height']].astype('float')
    df2 = df2[['start_point_x', 'start_point_y', 'width', 'height']].astype('float')
    for index, value in df2.iterrows():
        x = df2.loc[index, 'start_point_x']
        y = df2.loc[index, 'start_point_y']
        width = df2.loc[index, 'width']
        height = df2.loc[index, 'height']
        ax1.add_patch(patches.Rectangle((x, y), width, height, alpha=0.3, color='black', edgecolor='black', linewidth=1))

def visualization(df1, df2):
    wall_list = df1['wall'].unique().tolist()
    simulation_list = df1['simulation'].unique().tolist()
    for simulation in simulation_list:
        for wall in wall_list:
            D = df1[(df1['simulation']==simulation) & (df1['wall']==wall)]
            W = df2[(df2['simulation']==simulation) & (df2['wall']==wall)]
            visual(wall, D, W) 


# df1 = df_walls.loc[df_walls['Attribute:Name']=='U11']
# df2= df_walls.loc[df_walls['Attribute:Name']=='U14']
# df3= df_walls.loc[df_walls['Attribute:Name']=='M3']
# df_twowalls = pd.concat([df1,df2,df3])

#two_walls = runSimulationforHouse(1, 'House Prototype', df_walls, df_studs, df_doors, df_windows,'Greedy', 0, 1)
house = runSimulationForHouse(1, 'Residential House Prototype', df_walls, df_studs, df_doors, df_windows, 'BestFit', 4, 0.5)
#house.getDrywallDF().to_csv(r'C:\Users\josec\Desktop\Python Prototype\Results_Base_Case_Drywall.csv', index = None, header=True)
#house.getWasteDF().to_csv(r'C:\Users\josec\Desktop\Python Prototype\Results_Base_Case_Waste.csv', index = None, header=True)

df_drywall = house.getDrywallDF()
df_waste = house.getWasteDF()
visualization(df_drywall, df_waste)