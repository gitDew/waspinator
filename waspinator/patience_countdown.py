class PatienceCountdown:
    """A simple countdown timer that can be reset and ticked down. Used to implement a patience mechanism for the trap."""
    def __init__(self, start):
        self.start = start
        self.count = start

    def tick(self):
        if self.count > 0:
            self.count -= 1

    def reset(self):
        self.count = self.start

    def ran_out(self):
        return self.count == 0
