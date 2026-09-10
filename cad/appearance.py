"""Original Micro X paint masks in assembly mm. Design data: root LICENSE.
Eye graphics are paint/multicolor-finish intent, not additional loose components.
"""
import numpy as np
def paint(mesh,name,color):
 colors=np.tile((np.array(color)*255).astype(np.uint8),(len(mesh.vertices),1))
 if name.startswith('eye_'):
  sign=1 if name.endswith('left') else -1
  x,y,z=mesh.vertices.T
  front=sign*y>36
  pupil=front&(((x-78)/9.8)**2+((z-222)/10.5)**2<1)
  colors[pupil]=[13,24,21,255]
  highlight=pupil&(((x-74)/2.8)**2+((z-227)/3.1)**2<1)
  glint=pupil&(((x-82)/1.2)**2+((z-218)/1.2)**2<1)
  colors[highlight|glint]=[251,252,240,255]
 mesh.visual.vertex_colors=colors
 return mesh
