import requests
import json
from typing import List
import pandas as pd
import numpy as np

from upload_utils import *




def create_tags_if_not_exists(tags: List[str]):
    tags_doc = requests.get(
        f"{base_url}/tags?depth=1&limit=1000000",
        headers=headers).json()["docs"]
    all_tags = [tag["id"] for tag in tags_doc]
    print(f"Existing tags: {all_tags}")
    # return

    for tag in tags:
        if tag not in all_tags:
            try:
                r = requests.post(
                    f"{base_url}/tags",
                    headers=headers,
                    json={
                        "id": tag,
                        "name": tag,
                        "createdBy": "HCISLab",
                        "description": tag  # optional
                    }
                )
                print(r.json())
            except Exception as e:
                print(e)
                print(f"Failed to create tag {tag}")
                
def upload_openscenario(file_path, filename=None):
    if filename is None:
        filename = file_path.split("/")[-1]
    with open(file_path, "rb") as f:
        files = {
            "file": (filename, f, "application/octet-stream")
        }
        # print(files);exit()
        r = requests.post(
            f"{base_url}/openScenarios",
            headers=headers,
            files=files,
        )
    scenario_id = r.json()["doc"]["id"]
    print(json.dumps(r.json(), indent=4))
    return {
        "type": "File",
        "openScenario": scenario_id
    }

def build_tagTree_from_csv(row):
    scenario = ScenarioTagTree()
    scenario.set_ego_vehicle_activity(row)
    scenario.add_actor(row)
    scenario.set_road_layout(row)
    
    return scenario.tagTree

def itri_tags(cetran_number, agent_direction, agent_lat_mode,  agent_lat_direction):
    tags = []
    if cetran_number != None:
        tags.append(f"src:cetran:{cetran_number}")
    if agent_direction == 'sameAsEgo':
        agent_direction = 'same'
    if agent_lat_mode == 'goingStraight':
        agent_behavior = 'go-straight'
    else:
        agent_behavior = f"{agent_lat_mode}-{agent_lat_direction}"

    tags.append(f"agent-direction:{agent_direction}")
    tags.append(f"agent-behavior:{agent_behavior}")

    return tags
    
def use_scenario_string(content):
    return {
        "type": "String",
        "content": content,
    }

if 'init':
    base_url = "http://172.30.1.139:3000/api"
    user_api_key = "18f94155-086c-48b5-a210-59b545b4a039"  # HCIS API Key
    headers = {
        "Authorization": f"users API-Key {user_api_key}",
    }
    route = "route-666c15f9173ee59246206343 hct-default"
    
    tags_to_be_used_in_created_scenario = [
        "behavior:intersection",
        "party:hcis",
        "deliver:2024Jul",
        "field:hct",
        "vehicle:car",
        "ego-behavior:go-straight",
        "roadtype:main-roadway",
    ]
    
    test_objective = {
        "criticalityMetrics": [
            {
                "keyPerformanceIndicator": "666c0d22173ee5924620629a",  # "Collision Less Than"
                "threshold": 1,
                "description": "No collision allowed",
            },
            {
                "keyPerformanceIndicator": "666c0d33173ee592462062a2",  # "Max Deceleration Less Than"
                "threshold": 10,
                "id": "666c16533638a200018f9d21"
            }
        ]
    }


scenario_id = 70

df = pd.read_csv('./HCIS_scenarios.csv')
result = df[df['scenario_id'] == scenario_id].replace({np.nan:None})
if result.empty:
    print(f"Scenario ID {scenario_id} not found in the CSV file")
    exit()
else:
    result = result.to_dict('records')[0]


itri_tags(result['cetran_number'], result['agent1_init_direction'], result['agent1_lat_mode'], result['agent1_lat_direction'])

# create_tags_if_not_exists(tags_to_be_used_in_created_scenario)
description = result['description']
    
parameters = [  # Should be the same name using in the OpenSCENARIO file
    {
    "name": "Agent0_S",
    "unit": "m",
    "min": result['agent1_S'].split('-')[0],
    "max": result['agent1_S'].split('-')[1],
},
{
    "name": "Agent0Speed",
    "unit": "m/s",
    "min": result['agent1_Speed'].split('-')[0],
    "max": result['agent1_Speed'].split('-')[1],
},
{

    "name": "Agent0LowSpeed",
    "unit": "m/s",
    "min": result['agent1_LowSpeed'].split('-')[0],
    "max": result['agent1_LowSpeed'].split('-')[1],
},

{
    "name": "Agent0DynamicDuration",
    "unit": "s",
    "min": result['agent1_DynamicDuration'].split('-')[0],
    "max": result['agent1_DynamicDuration'].split('-')[1],
},
{
    "name": "Agent0DynamicDelay",
    "unit": "s",
    "min": result['agent1_DynamicDelay'].split('-')[0],
    "max": result['agent1_DynamicDelay'].split('-')[1],
},
]

tag_tree = build_tagTree_from_csv(result)

# tag_tree = {
#     "ego": {
#         "vehicleLongitudinalActivity": {
#             "mode": "drivingForward",
#             "drivingForwardMode": "cruising"
#         },
#         "vehicleLateralActivity": {
#             "mode": "goingStraight"
#         }
#     },
#     "actors": [
#     {

#         "vehicleLongitudinalActivity": {

#             "mode": "drivingForward",
#             "drivingForwardMode": "cruising"

#         },
#         "vehicleLateralActivity": {

#             "mode": "goingStraight"

#         },
#         "initialState": {

#             "direction": "oncoming",
#             "dynamics": "standingStill",
#             "lateralPosition": "leftOfEgo",
#             "longitudinalPosition": "inFrontOfEgo"

#         },
#         "leadVehicle": {

#             "mode": "appearing",
#             "appearingMode": "gapClosing"

#         },
#     }
#     ],
#     "roadLayout": {
#         "mode": "junction",
#         "junctionMode": "noTrafficLight"
#     }
# }

# print(tag_tree)
        
# exit()





valid_conditions = [ # will be valid if trigger this condition, empty means all conditions are valid
    # {
        #all, so is empty
        # "condition": "TargetStartWhenEgoCloseToTheJunction",
        # "condition": "EgoApproachInitWp" 
    # }
]

start_conditions = [ # the start recording conditions
    # {
    #     "condition": "TargetStartWhenEgoCloseToTheJunction"
    # },
    {
        "condition": "EgoApproachInitWp"
    }
]

observation_recording_agents = [
    {
        "name": "Agent0"
    },
]


filename = f"{result['scenario_name']}"
file_path = f"/home/hcis-s19/Documents/ChengYu/ITRI/xosc/0722/{filename}.xosc"
print(filename)



openScenarioField = upload_openscenario(file_path)
# openScenarioField = None

# openScenarioField = use_scenario_string("<OpenSCENARIO> <!-- some scenario --> </OpenSCENARIO>")
print(openScenarioField)
# description = [val for key, val in descriptions.items() if key in filename]
# description = " ,and ".join(description)+"."
data = create_request_body(
    scenarioId = filename,
    tags = tags_to_be_used_in_created_scenario,
    description = description,
    parameters = parameters,
    openDrive = "666c15f9173ee59246206343",  # ID of hct_6.xodr
    openScenario = openScenarioField,
    usedRoute = route,
    tagTree = tag_tree,
    testObjectives = test_objective,
    validConditions = valid_conditions,
    startObservationSamplingConditions = start_conditions,
    observationRecordingAgents = observation_recording_agents,
    egoTargetSpeed = 60
)

# data = {'id': 'hcis_4_01FR-TL','parameters': [{'name': 'Agent0_S', 'unit': 'm', 'min': '0', 'max': '20'}], 'openDrive': '666c15f9173ee59246206343', 'openScenarioField': {'type': 'String', 'content': '<OpenSCENARIO> <!-- some scenario --> </OpenSCENARIO>'}, 'usedRoute': 'route-666c15f9173ee59246206343 hct-default', 'tagTree': {}, 'testObjectives': {'criticalityMetrics': [{'keyPerformanceIndicator': '666c0d22173ee5924620629a', 'threshold': 1, 'description': 'No collision allowed'}, {'keyPerformanceIndicator': '666c0d33173ee592462062a2', 'threshold': 10, 'id': '666c16533638a200018f9d21'}]}, 'validConditions': [], 'startObservationSamplingConditions': [{'condition': 'EgoApproachInitWp'}], 'observationRecordingAgents': [{'name': 'Agent0'}], 'egoTargetSpeed': 60}

# {'id': 'test_scenario_from_api', 'tags': ['behavior:cut-in', 'party:hcis', 'deliver:2024Jul', 'src:cetran', 'field:hct'], 'description': 'A vehicle crossing when the ego vehicle is about to enter the intersection.', 'parameters': [{'name': 'TargetSpeed', 'unit': 'm/s', 'min': 20, 'max': 40}, {'name': 'TargetLateralOffset', 'unit': 'm', 'min': 1, 'max': -1}, {'name': 'TargetS', 'unit': 'm', 'min': -5, 'max': 5}], 'openDrive': '666c15f9173ee59246206343', 'openScenarioField': {'type': 'String', 'content': '<OpenSCENARIO> <!-- some scenario --> </OpenSCENARIO>'}, 'usedRoute': 'route-666c15f9173ee59246206343 hct-default', 'tagTree': {'ego': {'vehicleLongitudinalActivity': {'mode': 'drivingForward', 'drivingForwardMode': 'cruising'}, 'vehicleLateralActivity': {'mode': 'goingStraight'}}, 'actors': [{'vehicleLongitudinalActivity': {'mode': 'drivingForward', 'drivingForwardMode': 'cruising'}, 'vehicleLateralActivity': {'mode': 'goingStraight'}, 'initialState': {'direction': 'oncoming', 'dynamics': 'standingStill', 'lateralPosition': 'leftOfEgo', 'longitudinalPosition': 'inFrontOfEgo'}, 'leadVehicle': {'mode': 'appearing', 'appearingMode': 'gapClosing'}}], 'roadLayout': {'mode': 'junction', 'junctionMode': 'noTrafficLight'}}, 'testObjectives': {'criticalityMetrics': [{'keyPerformanceIndicator': '666c0d22173ee5924620629a', 'threshold': 1, 'description': 'No collision allowed'}, {'keyPerformanceIndicator': '666c0d33173ee592462062a2', 'threshold': 10, 'id': '666c16533638a200018f9d21'}]}, 'validConditions': [{'condition': 'TargetStartWhenEgoCloseToTheJunction'}], 'startObservationSamplingConditions': [{'condition': 'TargetStartWhenEgoCloseToTheJunction'}, {'condition': 'SomeOtherCondition'}], 'observationRecordingAgents': [{'name': 'Target1'}, {'name': 'Target2'}], 'egoTargetSpeed': 40}

# data = 
# print(data)
# exit()
r = requests.post(f"{base_url}/scenarios", headers=headers, json=data)
try:
    print(json.dumps(r.json(), indent=4))
except Exception as e:
    print(e)
except:
    print(r.text)