import numpy as np

class Behavior():
    def __init__(self) -> None:
        self.origin = ''
        self.origin_offset = 0
        self.to = ''
        self.init_speed = None
        self.target_speed = None
        self.offset = 0
        self.from_opposite = False
        self.dynamic_start = 0
        self.dynamic_shape ='step'


class ScenarioCategory():
    def __init__(self, scate) -> None:
        self.topo = None
        self.topo_center = None
        self.ego = Behavior()
        self.adv = {}
        self.adv[0] = Behavior()
        self.scate = scate

        self._build_scenario()

    def _build_scenario(self):
        for i, ScenarioCategory in enumerate(self.scate):
            if i == 0: #EGO 以第一個Scenario Category為主
                self._get_scenario(ScenarioCategory, self.ego, self.adv[0])
            else:
                self.adv[i] = Behavior()
                self._get_scenario(ScenarioCategory, None, self.adv[i])

            # from pprint import pprint
            # attrs = vars(self.adv[i])
            # pprint(', '.join("%s: %s" % item for item in attrs.items()))



    def _get_scenario(self, cate, ego, adv):
        if ego is None: ego = Behavior()
        if adv is None: adv = Behavior()


        # 4-way
        # self.topo_center = (46, -113)
        self.topo = '4way'
        
        # sl1_wlN1 = [(690,-138),(685,-134),(680,-131),(670,-132)]

        AgentSpeed = '${$Agent1Speed / 3.6}'
        AgentLowSpeed = '${$Agent1LowSpeed / 3.6}'
        DynamicDuration = '$Agent1DynamicDuration' #3.1
        DynamicHaltDuration = '${$Agent1DynamicDuration / 3}' #1
        AgentDelay = '$Agent1Delay' # 0.45
        BehaviorMode = {'keeping':(AgentSpeed, AgentSpeed, DynamicDuration, 'linear', None), #等速
                        'braking':(AgentSpeed, AgentLowSpeed, DynamicDuration, 'linear', None),  #減速
                        'braking_halt': (AgentSpeed, 0, DynamicDuration, 'linear', None), #減速|未完成
                        'sudden_braking_halt':(AgentSpeed, 0, DynamicHaltDuration, 'sinusoidal', AgentDelay),  #急煞|未完成
                        'speed_up': ( 0, AgentSpeed, DynamicDuration, 'linear', None), #加速
                       } 
        # BehaviorMode = {'keeping':(AgentSpeed, AgentSpeed, 1, 'linear', None), #等速
        #                 'braking':(AgentSpeed, 4, 3.2, 'linear', None),  #減速
        #                 'braking_halt': (AgentSpeed, 0, 3.1, 'linear', None), #減速|未完成
        #                 'sudden_braking_halt':(AgentSpeed, 0, 1, 'sinusoidal', 0.45),  #急煞|未完成
        #                 'speed_up': ( 0, AgentSpeed, 5, 'linear', None), #加速
        #                 'speed_up': ( 0, AgentSpeed, 5, 'linear', None), #加速
        #                } 


        # ex: cate = 'hcis_23_01SR-TR'
        tags = cate.split('_')
        agent1Tag = tags[2][2:]
        scenarioId = tags[1]
        agent1InitPosition = agent1Tag.split('-')[0]
        agent1Lateral = agent1Tag.split('-')[1]

        """ Ego - Go Straight """
        ## Agent Left Turn
        ego.origin, ego.to = 'sl2', 'nl-2'
        adv.to = 'wl-1'

        # Position 2
        adv.origin = 'sl1'
        if scenarioId == '1': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[0]
        if scenarioId == '2': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[1]
        if scenarioId == '3': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[2]
        if scenarioId == '4': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[3]
        if scenarioId == '5': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[4]
        if scenarioId == '6': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[5]
        if scenarioId == '7': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[6]
        if scenarioId == '8': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[7]
        if scenarioId == '9': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[8]
        # Position 3
        adv.origin = 'sr1'
        adv.traj = 1
        if scenarioId == '11': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[0]
        if scenarioId == '12': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[1]
        if scenarioId == '13': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[2]
        if scenarioId == '14': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[3]
        if scenarioId == '15': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[4]
        if scenarioId == '16': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[5]
        if scenarioId == '17': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[6]
        if scenarioId == '18': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[7]
        if scenarioId == '19': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[8]
        # Position 5
        adv.origin = 'sr2'
        adv.traj = 1
        if scenarioId == '21': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[0]
        if scenarioId == '22': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[1]
        if scenarioId == '23': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[2]
        if scenarioId == '24': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[3]
        if scenarioId == '25': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[4]
        if scenarioId == '26': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[5]
        if scenarioId == '27': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[6]
        if scenarioId == '28': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[7]
        if scenarioId == '29': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[8]


        ## Agent Right Turn
        ego.origin, ego.to = 'sr2', 'nr-2'
        adv.to = 'el-1'
        # Position 2
        adv.origin = 'sr1'
        if scenarioId == '31': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[0]
        if scenarioId == '32': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[1]
        if scenarioId == '33': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[2]
        if scenarioId == '34': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[3]
        if scenarioId == '35': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[4]
        if scenarioId == '36': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[5]
        if scenarioId == '37': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[6]
        if scenarioId == '38': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[7]
        if scenarioId == '39': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[8]
        # Position 1
        adv.origin = 'sl1'
        adv.traj = 1
        if scenarioId == '41': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[0]
        if scenarioId == '42': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[1]
        if scenarioId == '43': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[2]
        if scenarioId == '44': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[3]
        if scenarioId == '45': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[4]
        if scenarioId == '46': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[5]
        if scenarioId == '47': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[6]
        if scenarioId == '48': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[7]
        if scenarioId == '49': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[8]
        # Position 4
        adv.origin = 'sl2'
        adv.traj = 1
        if scenarioId == '51': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[0]
        if scenarioId == '52': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[1]
        if scenarioId == '53': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[2]
        if scenarioId == '54': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[3]
        if scenarioId == '55': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[4]
        if scenarioId == '56': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[5]
        if scenarioId == '57': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[6]
        if scenarioId == '58': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[7]
        if scenarioId == '59': adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = list(BehaviorMode.values())[8]


        return
        

        

        #Position 2
        adv.delay = 0.2
        if cate =='left_turn1':
            ego.origin, ego.to, adv.origin, adv.to = 'sl2', 'nl-2', 'sl1', 'wl-1'
            adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape = '${$TargetSpeed / 3.6}', "${$TargetSpeed / 3.6}", 1, 'linear'
            adv.traj = sl1_wlN1
        if cate =='left_turn2':
            ego.origin, ego.to, adv.origin, adv.to = 'sl2', 'nl-2', 'sl1', 'wl-1'
            adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape = '${$TargetSpeed / 3.6}', 4, 3.2, 'linear' #減速
        if cate =='left_turn3':
            ego.origin, ego.to, adv.origin, adv.to = 'sl2', 'nl-2', 'sl1', 'wl-1'
            adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape = '${$TargetSpeed / 3.6}', 0, 3.1, 'linear' #減速|未完成
        if cate =='left_turn4':
            ego.origin, ego.to, adv.origin, adv.to = 'sl2', 'nl-2', 'sl1', 'wl-1'
            adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = '${$TargetSpeed / 3.6}', 0, 1, 'sinusoidal', 0.45 #急煞|未完成
        if cate =='left_turn5':
            ego.origin, ego.to, adv.origin, adv.to = 'sl2', 'nl-2', 'sl1', 'wl-1'
            adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape = 0, '${$TargetSpeed / 3.6}', 5, 'linear' #加速

        #Position 3
        if cate =='left_turn6':
            ego.origin, ego.to, adv.origin, adv.to = 'sl2', 'nl-2', 'sr1', 'wl-1'
            adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape = '${$TargetSpeed / 3.6}', "${$TargetSpeed / 3.6}", 1, 'linear'
        if cate =='left_turn7':
            ego.origin, ego.to, adv.origin, adv.to = 'sl2', 'nl-2', 'sr1', 'wl-1'
            adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape = '${$TargetSpeed / 3.6}', 4, 3.2, 'linear' #減速
        if cate =='left_turn8':
            ego.origin, ego.to, adv.origin, adv.to = 'sl2', 'nl-2', 'sr1', 'wl-1'
            adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape = '${$TargetSpeed / 3.6}', 0, 3.1, 'linear' #減速|未完成
        if cate =='left_turn9':
            ego.origin, ego.to, adv.origin, adv.to = 'sl2', 'nl-2', 'sr1', 'wl-1'
            adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = '${$TargetSpeed / 3.6}', 0, 1, 'sinusoidal', 0.45 #急煞|未完成
        if cate =='left_turn10':
            ego.origin, ego.to, adv.origin, adv.to = 'sl2', 'nl-2', 'sr1', 'wl-1'
            adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape = 0, '${$TargetSpeed / 3.6}', 5, 'linear' #加速


        #Position 5
        if cate =='left_turn11':
            ego.origin, ego.to, adv.origin, adv.to = 'sl2', 'nl-2', 'sr2', 'wl-1'
            adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape = '${$TargetSpeed / 3.6}', "${$TargetSpeed / 3.6}", 1, 'linear'
        if cate =='left_turn12':
            ego.origin, ego.to, adv.origin, adv.to = 'sl2', 'nl-2', 'sr2', 'wl-1'
            adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape = '${$TargetSpeed / 3.6}', 4, 3.2, 'linear' #減速
        if cate =='left_turn13':
            ego.origin, ego.to, adv.origin, adv.to = 'sl2', 'nl-2', 'sr2', 'wl-1'
            adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape = '${$TargetSpeed / 3.6}', 0, 3.1, 'linear' #減速|未完成
        if cate =='left_turn14':
            ego.origin, ego.to, adv.origin, adv.to = 'sl2', 'nl-2', 'sr2', 'wl-1'
            adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = '${$TargetSpeed / 3.6}', 0, 1, 'sinusoidal', 0.45 #急煞|未完成
        if cate =='left_turn15':
            ego.origin, ego.to, adv.origin, adv.to = 'sl2', 'nl-2', 'sr2', 'wl-1'
            adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape = 0, '${$TargetSpeed / 3.6}', 5, 'linear' #加速
            
        #Position 2
        if cate =='hcis_01TR':
            ego.origin, ego.to, adv.origin, adv.to = 'sl2', 'nl-2', 'sl1', 'wl-1'
            adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape = '${$TargetSpeed / 3.6}', "${$TargetSpeed / 3.6}", 1, 'linear'
        if cate =='left_turn2':
            ego.origin, ego.to, adv.origin, adv.to = 'sl2', 'nl-2', 'sl1', 'wl-1'
            adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape = '${$TargetSpeed / 3.6}', 4, 3.2, 'linear' #減速
        if cate =='left_turn3':
            ego.origin, ego.to, adv.origin, adv.to = 'sl2', 'nl-2', 'sl1', 'wl-1'
            adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape = '${$TargetSpeed / 3.6}', 0, 3.1, 'linear' #減速|未完成
        if cate =='left_turn4':
            ego.origin, ego.to, adv.origin, adv.to = 'sl2', 'nl-2', 'sl1', 'wl-1'
            adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape, adv.delay = '${$TargetSpeed / 3.6}', 0, 1, 'sinusoidal', 0.45 #急煞|未完成
        if cate =='left_turn5':
            ego.origin, ego.to, adv.origin, adv.to = 'sl2', 'nl-2', 'sl1', 'wl-1'
            adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape = 0, '${$TargetSpeed / 3.6}', 5, 'linear' #加速



        # if cate =='left_turn6':
        #     ego.origin, ego.to, adv.origin, adv.to = 'sl2', 'nl-2', 'sl1', 'wl-1'
        #     adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape = 0, '${$TargetSpeed / 3.6}', 2, 'linear' #停止
        # if cate =='left_turn1':
        #     ego.origin, ego.to, adv.origin, adv.to = 'sl2', 'nl-2', 'sl1', 'wl-1'
        #     adv.init_speed, adv.end_speed, adv.dynamic_duration, adv.dynamic_shape = 'TargetSpeed', 0, 1, 'sinusoidal'
        if cate == '31-1': 
            ego.origin, ego.to, adv.origin, adv.to = 'z4', 'z2', 'z1', 'z4'
        if cate == '31-2': 
            ego.origin, ego.to, adv.origin, adv.to = 'z4', 'z2', 'z1', 'z3'
        if cate == '31-3': 
            ego.origin, ego.to, adv.origin, adv.to = 'z4', 'z2', 'z1', 'z2'
        if cate == '32-2':   #tol = 25
            ego.origin, ego.to, adv.origin, adv.to = 'z4', 'z2', 'z3', 'z1'
        if cate == '33':  #tol =23
            ego.origin, ego.to, adv.origin, adv.to = 'z4', 'z2', 'z3', 'z2'
        if cate == '65-1':  #s = 20
            ego.origin, ego.to, adv.origin, adv.to = 'z4', 'z2', 'z4', 'z1'
            ego.origin_offset = -27
        if cate == '65-2':  #65-1&65-2 ${$Target_S-7}
            ego.origin, ego.to, adv.origin, adv.to = 'z4', 'z2', 'z4', 'z3'
            ego.origin_offset = -27


        if cate == '29-1':  
            ego.origin, ego.to, adv.origin, adv.to = 'z4', 'z1', 'z2', 'z1'
        if cate == '32-3':
            ego.origin, ego.to, adv.origin, adv.to = 'z4', 'z1', 'z3', 'z1'

        if cate == '30-1':
            ego.origin, ego.to, adv.origin, adv.to = 'z4', 'z3', 'z2', 'z3'
        if cate == '30-2':
            ego.origin, ego.to, adv.origin, adv.to = 'z4', 'z3', 'z2', 'z4'
        if cate == '32-1':
            ego.origin, ego.to, adv.origin, adv.to = 'z4', 'z3', 'z3', 'z1'
        if cate == '34':
            ego.origin, ego.to, adv.origin, adv.to = 'z4', 'z3', 'z1', 'z3'
        if cate == '35-1':
            ego.origin, ego.to, adv.origin, adv.to = 'z4', 'z3', 'z1', 'z4'
        if cate == '35-2': #tol = 20
            ego.origin, ego.to, adv.origin, adv.to = 'z4', 'z3', 'z3', 'z2'
        return

        #ego straight
        self.topo = 'straight_cutin'
        if cate == '15': 
            ego.origin, ego.to, adv.origin, adv.to = 'r5', 'r4', 'r2', 'r4'
            adv.dynamic_shape = 'linear'
            adv.dyn_duration = 1.5
            adv.dyn_start = 0.01
            # self.topo_center = (248, -249)
            # self.topo_center = (359, -307)
            self.topo_center = (45, -196)
        elif cate == '9':
            ego.origin, ego.to, adv.origin, adv.to = 'r3', 'r1', 'r5', 'r1'
            adv.dyn_shape = 'sinusoidal'
            adv.dyn_duration = 1
            adv.dyn_start = 0.3
            self.topo_center = (143, -213) #sc9
            self.topo_center = (45, -196)
            # self.topo_center = (213, 143) #sc9
        elif cate == '22':
            ego.origin, ego.to, adv.origin, adv.to = 'r6', 'r5', 'r1', 'r5'
            adv.from_opposite = True
            adv.dyn_shape = 'sinusoidal'
            adv.dyn_duration = 1
            adv.dyn_start = 1.5
            self.topo_center = (86, -210)
        elif cate == '12':
            ego.origin, ego.to, adv.origin, adv.to = 'r6', 'r4', 'r5', 'r2'
            adv.from_opposite = False
            adv.dyn_shape = 'sinusoidal'
            adv.dyn_duration = 2
            adv.dyn_start = 1.5
            adv.trigger = 'sim_time'
            self.topo_center = (86, -210)


        self.topo = 'straight'
        self.topo_center = (86, -210)
        if cate == '62':
            ego.origin, ego.to, adv.origin, adv.to = 'r6', 'r5', 'r1', 'r5'
            adv.from_opposite = True
            adv.dyn_shape = 'sinusoidal'
            adv.dyn_duration = 1
            adv.dyn_start = 3
        if cate == '13':
            ego.origin, ego.to, adv.origin, adv.to = 'r6', 'r4', 'r5', 'r4'
            adv.trigger = 'sim_time'
        if cate == '8':  #自行設ego關閉Control
            ego.origin, ego.to, adv.origin, adv.to = 'r6', 'r4', 'r5', 'r4'
            adv.dyn_shape = 'sinusoidal'
            adv.dyn_duration = 0.1
            adv.from_opposite = False
            adv.dyn_start = 2
            adv.trigger = 'sim_time'
        if cate == '10':
            ego.origin, ego.to, adv.origin, adv.to = 'r5', 'r1', 'r3', 'r1'
            ego.dyn_shape = 'sinusoidal'
            ego.dyn_duration = 1.5
            ego.dyn_start = 1.5
            ego.trigger = 'sim_time'
            self.topo_center = (86, -210)
        return 

        self.topo = 'straight_static'
        self.stc = {}
        if cate == '21':
            ego.origin, ego.to, adv.origin, adv.to = 'r6', 'r4', 'r1', 'r3'
            adv.from_opposite = True
            adv.dyn_shape = 'sinusoidal'
            adv.dyn_duration = 1
            adv.dyn_start = 0
            adv.trigger ='sim_time'
        if cate == '14': #自行微調間距，結束時間 s=99, stop  =8sec 
            ego.origin, ego.to, adv.origin, adv.to = 'r6', 'r4', 'r5', 'r5'
            adv.dyn_duration = 1
            adv.dyn_start = 0
            adv.trigger ='sim_time'
            adv.init_speed = 0
            adv.target_speed = 0
            self.stc[0] = Behavior()
            self.stc[0].origin = 'r4'
            self.stc[0].offset = 0
        if cate == '20':
            ego.origin, ego.to, adv.origin, adv.to = 'r6', 'r4', 'r4', 'r6'
            adv.from_opposite = True
            adv.dyn_start = 0
            adv.trigger ='sim_time'
            self.stc[0] = Behavior()
            self.stc[0].origin = 'r1'

# INput: 4-way center


import carla

def get_zone():
    # Connect to the Carla server
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)

    # Get the world
    world = client.get_world()
    carla_map = world.get_map()

    # # Function to get a waypoint
    # def get_waypoint(location):
    #     map = world.get_map()
    #     return map.get_waypoint(location, project_to_road=True, lane_type=carla.LaneType.Any)

    # Define the junction center coordinates
    junction_x, junction_y = 70.0, 230.0  # Replace with actual coordinates
    junction_center = carla.Location(junction_x, junction_y, 0)

    # Get the waypoint for the junction center
    waypoint = carla_map.get_waypoint(junction_center)
    if waypoint is None:
        print("Waypoint not found at the given location")
        return

    # Get the junction ID
    junction = waypoint.get_junction()
    if junction is None:
        print("No junction found at the waypoint")
        return

    # Get the bounding box of the junction
    bbox = junction.bounding_box
    x = bbox.extent.x 
    y = bbox.extent.y 
    junction_center = bbox.location
    junction_rotate = bbox.rotation

    # Calculate the z4_anchor
    transform = carla.Transform(
        location=bbox.location - carla.Location(x=2*x, y=0, z=0),  # Adjust as needed
        rotation=junction_rotate
    )
    z4_anchor = carla_map.get_waypoint(transform.location)
    if z4_anchor is None:
        print("z4_anchor waypoint not found")
        return

    # Get the waypoints for z4
    z4 = []
    for wp in z4_anchor.next(z4_anchor.lane_width):
        z4.append(wp)

    # Print the z4 waypoints
    for wp in z4:
        print(f"Waypoint at location: {wp.transform.location}")

if __name__ == "__main__":
    main()



# crop area
# junction_center = (junction_x, junction_y)
# junction = get_waypoint(junction_center).junction_id
# x = junction.bounding_box.extent.x 
# y = junction.bounding_box.extent.y 
# junction_center = junction.bounding_box.location
# junction_rotate = junction.bounding_box.extent.rotate 
# z4_anchor = junction.transform(carla.Transform(junction.transform.location + 2*x,  junction_rotate))
# z4_anchor = get_waypoint(z4_anchor)
# z4 = []
# for wp in z4_anchor.next(z4_anchor.lane_width):
#     z4.append(wp)

# divid points into zones: z1, z2 ,c1,c2


#sample from zone


#find centline path from start to end