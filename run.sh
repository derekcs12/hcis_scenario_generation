# 生成Scenario config files(.yaml), csvs and xoscs
# Generation config files(.yaml & .csv)
python scripts/config_generator_4way.py
python scripts/config_generator_straight.py
python scripts/config_generator_straight_at4way.py

# # Do Config Files Combination (both .yaml & .csv)
python combine_all.py

# Turn .yaml into .xosc
python main.py -c all

# Upload .xosc with csv's paramerter ranges to itri payload
# python scenario_upload.py -s all