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

#Import python files containing relevant classes

from basic_classes import *
from wall_class import Wall
from robot_class import Robot

#Create filenames
drywalls_filename = 'df_drywalls.csv'
walls_filename = 'df_walls.csv'
studs_filename = 'df_studs_new.csv'
#plates_filename = 'df_plates.csv'
doors_filename = 'df_doors_new.csv'
windows_filename = 'df_windows_new.csv'

#Read files
df_walls = pd.read_csv(walls_filename)
df_studs = pd.read_csv(studs_filename)
#df_plates = pd.read_csv(plates_filename)
df_drywalls = pd.read_csv(drywalls_filename)
df_doors = pd.read_csv(doors_filename)
df_windows = pd.read_csv(windows_filename)



def runSimulation_Wall_to_Wall(trial, wall_name, wall_length, wall_height, unique_stud_df, unique_door_df, unique_window_df, df_waste, max_cuts, min_area):
    
    #random.seed(42)
    #Instanciate the wall
    wall = Wall(wall_name, wall_length, wall_height, unique_stud_df, unique_door_df, unique_window_df)
    #Instanciate the robot:
    robot = Robot(wall)
    robot.setSimulationNumber(trial)
    simulation_number = 'Simulation_' + str(robot.getSimulationNumber())   
    df_waste_copy = df_waste.copy()
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
                #wall.visualization(trial, total_cutting_loss_area)
                
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
            #print(rows_height)
       
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
        row = 0
        while row < len(rows_height):
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
              
                if df_waste.empty == False and robot.reuseCuttingLosses_BestFit(df_waste, min_area) == True:
                    
                    clipperAtDoor(robot, robot.getDrywall()) 
                    clipperAtWindow(robot, robot.getDrywall())
                    
                    robot.wall.updateDrywallDataframe(robot.getDrywall().getPosition(), robot.getDrywall(), simulation_number)
                    robot.wall.updateWasteDF_VC_HC(robot.getDrywall(), simulation_number)
                    
                    #print(robot.wall.getWaste()[['simulation', 'wall', 'name', 'width','type_of_cut']])
                    robot.wall.backup_WasteDF(robot.wall.getWaste())
                    #print('Temp. Waste DF: ') 
                    #print(robot.wall.getBackupWaste()[['simulation', 'wall', 'name', 'width','type_of_cut']])
                    #print('Drywall DF: ')
                    #print(robot.wall.getWallDataframe()[['simulation', 'wall', 'name', 'no_cuts']])
                    
                    #Add joint to Joints DataFrame
                    robot_position = robot.getRobotPosition()
                    wall_edge = robot.wall.getLength()
                    if robot.getRobotPosition().getX() < (wall_edge - 0.0625):
                        joints.append(robot_position.getX())  
                   
                 
                elif df_waste.empty == False and robot.reuseCuttingLosses_Greedy(df_waste, max_cuts, min_area) == True:
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
                        wall_edge = robot.wall.getLength()
                        print(wall_edge)
                        if robot.getRobotPosition().getX() < (wall_edge - 0.0625):
                            joints.append(robot_position.getX())  
                
                else:
                    
                    if temp_time_steps > 25:
                        temp_time_steps = 0
                        joints = []
                        #Break while loop
                        wall.backup_waste.drop(wall.backup_waste.index, inplace=True)
                        robot.wall.backup_WasteDF(df_waste_copy) 
                        robot.wall.DropDrywallResults(simulation_number)
                        origin = Position(0, 0)
                        robot.setRobotPosition(origin)
                        delta_X = 0
                        delta_Y = 0
                        row=-1
                        print('Disregard simulation')
                        break
                    
                    
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
                        #print('Drywall DF: ')
                        #print(robot.wall.getWallDataframe()[['simulation', 'wall', 'name', 'no_cuts']])
                        #Add joint to Joints DataFrame
                        robot_position = robot.getRobotPosition()
                        
                        wall_edge = robot.wall.getLength()
                        #print(wall_edge)
                        if robot.getRobotPosition().getX() < (wall_edge - 0.0625):
                            joints.append(robot_position.getX())  
                    
                        #print('Row Joints: ', joints)
                
                                
                #print("Wall: " + str(wall))
                #print("")
                
                #print(wall.isPositionInWall(robot.getRobotPosition()))
                
                #Add joint to Joints DataFrame
                #robot.wall.setJointsDF(robot)
                
                if wall.isPositionInWall(robot.getRobotPosition()) == False:
                    # print(robot.getRobotPosition())
                    #print("Row " + str(row) + " complete.")
                    delta_X = -robot.getRobotPosition().getX()
                    delta_Y = 4
                    break
             
            # if temp_time_steps > 25:
            #     temp_time_steps = 0
            #     wall.backup_waste.drop(wall.backup_waste.index, inplace=True)
            #     robot.wall.backup_WasteDF(df_waste_copy)
            #     robot.wall.DropDrywallResults(simulation_number)
            #     #Restart while loop
            #     row = 0
            #     origin = Position(0, 0)
            #     robot.setRobotPosition(origin)
            #     delta_X = 0
            #     delta_Y = 0
            #     print('Restart While Loop')
                
            
            wall.setJoints(row, joints)
            row += 1
            print('Wall Joints: ', wall.getJoints())
            robot.wall.setJointsDF(robot, joints)
                
        wall.saveWasteDF()
        
        print(robot.wall.getJointsDF())
        origin = Position(0, 0)
        robot.setRobotPosition(origin)     
        
        print(' ')
        
        print("End of simulation #" + str(trial))        
        
        cutting_losses = wall.getCuttingLosses()
        total_cutting_loss_area = round(np.sum(cutting_losses), 4)
        
        #wall.saveWasteDF()
        #print(wall.getWasteDF())
        
        #wall.visualization(trial, total_cutting_loss_area)
                
        return wall

  

def runSimulation_floor(num_trials, floor_name, df_walls, df_studs, df_doors, df_windows, max_cuts, min_area):
    
    random.seed(0)
    
    floor = Floor(floor_name)
    
    # Loop through num_trials
    for trial in range(num_trials):
        
        df_waste = pd.DataFrame()
        
        #Loop through each wall in the corresponding house floor
        for index, value in df_walls.iterrows():
            
            wall_name = df_walls.loc[index, 'Attribute:ID']
            print('Start Simulation for Wall: ' + str(wall_name))
            
            wall_length = df_walls.loc[index, 'Attribute:Length']
            wall_height = df_walls.loc[index, 'Attribute:Height']
            unique_stud_df = np.round(df_studs.loc[df_studs['Attribute:ID']== wall_name], 4)
            unique_door_df = np.round(df_doors.loc[df_doors['Attribute:ID']== wall_name], 4)
            unique_window_df = np.round(df_windows.loc[df_windows['Attribute:ID']== wall_name], 4)
            
            
            wall = runSimulation_Wall_to_Wall(trial, wall_name, wall_length, wall_height, unique_stud_df, unique_door_df, unique_window_df, df_waste, max_cuts, min_area)
            
            df_waste = wall.getWasteDF()
            #print(df_waste)
            print('----------------------------------------')
            #print(df_waste)
            #wall.backup_WasteDF()
            
            #print(wall)
            #print(wall.getWallDataframe())
            floor.saveDrywallDF(wall.getWallDataframe())
            floor.saveJointsDF(wall.getJointsDF())
        
        floor.saveWasteDF(wall.getWasteDF())
        
        #print(wall.getWasteDF())
        
            
        print('End Simulation for Wall: ' + str(wall_name))
        print(' ')
    
    return floor


def runSimulationForHouse(num_trials, house_name, df_walls, df_studs, df_doors, df_windows, max_cuts, min_area):
    
    #random.seed(0)
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
        floor = runSimulation_floor(num_trials, floor_name, df_walls_floor, df_studs, df_doors, df_windows, max_cuts, min_area)
        
        #Append the results from each floor simulation to the house list
        house.saveDrywallDF(floor.getDrywallDF())
        house.saveWasteDF(floor.getWasteDF())
        house.saveJointsDF(floor.getJointsDF())
        
        print('End Simulation for Floor: ' + str(floor_name))
        print(' ')
        
        #print(wall.getWallDataframe())
    
    return house
                

# df1 = df_walls.loc[df_walls['Attribute:ID']==848955]
# df2 = df_walls.loc[df_walls['Attribute:ID']==848957]
# df3= df_walls.loc[df_walls['Attribute:ID']==848959]
# df4= df_walls.loc[df_walls['Attribute:ID']==848960]
# df5= df_walls.loc[df_walls['Attribute:ID']==848961]
# df6= df_walls.loc[df_walls['Attribute:ID']==848962]
# df_twowalls = pd.concat([df1,df2,df3,df4,df5,df6])

# # 2 walls
# house = runSimulationForHouse(5, 'House Prototype', df_twowalls, df_studs, df_doors, df_windows, 10, 32)

#HOUSE
house = runSimulationForHouse(1, 'Residential House Prototype', df_walls, df_studs, df_doors, df_windows, 10, 12)
# with pd.ExcelWriter(r'C:\Users\jcuellar\Desktop\Desktop\Python Prototype\Python Prototype\Final Prototype\Final Results\WW_Results_drywall_CutWidth0.xlsx') as writer:  
#     house.getDrywallDF().to_excel(writer, sheet_name='Sheet1', index=None)
# with pd.ExcelWriter(r'C:\Users\jcuellar\Desktop\Desktop\Python Prototype\Python Prototype\Final Prototype\Final Results\WW_Results_waste_CutWidth0.xlsx') as writer:  
#     house.getWasteDF().to_excel(writer, sheet_name='Sheet1', index=None)
# with pd.ExcelWriter(r'C:\Users\jcuellar\Desktop\Desktop\Python Prototype\Python Prototype\Final Prototype\Final Results\WW_Results_joints_CutWidth0.xlsx') as writer:  
#     house.getJointsDF().to_excel(writer, sheet_name='Sheet1', index=None)
# house.getDrywallDF().to_csv(r'C:\Users\jcuellar\Desktop\Desktop\Python Prototype\Python Prototype\Final Prototype\Final Results\WW_Results_drywall_CutArea32.csv', index = None, header=True)
# house.getWasteDF().to_csv(r'C:\Users\jcuellar\Desktop\Desktop\Python Prototype\Python Prototype\Final Prototype\Final Results\WW_Results_waste_CutArea32.csv', index = None, header=True)
# house.getJointsDF().to_csv(r'C:\Users\jcuellar\Desktop\Desktop\Python Prototype\Python Prototype\Final Prototype\Final Results\WW_Results_joints_CutArea32.csv', index = None, header=True)

df_drywall = house.getDrywallDF()
df_waste = house.getWasteDF()
# df_joints = house.getJointsDF()
visualization(df_drywall, df_waste, df_doors, df_windows)