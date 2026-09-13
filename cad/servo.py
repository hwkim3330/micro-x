"""Purchased smart-servo envelope and clevis helpers for the actuated Micro X. mm.

Interface dimensions are those of the ROBOTIS XL330-M288-T class (20 x 34 x 23 body,
horn axis 9.5 mm from the short end, output horn Ø16 with four M2 holes on a Ø12
circle, matching idler pattern on the rear). They are measured purchased-part
interface dimensions, not copied CAD. Verify against the manufacturer drawing before
ordering; see engineering/actuator_interface.json.
"""
import math
import cadquery as cq
import numpy as np

ACROSS=20.0      # body width perpendicular to axis and to the long direction
ALONG=23.0       # body depth along the output axis
LONG=34.0        # body length in the long direction
HORN_OFFSET=9.5  # horn axis to the short end of the body
HORN_R=8.0       # output horn disc radius
HORN_H=3.0       # horn / idler disc height above the body face
HOLE_R=6.0       # radius of the four M2 horn holes
GAP=0.5          # running clearance between horn disc and child plate
FACE=HORN_H+GAP  # pivot plane to servo body face
PLATE=3.0        # clevis plate thickness
MASS_G=18.0

def unit(v):
    v=np.asarray(v,dtype=float);return v/np.linalg.norm(v)

def frame(h,d):
    """Local frame: x = horn direction h, z = long direction d, y = z × x."""
    x=unit(h);z=unit(d);z=unit(z-np.dot(z,x)*x);y=np.cross(z,x);return x,y,z

def to_world(shape,P,h,d):
    x,y,z=frame(h,d);P=np.asarray(P,dtype=float)
    plane=cq.Plane(origin=tuple(P),xDir=tuple(x),normal=tuple(z))
    return cq.Workplane(obj=shape.val().moved(cq.Location(plane)))

def local_box(x0,x1,y0,y1,z0,z1):
    return cq.Workplane('XY').box(x1-x0,y1-y0,z1-z0).translate(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2))

def envelope(P,h,d):
    """Servo body plus horn and idler discs, in world coordinates."""
    body=local_box(-(FACE+ALONG),-FACE,-ACROSS/2,ACROSS/2,-HORN_OFFSET,LONG-HORN_OFFSET).edges('|X').fillet(2.5)
    horn=cq.Workplane('YZ',origin=(-FACE,0,0)).circle(HORN_R).extrude(HORN_H)
    idler=cq.Workplane('YZ',origin=(-(FACE+ALONG),0,0)).circle(HORN_R).extrude(-HORN_H)
    shape=body.union(horn).union(idler)
    for k in range(4):
        a=k*math.pi/2;shape=shape.cut(cq.Workplane('YZ',origin=(-GAP,HOLE_R*math.cos(a),HOLE_R*math.sin(a))).circle(0.8).extrude(-6))
    return to_world(shape,P,h,d)

def horn_plate(P,h,d,width=ACROSS,length=None,thickness=PLATE):
    """Child plate bolted to the horn: pivot plane to pivot plane + thickness."""
    length=length or (LONG-HORN_OFFSET)*0+ACROSS
    plate=local_box(0,thickness,-width/2,width/2,-length/2,length/2).edges('|X').fillet(min(width,length)/2-0.01)
    plate=plate.cut(cq.Workplane('YZ').circle(1.6).extrude(thickness*2))
    for k in range(4):
        a=k*math.pi/2;plate=plate.cut(cq.Workplane('YZ',origin=(0,HOLE_R*math.cos(a),HOLE_R*math.sin(a))).circle(1.1).extrude(thickness*2))
    return to_world(plate,P,h,d)

def idler_plate(P,h,d,width=ACROSS,length=None,thickness=PLATE):
    """Child plate on the rear idler side, keeping the joint doubly supported."""
    length=length or ACROSS
    x0=-(FACE+ALONG+HORN_H+GAP)
    plate=local_box(x0-thickness,x0,-width/2,width/2,-length/2,length/2).edges('|X').fillet(min(width,length)/2-0.01)
    plate=plate.cut(cq.Workplane('YZ',origin=(x0+1,0,0)).circle(1.6).extrude(-thickness*2))
    for k in range(4):
        a=k*math.pi/2;plate=plate.cut(cq.Workplane('YZ',origin=(x0+1,HOLE_R*math.cos(a),HOLE_R*math.sin(a))).circle(1.1).extrude(-thickness*2))
    return to_world(plate,P,h,d)

def pocket(P,h,d,clearance=0.4):
    """Volume to subtract from the parent link so the servo body drops in."""
    c=clearance
    shape=local_box(-(FACE+ALONG)-c,-FACE+c,-ACROSS/2-c,ACROSS/2+c,-HORN_OFFSET-c,LONG-HORN_OFFSET+c)
    # Disc clearance stops 0.05 mm short of the clevis plate faces so no sliver is carved into a neighbouring plate.
    horn=cq.Workplane('YZ',origin=(-FACE+c,0,0)).circle(HORN_R+1).extrude(HORN_H+GAP-c-.05)
    idler=cq.Workplane('YZ',origin=(-(FACE+ALONG)-c,0,0)).circle(HORN_R+1).extrude(-(HORN_H+GAP-c-.05))
    return to_world(shape.union(horn).union(idler),P,h,d)

def span(P,h,d):
    """World-axis bounding box of the envelope, handy for layout checks."""
    bb=envelope(P,h,d).val().BoundingBox();return np.array([[bb.xmin,bb.ymin,bb.zmin],[bb.xmax,bb.ymax,bb.zmax]])

def cradle(P,h,d,faces,wall=2.5,clearance=0.4,extra=0.0):
    """Walls hugging chosen faces of the servo body, in world coordinates.
    faces: 'y+','y-' (across faces), 'end' (long end, +d), 'cap' (short end, -d), 'x-' (idler side), 'x+' (horn side).
    extra extends the walls beyond the body along d on both ends."""
    c=clearance;x0=-(FACE+ALONG)-c;x1=-FACE+c;y0=-ACROSS/2-c;y1=ACROSS/2+c;z0=-HORN_OFFSET-c-extra;z1=LONG-HORN_OFFSET+c+extra
    parts=[]
    if 'y+' in faces:parts.append(local_box(x0,x1,y1,y1+wall,z0,z1))
    if 'y-' in faces:parts.append(local_box(x0,x1,y0-wall,y0,z0,z1))
    if 'end' in faces:parts.append(local_box(x0,x1,y0-(wall if 'y-' in faces else 0),y1+(wall if 'y+' in faces else 0),z1,z1+wall))
    if 'cap' in faces:parts.append(local_box(x0,x1,y0-(wall if 'y-' in faces else 0),y1+(wall if 'y+' in faces else 0),z0-wall,z0))
    if 'x-' in faces:parts.append(local_box(x0-wall,x0,y0,y1,z0,z1))
    if 'x+' in faces:parts.append(local_box(x1,x1+wall,y0,y1,z0,z1))
    shape=parts[0]
    for q in parts[1:]:shape=shape.union(q)
    return to_world(shape,P,h,d)

def channel(P,h,d,faces=('y+','y-','far','near','back'),thick=2.4,clear=0.4,grow=0.0):
    """Walls hugging the servo body on the chosen faces, in world coordinates.

    faces: 'y+'/'y-' the two ACROSS faces, 'near'/'far' the two ends along d
    (near = short end, 9.5 mm from the horn axis), 'back' the rear face beyond the
    idler disc. The horn side is always open so the child link can reach the horn.
    grow extends the walls outward along d at both ends.
    """
    c=clear;t=thick;back=-(FACE+ALONG+HORN_H+c)
    outer=local_box(back-t,-FACE+HORN_H,-(ACROSS/2+c+t),ACROSS/2+c+t,-(HORN_OFFSET+c+t)-grow,LONG-HORN_OFFSET+c+t+grow)
    cavity=local_box(back,200,-(ACROSS/2+c),ACROSS/2+c,-(HORN_OFFSET+c),LONG-HORN_OFFSET+c)
    shape=outer.cut(cavity)
    big=400
    if 'y+' not in faces:shape=shape.cut(local_box(-big,big,ACROSS/2+c,big,-big,big))
    if 'y-' not in faces:shape=shape.cut(local_box(-big,big,-big,-(ACROSS/2+c),-big,big))
    if 'far' not in faces:shape=shape.cut(local_box(-big,big,-big,big,LONG-HORN_OFFSET+c,big))
    if 'near' not in faces:shape=shape.cut(local_box(-big,big,-big,big,-big,-(HORN_OFFSET+c)))
    if 'back' not in faces:shape=shape.cut(local_box(-big,back,-big,big,-big,big))
    return to_world(shape,P,h,d)

def plate_frame(P,h,d):
    """World axes of a horn plate: (out, across, along) unit vectors."""
    x,y,z=frame(h,d);return x,y,z
