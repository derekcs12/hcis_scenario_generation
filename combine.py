import glob
import os
import yaml
import csv
import argparse

def combine_scenario_name(name1, name2):
    # name1 = name1.split('_')[0]
    # name2 = name2.split('_')[0]
    actors_info = []
    # combine actors info
    for info in name1.split('_'):
        actors_info.append(info[2:])
    for info in name2.split('_'):
        actors_info.append(info[2:])
    actors_info = [f'{index:02}{info}' for index,info in enumerate(actors_info, start=1)]
    combined_scenario_name = '_'.join(actors_info)
    
    return combined_scenario_name


def combine_yaml(yaml1, yaml2,combined_scenario_name, mode='agent'):
    # load yaml files
    yaml1 = yaml.load(open(yaml1), Loader=yaml.FullLoader)
    yaml2 = yaml.load(open(yaml2), Loader=yaml.FullLoader)

    msg = ''
    # check if ego vehicle is the same
    if(yaml1['Ego'] != yaml2['Ego']):
        # print('ego vehicles are different')
        msg = 'Ego vehicles are different'
        return None, msg
    
    # check if map is the same
    if(yaml1['Map'] != yaml2['Map']):
        # print('maps are different')
        msg = 'Maps are different'
        return None, msg
    
    # combine actors
    actors1 = yaml1['Actors']
    actors2 = yaml2['Actors']
    agents1 = list(actors1['Agents']) if 'Agents' in actors1 else []
    agents2 = list(actors2['Agents']) if 'Agents' in actors2 else []
    pedestrians1 = list(actors1['Pedestrians']) if 'Pedestrians' in actors1 else []
    pedestrians2 = list(actors2['Pedestrians']) if 'Pedestrians' in actors2 else []
    if mode == 'agent':
        # combine 2 list
        combined_agents = agents1 + agents2
        combined_pedestrians = pedestrians1 + pedestrians2
    elif mode == 'act':
        acts1 = agents1[0]['Acts']
        acts2 = agents2[0]['Acts']
        combine_acts = acts1 + acts2
        agents1[0]['Acts'] = combine_acts
        combined_agents = agents1
        combined_pedestrians = pedestrians1

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
    return combined_yaml, msg

def combine_csv(csv1, csv2, combined_scenario_name, mode='agent'):
    with open(csv1, 'r') as file:
        reader = csv.reader(file)
        data1 = list(reader)
    with open(csv2, 'r') as file:
        reader = csv.reader(file)
        data2 = list(reader)
        
    # strip all elements in the first row
    data1[0] = [col.strip() for col in data1[0]]
    data2[0] = [col.strip() for col in data2[0]]
    
    # get agent count
    agent_count = int(data1[0][-1].split('_')[0][5:])
    for index, col in enumerate(data2[0]):
        if 'Agent' in col:
            current_agent_count = int(col.split('_')[0][5:])
            data2[0][index] = f'Agent{current_agent_count+agent_count}_' + '_'.join(col.split('_')[1:])

    # combine first row
    combined_csv = data1
    
    # new scenario id
    combined_csv[1][data1[0].index('scenario_id')] = combined_scenario_name.split('_')[-1]

    # combine scenario name
    combined_csv[1][data1[0].index('scenario_name')] = combined_scenario_name

    # combine description
    combined_csv[1][data1[0].index('description')] = data1[1][data1[0].index('description')] + '; ' + data2[1][data2[0].index('description')]

    # combine cetran_number
    # combined_csv[1][data1[0].index('cetran_number')] = data1[1][data1[0].index('cetran_number')] + '; ' + data2[1][data2[0].index('cetran_number')]

    combined_csv[0] += data2[0][10:] # skip the first 10 common columns
    combined_csv[1] += data2[1][10:]
    
    return combined_csv

def save_csv(content, save_path):
    with open(save_path, 'w') as file:
        writer = csv.writer(file)
        writer.writerows(content)

def save_yaml(content, save_path):
    with open(save_path, 'w') as file:
        documents = yaml.dump(content, file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # directory 1
    parser.add_argument('--s1', type=str,default='scenario_config/01FL-CI/1')
    # directory 2
    parser.add_argument('--s2', type=str,default='scenario_config/01FL-CI/2')
    parser.add_argument('--mode', type=str,default='agent')
    args = parser.parse_args()

    sc1_name = args.s1.split('/')[-2]
    sc2_name = args.s2.split('/')[-2]
    combined_scenario_name = combine_scenario_name(sc1_name, sc2_name)

    # get the current scenario number in the folder
    save_folder = f'scenario_config/{combined_scenario_name}'
    
    scenario_number = len(glob.glob(os.path.join(save_folder, '*.yaml'), recursive=True))+1
    combined_scenario_name = f'{combined_scenario_name}_{scenario_number}'
    
    yaml1 = args.s1 + '.yaml'
    yaml2 = args.s2 + '.yaml'
    combined_yaml, msg= combine_yaml(yaml1, yaml2, combined_scenario_name, mode=args.mode)

    if combined_yaml is None:
        print(msg)
        exit()

    csv1 = args.s1 + '.csv'
    csv2 = args.s2 + '.csv'
    combined_csv = combine_csv(csv1, csv2, combined_scenario_name, mode=args.mode)

    # save the combined data
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    save_path = f'{save_folder}/{scenario_number}'
    print('saving to:',save_path)

    save_yaml(combined_yaml, f'{save_path}.yaml')

    save_csv(combined_csv, f'{save_path}.csv')