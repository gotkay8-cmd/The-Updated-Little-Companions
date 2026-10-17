"""Input-driven animation state, with no keycodes or typed text stored."""
from collections import deque
from statistics import median
import math

class InputAnimation:
    def __init__(self,mode,frames=8):
        self.mode=mode;self.frames=frames;self.phase=0.;self.target=0.
        self.at=None;self.last_event=None;self.period=.75
        self.intervals=deque(maxlen=4);self.until=0.

    def advance(self,now):
        if self.at is not None and self.mode=='click':
            self.phase=min(self.target,self.phase+max(0,now-self.at)*self.frames/self.period)
        self.at=max(now,self.at or now)

    def event(self,now,count=1):
        self.advance(now)
        gap=None if self.last_event is None else now-self.last_event
        if gap is not None and .001<gap<2:
            self.intervals.append(gap/max(1,count))
        elif gap is None or gap>=2:
            self.intervals.clear()
        self.last_event=now
        if self.mode=='typing':
            self.phase+=max(1,count)
            self.target=self.phase
            hold=max(.35,min(1.5,(median(self.intervals) if self.intervals else .3)*1.5))
            self.until=now+hold
        else:
            self.period=max(.20,min(1.5,median(self.intervals))) if self.intervals else .75
            self.target=min(self.phase+self.frames, max(self.target,math.floor(self.phase))+self.frames*max(1,count))
            self.until=now+(self.target-self.phase)*self.period/self.frames+.05

    def frame(self,now):
        self.advance(now)
        return int(self.phase)%self.frames
