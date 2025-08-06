from pydantic import BaseModel, Field


class Machine(BaseModel):
    id: str # 这个机器的id
    max: int # 这个机器最多能放多少个carrier
    tags: list[str] # 这个机器能处理的工步
    on_work: list[str] = Field(default_factory=list) # 正在加工或者等待加工的carrier
    on_road: list[str] = Field(default_factory=list) # 正在运输到这个机台的carrier
    on_wait: list[str] = Field(default_factory=list) # 已经加工完，等待搬走的carrier
    
    

    @property
    def free(self):
        return self.max - len(self.on_work) - len(self.on_road) - len(self.on_wait)
    @property
    def contain(self):
        return self.on_work + self.on_road + self.on_wait
    @property
    def wait(self):
        return len(self.on_wait)
    @property
    def road(self):
        return len(self.on_road)
    @property
    def work(self):
        return len(self.on_work)
