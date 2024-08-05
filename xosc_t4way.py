#from scenariogeneration import xodr
import os
from scenariogeneration import xosc, prettyprint
from dicent_utils import *


def generate_4way(Map, Sc, sc_name=None, company='HCISLab'):
    hasSecondAgent = (len(Sc.adv.keys())>1)
    # print("hasSecondAgent",hasSecondAgent);exit()
    ### ParameterDeclarations (document:xosc.utiles)
    egoInit  = xosc.Parameter(name="EgoVehicle",parameter_type="string",value="car_white")
    egoSpeed = xosc.Parameter(name="EgoSpeed",parameter_type="double",value="60")
    egoS     = xosc.Parameter(name="Ego_S",parameter_type="double",value="27")

    agentInit  = xosc.Parameter(name="Agent1Vehicle",parameter_type="string",value="car_red")
    agentSpeed = xosc.Parameter(name="Agent1Speed",parameter_type="double",value="60")
    agentLowSpeed     = xosc.Parameter(name="Agent1LowSpeed",parameter_type="double",value="15")
    agentDynmDuration = xosc.Parameter(name="Agent1DynamicDuration",parameter_type="double",value="3.2")
    agentS     = xosc.Parameter(name="Agent1_S",parameter_type="double",value="20")


    # exit("ESSFSDFASDFSD")
    paraList = [egoInit, egoSpeed, egoS, agentInit, agentSpeed, agentS, agentLowSpeed, agentDynmDuration]
    paramdec = xosc.ParameterDeclarations()
    for i in paraList:
        paramdec.add_parameter(i)

    ### CatalogLocations & RoadNetwork (document:xosc.utiles)
    catalog = xosc.Catalog()
    if company == 'HCISLab':
        catalog.add_catalog("VehicleCatalog", "./Catalogs/Vehicles")
        road = xosc.RoadNetwork(roadfile="hct_6.xodr")

        # ACC controller
        egoControllerProperties = xosc.Properties()
        egoControllerProperties.add_property(name="timeGap", value="1.0")
        egoControllerProperties.add_property(name="mode", value="override")
        egoControllerProperties.add_property(name="setSpeed", value="${$EgoSpeed / 3.6}")
        egoController = xosc.Controller(name="ACCController", properties=egoControllerProperties)


    else: # ITRI
        # CatalogLocations
        catalog.add_catalog("VehicleCatalog", "../Catalogs/Vehicles")
        # catalog.add_catalog("ControllerCatalog", "../Catalogs/Controllers")
        # catalog.add_catalog("ControllerCatalog", "../../../workspace/src/esmini/resource/xosc/Catalogs/Controllers")

        # RoadNetwork
        road = xosc.RoadNetwork(roadfile="../../xodr/itri/hct_6.xodr")

        #construct ego controller - ROS
        egoControllerProperties = xosc.Properties()
        egoControllerProperties.add_property(name="timeGap", value="1.0")
        egoControllerProperties.add_property(name="mode", value="override")
        egoControllerProperties.add_property(name="setSpeed", value="${$EgoSpeed / 3.6}")
        egoController = xosc.Controller(name="ROSController", properties=egoControllerProperties)



    ### Entities (document:xosc.Entities)
    #construct CatalogReference
    egoObject = xosc.CatalogReference(catalogname="VehicleCatalog", entryname="$EgoVehicle") #xosc.utils
    agent1Object = xosc.CatalogReference(catalogname="VehicleCatalog", entryname="$Agent1Vehicle") #xosc.utils
    agent2Object = xosc.CatalogReference(catalogname="VehicleCatalog", entryname="$Agent1Vehicle") #xosc.utils


    # xosc.AssignRoute()



    # create entity
    egoName = "Ego"
    agent1Name = "Target1"
    entities = xosc.Entities()
    entities.add_scenario_object(name = egoName, entityobject = egoObject, controller = egoController)
    entities.add_scenario_object(name = agent1Name, entityobject = agent1Object)

    step_time = xosc.TransitionDynamics(xosc.DynamicsShapes.step, xosc.DynamicsDimension.time, 0)
    # print(Map.zones[Sc.ego.origin]);exit()
    ### Storyboard - Init 初始設定
    # Ego 初始化
    init = xosc.Init()
    egoInitS = Sc.ego.origin_offset-29
    egostart = xosc.TeleportAction(create_LanePosition_from_wp(Map.zones[Sc.ego.origin], s_offset=egoInitS))
    egospeed = xosc.AbsoluteSpeedAction("${$EgoSpeed / 3.6}", step_time)
    egocontl = xosc.ActivateControllerAction(lateral = "true", longitudinal = "true")
    egofinal = xosc.AcquirePositionAction(create_LanePosition_from_wp(Map.zones[Sc.ego.to])) #Ego終點

    # Adv1 初始化
    agent1start = xosc.TeleportAction(create_LanePosition_from_wp(Map.zones[Sc.adv[0].origin], s="$Agent1_S"))
    
    init.add_init_action(egoName, egostart)
    init.add_init_action(egoName, egospeed)
    init.add_init_action(egoName, egocontl)
    init.add_init_action(egoName, egofinal)
    init.add_init_action(agent1Name, agent1start)

    
    ### Storyboard - Event
    ## Adv1 - Event1: Adv Behavior
    # print("EEEEEEEEEEEEEEEEEEEEEEEE",Sc.adv[0].init_speed)
    # exit()
    adv1speed = xosc.AbsoluteSpeedAction(Sc.adv[0].init_speed, step_time)
    adv1contl = xosc.ActivateControllerAction(lateral = "true", longitudinal = "true")
    if Sc.adv[0].traj == None:
        adv1goal  = xosc.AcquirePositionAction(create_LanePosition_from_wp(Map.zones[Sc.adv[0].to]))
    else:
        # route = plan_path(start=Map.zones[Sc.adv[0].origin],
        #                     end=Map.zones[Sc.adv[0].to],
        #                     WAYPOINT_DISTANCE=0.5,
        #                     method="global_planner")
        # print(Map.zones[Sc.adv[0].origin])
        # print(Map.zones[Sc.adv[0].to])
        # print(route);exit()
        # route = Sc.adv[0].traj

        trajectory = xosc.Trajectory('selfDefineTrajectory',False)
        nurbs = xosc.Nurbs(4)
        nurbs.add_control_point(xosc.ControlPoint(create_LanePosition_from_wp(Map.zones[Sc.adv[0].origin], s="$Agent1_S"))) #出發點
        nurbs.add_control_point(xosc.ControlPoint(create_LanePosition_from_wp(Map.zones[Sc.adv[0].origin], s=0))) #與出發點同道之進入路口點，家這個點軌跡比較自然
        nurbs.add_control_point(xosc.ControlPoint(xosc.WorldPosition(Map.topo_center[0], Map.topo_center[1]))) #路口中心
        nurbs.add_control_point(xosc.ControlPoint(create_LanePosition_from_wp(Map.zones[Sc.adv[0].to]))) #目的地
        nurbs.add_knots([0,0,0,0,3,3,3,3])

        trajectory.add_shape(nurbs)

        # Create a FollowTrajectory action
        adv1goal = xosc.FollowTrajectoryAction(trajectory, xosc.FollowingMode.follow)

   
    trigger = create_EntityTrigger_at_egoInitWp(egoName, Map.zones[Sc.ego.origin], s=egoInitS)

    advStartSpeedEvent = xosc.Event("AdvStartSpeedEvent", xosc.Priority.overwrite)
    advStartSpeedEvent.add_action("AdvStartSpeedAction", adv1speed)
    advStartSpeedEvent.add_action("AdvStartSpeedAction", adv1contl)
    advStartSpeedEvent.add_action("AcquirePositionAction", adv1goal)
    advStartSpeedEvent.add_trigger(trigger)


    ## Adv1 - Event2: Speed Behavior
    dynamic_time = create_TransitionDynamics_from_sc(Sc.adv[0])
    adv1EndSpeed = xosc.AbsoluteSpeedAction(Sc.adv[0].end_speed, dynamic_time)
    trigger = create_Trigger_following_previous("AdvStartSpeedEvent", Sc.adv[0].delay)

    advEndSpeedEvent = xosc.Event("AdvEndSpeedEvent", xosc.Priority.parallel)
    advEndSpeedEvent.add_action("AdvEndSpeedEvent", adv1EndSpeed)
    advEndSpeedEvent.add_trigger(trigger)


    ### Storyboard - Story & Maneuver
    adv1Maneuver = xosc.Maneuver("Adv1Maneuver")
    adv1Maneuver.add_event(advStartSpeedEvent)
    adv1Maneuver.add_event(advEndSpeedEvent)



    sb = xosc.StoryBoard(init, create_StopTrigger(egoName))
    sb.add_maneuver(adv1Maneuver, agent1Name)



    sc_name = "_".join(Sc.scate)
    ### Create Scenario
    sce = xosc.Scenario( 
        name="hct_"+sc_name,
        author="HCIS_Chengyu",
        parameters = paramdec,
        entities=entities,
        storyboard=sb,
        roadnetwork=road,
        catalog=catalog,
        osc_minor_version=0
    )

    return sce







#########################################       Discard       ##################################################
"""
init = xosc.Init() #xosc.storyboard
init.add_init_action(egoName, xosc.TeleportAction(xosc.LanePosition(s = "$Ego_S", offset = 0,
                                                                    lane_id = Map.zones[Sc.ego.origin].lane_id, 
                                                                    road_id = Map.zones[Sc.ego.origin].road_id))) #Ego起點
init.add_init_action(egoName, xosc.AbsoluteSpeedAction("${$EgoSpeed / 3.6}", step_time))
init.add_init_action(egoName, xosc.ActivateControllerAction(lateral = "true", longitudinal = "true"))
init.add_init_action(egoName, xosc.AcquirePositionAction(xosc.LanePosition(s = 8, offset = 0, 
                                                                            lane_id = Map.zones[Sc.ego.to].lane_id, 
                                                                            road_id = Map.zones[Sc.ego.to].road_id))) #Ego終點

init.add_init_action(agent1Name, xosc.TeleportAction(xosc.LanePosition(s = "$Target_S", offset = 0,
                                                                        lane_id = Map.zones[Sc.adv[0].origin].lane_id, 
                                                                        road_id = Map.zones[Sc.adv[0].origin].road_id))) #Adv1起點
if hasSecondAgent:
    init.add_init_action(agent2Name, xosc.TeleportAction(xosc.LanePosition(s = "$Target_S", offset = 0,
                                                                            lane_id = Map.zones[Sc.adv[1].origin].lane_id, 
                                                                            road_id = Map.zones[Sc.adv[1].origin].road_id))) #Adv2起點
    

    init.add_init_action(agent2Name, xosc.AbsoluteSpeedAction("${$TargetSpeed / 3.6}", step_time))
    init.add_init_action(agent2Name, xosc.ActivateControllerAction(lateral = "true", longitudinal = "true"))


## Adv1 - Event2: Adv Behavior
adv1move = xosc.Event("moveAcion", xosc.Priority.overwrite)
adv1move.add_action("AcquirePositionActionStart", xosc.AcquirePositionAction(create_LanePosition_from_wp(Map.zones[Sc.adv[0].to])))


# Agent start trigger
entityCondition = xosc.ReachPositionCondition(xosc.LanePosition(s = 0, offset = 0, 
                                                                lane_id = Map.zones[Sc.ego.origin].lane_id, 
                                                                road_id = Map.zones[Sc.ego.origin].road_id), tolerance = 15)
adv1move.add_trigger(xosc.EntityTrigger(name = "EgoEnteringTheJunction", delay = 0,
                                        conditionedge = xosc.ConditionEdge.rising,
                                        entitycondition = entityCondition, triggerentity = egoName, triggeringrule = "any" ))

---
        # xosc.EntityTrigger(
        #     name = "ReachDestinationCondition",
        #     delay = 0,
        #     conditionedge = xosc.ConditionEdge.rising,
        #     entitycondition = xosc.ReachPositionCondition(xosc.LanePosition(s = 20, offset = 0, 
        #                                                                     lane_id = Map.zones[Sc.adv[0].to].lane_id, 
        #                                                                     road_id = Map.zones[Sc.adv[0].to].road_id), tolerance = 10),
        #     triggerentity = agent1Name, triggeringpoint="stop"))

    # stopTrigger = xosc.EntityTrigger(name = "tetetewtewtwe", delay = 0,
    #                                         conditionedge = xosc.ConditionEdge.rising,
    #                                         entitycondition = xosc.RelativeDistanceCondition(value = 5, entity = agentName, rule = "lessThan", dist_type = "cartesianDistance", freespace = "false"),
    #                                         triggerentity = egoName, triggeringrule = "any",triggeringpoint = "stop")
---

"""