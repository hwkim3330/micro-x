"""Original Micro X paint masks in assembly mm. Design data: root LICENSE.
Eye graphics are paint/multicolor-finish intent, not additional loose components.
"""
import numpy as np
def paint(mesh,name,color):
 colors=np.tile((np.array(color)*255).astype(np.uint8),(len(mesh.vertices),1))
 if name.startswith('eye_'):
  sign=1 if name.endswith('left') else -1
  x,y,z=mesh.vertices.T
  outward=sign*y>31
  # Large dark pupil looking slightly forward, with two highlights.
  pupil=outward&(((x-27)/9)**2+((z-250)/10)**2<1)
  colors[pupil]=[18,30,28,255]
  highlight=pupil&(((x-24.5)/2.8)**2+((z-253.5)/3.2)**2<1)
  glint=pupil&(((x-30)/1.4)**2+((z-246.5)/1.4)**2<1)
  colors[highlight|glint]=[252,252,246,255]
 if name=='torso_shell':
  x,y,z=mesh.vertices.T
  # Softer belly tone below the equator, painted, not a separate part.
  belly=(z<128)&(np.abs(y)<26)
  colors[belly]=[241,214,186,255]
 mesh.visual.vertex_colors=colors
 return mesh
