"""Original Micro X paint masks in assembly mm. Design data: root LICENSE.
Eye graphics are paint/multicolor-finish intent, not additional loose components.
"""
import numpy as np
def paint(mesh,name,color):
 colors=np.tile((np.array(color)*255).astype(np.uint8),(len(mesh.vertices),1))
 if name=='skull':
  x,y,z=mesh.vertices.T
  # Painted eye marks beside the muzzle: finish only, no parts to break off.
  for sgn in (1,-1):
   eye=(sgn*y>26)&(((x-26)/7)**2+((z-247)/8)**2<1)
   colors[eye]=[18,30,28,255]
   glint=eye&(((x-24)/2.2)**2+((z-250)/2.5)**2<1)
   colors[glint]=[252,252,246,255]
 if name=='torso_shell':
  x,y,z=mesh.vertices.T
  # Softer belly tone below the equator, painted, not a separate part.
  belly=(z<136)&(np.abs(y)<30)&(x>-40)
  colors[belly]=[250,240,202,255]
 mesh.visual.vertex_colors=colors
 return mesh
