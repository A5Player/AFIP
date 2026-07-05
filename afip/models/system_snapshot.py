from dataclasses import dataclass

@dataclass
class SystemSnapshot:
    mode:str="SIMULATION"
    health:str="READY"
    confidence:float=0.0
