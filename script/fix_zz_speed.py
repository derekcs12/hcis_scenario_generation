import os
import pandas as pd

def fix_zz_speed(input_csv):
    df = pd.read_csv(input_csv)

    for index, row in df.iterrows():
        scenario_name = row.get('scenario_name', '')
        if 'ZZ' in scenario_name:
            # 偵測 ZZ 所屬 agent：如 Agent2
            parts = scenario_name.split('_')
            zz_part = [p for p in parts if 'ZZ' in p]
            if not zz_part:
                print(f"[跳過] {input_csv} 的 {scenario_name} 沒有 ZZ 部分")
                continue
            
            has_fixed = False
            for part in parts:
                if 'ZZ' not in part:
                    continue
                if '01' in part:
                    agent_number = 1
                if '02' in part:
                    agent_number = 2
                
                agent_col = f'Agent{int(agent_number)}_1_SA_EndSpeed'
                if agent_col in df.columns:
                    speed_range = str(row[agent_col])
                    if '~' in speed_range:
                        try:
                            min_speed, max_speed = map(float, speed_range.split('~'))
                            if min_speed < 20.0:
                                print(f"[修正] {input_csv} 的 {agent_col} 值為 {speed_range}，將其設置為 20.0~20.0")
                                df.at[index, agent_col] = '20.0~20.0'
                                has_fixed = True

                            else:
                                print(f"[跳過] {input_csv} 的 {agent_col} 值為 {speed_range}，不符合條件")
                                continue
                            
                        except ValueError:
                            # 若格式錯誤，跳過
                            continue
            if has_fixed:
                df.to_csv(input_csv, index=False)
                print(f'處理完成，結果儲存至 {input_csv}')
        else:
            print(f"[跳過] {input_csv} 的 {scenario_name} 沒有 Agent 部分")
    # from pprint import pprint
    # pprint(df.to_dict(orient='records'))
    # exit()


def process_xosc_list(zz_xosc_list, base_csv_dir_combined, base_csv_dir_single):
    for xosc_path in zz_xosc_list:
        xosc_name = os.path.splitext(os.path.basename(xosc_path))[0]
        parts = xosc_name.split('_')

        if len(parts) >= 2:
            folder_name = '_'.join(parts[:-1])
            csv_file = f"{parts[-1]}.csv"

            is_combined = '02' in xosc_name
            csv_base = base_csv_dir_combined if is_combined else base_csv_dir_single
            csv_path = os.path.join(csv_base, folder_name, csv_file)
            # if is_combined:
            #     continue

            fix_zz_speed(csv_path)
        else:
            print(f"[跳過] 無法解析 xosc 名稱: {xosc_name}")

def find_zz_xosc_files(folder_path):
    zz_files = []
    
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.xosc') and 'ZZ' in file:
                full_path = os.path.join(root, file)
                zz_files.append(full_path)
    
    return zz_files


folder = "/home/hcis-s19/Documents/ChengYu/ITRI/xosc/0117/"
zz_xosc_list = find_zz_xosc_files(folder)

# # 印出結果
# for file in zz_xosc_list:
#     print(file)
# zz_xosc_list = ['/home/hcis-s19/Documents/ChengYu/ITRI/xosc/0117/01FS-ZZ_02SR-ZZ_3.xosc']

process_xosc_list(
    zz_xosc_list,
    base_csv_dir_combined="/home/hcis-s19/Documents/ChengYu/hcis_scenario_generation/scenario_config_combined/",
    base_csv_dir_single="/home/hcis-s19/Documents/ChengYu/hcis_scenario_generation/scenario_config/"
)