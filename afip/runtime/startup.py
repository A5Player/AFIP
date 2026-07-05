from afip.bootstrap.bootstrapper import Bootstrapper

class Startup:
    def run(self):
        return Bootstrapper().initialize()
