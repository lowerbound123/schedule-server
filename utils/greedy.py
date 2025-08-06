from models import Carrier, Machine, Shelf, StandardResponse
from random import choice


class RandomGreddy:
    def __init__(self, tags: dict[str, list[str]]):
        self.tags: dict[str, list[str]] = tags
        self.machines: dict[str, Machine] = {}
        self.carriers: dict[str, Carrier] = {}
        self.shelves: dict[str, Shelf] = {}
    
    def possible_machines(self, carrier: Carrier):
        if carrier.current == len(carrier.workflow):
            return []
        result = []
        for machine in self.tags[carrier.workflow[carrier.current][0]]:
            if self.machines[machine].free >= 1:
                result.append(machine)
        return result
    
    def possible_shelves(self, carrier: Carrier):
        if carrier.current == len(carrier.workflow):
            return ["Output"]
        result = []
        for shelf in self.shelves.values():
            if shelf.id != 'Input' and shelf.id != 'Output' and shelf.free >= 1:
                result.append(shelf.id)
        return result
                
    # 限制在INPUT上等待的载具数量，防止爆token
    def get_input_carriers(self, INPUT: Shelf):
        result = []
        idx = 0
        while idx < len(INPUT.on_wait) and len(result) < 5:
            if self.carriers[INPUT.on_wait[idx]].status == 1:
                next_machines = self.possible_machines(self.carriers[INPUT.on_wait[idx]])
                if len(next_machines) > 0:
                    result.append((INPUT.on_wait[idx], next_machines))
            idx += 1
        return result
    
    def update(self, machines: dict[str, Machine], shelves: dict[str, Shelf], carriers: dict[str, Carrier]):
        self.machines = machines
        self.shelves = shelves
        self.carriers = carriers
    
    def __call__(self, machines: dict[str, Machine], shelves: dict[str, Shelf], carriers: dict[str, Carrier]) -> StandardResponse:
        self.machines = machines
        self.shelves = shelves
        self.carriers = carriers
        # print("* Machine")
        # for machine in machines.values():
        #     print("\t*", machine.free, machine.on_work, machine.on_wait, machine.on_road)
        # print("* Shelf")
        # for shelf in shelves.values():
        #     print("\t*", shelf.free, shelf.on_wait, shelf.on_road)
        first_tier = []  # 优先转运机器上的载具
        for machine in machines.values():
            for carrier in machine.on_wait:
                if carriers[carrier].status == 1:
                    next_machines = self.possible_machines(carriers[carrier])
                    next_shelves = self.possible_shelves(carriers[carrier])
                    if len(next_machines) > 0 or len(next_shelves) > 0:
                        first_tier.append((carrier, next_machines, next_shelves))
        if len(first_tier) > 0:
            r_carrier, next_machines, next_shelves = choice(first_tier)
            # 如果存在可以立刻过去的机台就立刻送过去, 否则送到一个架子上
            if len(next_machines) > 0:
                return StandardResponse(
                    carrier=r_carrier, 
                    orgi=carriers[r_carrier].at, 
                    dest=choice(next_machines)
                )
            else:
                return StandardResponse(
                    carrier=r_carrier, 
                    orgi=carriers[r_carrier].at, 
                    dest=choice(next_shelves)
                )

        second_tier = [] # 次优先转运货架上的载具
        for shelf in shelves.values():
            if shelf.id == 'Input' or shelf.id == 'Output': 
                continue
            for carrier in shelf.on_wait:
                if carriers[carrier].status == 1:
                    next_machines = self.possible_machines(carriers[carrier])
                    if len(next_machines) > 0:
                        second_tier.append((carrier, next_machines))
        if len(second_tier) > 0:
            r_carrier, next_machines = choice(second_tier)
            # 如果货物在货架上，那只能再送到一个机器上
            return StandardResponse(
                carrier=r_carrier, 
                orgi=carriers[r_carrier].at, 
                dest=choice(next_machines)
            )
                
        third_tier = self.get_input_carriers(shelves['Input'])  # 最后转运Input中的载具
        if len(third_tier) > 0:
            r_carrier, next_machines = choice(third_tier)
            # 如果货物在货架(Input)上，那只能再送到一个机器上
            return StandardResponse(
                carrier=r_carrier, 
                orgi=carriers[r_carrier].at, 
                dest=choice(next_machines)
            )
        
        return StandardResponse(
            carrier="None",
            orgi="None",
            dest="None"
        )