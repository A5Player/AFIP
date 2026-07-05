from .base_intelligence import BaseIntelligence

class SessionIntelligence(BaseIntelligence):
    name='SessionIntelligence'
    def collect(self): return {}
    def analyze(self): return {}
    def confidence(self): return 0.0
    def recommendation(self): return {'module':self.name,'action':'WAIT','confidence':self.confidence()}
