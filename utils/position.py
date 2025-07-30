import numpy as np
from scenariogeneration import xosc

from config import RELATIVE_TRIGGER_POSITIONS
from utils.trigger import * 

def create_LanePosition_from_config(Map, position, orientation=False, s=None, offset=0):
    if s == None:
        # index, lane_id , s = map(int,position.split(' '))
        index, lane_id, s, offset, orientation = position
    else:
        # index, lane_id , _ = map(int,position.split(' '))
        index, lane_id, _, offset, orientation = position

    orientation = True if orientation == -1 else False
    # print("index, lane_id , s", index, lane_id , s)
    road = int(Map[index]) # if index < 4 else index #derek: SinD地圖太亂，traj直接給road比較快
    return xosc.LanePosition(
        s=s,
        offset=offset*np.sign(lane_id),
        lane_id=lane_id,
        road_id=road,
        orientation=xosc.Orientation(
            h=3.14159, reference='relative') if orientation else xosc.Orientation()
    )


def get_entity_position(entityName):
    return xosc.RelativeLanePosition(lane_id=0, entity=entityName, dsLane=0)


# =======================
# Used for config_generator_*.py
# =======================

def set_agentpos_relative_to_egopos(egoPos, road_index=None, relative_lane=0, s_offset=0, lane_offset=0, orientation=1):
    agentPos = egoPos.copy()
    agentPos[0] = road_index if road_index != None else agentPos[0]
    agentPos[1] += relative_lane * int(np.sign(agentPos[1]))
    agentPos[2] += s_offset * -int(np.sign(agentPos[1]))
    agentPos[3] += lane_offset
    agentPos[4] = orientation
    # list(map(add, config['Ego']['Start_pos'], [0,0,20,0,0]))

    return agentPos


def set_agentStart_from_relative_triggerAt(egoTriggerAt, relative_pos):
    # + RELATIVE_TRIGGER_POSITIONS[relative_pos][2]
    road_index = egoTriggerAt[0]
    relative_lane = RELATIVE_TRIGGER_POSITIONS[relative_pos][1]
    s_offset = RELATIVE_TRIGGER_POSITIONS[relative_pos][3]
    lane_offset = egoTriggerAt[3] + RELATIVE_TRIGGER_POSITIONS[relative_pos][4]

    return set_agentpos_relative_to_egopos(egoTriggerAt, road_index=road_index, relative_lane=relative_lane, s_offset=s_offset, lane_offset=lane_offset)


def set_trigger_dict_from_absolute_pos(lane, road, s, offset, triggertype='absolute'):
    position_vals = [triggertype, lane, road, s, offset]
    trigger_dict = dict.fromkeys(['type', 'lane', 'road', 's', 'offset'], '')
    trigger_dict.update(zip(trigger_dict, position_vals))

    return trigger_dict
