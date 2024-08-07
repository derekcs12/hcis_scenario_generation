
from dicent_utils import *
import yaml

if 'init':
    config = {}
    config['Map'] = [121, 17, 144, 16]
    config['Center'] = '685.61 -134.05'
    
    egoStraightAsideLeft = {'Start': '0 1 40', 'End': '2 -1 40'}
    egoStraightAsideRight = {'Start': '0 2 40', 'End': '2 -2 40'}
    
    agentFromSameDirectionAsideLeft = '0 1 20'
    agentFromSameDirectionAsideRight = '0 2 20'
    agentFromOppositeDirectionAsideLeft = '2 -1 20'
    # agentFromOppositeDirectionAsideRight = '2 -2 20'
    agentToSameDirectionAsideLeft = '2 1 20'
    agentToSameDirectionAsideRight = '2 2 20'
    agentToSameRoadOppositeDirectionAsideLeft = '0 -1 20'
    # agentToOppositeDirectionAsideRight = '2 -2 20'
    agentFromLeft = '1 1 20'
    agentFromRight = '3 1 20'
    agentToLeft = '1 -1 20'
    agentToRight = '3 -1 20'
    
    # BehaviorMode
    AgentSpeed = '${$Agent0Speed / 3.6}'
    AgentLowSpeed = '${$Agent0LowSpeed / 3.6}'
    DynamicDuration = '$Agent0DynamicDuration' #3.0
    DynamicHaltDuration = '${$Agent1DynamicDuration / 3}' #1
    AgentDelay = '$Agent0Delay' # 0.45
    
    # BehaviorMode
    AgentSpeed = '40'
    AgentLowSpeed = '10'
    DynamicDuration = '3' #3.0
    DynamicHaltDuration = '1.5' #1
    DynamicDelay = '2' #1
    # AgentDelay = '0.5' # 0.45
    
    
    BehaviorMode = {}
    BehaviorMode['keeping']  = (AgentSpeed, AgentSpeed, DynamicDuration, 'linear', DynamicDelay) #等速
    BehaviorMode['braking'] = (AgentSpeed, AgentLowSpeed, DynamicDuration, 'linear', DynamicDelay)  #減速
    BehaviorMode['braking_halt'] = (AgentSpeed, 0, DynamicHaltDuration, 'linear', DynamicDelay) #減速|未完成
    BehaviorMode['sudden_braking_halt'] = (AgentSpeed, 0, DynamicHaltDuration, 'sinusoidal', DynamicDelay)  #急煞|未完成
    BehaviorMode['speed_up'] = ( 0, AgentSpeed, DynamicDuration, 'linear', DynamicDelay) #加速



###### Ego Go Straight Aside Left #####
config['Ego'] = egoStraightAsideLeft
agent1 = {}


# Agent Position:2,3,5 - Turn Left
if "Agent Position:2,3,5 - Turn Left":
    lateral_behavior = 'TL'
    for agentPos, trigger in zip([agentFromSameDirectionAsideLeft, agentFromSameDirectionAsideRight, agentFromSameDirectionAsideRight], 
                                    [('absolute', 0, 1, 20 + 10), ('absolute', 0, 1, 20 + 10), ('absolute', 0, 1, 20)]):
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
            agent1['Behavior']['Start_speed'] = behavior[0]
            agent1['Behavior']['End_speed'] = behavior[1]
            agent1['Behavior']['Dynamic_duration'] = behavior[2]
            agent1['Behavior']['Dynamic_shape'] = behavior[3]
            agent1['Behavior']['Dynamic_delay'] = behavior[4]
            
            if agentPos[2] == '2':
                agent1['Behavior']['Use_route'] = True
            else:
                agent1['Behavior']['Use_route'] = False
            
            
            config['Agents'] = [agent1]
            
            next_id = get_next_scenario_id()
            scenario_name = f'hcis_{next_id}_01{initRelPostAbbvLon}{initRelPostAbbvLat}-{lateral_behavior}'
            config['Scenario_name'] = scenario_name
            yaml.dump(config, open(f'./scenario_config/{scenario_name}.yaml', 'a+'))

# Agent From Oncoming - Turn Left
if "Agent From Oncoming - Turn Left":
    lateral_behavior = 'TL'
    for agentPos, agentToPos in zip([agentFromLeft, agentFromOppositeDirectionAsideLeft, agentFromRight], 
                                    [agentToSameDirectionAsideLeft, agentToRight, agentToSameRoadOppositeDirectionAsideLeft]):
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
            agent1['Behavior']['Start_speed'] = behavior[0]
            agent1['Behavior']['End_speed'] = behavior[1]
            agent1['Behavior']['Dynamic_duration'] = behavior[2]
            agent1['Behavior']['Dynamic_shape'] = behavior[3]
            agent1['Behavior']['Dynamic_delay'] = behavior[4]
            agent1['Behavior']['Use_route'] = False
            
            
            config['Agents'] = [agent1]
            
            next_id = get_next_scenario_id()
            scenario_name = f'hcis_{next_id}_01{initRelPostAbbvLon}{initRelPostAbbvLat}-{lateral_behavior}'
            config['Scenario_name'] = scenario_name
            yaml.dump(config, open(f'./scenario_config/{scenario_name}.yaml', 'a+'))
            
# Agent From Oncoming - U-turn to Same lane
if "Agent From Oncoming - U-turn to Same lane":
    lateral_behavior = 'TL'

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
        agent1['Behavior']['Start_speed'] = behavior[0]
        agent1['Behavior']['End_speed'] = behavior[1]
        agent1['Behavior']['Dynamic_duration'] = behavior[2]
        agent1['Behavior']['Dynamic_shape'] = behavior[3]
        agent1['Behavior']['Dynamic_delay'] = behavior[4]
        agent1['Behavior']['Use_route'] = True
        
        config['Agents'] = [agent1]
        
        next_id = get_next_scenario_id()
        scenario_name = f'hcis_{next_id}_01{initRelPostAbbvLon}{initRelPostAbbvLat}-{lateral_behavior}'
        config['Scenario_name'] = scenario_name
        yaml.dump(config, open(f'./scenario_config/{scenario_name}.yaml', 'a+'))
                
                
         
            
##### Ego Go Straight Aside Right #####
config['Ego'] = egoStraightAsideRight
agent1 = {}
# Agent Position:1,2,4 - Turn Right
if "Agent Position:1,2,4 - Turn Right":
    lateral_behavior = 'TR'
    for agentPos, trigger in zip([agentFromSameDirectionAsideLeft, agentFromSameDirectionAsideRight, agentFromSameDirectionAsideLeft], 
                                    [('absolute', 0, 2, 20 + 10), ('absolute', 0, 2, 20 + 10), ('absolute', 0, 2, 20)]):
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
            agent1['Behavior']['Start_speed'] = behavior[0]
            agent1['Behavior']['End_speed'] = behavior[1]
            agent1['Behavior']['Dynamic_duration'] = behavior[2]
            agent1['Behavior']['Dynamic_shape'] = behavior[3]
            agent1['Behavior']['Dynamic_delay'] = behavior[4]
            
            if agentPos[2] == '1':
                agent1['Behavior']['Use_route'] = True
            else:
                agent1['Behavior']['Use_route'] = False
            
            config['Agents'] = [agent1]
            
            next_id = get_next_scenario_id()
            scenario_name = f'hcis_{next_id}_01{initRelPostAbbvLon}{initRelPostAbbvLat}-{lateral_behavior}'
            config['Scenario_name'] = scenario_name
            yaml.dump(config, open(f'./scenario_config/{scenario_name}.yaml', 'a+'))

# Agent From Oncoming - Turn Right
if "Agent From Oncoming - Turn Right":
    lateral_behavior = 'TR'

    agent1['Start'] = agentFromRight
    agent1['End'] = agentToSameDirectionAsideLeft
    
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
        agent1['Behavior']['Start_speed'] = behavior[0]
        agent1['Behavior']['End_speed'] = behavior[1]
        agent1['Behavior']['Dynamic_duration'] = behavior[2]
        agent1['Behavior']['Dynamic_shape'] = behavior[3]
        agent1['Behavior']['Dynamic_delay'] = behavior[4]
        agent1['Behavior']['Use_route'] = False
        
        
        config['Agents'] = [agent1]
        
        next_id = get_next_scenario_id()
        scenario_name = f'hcis_{next_id}_01{initRelPostAbbvLon}{initRelPostAbbvLat}-{lateral_behavior}'
        config['Scenario_name'] = scenario_name
        yaml.dump(config, open(f'./scenario_config/{scenario_name}.yaml', 'a+'))
        
# Agent From Oncoming - U-turn
if "Agent From Oncoming - U-turn":
    lateral_behavior = 'TL'

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
        agent1['Behavior']['Start_speed'] = behavior[0]
        agent1['Behavior']['End_speed'] = behavior[1]
        agent1['Behavior']['Dynamic_duration'] = behavior[2]
        agent1['Behavior']['Dynamic_shape'] = behavior[3]
        agent1['Behavior']['Dynamic_delay'] = behavior[4]
        agent1['Behavior']['Use_route'] = True
        
        
        config['Agents'] = [agent1]
        
        next_id = get_next_scenario_id()
        scenario_name = f'hcis_{next_id}_01{initRelPostAbbvLon}{initRelPostAbbvLat}-{lateral_behavior}'
        config['Scenario_name'] = scenario_name
        yaml.dump(config, open(f'./scenario_config/{scenario_name}.yaml', 'a+'))
        
        
        
        
# egoStraightAsideLeft = {'Start': '0 1 40', 'End': '2 -1 40'}
config['Ego'] = egoStraightAsideLeft
config['Map'] = [98, 119, 141, 106]
config['Center'] =  '257 30.5'
agentFromLeft = '1 1 10'
agentFromRight = '3 1 10'

# Agent From Oncoming - Keeping
if "Agent From Oncoming - Keeping":

    lateral_behavior = 'KEEP'
    for agentPos, agentToPos in zip([agentFromLeft, agentFromRight], 
                                    [agentToRight, agentToLeft]):
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
            agent1['Behavior']['Start_speed'] = behavior[0]
            agent1['Behavior']['End_speed'] = behavior[1]
            agent1['Behavior']['Dynamic_duration'] = behavior[2]
            agent1['Behavior']['Dynamic_shape'] = behavior[3]
            agent1['Behavior']['Dynamic_delay'] = behavior[4]
            agent1['Behavior']['Use_route'] = False
            
            
            config['Agents'] = [agent1]
            
            next_id = get_next_scenario_id()
            scenario_name = f'hcis_{next_id}_01{initRelPostAbbvLon}{initRelPostAbbvLat}-{lateral_behavior}'
            config['Scenario_name'] = scenario_name
            yaml.dump(config, open(f'./scenario_config/{scenario_name}.yaml', 'a+'))
    
   