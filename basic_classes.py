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
df_drywalls = pd.read_csv(drywalls_filename)

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
        if vertical_cut.getArea() > 0:
            self.vertical_cut = vertical_cut
        
    def setHorizontalCut(self, horizontal_cut):
        if horizontal_cut.getArea() > 0:
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
        self.wall_name = int(wall_name)
    def compliesArea(self, min_width):
        #print(self.getArea())
        #print(nominal_area)
        if self.getWidth() >= min_width:
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

# def staggerJoints(robot, position):
    
#     joints = robot.wall.getJoints()
#     row_number = robot.getRowNumber()
#     #print(row_number)
    
#     if (len(joints)!=0) and ((row_number-1)>=0) and (position.getX() in joints[row_number-1]):
#         #print('PROBLEM - Select different drywall size')
#         return True
            
#     else:
#         #print('No need to stagger joints')
#         return False

def staggerJoints(robot, position):
    
    joints = robot.wall.getJoints()
    row_number = robot.getRowNumber()
    #print(row_number)
    x = False
    if (len(joints)!=0) and ((row_number-1)>=0):
        for joint in joints[row_number-1]:
            min_value = joint - 0.4
            max_value = joint + 0.4
            if position.getX() >= min_value and position.getX() <= max_value:
                print("Need to Stagger Joints")
                print('PROBLEM - Select different drywall size')
                x = True
                return True
    if x == False:
        print('No need to stagger joints')
        return False
    
def isEdgeAroundDoorOpeningCorner(robot, position):
  
    doors_df = robot.wall.getDoors()
    
    # Check if position is on the edge of the wall. if True, ignore rule.
    
    wall_edge = robot.wall.getLength()
    if (wall_edge - 0.125 ) <= position.getX():
        return False

    if len(doors_df)==0:
        return False
    
    else:
        x = False
        #print(position)
        
        for index, value in doors_df.iterrows():
            d_start_point_x = doors_df.loc[index, 'Doors.Openning.StartPoint.Attribute:X']
            d_start_point_y = doors_df.loc[index, 'Doors.Openning.StartPoint.Attribute:Y']
            d_end_point_x = doors_df.loc[index, 'Doors.Openning.EndPoint.Attribute:X']
            d_end_point_y = doors_df.loc[index, 'Doors.Openning.EndPoint.Attribute:Y']
            #door_width = end_point_x - start_point_x 
            #door_height = end_point_y - start_point_y  
            #print(d_start_point_x)
            #print(d_end_point_x)
        
            
            if (((d_start_point_x - 1) < position.getX()) and (position.getX() < (d_start_point_x + 1))) or \
                (((d_end_point_x - 0.125) < position.getX()) and (position.getX() < (d_end_point_x + 1))):
                    print('Edge is around Door Opening Corner')
                    x = True
                    
                    if ((position.getY() < (d_start_point_y )) and (position.getY() + 4 < (d_start_point_y ))) or \
                        (position.getY() > (d_end_point_y )):
                         return False
                    else:
                        return True
                        break
        
        if x == False:
            #print('Edge is NOT around Door Opening Corner')
            return False


def isEdgeAroundWindowOpeningCorner(robot, position):    
    
    windows_df = robot.wall.getWindows()
    
    # Check if position is on the edge of the wall. if True, ignore rule.
    
    wall_edge = robot.wall.getLength()
    if (wall_edge - 0.125 ) <= position.getX():
        return False
    
    if len(windows_df)==0:
        return False
    
    else:
        x = False
        for index, value in windows_df.iterrows():
            w_start_point_x = windows_df.loc[index, 'Windows.Openning.StartPoint.Attribute:X']
            w_start_point_y = windows_df.loc[index, 'Windows.Openning.StartPoint.Attribute:Y']
            w_end_point_x = windows_df.loc[index, 'Windows.Openning.EndPoint.Attribute:X']
            w_end_point_y = windows_df.loc[index, 'Windows.Openning.EndPoint.Attribute:Y']
            #window_width = end_point_x - start_point_x 
            #window_height = end_point_y - start_point_y
            #print(w_start_point_x)
            #print(w_end_point_x)
            
            if (((w_start_point_x - 1) <= position.getX()) and (position.getX() <= (w_start_point_x + 0.125))) or \
            (((w_end_point_x - 0.125) <= position.getX()) and (position.getX() <= (w_end_point_x + 0.8))): 
                print('Edge is around Window Opening Corner')
                x = True
                
                if ((position.getY() < (w_start_point_y )) and (position.getY() + 4 < (w_start_point_y ))) or \
                    (position.getY() > (w_end_point_y )):
                        return False
                else:
                    return True
                    break
            
        if x == False:
            #print('Edge is NOT around Door Opening Corner')
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
                       
            if drywall.getWidth()!=0:
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
                         

class Floor(object):
    def __init__(self, floor_name):
        self.floor_name = floor_name
        self.drywallDF = pd.DataFrame()
        self.wasteDF = pd.DataFrame()
        self.jointsDF = pd.DataFrame()
    def getDrywallDF(self):
        return self.drywallDF
    def saveDrywallDF(self, df_drywall):
        self.drywallDF = self.drywallDF.append(df_drywall, ignore_index=True)
    def getWasteDF(self):
        return self.wasteDF
    def saveWasteDF(self, df_waste):
        self.wasteDF = self.wasteDF.append(df_waste, ignore_index=True)
    def getJointsDF(self):
        return self.jointsDF
    def saveJointsDF(self, df_joints):
        self.jointsDF = self.jointsDF.append(df_joints, ignore_index=True)
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
     

class House(object):
    def __init__(self, house_name):
        self.house_name = house_name
        self.drywallDF = pd.DataFrame()
        self.wasteDF = pd.DataFrame()
        self.jointsDF = pd.DataFrame()
    def getDrywallDF(self):
        return self.drywallDF
    def saveDrywallDF(self, df_drywall):
        self.drywallDF = self.drywallDF.append(df_drywall, ignore_index=True)
    def getWasteDF(self):
        return self.wasteDF
    def saveWasteDF(self, df_waste):
        self.wasteDF = self.wasteDF.append(df_waste, ignore_index=True)
    def getJointsDF(self):
        return self.jointsDF
    def saveJointsDF(self, df_joints):
        self.jointsDF = self.jointsDF.append(df_joints, ignore_index=True)


def visual(name, df1, df2, df_doors, df_windows):

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
    
     #Plot doors
    doors_df = df_doors
    for index, value in doors_df.iterrows():
        start_point_x = doors_df.loc[index, 'Doors.Openning.StartPoint.Attribute:X']
        start_point_y = doors_df.loc[index, 'Doors.Openning.StartPoint.Attribute:Y']
        end_point_x = doors_df.loc[index, 'Doors.Openning.EndPoint.Attribute:X']
        end_point_y = doors_df.loc[index, 'Doors.Openning.EndPoint.Attribute:Y']
        door_width = end_point_x - start_point_x 
        door_height = end_point_y - start_point_y
        ax1.add_patch(patches.Rectangle((start_point_x, start_point_y), door_width, door_height, color='white', alpha=0.7, edgecolor='black', linewidth=3))

    #Plot windows
    windows_df = df_windows
    for index, value in windows_df.iterrows():
        start_point_x = windows_df.loc[index, 'Windows.Openning.StartPoint.Attribute:X']
        start_point_y = windows_df.loc[index, 'Windows.Openning.StartPoint.Attribute:Y']
        end_point_x = windows_df.loc[index, 'Windows.Openning.EndPoint.Attribute:X']
        end_point_y = windows_df.loc[index, 'Windows.Openning.EndPoint.Attribute:Y']
        window_width = end_point_x - start_point_x 
        window_height = end_point_y - start_point_y
        ax1.add_patch(patches.Rectangle((start_point_x, start_point_y), window_width, window_height, color='white', alpha=0.7, edgecolor='black', linewidth=3))
    
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

def visualization(df1, df2, df_doors, df_windows):
    wall_list = df1['wall'].unique().tolist()
    simulation_list = df1['simulation'].unique().tolist()
    for simulation in simulation_list:
        for wall in wall_list:
            D = df1[(df1['simulation']==simulation) & (df1['wall']==wall)]
            W = df2[(df2['simulation']==simulation) & (df2['wall']==wall)]
            doors = df_doors[(df_doors['Attribute:ID']==wall)]
            windows = df_windows[(df_windows['Attribute:ID']==wall)]
            visual(wall, D, W, doors, windows) 

