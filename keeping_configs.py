from dicent_utils import *
import yaml




lateral_behavior = None
initRelPostAbbvLat = None
initRelPostAbbvLon = None
description = None
scenario_name = None



config = {}
config['Map'] = [139, 166]
# config['Center'] = '685.61 -134.05'

# Position information
# egoStraightAsideLeft = {'Start_pos': [0, -2, 20, 0], 'End_pos': [1, 2, 20, 0]}
egoStraightAsideLeft = {}
egoStraightAsideLeft['Start_pos'] = [0, -1, 7, 0, 1]
egoStraightAsideLeft['End_pos'] = [1, 1, 10, 0,1]
egoStartSpeed = 50

# default relaive trigger
Pos2 = {'Start_pos': [0, -1, 20, 0, 1],'End_pos':[1, 1, 20, 0, 1], 'Start_trigger': {'lane':0, 'road': -1 ,'s':10, 'offset': 0,'type':'relative'}}
Pos3 = {'Start_pos': [0, -2, 20, 0, 1],'End_pos':[1, 2, 20, 0, 1], 'Start_trigger': {'lane':-1, 'road': -1 ,'s':10, 'offset': 0,'type':'relative'}}
Pos5 = {'Start_pos': [0, -2, 7, 0, 1],'End_pos': [1, 2, 7, 0, 1], 'Start_trigger': {'lane':-1 , 'road':0 ,'s':0, 'offset': 0,'type':'relative'}}



# Defualt values
BehaviorMode = get_behavior_mode()


config['Ego'] = egoStraightAsideLeft
config['Ego']['Start_speed'] = egoStartSpeed


# car1, agent at 2, Keeping
describe = 'Agent at 2, keeping'
initRelPostAbbvLat = 'KEEP'
initRelPostAbbvLat = 'S'
initRelPostAbbvLon = 'F'

car = {}
car['Type'] = 'car_red'
car['Start_pos'] = Pos2['Start_pos']
car['Start_trigger'] = Pos2['Start_trigger']

# straight_end = np.array(Pos2['Start_pos']) + np.array([1,0,0,0, 0])
straight_end = Pos2['End_pos']
# print(straight_end);exit()
gostraightAct = [{'Type':'position', 'End':straight_end,'Dynamic_delay':0,'Dynamic_duration':0,'Dynamic_shape':'Straight','Use_route':'null'}, 
                 {'Type':'speed','Use_route':'null'}]



            
for type, behavior in BehaviorMode.items():
    # agent1['Behavior'] = {}
    # agent1['Behavior']['  type'] = type
    car['Start_speed'] = behavior[1]
    gostraightAct[1]['End'] = behavior[2]
    gostraightAct[1]['Dynamic_duration'] = behavior[3]
    gostraightAct[1]['Dynamic_shape'] = behavior[4]
    gostraightAct[1]['Dynamic_delay'] = behavior[5]
    car['Acts'] = [{'Type': 'gostraight','Delay':0, 'Events':gostraightAct}]
    
    config['Actors'] = {'Agents':[car]}
    
    
    description = f'{describe} - {behavior[0]}'
    next_id = get_next_scenario_id()
    scenario_name = f'hcis_{next_id}_01{initRelPostAbbvLon}{initRelPostAbbvLat}-{lateral_behavior}'
    config['Scenario_name'] = scenario_name
    
    import pprint
    pprint.pprint(config)
    
    config = sort_config_dict(config)
    
    yaml.dump(config, open(f'./scenario_config/keeping/{scenario_name}.yaml', 'a+'), sort_keys=False)
    
    break
            # , default_flow_style=None
    #Write scenario description
    # write_to_scenario_table(next_id, [{'description': description, 'scenario_name': scenario_name}])
    
    
    
    # agent1['Behavior']['End_speed'] = behavior[2]
    # agent1['Behavior']['Dynamic_duration'] = behavior[3]
    # agent1['Behavior']['Dynamic_shape'] = behavior[4]
    # agent1['Behavior']['Dynamic_delay'] = behavior[5]
"""
Type: position
Dynamic_delay: 1 
Dynamic_duration: X # irrelavant
Dynamic_shape: X # irrelevant
End: [0,-1,40,0] # Target position [road index, lane id, s]
Use_route: null # or RoadCenter([x,y]): absolute world position (for NURBS)
"""