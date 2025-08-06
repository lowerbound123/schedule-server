from pydantic import BaseModel, Field
from enum import Enum


class CarrierStatus(int, Enum):
    WORK = 0
    WAIT = 1
    FINISH = -1


class Carrier(BaseModel):
    id: str # 机台编号
    workflow: list[tuple[str, int]] # 工作流，一个list，里面每个元素(workstep, time)表示工步和这个工步需要的时间
    current: int = Field(default=0) # 当前在哪个工步
    status: CarrierStatus = Field(default=CarrierStatus.WAIT) # 当前状态，是在等待，还是在被处理，还是已经搞完了
    at: str = Field(default="Input") # 当前在哪个机台
    
    @property
    def current_cost(self):
        if self.current < len(self.workflow):
            return self.workflow[self.current][1]
        else:
            return 0
    @property
    def current_tag(self):
        if self.current < len(self.workflow):
            return self.workflow[self.current][0]
        else:
            return "Output"
