
import yaml

from dicent_utils import *
from upload_utils import *
from config import RELATIVE_TRIGGER_POSITIONS
from operator import *

config = {}
config['Map'] = [121, 17, 144, 16]
config['Center'] = [685.61, -134.05]



egoStraightAsideLeft = {'Start_pos': [0, 1, 40, 0, 1], 'End_pos': [2, -1, 10, 0, 1],'Start_speed': 30}
egoStraightAsideRight = {'Start_pos': [0, 2, 40, 0, 1], 'End_pos': [2, -2, 10, 0, 1],'Start_speed': 30}


# agentFromSameDirectionAsideLeft = [0, -1, 60, 0, 1]
# agentFromSameDirectionAsideRight = [0, -2, 60, 0, 1]
# agentFromOppositeDirectionAsideLeft = '2 -1 20'
# # agentFromOppositeDirectionAsideRight = '2 -2 20'
# agentToSameDirectionAsideLeft = [1, 1, 60, 0, 1]
# agentToSameDirectionAsideRight = [1, 2, 60, 0, 1]
# agentToSameRoadOppositeDirectionAsideLeft = '0 -1 20'
# # agentToOppositeDirectionAsideRight = '2 -2 20'
# agentFromLeft = '1 1 20'
# agentFromRight = '3 1 20'
# agentToLeft = '1 -1 20'
# agentToRight = '3 -1 20'

"""
"FL-1": ("relative", -1,  0,  20,  0),
"FS-2": ("relative",  0,  0,  20,  0),
"FR-3": ("relative",  1,  0,  20,  0),
"SL-4": ("relative", -1,  0,   0,  0),
"SR-5": ("relative",  1,  0,   0,  0),
"BL-6": ("relative", -1,  0, -20,  0),
"BS-7": ("relative",  0,  0, -20,  0),
"BR-8": ("relative",  1,  0, -20,  0),
"""


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


# Motor Turn left
# (U turn)
# Motor Turn Right
#  Turn Left 
# (U turn)
# Keep 
## Not same direction
# keep / turn left / turn right/ u turn to same line
# Motor Turn Right(U turn)
def clone_behavior_mode_and_wriite_content(behavior_type, behavior, agent1, agent1_act, agent1_lat_event, config, initRelPostAbbvLat, initRelPostAbbvLon, lateral_behavior, descript, agent1_lat_mode, agent1_lat_direction, agent1_init_direction, cetranNo=None):
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

    csv_row = generate_csv_content(behavior, behavior_type, descript, lateral_behavior, scenario_name, initRelPostAbbvLat, initRelPostAbbvLon, cetranNo, agent1_lat_mode, agent1_lat_direction, agent1_init_direction)
    # print(csv_row);exit()
    write_to_scenario_table(next_id, [csv_row], file_path= f'./scenario_config/{name_attribute}/{next_id}.csv')



# Turn right
if 1: 
    lateral_behavior = 'TR'
    for relative_pos, use_route, shape in [("FL-1",list(config['Center']),"Curve"),("FS-2",None,"Route"),("SL-4",list(config['Center']),"Curve")]:
        descript = f"Agent at {relative_pos} turning right - "
        initRelPostAbbvLon = relative_pos[0]
        initRelPostAbbvLat = relative_pos[1]

        config['Ego'] = egoStraightAsideRight
        egoTriggerAt = [0, 2, 30, 0, 1]
        agent1_lat_mode = 'turning'
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
        agent1_act['Type'] = 'Turning'
        agent1_act['Delay'] = 0
        agent1_act['Events'] = []

        agent1_lat_event = {}
        agent1_lat_event['Type'] = 'position'
        agent1_lat_event['Dynamic_delay'] = 0
        agent1_lat_event['Dynamic_duration'] = 1
        agent1_lat_event['Dynamic_shape'] = shape
        agent1_lat_event['End'] = [3, -1, 15, 0, 1]
        agent1_lat_event['Use_route'] = use_route

        
        for behavior_type, behavior in BehaviorMode.items():
            clone_behavior_mode_and_wriite_content(behavior_type, behavior, agent1, agent1_act, agent1_lat_event, config, initRelPostAbbvLat, initRelPostAbbvLon, lateral_behavior, descript, agent1_lat_mode, agent1_lat_direction, agent1_init_direction)

#  Turn Left/Left U turn
if 1: 
    config['Ego'] = egoStraightAsideLeft

    # Agent
    lateral_behavior = 'TL'
    for relative_pos, use_route, shape in [("FS-2",None,"Route"),("FR-3",list(config['Center']),"Curve"),("SR-5",list(config['Center']),"Curve")]:
        initRelPostAbbvLon = relative_pos[0]
        initRelPostAbbvLat = relative_pos[1]

        egoTriggerAt = [0, 1, 30, 0, 1]
        agent1_lat_mode = 'turning'
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
        agent1_act['Type'] = 'Turning'
        agent1_act['Delay'] = 0
        agent1_act['Events'] = []

        for end, action in [([1, -1, 10, 0, 1],'turning left'), 
                            ([0, -1, 15, 0, 1],'left U turn')]: 
            descript = f"Agent at {relative_pos} {action} - "


            agent1_lat_event = {}
            agent1_lat_event['Type'] = 'position'
            agent1_lat_event['Dynamic_delay'] = 0
            agent1_lat_event['Dynamic_duration'] = 1
            agent1_lat_event['Dynamic_shape'] = shape
            agent1_lat_event['End'] = end
            agent1_lat_event['Use_route'] = list(config['Center']) if action == 'left U turn' else use_route

            
            for behavior_type, behavior in BehaviorMode.items():
                clone_behavior_mode_and_wriite_content(behavior_type, behavior, agent1, agent1_act, agent1_lat_event, config, initRelPostAbbvLat, initRelPostAbbvLon, lateral_behavior, descript, agent1_lat_mode, agent1_lat_direction, agent1_init_direction)

              
#  Keeping From opposite direction
if 1: 
    config['Ego'] = egoStraightAsideLeft

    # Agent
    lateral_behavior = 'KEEP'
    for relative_pos, start_pos, end_pos in [("FL-1",[1, 1, 10, 0, 1],[3, -1, 15, 0, 1]),
                                    ("FL-1",[2, 1, 10, 0, 1],[0, -1, 15, 0, 1]),
                                    ("FR-3",[3, 1, 10, 0, 1],[1, -1, 15, 0, 1])]:
        
        descript = f"Agent at {relative_pos} keeping - "
        initRelPostAbbvLon = relative_pos[0]
        initRelPostAbbvLat = relative_pos[1]

        egoTriggerAt = [0, 1, 30, 0, 1]
        agent1_lat_mode = 'goingStraight'
        agent1_lat_direction = None
        agent1_init_direction = 'oncoming'

        agent1['Start_pos'] = start_pos
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
        agent1_lat_event['Dynamic_shape'] = 'Straight'
        agent1_lat_event['End'] = end_pos
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


#  Left turn From opposite direction
if 1: 
    config['Ego'] = egoStraightAsideLeft

    # Agent
    lateral_behavior = 'TL'
    for relative_pos, start_pos, end_pos in [("FL-1",[1, 1, 10, 0, 1],[2, -1, 15, 0, 1]),
                                             ("FL-1",[2, 1, 10, 0, 1],[3, -1, 15, 0, 1]),
                                             ("FR-3",[3, 1, 10, 0, 1],[0, -1, 15, 0, 1])]:
        
        descript = f"Agent at {relative_pos} turning left - "
        initRelPostAbbvLon = relative_pos[0]
        initRelPostAbbvLat = relative_pos[1]

        egoTriggerAt = [0, 1, 30, 0, 1]
        agent1_lat_mode = 'goingStraight'
        agent1_lat_direction = None
        agent1_init_direction = 'oncoming'

        agent1['Start_pos'] = start_pos
        agent1['Start_speed'] = None
        agent1['Start_trigger'] = set_trigger_dict_from_absolute_pos(road=egoTriggerAt[0], 
                                                                     lane=egoTriggerAt[1], 
                                                                     s=egoTriggerAt[2], 
                                                                     offset=egoTriggerAt[3])
        agent1['Acts'] = []

        agent1_act = {}
        agent1_act['Type'] = 'Turning'
        agent1_act['Delay'] = 0
        agent1_act['Events'] = []

      
        agent1_lat_event = {}
        agent1_lat_event['Type'] = 'position'
        agent1_lat_event['Dynamic_delay'] = 0
        agent1_lat_event['Dynamic_duration'] = 1
        agent1_lat_event['Dynamic_shape'] = 'Route'
        agent1_lat_event['End'] = end_pos
        agent1_lat_event['Use_route'] = None

        
        for behavior_type, behavior in BehaviorMode.items():
            clone_behavior_mode_and_wriite_content(behavior_type, behavior, agent1, agent1_act, agent1_lat_event, config, initRelPostAbbvLat, initRelPostAbbvLon, lateral_behavior, descript, agent1_lat_mode, agent1_lat_direction, agent1_init_direction)


#  Right turn From opposite direction
if 1: 
    config['Ego'] = egoStraightAsideLeft

    # Agent
    lateral_behavior = 'TL'
    for relative_pos, start_pos, end_pos in [("FR-3",[3, 1, 10, 0, 1],[2, -1, 15, 0, 1])]:
        
        descript = f"Agent at {relative_pos} turning left - "
        initRelPostAbbvLon = relative_pos[0]
        initRelPostAbbvLat = relative_pos[1]

        egoTriggerAt = [0, 1, 30, 0, 1]
        agent1_lat_mode = 'goingStraight'
        agent1_lat_direction = None
        agent1_init_direction = 'oncoming'

        agent1['Start_pos'] = start_pos
        agent1['Start_speed'] = None
        agent1['Start_trigger'] = set_trigger_dict_from_absolute_pos(road=egoTriggerAt[0], 
                                                                     lane=egoTriggerAt[1], 
                                                                     s=egoTriggerAt[2], 
                                                                     offset=egoTriggerAt[3])
        agent1['Acts'] = []

        agent1_act = {}
        agent1_act['Type'] = 'Turning'
        agent1_act['Delay'] = 0
        agent1_act['Events'] = []

      
        agent1_lat_event = {}
        agent1_lat_event['Type'] = 'position'
        agent1_lat_event['Dynamic_delay'] = 0
        agent1_lat_event['Dynamic_duration'] = 1
        agent1_lat_event['Dynamic_shape'] = 'Route'
        agent1_lat_event['End'] = end_pos
        agent1_lat_event['Use_route'] = None

        
        for behavior_type, behavior in BehaviorMode.items():
            clone_behavior_mode_and_wriite_content(behavior_type, behavior, agent1, agent1_act, agent1_lat_event, config, initRelPostAbbvLat, initRelPostAbbvLon, lateral_behavior, descript, agent1_lat_mode, agent1_lat_direction, agent1_init_direction)
            
#  Left u turn From opposite direction
if 1: 
    config['Ego'] = egoStraightAsideLeft

    # Agent
    lateral_behavior = 'TL'
    for relative_pos, start_pos, end_pos in [("FL-1",[2, 1, 10, 0, 1],[2, -1, 15, 0, 1]),
                                             ("FL-1",[2, 1, 10, 0, 1],[2, -2, 15, 0, 1])]:
        
        descript = f"Agent at {relative_pos} left U turn - "
        initRelPostAbbvLon = relative_pos[0]
        initRelPostAbbvLat = relative_pos[1]

        egoTriggerAt = [0, 1, 30, 0, 1]
        agent1_lat_mode = 'goingStraight'
        agent1_lat_direction = None
        agent1_init_direction = 'oncoming'

        agent1['Start_pos'] = start_pos
        agent1['Start_speed'] = None
        agent1['Start_trigger'] = set_trigger_dict_from_absolute_pos(road=egoTriggerAt[0], 
                                                                     lane=egoTriggerAt[1], 
                                                                     s=egoTriggerAt[2], 
                                                                     offset=egoTriggerAt[3])
        agent1['Acts'] = []

        agent1_act = {}
        agent1_act['Type'] = 'Turning'
        agent1_act['Delay'] = 0
        agent1_act['Events'] = []

      

        agent1_lat_event = {}
        agent1_lat_event['Type'] = 'position'
        agent1_lat_event['Dynamic_delay'] = 0
        agent1_lat_event['Dynamic_duration'] = 1
        agent1_lat_event['Dynamic_shape'] = 'Curve'
        agent1_lat_event['End'] = end_pos
        agent1_lat_event['Use_route'] = list(config['Center'])

        
        for behavior_type, behavior in BehaviorMode.items():
            clone_behavior_mode_and_wriite_content(behavior_type, behavior, agent1, agent1_act, agent1_lat_event, config, initRelPostAbbvLat, initRelPostAbbvLon, lateral_behavior, descript, agent1_lat_mode, agent1_lat_direction, agent1_init_direction)
            
        
############# Motor ###############
agent1['Type'] = 'bicycle'
# Turn right
if 1: 
    lateral_behavior = 'TR'
    for relative_pos in ["FL-M1","FR-M1","SL-M1","SR-M1","BL-M1","BR-M1","FL-M2","SL-M2"]:
        descript = f"Agent at {relative_pos} turning right - "
        initRelPostAbbvLon = relative_pos[0]
        initRelPostAbbvLat = relative_pos[1]

        config['Ego'] = egoStraightAsideRight
        egoTriggerAt = [0, 2, 30, 0, 1]
        agent1_lat_mode = 'turning'
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
        agent1_act['Type'] = 'Turning'
        agent1_act['Delay'] = 0
        agent1_act['Events'] = []

        agent1_lat_event = {}
        agent1_lat_event['Type'] = 'position'
        agent1_lat_event['Dynamic_delay'] = 0
        agent1_lat_event['Dynamic_duration'] = 1
        agent1_lat_event['Dynamic_shape'] = 'Curve'
        agent1_lat_event['End'] = [3, -1, 15, 0, 1]
        agent1_lat_event['Use_route'] = list(config['Center'])

        
        for behavior_type, behavior in BehaviorMode.items():
            clone_behavior_mode_and_wriite_content(behavior_type, behavior, agent1, agent1_act, agent1_lat_event, config, initRelPostAbbvLat, initRelPostAbbvLon, lateral_behavior, descript, agent1_lat_mode, agent1_lat_direction, agent1_init_direction)

#  Motor Left U turn
if 1:
    config['Ego'] = egoStraightAsideLeft

    # Agent
    lateral_behavior = 'TL'
    for relative_pos in ["FL-M1","FR-M1","SL-M1","SR-M1"]:
        initRelPostAbbvLon = relative_pos[0]
        initRelPostAbbvLat = relative_pos[1]

        egoTriggerAt = [0, 1, 30, 0, 1]
        agent1_lat_mode = 'turning'
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
        agent1_act['Type'] = 'Turning'
        agent1_act['Delay'] = 0
        agent1_act['Events'] = []

        for end, action in [ #([1, -1, 10, 0, 1],'turning left'), 
                            ([0, -1, 15, 0, 1],'left U turn')]: 
            descript = f"Agent at {relative_pos} {action} - "


            agent1_lat_event = {}
            agent1_lat_event['Type'] = 'position'
            agent1_lat_event['Dynamic_delay'] = 0
            agent1_lat_event['Dynamic_duration'] = 1
            agent1_lat_event['Dynamic_shape'] = 'Curve'
            agent1_lat_event['End'] = end
            agent1_lat_event['Use_route'] = list(config['Center'])

            
            for behavior_type, behavior in BehaviorMode.items():
                clone_behavior_mode_and_wriite_content(behavior_type, behavior, agent1, agent1_act, agent1_lat_event, config, initRelPostAbbvLat, initRelPostAbbvLon, lateral_behavior, descript, agent1_lat_mode, agent1_lat_direction, agent1_init_direction)

