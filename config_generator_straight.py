
import yaml

from dicent_utils import *
from upload_utils import *
from config import RELATIVE_TRIGGER_POSITIONS
from operator import *

config = {}
config['Map'] = [139, 166]


# config['Center'] = '457 164'

egoStraightAsideLeft = {'Start_pos': [0, -1, 40, 0, 1], 'End_pos': [1, 1, 10, 0, 1],'Start_speed': 30}
egoStraightAsideRight = {'Start_pos': [0, -2, 40, 0, 1], 'End_pos': [1, 2, 10, 0, 1],'Start_speed': 30}


agentFromSameDirectionAsideLeft = [0, -1, 60, 0, 1]
agentFromSameDirectionAsideRight = [0, -2, 60, 0, 1]
# agentFromOppositeDirectionAsideLeft = '2 -1 20'
# # agentFromOppositeDirectionAsideRight = '2 -2 20'
agentToSameDirectionAsideLeft = [1, 1, 60, 0, 1]
agentToSameDirectionAsideRight = [1, 2, 60, 0, 1]
# agentToSameRoadOppositeDirectionAsideLeft = '0 -1 20'
# # agentToOppositeDirectionAsideRight = '2 -2 20'
# agentFromLeft = '1 1 20'
# agentFromRight = '3 1 20'
# agentToLeft = '1 -1 20'
# agentToRight = '3 -1 20'


# BehaviorMode
AgentSpeed = 40
AgentLowSpeed = 10
DynamicDuration = 3 #3.0
DynamicHaltDuration = 1 #1
DynamicDelay = 1 #1

BehaviorMode = {}
BehaviorMode['keeping']  = ('Cruise.',AgentSpeed, AgentSpeed, DynamicDuration, 'linear', DynamicDelay,'drivingForward','cruising') #等速
BehaviorMode['braking'] = ('Braking.',AgentSpeed, AgentLowSpeed, DynamicDuration, 'linear', DynamicDelay,'drivingForward','braking')  #減速
BehaviorMode['braking_halt'] = ('Braking & Halted halfway.',AgentSpeed, 0, DynamicHaltDuration, 'linear', DynamicDelay,'drivingForward','braking') #減速|未完成
BehaviorMode['sudden_braking_halt'] = ('Sudden braking & Halted halfway.',AgentSpeed, 0, DynamicHaltDuration, 'sinusoidal', DynamicDelay,'drivingForward','braking')  #急煞|未完成
BehaviorMode['speed_up'] = ( 'Speed up.',0, AgentSpeed, DynamicDuration-1, 'linear', DynamicDelay-1,'drivingForward','accelerating') #加速
    



##### Ego Go Straight Aside Right #####
config['Ego'] = egoStraightAsideLeft
config['Actors'] = None

agent1 = {}
agent1['Type'] = 'car_red'


# cut-in : Agent at 5 cut in
if 1: 
    lateral_behavior = 'CI'
    descript = "Agent at 5 cut in"
    itri_tags = ['']
    # lateral_behavior = 'CI'
    relative_pos = 'SR-5'
    initRelPostAbbvLon = relative_pos[0]
    initRelPostAbbvLat = relative_pos[1]

    egoTriggerAt = [0, -1, 50, 0, 1]
    agent1_lat_mode = 'changingLane'
    agent1_lat_direction = 'left'
    agent1_init_direction = 'sameAsEgo'

    agent1['Start_pos'] = set_agentStart_from_relative_triggerAt(egoTriggerAt, relative_pos)
    agent1['Start_speed'] = None
    agent1['Start_trigger'] = set_trigger_dict_from_absolute_pos(road=egoTriggerAt[0], 
                                                                    lane=egoTriggerAt[1], 
                                                                    s=egoTriggerAt[2], 
                                                                    offset=egoTriggerAt[3])
    agent1['Acts'] = []

    agent1_act = {}
    agent1_act['Type'] = 'Cut-in'
    agent1_act['Delay'] = 0
    agent1_act['Events'] = []

    agent1_lat_event = {}
    agent1_lat_event['Type'] = 'cut'
    agent1_lat_event['Dynamic_delay'] = 0
    agent1_lat_event['Dynamic_duration'] = 2.5
    agent1_lat_event['Dynamic_shape'] = 'sinusoidal'
    agent1_lat_event['End'] = [-1, 0]
    agent1_lat_event['Use_route'] = None

    
    for behavior_type, behavior in BehaviorMode.items():

        agent1['Start_speed'] = behavior[1]
        agent1_long_event = set_behavior_dict('speed',behavior)
        agent1_act['Events'] = []
        agent1_act['Events'].append(agent1_lat_event)
        agent1_act['Events'].append(agent1_long_event)
        agent1['Acts'] = [agent1_act]
        config['Actors'] = {'Agents': [agent1]}
        
        name_attribute = f'01{initRelPostAbbvLon}{initRelPostAbbvLat}-{lateral_behavior}'
        next_id = get_next_id_in_folder(name_attribute)
        scenario_name = f'{name_attribute}_{next_id}'
        config['Scenario_name'] = scenario_name
        save_config_yaml(config, f'./scenario_config/{name_attribute}/{next_id}.yaml')

        cetranNo = None
        csv_row = generate_csv_content(behavior, behavior_type, descript, lateral_behavior, scenario_name, initRelPostAbbvLat, initRelPostAbbvLon, cetranNo, agent1_lat_mode, agent1_lat_direction, agent1_init_direction)
        # print(csv_row);exit()
        write_to_scenario_table(next_id, [csv_row], file_path= f'./scenario_config/{name_attribute}/{next_id}.csv')

# cut-out : Agent at 2 cut out
if 1: 
    descript = "Agent at 2 cut out"
    lateral_behavior = 'CO'
    relative_pos = 'FS-2'
    initRelPostAbbvLon = relative_pos[0]
    initRelPostAbbvLat = relative_pos[1]

    egoTriggerAt = [0, -1, 50, 0, 1]
    agent1_lat_mode = 'changingLane'
    agent1_lat_direction = 'right'
    agent1_init_direction = 'sameAsEgo'

    agent1['Start_pos'] = set_agentStart_from_relative_triggerAt(egoTriggerAt, relative_pos)
    agent1['Start_speed'] = None
    agent1['Start_trigger'] = set_trigger_dict_from_absolute_pos(road=egoTriggerAt[0], 
                                                                    lane=egoTriggerAt[1], 
                                                                    s=egoTriggerAt[2], 
                                                                    offset=egoTriggerAt[3])

    agent1['Acts'] = []

    agent1_act = {}
    agent1_act['Type'] = 'cut'
    agent1_act['Delay'] = 0
    agent1_act['Events'] = []

    agent1_lat_event = {}
    agent1_lat_event['Type'] = 'cut'
    agent1_lat_event['Dynamic_delay'] = 0
    agent1_lat_event['Dynamic_duration'] = 2.5
    agent1_lat_event['Dynamic_shape'] = 'sinusoidal'
    agent1_lat_event['End'] = [-2, 0] #set_agentpos_relative_to_egopos(config['Ego']['Start_pos'], s_offset=1) 
    agent1_lat_event['Use_route'] = None

    
    for behavior_type, behavior in BehaviorMode.items():

        agent1['Start_speed'] = behavior[1]
        agent1_long_event = set_behavior_dict('speed',behavior)
        agent1_act['Events'] = []
        agent1_act['Events'].append(agent1_lat_event)
        agent1_act['Events'].append(agent1_long_event)
        agent1['Acts'] = [agent1_act]
        config['Actors'] = {'Agents': [agent1]}
        
        name_attribute = f'01{initRelPostAbbvLon}{initRelPostAbbvLat}-{lateral_behavior}'
        next_id = get_next_id_in_folder(name_attribute)
        scenario_name = f'{name_attribute}_{next_id}'
        config['Scenario_name'] = scenario_name
        save_config_yaml(config, f'./scenario_config/{name_attribute}/{next_id}.yaml')

        cetranNo = None
        csv_row = generate_csv_content(behavior, behavior_type, descript, lateral_behavior, scenario_name, initRelPostAbbvLat, initRelPostAbbvLon, cetranNo, agent1_lat_mode, agent1_lat_direction, agent1_init_direction)
        # print(csv_row);exit()
        write_to_scenario_table(next_id, [csv_row], file_path= f'./scenario_config/{name_attribute}/{next_id}.csv')

# keeping at 2
if 1:
    lateral_behavior = 'KEEP'
    descript == "keeping at 2"
    relative_pos = 'FS-2'
    initRelPostAbbvLon = relative_pos[0]
    initRelPostAbbvLat = relative_pos[1]
    
    egoTriggerAt = [0, -1, 50, 0, 1]
    agent1_lat_mode = 'goingStraight'
    agent1_lat_direction = ''
    agent1_init_direction = 'sameAsEgo'

    agent1['Start_pos'] = set_agentStart_from_relative_triggerAt(egoTriggerAt, relative_pos)
    agent1['Start_speed'] = None
    agent1['Start_trigger'] = set_trigger_dict_from_absolute_pos(road=egoTriggerAt[0], 
                                                                 lane=egoTriggerAt[1], 
                                                                 s=egoTriggerAt[2], 
                                                                 offset=egoTriggerAt[3])
    agent1['Acts'] = []
    

    agent1_act = {}
    agent1_act['Type'] = 'Keeping'
    agent1_act['Delay'] = 0
    agent1_act['Events'] = []

    agent1_lat_event = {}
    agent1_lat_event['Type'] = 'position'
    agent1_lat_event['Dynamic_delay'] = 0
    agent1_lat_event['Dynamic_duration'] = 1
    agent1_lat_event['Dynamic_shape'] = 'Other'
    agent1_lat_event['End'] = [1, 1, 30, 0, 1]
    agent1_lat_event['Use_route'] = None

        
    for behavior_type, behavior in BehaviorMode.items():

        agent1['Start_speed'] = behavior[1]
        agent1_long_event = set_behavior_dict('speed',behavior)
        agent1_act['Events'] = []
        agent1_act['Events'].append(agent1_lat_event)
        agent1_act['Events'].append(agent1_long_event)
        agent1['Acts'] = [agent1_act]
        config['Actors'] = {'Agents': [agent1]}
            
        name_attribute = f'01{initRelPostAbbvLon}{initRelPostAbbvLat}-{lateral_behavior}'
        next_id = get_next_id_in_folder(name_attribute)
        scenario_name = f'{name_attribute}_{next_id}'
        config['Scenario_name'] = scenario_name
        save_config_yaml(config, f'./scenario_config/{name_attribute}/{next_id}.yaml')

        cetranNo = None
        csv_row = generate_csv_content(behavior, behavior_type, descript, lateral_behavior, scenario_name, initRelPostAbbvLat, initRelPostAbbvLon, cetranNo, agent1_lat_mode, agent1_lat_direction, agent1_init_direction)
        # print(csv_row);exit()
        write_to_scenario_table(next_id, [csv_row], file_path= f'./scenario_config/{name_attribute}/{next_id}.csv')

# keeping at 2 far
if 1:
    lateral_behavior = 'KEEP'
    descript == "keeping at 2 far"
    relative_pos = 'FS-2'
    initRelPostAbbvLon = relative_pos[0]
    initRelPostAbbvLat = relative_pos[1]

    egoTriggerAt = [0, -1, 50, 0, 1]
    agent1_lat_mode = 'goingStraight'
    agent1_lat_direction = ''
    agent1_init_direction = 'sameAsEgo'
    
    agent1['Start_pos'] = set_agentStart_from_relative_triggerAt(egoTriggerAt, relative_pos)
    agent1['Start_speed'] = None
    agent1['Start_trigger'] = set_trigger_dict_from_absolute_pos(road=egoTriggerAt[0], 
                                                                 lane=egoTriggerAt[1], 
                                                                 s=egoTriggerAt[2], 
                                                                 offset=egoTriggerAt[3])
    
    agent1['Acts'] = []
    

    agent1_act = {}
    agent1_act['Type'] = 'Keeping'
    agent1_act['Delay'] = 0
    agent1_act['Events'] = []

    agent1_lat_event = {}
    agent1_lat_event['Type'] = 'position'
    agent1_lat_event['Dynamic_delay'] = 0
    agent1_lat_event['Dynamic_duration'] = 1
    agent1_lat_event['Dynamic_shape'] = 'Other'
    agent1_lat_event['End'] = [1, 1, 30, 0, 1]
    agent1_lat_event['Use_route'] = None

        
    for behavior_type, behavior in BehaviorMode.items():

        agent1['Start_speed'] = behavior[1]
        agent1_long_event = set_behavior_dict('speed',behavior)
        agent1_act['Events'] = []
        agent1_act['Events'].append(agent1_lat_event)
        agent1_act['Events'].append(agent1_long_event)
        agent1['Acts'] = [agent1_act]
        config['Actors'] = {'Agents': [agent1]}
            
        name_attribute = f'01{initRelPostAbbvLon}{initRelPostAbbvLat}-{lateral_behavior}'
        next_id = get_next_id_in_folder(name_attribute)
        scenario_name = f'{name_attribute}_{next_id}'
        config['Scenario_name'] = scenario_name
        save_config_yaml(config, f'./scenario_config/{name_attribute}/{next_id}.yaml')

        cetranNo = None
        csv_row = generate_csv_content(behavior, behavior_type, descript, lateral_behavior, scenario_name, initRelPostAbbvLat, initRelPostAbbvLon, cetranNo, agent1_lat_mode, agent1_lat_direction, agent1_init_direction)
        # print(csv_row);exit()
        write_to_scenario_table(next_id, [csv_row], file_path= f'./scenario_config/{name_attribute}/{next_id}.csv')

# Motor keeping at all
if 1:
    agent1['Type'] = 'bicycle'
    lateral_behavior = 'KEEP'
    for relative_pos in ["FL-M1","FR-M1","SL-M1","SR-M1","BL-M1","BR-M1"]:
        descript = f"Bike keeping at nearside {relative_pos[:2]}"
        # relative_pos = 'FS-2'
        initRelPostAbbvLon = relative_pos[0]
        initRelPostAbbvLat = relative_pos[1]
        
        egoTriggerAt = [0, -1, 50, 0, 1]
        agent1_lat_mode = 'goingStraight'
        agent1_lat_direction = ''
        agent1_init_direction = 'sameAsEgo'

        agent1['Start_pos'] = set_agentStart_from_relative_triggerAt(egoTriggerAt, relative_pos)
        agent1['Start_speed'] = None
        agent1['Start_trigger'] = set_trigger_dict_from_absolute_pos(road=egoTriggerAt[0], 
                                                                     lane=egoTriggerAt[1], 
                                                                     s=egoTriggerAt[2], 
                                                                     offset=egoTriggerAt[3])
        agent1['Acts'] = []
        

        agent1_act = {}
        agent1_act['Type'] = 'Keeping'
        agent1_act['Delay'] = 0
        agent1_act['Events'] = []

        agent1_lat_event = {}
        agent1_lat_event['Type'] = 'position'
        agent1_lat_event['Dynamic_delay'] = 0
        agent1_lat_event['Dynamic_duration'] = 1
        agent1_lat_event['Dynamic_shape'] = 'Other'
        agent1_lat_event['End'] = [1, 1, 30, RELATIVE_TRIGGER_POSITIONS[relative_pos][4], 1]
        agent1_lat_event['Use_route'] = None

            
        for behavior_type, behavior in BehaviorMode.items():

            agent1['Start_speed'] = behavior[1]
            agent1_long_event = set_behavior_dict('speed',behavior)
            agent1_act['Events'] = []
            agent1_act['Events'].append(agent1_lat_event)
            agent1_act['Events'].append(agent1_long_event)
            agent1['Acts'] = [agent1_act]
            config['Actors'] = {'Agents': [agent1]}
                
            name_attribute = f'01{initRelPostAbbvLon}{initRelPostAbbvLat}-{lateral_behavior}'
            next_id = get_next_id_in_folder(name_attribute)
            scenario_name = f'{name_attribute}_{next_id}'
            config['Scenario_name'] = scenario_name
            save_config_yaml(config, f'./scenario_config/{name_attribute}/{next_id}.yaml')

            cetranNo = None
            csv_row = generate_csv_content(behavior, behavior_type, descript, lateral_behavior, scenario_name, initRelPostAbbvLat, initRelPostAbbvLon, cetranNo, agent1_lat_mode, agent1_lat_direction, agent1_init_direction)
            # print(csv_row);exit()
            write_to_scenario_table(next_id, [csv_row], file_path= f'./scenario_config/{name_attribute}/{next_id}.csv')

# Motor cut in to middle/nearside
if 1:
    config['Ego'] = egoStraightAsideLeft # [0, -1, 40, 0, 1]
    agent1 = {}
    agent1['Type'] = 'bicycle'
    lateral_behavior = 'CI'
    for relative_pos, end_lane in [("FR-M1",[-1, 0]),("FR-M2",[-1, 0]),("FR-M3",[-1, 0]),("SR-M1",[-1, 0]),("SR-M2",[-1, 0]),("SR-M3",[-1, 0]),
                         ("FR-M2",[-1, 1.5]),("FR-M3",[-1, 1.5]),("SR-M2",[-1, 1.5]),("SR-M3",[-1, 1.5])]:
        descript = f"Bike cutting in to middle {relative_pos} - "
        initRelPostAbbvLon = relative_pos[0]
        initRelPostAbbvLat = relative_pos[1]
        
        # 固定ego trigger 點，來設置agent 起始位置
        egoTriggerAt = [0, -1, 50, 0, 1]
        agent1_lat_mode = 'changingLane'
        agent1_lat_direction = 'right' if relative_pos[1] == 'L' else 'left'
        agent1_init_direction = 'sameAsEgo'

        agent1['Start_pos'] = set_agentStart_from_relative_triggerAt(egoTriggerAt, relative_pos)
        agent1['Start_speed'] = None
        agent1['Start_trigger'] = set_trigger_dict_from_absolute_pos(road=egoTriggerAt[0], 
                                                                     lane=egoTriggerAt[1], 
                                                                     s=egoTriggerAt[2], 
                                                                     offset=egoTriggerAt[3])
        agent1['Acts'] = []
        

        agent1_act = {}
        agent1_act['Type'] = 'Cut-in'
        agent1_act['Delay'] = 0
        agent1_act['Events'] = []

        agent1_lat_event = {}
        agent1_lat_event['Type'] = 'cut'
        agent1_lat_event['Dynamic_delay'] = 0
        agent1_lat_event['Dynamic_duration'] = 2.5
        agent1_lat_event['Dynamic_shape'] = 'sinusoidal'
        agent1_lat_event['End'] = end_lane
        agent1_lat_event['Use_route'] = None

        
        for behavior_type, behavior in BehaviorMode.items():

            agent1['Start_speed'] = behavior[1]
            agent1_long_event = set_behavior_dict('speed',behavior)
            agent1_act['Events'] = []
            agent1_act['Events'].append(agent1_lat_event)
            agent1_act['Events'].append(agent1_long_event)
            agent1['Acts'] = [agent1_act]
            config['Actors'] = {'Agents': [agent1]}
            
            name_attribute = f'01{initRelPostAbbvLon}{initRelPostAbbvLat}-{lateral_behavior}'
            next_id = get_next_id_in_folder(name_attribute)
            scenario_name = f'{name_attribute}_{next_id}'
            config['Scenario_name'] = scenario_name
            save_config_yaml(config, f'./scenario_config/{name_attribute}/{next_id}.yaml')

            cetranNo = None
            csv_row = generate_csv_content(behavior, behavior_type, descript, lateral_behavior, scenario_name, initRelPostAbbvLat, initRelPostAbbvLon, cetranNo, agent1_lat_mode, agent1_lat_direction, agent1_init_direction)
            # print(csv_row);exit()
            write_to_scenario_table(next_id, [csv_row], file_path= f'./scenario_config/{name_attribute}/{next_id}.csv')
            
            
            
