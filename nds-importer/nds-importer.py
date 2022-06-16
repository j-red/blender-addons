#### import entire directory of collada files and process properly

#### TODO: 
#   - auto-import proper material from same directory
#   - rename armatures based on the imported file
#   - move armatures to next open space (by variable amount)
#   - move armatures into grid instead of straight line?
#   - specify transformations to apply (scale down and use smaller margins instead)
#      - allow custom axis rotations in case imports are off
#   - add confirmation that all objects will be deleted (in addon, add toggle to disable this)
#   - add debug option to only import first N models to ensure import settings are correct
#   - delet obj if it has no image texture
#   - add option to disable vertex merging/de-triangularization (speed up model imports)
#   - use modal timer to live-update in background instead of freezing on import
#   - use addon window to specify what objects to import, rather than entire directory?
#   - allow partial iterations -- use an empty that moves to position of next import?
#   - add checkbox for smooth shading? (not needed, select all and right click to change shading)
#   - if addon: add utility to apply smooth shading to all selcted objects, 
#   - ADDON: distribute items with specified margins, auto grid size (smallest grid)
#   - cleanup utility to delete armatures with no mesh object
#   - utility to move all objects with no armature to separate collection
# temp fix: delete objects if they possess a material that starts with "Mat_"

#### NOTE: this script requires minimum blender 2.80 for active context selection

import os, bpy
from glob import glob

target_dir = "E:\\Emulation\\out\\" # target directory
convert_tris_to_quads = True # set to True or False

margin = 100 # space to place between imported models

# interpolation mode for image texture
interpolation_mode = "Closest" # choose from ['Linear', 'Closest', 'Cubic', 'Smart']


output_shader_name = "Principled BSDF" # node name for shader target
alpha_input_index = 21 # zero-based index for alpha input on output shader

attempt_skip_LOD = True # if we should attempt to skip LOD meshes
lod_keyword = "_f" # check for this string in filename to skip loading


#### ========================== INITIAL PREP ==========================

#### delete all objects currently in scene
try:
	bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
except:
	pass

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

#### ========================== MODEL IMPORTS ==========================

_count = 0 # counter for margin displacement
_rowCount = 10 # how many models should fit in one row
_yCount = 0 # column displacement



# for the DQ IX demo, ther are 5740 .dae models  to try importing, many of which are invalid.

for f in glob(f'{target_dir}*.dae')[:1000]: # use [:10] to import first 10 for debugging or [X:Y] for indices X through Y-1

	if (attempt_skip_LOD and lod_keyword in f): # if "_f" is in the .dae filename, skip (aka, don't load lod mesh)
		continue

	#### import model
	bpy.ops.wm.collada_import(filepath=f)
	_bail = False # if we should abort this model
	
	#### references to model and parent armature
	_obj = bpy.context.active_object

	try:
		_parent = _obj.parent

		#### DEBUG: PLACEHOLDER FIX. if object has material starting with "Mat_", delet it and move to next.
		_matnames = [(i.name + "    ")[:4] for i in bpy.context.view_layer.objects.active.material_slots]
		if ("Mat_" in _matnames):
			_bail = True
		else:
			#### DEBUG PLACEHOLDER 2: delet object if any materials have no image texture
			for _objMat in bpy.context.view_layer.objects.active.material_slots:
				tree = _objMat.material.node_tree.nodes
				_myTex = tree.get("Image Texture")
				
				if (_myTex is None): # delet if no image texture found
					_bail = True
					break
	
	except:
		_bail = True
		
	if (_bail):
		bpy.ops.object.delete(use_global=False) # delete active AND parent (since both are selected on import)
		continue # to next object to import
	
	#### enter editmode and merge verts
	# bpy.ops.object.editmode_toggle()
	bpy.ops.object.mode_set(mode='EDIT', toggle=False)
	try:
		bpy.ops.mesh.select_all(action='SELECT')
		bpy.ops.mesh.remove_doubles()
		
		if (convert_tris_to_quads):
			bpy.ops.mesh.tris_convert_to_quads()
	except:
		# if an object has no verts, the above ops will fail
		pass

	#### exit edit mode
	bpy.ops.object.editmode_toggle()

	#### set active object to parent
	bpy.context.view_layer.objects.active = _parent
	
	#### translate parent
	bpy.ops.transform.translate(
		value=(margin * _count, _yCount * margin, 0), 
		orient_type='GLOBAL', 
		orient_matrix_type='GLOBAL', 
		use_proportional_edit=False, 
	)
	
	#### rename parent
	_name = f.replace("\\", "/").split('/')[-1][:-4] # use unix-style paths and same name as file without .dae
	if (_parent):
		_parent.name = _name + " Rig"

	#### deselect all objects
	bpy.ops.object.select_all(action='DESELECT')
	
	#### increment counts for margins
	_count += 1
	
	if (_count >= _rowCount):
		_yCount += 1
		_count = 0
	
#### end loop through .dae files in target directory

#### ========================== MATERIAL MANAGEMENT ==========================

#### loop through ALL materials materials, set to alpha clip, and attach proper alpha node in material
#### see https://blender.stackexchange.com/questions/88659/return-list-of-nodes-inside-material
for _mat in bpy.data.materials:
	try:
		#### parent refernces to material nodes and links
		tree = _mat.node_tree.nodes
		links = _mat.node_tree.links
				
		#### mix by specific node names
		_tex = tree.get("Image Texture")
		_bsdf = tree.get(output_shader_name)
		
		#### create new link from image alpha to principled alpha
		links.new(_tex.outputs[1], _bsdf.inputs[alpha_input_index])
		
		#### set material and shadow types to alpha clip
		_mat.blend_method = 'CLIP'
		_mat.shadow_method = 'CLIP'
		
		#### set image texture interpolation mode
		_tex.interpolation = interpolation_mode

	except:
		#### this should only trigger on invalid materials, so no need to worry about it... right?
		continue 


#### ================== ADDON SETUP (DO NOT MODIFY PAST THIS POINT) ==================
	
def register():
    pass
