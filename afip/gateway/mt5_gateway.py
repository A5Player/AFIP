class MT5Gateway:
    def connect(self): return False
    def account_info(self): return {}
    def send_order(self, order): raise NotImplementedError("Live trading not enabled")
