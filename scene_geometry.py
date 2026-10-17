"""One room coordinate system shared by drawing, dragging and hit testing."""
from dataclasses import dataclass

@dataclass(frozen=True)
class RoomView:
    scale: float
    left: float
    top: float
    width: float
    height: float

    def point(self,x,y):return self.left+x*self.width,self.top+y*self.height
    def normalized(self,x,y):return ((x-self.left)/self.width,(y-self.top)/self.height)

def room_view(width,height):
    # Uniform scaling and letterboxing preserve the entire room at any aspect ratio.
    scale=max(.01,min(max(1,width)/780,max(1,height)/520))
    return RoomView(scale,(width-780*scale)/2,(height-520*scale)/2,780*scale,520*scale)

# Interaction coordinates are ground-relative (canvas y minus 50 for the
# anchored 360px artwork). Match the seated chin/shoulder rather than old art.
SHOULDERS={'Mochi':210,'Maple':208,'Clover':220,'Pip':213}
def pet_zone(pet,x,y):
    shoulder=SHOULDERS.get(pet,180)
    if 48<=x<=300 and 26<=y<shoulder:return 'pet'
    if 35<=x<=325 and shoulder<=y<=310:return 'toy'
    return None

def local_pet_point(view,room_scale,x,y):
    cx,floor=view.point(.51,.96);s=view.scale*room_scale/100
    return (x-cx)/s+180,(y-floor)/s+310
