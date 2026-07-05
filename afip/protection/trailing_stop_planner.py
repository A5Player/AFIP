class TrailingStopPlanner:
    def update(self, floating_points: float, confidence: float)->dict:
        if floating_points<=0:
            return {"status":"WAIT","lock_points":0}
        gap=700 if confidence>=70 else 400 if confidence>=50 else 200
        return {"status":"ACTIVE","lock_points":max(0,floating_points-gap),"gap":gap}
