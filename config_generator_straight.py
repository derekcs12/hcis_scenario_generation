
import yaml

from dicent_utils import *
from upload_utils import *
from config import RELATIVE_POSITIONS

config = {}
config['Map'] = [139, 166]


# config['Center'] = '457 164'

egoStraightAsideLeft = {'Start_pos': [0, -1, 50, 0, 1], 'End_pos': [1, 1, 10, 0, 1],'Start_speed': 30}
egoStraightAsideRight = {'Start_pos': [0, -2, 50, 0, 1], 'End_pos': [1, 2, 10, 0, 1],'Start_speed': 30}


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
    
def get_param_by_behaviormode(behavior_type):
    if behavior_type == 'keeping':
        # Agent1_S, Agent1Speed, Agent1LowSpeed, Agent1DynamicDuration, Agent1DynamicDelay
        return ['0-20','40-60','40-60','5-5','0-3']
    elif behavior_type == 'braking':
        return ['0-20','40-60','10-20','3-5','0-3']
    elif behavior_type == 'braking_halt':
        return ['0-20','40-60','0-0','2-4','0-3']
    elif behavior_type == 'sudden_braking_halt':    
        return ['0-20','40-60','0-0','0.5-2','0-3'] 
    elif behavior_type == 'speed_up':    
        return ['0-20','0-10','40-60','2-4','0-2']


##### Ego Go Straight Aside Right #####
config['Ego'] = egoStraightAsideLeft
config['Actors'] = None

agent1 = {}
agent1['Type'] = 'car_red'


# cut-in
lateral_behavior = 'CI'
descript = "Agent at 5"

if descript == "Agent at 5": 
    # lateral_behavior = 'CI'
    relative_pos = 'SR-5'
    initRelPostAbbvLon = relative_pos[0]
    initRelPostAbbvLat = relative_pos[1]

    agent1['Start_pos'] = agentFromSameDirectionAsideRight
    agent1['Start_speed'] = None
    agent1['Start_trigger'] = set_trigger_dict_from_relative_pos(relative_pos)
    # print(agent1['Start_trigger']);exit()
    agent1['Acts'] = []

    agent1_act = {}
    agent1_act['Type'] = 'cut'
    agent1_act['Delay'] = 0
    agent1_act['Events'] = []

    agent1_lat_event = {}
    agent1_lat_event['Type'] = 'cut'
    agent1_lat_event['Dynamic_delay'] = 0
    agent1_lat_event['Dynamic_duration'] = 1
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
        #Write scenario description
        content = ScenarioContent('junction', cetran_number=cetranNo)
        content.ego_long_mode = 'drivingForward'
        content.ego_long_mode_type = 'cruising'
        content.ego_lat_mode = 'goingStraight'
        content.agents[0].update({
                            'long_mode': behavior[6],
                            'long_mode_type': behavior[7],
                            'lat_mode': 'turning',
                            'lat_direction': 'left',
                            'init_direction': 'sameAsEgo',
                            'init_dynm': get_tag(behavior[1], 'init_dynm'),
                            'init_lat_pos': get_tag(initRelPostAbbvLat, 'init_lat_pos'),
                            'init_long_pos': get_tag(initRelPostAbbvLon, 'init_long_pos'),
                            'S': get_param_by_behaviormode(behavior_type)[0],
                            'Speed': get_param_by_behaviormode(behavior_type)[1],
                            '1_1_EndSpeed': get_param_by_behaviormode(behavior_type)[2],
                            '1_1_DynamicDuration': get_param_by_behaviormode(behavior_type)[3],
                            '1_1_DynamicDelay': get_param_by_behaviormode(behavior_type)[4],
                        })
        description = descript + behavior_type + lateral_behavior
        csv_row = {'description': description, 'scenario_name': scenario_name}
        csv_row.update(content.to_dict())
        # print(csv_row);exit()
        write_to_scenario_table(next_id, [csv_row], file_path= f'./scenario_config/{name_attribute}/{next_id}.csv')
        # break
