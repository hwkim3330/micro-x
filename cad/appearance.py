"""Original Micro X paint masks in assembly mm. Design data: root LICENSE.
Eye graphics are paint/multicolor-finish intent, not additional loose components.
"""
import numpy as np
def paint(mesh,name,color):
 colors=np.tile((np.array(color)*255).astype(np.uint8),(len(mesh.vertices),1))
 if name.startswith('eye_'):
  sign=1 if name.endswith('left') else -1
  x,y,z=mesh.vertices.T
  front=sign*y>31
  pupil=front&(((x-72)/8.1)**2+((z-243)/8.6)**2<1)
  colors[pupil]=[13,24,21,255]
  highlight=pupil&(((x-69)/2.1)**2+((z-247)/2.4)**2<1)
  glint=pupil&(((x-75.5)/.9)**2+((z-240.5)/.9)**2<1)
  colors[highlight|glint]=[251,252,240,255]
 mesh.visual.vertex_colors=colors
 return mesh
