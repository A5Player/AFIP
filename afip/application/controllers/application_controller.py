class ApplicationController:
    def start(self, context):
        return {"status": "RUNNING", "mode": context.mode}
