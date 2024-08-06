#from scenariogeneration import xodr
import os
from scenariogeneration import xosc, prettyprint
from dicent_utils import *


def generate(config, company='HCISLab'):
    Agents = config['Agents']
    paramdec = xosc.ParameterDeclarations()
    
    ### ParameterDeclarations (document:xosc.utiles)
    egoInit  = xosc.Parameter(name="EgoVehicle",parameter_type="string",value="car_white")
    egoSpeed = xosc.Parameter(name="EgoSpeed",parameter_type="double",value="60")
    egoS     = xosc.Parameter(name="Ego_S",parameter_type="double",value="27")
    paraList = [egoInit, egoSpeed, egoS]

    for i in range(len(Agents)):
        agentBehavior = Agents[i]['Behavior']
        if '~' in Agents[i]['Start']:
            agentInit_S = sum(map(int,Agents[i]['Start'].split(' ')[-1].split('~')))/2  
        else: 
            agentInit_S = int(Agents[i]['Start'].split(' ')[-1])
        agentInit  = xosc.Parameter(name=f"Agent{i}Vehicle",parameter_type="string",value="car_red")
        agentSpeed = xosc.Parameter(name=f"Agent{i}Speed",parameter_type="double",value=str(agentBehavior['Start_speed']))
        agentLowSpeed     = xosc.Parameter(name=f"Agent{i}LowSpeed",parameter_type="double",value=str(agentBehavior['End_speed']))
        agentDynmDuration = xosc.Parameter(name=f"Agent{i}DynamicDuration",parameter_type="double",value=str(agentBehavior['Dynamic_duration']))
        agentS     = xosc.Parameter(name=f"Agent{i}_S",parameter_type="double",value=str(agentInit_S))
        paraList.extend([agentInit, agentSpeed, agentS, agentLowSpeed, agentDynmDuration])

    # paraList = [egoInit, egoSpeed, egoS, agentInit, agentSpeed, agentS, agentLowSpeed, agentDynmDuration]
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

        # RoadNetwork
        road = xosc.RoadNetwork(roadfile="../../xodr/itri/hct_6.xodr")

        #construct ego controller - ROS
        egoControllerProperties = xosc.Properties()
        egoControllerProperties.add_property(name="timeGap", value="1.0")
        egoControllerProperties.add_property(name="mode", value="override")
        egoControllerProperties.add_property(name="setSpeed", value="${$EgoSpeed / 3.6}")
        egoController = xosc.Controller(name="ROSController", properties=egoControllerProperties)



    ### Entities (document:xosc.Entities)
    # construct CatalogReference
    egoObject = xosc.CatalogReference(catalogname="VehicleCatalog", entryname="$EgoVehicle") #xosc.utils
    
    # Create agent object
    agentObjectList = []
    for i in range(len(Agents)):
        agentObject = xosc.CatalogReference(catalogname="VehicleCatalog", entryname=f"$Agent{i}Vehicle")
        agentObjectList.append(agentObject)


    # create entity
    egoName = "Ego"
    entities = xosc.Entities()
    entities.add_scenario_object(name = egoName, entityobject = egoObject, controller = egoController)
    for i in range(len(Agents)):
        entities.add_scenario_object(name = f"Agent{i}", entityobject = agentObjectList[i])

    step_time = xosc.TransitionDynamics(xosc.DynamicsShapes.step, xosc.DynamicsDimension.time, 0)

    ### Storyboard - Init 初始設定
    # Ego 初始化
    init = xosc.Init()
    egoInitS = config['Ego']['Start'].split(' ')[-1]
    egostart = xosc.TeleportAction(create_LanePosition_from_config(config['Map'],config['Ego']['Start']))
    egospeed = xosc.AbsoluteSpeedAction("${$EgoSpeed / 3.6}", step_time)
    egocontl = xosc.ActivateControllerAction(lateral = "true", longitudinal = "true")
    egofinal = xosc.AcquirePositionAction(create_LanePosition_from_config(config['Map'],config['Ego']['End'])) #Ego終點
    init.add_init_action(egoName, egostart)
    init.add_init_action(egoName, egospeed)
    init.add_init_action(egoName, egocontl)
    init.add_init_action(egoName, egofinal)

    # Agents 初始化
    for i in range(len(Agents)):
        agentStart = xosc.TeleportAction(create_LanePosition_from_config(config['Map'],Agents[i]['Start']))
        init.add_init_action(f"Agent{i}", agentStart)
    

    
    sb = xosc.StoryBoard(init, create_StopTrigger(egoName,agent_count=len(Agents),distance=130))
    
    ### Storyboard - Event
    for i in range(len(Agents)):
        agentManeuver = generate_Adv_Maneuver(config,i)
        sb.add_maneuver(agentManeuver, f"Agent{i}")


    ### Create Scenario
    sce = xosc.Scenario( 
        name="hct_"+config['Scenario_name'],
        author="HCIS_YuSheng",
        parameters = paramdec,
        entities=entities,
        storyboard=sb,
        roadnetwork=road,
        catalog=catalog,
        osc_minor_version=0
    )

    return sce

def generate_Adv_Maneuver(config,index):
    ## Event1: Adv Behavior
    Behavior = config['Agents'][index]['Behavior']
    advspeed = xosc.AbsoluteSpeedAction(Behavior['Start_speed'], xosc.TransitionDynamics(xosc.DynamicsShapes.step, xosc.DynamicsDimension.time, 0))
    # advcontl = xosc.ActivateControllerAction(lateral = "true", longitudinal = "true")

    # if Sc.adv[0].traj == None:
    #     adv1goal  = xosc.AcquirePositionAction(create_LanePosition_from_wp(Map.zones[Sc.adv[0].to]))
    # else:
    if True:
        # route = plan_path(start=Map.zones[Sc.adv[0].origin],
        #                     end=Map.zones[Sc.adv[0].to],
        #                     WAYPOINT_DISTANCE=0.5,
        #                     method="global_planner")
        # print(Map.zones[Sc.adv[0].origin])
        # print(Map.zones[Sc.adv[0].to])
        # print(route);exit()
        # route = Sc.adv[0].traj

        trajectory = xosc.Trajectory('selfDefineTrajectory',False)
        road_center = list(map(float,config['Center'].split(' ')))
        nurbs = xosc.Nurbs(4)
        nurbs.add_control_point(xosc.ControlPoint(create_LanePosition_from_config(config['Map'],config['Agents'][index]['Start']))) #出發點
        nurbs.add_control_point(xosc.ControlPoint(create_LanePosition_from_config(config['Map'],config['Agents'][index]['Start'], s = 0))) #與出發點同道之進入路口點，家這個點軌跡比較自然
        nurbs.add_control_point(xosc.ControlPoint(xosc.WorldPosition(road_center[0],road_center[1]),weight = 0.5)) #路口中心
        nurbs.add_control_point(xosc.ControlPoint(create_LanePosition_from_config(config['Map'],config['Agents'][index]['End'],s = 0))) #目的地
        nurbs.add_control_point(xosc.ControlPoint(create_LanePosition_from_config(config['Map'],config['Agents'][index]['End']))) #目的地
        nurbs.add_knots([0,0,0,0,1,1,1,1,1])

        trajectory.add_shape(nurbs)

        # Create a FollowTrajectory action
        advgoal = xosc.FollowTrajectoryAction(trajectory, xosc.FollowingMode.position)

        ## AssignRouteAction
        # route = xosc.Route(f"Adv{index}Route")
        # route.add_waypoint(create_LanePosition_from_config(config['Map'],config['Agents'][index]['Start']),routestrategy=xosc.RouteStrategy.fastest)
        # route.add_waypoint(create_LanePosition_from_config(config['Map'],config['Agents'][index]['Start'],s=0),routestrategy=xosc.RouteStrategy.fastest)
        # route.add_waypoint(create_LanePosition_from_config(config['Map'],config['Agents'][index]['End'],s=0),routestrategy=xosc.RouteStrategy.fastest)
        # route.add_waypoint(create_LanePosition_from_config(config['Map'],config['Agents'][index]['End']),routestrategy=xosc.RouteStrategy.fastest)
        # advgoal = xosc.AssignRouteAction(route)


    if config['Agents'][index]['Trigger']['type'] == 'relative':
        ...
    else: #absolute
        trigger = create_EntityTrigger_at_absolutePos(config['Map'],config['Agents'][index]['Trigger'],'Ego')

        advStartSpeedEvent = xosc.Event(f"Adv{index}StartSpeedEvent", xosc.Priority.overwrite)
        advStartSpeedEvent.add_action(f"Adv{index}StartSpeedAction", advspeed)
        # advStartSpeedEvent.add_action("AdvControlAction", advcontl)
        advStartSpeedEvent.add_action("AcquirePositionAction", advgoal)
        advStartSpeedEvent.add_trigger(trigger)


        ## Adv1 - Event2: Speed Behavior
        advEndSpeed = create_TransitionDynamics_from_config(config['Agents'][index]['Behavior'])
        trigger = create_Trigger_following_previous(f"Adv{index}StartSpeedEvent", 0)

        advEndSpeedEvent = xosc.Event(f"Adv{index}EndSpeedEvent", xosc.Priority.parallel)
        advEndSpeedEvent.add_action(f"Adv{index}EndSpeedEventAction", advEndSpeed)
        advEndSpeedEvent.add_trigger(trigger)


        ### Storyboard - Story & Maneuver
        advManeuver = xosc.Maneuver(f"Adv{index}Maneuver")
        advManeuver.add_event(advStartSpeedEvent)
        advManeuver.add_event(advEndSpeedEvent)
    return advManeuver