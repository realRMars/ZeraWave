"""Authored stormglass chart and bounded charge relay, sharing FluxMemory interpretation."""
import math
import numpy as np
from magnetic_response import FluxMemory
from color_controls import PALETTE_FAMILIES

class ArcNetwork:
    """Nine persistent junctions, eight chart edges and four temporary relay paths."""
    EDGES=((0,1),(1,2),(2,3),(3,4),(3,5),(5,6),(5,7),(4,8))
    def __init__(self,seed=7301):
        self.seed=int(seed);self.f=np.linspace(0.,1.,17);self.groups=np.arange(4)[:,None]*4+np.arange(5)[None,:]
        self.positions=np.array([(-2.00,.52,.18),(-1.24,-.24,-.15),(-.68,.85,.10),(-.20,.06,.40),(-.40,-.92,-.12),(.75,.40,-.22),(1.74,1.00,.30),(1.98,-.22,.18),(.88,-.98,.25)])
        self.palettes=np.array([[[int(h[k:k+2],16)/255. for k in (1,3,5)] for h in colors] for colors in PALETTE_FAMILIES['arcs.asterism'].values()])
        self.radius=np.array([.19,.25,.17,.30,.20,.24,.18,.23,.15]);self.data=None
    def pigments(self,memory):
        phase=memory.phase*.014+max(0,memory.visit-1)*.41;family=int(phase)%3
        f=max(0.,min(1.,((phase%1.)-.7)/.3));f=f*f*(3.-2.*f)
        return tuple(map(tuple,self.palettes[family]*(1.-f)+self.palettes[(family+1)%3]*f))
    def build(self,memory,t,amount=1.):
        phase=memory.phase;energy=memory.energy*amount;high=memory.high*amount
        world=self.positions.copy();ids=np.arange(9.)
        world[:,0]+=.05*np.sin(phase*.19+ids*1.3);world[:,1]+=.06*np.sin(phase*.16+ids*2.1)
        heat=np.zeros(9);meta=np.zeros((12,4));active=np.zeros(12,dtype=bool);active[:8]=True
        # Quiet chart paths have a slow moving witness; sustained pressure lights a route in order.
        route=phase*.36;cursor=route%8
        for row in range(8):
            gap=min(abs(cursor-row),8-abs(cursor-row));meta[row]=(0.,(phase*.13+row*.127)%1.,.025+high*.12,.13+energy*(.20+.55*math.exp(-gap*gap/1.7)))
        links=list(self.EDGES)+[(0,0)]*4
        for i,event in enumerate(memory.events):
            age=t-event[0];edge=int(event[1]);a,b=self.EDGES[edge];power=event[2]*amount;front=(age-.06)/.84
            residue=power*math.exp(-age*.55)
            heat[a]+=residue*.30;heat[b]+=residue*max(0.,min(1.,front))
            world[b,1]+=.035*power*math.sin(age*11.)*math.exp(-age*2.)
            meta[edge,0]+=residue*.75
            if 0.<front<1.2:meta[edge,1:3]=(front,power*math.exp(-age*.7)*1.8)
            # Relay chooses a valid neighboring chart junction; leaf endpoints answer back along the chart.
            neighbors=[y if x==b else x for x,y in self.EDGES if x==b or y==b]
            candidates=[n for n in neighbors if n!=a] or [a]
            target=candidates[int(event[3]*len(candidates))%len(candidates)];links[8+i]=(b,target)
            relay=(age-.88)/1.03
            if amount>0 and .88<age<4.5:
                active[8+i]=True;meta[8+i]=(residue*.5,relay,power*math.exp(-max(0.,age-.88)*.85)*1.45 if relay<1.2 else 0.,0.)
                heat[target]+=power*math.exp(-max(0.,age-1.7)*.85)*max(0.,min(1.,relay))*.75
        yaw=.11*math.sin(phase*.027);c,s=math.cos(yaw),math.sin(yaw)
        world=world@np.array([[c,0.,-s],[0.,1.,0.],[s,0.,c]]);world[:,2]+=4.1
        projected=world[:,:2]/world[:,2:3]*1.35
        nodes=np.column_stack((projected,self.radius*1.35/world[:,2],world[:,2]))
        shapes=np.column_stack((1.+.45*(ids%3)/2.,.17*np.sin(ids*2.3)+phase*.008,heat+energy*(.08+.18*(.5+.5*np.sin(phase*.43-ids*.63))),ids%3))
        paths=np.zeros((12,17,3));f=self.f[:,None]
        for row,(a,b) in enumerate(links):
            start,end=world[a],world[b];delta=end-start;side=np.array([-delta[1],delta[0],0.]);side/=max(np.linalg.norm(side),1e-8)
            seed=(row*31+self.seed%97)*.17
            jag=(np.sin(self.f*27.+seed)*.020+np.sin(self.f*55.+seed*.7)*.012)*(.3+energy)+meta[row,0]*.045*np.sin(self.f*73.+seed)
            # Temporary relays lift away from the quieter inked chart path, rooted at both ends.
            if row>=8:jag+=.045*np.sin(self.f*np.pi)
            paths[row]=start[None,:]*(1-f)+end[None,:]*f+side[None,:]*jag[:,None]*np.sin(self.f*np.pi)[:,None]
        data=np.empty((12,17,4),dtype='f4');data[:,:,:2]=paths[:,:,:2]/np.maximum(paths[:,:,2:3],.5)*1.35;data[:,:,2]=1./np.maximum(paths[:,:,2],.5);data[:,:,3]=self.f
        bounds=np.concatenate((data[:,:,:2].min(axis=1),data[:,:,:2].max(axis=1)),axis=1)
        group_points=data[:,self.groups,:2];groups=np.concatenate((group_points.min(axis=2),group_points.max(axis=2)),axis=-1)
        bounds[~active]=1000.;groups[~active]=1000.;self.data=data
        return data.tobytes(),tuple(map(tuple,bounds)),tuple(map(tuple,groups.reshape(48,4))),tuple(map(tuple,nodes)),tuple(map(tuple,shapes)),tuple(map(tuple,meta))


class ArcStage:
    """One small lazy scene pass, retaining the existing shared renderer/director."""
    def __init__(self,ctx,vertices,vertex_shader,source_name="arc_constellation.frag",texture_unit=6):
        from pathlib import Path
        import moderngl
        self.ctx=ctx;self.texture=None;self.fbo=None;self.size=None;self.texture_unit=texture_unit
        source=(Path(__file__).parent/'shaders'/source_name).read_text()
        import time
        began=time.perf_counter();self.program=ctx.program(vertex_shader=vertex_shader,fragment_shader=source);self.program_seconds=time.perf_counter()-began
        self.vao=ctx.simple_vertex_array(self.program,vertices,'in_position')
        if 'u_arc_paths' in self.program:self.program['u_arc_paths'].value=5
    def draw(self,size):
        import moderngl
        if size[0] <= 0 or size[1] <= 0:
            return
        if self.size!=size:
            if self.fbo is not None:self.fbo.release();self.texture.release()
            self.texture=self.ctx.texture(size,4,dtype='f2')
            self.texture.filter=(moderngl.LINEAR,moderngl.LINEAR);self.texture.repeat_x=self.texture.repeat_y=False
            self.fbo=self.ctx.framebuffer([self.texture]);self.size=size
        self.fbo.use();self.ctx.viewport=(0,0,*size);self.program['u_resolution'].value=tuple(map(float,size))
        self.vao.render(mode=moderngl.TRIANGLE_STRIP);self.texture.use(location=self.texture_unit)
    def release(self):
        if self.fbo is not None:self.fbo.release();self.texture.release();self.fbo=None;self.texture=None
        self.vao.release();self.program.release();self.size=None
