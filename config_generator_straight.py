
from dicent_utils import *
import yaml

    config = {}
    config['Map'] = [21]
    config['Center'] = '457 164'
    
    egoStraightAsideLeft = {'Start': '0 1 0', 'End': '0 1 60'}
    
    # egoStraightAsideRight = {'Start': '0 2 40', 'End': '2 -2 40'}
    
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
    DynamicHaltDuration = '1' #1
    AgentDelay = '0.5' # 0.45
    
    
    BehaviorMode = {}
    BehaviorMode['keeping']  = (AgentSpeed, AgentSpeed, DynamicDuration, 'linear', None) #等速
    BehaviorMode['braking'] = (AgentSpeed, AgentLowSpeed, DynamicDuration, 'linear', None)  #減速
    BehaviorMode['braking_halt'] = (AgentSpeed, 0, DynamicHaltDuration, 'linear', None) #減速|未完成
    BehaviorMode['sudden_braking_halt'] = (AgentSpeed, 0, DynamicHaltDuration, 'sinusoidal', AgentDelay)  #急煞|未完成
    BehaviorMode['speed_up'] = ( 0, AgentSpeed, DynamicDuration, 'linear', None) #加速
    
    ##### Ego Go Straight Aside Right #####
    config['Ego'] = egoStraightAsideRight
    agent1 = {}
    
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
            
            
            config['Agents'] = [agent1]
            
            next_id = get_next_scenario_id()
            scenario_name = f'hcis_{next_id}_01{initRelPostAbbvLon}{initRelPostAbbvLat}-{lateral_behavior}'
            config['Scenario_name'] = scenario_name
            yaml.dump(config, open(f'./scenario_config/{scenario_name}.yaml', 'a+'))
            
            