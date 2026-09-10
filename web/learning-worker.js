import {train,evaluate,ENV} from './learning-core.js';
self.onmessage=async({data})=>{
  try {
    let last;const history=[];
    for(const result of train(data)){last=result;history.push({generation:result.generation,loss:result.loss});self.postMessage({type:'progress',...result});await new Promise(r=>setTimeout(r,0));}
    self.postMessage({type:'complete',policy:{schema:'micro-x-policy-v1',environment:ENV,algorithm:'cem-log-pd',joint:'virtual_jaw',angleRangeDegrees:[0,20],weights:last.weights,settings:data,history,heldout:evaluate(last.weights,true),hardwareValidated:false}});
  } catch(error){self.postMessage({type:'error',message:error.message});}
};
