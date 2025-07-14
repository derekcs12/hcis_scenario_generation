#!/usr/bin/env python3
"""
整合 scenario_config 和 scenario_config_combined 目錄下所有CSV檔案的腳本
將所有CSV檔案合併成一個總表
"""

import os
import pandas as pd
import glob
from pathlib import Path


def combine_csv_files():
    # 獲取當前腳本所在目錄
    script_dir = Path(__file__).parent
    
    # 定義要掃描的目錄
    target_dirs = [
        script_dir / "scenario_config",
        script_dir / "scenario_config_combined"
    ]
    
    all_dataframes = []
    total_files = 0
    
    print("開始掃描CSV檔案...")
    
    for target_dir in target_dirs:
        if not target_dir.exists():
            print(f"警告: 目錄 {target_dir} 不存在，跳過...")
            continue
            
        print(f"\n正在處理目錄: {target_dir}")
        
        # 遍歷所有子目錄
        for subdir in target_dir.iterdir():
            if subdir.is_dir():
                print(f"  掃描子目錄: {subdir.name}")
                
                # 查找該子目錄下的所有CSV檔案
                csv_files = list(subdir.glob("*.csv"))
                
                if not csv_files:
                    print(f"    子目錄 {subdir.name} 中沒有找到CSV檔案")
                    continue
                
                print(f"    找到 {len(csv_files)} 個CSV檔案")
                
                for csv_file in csv_files:
                    try:
                        # 讀取CSV檔案
                        df = pd.read_csv(csv_file)
                        
                        # 添加來源資訊欄位
                        df['source_directory'] = target_dir.name  # scenario_config 或 scenario_config_combined
                        df['source_subfolder'] = subdir.name      # 子目錄名稱
                        df['source_filename'] = csv_file.name     # CSV檔案名稱
                        df['source_full_path'] = str(csv_file)    # 完整路徑
                        
                        all_dataframes.append(df)
                        total_files += 1
                        
                        # print(f"      ✓ 成功讀取: {csv_file.name} ({len(df)} 行)")
                        
                    except Exception as e:
                        print(f"      ✗ 讀取失敗: {csv_file.name} - 錯誤: {e}")
    
    if not all_dataframes:
        print("\n錯誤: 沒有找到任何可讀取的CSV檔案!")
        return
    
    print(f"\n總共處理了 {total_files} 個CSV檔案")
    print("正在合併所有資料...")
    
    # 合併所有DataFrame
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    
    # 輸出檔案路徑
    output_file = script_dir / "runtime_data/scenario_overview.csv"
    
    # 儲存合併後的CSV檔案
    try:
        combined_df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"\n✓ 成功創建合併檔案: {output_file}")
        print(f"  總行數: {len(combined_df)}")
        print(f"  總欄位數: {len(combined_df.columns)}")
        
        # 顯示統計資訊
        print("\n統計資訊:")
        print(f"  來源目錄分布:")
        source_dir_counts = combined_df['source_directory'].value_counts()
        for dir_name, count in source_dir_counts.items():
            print(f"    {dir_name}: {count} 行")
        
        print(f"\n  子目錄分布 (前10個):")
        subfolder_counts = combined_df['source_subfolder'].value_counts().head(10)
        for folder_name, count in subfolder_counts.items():
            print(f"    {folder_name}: {count} 行")
        
        # 顯示欄位名稱
        print(f"\n  欄位列表:")
        for i, col in enumerate(combined_df.columns, 1):
            print(f"    {i:2d}. {col}")
            
    except Exception as e:
        print(f"\n✗ 儲存檔案失敗: {e}")
        return
    
    print(f"\n完成! 合併檔案已儲存至: {output_file}")


def main():
    print("=" * 60)
    print("CSV檔案整合工具")
    print("=" * 60)
    
    try:
        combine_csv_files()
    except KeyboardInterrupt:
        print("\n\n程式被用戶中斷")
    except Exception as e:
        print(f"\n發生未預期的錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
