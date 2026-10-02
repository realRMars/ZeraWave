"""Small renderer-owned basin view controller; no simulation or audio clock."""
import math

def validate_pose(data=None):
    c=dict(yaw=.50,pitch=.724,distance=3.50,pan=[0.,0.],manual=False);c.update(data or {})
    if set(c)!=set(('yaw','pitch','distance','pan','manual')) or type(c['manual']) is not bool:raise ValueError('Invalid Water view')
    for k,a,b in (('yaw',-100.,100.),('pitch',.28,1.32),('distance',1.7,10.)):
        if type(c[k]) not in (int,float) or not math.isfinite(c[k]) or not a<=c[k]<=b:raise ValueError('Invalid view '+k)
    if not isinstance(c['pan'],(list,tuple)) or len(c['pan'])!=2 or any(type(x) not in (int,float) or not math.isfinite(x) or abs(x)>2. for x in c['pan']):raise ValueError('View pan bounded +/-2')
    c['pan']=list(c['pan']);return c

class BasinView:
    def __init__(self,data=None):self.load(data);self.auto=None;self.button_down=None;self.serial=0
    def load(self,data=None):
        c=validate_pose(data);self.base=c['yaw'];self.yaw=c['yaw'];self.pitch=c['pitch'];self.distance=c['distance'];self.pan=c['pan'];self.manual=c['manual'];self.button_down=None
    def reset(self):self.load();self.auto=None;self.serial+=1
    def config(self):return dict(yaw=self.yaw if self.manual or self.auto is False else self.base,pitch=self.pitch,distance=self.distance,pan=list(self.pan),manual=self.manual)
    def sample(self,seconds,automatic):
        angle=.48*math.sin(seconds*math.tau/120.)
        if self.auto is not None and bool(automatic)!=self.auto:
            if automatic:self.base=self.yaw-angle;self.manual=False
        self.auto=bool(automatic)
        if automatic and not self.manual:self.yaw=self.base+angle
        return (self.yaw,self.pitch,self.distance),tuple(self.pan)
    def button(self,button,pressed,x,y,shift=False):
        if not pressed:self.button_down=None;return
        self.button_down='pan' if button==1 or shift else 'orbit';self.cursor=(x,y);self.manual=True;self.serial+=1
    def move(self,x,y,width,height):
        if self.button_down is None:self.cursor=(x,y);return
        dx=x-self.cursor[0];dy=y-self.cursor[1];self.cursor=(x,y);unit=max(1.,min(width,height))
        if self.button_down=='orbit':self.yaw=max(-100.,min(100.,self.yaw-dx/unit*2.4));self.pitch=max(.28,min(1.32,self.pitch+dy/unit*1.8))
        else:self.pan=[max(-2.,min(2.,self.pan[0]-dx/unit*self.distance*.5)),max(-2.,min(2.,self.pan[1]+dy/unit*self.distance*.5))]
        self.serial+=1
    def scroll(self,delta):self.distance=max(1.7,min(10.,self.distance*math.exp(-delta*.12)));self.serial+=1
