import yaml
import os


# Route mappings
route1_mapping = {112: -1, 112: -2, 964: -2, 114: -2, 1099: -1, 63: -2, 913: -1, 84: 1, 385: 1, 4: -1, 156: -1, 682: -1, 167: -1, 270: -1, 86: -1, 1156: -1, 80: 1, 880: 1, 115: -1, 720: -1, 126: -1, 855: -1, 516: -1, 31: -1, 418: -1, 160: -1, 28: -1, 41: -1, 561: -1, 44: 1, 840: 1, 74: 1, 559: 1, 121: 1, 476: 1, 144: -1, 975: -1, 36: -1, 983: -1, 65: -1, 65: -2, 712: -1, 23: -2, 443: -1, 39: -2}
route2_mapping = {112: -2, 112: -3, 964: -3, 114: -3, 1107: -1, 63: -3, 63: -2, 913: -1, 84: 1, 387: 1, 135: -1, 1164: -1, 82: -1, 954: -1, 150: -1, 646: -1, 56: -2, 28: -1, 41: -1, 561: -1, 44: 1, 840: 1, 74: 1, 559: 1, 121: 2, 478: 1, 144: -2, 974: -1, 36: -2, 986: -1, 65: -2, 712: -1, 23: -1, 439: -1, 39: -1}

def get_route(road_id, lane_id):
    if (road_id, lane_id) in route1_mapping.items():
        return "Route1"
    elif (road_id, lane_id) in route2_mapping.items():
        return "Route2"
    else:
        return "noRoute"

def assign_route(ego_data, map_data):
    start_road_id = map_data[ego_data['Start_pos'][0]]
    start_lane_id = ego_data['Start_pos'][1]
    end_road_id = map_data[ego_data['End_pos'][0]]
    end_lane_id = ego_data['End_pos'][1]

    start_route = get_route(start_road_id, start_lane_id)
    end_route = get_route(end_road_id, end_lane_id)

    if start_route == "Route2" and end_route == "Route2":
        return "678bcecc26076f8d8be39e95"
    elif start_route == "Route1" and end_route == "Route1":
        return "66e2bb985ac155b0acf389a4"
    else: #default
        return "666c15f9173ee59246206343"

def process_yaml_file(filepath):
    with open(filepath, 'r') as file:
        yaml_data = yaml.safe_load(file)
    
    # Load ego data and map data from YAML
    ego_data = yaml_data['Ego']
    map_data = yaml_data['Map']
    
    # Assign route
    return assign_route(ego_data, map_data)

if __name__ == "__main__":
    # Directory containing YAML files
    scenario_config_dir = '/home/hcis-s19/Documents/ChengYu/hcis_scenario_generation/scenario_config/'

    # Process each YAML file in the directory
    for folder in os.listdir(scenario_config_dir):
        for filename in os.listdir(os.path.join(scenario_config_dir, folder)):
            if filename.endswith('.yaml'):
                filepath = os.path.join(scenario_config_dir, folder, filename)
                assigned_route = process_yaml_file(filepath)
                if assigned_route == 'noRoute':
                    print(f"File: {filename}, Assigned Route: {assigned_route}")