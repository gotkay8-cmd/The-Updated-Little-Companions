"""Frame-rate-independent cardinal wandering, separate from saved room placement."""
import random

def walking_bounds(percent):
    scale=percent/100
    margin=min(.4,180*scale/819+.015)
    return margin,1-margin,min(.91,max(.66,(235*scale+45)/476)),.97

def new_walk(home,now):
    return dict(x=home[0],y=home[1],target=home,direction='right',moving=False,
                at=now,pause=now,started=now,returning=False)

def advance_walk(w,home,bounds,now,returning=False,rng=random):
    dt=min(.05,max(0,now-w['at']));w['at']=now
    if returning and not w['returning']:
        w['moving']=False;w['pause']=now
    w['returning']=returning
    if not w['moving'] and now>=w['pause']:
        if returning:
            if abs(home[0]-w['x'])>.001:target=(home[0],w['y'])
            elif abs(home[1]-w['y'])>.001:target=home
            else:return True
        else:
            left,right,top,bottom=bounds
            candidates=[('left',(max(left,w['x']-.16),w['y'])),('right',(min(right,w['x']+.16),w['y'])),
                        ('up',(w['x'],max(top,w['y']-.12))),('down',(w['x'],min(bottom,w['y']+.12)))]
            candidates=[(direction,target) for direction,target in candidates if abs(target[0]-w['x'])+abs(target[1]-w['y'])>.025]
            if not candidates:return False
            _,target=rng.choice(candidates)
        dx,dy=target[0]-w['x'],target[1]-w['y']
        w['direction']=('right' if dx>0 else 'left') if abs(dx)>.001 else ('down' if dy>0 else 'up')
        w['target']=target;w['moving']=True;w['started']=now
    if w['moving']:
        axis='x' if w['direction'] in ('left','right') else 'y';i=0 if axis=='x' else 1
        delta=w['target'][i]-w[axis];step=(.07 if axis=='x' else .12)*dt
        if abs(delta)<=step:
            w[axis]=w['target'][i];w['moving']=False;w['pause']=now+(0 if returning else 1.25)
        else:w[axis]+=step if delta>0 else -step
    return False
