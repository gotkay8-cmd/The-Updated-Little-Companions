"""Time-based taskbar run with dedicated fitted eight-frame cycles."""
from wardrobe import outfit_sprite

class TaskbarRun:
    def __init__(self):
        self.at=None;self.position=None;self.direction=1;self.phase=0.;self.active=False;self.crossings=0;self.nap_until=None;self.napping=False
    def advance(self,now,x,width,work,scale,blocked=False,return_home=False,home_x=None):
        dt=0 if self.at is None else min(.05,max(0,now-self.at));self.at=now
        left,_,right,_=work;limit=max(left,right-width)
        if self.position is None or abs(x-round(self.position))>1:self.position=float(x)
        if blocked or return_home:
            self.crossings=0;self.nap_until=None;self.napping=False
        if self.nap_until is not None and now>=self.nap_until:
            self.nap_until=None;self.crossings=0
        self.napping=self.nap_until is not None
        if return_home:self.position=float(max(left,min(left+8 if home_x is None else home_x,limit)));self.direction=1;self.phase=0
        self.position=max(left,min(limit,self.position));self.active=not (blocked or return_home or self.napping) and limit>left
        if self.active:
            self.position+=self.direction*145*scale*dt;self.phase+=dt*10
            reached=False
            if self.direction>0 and self.position>=limit:self.position=float(limit);self.direction=-1;reached=True
            elif self.direction<0 and self.position<=left:self.position=float(left);self.direction=1;reached=True
            if reached:
                self.crossings+=1
                if self.crossings==2:
                    self.nap_until=now+10.;self.napping=True;self.active=False
        return round(self.position),'right' if self.direction>0 else 'left',int(self.phase)

def running_sprite(art_dir,data,pet,direction,index):
    from pathlib import Path
    return outfit_sprite(art_dir,data,pet,'idle',index,running=direction) or Path(art_dir)/f'{pet.lower()}-run-{direction}-{index%8}.png'
