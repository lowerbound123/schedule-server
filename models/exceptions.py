class ErrorStructure(Exception):
    """输出了{id: xxx, orig: xxx,dest: xxx}结构以外的结构"""
    pass

class NonExistentMachine(Exception):
    """方案中出现了一个不存在的机器或货架"""
    pass

class NonExistentCarrier(Exception):
    """方案中出现了一个不存在的货物"""
    pass

class FaultOrigin(Exception):
    """来源地不存在对应货物"""
    pass

class FaultDestination(Exception):
    """目的地不能处理对应的workstep"""
    pass

class FaultCarrier(Exception):
    """货物目前正在加工，不需要安排任务"""
    pass

class FullDestination(Exception):
    """目的地放不下了"""
    pass

