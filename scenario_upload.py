import requests
import json
from typing import List
import pandas as pd
import numpy as np
import time
import copy

from tqdm import tqdm
from pprint import pprint

from upload_utils import *
from cache_util import *

import argparse

if 'init':
    base_url = "http://172.30.1.139:3000/api"
    user_api_key = "18f94155-086c-48b5-a210-59b545b4a039"  # HCIS API Key
    headers = {
        "Authorization": f"users API-Key {user_api_key}",
    }
    # route = "route-666c15f9173ee59246206343 hct-default"
    route = "66e2bb985ac155b0acf389a4"
    
        
    tags_to_be_used_in_created_scenario = [
        # "behavior:intersection",
        "party:hcis",
        "deliver:2024Jan",
        "field:hct",
        "vehicle:car",
        "ego-behavior:go-straight",
        "roadtype:main-roadway",
        "combination:none",
        # "edit:5-parameter",
        "edit:narrow-down-param-range",
    ]
        
    
    test_objective = {
        "criticalityMetrics": [
            {
                # Pass Time Less Than
                "keyPerformanceIndicator": "66d6af255fff188fbab3f690",  # threshold should always be 0
                "threshold": 0,
            },
            {
                # Minimum Space Between Ego and Agents
                "keyPerformanceIndicator": "666c0d62173ee592462062aa",
                "threshold": 2,
            },
            {
                # Max Deceleration Less Than
                "keyPerformanceIndicator": "666c0d33173ee592462062a2",
                "threshold": 10,
            },
            {
                # Collision Less Than
                "keyPerformanceIndicator": "666c0d22173ee5924620629a",  # threshold should always be 0
                "threshold": 0,
            }
        ]
    }

    cache = {}
    CACHE_FILE = 'cache.json'
    
def handle_tags_creation_and_get_ids(tags: List[str]):
    global base_url
    url = f"{base_url}/tags?depth=1&limit=1000000"
    tags_doc = get_cache_data(url, headers)
    # print(tags_doc)
    # exit
    tags_doc = tags_doc["docs"]
    # tags_doc = requests.get(
    #     f"{base_url}/tags?depth=1&limit=1000000",
    #     headers=headers).json()["docs"]
    all_tags = dict( [ (tag["name"], tag["id"]) for tag in tags_doc ] )

    
    for tag in tags:
        if tag not in all_tags:
            # Create tags that do not exist
            # try:
            if 1:
                response = requests.post(
                    f"{base_url}/tags",
                    headers=headers,
                    json={
                        "name": tag,
                    }
                )
                if response.status_code == 201 and response.json().get("message") == "Tag successfully created.":
                    created_id = response.json()["doc"]["id"]
                    print(f"Tag '{tag}' created successfully. ID: {created_id}")
                    all_tags[tag] = created_id
                    # Update the cache with the newly created tag
                    tags_doc = get_cache_data(base_url, headers)
                    # print(tags_doc)
                    # exit
                    tags_doc = tags_doc["docs"]
                    all_tags = dict( [ (tag["name"], tag["id"]) for tag in tags_doc ] )
                    # exit()
                else:
                    raise Exception(f"Unexpected response while creating tag '{tag}': {response.json()}")
            # except Exception as e:
            else:
                raise Exception(f"Failed to create tag '{tag}': {e}")


    return list({tag: all_tags[tag] for tag in tags}.values())
                
def upload_openscenario_file(file_path, filename=None):    
    global base_url
    url = f"{base_url}/openScenarios?limit=10000"
    tags_doc = get_cache_data(url, headers)['docs']
    # tags_doc = requests.get(
    #     # f"{base_url}/scenarios?where[createdBy][equals]=HCIS%20Lab",
    #     f"{base_url}/openScenarios?limit=10000",
    #     headers=headers).json()["docs"]

    all_tags = dict( [ (tag["filename"], tag["id"]) for tag in tags_doc ] )

    if filename is None:
        filename = file_path.split("/")[-1]

    with open(file_path, "rb") as f:
        files = {
            "file": (filename, f, "application/octet-stream")
        }
  
        if filename in all_tags.keys():
            print("  Xosc file already exists.")
            # return
            scenario_uuid = all_tags[filename]
            # update xosc
            r = requests.patch(
                f"{base_url}/openScenarios/{scenario_uuid}",
                headers=headers,
                files=files,
            )
        else:
            time.sleep(0.5)
            r = requests.post(
                f"{base_url}/openScenarios",
                headers=headers,
                files=files,
            )
    scenario_id = r.json()["doc"]["id"]
    # print(json.dumps(r.json(), indent=4))
    print("  ",r.json().get("message"))
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

def use_scenario_string(content):
    return {
        "type": "String",
        "content": content,
    }


import requests
from functools import lru_cache

# @lru_cache(maxsize=None)
def fetch_scenarios(url, headers):
    # print(url)
    # print(headers)
    response = requests.get(
        url,
        headers=headers
    )
    return response.json()["docs"]

def K_check_scenario_exists(base_url, headers, filename):
    # print(base_url, headers, filename)
    # print(type(headers), headers)
    # return
    # headers_tuple = tuple(headers.items())
    scenarios_doc = fetch_scenarios(base_url, headers)
    all_scenarios = dict((scenario["scenarioId"], scenario["id"]) for scenario in scenarios_doc)
    
    if filename in all_scenarios.keys():  # Update
        print("  Scenario already exists.")
        return True

    return False

def check_scenario_exists(url, headers, filename):
    data_list = get_cache_data(url, headers)
    return filename in data_list 

# def get_cache_data(url, headers, clear_cache=False):

#     global cache
#     current_time = time.time()
    
#     # Cache key based on URL and headers
#     cache_key = (url, tuple(sorted(headers.items())))
#     print("cache_key:", cache_key)
#     print(cache);exit
    
#     # Check if the result is in the cache and still valid
#     if cache_key in cache and cache[cache_key]['expires_at'] > current_time and not clear_cache:
#         data_list = cache[cache_key]['data']
#     else:
#         # Fetch the data from the URL
#         try:
#             response = requests.get(url, headers=headers)
#             # response.raise_for_status()
#             data_list = response.json()  # Assuming the response is JSON
#             print("No Cache data, GET")
#         except Exception as e:
#             print(f"Error fetching data: {e}")
#             return False
        
#         # Update the cache
#         cache[cache_key] = {
#             'data': data_list,
#             'expires_at': current_time + 300  # Cache for 60 seconds
#         }
    
#     return data_list



def upload(scenario_id):
    scenario_folder = scenario_id[:scenario_id.rfind("_")]
    scenario_index = scenario_id[scenario_id.rfind("_")+1:].replace(".xosc", "")
    
    if "_" in scenario_folder:
        parenet_folder = "scenario_config_combined"
    else:
        parenet_folder = "scenario_config"
    # print(f'./scenario_config/{scenario_folder}/{scenario_index}.csv')
    # exit()
    df = pd.read_csv(f'/home/hcis-s19/Documents/ChengYu/hcis_scenario_generation/{parenet_folder}/{scenario_folder}/{scenario_index}.csv')
    # print(df)
    result = df.replace({np.nan:None})
    if result.empty:
        print(f"Scenario ID {scenario_id}'s CSV file not found.  " + f'./{parenet_folder}/{scenario_folder}/{scenario_index}.csv')
        return False
    else:
        result = result.to_dict('records')[0]


    global tags_to_be_used_in_created_scenario
    current_tags_to_be_used_in_created_scenario = copy.copy(tags_to_be_used_in_created_scenario)
    current_tags_to_be_used_in_created_scenario += add_itri_tags(result)
    tag_ids_to_be_used_in_created_scenario = handle_tags_creation_and_get_ids(current_tags_to_be_used_in_created_scenario)
    # print("current_tags_to_be_used_in_created_scenario",current_tags_to_be_used_in_created_scenario)
    description = result['description']
    # exit()
        
    parameters = write_param(result)  # Should be the same name using in the OpenSCENARIO file

    tag_tree = build_tagTree_from_csv(result)

    """
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
    """

    valid_conditions = { # Only if these conditions are triggered will the trial be considered valid.
        "conditionLogic": "And",  # Available options: "And", "Or"
        "conditions": [
            "EgoApproachInitWp"
        ]
    }
    fail_conditions = { # If these conditions are triggered, the trial will stop right away.
        # "conditionLogic": "Or",  # Available options: "And", "Or"
        # "conditions": [
        #     "Condition B", "Condition C"
        # ]
    }
    end_conditions = { # If these conditions are triggered, the trial will stop right away.
        # "conditionLogic": "Or",  # Available options: "And", "Or"
        # "conditions": [
        #     "Condition D", "Condition E"
        # ]
    }
    start_conditions = {  # After theses events start, the scenario will be recorded.
        "conditionLogic": "And",  # Available options: "And", "Or"
        "conditions": [
            "EgoApproachInitWp"
        ]
    }
    conditions = {
        "validConditions": valid_conditions,
        "failConditions": fail_conditions,
        "endConditions": end_conditions,
        "startObservationSamplingConditions": start_conditions
    }


    # observation_recording_agents = ["Agent1"]
    observation_recording_agents = []


    filename = f"{result['scenario_name']}"
    file_path = f"/home/hcis-s19/Documents/ChengYu/ITRI/xosc/1121/{filename}.xosc"

    # exit()
    openScenarioField = upload_openscenario_file(file_path)
    # openScenarioField = None

    # openScenarioField = use_scenario_string("<OpenSCENARIO> <!-- some scenario --> </OpenSCENARIO>")
    # print(openScenarioField)
    # description = [val for key, val in descriptions.items() if key in filename]
    # description = " ,and ".join(description)+"."
    data = create_request_body(
        scenarioId = filename,
        tags = tag_ids_to_be_used_in_created_scenario,
        description = description,
        parameters = parameters,
        openDrive = "666c15f9173ee59246206343",  # ID of hct_6.xodr
        openScenario = openScenarioField,
        usedRoute = route,
        tagTree = tag_tree,
        testObjectives = test_objective,
        conditions = conditions,
        observationRecordingAgents = observation_recording_agents,
        egoTargetSpeed = 50
    )

    r = ''
    # """
    global base_url
    url = f"{base_url}/scenarios?limit=10000&where[createdBy][equals]=HCIS%20Lab"
    scenarios_doc = get_cache_data(url, headers)['docs']
    # scenarios_doc = requests.get(
    #     f"{base_url}/scenarios?limit=10000&where[createdBy][equals]=HCIS%20Lab",
    #     headers=headers).json()["docs"]
    all_scenarios = dict( [ (scenario["scenarioId"], scenario["id"]) for scenario in scenarios_doc ] )

    # """
    
    url = f"{base_url}/scenarios?limit=10000&where[createdBy][equals]=HCIS%20Lab"
    # print((url, headers, filename))
    exists = check_scenario_exists(url, headers, filename)
    # print(f"Scenario is {exists}!")
    # return
    if exists:
        print(f"Scenario {filename} exists.")
        return
        r = requests.patch(f"{base_url}/scenarios/{all_scenarios[filename]}", headers=headers, json=data)
    else:
        # print(data)
        time.sleep(0.1)
        r = requests.post(f"{base_url}/scenarios", headers=headers, json=data)
        # print(f"Scenario {filename} does not exist.")

    """
    if filename in all_scenarios.keys(): # Update
        print("  Scenario already exists.")
        return
        r = requests.patch(f"{base_url}/scenarios/{all_scenarios[filename]}", headers=headers, json=data)
    else: # Create
        time.sleep(0.1)
        r = requests.post(f"{base_url}/scenarios", headers=headers, json=data)
    """
        
    try:
        print("  ",r.json().get("message"))
        if (r.status_code == 201 and r.json().get("message") == "Scenario successfully created.") or \
           (r.status_code == 200 and r.json().get("message") == "Updated successfully."):
            return 1
        else:
            print("status", r.status_code)
            print(json.dumps(r.json(), indent=4))
            pprint(tag_tree)
            return 0
    except Exception as e:
        print(e)
    except:
        print(r.text)
        
        
if __name__ == '__main__':
    clear_cache_file()
    try: 
        argparser = argparse.ArgumentParser()
        argparser.add_argument(
            '-s', '--sc',
            metavar='S',
            default='',
            nargs="+",
            help='Scenario category (default: all)')
        args = argparser.parse_args()

        
        
        scenario_ids = args.sc
        if args.sc[0] == 'all':
            scenario_ids = []
            for file in os.listdir("/home/hcis-s19/Documents/ChengYu/ITRI/xosc/1231/"):
                if file.endswith('.xosc'):
                    scenario_ids.append(file)

        # fetch_scenarios.cache_clear()

        success_upload = 0
        for scenario_id in tqdm(scenario_ids):
            print(f"Uploading scenario {scenario_id}...")
            
            if upload(scenario_id):
                success_upload += 1
            else:
                print(f"  Failed to upload: {scenario_id}")
            # break

            

    finally:
        # 清除緩存
        clear_cache_file()
        print(f'{success_upload} Done.')



    

    # data = {'id': 'hcis_4_01FR-TL','parameters': [{'name': 'Agent0_S', 'unit': 'm', 'min': '0', 'max': '20'}], 'openDrive': '666c15f9173ee59246206343', 'openScenarioField': {'type': 'String', 'content': '<OpenSCENARIO> <!-- some scenario --> </OpenSCENARIO>'}, 'usedRoute': 'route-666c15f9173ee59246206343 hct-default', 'tagTree': {}, 'testObjectives': {'criticalityMetrics': [{'keyPerformanceIndicator': '666c0d22173ee5924620629a', 'threshold': 1, 'description': 'No collision allowed'}, {'keyPerformanceIndicator': '666c0d33173ee592462062a2', 'threshold': 10, 'id': '666c16533638a200018f9d21'}]}, 'validConditions': [], 'startObservationSamplingConditions': [{'condition': 'EgoApproachInitWp'}], 'observationRecordingAgents': [{'name': 'Agent0'}], 'egoTargetSpeed': 60}

    # {'id': 'test_scenario_from_api', 'tags': ['behavior:cut-in', 'party:hcis', 'deliver:2024Jul', 'src:cetran', 'field:hct'], 'description': 'A vehicle crossing when the ego vehicle is about to enter the intersection.', 'parameters': [{'name': 'TargetSpeed', 'unit': 'm/s', 'min': 20, 'max': 40}, {'name': 'TargetLateralOffset', 'unit': 'm', 'min': 1, 'max': -1}, {'name': 'TargetS', 'unit': 'm', 'min': -5, 'max': 5}], 'openDrive': '666c15f9173ee59246206343', 'openScenarioField': {'type': 'String', 'content': '<OpenSCENARIO> <!-- some scenario --> </OpenSCENARIO>'}, 'usedRoute': 'route-666c15f9173ee59246206343 hct-default', 'tagTree': {'ego': {'vehicleLongitudinalActivity': {'mode': 'drivingForward', 'drivingForwardMode': 'cruising'}, 'vehicleLateralActivity': {'mode': 'goingStraight'}}, 'actors': [{'vehicleLongitudinalActivity': {'mode': 'drivingForward', 'drivingForwardMode': 'cruising'}, 'vehicleLateralActivity': {'mode': 'goingStraight'}, 'initialState': {'direction': 'oncoming', 'dynamics': 'standingStill', 'lateralPosition': 'leftOfEgo', 'longitudinalPosition': 'inFrontOfEgo'}, 'leadVehicle': {'mode': 'appearing', 'appearingMode': 'gapClosing'}}], 'roadLayout': {'mode': 'junction', 'junctionMode': 'noTrafficLight'}}, 'testObjectives': {'criticalityMetrics': [{'keyPerformanceIndicator': '666c0d22173ee5924620629a', 'threshold': 1, 'description': 'No collision allowed'}, {'keyPerformanceIndicator': '666c0d33173ee592462062a2', 'threshold': 10, 'id': '666c16533638a200018f9d21'}]}, 'validConditions': [{'condition': 'TargetStartWhenEgoCloseToTheJunction'}], 'startObservationSamplingConditions': [{'condition': 'TargetStartWhenEgoCloseToTheJunction'}, {'condition': 'SomeOtherCondition'}], 'observationRecordingAgents': [{'name': 'Target1'}, {'name': 'Target2'}], 'egoTargetSpeed': 40}

    # data = 
    # print(data)
    # exit()
    