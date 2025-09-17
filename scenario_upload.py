import os
import json
import time
import copy
import pandas as pd
import numpy as np
import argparse
import requests


from tqdm import tqdm
from pprint import pprint
from typing import List
from datetime import date

from utils.upload import *
from utils.cache import *
from utils.assign_route import process_yaml_file

"""
Usage:
    python scenario_upload.py -s queue
"""

RUNTIME_DATA_DIR = 'runtime_data'


# ===========================================================================================
# Global Variables
# ===========================================================================================
if 'init':
    base_url = "http://172.30.1.139:3000/api"
    user_api_key = "18f94155-086c-48b5-a210-59b545b4a039"  # HCIS API Key
    headers = {
        "Authorization": f"users API-Key {user_api_key}",
    }
    # route = "route-666c15f9173ee59246206343 hct-default"
    route_id = {
        'hsinchu_gfr_pr_br_elr': '66e2bb985ac155b0acf389a4', # 靠左
        'hcis_route2': '678bcecc26076f8d8be39e95', # 靠右
        'hct_default': '66e2bb745ac155b0acf3896b'
    }
    
        
    tags_to_be_used_in_created_scenario = [
        # "behavior:intersection",
        "party:hcis",
        "deliver:2025Jul",
        "field:hct",
        "vehicle:car",
        "ego-behavior:go-straight",
        "roadtype:main-roadway",
        # "combination:none",
        # "edit:5-parameter",
        "edit:raw-param-range",
        "edit:10-sample-scenarios",
        # "edit:zz_range",
        # "edit:new_stop_condition",
        "edit:ego_speed_30",
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

    # Cache configuration
    cache = {}
    CACHE_FILE = 'cache.json'


# ===========================================================================================
# Helper Functions
# ===========================================================================================

def handle_tags_creation_and_get_ids(tags: List[str]):
    """Handle tag creation and return their IDs."""
    print("   [TAG] Handling tags...")
    
    global base_url
    url = f"{base_url}/tags?depth=1&limit=1000000"
    tags_doc = get_cache_data(url, headers)
    
    if "docs" not in tags_doc:
        raise KeyError(f"'docs' key not found in the response: {tags_doc}")
    
    tags_doc = tags_doc["docs"]
    all_tags = dict([(tag["name"], tag["id"]) for tag in tags_doc])

    for tag in tags:
        if tag not in all_tags:
            print(f"   [TAG] Tag '{tag}' does not exist, creating...")
            response = requests.post(
                f"{base_url}/tags",
                headers=headers,
                json={"name": tag}
            )
            # print(response.json()); exit()
            if response.status_code == 201 and response.json().get("message") == "Tag successfully created.":
                created_id = response.json()["doc"]["id"]
                print(f"   [TAG] Tag '{tag}' created successfully. ID: {created_id}")
            else:
                raise Exception(f"Unexpected response while creating tag '{tag}': {response.json()}")
            
    # Update the tags data
    tags_doc = fetch_and_update_cache(url, headers)  # Update cache after creating tags
    tags_doc = tags_doc["docs"]
    all_tags = dict([(tag["name"], tag["id"]) for tag in tags_doc])
    tags_ids = [all_tags[tag] for tag in tags]
    
    return tags_ids
                
def upload_openscenario_file(file_path, filename=None):
    """Upload or update an OpenScenario file."""
    global base_url
    
    if filename is None:
        filename = file_path.split("/")[-1]
    
    # First check if scenario exists in /scenarios endpoint
    scenarios_url = f"{base_url}/scenarios?limit=100000"
    scenarios_doc = get_cache_data(scenarios_url, headers)['docs']
    
    # Check if any scenario uses this filename in its openScenario
    scenario_uuid = None
    for scenario in scenarios_doc:
        if (scenario.get('openScenario') and 
            scenario['openScenario'].get('type') == 'File' and
            scenario['openScenario'].get('filename') == filename):
            scenario_uuid = scenario['openScenario']['openScenario']
            print(f"   [XOSC] Found existing scenario using this file, openScenario UUID: {scenario_uuid}")
            break
    
    # If not found in scenarios, check openScenarios endpoint
    if scenario_uuid is None:
        openscenarios_url = f"{base_url}/openScenarios?limit=100000"
        openscenarios_doc = get_cache_data(openscenarios_url, headers)['docs']
        all_openscenarios = dict([(tag["filename"], tag["id"]) for tag in openscenarios_doc])
        
        if filename in all_openscenarios.keys():
            scenario_uuid = all_openscenarios[filename]
            print("   [XOSC] File already exists in openScenarios.")

    with open(file_path, "rb") as f:
        files = {
            "file": (filename, f, "application/octet-stream")
        }
        
        if scenario_uuid is not None:
            print("   [XOSC] Update by ID....")
            # Update xosc
            r = requests.patch(
                f"{base_url}/openScenarios/{scenario_uuid}",
                headers=headers,
                files=files,
            )
            time.sleep(1)
        else:
            print("   [XOSC] Creating file...")
            r = requests.post(
                f"{base_url}/openScenarios",
                headers=headers,
                files=files,
            )
            time.sleep(1)
            
    scenario_id = r.json()["doc"]["id"]
    # print(json.dumps(r.json(), indent=4))
    print(f"   [XOSC] {r.json().get('message')} ID: {scenario_id}")
    
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


def fetch_scenarios(url, headers):
    # print(url)
    # print(headers)
    response = requests.get(url, headers=headers)
    return response.json()["docs"]


def check_scenario_exists(url, headers, filename):
    data_list = get_cache_data(url, headers)
    return filename in data_list


def remove_scenario_from_queue(scenario_id):
    # Read the scenario queue from the file
    with open(f'{RUNTIME_DATA_DIR}/scenario_queue.txt', 'r') as queue_file:
        scenario_ids = queue_file.readlines()

    # Remove the specified scenario ID from the list
    scenario_ids = [s.strip() for s in scenario_ids if s.strip() != scenario_id]

    # Write the updated list back to the file
    with open(f'{RUNTIME_DATA_DIR}/scenario_queue.txt', 'w') as queue_file:
        for s in scenario_ids:
            queue_file.write(f"{s}\n")

# ===========================================================================================
# Main Upload Function  
# ===========================================================================================

def upload(scenario_id):
    scenario_folder = scenario_id[:scenario_id.rfind("_")]
    scenario_index = scenario_id[scenario_id.rfind("_")+1:].replace(".xosc", "")
    scenario_id = scenario_id.replace(".xosc", "")  # Remove the .xosc extension for consistency
    
    if "_" in scenario_folder:
        parent_folder = "scenario_config_combined"
    else:
        parent_folder = "scenario_config"
    # print(f'./scenario_config/{scenario_folder}/{scenario_index}.csv')
    # exit()

    df = pd.read_csv(
        f'/home/hcis-s19/Documents/ChengYu/hcis_scenario_generation/{parent_folder}/{scenario_folder}/{scenario_index}.csv'
    )
    # print(df)
    result = df.replace({np.nan: None})
    if result.empty:
        print(
            f"Scenario ID {scenario_id}'s CSV file not found.  "
            f'./{parent_folder}/{scenario_folder}/{scenario_index}.csv'
        )
        return False
    else:
        result = result.to_dict('records')[0]

    global tags_to_be_used_in_created_scenario
    current_tags_to_be_used_in_created_scenario = copy.copy(tags_to_be_used_in_created_scenario)
    current_tags_to_be_used_in_created_scenario += add_itri_tags(result)
    tag_ids_to_be_used_in_created_scenario = handle_tags_creation_and_get_ids(
        current_tags_to_be_used_in_created_scenario
    )
    # print("current_tags_to_be_used_in_created_scenario", current_tags_to_be_used_in_created_scenario)
    
    description = result['description']
    
    yaml_path = f'/home/hcis-s19/Documents/ChengYu/hcis_scenario_generation/{parent_folder}/{scenario_folder}/{scenario_index}.yaml'
    route = process_yaml_file(yaml_path)  # Use the function to get the route
        
    parameters = write_param(result)  # Should be the same name using in the OpenSCENARIO file
    tag_tree = build_tagTree_from_csv(result)


    # Condition configurations
    """
    valid_conditions = [  # will be valid if trigger this condition, empty means all conditions are valid
        # {
            # all, so is empty
            # "condition": "TargetStartWhenEgoCloseToTheJunction",
            # "condition": "EgoApproachInitWp" 
        # }
    ]

    start_conditions = [  # the start recording conditions
        # {
        #     "condition": "TargetStartWhenEgoCloseToTheJunction"
        # },
        {
            "condition": "EgoApproachInitWp"
        }
    ]
    """

    # Only if these conditions are triggered will the trial be considered valid
    valid_conditions = {
        "conditionLogic": "Or",  # Available options: "And", "Or"
        "conditions": [
            "IS_VALID_Trigger",
        ]
    }
    
    # If these conditions are triggered, the trial will be considered invalid
    invalid_conditions = {
        "conditionLogic": "Or",  # Available options: "And", "Or"
        "conditions": [
            "AV_CONNECTION_TIMEOUT_Trigger",
            "WRONG_START_SPEED_Trigger",
            "EGO_STROLL_Trigger",
        ]
    }
    
    # If these conditions are triggered, the trial will stop right away
    fail_conditions = {
        "conditionLogic": "Or",  # Available options: "And", "Or"
        "conditions": [
            "EGO_TLE_Trigger",
            "EGO_COLLISION_Trigger",
        ]
    }
    
    # If these conditions are triggered, the trial will stop right away
    end_conditions = {
        "conditionLogic": "Or",  # Available options: "And", "Or"
        "conditions": [
            "AV_CONNECTION_TIMEOUT_Trigger",
            "WRONG_START_SPEED_Trigger",
            "EGO_REACHED_END_Trigger",
            "EGO_TLE_Trigger",
            "EGO_COLLISION_Trigger",
            "EGO_STROLL_Trigger",
        ]
    }
    
    # After these events start, the scenario will be recorded
    start_conditions = {
        "conditionLogic": "And",  # Available options: "And", "Or"
        "conditions": [
            "EgoHasMoved"
        ]
    }
    
    conditions = {
        "validConditions": valid_conditions,
        "invalidConditions": invalid_conditions,
        "failConditions": fail_conditions,
        "endConditions": end_conditions,
        "startObservationSamplingConditions": start_conditions
    }


    observation_recording_agents = []

    folder = date.today().strftime("%m%d")
    filename = f"{result['scenario_name']}"
    file_path = f"/home/hcis-s19/Documents/ChengYu/ITRI/xosc/{folder}/{filename}.xosc"

    # exit()
    openScenarioField = upload_openscenario_file(file_path)

    data = create_request_body(
        scenarioId=filename,
        tags=tag_ids_to_be_used_in_created_scenario,
        description=description,
        parameters=parameters,
        openDrive="666c15f9173ee59246206343",  # ID of hct_6.xodr
        openScenario=openScenarioField,
        usedRoute=route,
        tagTree=tag_tree,
        testObjectives=test_objective,
        conditions=conditions,
        observationRecordingAgents=observation_recording_agents,
        egoTargetSpeed=30
    )

    r = ''
    # """
    global base_url
    url = f"{base_url}/scenarios?limit=10000&sort=updatedAt&where[createdBy][equals]=HCIS%20Lab"
    scenarios_doc = get_cache_data(url, headers)['docs']
    all_scenarios = dict((scenario["scenarioId"], scenario) for scenario in scenarios_doc)
    
    if scenario_id in all_scenarios.keys():
        scenario_id_to_update = all_scenarios[scenario_id]["id"]
        print(f"   [SCENARIO] Scenario exists, updating by ID: {scenario_id_to_update}...")
        r = requests.patch(f"{base_url}/scenarios/{scenario_id_to_update}", headers=headers, json=data)
        time.sleep(3)
    else:
        print("   [SCENARIO] Scenario does not exist, creating new...")
        r = requests.post(f"{base_url}/scenarios", headers=headers, json=data)
        time.sleep(3)

    try:
        print(f"   [SCENARIO] {r.json().get('message')}")
        if ((r.status_code == 201 and r.json().get("message") == "Scenario successfully created.") or
           (r.status_code == 200 and r.json().get("message") == "Updated successfully.")):
            # 更新預覽圖和影片
            print("   [SCENARIO] Updating preview schematic and video...")
            update_url = f"{base_url}/updatePreviewSchematicAndVideo/{scenario_id}"
            r = requests.post(
                update_url,
                headers=headers
            )
            print(f"   [SCENARIO] {r.json().get('message')}")
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

# ===========================================================================================
# Main Execution
# ===========================================================================================

if __name__ == '__main__':
    clear_cache_file()
    try:
        argparser = argparse.ArgumentParser()
        argparser.add_argument(
            '-s', '--sc',
            metavar='S',
            default='',
            nargs="+",
            help='Scenario category (default: all)'
        )
        args = argparser.parse_args()


        # === 建立跳過檔案清單 ===
        # 手動指定要跳過的檔案
        manually_skipped_files = [
            '01FL-KEEP_6.xosc', '01FL-KEEP_7.xosc', '01FL-KEEP_8.xosc', 
            '01FL-KEEP_9.xosc', '01FL-KEEP_10.xosc'
        ]
        
        # 載入none-critical scenario清單（從檔案讀取）
        non_critical_scenarios = []
        non_critical_file_path = f'/home/hcis-s19/Documents/ChengYu/hcis_scenario_generation/{RUNTIME_DATA_DIR}/none_critical_scenario_combined_0806.txt'
        with open(non_critical_file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line:
                    scenario_name = line.replace('_metrics.csv', '.xosc')
                    non_critical_scenarios.append(scenario_name)
                    
        # print(none_critical_scenario_combined_0806)
        
        # 載入已成功上傳的情境清單
        already_uploaded_scenarios = []
        success_file_path = f'/home/hcis-s19/Documents/ChengYu/hcis_scenario_generation/{RUNTIME_DATA_DIR}/success_upload_scenario.txt'
        with open(success_file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line:
                    already_uploaded_scenarios.append(line)
        
        # 合併所有要跳過的檔案
        non_critical_scenarios += manually_skipped_files

        scenario_ids = args.sc
        
        if args.sc[0] == 'all' and 0:
            scenario_ids = []
            prefix_dict = {}
            
            # 請修改路徑
            folder = date.today().strftime("%m%d")
            xosc_dir = f"/home/hcis-s19/Documents/ChengYu/ITRI/xosc/{folder}/"
            for file in os.listdir(xosc_dir):
                if file.endswith('.xosc'):
                    if file in non_critical_scenarios:
                        continue

                    prefix = "_".join(file.split("_")[:-1])
                    if prefix not in prefix_dict:
                        prefix_dict[prefix] = []
                    prefix_dict[prefix].append(file)
            
            # Combined scnearios參數排列組合較多, 抽樣上傳, 避免crash
            for prefix, files in prefix_dict.items():
                if '02' in prefix and len(files) > 500:
                    # continue
                    sampled_files = np.random.choice(files, 100, replace=False)
                    scenario_ids.extend(sampled_files)
                else:
                    scenario_ids.extend(files)

            print("Scenarios in queue: ", len(scenario_ids))
            print("Scenarios to upload: ", len(set(scenario_ids) - set(already_uploaded_scenarios)))

            # Save the scenario_ids to a queue file
            queue_file_path = f'{RUNTIME_DATA_DIR}/scenario_queue.txt'
            with open(queue_file_path, 'w') as queue_file:
                for scenario_id in scenario_ids:
                    queue_file.write(f"{scenario_id}\n")

            # 紀錄已上傳成功scenario, server crash需要重傳時, 可直接跳過
            success_upload = 0
            with open(f'{RUNTIME_DATA_DIR}/success_upload_scenario.txt', 'w') as success_file:
                for scenario_id in tqdm(scenario_ids):
                    if scenario_id in already_uploaded_scenarios:
                        print(f'[MAIN] Skipped {scenario_id} - already uploaded')
                        success_upload += 1
                        continue
                    
                    print(f"\n[MAIN] Processing scenario: {scenario_id}")
                    if upload(scenario_id):
                        success_upload += 1
                        success_file.write(f"{scenario_id}\n")
                        print(f"[MAIN] ✓ Successfully processed {scenario_id}")
                    else:
                        print(f"[MAIN] ✗ Failed to upload: {scenario_id}")

            # Check if all scenarios were successfully uploaded
            if success_upload == len(scenario_ids):
                # Clear the queue file
                open(f'{RUNTIME_DATA_DIR}/scenario_queue.txt', 'w').close()
        
        elif args.sc[0] == 'queue':
            print("Upload scenarios from queue list...")
            success_upload = 0
            
            queue_file_path = f'{RUNTIME_DATA_DIR}/scenario_queue.txt'
            with open(queue_file_path, 'r') as queue_file:
                scenario_ids = [line.strip() for line in queue_file.readlines()]
            # scenario_ids.reverse()



            for scenario_id in tqdm(scenario_ids):
            # for scenario_id in ['01FS-ZZ_02SR-ZZ_3']:
                    
                # if scenario_id in non_critical_scenarios:
                #         print('Skipped. None-critical scenario.')
                #         # success_upload += 1
                #         continue
                    
                # if scenario_id in already_uploaded_scenarios:
                #     print('Skipped. Since already uploaded, check success_upload_scenario.txt')
                #     success_upload += 1
                #     continue
                
                # # 只更新zigzag range
                # if 'ZZ' in scenario_id:
                #     print(' ZZ, skipped.')
                #     continue     
                  
                # sample_scenarios = [
                #     '01BL-KEEP_02FS-ZZ_3.xosc', '01BL-KEEP_02SR-ZZ_5.xosc', 
                #     '01FR-ZZ_02FR-CI_2.xosc', '01FL-TL_14.xosc', 
                #     '01BL-TR_02SL-TR_50.xosc', '01BR-KEEP_02SR-ZZ_1.xosc', 
                #     '01FR-CI_02SR-CI_24.xosc', '01FL-ZZ_02FR-CI_13.xosc', 
                #     '01FL-TL_02FR-TL_1121.xosc', '01FL-KEEP_02FR-TL_254.xosc'
                # ]
                # if scenario_id not in sample_scenarios:
                #     continue

                print(f"\n[MAIN] Processing scenario: {scenario_id}")
                if upload(scenario_id):
                    success_upload += 1
                    print(f"[MAIN] ✓ Successfully processed {scenario_id}")
                    # break
                    # success_file.write(f"{scenario_id}\n")
                else:
                    print(f"[MAIN] ✗ Failed to upload: {scenario_id}")
                    
    finally:
        clear_cache_file()
        print(f'\n[MAIN] Upload completed! Successfully processed {success_upload} scenarios.')