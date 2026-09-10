// MIT. Independent normalized 1-DOF teaching environment, not hardware dynamics.
export const ENV='micro-x-virtual-jaw-v1';
export const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
export function rng(seed){let x=seed>>>0;return()=>{x=(1664525*x+1013904223)>>>0;return(x+.5)/4294967296;};}
export function advance(state,target,weights,dt=1/60){
  const action=clamp(Math.exp(weights[0])*(target-state.q)-Math.exp(weights[1])*state.v,-3,3);
  let v=state.v+(action-.12*state.v)*dt,q=state.q+v*dt;
  if(q<0||q>1){q=clamp(q,0,1);v=0;}
  return {q,v,action};
}
export function evaluate(weights,heldout=false){
  const targets=heldout?[.23,.63,.92]:[.15,.45,.75,.9];let error=0,effort=0,n=0;const trace=[];
  for(const target of targets){let state={q:1-target,v:0};
    for(let i=0;i<240;i++){state=advance(state,target,weights);error+=(target-state.q)**2;effort+=state.action**2;n++;if(heldout&&target===.63&&i%3===0)trace.push({t:i/60,target,q:state.q});}
  }
  return {loss:error/n+.0005*effort/n,rmseDegrees:Math.sqrt(error/n)*20,trace};
}
export function* train({seed=42,generations=40,population=32}={}){
  if(!Number.isInteger(seed)||seed<0||seed>4294967295||!Number.isInteger(generations)||generations<1||generations>100||!Number.isInteger(population)||population<8||population>64)throw Error('Invalid training settings');
  const random=rng(seed),normal=()=>Math.sqrt(-2*Math.log(random()))*Math.cos(2*Math.PI*random());
  let mean=[0,0],std=[1.5,1.5],best={weights:[0,0],...evaluate([0,0])};
  for(let generation=1;generation<=generations;generation++){
    const candidates=[best];
    for(let k=1;k<population;k++){const weights=mean.map((m,i)=>clamp(m+std[i]*normal(),-4,5));candidates.push({weights,...evaluate(weights)});}
    candidates.sort((a,b)=>a.loss-b.loss);best=candidates[0];const elite=candidates.slice(0,Math.max(2,Math.floor(population/5)));
    mean=mean.map((_,i)=>elite.reduce((s,c)=>s+c.weights[i],0)/elite.length);
    std=std.map((_,i)=>Math.max(.05,Math.sqrt(elite.reduce((s,c)=>s+(c.weights[i]-mean[i])**2,0)/elite.length)));
    yield {generation,weights:[...best.weights],loss:best.loss,rmseDegrees:best.rmseDegrees};
  }
}
export function validatePolicy(data){
  if(!data||data.schema!=='micro-x-policy-v1'||data.environment!==ENV||data.algorithm!=='cem-log-pd'||data.joint!=='virtual_jaw'||data.angleRangeDegrees?.length!==2||data.angleRangeDegrees[0]!==0||data.angleRangeDegrees[1]!==20||!Array.isArray(data.weights)||data.weights.length!==2||!data.weights.every(x=>typeof x==='number'&&Number.isFinite(x)&&x>=-4&&x<=5))throw Error('이 실험실의 가상 턱 정책 파일만 불러올 수 있습니다.');
  return [...data.weights];
}
