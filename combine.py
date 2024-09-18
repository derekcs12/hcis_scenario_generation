import glob
import os
import yaml
import csv
import argparse

def combine_scenario_name(name1, name2):
    actors_info = []
    # combine actors info
    for info in name1.split('_'):
        actors_info.append(info[2:])
    for info in name2.split('_'):
        actors_info.append(info[2:])
    actors_info = [f'{index:02}{info}' for index,info in enumerate(actors_info, start=1)]
    combined_scenario_name = '_'.join(actors_info)
    print('combined scenario name:',combined_scenario_name)
    print('total actors:',len(actors_info))
    return combined_scenario_name



def combine_yaml(yaml1, yaml2):
    # load yaml files
    yaml1 = yaml.load(open(yaml1), Loader=yaml.FullLoader)
    yaml2 = yaml.load(open(yaml2), Loader=yaml.FullLoader)

    # combine scenario name
    combined_scenario_name = combine_scenario_name(yaml1['Scenario_name'], yaml2['Scenario_name'])

    # check if ego vehicle is the same
    if(yaml1['Ego'] != yaml2['Ego']):
        print('ego vehicles are different')
        return None, None
    
    # check if map is the same
    if(yaml1['Map'] != yaml2['Map']):
        print('maps are different')
        return None, None
    
    # combine actors
    actors1 = yaml1['Actors']
    actors2 = yaml2['Actors']
    agents1 = list(actors1['Agents']) if 'Agents' in actors1 else []
    agents2 = list(actors2['Agents']) if 'Agents' in actors2 else []
    pedestrians1 = list(actors1['Pedestrians']) if 'Pedestrians' in actors1 else []
    pedestrians2 = list(actors2['Pedestrians']) if 'Pedestrians' in actors2 else []

    # combine 2 list
    combined_agents = agents1 + agents2
    combined_pedestrians = pedestrians1 + pedestrians2

    # reconstruct yaml
    combined_yaml = {
        'Scenario_name': combined_scenario_name,
        'Ego': yaml1['Ego'],
        'Map': yaml1['Map'],
        'Actors': {
            'Agents': combined_agents,
            'Pedestrians': combined_pedestrians
        }
    }
    return combined_yaml, combined_scenario_name


def combine_csv(csv1, csv2):
    with open(csv1, 'r') as file:
        reader = csv.reader(file)
        data1 = list(reader)
    with open(csv2, 'r') as file:
        reader = csv.reader(file)
        data2 = list(reader)
    # get agent count
    agent_count = int(data1[0][-1].split('_')[0][5:])
    for index, col in enumerate(data2[0]):
        if 'agent' in col:
            current_agent_count = int(col.split('_')[0][5:])
            data2[0][index] = f'agent{current_agent_count+agent_count}_' + '_'.join(col.split('_')[1:])
            # print(data2[0][index])

    # combine first row
    combined_csv = data1
    combined_csv[0] += data2[0][10:] # skip the first 10 common columns
    combined_csv[1] += data2[1][10:]
    # print('combined csv:',combined_csv[0])
    # exit()
    
    return combined_csv

if __name__ == '__main__':
    # parser = argparse.ArgumentParser()
    # # directory 1
    # parser.add_argument('s1', type=str,default='scenario_config/01FL-CI/1.yaml',required=False)
    # # directory 2
    # parser.add_argument('s2', type=str,default='scenario_config/01FL-CI/2.yaml',required=False)

    # args = parser.parse_args()

    # yaml1 = args.s1 + '/data.yaml'
    # yaml2 = args.s2 + '/data.yaml'
    # csv1 = args.s1 + '/data.csv'
    # csv2 = args.s2 + '/data.csv'

    yaml1 = 'scenario_config/01FL-CI/1.yaml'
    yaml2 = 'scenario_config/01SL-CI/2.yaml'
    combined_yaml, folder_name = combine_yaml(yaml1, yaml2)

    csv1 = 'scenario_config/01FL-CI/1.csv'
    csv2 = 'scenario_config/01SL-CI/2.csv'
    combined_csv = combine_csv(csv1, csv2)

    # get the current scenario number in the folder
    save_folder = f'scenario_config/{folder_name}/'
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    scenario_number = len(glob.glob(os.path.join(save_folder, '*.yaml'), recursive=True))+1
            
    # save the combined data
    save_path = f'{save_folder}{scenario_number}'
    print('saving to:',save_path)
    with open(f'{save_path}.yaml', 'w') as file:
        documents = yaml.dump(combined_yaml, file)

    with open(f'{save_path}.csv', 'w') as file:
        writer = csv.writer(file)
        writer.writerows(combined_csv)