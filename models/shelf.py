from pydantic import BaseModel, Field


class Shelf(BaseModel):
    id: str  # shelf id
    max: int # 这个shelf最多放几个机器
    on_road: list[str] = Field(default_factory=list) # 正在路上的carrier
    on_wait: list[str] = Field(default_factory=list) # 正在等待的carrier

    @property
    def free(self):
        return self.max - len(self.on_road) - len(self.on_wait)
    @property
    def contain(self):
        return len(self.on_road) + len(self.on_wait)
    @property
    def wait(self):
        return len(self.on_wait)
    @property
    def road(self):
        return len(self.on_road)