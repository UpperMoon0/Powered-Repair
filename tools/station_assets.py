"""One block model and material set shared by every supported game version."""
from pathlib import Path

ART = Path(__file__).resolve().parents[1] / 'assets-source'

def model(mod):
    elements = []
    def box(start, end, material, faces=None):
        x1,y1,z1=start
        x2,y2,z2=end
        # Explicit vanilla-oriented projections: one UV unit is one texel on a 16x16 material.
        uvs={'down':[x1,16-z2,x2,16-z1], 'up':[x1,z1,x2,z2],
             'north':[16-x2,16-y2,16-x1,16-y1], 'south':[x1,16-y2,x2,16-y1],
             'west':[z1,16-y2,z2,16-y1], 'east':[16-z2,16-y2,16-z1,16-y1]}
        if material=='circuit':
            # Select a piece of the artwork; never fit the whole 16x16 tile onto a small panel.
            for face,uv in uvs.items():
                w,h=uv[2]-uv[0],uv[3]-uv[1]
                u,v=min(9,16-w),min(2,16-h)
                uvs[face]=[u,v,u+w,v+h]
        elements.append({'from': start, 'to': end, 'faces': {
            face: {'texture': '#' + (faces or {}).get(face, material),
                   'uv':uvs[face]}
            for face in ('down', 'up', 'north', 'south', 'west', 'east')}})
    for x in (1, 12):
        for z in (1, 12):
            box([x, 0, z], [x + 3, 2, z + 3], 'steel')
    box([0, 2, 0], [16, 3, 16], 'steel')
    box([1, 3, 1], [15, 8, 15], 'casing', {'west': 'vent', 'east': 'vent', 'south': 'vent'})
    box([3, 4, 0], [10, 7, 1], 'circuit')
    box([11, 4, 0], [13, 7, 1], 'vent')
    box([0, 8, 0], [16, 9, 16], 'steel')
    box([2, 9, 2], [14, 10, 12], 'vent')
    for x in (1, 14):
        box([x, 9, 1], [x + 1, 11, 13], 'steel')
    box([5, 10, 4], [11, 11, 10], 'steel')
    box([6, 11, 5], [10, 12, 9], 'casing')
    box([4, 12, 3], [12, 14, 10], 'steel')
    box([2, 12, 4], [4, 13, 8], 'steel')
    for x in (1, 13):
        box([x, 9, 12], [x + 2, 15, 15], 'casing')
        box([x, 10, 11], [x + 2, 14, 12], 'circuit')
    box([1, 15, 12], [15, 16, 15], 'steel')
    box([5, 14, 12], [11, 15, 14], 'circuit')
    return {'parent': 'minecraft:block/block', 'ambientocclusion': True,
            'textures': {**{name: f'{mod}:block/{name}' for name in ('steel','casing','vent','circuit')},
                         'particle': f'{mod}:block/casing'},
            'elements': elements,
            'display': {
                'gui': {'rotation': [30, 225, 0], 'translation': [0, 0, 0], 'scale': [.65,.65,.65]},
                'ground': {'translation': [0, 3, 0], 'scale': [.25,.25,.25]},
                'fixed': {'scale': [.5,.5,.5]},
                'thirdperson_righthand': {'rotation': [75,45,0], 'translation': [0,2.5,0], 'scale': [.375,.375,.375]},
                'firstperson_righthand': {'rotation': [0,45,0], 'scale': [.4,.4,.4]}}}

def translations(mod):
    prefix = 'ui.' + mod + '.'
    return {'itemGroup.' + mod: 'Powered Repair', **{prefix + k: v for k, v in {
        'subtitle': 'Restore durability with energy', 'equipment': 'Equipment', 'energy': 'Energy',
        'inventory': 'Inventory', 'cost': 'Cost / point', 'rate': 'Repair rate',
        'empty': 'Insert damaged equipment', 'ready': 'Repairs complete',
        'paused': 'Paused by redstone', 'unpowered': 'Needs power', 'working': 'Repairing equipment',
        'energy_tip': '%s / %s FE\nUp to %s durability per tick\nEnergy input: every face',
        'equipment_tip': 'Five repair slots\nInsert damaged tools, weapons or armor.\nPercentages show remaining durability.\nItems share the repair rate.\nHoppers extract only fully repaired items.',
    }.items()}}
