"""Original Micro X paint masks in assembly mm. Design data: root LICENSE.
Eye graphics are paint/multicolor-finish intent, not additional loose components.
"""
import numpy as np
EYE=dict(x=36,z=257,face=57.0,r=10.0) # eye button; set by cad/build.py
def paint(mesh,name,color):
 colors=np.tile((np.array(color)*255).astype(np.uint8),(len(mesh.vertices),1))
 if name=='skull':
  x,y,z=mesh.vertices.T;e=EYE
  face=np.abs(y)>e['face']-1.6                           # the button face and its rounded rim
  rad=np.hypot(x-e['x'],z-e['z'])
  colors[face&(rad<e['r']+0.05)]=[18,30,28,255]
  colors[face&(np.hypot(x-e['x']-3.5,z-e['z']-3.5)<3.0)]=[252,252,246,255]
 if name=='torso_shell':
  x,y,z=mesh.vertices.T
  # Softer belly tone below the equator, painted, not a separate part.
  belly=(z<136)&(np.abs(y)<30)&(x>-40)
  colors[belly]=[250,240,202,255]
 mesh.visual.vertex_colors=colors
 return mesh
