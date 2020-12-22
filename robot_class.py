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

from basic_classes import *
from wall_class import Wall
 
 
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
        
        wall_edge = self.wall.getLength()
        if (wall_edge - 0.125 ) <= self.getRobotPosition().getX():
            self.setRobotPosition(self.getRobotPosition().getNewPosition(1, 0))
            print("Edge of the Wall - Break loop and start next row or wall")
            print("Row Done")
            return False
        
        drywall_list = CreateDrywallInstances(df_drywalls)
        #print(drywall_list)
        
        #Randomly select a drywall sheet
        random_drywall = random.choice(drywall_list)
        #print(random_drywall)
        #print(random_drywall.getArea())
        
        #Calculate possible next_position
        delta_X = random_drywall.getWidth()
        print('Random_Drywall_Width: ' + str(delta_X))
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
            
            print('No, it is outside the wall')
                        
            #Locate closest stud
            position_X = next_position.getX()
            distances = position_X - studs_locationX_array 
            #print(position_X)
            #print(studs_locationX_array)
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
            
            # If new_drywall_width <= 0, 
            # it means the drywall edge fits on the edge of the wall.
            # Add some distance to break the loop in Simulation
            print("Cutting loss VC width", cutting_loss_VC_width)
            #print(new_drywall_width)
            if new_drywall_width <= 0:
                self.setRobotPosition(next_position.getNewPosition(1, 0))
                print('Row Done!!')
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
            print("Yes, it is inside the wall")
            
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
                        print('No need to stagger joints')
                        
                        self.setRobotPosition(next_position)
                        
                        #Check if robot position is at the edge of the wall (to include joint or not)
                        #wall_edge = self.wall.getLength()
                        #if (wall_edge - 0.0625 ) <= self.getRobotPosition().getX() <= (wall_edge + 0.0625):
                        #    self.wall.setJointsDF(self)
                        
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
                print('No, it is not Located on a Stud')
                
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
                print('Is Edge around an Opening Corner?')
                #print(new_position)
                if isEdgeAroundDoorOpeningCorner(self, new_position) == True or \
                    isEdgeAroundWindowOpeningCorner(self, new_position) == True:
                        print('PROBLEM - Select different drywall size')
                        return False
                
                else:
                   
                    #Do we need to stagger Joints?
                    joints = self.wall.getJoints()
                    print('Joints: ', joints)
                    
                    if staggerJoints(self, new_position)==True:
                        print('PROBLEM - Select different drywall size')
                        return False
                    
                    else:
                        #print('No need to stagger joints')
                        self.setRobotPosition(new_position)
                        #print('Robot Position: ' + str(self.getRobotPosition()))
                        
                        #Check if robot position is at the edge of the wall (to include joint or not)
                        #wall_edge = self.wall.getLength()
                        #if (wall_edge - 0.0625 ) <= self.getRobotPosition().getX() <= (wall_edge + 0.0625):
                        #    self.wall.setJointsDF(self)
              
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
        
        wall_edge = self.wall.getLength()
        if (wall_edge - 0.125 ) <= self.getRobotPosition().getX():
            self.setRobotPosition(self.getRobotPosition().getNewPosition(1, 0))
            print("Edge of the Wall - Break loop and start next row or wall")
            print("Row Done")
            return False
        
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
            #nominal_area = cut.getDrywall().getNominalArea()            
            #print(cut.getArea()/nominal_area)
            if cut.getHeight() >= self.getRowHeight() and cut.getWidth() > 1.33333 and no_cuts < max_cuts and cut.compliesArea(min_area): #1.33333 == 16in (Min stud frame spacing)
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
                    #If new_drywall_width <= 0, 
                    #it means the drywall edge fits on the edge of the wall.
                    #Add some distance to break the loop in Simulation
                    if new_cut_width <= 0:
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
                            #if cutting_loss_VC_width == 0 or cutting_loss_HC_height == 0:
                             #   print('FULL CUT')
                            self.wall.getBackupWaste().drop(index, axis=0, inplace=True)
                            
                            #else:
                             #   print('Adjust new size of cut & Add extra losses')
                                #Update Waste Dataframe
                                #simulation_number = 'Simulation_' + str(self.getSimulationNumber())
                                #cut.setWallName(wall_name)
                                #self.wall.updateWasteDF(cut, simulation_number) # Keep cut in previous wall
                                #self.wall.getBackupWaste().drop(index, axis=0, inplace=True)
                                #self.wall.updateWasteDF_VC_HC(self.getDrywall(), simulation_number)
                            
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
                                #wall_edge = self.wall.getLength()
                                #if (wall_edge - 0.0625 ) <= self.getRobotPosition().getX() <= (wall_edge + 0.0625):
                                #    self.wall.setJointsDF(self)
                                
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
                                #print(cutting_loss_HC_height)
                                #if cutting_loss_HC_height == 0:
                                 #   print('FULL CUT')
                                self.wall.getBackupWaste().drop(index, axis=0, inplace=True)
                                   # print(self.wall.getBackupWaste())
                                #else:
                                 #   print('Adjust new size of cut & Add extra losses')
                                    #Update Waste Dataframe
                                  #  simulation_number = 'Simulation_' + str(self.getSimulationNumber())
                                    #cut.setWallName(wall_name)
                                    #self.wall.updateWasteDF(cut, simulation_number)
                                   # self.wall.getBackupWaste().drop(index, axis=0, inplace=True)
                                    #self.wall.updateWasteDF_VC_HC(self.getDrywall(), simulation_number)
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
                                #wall_edge = self.wall.getLength()
                                #if (wall_edge - 0.0625 ) <= self.getRobotPosition().getX() <= (wall_edge + 0.0625):
                                #    self.wall.setJointsDF(self)
                      
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
                                if x <= 0: # it means the sheet's width is less than the stud spacing
                                    return False
                                
                                else:
                                    cut_position = new_position.getNewPosition(-x, 0)
                                    self.wall.placeDrywallAtPosition(cut_position, cut_as_drywall)
                                    
                                    #self.wall.updateDrywallDataframe(drywall_position, random_drywall, simulation_number)
                                    cut_as_drywall.setPosition(cut_position)
                                    self.setDrywall(cut_as_drywall)
                                    
                                    # if new cut HC height OR cut VC width is  0, drop row from waste df
                                    #print(self.wall.getWaste())
                                    #if cutting_loss_VC_width == 0 and cutting_loss_HC_height == 0:
                                     #   print('FULL CUT')
                                        #print(self.wall.getBackupWaste())
                                    self.wall.getBackupWaste().drop(index, axis=0, inplace=True)
                                    #else:
                                     #   print('Adjust new size of cut & Add extra losses')
                                        #Update Waste Dataframe
                                      #  simulation_number = 'Simulation_' + str(self.getSimulationNumber())
                                        #cut.setWallName(wall_name)
                                        #self.wall.updateWasteDF(cut, simulation_number)
                                       # self.wall.getBackupWaste().drop(index, axis=0, inplace=True)
                                        #self.wall.updateWasteDF_VC_HC(self.getDrywall(), simulation_number)
                                    # print('CUT WAS PLACED ON THE WALL!!')
                                    # print('Iteration: ' + str(index))
                                    
                                    return True
                                    break
                                
    def reuseCuttingLosses_BestFit(self, df_waste, min_area): #, cuts_allowed, area_allowed
        """
        Simulate the passage of a single time-step.

        Move the robot to a new position and mark the stud it is on as having
        been placed if complies with design rules. Keeps track of drywall cuts.
        """
        wall_edge = self.wall.getLength()
        if (wall_edge - 0.125 ) <= self.getRobotPosition().getX():
            self.setRobotPosition(self.getRobotPosition().getNewPosition(1, 0))
            print("Edge of the Wall - Break loop and start next row or wall")
            print("Row Done")
            return False
        
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
            
            if cut.getHeight() >= self.getRowHeight() and cut.getWidth() > 1.33333 and cut.compliesArea(min_area):
                
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
                            #wall_edge = self.wall.getLength()
                            #if (wall_edge - 0.0625 ) <= self.getRobotPosition().getX() <= (wall_edge + 0.0625):
                            #    self.wall.setJointsDF(self)
                            
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
                            
                            print('Cut width: ' + str(x))
                            
                            if x <= 0: # it means the sheet's width is less than the stud spacing
                                return False
                                
                            else:
                                cut_position = next_position.getNewPosition(-x, 0)
                                self.wall.placeDrywallAtPosition(cut_position, cut_as_drywall)
                                
                                #self.wall.updateDrywallDataframe(drywall_position, random_drywall, simulation_number)
                                cut_as_drywall.setPosition(cut_position)
                                self.setDrywall(cut_as_drywall)
                                
                                # if new cut HC height OR cut VC width is  0, drop row from waste df
                                #print(self.wall.getWaste())
                                #if cutting_loss_VC_width == 0 and cutting_loss_HC_height == 0:
                                 #   print('FULL CUT')
                                    #print(self.wall.getBackupWaste())
                                self.wall.getBackupWaste().drop(index, axis=0, inplace=True)
                                #else:
                                 #   print('Adjust new size of cut & Add extra losses')
                                    #Update Waste Dataframe
                                  #  simulation_number = 'Simulation_' + str(self.getSimulationNumber())
                                    #cut.setWallName(wall_name)
                                    #self.wall.updateWasteDF(cut, simulation_number)
                                   # self.wall.getBackupWaste().drop(index, axis=0, inplace=True)
                                    #self.wall.updateWasteDF_VC_HC(self.getDrywall(), simulation_number)
                                print('CUT WAS PLACED ON THE WALL!!')
                                # print('Iteration: ' + str(index))
                                
                                return True
                                break
                            
                                     

