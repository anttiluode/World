"""Execute the HTML's shader bodies through desktop OpenGL/EGL, without a browser.

Requires numpy, moderngl, Pillow. This is NOT WebGL/browser or RTX verification.
Only the GLSL version/ES precision declarations are translated; equations are read
from index.html. Outputs a machine-readable ledger and a rendered scene.
"""
from pathlib import Path
import json, re, subprocess, time
import numpy as np
import moderngl
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
html=(ROOT/'index.html').read_text()
def quoted(name):
    return re.search(r'const '+name+r'=`([\s\S]*?)`;',html).group(1)
def glsl(s):
    return re.sub(r'precision highp (?:float|int);','',s.replace('#version 300 es','#version 330'))
ctx=moderngl.create_standalone_context(backend='egl')
vs=glsl(quoted('VS')); head=quoted('HEAD')
part=html.split('const shaders={',1)[1].split('\n};',1)[0]
programs={k:ctx.program(vertex_shader=vs,fragment_shader=glsl(head+s)) for k,s in re.findall(r'(\w+):HEAD\+`([\s\S]*?)`',part)}
vaos={k:ctx.vertex_array(p,[]) for k,p in programs.items()}
mesh=ctx.program(vertex_shader=glsl(quoted('meshVS')),fragment_shader=glsl(quoted('meshFS')))

# Reuse the actual JavaScript organ and weather generators, not a Python port.
script=r'''const fs=require('fs'),vm=require('vm');let h=fs.readFileSync('index.html','utf8');let c={};vm.createContext(c);vm.runInContext(h.match(/<script id="world-core">([\s\S]*?)<\/script>/)[1],c);let all=[];for(let v=0;v<2;v++){let o=new c.WorldCore.Organ(),rows=[];for(let t=0;t<2000;t++){let b=c.WorldCore.weather(t,v),r=o.step(b);rows.push([b,r.echo,r.mismatch]);}all.push(rows);}process.stdout.write(JSON.stringify(all));'''
scores=json.loads(subprocess.check_output(['node','-e',script],cwd=ROOT))

def target(n):
    t=ctx.texture((n,n),4,dtype='f4');t.filter=(moderngl.NEAREST,moderngl.NEAREST);t.repeat_x=t.repeat_y=False
    return t,ctx.framebuffer([t])
def put(p,k,v):
    if k in p:
        if isinstance(v,(list,tuple,np.ndarray)):p[k].value=tuple(v)
        else:p[k].value=v
class Sim:
    def __init__(self,n=64,seed=2718,structured=1):
        self.n=n;self.seed=seed;self.structured=structured
        self.geo=[target(n),target(n)];self.mat=[target(n),target(n)];self.force=[target(n),target(n)];self.flux=target(n);self.reset()
    def draw(self,name,target,mode=0,brush=(0,0,0)):
        p=programs[name];target[1].use();ctx.viewport=(0,0,self.n,self.n);ctx.disable(moderngl.DEPTH_TEST)
        for i,(k,t) in enumerate([('geo',self.geo[0]),('mat',self.mat[0]),('force',self.force[0]),('flux',self.flux)]):t[0].use(i);put(p,k,i)
        for k,v in [('N',self.n),('seed',self.seed),('tick',self.tick),('structured',self.structured),('mode',mode),('brush',brush),('bands',self.bands),('echo',self.echo),('surprise',self.surprise),('organOn',self.organ_on)]:put(p,k,v)
        vaos[name].render(vertices=3)
    def reset(self):
        self.tick=0;self.bands=[0]*8;self.echo=[0]*8;self.surprise=0.;self.organ_on=1.;self.fm=0;self.mm=0
        self.draw('seed',self.geo[1]);self.geo.reverse();self.draw('init',self.mat[1]);self.mat.reverse()
        for t in self.force:t[1].clear(0,0,0,0)
        self.flux[1].clear(0,0,0,0)
    def step(self,variant=0):
        self.bands,self.echo,self.surprise=scores[variant][self.tick//4]
        self.draw('force',self.force[1],self.fm);self.force.reverse();self.draw('flux',self.flux);self.draw('matter',self.mat[1],self.mm);self.mat.reverse();self.tick+=1
    def run(self,n,variant=0):
        for _ in range(n):self.step(variant)
    def read(self,name='mat'):
        return np.frombuffer(getattr(self,name)[0][0].read(),np.float32).reshape(self.n,self.n,4).copy()
    def write(self,name,data):getattr(self,name)[0][0].write(data.astype('f4').tobytes())
    def intervene(self,u=.5,v=.5,kind=0):
        a=self.geo if kind==0 else self.mat;self.draw('brush',a[1],kind,(u,v,0));a.reverse()
    def close(self):
        for arr in (self.geo,self.mat,self.force,[self.flux]):
            for t,f in arr:f.release();t.release()

report={'backend':ctx.info['GL_RENDERER'],'method':'Exact HTML shader bodies, GLSL ES 300 version/precision translated to desktop GLSL 330; EGL, not a browser.','grid':64,'checks':[]}
def check(name,ok,**values):
    row={'name':name,'pass':bool(ok),**values};report['checks'].append(row);print(json.dumps(row),flush=True)
def diff(a,b,channels=None):
    d=np.abs(a.astype('f8')-b.astype('f8'))
    if channels is not None:d=d[...,channels]
    return {'mean':float(d.mean()),'max':float(d.max())}
def mass(a):return float(a[...,:2].astype('f8').sum())

start=time.time();a=Sim();b=Sim();initial=mass(a.read());a.run(320);b.run(320);ma=a.read();d=diff(ma,b.read());check('Deterministic feature replay',d['max']==0,**d)
check('Finite nonnegative material and finite forces',np.isfinite(ma).all() and np.isfinite(a.read('force')).all() and ma.min()>=0,minimum=float(ma.min()))
err=abs(mass(ma)-initial)/initial;check('Sediment mass conservation',err<1e-5,initial=initial,final=mass(ma),relativeError=err)
b.reset();b.run(320,1);d=diff(ma,b.read(),[0,1]);check('Different weather changes material',d['mean']>1e-5,**d)
b.structured=0;b.reset();b.run(320);d=diff(ma,b.read(),[0,1]);df=diff(a.read('force'),b.read('force'));check('Seed changes evolved matter and forces',d['mean']>1e-5 and df['mean']>1e-5,material=d,force=df)
b.structured=1;b.reset();b.fm=2;b.run(320);d=diff(ma,b.read(),[0,1]);check('Removing forces changes deposition',d['mean']>1e-5,**d)
b.reset();old=b.read();b.mm=1;b.run(160);d=diff(old,b.read());check('Frozen matter stays exact',d['max']==0,**d)
b.reset();b.run(80);old=b.read('force');b.fm=1;b.run(80);d=diff(old,b.read('force'));check('Frozen forces stay exact',d['max']==0,**d)
b.fm=2;b.run(1);check('Killed forces are zero',np.all(b.read('force')==0))
a.reset();b.reset();a.run(120);b.run(120);b.intervene();a.run(100);b.run(100);yy,xx=np.mgrid[0:64,0:64];outside=np.hypot((xx+.5)/64-.5,(yy+.5)/64-.5)>.12;dm=diff(a.read()[outside],b.read()[outside],[0,1]);df=diff(a.read('force')[outside],b.read('force')[outside],[0,1]);check('Rock effects propagate beyond brush radius',dm['mean']>1e-10 and df['mean']>1e-9,material=dm,force=df,brushRadius=.1,measuredBeyond=.12)
a.reset();b.reset();a.run(200);b.run(200,1);aa=a.read();bb=b.read();past=diff(aa,bb,[2]);bb[...,[0,1,3]]=aa[...,[0,1,3]];b.write('mat',bb);b.write('force',a.read('force'));now=diff(a.read(),b.read(),[0,1,3]);a.tick=b.tick=0;a.run(160);b.run(160);d=diff(a.read(),b.read(),[0,1]);check('Matched surface with different past compaction has different future transport',past['mean']>1e-7 and now['max']==0 and d['mean']>1e-8,past=past,matched=now,future=d)
a.reset();b.reset();b.organ_on=0;a.run(400);b.run(400);d=diff(a.read(),b.read(),[0,1]);check('Organ affects matter',d['mean']>1e-6,**d)
a.close();b.close()

# Production-sized numerical stress run and material-derived render. No screenshot
# of a browser is fabricated; the PNG is explicitly an EGL render of these shaders.
world=Sim(192);t=time.perf_counter();world.run(1600);ctx.finish();report['productionGrid']={'grid':192,'steps':1600,'elapsedSeconds':time.perf_counter()-t}
check('Production grid stays finite after 1600 steps',np.isfinite(world.read()).all() and np.isfinite(world.read('force')).all())
def render_world(world,path,w=1360,h=900):
    n=world.n;indices=[]
    for y in range(n-1):
        for x in range(n-1):
            k=y*n+x;indices.extend([k,k+n,k+1,k+1,k+n,k+n+1])
    ib=ctx.buffer(np.array(indices,'u4').tobytes());vao=ctx.vertex_array(mesh,[],index_buffer=ib,index_element_size=4)
    fb=ctx.simple_framebuffer((w,h));fb.use();fb.clear(.025,.043,.05,1,depth=1);ctx.enable(moderngl.DEPTH_TEST);ctx.disable(moderngl.CULL_FACE)
    yaw=.48;pitch=.72;dist=12.5;eye=np.array([np.sin(yaw)*np.cos(pitch)*dist,np.sin(pitch)*dist,np.cos(yaw)*np.cos(pitch)*dist]);forward=np.array([0,.1,0])-eye;forward/=np.linalg.norm(forward);right=np.cross(forward,[0,1,0]);right/=np.linalg.norm(right);up=np.cross(right,forward)
    for i,(k,a) in enumerate([('geo',world.geo),('mat',world.mat),('force',world.force)]):a[0][0].use(i);put(mesh,k,i)
    for k,v in [('N',n),('eye',eye),('rightV',right),('upV',up),('forwardV',forward),('aspect',w/h),('picking',0)]:put(mesh,k,v)
    vao.render();Image.frombytes('RGB',(w,h),fb.read(components=3)).transpose(Image.Transpose.FLIP_TOP_BOTTOM).save(path)
    fb.release();vao.release();ib.release()
out=ROOT/'results';out.mkdir(exist_ok=True);render_world(world,out/'stage1-egl.png');world.close()
report['elapsedSeconds']=time.time()-start;report['browser']='Preview browser did not provide the required WebGL2/float setup; not verified.';report['rtx3060']='Not available; not measured.'
(out/'gpu-egl.json').write_text(json.dumps(report,indent=2)+'\n')
print('REPORT',out/'gpu-egl.json')
raise SystemExit(0 if all(c['pass'] for c in report['checks']) else 1)
