"""Validate actual texel density, independent of the model's UV-generation strategy."""
import math

def validate_model(model, texture_sizes):
    faces_checked=0
    for index,element in enumerate(model['elements']):
        start,end=element['from'],element['to']
        if any(not float(n).is_integer() for n in start+end):
            raise ValueError(f'Element {index}: geometry must lie on the whole-texel grid')
        sizes=[b-a for a,b in zip(start,end)]
        if any(n<=0 for n in sizes):
            raise ValueError(f'Element {index}: non-positive cuboid size')
        if element.get('rotation',{}).get('rescale',False):
            raise ValueError(f'Element {index}: rescaling rotation changes texel density')
        for direction,face in element['faces'].items():
            axes={'up':(0,2),'down':(0,2),'north':(0,1),'south':(0,1),'east':(2,1),'west':(2,1)}[direction]
            expected=[sizes[a] for a in axes]
            uv=face.get('uv')
            if uv is None or len(uv)!=4:
                raise ValueError(f'Element {index}/{direction}: explicit UV rectangle required')
            if any(not float(n).is_integer() or not 0<=n<=16 for n in uv):
                raise ValueError(f'Element {index}/{direction}: UV must align to whole texels inside the tile')
            texture=face['texture']
            seen=set()
            while texture.startswith('#'):
                if texture in seen:
                    raise ValueError('Cyclic texture reference')
                seen.add(texture)
                texture=model['textures'][texture[1:]]
            width,height=texture_sizes[texture]
            actual=[abs(uv[2]-uv[0])*width/16,abs(uv[3]-uv[1])*height/16]
            rotation=face.get('rotation',0)
            if rotation not in (0,90,180,270):
                raise ValueError('Invalid UV rotation')
            if rotation in (90,270): actual.reverse()
            if any(not math.isclose(a,b,abs_tol=1e-9) for a,b in zip(actual,expected)):
                raise ValueError(f'Element {index}/{direction}: stretched texture, model {expected} vs texels {actual}')
            faces_checked+=1
    return faces_checked
