class AFIPApplication:
    def __init__(self, integration_manager):
        self.integration_manager=integration_manager
    def start(self):
        return self.integration_manager.build_context()
