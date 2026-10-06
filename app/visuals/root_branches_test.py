"""Root cache versus procedural GPU output, direct draws and target ownership."""
import argparse,json,os,sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio'),str(ROOT/'app')]
import glfw,moderngl
from renderer import Renderer,VERTEX_SHADER
from prepared_program import PreparedProgram
from analyzer import AudioAnalyzer
from studio_color_link import configure_colors
from starfield_tuning import configure as configure_tuning


def run(output):
    output.mkdir(parents=True,exist_ok=False)
    os.environ.update(ZERAWAVE_AUDIO_RUN='root-cache-test',ZERAWAVE_AUDIO_SESSION='fixed')
    renderer=Renderer(640,360,seed=7301)
    renderer.debug_state=12;renderer.startup_callback=lambda phase:print(phase,flush=True)
    read,write=os.pipe()
    with patch('sys.stdin',SimpleNamespace(fileno=lambda:read)):configure_colors(renderer,{},True)
    configure_tuning(renderer,AudioAnalyzer(),normal=True)
    init=glfw.init
    def hidden():
        value=init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);glfw.window_hint(glfw.FOCUSED,glfw.FALSE);return value
    procedural=None;target=None;rows=[]
    try:
        with patch.object(glfw,'init',hidden):renderer.create()
        renderer.startup_callback=None;glfw.swap_interval(0)
        # The original procedural equations remain available to raw shader tools.
        procedural=PreparedProgram(renderer.ctx,renderer.vertices,VERTEX_SHADER,renderer.audio_uniform_contract.source)
        target=renderer.ctx.simple_framebuffer((640,360))
        texture=renderer.root_branch_stage.texture
        identity=texture.glo
        for scope in ('held','planet-boundary'):
            renderer.debug_state=12 if scope=='held' else 0
            if scope!='held':renderer.configure_transitions(dict(pair=[12,5],hold=1.,duration=2.,isolate={'pair':'tr_branch_iris'}))
            for index,gain in enumerate((1.,.73,-1.3,0.)):
                renderer.parameters.flux=.71;renderer.parameters.scale=.45
                renderer.render(2.+index*.1)
                ids=(12,5);a=[(1.,1.,1.,1.)]*32;b=list(a);a[16]=(gain,1.,1.,1.)
                renderer.program['u_audio_forms'].value=ids
                renderer.program['u_form_audio_a'].value=a;renderer.program['u_form_audio_b'].value=b
                renderer.audio_uniform_contract.upload(renderer,ids,a,b,0,[(1.,1.,1.,1.)]*32)
                # Exercise callers that edit uniform clocks then draw directly.
                renderer.program['u_time'].value+=.321
                renderer.program['u_planet_time'].value+=.789
                for name,state in renderer.program.uniforms.items():
                    if name in procedural and state.stored is not None:procedural[name].value=state.value
                target.use();renderer.ctx.viewport=(3,5,620,340)
                renderer.vao.render(mode=moderngl.TRIANGLE_STRIP)
                assert renderer.ctx.fbo.glo==target.glo and renderer.ctx.viewport==(3,5,620,340)
                cached=np.frombuffer(target.read(components=3,alignment=1),np.uint8).copy()
                procedural.render(mode=moderngl.TRIANGLE_STRIP)
                original=np.frombuffer(target.read(components=3,alignment=1),np.uint8).copy()
                # Ignore untouched border storage outside the viewport.
                cached=cached.reshape(360,640,3)[5:345,3:623]
                original=original.reshape(360,640,3)[5:345,3:623]
                difference=np.abs(cached.astype(np.int16)-original.astype(np.int16))
                row={'scope':scope,'gain':gain,'max_channel_difference':int(difference.max()),'mean_difference':float(difference.mean())}
                rows.append(row);assert difference.max()<=1,row
                assert texture.glo==identity and texture.size==(31,4)
                renderer.ctx.screen.use();renderer.ctx.viewport=(0,0,640,360)
        assert renderer.root_branch_stage is not None
    finally:
        if target is not None:target.release()
        if procedural is not None:procedural.release()
        renderer.close();os.close(write)
        assert renderer.root_branch_stage is None
        (output/'result.json').write_text(json.dumps({'cases':rows,'texture_bytes':31*4*4*4,'checks':['procedural GPU parity','encoded gains','independent clock variants','direct uniform/VAO draws','owned framebuffer/viewport restoration','fixed resource across draws','release'],'class':'640x360 synthetic GPU preservation; not performance or listening'},indent=2))
    print('Root branch GPU contracts PASS',len(rows),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args().output)
