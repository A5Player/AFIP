class RuntimeManager:
    def __init__(self):
        self.state = "INITIALIZING"

    def start(self):
        self.state = "RUNNING"

    def stop(self):
        self.state = "STOPPED"
