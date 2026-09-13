"""Original Micro X paint masks in assembly mm. Design data: root LICENSE.
Eye graphics are paint/multicolor-finish intent, not additional loose components.
"""
import numpy as np
def paint(mesh,name,color):
 colors=np.tile((np.array(color)*255).astype(np.uint8),(len(mesh.vertices),1))
 if name=='skull':
  x,y,z=mesh.vertices.T
  # Painted eye and brow marks over the widest part of the skull: finish only, nothing to break off.
  for sgn in (1,-1):
   side=sgn*y>32
   eye=side&(((x-22)/10)**2+((z-252)/10)**2<1)
   colors[eye]=[18,30,28,255]
   glint=side&(((x-18)/3)**2+((z-256)/3)**2<1)
   colors[glint]=[252,252,246,255]
   brow=side&(((x-22)/15)**2+((z-265)/4.5)**2<1)
   colors[brow]=[88,120,101,255]
 if name=='torso_shell':
  x,y,z=mesh.vertices.T
  # Softer belly tone below the equator, painted, not a separate part.
  belly=(z<136)&(np.abs(y)<30)&(x>-40)
  colors[belly]=[250,240,202,255]
 mesh.visual.vertex_colors=colors
 return mesh
