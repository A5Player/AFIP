from afip.workflow.system_workflow import SystemWorkflow

class ApplicationRunner:
    def run(self, context=None):
        return SystemWorkflow().execute(context)
