# ./utils 的共用變數和函式
from scenariogeneration import xosc
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config



condition_map = {
    "ParameterCondition": xosc.ParameterCondition,
    "VariableCondition": xosc.VariableCondition
}

set_flag_action = {
    "ParameterSetAction": xosc.ParameterSetAction,
    "VariableSetAction": xosc.VariableSetAction
}

agent_type_map = {
    "car_white": "car_white",
    "car_blue": "car_blue",
    "car_yellow": "car_yellow",
    "car_red": "car_red",
    "bus_blue": "bus_blue",
    "scooter" : "scooter",
    "pedestrian_adult": "pedestrian_adult",
    "bicycle" : "bicycle"
}

DEFAULT_AGENT_CONTROLLER = "ACCController"

agent_controller = {
    "car_white": "ExternalControl",      # ego
    # "car_red": "DummyControl",         # car-adv
    # "car_blue": "ACCController",       # car-replayer
    # # "car_yellow": "AutonomousControl",
    # "bus_blue": "ACCController",       # bus-replayer&adv
    # "truck_yellow": "ACCController",   # truck-replayer
    # "van_red": "DummyControl",         # truck-adv
    # "scooter": "ACCController",        # motorbike-replayer
    # "motorbike": "DummyControl",       # motorbike-adv
    # "bicycle": "ACCController",        # bike-replayer&adv
    # "pedestrian_adult": "DummyControl",   # ped-adv
    # "pedestrian_adult2": "DummyControl",  # ped-replayer
}

if config.DEBUG:
    agent_controller = {
        "car_white": "ACCController",      # ego
    }





if config.OPENSCENARIO_VERSION < 1.1:
    # scenario_runner 1.0 不支援 VariableCondition，暫時先用 condition_map 來切換對應 conditionType 和對應的類別
    condition_map = {
        "ParameterCondition": xosc.ParameterCondition,
        "VariableCondition": xosc.VariableCondition
    }

    set_flag_action = {
        "ParameterSetAction": xosc.ParameterSetAction,
        "VariableSetAction": xosc.VariableSetAction
    }

if config.SIMULATION_FOR == "CARLA":
    agent_type_map = {
        "car_white": "vehicle.tesla.model3", #ego
        "car_red": "vehicle.mercedes.coupe_2020", #car-adv
        "car_blue": "vehicle.lincoln.mkz_2017", #car-replayer
        # "car_yellow": "vehicle.volkswagen.t2", #car-adv?
        "bus_blue": "vehicle.mitsubishi.fusorosa", #bus-replpayer&adv
        "truck_yellow": "vehicle.carlamotors.carlacola", #truck-replayer
        "van_red": "vehicle.volkswagen.t2_2021", #truck-adv
        "scooter" : "vehicle.vespa.zx125", #motobike-replayer
        "motorbike" : "vehicle.kawasaki.ninja", #motobike-adv
        "bicycle" : "vehicle.gazelle.omafiets", #bike-replayer&adv
        "pedestrian_adult": "Pedestrian1", #ped-adv
        "pedestrian_adult2": "Pedestrian1", #ped-replayer
    }

