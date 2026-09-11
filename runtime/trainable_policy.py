"""Load the official ONNX actor into the same differentiable MLP architecture.
No robot assets are used. Original weights stay in the local cache.
"""
import numpy as np,onnx,torch
from onnx import numpy_helper
from torch import nn
class Actor(nn.Module):
    def __init__(self,path):
        super().__init__();graph=onnx.load(path).graph;values={v.name:numpy_helper.to_array(v).copy() for v in graph.initializer}
        expected=['Sub','Div','Gemm','Elu','Gemm','Elu','Gemm','Elu','Gemm']
        if [n.op_type for n in graph.node]!=expected:raise ValueError('Unsupported policy graph; refusing approximate conversion')
        divisor=graph.node[1].input[1]
        self.register_buffer('mean',torch.tensor(values['obs_normalizer._mean']))
        self.register_buffer('divisor',torch.tensor(values[divisor]))
        layers=[]
        for index in [0,2,4,6]:
            weight=values[f'mlp.{index}.weight'];layer=nn.Linear(weight.shape[1],weight.shape[0]);layer.weight.data.copy_(torch.from_numpy(weight));layer.bias.data.copy_(torch.from_numpy(values[f'mlp.{index}.bias']));layers.append(layer)
            if index!=6:layers.append(nn.ELU())
        self.mlp=nn.Sequential(*layers)
    def forward(self,observation):return self.mlp((observation-self.mean)/self.divisor)
