# 生成Scenario config files(.yaml), csvs and xoscs
# Generation config files(.yaml & .csv)
python scripts/config_generator_4way.py
python scripts/config_generator_straight.py
python scripts/config_generator_straight_at4way.py

# # Do Config Files Combination (both .yaml & .csv)
python combine_all.py

# Create Scenario Overview list
python scripts/combine_csv_files.py

# Turn .yaml into .xosc
python main.py -b config/base/hcis_no_runup.yaml -c all
# python main.py -b config/base/itri_no_runup.yaml -c all
# python main.py -b config/base/hcis_no_runup.yaml -c all --esmini-path /home/hcis-s19/Documents/ChengYu/esmini

# Upload .xosc with csv's paramerter ranges to itri payload
# python scenario_upload.py -s all