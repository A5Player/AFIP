class PositionLifecycleManager:
    STATES=("NEW","OPEN","PROTECTED","CLOSED")
    def next_state(self,current,profit_points):
        if current=="NEW": return "OPEN"
        if current=="OPEN" and profit_points>0: return "PROTECTED"
        if current=="PROTECTED" and profit_points<=0: return "CLOSED"
        return current
