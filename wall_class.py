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

import basic_classes


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
        self.wall_name = int(wall_name)
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
    def setJointsDF(self, robot, joints):
        simulation_number = 'Simulation_' + str(robot.getSimulationNumber())
        #columns=['simulation', 'wall', 'x', 'y', 'length']
        df = pd.DataFrame(joints, columns=['x'])
        df['simulation'] = simulation_number
        df['wall'] = self.wall_name
        df['y'] = robot.getRobotPosition().getY()
        df['length'] = robot.getRowHeight()
        df = df[['simulation', 'wall', 'x', 'y', 'length']]
        #df = pd.DataFrame(np.array([[simulation_number, self.wall_name, robot.getRobotPosition().getX(), robot.getRobotPosition().getY(), robot.getRowHeight()]]), columns=columns)
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
        df2['wall'] = df2['wall'].astype('int64')
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
        self.waste = self.waste.drop_duplicates(subset='name', keep='last')

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

        """
        #Set column labels
        columns=['simulation', 'wall', 'drywall_ID', 'drywall_object', 'cut_object','name', 'start_point_x', 'start_point_y', 'height', 'width', 'area_ft2', 'type_of_cut', 'no_cuts']

        #Import cuts
        vc = drywall.getVerticalCut() #vertical cut
        hc = drywall.getHorizontalCut() #horizontal cut
        #print('vertical cut', vc)
        #Append to dataframe if not empty
        if vc != 0:
            if vc.getArea() != 0:
                print('Yes, vertical cut should be added')
                df1 = pd.DataFrame(np.array([[simulation_number, self.wall_name, vc.getID(), vc.getDrywall(), vc, vc.getName(), vc.getPosition().getX(), vc.getPosition().getY(), vc.getHeight(), vc.getWidth(), vc.getArea(), vc.getType(), vc.getNoCuts()]]), columns=columns)
                self.waste_dataframe = self.waste_dataframe.append(df1, ignore_index=True)
                #print(self.waste_dataframe)

        if hc != 0:
            if hc.getArea() != 0:
                df2 = pd.DataFrame(np.array([[simulation_number, self.wall_name, hc.getID(), hc.getDrywall(), hc, hc.getName(), hc.getPosition().getX(), hc.getPosition().getY(), hc.getHeight(), hc.getWidth(), hc.getArea(), hc.getType(), hc.getNoCuts()]]), columns=columns)
                self.waste_dataframe = self.waste_dataframe.append(df2, ignore_index=True)
    
    def DropDrywallResults(self, simulation_number):
        self.drywall_dataframe = self.drywall_dataframe[self.drywall_dataframe['simulation']!=simulation_number]
    
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

# class Wall(object):
#     '''
#     A Wall Class represents a wall object with the following attributes:
#     - wall_name (string): unique ID which allows to identify the wall in BIM.
#     - length (float > 0): length of the wall.
#     - height (float > 0): height of the wall.
#     '''
#     def __init__(self, wall_name, length, height):
#         self.wall_name = str(wall_name)
#         self.length = float(length)
#         self.height = float(height)

    # def getArea(self):
    #     '''
    #     This functions calculates the area of the wall based on a given
    #     length and height.
    #     '''
    #     return self.length * self.height
