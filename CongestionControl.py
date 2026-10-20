class CongestionControl:
    def __init__(self, MSS):
        self.current_state = 0 # 0 == slow start, 1 == congestion avoidance
        self.MSS = MSS
        self.cwnd = MSS
        self.ssthresh = None

    def get_cwnd(self):
        return self.cwnd

    def get_ssthresh(self):
        return self.ssthresh

    def get_MSS_in_cwnd(self):
        return self.get_cwnd() // self.MSS

    def event_ack_received(self):
        if self.current_state == 0:
            self.cwnd += self.MSS
            if self.ssthresh is not None and self.cwnd >= self.ssthresh:
                self.current_state = 1
        else:
            self.cwnd += 1/self.get_MSS_in_cwnd() * self.MSS
        return

    def event_timeout(self):
        if self.current_state == 0:
            self.ssthresh = self.get_cwnd()//2
            self.cwnd = self.MSS
        else:
            self.ssthresh = self.get_cwnd()//2
            self.cwnd = self.MSS
            self.current_state = 0
        return

    def is_state_slow_start(self):
        return True if self.current_state == 0 else False

    def is_state_congestion_avoidance(self):
        return True if self.current_state == 1 else False
