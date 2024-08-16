
from dicent_utils import *
from upload_utils import *
import yaml



import os
import glob

def remove_yaml_files(directory='./scenario_config'):
    # Construct the pattern for YAML files
    pattern = os.path.join(directory, '*.yaml')
    
    # Find all files matching the pattern
    yaml_files = glob.glob(pattern)
    
    # Remove each file
    for file in yaml_files:
        os.remove(file)
        print(f"Removed: {file}")
        
    try:
        os.remove('./HCIS_scenarios.csv')
        print(f"Removed: ./HCIS_scenarios.csv")
    except:
        pass

# Call the function
remove_yaml_files()


if 'init':
    config = {}
    config['Map'] = [121, 17, 144, 16]
    config['Center'] = '685.61 -134.05'
    
    egoStraightAsideLeft = {'Start': '0 1 40', 'End': '2 -1 40'}
    egoStraightAsideRight = {'Start': '0 2 40', 'End': '2 -2 40'}
    
    FromSameDirection_offset = 15
    agentFromSameDirectionAsideLeft = f'0 1 {FromSameDirection_offset}'
    agentFromSameDirectionAsideRight = f'0 2 {FromSameDirection_offset}'
    agentFromOppositeDirectionAsideLeft = '2 1 12'
    # agentFromOppositeDirectionAsideRight = '2 2 20'
    agentToSameDirectionAsideLeft = '2 -1 20'
    agentToSameDirectionAsideRight = '2 -2 20'
    agentToSameRoadOppositeDirectionAsideLeft = '0 -1 20'
    # agentToOppositeDirectionAsideRight = '2 -2 20'
    agentFromLeft = '1 1 10'
    agentFromRight = '3 1 10'
    agentToLeft = '1 -1 20'
    agentToRight = '3 -1 20'
    
    # BehaviorMode
    AgentSpeed = '${$Agent0Speed / 3.6}'
    AgentLowSpeed = '${$Agent0LowSpeed / 3.6}'
    DynamicDuration = '$Agent0DynamicDuration' #3.0
    DynamicHaltDuration = '${$Agent1DynamicDuration / 3}' #1
    AgentDelay = '$Agent0Delay' # 0.45
    
    # BehaviorMode
    AgentSpeed = 40
    AgentLowSpeed = 10
    DynamicDuration = 3 #3.0
    DynamicHaltDuration = 1 #1
    DynamicDelay = 1 #1
    # AgentDelay = 0.5 # 0.45
    
    
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




###### Ego Go Straight Aside Left #####
config['Ego'] = egoStraightAsideLeft
agent1 = {}


# Agent Position:2,3,5 - Turn Left 1~15
if "Agent Position:2,3,5 - Turn Left":
    lateral_behavior = 'TL'
    for agentPos, trigger, describe, cetranNo in zip([agentFromSameDirectionAsideLeft, agentFromSameDirectionAsideRight, agentFromSameDirectionAsideRight], 
                                                     [('absolute', 0, 1, 20 + 14), ('absolute', 0, 1, 20 + 14), ('absolute', 0, 1, 20)],
                                                     ['Agent at 2, turn Left', 'Agent at 3, turn Left', 'Agent at 5, turn Left'],
                                                     [65, None, None]):
        agent1['Start'] = agentPos
        agent1['End'] = agentToLeft
        agent1['Trigger'] = {}
        agent1['Trigger']['type'] = trigger[0]
        agent1['Trigger']['road'] = trigger[1]
        agent1['Trigger']['lane'] = trigger[2]
        agent1['Trigger']['s'] = trigger[3]
        
        if trigger[2] == config['Ego']['Start'][2]:
            initRelPostAbbvLat = 'S'
        else:
            initRelPostAbbvLat = 'R'
            
        if trigger[3] == 20:
            initRelPostAbbvLon = 'S'
        else:
            initRelPostAbbvLon = 'F'
            
        for type, behavior in BehaviorMode.items():
            agent1['Behavior'] = {}
            agent1['Behavior']['type'] = type
            agent1['Behavior']['Start_speed'] = behavior[1]
            agent1['Behavior']['End_speed'] = behavior[2]
            agent1['Behavior']['Dynamic_duration'] = behavior[3]
            agent1['Behavior']['Dynamic_shape'] = behavior[4]
            agent1['Behavior']['Dynamic_delay'] = behavior[5]
            
            if agentPos[2] == '2':
                agent1['Behavior']['Use_route'] = True
            else:
                agent1['Behavior']['Use_route'] = False
            
            
            config['Agents'] = [agent1]
            
            description = f'{describe} - {behavior[0]}'
            next_id = get_next_scenario_id()
            scenario_name = f'hcis_{next_id}_01{initRelPostAbbvLon}{initRelPostAbbvLat}-{lateral_behavior}'
            config['Scenario_name'] = scenario_name
            yaml.dump(config, open(f'./scenario_config/{scenario_name}.yaml', 'a+'))
            
            #Write scenario description
            content = ScenarioContent('junction', cetranNo)
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
                                'S': get_param_by_behaviormode(type)[0],
                                'Speed': get_param_by_behaviormode(type)[1],
                                'LowSpeed': get_param_by_behaviormode(type)[2],
                                'DynamicDuration': get_param_by_behaviormode(type)[3],
                                'DynamicDelay': get_param_by_behaviormode(type)[4],
                            })
            csv_row = {'description': description, 'scenario_name': scenario_name}
            csv_row.update(content.to_dict())
            write_to_scenario_table(next_id, [csv_row])




# Agent From Oncoming - Turn Left 16~30
if "Agent From Oncoming - Turn Left":
    lateral_behavior = 'TL'
    for agentPos, agentToPos, describe, cetranNo in zip([agentFromLeft, agentFromOppositeDirectionAsideLeft, agentFromRight], 
                                              [agentToSameDirectionAsideLeft, agentToRight, agentToSameRoadOppositeDirectionAsideLeft],
                                              ['Agent from Left, turn Left', 'Agent from Oncoming, turn Left', 'Agent from Right, turn Left'],
                                              [33, 27, 31]):
        agent1['Start'] = agentPos
        agent1['End'] = agentToPos
        
        trigger = ('absolute', 0, 1, 20)
        agent1['Trigger'] = {}
        agent1['Trigger']['type'] = trigger[0]
        agent1['Trigger']['road'] = trigger[1]
        agent1['Trigger']['lane'] = trigger[2]
        agent1['Trigger']['s'] = trigger[3]
        
        if agentPos[0] == 1 or agentPos[0] == 2:
            initRelPostAbbvLat = 'L'
        else:
            initRelPostAbbvLat = 'R'
            
        initRelPostAbbvLon = 'F'
            
        for type, behavior in BehaviorMode.items():
            agent1['Behavior'] = {}
            agent1['Behavior']['type'] = type
            agent1['Behavior']['Start_speed'] = behavior[1]
            agent1['Behavior']['End_speed'] = behavior[2]
            agent1['Behavior']['Dynamic_duration'] = behavior[3]
            agent1['Behavior']['Dynamic_shape'] = behavior[4]
            agent1['Behavior']['Dynamic_delay'] = behavior[5]
            agent1['Behavior']['Use_route'] = False
            
            
            config['Agents'] = [agent1]
            
            description = f'{describe} - {behavior[0]}'
            
            next_id = get_next_scenario_id()
            scenario_name = f'hcis_{next_id}_01{initRelPostAbbvLon}{initRelPostAbbvLat}-{lateral_behavior}'
            config['Scenario_name'] = scenario_name
            yaml.dump(config, open(f'./scenario_config/{scenario_name}.yaml', 'a+'))
            
            #Write scenario description
            content = ScenarioContent('junction', cetranNo)
            content.ego_long_mode = 'drivingForward'
            content.ego_long_mode_type = 'cruising'
            content.ego_lat_mode = 'goingStraight'
            content.agents[0].update({
                                'long_mode': behavior[6],
                                'long_mode_type': behavior[7],
                                'lat_mode': 'turning',
                                'lat_direction': 'left',
                                'init_direction': 'oncoming',
                                'init_dynm': get_tag(behavior[1], 'init_dynm'),
                                'init_lat_pos': get_tag(initRelPostAbbvLat, 'init_lat_pos'),
                                'init_long_pos': get_tag(initRelPostAbbvLon, 'init_long_pos'),
                                'S': get_param_by_behaviormode(type)[0],
                                'Speed': get_param_by_behaviormode(type)[1],
                                'LowSpeed': get_param_by_behaviormode(type)[2],
                                'DynamicDuration': get_param_by_behaviormode(type)[3],
                                'DynamicDelay': get_param_by_behaviormode(type)[4],
                            })
            csv_row = {'description': description, 'scenario_name': scenario_name}
            csv_row.update(content.to_dict())
            write_to_scenario_table(next_id, [csv_row])
            
            
            
            
# Agent From Oncoming - U-turn to Same lane 31~35
if "Agent From Oncoming - U-turn to Same lane":
    lateral_behavior = 'TL'
    describe = 'Agent from Oncoming, U-turn to Same lane'

    agent1['Start'] = agentFromOppositeDirectionAsideLeft
    agent1['End'] = agentToSameDirectionAsideLeft
    
    trigger = ('absolute', 0, 1, 20)
    agent1['Trigger'] = {}
    agent1['Trigger']['type'] = trigger[0]
    agent1['Trigger']['road'] = trigger[1]
    agent1['Trigger']['lane'] = trigger[2]
    agent1['Trigger']['s'] = trigger[3]
    
    initRelPostAbbvLat = 'L'
    initRelPostAbbvLon = 'F'
        
    for type, behavior in BehaviorMode.items():
        agent1['Behavior'] = {}
        agent1['Behavior']['type'] = type
        agent1['Behavior']['Start_speed'] = behavior[1]
        agent1['Behavior']['End_speed'] = behavior[2]
        agent1['Behavior']['Dynamic_duration'] = behavior[3]
        agent1['Behavior']['Dynamic_shape'] = behavior[4]
        agent1['Behavior']['Dynamic_delay'] = behavior[5]
        agent1['Behavior']['Use_route'] = True
        
        config['Agents'] = [agent1]
        
        description = f'{describe} - {behavior[0]}'
        
        next_id = get_next_scenario_id()
        scenario_name = f'hcis_{next_id}_01{initRelPostAbbvLon}{initRelPostAbbvLat}-{lateral_behavior}'
        config['Scenario_name'] = scenario_name
        yaml.dump(config, open(f'./scenario_config/{scenario_name}.yaml', 'a+'))
        
        #Write scenario description
        content = ScenarioContent('junction')
        content.ego_long_mode = 'drivingForward'
        content.ego_long_mode_type = 'cruising'
        content.ego_lat_mode = 'goingStraight'
        content.agents[0].update({
                            'long_mode': behavior[6],
                            'long_mode_type': behavior[7],
                            'lat_mode': 'turning',
                            'lat_direction': 'left',
                            'init_direction': 'oncoming',
                            'init_dynm': get_tag(behavior[1], 'init_dynm'),
                            'init_lat_pos': get_tag(initRelPostAbbvLat, 'init_lat_pos'),
                            'init_long_pos': get_tag(initRelPostAbbvLon, 'init_long_pos'),
                            'S': get_param_by_behaviormode(type)[0],
                            'Speed': get_param_by_behaviormode(type)[1],
                            'LowSpeed': get_param_by_behaviormode(type)[2],
                            'DynamicDuration': get_param_by_behaviormode(type)[3],
                            'DynamicDelay': get_param_by_behaviormode(type)[4],
                        })
        csv_row = {'description': description, 'scenario_name': scenario_name}
        csv_row.update(content.to_dict())
        write_to_scenario_table(next_id, [csv_row])
                
                
         
            
##### Ego Go Straight Aside Right #####
config['Ego'] = egoStraightAsideRight
agent1 = {}
# Agent Position:1,2,4 - Turn Right 36~50
if "Agent Position:1,2,4 - Turn Right":
    lateral_behavior = 'TR'
    for agentPos, trigger, describe, cetranNo in zip([agentFromSameDirectionAsideLeft, agentFromSameDirectionAsideRight, agentFromSameDirectionAsideLeft], 
                                           [('absolute', 0, 2, 20 + 14), ('absolute', 0, 2, 20 + 14), ('absolute', 0, 2, 20)],
                                           ['Agent at 1, turn Right', 'Agent at 2, turn Right', 'Agent at 4, turn Right'],
                                         [None, 65, None]):
        agent1['Start'] = agentPos
        agent1['End'] = agentToRight
        agent1['Trigger'] = {}
        agent1['Trigger']['type'] = trigger[0]
        agent1['Trigger']['road'] = trigger[1]
        agent1['Trigger']['lane'] = trigger[2]
        agent1['Trigger']['s'] = trigger[3]
        
        if trigger[2] == config['Ego']['Start'][2]:
            initRelPostAbbvLat = 'S'
        else:
            initRelPostAbbvLat = 'L'
            
        if trigger[3] == 20:
            initRelPostAbbvLon = 'S'
        else:
            initRelPostAbbvLon = 'F'
            
        for type, behavior in BehaviorMode.items():
            agent1['Behavior'] = {}
            agent1['Behavior']['type'] = type
            agent1['Behavior']['Start_speed'] = behavior[1]
            agent1['Behavior']['End_speed'] = behavior[2]
            agent1['Behavior']['Dynamic_duration'] = behavior[3]
            agent1['Behavior']['Dynamic_shape'] = behavior[4]
            agent1['Behavior']['Dynamic_delay'] = behavior[5]
            
            if agentPos[2] == '1':
                agent1['Behavior']['Use_route'] = True
            else:
                agent1['Behavior']['Use_route'] = False
            
            config['Agents'] = [agent1]
            
            description = f'{describe} - {behavior[0]}'
            
            next_id = get_next_scenario_id()
            scenario_name = f'hcis_{next_id}_01{initRelPostAbbvLon}{initRelPostAbbvLat}-{lateral_behavior}'
            config['Scenario_name'] = scenario_name
            yaml.dump(config, open(f'./scenario_config/{scenario_name}.yaml', 'a+'))
            
            #Write scenario description
            content = ScenarioContent('junction', cetranNo)
            content.ego_long_mode = 'drivingForward'
            content.ego_long_mode_type = 'cruising'
            content.ego_lat_mode = 'goingStraight'
            content.agents[0].update({
                                'long_mode': behavior[6],
                                'long_mode_type': behavior[7],
                                'lat_mode': 'turning',
                                'lat_direction': 'right',
                                'init_direction': 'sameAsEgo',
                                'init_dynm': get_tag(behavior[1], 'init_dynm'),
                                'init_lat_pos': get_tag(initRelPostAbbvLat, 'init_lat_pos'),
                                'init_long_pos': get_tag(initRelPostAbbvLon, 'init_long_pos'),
                                'S': get_param_by_behaviormode(type)[0],
                                'Speed': get_param_by_behaviormode(type)[1],
                                'LowSpeed': get_param_by_behaviormode(type)[2],
                                'DynamicDuration': get_param_by_behaviormode(type)[3],
                                'DynamicDelay': get_param_by_behaviormode(type)[4],
                            })
            csv_row = {'description': description, 'scenario_name': scenario_name}
            csv_row.update(content.to_dict())
            write_to_scenario_table(next_id, [csv_row])

# Agent From Oncoming - Turn Right 51~55
if "Agent From Oncoming - Turn Right":
    lateral_behavior = 'TR'
    describe = 'Agent from Oncoming, turn Right'

    agent1['Start'] = agentFromRight
    agent1['End'] = agentToSameDirectionAsideRight
    
    trigger = ('absolute', 0, 2, 20)
    agent1['Trigger'] = {}
    agent1['Trigger']['type'] = trigger[0]
    agent1['Trigger']['road'] = trigger[1]
    agent1['Trigger']['lane'] = trigger[2]
    agent1['Trigger']['s'] = trigger[3]
    
    if agentPos[2] == '1' or agentPos[2] == '2':
        initRelPostAbbvLat = 'L'
    else:
        initRelPostAbbvLat = 'R'
        
    initRelPostAbbvLon = 'F'
        
    for type, behavior in BehaviorMode.items():
        agent1['Behavior'] = {}
        agent1['Behavior']['type'] = type
        agent1['Behavior']['Start_speed'] = behavior[1]
        agent1['Behavior']['End_speed'] = behavior[2]
        agent1['Behavior']['Dynamic_duration'] = behavior[3]
        agent1['Behavior']['Dynamic_shape'] = behavior[4]
        agent1['Behavior']['Dynamic_delay'] = behavior[5]
        agent1['Behavior']['Use_route'] = False
        
        
        config['Agents'] = [agent1]
        
        description = f'{describe} - {behavior[0]}'
        
        next_id = get_next_scenario_id()
        scenario_name = f'hcis_{next_id}_01{initRelPostAbbvLon}{initRelPostAbbvLat}-{lateral_behavior}'
        config['Scenario_name'] = scenario_name
        yaml.dump(config, open(f'./scenario_config/{scenario_name}.yaml', 'a+'))
        
        #Write scenario description
        content = ScenarioContent('junction', 31)
        content.ego_long_mode = 'drivingForward'
        content.ego_long_mode_type = 'cruising'
        content.ego_lat_mode = 'goingStraight'
        content.agents[0].update({
                            'long_mode': behavior[6],
                            'long_mode_type': behavior[7],
                            'lat_mode': 'turning',
                            'lat_direction': 'right',
                            'init_direction': 'oncoming',
                            'init_dynm': get_tag(behavior[1], 'init_dynm'),
                            'init_lat_pos': get_tag(initRelPostAbbvLat, 'init_lat_pos'),
                            'init_long_pos': get_tag(initRelPostAbbvLon, 'init_long_pos'),
                            'S': get_param_by_behaviormode(type)[0],
                            'Speed': get_param_by_behaviormode(type)[1],
                            'LowSpeed': get_param_by_behaviormode(type)[2],
                            'DynamicDuration': get_param_by_behaviormode(type)[3],
                            'DynamicDelay': get_param_by_behaviormode(type)[4],
                        })
        csv_row = {'description': description, 'scenario_name': scenario_name}
        csv_row.update(content.to_dict())
        write_to_scenario_table(next_id, [csv_row])
        
# Agent From Oncoming - U-turn 56~60
if "Agent From Oncoming - U-turn":
    lateral_behavior = 'TL'
    describe = 'Agent from Oncoming, U-turn'

    agent1['Start'] = agentFromOppositeDirectionAsideLeft
    agent1['End'] = agentToSameDirectionAsideLeft
    
    trigger = ('absolute', 0, 2, 20)
    agent1['Trigger'] = {}
    agent1['Trigger']['type'] = trigger[0]
    agent1['Trigger']['road'] = trigger[1]
    agent1['Trigger']['lane'] = trigger[2]
    agent1['Trigger']['s'] = trigger[3]
    
    initRelPostAbbvLat = 'L'
    initRelPostAbbvLon = 'F'
        
    for type, behavior in BehaviorMode.items():
        agent1['Behavior'] = {}
        agent1['Behavior']['type'] = type
        agent1['Behavior']['Start_speed'] = behavior[1]
        agent1['Behavior']['End_speed'] = behavior[2]
        agent1['Behavior']['Dynamic_duration'] = behavior[3]
        agent1['Behavior']['Dynamic_shape'] = behavior[4]
        agent1['Behavior']['Dynamic_delay'] = behavior[5]
        agent1['Behavior']['Use_route'] = True
        
        
        config['Agents'] = [agent1]
        
        description = f'{describe} - {behavior[0]}'
        
        next_id = get_next_scenario_id()
        scenario_name = f'hcis_{next_id}_01{initRelPostAbbvLon}{initRelPostAbbvLat}-{lateral_behavior}'
        config['Scenario_name'] = scenario_name
        yaml.dump(config, open(f'./scenario_config/{scenario_name}.yaml', 'a+'))
        
        #Write scenario description
        content = ScenarioContent('junction', cetranNo)
        content.ego_long_mode = 'drivingForward'
        content.ego_long_mode_type = 'cruising'
        content.ego_lat_mode = 'goingStraight'
        content.agents[0].update({
                            'long_mode': behavior[6],
                            'long_mode_type': behavior[7],
                            'lat_mode': 'turning',
                            'lat_direction': 'left',
                            'init_direction': 'oncoming',
                            'init_dynm': get_tag(behavior[1], 'init_dynm'),
                            'init_lat_pos': get_tag(initRelPostAbbvLat, 'init_lat_pos'),
                            'init_long_pos': get_tag(initRelPostAbbvLon, 'init_long_pos'),
                            'S': get_param_by_behaviormode(type)[0],
                            'Speed': get_param_by_behaviormode(type)[1],
                            'LowSpeed': get_param_by_behaviormode(type)[2],
                            'DynamicDuration': get_param_by_behaviormode(type)[3],
                            'DynamicDelay': get_param_by_behaviormode(type)[4],
                        })
        csv_row = {'description': description, 'scenario_name': scenario_name}
        csv_row.update(content.to_dict())
        write_to_scenario_table(next_id, [csv_row])
        
        
        
        
# egoStraightAsideLeft = {'Start': '0 1 40', 'End': '2 -1 40'}
config['Ego'] = egoStraightAsideLeft
config['Map'] = [98, 119, 141, 106]
config['Center'] =  '257 30.5'
agentFromLeft = '1 -1 10'
agentToLeft = '1 1 20'

# Agent From Oncoming - Keeping 61~70
if "Agent From Oncoming - Keeping":

    lateral_behavior = 'KEEP'
    for agentPos, agentToPos, describe, cetranNo in zip([agentFromLeft, agentFromRight], 
                                              [agentToRight, agentToLeft],
                                              ['Agent from Left, Keeping', 'Agent from Right, Keeping'],
                                              [32, 31]):
        agent1['Start'] = agentPos
        agent1['End'] = agentToPos
        
        trigger = ('absolute', 0, 1, 20)
        agent1['Trigger'] = {}
        agent1['Trigger']['type'] = trigger[0]
        agent1['Trigger']['road'] = trigger[1]
        agent1['Trigger']['lane'] = trigger[2]
        agent1['Trigger']['s'] = trigger[3]
        
        if agentPos[0] == '1' or agentPos[0] == '2':
            initRelPostAbbvLat = 'L'
        else:
            initRelPostAbbvLat = 'R'
            
        
        initRelPostAbbvLon = 'F'
            
        for type, behavior in BehaviorMode.items():
            agent1['Behavior'] = {}
            agent1['Behavior']['type'] = type
            agent1['Behavior']['Start_speed'] = behavior[1]
            agent1['Behavior']['End_speed'] = behavior[2]
            agent1['Behavior']['Dynamic_duration'] = behavior[3]
            agent1['Behavior']['Dynamic_shape'] = behavior[4]
            agent1['Behavior']['Dynamic_delay'] = behavior[5]
            agent1['Behavior']['Use_route'] = False
            
            
            config['Agents'] = [agent1]
            
            description = f'{describe} - {behavior[0]}'
            
            next_id = get_next_scenario_id()
            scenario_name = f'hcis_{next_id}_01{initRelPostAbbvLon}{initRelPostAbbvLat}-{lateral_behavior}'
            config['Scenario_name'] = scenario_name
            yaml.dump(config, open(f'./scenario_config/{scenario_name}.yaml', 'a+'))


            
            #Write scenario description
            content = ScenarioContent('junction', cetranNo)
            content.ego_long_mode = 'drivingForward'
            content.ego_long_mode_type = 'cruising'
            content.ego_lat_mode = 'goingStraight'
            content.agents[0].update({
                                'long_mode': behavior[6],
                                'long_mode_type': behavior[7],
                                'lat_mode': 'goingStraight',
                                # 'lat_direction': 'left',
                                'init_direction': 'oncoming',
                                'init_dynm': get_tag(behavior[1], 'init_dynm'),
                                'init_lat_pos': get_tag(initRelPostAbbvLat, 'init_lat_pos'),
                                'init_long_pos': get_tag(initRelPostAbbvLon, 'init_long_pos'),
                                'S': get_param_by_behaviormode(type)[0],
                                'Speed': get_param_by_behaviormode(type)[1],
                                'LowSpeed': get_param_by_behaviormode(type)[2],
                                'DynamicDuration': get_param_by_behaviormode(type)[3],
                                'DynamicDelay': get_param_by_behaviormode(type)[4],
                            })
            csv_row = {'description': description, 'scenario_name': scenario_name}
            csv_row.update(content.to_dict())
            write_to_scenario_table(next_id, [csv_row])
        
    
   
