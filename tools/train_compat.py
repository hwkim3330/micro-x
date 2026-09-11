"""CPU PPO fine-tuning harness for X, warm-started from the official actor.
Matches actor and IO; this is NOT parity with the full upstream mjlab recipe.
"""
from pathlib import Path
import argparse,hashlib,json,sys,time
import numpy as np,torch,onnxruntime as ort
from torch import nn
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'runtime'))
from compat_env import Environment
from trainable_policy import Actor
p=argparse.ArgumentParser();p.add_argument('--updates',type=int,default=10);p.add_argument('--steps',type=int,default=256);p.add_argument('--seed',type=int,default=42);args=p.parse_args()
if not 1<=args.updates<=10000 or not 32<=args.steps<=4096:raise ValueError('Invalid training workload')
torch.set_num_threads(2);torch.manual_seed(args.seed);rng=np.random.default_rng(args.seed)
source=R/'.cache/compat/alpha_walking.onnx';actor=Actor(source);critic=nn.Sequential(nn.Linear(61,128),nn.ELU(),nn.Linear(128,1));log_std=nn.Parameter(torch.full((14,),-2.5));parameters=list(actor.parameters())+list(critic.parameters())+[log_std];optimizer=torch.optim.Adam(parameters,lr=1e-5)
session=ort.InferenceSession(str(source),providers=['CPUExecutionProvider']);samples=rng.normal(0,.2,(128,61)).astype(np.float32)
with torch.no_grad():converted=actor(torch.from_numpy(samples)).numpy()
reference=np.concatenate([session.run(None,{session.get_inputs()[0].name:row[None]})[0] for row in samples]);max_error=float(np.max(np.abs(converted-reference)))
if max_error>1e-5:raise ValueError('Actor conversion parity failed')
env=Environment();obs=env.reset(args.seed,(.1,0,0));history=[];episode_steps=0;started=time.time()
initial=[p.detach().clone() for p in actor.parameters()]
for update in range(args.updates):
    observations=[];actions=[];old_logp=[];values=[];rewards=[];dones=[];falls=0
    for _ in range(args.steps):
        x=torch.tensor(obs);observations.append(x)
        with torch.no_grad():
            distribution=torch.distributions.Normal(actor(x).squeeze(0),log_std.exp());action=distribution.sample();value=critic(x).squeeze();lp=distribution.log_prob(action).sum()
        previous_x=float(env.data.qpos[0]);next_obs,fallen,info=env.step(action.numpy());episode_steps+=1
        vx=(float(env.data.qpos[0])-previous_x)/.02;target=float(env.policy.vel_cmd[0]);reward=float(np.exp(-((vx-target)/.2)**2)+.5*np.cos(np.radians(info['tilt_degrees']))-.001*np.square(action.numpy()).sum()-(5 if fallen else 0))
        done=fallen or episode_steps>=500;actions.append(action);old_logp.append(lp);values.append(value);rewards.append(reward);dones.append(done)
        if done:falls+=int(fallen);episode_steps=0;obs=env.reset(int(rng.integers(0,100000)),(float(rng.choice([0,.1,.3])),0,0))
        else:obs=next_obs
    with torch.no_grad():next_value=critic(torch.tensor(obs)).squeeze()
    advantage=torch.zeros(args.steps);gae=0.
    for i in range(args.steps-1,-1,-1):
        mask=1-float(dones[i]);delta=rewards[i]+.99*next_value*mask-values[i];gae=delta+.99*.95*mask*gae;advantage[i]=gae;next_value=values[i]
    returns=advantage+torch.stack(values);advantage=(advantage-advantage.mean())/(advantage.std()+1e-8);x=torch.stack(observations);a=torch.stack(actions);old=torch.stack(old_logp)
    for _ in range(4):
        distribution=torch.distributions.Normal(actor(x),log_std.exp());ratio=(distribution.log_prob(a).sum(-1)-old).exp();policy_loss=-torch.minimum(ratio*advantage,ratio.clamp(.8,1.2)*advantage).mean();value_loss=(critic(x).squeeze(-1)-returns).square().mean();loss=policy_loss+.5*value_loss-.001*distribution.entropy().mean();optimizer.zero_grad();loss.backward();nn.utils.clip_grad_norm_(parameters,.5);optimizer.step()
    row=dict(update=update+1,mean_reward=round(float(np.mean(rewards)),4),falls=falls,loss=float(loss.detach()));history.append(row);print(row,flush=True)
dest=R/'.cache/checkpoints';dest.mkdir(parents=True,exist_ok=True)
torch.save(dict(actor=actor.state_dict(),critic=critic.state_dict(),log_std=log_std.detach(),optimizer=optimizer.state_dict(),seed=args.seed,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest()),dest/'micro_x_14.pt')
torch.onnx.export(actor,torch.zeros(1,61),str(dest/'micro_x_14.onnx'),input_names=['obs'],output_names=['actions'],opset_version=17,dynamo=False)
exported=ort.InferenceSession(str(dest/'micro_x_14.onnx'),providers=['CPUExecutionProvider'])
with torch.no_grad():expected=actor(torch.tensor(samples[:1])).numpy()
export_error=float(np.max(np.abs(exported.run(None,{'obs':samples[:1]})[0]-expected)));assert export_error<1e-5
report=dict(model_sha256=env.model_sha256,scope='Independent CPU PPO warm-start/fine-tuning smoke run. Same pretrained 61→512→256→128→14 ELU actor and normalization; not full upstream training recipe parity or locomotion acceptance.',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),initial_actor_max_error=max_error,export_max_error=export_error,actor_weights_changed=any(not torch.equal(before,after.detach()) for before,after in zip(initial,actor.parameters())),updates=args.updates,steps_per_update=args.steps,seed=args.seed,elapsed_s=round(time.time()-started,2),history=history,checkpoint_sha256=hashlib.sha256((dest/'micro_x_14.onnx').read_bytes()).hexdigest(),physical_verified=False,upstream_training_recipe_parity=False)
(R/'artifacts/compat_training.json').write_text(json.dumps(report,indent=2)+'\n')
