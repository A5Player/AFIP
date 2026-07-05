class IntelligenceRegistry:
    def __init__(self):
        self._modules={}
    def register(self,module):
        self._modules[module.name]=module
    def all(self):
        return self._modules
