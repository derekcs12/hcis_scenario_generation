import os
import csv
import glob
import pandas as pd
from typing import List
import re

class ScenarioContent:
    def __init__(self, road_layout, road_layout_mode='noTrafficLight', cetran_number=None, agent_number=1):
        self.road_layout = road_layout
        self.road_layout_mode = road_layout_mode
        self.cetran_number = cetran_number
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
            'S': '0-20',
            'Speed': None,
            'LowSpeed': None,
            'DynamicDuration': None,
            'DynamicDelay': None,
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
                re[f'agent{i+1}_{key}'] = value
                
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
                    "direction": row[f'agent{i}_init_direction'],
                    "dynamics": row[f'agent{i}_init_dynm'],
                    "lateralPosition": row[f'agent{i}_init_lat_pos'],
                    "longitudinalPosition": row[f'agent{i}_init_long_pos']
                },
                "leadVehicle": {
                    "mode": 'appearing',
                    "appearingMode": 'gapClosing'
                },
            }
            actor['vehicleLongitudinalActivity'] = self._set_longitudinal_activity(row[f'agent{i}_long_mode'], row[f'agent{i}_long_mode_type'])
            actor['vehicleLateralActivity'] = self._set_lateral_activity(row[f'agent{i}_lat_mode'], row[f'agent{i}_lat_direction'])
            self.tagTree["actors"].append(actor)

    def set_road_layout(self, row):
        self.tagTree["roadLayout"]["mode"] = row['road_layout']
        self.tagTree["roadLayout"][f"{row['road_layout']}Mode"] = row['road_layout_mode']





def get_tag(value, param_name):
    if param_name == 'init_dynm':
        return 'standingStill' if value == 0 else 'moving'
    if param_name == 'init_lat_pos':
        if value == 'S': return 'sameAsEgo'
        if value == 'R': return 'rightOfEgo'
        if value == 'L': return 'leftOfEgo'        
    if param_name == 'init_long_pos':
        if value == 'S': return 'sideOfEgo'
        if value == 'F': return 'inFrontOfEgo'
        if value == 'B': return 'rearOfEgo'
        
        
def get_next_scenario_id(directory='./scenario_config'):
    # Regular expression to match filenames with format {party}_{scenario_id}
    pattern = re.compile(r'^[^_]+_(\d+)_.*$')
    
    max_scenario_id = 0
    
    # List all files in the directory
    for filename in os.listdir(directory):
        match = pattern.match(filename)
        if match:
            scenario_id = int(match.group(1))
            if scenario_id > max_scenario_id:
                max_scenario_id = scenario_id
    
    # Calculate the next scenario ID
    next_scenario_id = max_scenario_id + 1
    
    return next_scenario_id

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
    

    columns = ['scenario_id','scenario_name','description','road_layout','road_layout_mode', 'cetran_number', 'ego_long_mode','ego_long_mode_type', 'ego_lat_mode', 'ego_lat_direction',
               'agent1_type', 'agent1_long_mode', 'agent1_long_mode_type', 'agent1_lat_mode', 'agent1_lat_direction',
               'agent1_init_direction', 'agent1_init_dynm', 'agent1_init_lat_pos', 'agent1_init_long_pos',
               'agent1_S','agent1_Speed','agent1_LowSpeed','agent1_DynamicDuration','agent1_DynamicDelay', # BehaviorMode Parameters
               ]    # Check if the file exists
    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=columns)
        df.to_csv(file_path, index=False)
    # print(content);exit()
            
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
            validConditions: List[dict],
            startObservationSamplingConditions: List[dict],
            observationRecordingAgents: List[dict],
            egoTargetSpeed: float
        ):
    return {
        "id": scenarioId,
        "tags": tags,
        "description": description,
        "parameters": parameters,
        "openDrive": openDrive,
        "openScenarioField": openScenario,
        "usedRoute": usedRoute,
        "tagTree": tagTree,
        "testObjectives": testObjectives,
        "validConditions": validConditions,
        "startObservationSamplingConditions": startObservationSamplingConditions,
        "observationRecordingAgents": observationRecordingAgents,
        "egoTargetSpeed": egoTargetSpeed
    }
    

    
