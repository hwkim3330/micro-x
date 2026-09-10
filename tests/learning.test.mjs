import test from 'node:test';
import assert from 'node:assert/strict';
import {train,evaluate,advance,validatePolicy,ENV} from '../web/learning-core.js';
test('seeded learning improves held-out tracking and is reproducible',()=>{
  const first=[...train()],second=[...train()];assert.deepEqual(first,second);
  const baseline=evaluate([0,0],true),result=evaluate(first.at(-1).weights,true);
  assert.ok(result.rmseDegrees<baseline.rmseDegrees*.7);
  for(let i=1;i<first.length;i++)assert.ok(first[i].loss<=first[i-1].loss);
});
test('virtual travel and action limits hold across changing targets',()=>{
  let state={q:0,v:0};for(let i=0;i<3000;i++){state=advance(state,i%100<50?0:1,[5,-4]);assert.ok(state.q>=0&&state.q<=1);assert.ok(Number.isFinite(state.v));assert.ok(Math.abs(state.action)<=3);}
});
test('foreign, malformed or nonfinite policies cannot execute',()=>{
  const valid={schema:'micro-x-policy-v1',environment:ENV,algorithm:'cem-log-pd',joint:'virtual_jaw',angleRangeDegrees:[0,20],weights:[1,2]};assert.deepEqual(validatePolicy(valid),[1,2]);
  for(const patch of [{environment:'microduck'},{weights:[NaN,1]},{weights:[1,Infinity]},{weights:[1,2,3]},{weights:['1',2]},{angleRangeDegrees:[0,90]},{joint:'hip'},{algorithm:'onnx'}])assert.throws(()=>validatePolicy({...valid,...patch}));
  for(const data of [null,{},[]])assert.throws(()=>validatePolicy(data));
});
test('training workload rejects invalid or unbounded settings',()=>{
  for(const settings of [{generations:0},{generations:101},{population:1000},{seed:-1},{seed:1.5}])assert.throws(()=>[...train(settings)]);
});
