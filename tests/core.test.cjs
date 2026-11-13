const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'), vm=require('node:vm');
const html=fs.existsSync('index.html')?fs.readFileSync('index.html','utf8'):'';
const script=html.match(/<script id="world-core">([\s\S]*?)<\/script>/)?.[1];
const context={};vm.createContext(context);if(script)vm.runInContext(script,context);
test('core is embedded in the offline HTML',()=>assert.ok(context.WorldCore,'WorldCore missing'));
test('ring remembers a period beyond local context and detects a break',()=>{
 assert.ok(context.WorldCore,'WorldCore missing');const r=new context.WorldCore.Organ();let out;
 for(let t=0;t<700;t++)out=r.step(Array.from({length:8},(_,i)=>t%23===i*2?1:0));
 assert.ok(out.laps.includes(23));assert.ok(out.surprise<.01);
 out=r.step(new Array(8).fill(1));assert.ok(out.mismatch>.4);
});
test('silence does not invent an echo',()=>{
 assert.ok(context.WorldCore,'WorldCore missing');const r=new context.WorldCore.Organ();let out;
 for(let t=0;t<300;t++)out=r.step(new Array(8).fill(0));assert.equal(out.echo.reduce((a,b)=>a+b,0),0);
});
test('weather fixtures repeat exactly and differ from one another',()=>{
 assert.ok(context.WorldCore,'WorldCore missing');const {weather}=context.WorldCore;
 for(let t=0;t<300;t++)assert.deepEqual(weather(t,0),weather(t,0));
 assert.notDeepEqual(weather(24,0),weather(24,1));
});
test('transport conserves mass and remains nonnegative under strong velocity',()=>{
 assert.ok(context.WorldCore,'WorldCore missing');const {transportReference}=context.WorldCore;
 let a=Array.from({length:64},(_,i)=>(i%7)*.1);const m=a.reduce((x,y)=>x+y,0);
 for(let t=0;t<200;t++)a=transportReference(a,8,(i)=>[Math.sin(i+t)*2,Math.cos(i-t)*2]);
 assert.ok(a.every(x=>x>=0));assert.ok(Math.abs(a.reduce((x,y)=>x+y,0)-m)<1e-10);
});
test('spectrum resolves low and high tones into the correct broad bands',()=>{
 assert.equal(typeof context.WorldCore.features,'function');const {features}=context.WorldCore,rate=24000;
 for(const [hz,band] of [[130,1],[1040,4],[4160,6]]){
  const a=Float32Array.from({length:2048},(_,i)=>.3*Math.sin(2*Math.PI*hz*i/rate));const f=features(a,rate,0);
  assert.equal(f.indexOf(Math.max(...f)),band);assert.ok(f[band]>.2);
 }
});
test('recording validator rejects malformed and unsorted event state',()=>{
 assert.equal(typeof context.WorldCore.validateTape,'function');const {validateTape}=context.WorldCore;
 const d={version:1,resolution:192,seed:1,structured:1,totalTicks:8,frames:[Array(8).fill(.2),Array(8).fill(.4)],initial:{forces:'freeze',matter:'live',organ:0},events:[]};
 assert.doesNotThrow(()=>validateTape(d));
 for(const events of [[{tick:2,type:'organ',value:5}],[{tick:2,type:'band',band:9,value:1}],[{tick:3,type:'rock',u:.5,v:.5},{tick:1,type:'rock',u:.5,v:.5}]])assert.throws(()=>validateTape({...d,events}));
 assert.throws(()=>validateTape({...d,frames:[]}));
});
test('decoded song becomes a repeatable feature score',async()=>{
 assert.equal(typeof context.WorldCore.scoreAudio,'function');const {scoreAudio}=context.WorldCore;
 const pcm=Float32Array.from({length:24000},(_,i)=>.3*Math.sin(2*Math.PI*520*i/24000));
 const score=await scoreAudio(pcm,24000,1,()=>Promise.resolve());
 assert.equal(score.length,8);assert.ok(score.every(a=>a.length===8&&a[3]>.2));
 assert.deepEqual(score,await scoreAudio(pcm,24000,1,()=>Promise.resolve()));
});
