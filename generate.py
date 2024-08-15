#from scenariogeneration import xodr
import os
from scenariogeneration import xosc, prettyprint
from dicent_utils import *

def generate(config, company='HCISLab'):

    paramdec = parameter_Declaration(config)

    ### CatalogLocations & RoadNetwork (document:xosc.utiles)
    catalog = xosc.Catalog()
    if company == 'HCISLab':
        catalog.add_catalog("VehicleCatalog", "./Catalogs/Vehicles")
        road = xosc.RoadNetwork(roadfile="hct_6.xodr")

        # ACC controller
        egoControllerProperties = xosc.Properties()
        egoControllerProperties.add_property(name="timeGap", value="1.0")
        egoControllerProperties.add_property(name="mode", value="override")
        egoControllerProperties.add_property(name="setSpeed", value="${$Ego_Speed / 3.6}")
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
        egoControllerProperties.add_property(name="setSpeed", value="${$Ego_Speed / 3.6}")
        egoController = xosc.Controller(name="ROSController", properties=egoControllerProperties)



    ### Entities (document:xosc.Entities)
    entities = create_Entity(egoController, len(config['Agents']))

    step_time = xosc.TransitionDynamics(xosc.DynamicsShapes.step, xosc.DynamicsDimension.time, 0)

    ### Storyboard - Init 初始設定
    # Ego 初始化
    init = xosc.Init()
    # egoInitS = config['Ego']['Start_pos'][-1]
    egostart = xosc.TeleportAction(create_LanePosition_from_config(config['Map'],config['Ego']['Start_pos']))
    egospeed = xosc.AbsoluteSpeedAction("${$Ego_Speed / 3.6}", step_time)
    egocontl = xosc.ActivateControllerAction(lateral = "true", longitudinal = "true")
    egofinal = xosc.AcquirePositionAction(create_LanePosition_from_config(config['Map'],config['Ego']['End_pos'])) #Ego終點
    init.add_init_action('Ego', egostart)
    init.add_init_action('Ego', egospeed)
    init.add_init_action('Ego', egocontl)
    init.add_init_action('Ego', egofinal)

    # Agents 初始化
    for agentIndex, agent in enumerate(config['Agents'], start=1):
        agentStart = xosc.TeleportAction(create_LanePosition_from_config(config['Map'],agent['Start_pos'],s=f"$Agent{agentIndex}_S"))
        init.add_init_action(f"Agent{agentIndex}", agentStart)
    

    
    
    # sb = xosc.StoryBoard(init, create_StopTrigger('Ego',agent_count=len(config['Agents']),distance=130))

    ### Storyboard - Event
    allEvent = []
    allManeuver = []
    for agentIndex, agent in enumerate(config['Agents'],start=1):
        agentManeuver, previousEventNames = generate_Adv_Maneuver(agentIndex, agent, config['Map'])
        allEvent.extend(previousEventNames)
        allManeuver.append(agentManeuver)
        # sb.add_maneuver(agentManeuver, f"Agent{agentIndex}")
        
    sb = xosc.StoryBoard(init, create_StopTrigger2('Ego',distance=500,allEventName=allEvent))
    for i in allManeuver:
        sb.add_maneuver(i, f"Agent{allManeuver.index(i)+1}")

    ### Create Scenario
    sce = xosc.Scenario( 
        name="hct_"+config['Scenario_name'],
        author="HCIS_ChengYuSheng",
        parameters = paramdec,
        entities=entities,
        storyboard=sb,
        roadnetwork=road,
        catalog=catalog,
        osc_minor_version=0
    )

    return sce

def parameter_Declaration(config):
    paramdec = xosc.ParameterDeclarations()

    ### ParameterDeclarations (document:xosc.utiles)
    egoInit  = xosc.Parameter(name="Ego_Vehicle",parameter_type="string",value="car_white")
    egoSpeed = xosc.Parameter(name="Ego_Speed",parameter_type="double",value=config['Ego']['Start_speed'])
    egoS     = xosc.Parameter(name="Ego_S",parameter_type="double",value=config['Ego']['Start_pos'][-1])
    paraList = [egoInit, egoSpeed, egoS]

    Agents = config['Agents']
    for agentIndex, agent in enumerate(Agents, start=1):

        # agent's Init parameter
        agentVehicle  = xosc.Parameter(name=f"Agent{agentIndex}_Vehicle",parameter_type="string",value="car_red")
        agentInitSpeed = xosc.Parameter(name=f"Agent{agentIndex}_Speed",parameter_type="double",value=str(agent['Start_speed']))
        agentInitS     = xosc.Parameter(name=f"Agent{agentIndex}_S",parameter_type="double",value=str(agent['Start_pos'][-1]))
        paraList.extend([agentVehicle, agentInitSpeed, agentInitS])

        # agent's Event parameter
        for actIndex, act in enumerate(agent['Acts'], start=1):
            if act['Type'] == 'zigzag':
                for eventIndex, event in enumerate(act['Events'], start=1):
                    if event['Type'] == 'offset':
                        delay = xosc.Parameter(name=f"Agent{agentIndex}_{actIndex}_Deley",parameter_type="double",value=str(event['Dynamic_delay']))
                        offset = xosc.Parameter(name=f"Agent{agentIndex}_{actIndex}_Offset",parameter_type="double",value=str(event['Dynamic_shape']))
                        period = xosc.Parameter(name=f"Agent{agentIndex}_{actIndex}_Period",parameter_type="double",value=str(event['Dynamic_duration']))
                        times = xosc.Parameter(name=f"Agent{agentIndex}_{actIndex}_Times",parameter_type="double",value=str(event['End']))
                        paraList.extend([delay, offset, period, times])
                    if event['Type'] == 'speed':
                        dynamicDelay = xosc.Parameter(name=f"Agent{agentIndex}_{actIndex}_DynamicDelay",parameter_type="double",value=str(event['Dynamic_delay']))
                        dynamicDuration = xosc.Parameter(name=f"Agent{agentIndex}_{actIndex}_DynamicDuration",parameter_type="double",value=str(event['Dynamic_duration']))
                        dynamicShape = xosc.Parameter(name=f"Agent{agentIndex}_{actIndex}_DynamicShape",parameter_type="double",value=str(event['Dynamic_shape']))
                        endSpeed = xosc.Parameter(name=f"Agent{agentIndex}_{actIndex}_EndSpeed",parameter_type="double",value=str(event['End']))
                        paraList.extend([dynamicDelay, dynamicShape, dynamicDuration, endSpeed])
            else:
                for eventIndex, event in enumerate(act['Events'], start=1):
                    if event['Type'] == 'speed':
                        endSpeed = xosc.Parameter(name=f"Agent{agentIndex}_{actIndex}_{eventIndex}_EndSpeed",parameter_type="double",value=str(event['End']))
                        paraList.append(endSpeed)
                    dynamicDelay = xosc.Parameter(name=f"Agent{agentIndex}_{actIndex}_{eventIndex}_DynamicDelay",parameter_type="double",value=str(event['Dynamic_delay']))
                    dynamicDuration = xosc.Parameter(name=f"Agent{agentIndex}_{actIndex}_{eventIndex}_DynamicDuration",parameter_type="double",value=str(event['Dynamic_duration']))
                    dynamicShape = xosc.Parameter(name=f"Agent{agentIndex}_{actIndex}_{eventIndex}_DynamicShape",parameter_type="string",value=event['Dynamic_shape'])
                    paraList.extend([dynamicDelay, dynamicDuration, dynamicShape])

    for i in paraList:
        paramdec.add_parameter(i)
        # print(i.name, i.value)
    
    return paramdec


def create_Catalog_and_RoadNetwork():
    ...


def create_Entity(egoController, agentCount):
    # construct CatalogReference
    egoObject = xosc.CatalogReference(catalogname="VehicleCatalog", entryname="$Ego_Vehicle") #xosc.utils
    
    # Create agent object
    agentObjectList = []
    for i in range(agentCount):
        agentObject = xosc.CatalogReference(catalogname="VehicleCatalog", entryname=f"$Agent{i+1}_Vehicle")
        agentObjectList.append(agentObject)


    # create entity
    entities = xosc.Entities()
    egoName = "Ego"
    entities.add_scenario_object(name = egoName, entityobject = egoObject, controller = egoController)
    for i in range(agentCount):
        entities.add_scenario_object(name = f"Agent{i+1}", entityobject = agentObjectList[i])

    return entities


def generate_Adv_Maneuver(agentIndex, agent, Map):
    advManeuver = xosc.Maneuver(f"Adv{agentIndex}_Maneuver")
    agentStartEvent = generate_Agent_Start_Event(agentIndex, agent, Map)
    advManeuver.add_event(agentStartEvent)
    previousEventName = [agentStartEvent.name]
    currentPosition = agent['Start_pos']


    for actIndex, act in enumerate(agent['Acts'], start=1):
        currentEventName = []
        if act['Type'] == 'zigzag':
            ...
        else:
            for eventIndex, event in enumerate(act['Events'], start=1):
                if event['Type'] == 'speed':
                    currentEvent = generate_Speed_Event(agentIndex, actIndex, eventIndex, event, previousEventName)
                elif event['Type'] == 'offset':
                    currentEvent = generate_Offset_Event(agentIndex, actIndex, eventIndex)
                elif event['Type'] == 'cut':
                    currentEvent, currentPosition = generate_Cut_Event(agentIndex, actIndex, eventIndex, event, previousEventName, currentPosition)
                elif event['Type'] == 'position':
                    currentEvent , currentPosition = generate_Position_Event(agentIndex, actIndex, event, Map, previousEventName ,currentPosition)
                else:
                    print('Event Type Error')
                    break
                # previousEventName = currentEvent.name
                currentEventName.append(currentEvent.name)
                advManeuver.add_event(currentEvent)
            previousEventName = currentEventName


    return advManeuver, previousEventName





    ## Event1: Adv Behavior
    Behavior = config['Agents'][index]['Behavior']
    advspeed = xosc.AbsoluteSpeedAction(f'${{$Agent{index}Speed / 3.6}}', xosc.TransitionDynamics(xosc.DynamicsShapes.step, xosc.DynamicsDimension.time, 0))
    # advcontl = xosc.ActivateControllerAction(lateral = "true", longitudinal = "true")

    if Behavior['Catagory'] == 'cut_in':
        dynamic_shape = getattr(xosc.DynamicsShapes, Behavior['Dynamic_shape'])
        transition_dynamics = xosc.TransitionDynamics(dynamic_shape, xosc.DynamicsDimension.time, f"$Agent{index}DynamicDuration")
        advgoal = xosc.AbsoluteLaneChangeAction(int(config['Agents'][index]['End'].split(' ')[1]),transition_dynamics)
    else:
        if Behavior['Use_route'] == True:

            trajectory = xosc.Trajectory('selfDefineTrajectory',False)
            road_center = list(map(float,config['Center'].split(' ')))
            nurbs = xosc.Nurbs(4)
            nurbs.add_control_point(xosc.ControlPoint(create_LanePosition_from_config(config['Map'],config['Agents'][index]['Start']))) #出發點
            nurbs.add_control_point(xosc.ControlPoint(create_LanePosition_from_config(config['Map'],config['Agents'][index]['Start'], s = 0))) #與出發點同道之進入路口點，家這個點軌跡比較自然
            nurbs.add_control_point(xosc.ControlPoint(xosc.WorldPosition(road_center[0],road_center[1]),weight = 0.5)) #路口中心
            nurbs.add_control_point(xosc.ControlPoint(create_LanePosition_from_config(config['Map'],config['Agents'][index]['End'],s = 0))) #目的地
            nurbs.add_control_point(xosc.ControlPoint(create_LanePosition_from_config(config['Map'],config['Agents'][index]['End']))) #目的地
            nurbs.add_knots([0,0,0,0,1,2,2,2,2])

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
        else:
            advgoal = xosc.AcquirePositionAction(create_LanePosition_from_config(config['Map'],config['Agents'][index]['End']))

    if config['Agents'][index]['Trigger']['type'] == 'relative':
        # trigger = create_EntityTrigger_at_relativePos(config['Map'], config['Ego'], config['Agents'][index]['Trigger'],'Ego')
        trigger = create_EntityTrigger_at_relativePos2(config['Map'], config['Agents'][index],'Ego')
    else: #absolute
        trigger = create_EntityTrigger_at_absolutePos(config['Map'],config['Agents'][index]['Trigger'],'Ego')

    advStartSpeedEvent = xosc.Event(f"Adv{index}StartSpeedEvent", xosc.Priority.overwrite)
    advStartSpeedEvent.add_action(f"Adv{index}StartSpeedAction", advspeed)
    advStartSpeedEvent.add_trigger(trigger)
    # advStartSpeedEvent.add_action("AdvControlAction", advcontl)
    advActionEvent = xosc.Event(f"Adv{index}ActionEvent", xosc.Priority.parallel)
    trigger = create_Trigger_following_previous(f"Adv{index}StartSpeedEvent", f'$Agent{index}DynamicDelay')
    advActionEvent.add_action(f"Adv{index}AcquirePositionAction", advgoal)
    advActionEvent.add_action(f"Adv{index}AcquirePositionAction", advgoal)
    advActionEvent.add_trigger(trigger)


    ## Adv1 - Event2: Speed Behavior
    advEndSpeed = create_TransitionDynamics_from_config(Behavior,index=index)
    trigger = create_Trigger_following_previous(f"Adv{index}ActionEvent", f'$Agent{index}DynamicDelay')

    advEndSpeedEvent = xosc.Event(f"Adv{index}EndSpeedEvent", xosc.Priority.parallel)
    advEndSpeedEvent.add_action(f"Adv{index}EndSpeedEventAction", advEndSpeed)
    advEndSpeedEvent.add_trigger(trigger)

    ### Storyboard - Story & Maneuver
    advManeuver = xosc.Maneuver(f"Adv{index}Maneuver")
    advManeuver.add_event(advStartSpeedEvent)
    advManeuver.add_event(advEndSpeedEvent)
    advManeuver.add_event(advActionEvent)

    
    return advManeuver