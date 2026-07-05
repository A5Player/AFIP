class TelemetryService:
    def emit(self,event:str,payload:dict):
        return {"event":event,"accepted":True}
