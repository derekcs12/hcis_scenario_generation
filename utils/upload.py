import os
import csv
import glob
import pandas as pd
from typing import List
import re
import yaml

import xml.etree.ElementTree as ET
from scenariogeneration import xosc, prettyprint

class ScenarioContent:
    def __init__(self, road_layout, road_layout_mode='noTrafficLight', cetran_number=None, agent_number=1):
        self.road_layout = road_layout
        self.road_layout_mode = road_layout_mode
        self.cetran_number = cetran_number
        self.route = None
        self.ego_long_mode = None,
        self.ego_long_mode_type = None,
        self.ego_lat_mode = None
        self.ego_lat_direction = None
        
        agent = {
            'type': 'M1',
            'long_mode': None,
            'long_mode_type': None,
            'lat_mode': None,
            'lat_direction': None,
            'init_direction': None,
            'init_dynm': None,
            'init_lat_pos': None,
            'init_long_pos': None,
            'S': '0~20',
            'Speed': '0~20',
            '1_SA_EndSpeed': None,
            '1_SA_DynamicDuration': None,
            '1_SA_DynamicDelay': None,
            # 'agent1_1_1_DynamicShape': None,
        }
        
        self.agents = []
        for _ in range(agent_number):
            self.agents.append(agent)
    
    def to_dict(self):
        re = {
            'road_layout': self.road_layout,
            'road_layout_mode': self.road_layout_mode,
            'cetran_number': self.cetran_number,
            'ego_long_mode': self.ego_long_mode,
            'ego_long_mode_type': self.ego_long_mode_type,
            'ego_lat_mode': self.ego_lat_mode,
            'ego_lat_direction': self.ego_lat_direction,
        }
        
        for i, agent in enumerate(self.agents):
            for key, value in agent.items():
                re[f'Agent{i+1}_{key}'] = value
                
        return re
    

# Upload tag tree basic structure
class ScenarioTagTree:
    def __init__(self):
        self.tagTree = {
            "ego": {
                "vehicleLongitudinalActivity": {
                    "mode": None,
                    # "drivingForwardMode": None
                },
                "vehicleLateralActivity": {
                    "mode": None
                }
            },
            "actors": [],
            "roadLayout": {
                "mode": None,
                # "junctionMode": None
            }
        }
    
    def _set_longitudinal_activity(self, mode, driving_forward_mode):
        long_act = {}
        long_act['mode'] = mode
        if mode == 'drivingForward':
            long_act['drivingForwardMode'] = driving_forward_mode
        return long_act
    
    def _set_lateral_activity(self, mode, direction):
        lat_act = {}
        lat_act['mode'] = mode
        if mode != 'goingStraight':
            lat_act['direction'] = direction
        return lat_act

    def set_ego_vehicle_activity(self, row):
        self.tagTree["ego"]['vehicleLongitudinalActivity'] = self._set_longitudinal_activity(row['ego_long_mode'], row['ego_long_mode_type'])
        self.tagTree["ego"]['vehicleLateralActivity'] = self._set_lateral_activity(row['ego_lat_mode'], row['ego_lat_direction'])

    def add_actor(self, row):
        actor_num = 1
        for i in range(1, actor_num+1):
            actor = {
                "initialState": {
                    "direction": row[f'Agent{i}_init_direction'],
                    "dynamics": row[f'Agent{i}_init_dynm'],
                    "lateralPosition": row[f'Agent{i}_init_lat_pos'],
                    "longitudinalPosition": row[f'Agent{i}_init_long_pos']
                },
                "leadVehicle": {
                    "mode": 'appearing',
                    "appearingMode": 'gapClosing'
                },
            }
            actor['vehicleLongitudinalActivity'] = self._set_longitudinal_activity(row[f'Agent{i}_long_mode'], row[f'Agent{i}_long_mode_type'])
            actor['vehicleLateralActivity'] = self._set_lateral_activity(row[f'Agent{i}_lat_mode'], row[f'Agent{i}_lat_direction'])
            self.tagTree["actors"].append(actor)

    def set_road_layout(self, row):
        self.tagTree["roadLayout"]["mode"] = row['road_layout']
        self.tagTree["roadLayout"][f"{row['road_layout']}Mode"] = row['road_layout_mode']



def add_itri_tags(csv):
    tags = []
    if csv['cetran_number'] != None:
        for n in csv['cetran_number'].split(','):
            tags.append(f"src:cetran:{n}")
    if csv['ego_lat_mode'] == 'goingStraight':
        tags.append('ego-behavior:go-straight')

    if 'CO' in csv['scenario_name']:
        tags.append('behavior:cut-out')
    if 'CI' in csv['scenario_name']:
        tags.append('behavior:cut-in')
    if 'TL' in csv['scenario_name']:
        tags.append('behavior:turn-left')
    if 'TR' in csv['scenario_name']:
        tags.append('behavior:turn-right')
    if 'KEEP' in csv['scenario_name']:
        tags.append('behavior:keeping')
    if 'SWR' in csv['scenario_name']:
        tags.append('behavior:swerving')
    if 'ZZ' in csv['scenario_name']:
        tags.append('behavior:zigzag')
    if 'OT' in csv['scenario_name']:
        tags.append('behavior:overtake')
    if 'SP' in csv['scenario_name']:
        tags.append('behavior:sidepass')

    if csv['Agent1_type'] == 'M1':
        tags.append('vehicle:car')
    if csv['Agent1_type'] == 'Cyclist':
        tags.append('vehicle:scooter')

    return tags

def write_param(csv):
    parameters = []
    columns = csv.keys()
    for col in columns:
        param_info = {}

        if '_EndSpeed' in col:
            param_info["unit"] = "m/s"
        elif '_Speed' in col:
            param_info["unit"] = "m/s"
        elif '_S' in col:
            param_info["unit"] = "m"
        elif '_DynamicDuration' in col:
            param_info["unit"] = "s"
        # elif '_DynamicDelay' in col:
        #     param_info["unit"] = "s"
        # elif '_Delay' in col:
        #     param_info["unit"] = "s"
        # elif '_Offset' in col:
        #     param_info["unit"] = "m"
        elif '_Period' in col:
            param_info["unit"] = "1/s"
        # elif '_Times' in col:
        #     param_info["unit"] = "times"
        else:
            continue

        param_info["name"] = col
        param_info["min"] = csv[col].split('~')[0]
        param_info["max"] = csv[col].split('~')[1]

        if float(param_info["min"]) >= float(param_info["max"]):
            continue # Skip parameters with the same min and max values(07/28, itir)
        
        parameters.append(param_info)
        
    return parameters

    
def create_request_body(
            scenarioId: str,
            tags: List[str],
            description: str,
            parameters: List[dict],
            openDrive: str,
            openScenario: str,
            usedRoute: str,
            tagTree: dict,
            testObjectives: dict,
            conditions: dict,
            observationRecordingAgents: List[dict],
            egoTargetSpeed: float
        ):
    return {
        "scenarioId": scenarioId,
        "tags": tags,
        "description": description,
        "parameters": parameters,
        "openDrive": openDrive,
        "openScenarioField": openScenario,
        "usedRoute": usedRoute,
        "tagTree": tagTree,
        "testObjectives": testObjectives,
        "conditions": conditions,
        "observationRecordingAgents": observationRecordingAgents,
        "egoTargetSpeed": egoTargetSpeed
    }




# --- clone_behavior_mode_and_wriite_content() ---

def write_to_scenario_table(scenario_id, content, file_path='./HCIS_scenarios.csv'):
    """
    Writes the given content to a CSV file with the specified scenario_id.

    :param scenario_id: The scenario ID to be included in the CSV file.
    :param content: List of dictionaries or list of lists to write to the CSV file.
    :param file_path: Path to the CSV file. Default is 'scenario_table.csv'.
    
    # Example input
    content_dicts = [
        {'Name': 'Alice', 'Age': 30, 'City': 'New York'},
        {'Name': 'Bob', 'Age': 25, 'City': 'Los Angeles'},
        {'Name': 'Charlie', 'Age': 35, 'City': 'Chicago'}
    ]
    """
    print(f"write {scenario_id}, description: {content[0]['description']}.")

    columns = ['scenario_id','scenario_name','description','road_layout','road_layout_mode', 'route_name' ,'cetran_number', 
               'ego_long_mode','ego_long_mode_type', 'ego_lat_mode', 'ego_lat_direction',
               'Agent1_type', 'Agent1_long_mode', 'Agent1_long_mode_type', 'Agent1_lat_mode', 'Agent1_lat_direction',
               'Agent1_init_direction', 'Agent1_init_dynm', 'Agent1_init_lat_pos', 'Agent1_init_long_pos',
               'Agent1_S','Agent1_Speed','Agent1_1_SA_EndSpeed','Agent1_1_SA_DynamicDuration','Agent1_1_SA_DynamicDelay', # BehaviorMode Parameters
               'Agent1_Offset', 'Agent1_TA_Offset',
              ]   
    
    for col in content[0].keys():
        if col not in columns:
            columns.append(col)
            
    # Check if the file exists
    if not os.path.exists(file_path):
        ensure_folder_exists(file_path)
            
        df = pd.DataFrame(columns=columns)
        df.to_csv(file_path, index=False)

            
    # Check if content is a list of dictionaries
    if isinstance(content, list) and all(isinstance(row, dict) for row in content):
        # Add scenario_id to each dictionary
        for row in content:
            row['scenario_id'] = scenario_id
        
        
        with open(file_path, mode='a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writerows(content)
    else:
        # Add scenario_id to each list
        content_with_id = [[scenario_id] + row for row in content]
        
        with open(file_path, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(content_with_id)


def _get_next_id_in_folder(folder_name, directory='./scenario_config'):
    file_path = f'{directory}/{folder_name}/'
    ensure_folder_exists(file_path)
    # Regular expression to match filenames with format {party}_{scenario_id}
    pattern = re.compile(r'^(\d+)\.csv$')
    
    max_scenario_id = 0
    
    # List all files in the directory
    for filename in os.listdir(file_path):
        match = pattern.match(filename)
        if match:
            scenario_id = int(match.group(1))
            if scenario_id > max_scenario_id:
                max_scenario_id = scenario_id
    
    # Calculate the next scenario ID
    next_scenario_id = max_scenario_id + 1
    
    return next_scenario_id

def _get_param_by_behaviormode(behavior_type):
    """ 
    if behavior_type == 'keeping':
        # agent1_S, agent1Speed, agent1EndSpeed, agent1DynamicDuration, agent1DynamicDelay, ｜ agent1EventStartDelay, TA_DynamicDuration, TA_DynamicDelay
        return ['0~20','40~60','40~60','5~5','0~3', '0~2', '5~5', '0~1']
    elif behavior_type == 'braking':
        return ['0~20','40~60','10~20','3~5','0~3', '0~2', '5~5', '0~1']
    elif behavior_type == 'braking_halt':
        return ['0~20','40~60','0~0','2~4','0~3', '0~2', '5~5', '0~1']
    elif behavior_type == 'sudden_braking_halt':    
        return ['0~20','40~60','0~0','0.5~2','0~3', '0~2', '5~5', '0~1'] 
    elif behavior_type == 'speed_up':    
        return ['0~20','0~10','40~60','2~4','0~2', '0~2', '5~5', '0~1']
    """
    
    if behavior_type == 'keeping':
        # agent1_S, agent1Speed, agent1EndSpeed, agent1DynamicDuration, agent1DynamicDelay, ｜ agent1EventStartDelay, TA_DynamicDuration, TA_DynamicDelay
        return ['0~20','40~60','40~60','5~5','0~3', '0~2', '5~5', '0~1']
        # # agent1_S, agent1Speed, agent1EndSpeed, agent1DynamicDuration, TA_DynamicDuration
        # return ['0~20','40~60','40~60','5~5', '5~5']
    elif behavior_type == 'braking':
        return ['0~20','40~60','10~20','3~5','0~3', '0~2', '5~5', '0~1']
        # return ['0~20','40~60','10~20','3~5', '5~5']
    elif behavior_type == 'braking_halt':
        return ['0~20','40~60','0~0','2~4','0~3', '0~2', '5~5', '0~1']
        # return ['0~20','40~60','0~0','2~4', '5~5']
    elif behavior_type == 'sudden_braking_halt':    
        return ['0~20','40~60','0~0','0.5~2','0~3', '0~2', '5~5', '0~1'] 
        # return ['0~20','40~60','0~0','0.5~2', '5~5'] 
    elif behavior_type == 'speed_up':    
        return ['0~20','0~10','40~60','2~4','0~2', '0~2', '5~5', '0~1']
        # return ['0~20','0~10','40~60','2~4', '5~5']

def _get_tag(value, param_name):
    if param_name == 'init_dynm':
        return 'standingStill' if value == 0 else 'moving'
    if param_name == 'init_lat_pos':
        if value == 'S': return 'sameLane'
        if value == 'R': return 'rightOfEgo'
        if value == 'L': return 'leftOfEgo'        
    if param_name == 'init_long_pos':
        if value == 'S': return 'sideOfEgo'
        if value == 'F': return 'inFrontOfEgo'
        if value == 'B': return 'rearOfEgo'
     
def generate_csv_content(behavior, behavior_type, descript, lateral_behavior, scenario_name, route_name, initRelPostAbbvLat, initRelPostAbbvLon, cetranNo, agent1_lat_mode, agent1_lat_direction, agent1_init_direction, isZigzag=False):
    # Write scenario description
    content = ScenarioContent('junction', cetran_number=cetranNo)
    content.ego_long_mode = 'drivingForward'
    content.ego_long_mode_type = 'cruising'
    content.ego_lat_mode = 'goingStraight'
    content.agents[0].update({
        'long_mode': behavior[6],
        'long_mode_type': behavior[7],
        'lat_mode':  agent1_lat_mode,
        'lat_direction': agent1_lat_direction,
        'init_direction': agent1_init_direction,
        'init_dynm': _get_tag(behavior[1], 'init_dynm'),
        'init_lat_pos': _get_tag(initRelPostAbbvLat, 'init_lat_pos'),
        'init_long_pos': _get_tag(initRelPostAbbvLon, 'init_long_pos'),
        'S': _get_param_by_behaviormode(behavior_type)[0],
        'Speed': _get_param_by_behaviormode(behavior_type)[1],
        '1_DynamicDelay': '0~0', # _get_param_by_behaviormode(behavior_type)[5]
        '1_SA_EndSpeed': _get_param_by_behaviormode(behavior_type)[2],
        '1_SA_DynamicDuration': _get_param_by_behaviormode(behavior_type)[3],
        '1_SA_DynamicDelay': '0~0', # _get_param_by_behaviormode(behavior_type)[4]
    })
    if not isZigzag:
        content.agents[0].update({
            '1_TA_DynamicDuration': _get_param_by_behaviormode(behavior_type)[6],
            '1_TA_DynamicDelay': '0~0', # _get_param_by_behaviormode(behavior_type)[7]
        })
    elif isZigzag:
        content.agents[0].update({
            '1_TA_Offset': '-1', #'-1~1'
            '1_TA_Period': '0.2~1',
            '1_TA_Times': '2', #'1~5'
        })
        ## 加上 zigzag 最低限速，避免車頭太不自然
        for name in ['Speed', '1_SA_EndSpeed']:
            range = content.agents[0][name]
            try:
                min_speed, max_speed = map(float, range.split('~'))
                if min_speed < 20.0:
                    print(f"[修正] {scenario_name} {name}的值為 {range}，將其設置為 20.0~20.0")
                content.agents[0][name] = '20.0~20.0'

                # else:
                #     print(f"[跳過] {scenario_name} 1_SA_EndSpeed的值為 {speed_range}，不符合條件")
                        
                pass
            except ValueError:
                # 若格式錯誤，跳過
                pass


    # Customize Parameter Range
    agent = set_offset(content, descript, lateral_behavior, agent1_init_direction)
    content.agents[0].update(agent)
    

    description = descript + behavior_type + lateral_behavior
    csv_row = {'description': description, 'scenario_name': scenario_name, 'route_name': route_name}
    csv_row.update(content.to_dict())
    return csv_row

def ensure_folder_exists(file_path):
    folder_path = os.path.dirname(file_path)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def save_config_yaml(config, file_path):
    ensure_folder_exists(file_path)
    yaml.dump(config, open(file_path, 'a+'))
 
def set_behavior_dict(behavior_type, behavior_mode):
    extracted_elements = [behavior_mode[5], behavior_mode[3],
                          behavior_mode[4], behavior_mode[2], behavior_mode[0], 'null']

    # behavior_dict = dict.fromkeys(['type','Start_speed', 'End_speed','Dynamic_duration','Dynamic_shape'],'')
    behavior_dict = dict.fromkeys(
        ['Type', 'Dynamic_delay', 'Dynamic_duration', 'Dynamic_shape', 'End', 'Use_route'], '')
    behavior_dict.update(
        zip(behavior_dict, [behavior_type] + extracted_elements))

    return behavior_dict


def clone_behavior_mode_and_wriite_content(behavior_type, behavior, agent1, agent1_act, agent1_lat_event, config, initRelPostAbbvLat, initRelPostAbbvLon, lateral_behavior, descript, agent1_lat_mode, agent1_lat_direction, agent1_init_direction, cetranNo=None, route='hct_default'):
    agent1['Start_speed'] = behavior[1]
    agent1_long_event = set_behavior_dict('speed',behavior)
    agent1_act['Events'] = []
    agent1_act['Events'].append(agent1_lat_event)
    agent1_act['Events'].append(agent1_long_event)
    agent1['Acts'] = [agent1_act]
    config['Actors'] = {'Agents': [agent1]}
    
    name_attribute = f'01{initRelPostAbbvLon}{initRelPostAbbvLat}-{lateral_behavior}'
    next_id = _get_next_id_in_folder(name_attribute)
    scenario_name = f'{name_attribute}_{next_id}'
    config['Scenario_name'] = scenario_name
    save_config_yaml(config, f'./scenario_config/{name_attribute}/{next_id}.yaml')

    isZigzag = True if agent1_act['Type'] == 'zigzag' else False
    csv_row = generate_csv_content(behavior, behavior_type, descript, lateral_behavior, scenario_name, route, initRelPostAbbvLat, initRelPostAbbvLon, cetranNo,  agent1_lat_mode, agent1_lat_direction, agent1_init_direction, isZigzag)
    # print(csv_row);exit()
    write_to_scenario_table(next_id, [csv_row], file_path= f'./scenario_config/{name_attribute}/{next_id}.csv')



# ================
# Customize Offset
# ================
def set_offset(content, descript, lateral_behavior, agent1_init_direction):
    agent = content.agents[0]

    def is_motorcycle_left(): return 'R-M2' in descript or 'L-M3' in descript
    def is_motorcycle_right(): return 'R-M3' in descript or 'L-M2' in descript
    def is_car(): return not (is_motorcycle_left() or is_motorcycle_right())

    # _Offset: 起始偏移量, _TA_Offset: 結束偏移量
    if 'CI' in lateral_behavior or 'CO' in lateral_behavior:
        if is_motorcycle_left():
            agent.update({'1_Offset': '-1.5~-0.5'})
        elif is_motorcycle_right():
            agent.update({'1_Offset': '0.5~1.5'})
        else:
            agent.update({'1_Offset': '-1.5~1.5'})

    elif ('U turn' in descript or 'turning left' in descript) and agent1_init_direction == 'sameAsEgo':
        if 'R-M2' in descript:
            agent.update({'1_Offset': '-1.5~-0.5'})
        elif 'R-M3' in descript:
            agent.update({'1_Offset': '0.5~1.5'})
        elif any(tag in descript for tag in ['-3', '-5', '-8']):
            agent.update({'1_Offset': '-1.5~1.5'})

    elif 'U turn' in descript and agent1_init_direction == 'oncoming':
        agent.update({'1_TA_Offset': '-1.5~1.5'})
        
    return agent