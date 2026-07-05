class ModeController:
    MODES=("SIMULATION","DEMO","LIVE")
    def __init__(self): self.mode="SIMULATION"
    def set_mode(self,mode):
        if mode in self.MODES: self.mode=mode
