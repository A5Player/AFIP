class SimulationJournal:
    def __init__(self):
        self.records=[]
    def record(self,event:dict):
        self.records.append(event)
        return len(self.records)
