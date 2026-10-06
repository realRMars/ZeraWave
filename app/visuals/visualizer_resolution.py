"""One explicit render-pixel policy, independent of presentation geometry."""
PRESETS = ((640,360),(1280,720),(1920,1080))

def failure_message(exc):
    detail=str(exc).splitlines()[0] if str(exc) else type(exc).__name__
    return 'Resolution unchanged: '+detail[:160]

def validate(policy, limit=16384):
    if policy is None:return None  # preserve the existing Quality scale
    if not isinstance(policy,dict):raise ValueError('Invalid visualizer resolution')
    if policy.get('mode')=='native':return {'mode':'native'}
    size=policy.get('size');choice=policy.get('choice','Custom')
    if policy.get('mode')!='fixed' or not isinstance(size,(list,tuple)) or len(size)!=2:
        raise ValueError('Choose Native or a width and height')
    if any(type(v) is not int or not 1<=v<=limit for v in size):
        raise ValueError(f'Width and height must be whole pixels from 1 to {limit}')
    if choice!='Custom' and (tuple(size) not in PRESETS or choice!=f'{size[0]}×{size[1]}'):
        raise ValueError('Invalid resolution preset')
    return {'mode':'fixed','size':list(size),'choice':choice}

def internal_size(policy, viewport, legacy_scale=1.):
    if policy and policy['mode']=='fixed':return tuple(policy['size'])
    scale=1. if policy else legacy_scale
    return tuple(max(1,round(v*scale)) for v in viewport)

def fit_rect(image,viewport):
    scale=min(viewport[0]/image[0],viewport[1]/image[1])
    width=max(1,round(image[0]*scale));height=max(1,round(image[1]*scale))
    return ((viewport[0]-width)//2,(viewport[1]-height)//2,width,height)
