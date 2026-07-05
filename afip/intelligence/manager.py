class IntelligenceManager:
    def __init__(self,registry):
        self.registry=registry
    def evaluate(self):
        return {k:v.recommendation() for k,v in self.registry.all().items()}
