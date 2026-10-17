"""Select approved poses by cursor side without playing the opposite paw."""
class CursorReaction:
    def __init__(self):
        self.zone=None
        self.side='left'
        self.target='left'
        self.level=0
        self.at=None

    def reset(self):
        self.zone=None;self.level=0;self.at=None

    def update(self,zone,x,now):
        if zone not in ('pet','toy'):
            self.reset();return
        if self.zone!=zone:
            self.zone=zone;self.level=0;self.at=now
            self.side=self.target='right' if x>=180 else 'left'
        # A small center dead zone prevents flickering between sides.
        if x<168:self.target='left'
        elif x>192:self.target='right'
        steps=int((now-self.at+.000001)/.10)
        if steps<=0:return
        self.at=now
        for _ in range(min(steps,6)):
            if self.side!=self.target:
                if self.level:self.level-=1
                else:self.side=self.target
            else:self.level=min(3 if zone=='pet' else 2,self.level+1)

    @property
    def frame(self):
        if self.zone=='pet':
            return ([0,1,2,3] if self.side=='left' else [0,1,2,4])[self.level]
        return ([0,1,2] if self.side=='left' else [4,5,6])[min(self.level,2)]
