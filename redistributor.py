bl_info = {
	"name": "Redistribute",
	"description": "",
	"author": "j-red.github.io",
	"version": (1, 0),
	"blender": (3, 2, 0),
	"location": "3D View > Tools",
	"warning": "", 
	"wiki_url": "",
	"tracker_url": "",
	"category": "Object"
}

import bpy
from mathutils import Vector

from bpy.utils import ( register_class, unregister_class )
from bpy.props import ( 
	StringProperty,
	BoolProperty,
	IntProperty,
	FloatProperty,
	FloatVectorProperty,
	EnumProperty,
	PointerProperty,
)

from bpy.types import ( 
	Panel,
	AddonPreferences,
	Operator,
	PropertyGroup,
)


# this must match the addon name, use '__package__' when defining this in a submodule of a python package.
addon_name = __name__	  # when single file 
#addon_name = __package__   # when file in package 

# ------------------------------------------------------------------------
#   settings in addon-preferences panel 
# ------------------------------------------------------------------------

# panel update function for PREFS_PT_MyPrefs panel 
def _update_panel_fnc (self, context):
	# load addon custom-preferences 
	print( addon_name, ': update pref.panel function called' )
	main_panel =  OBJECT_PT_my_panel
	main_panel .bl_category = context .preferences.addons[addon_name] .preferences.tab_label
	# re-register for update 
	unregister_class( main_panel )
	register_class( main_panel )


class PREFS_PT_MyPrefs( AddonPreferences ):
	''' 
	Custom Addon Preferences Panel - in addon activation panel -
	menu / edit / preferences / add-ons  
	'''

	bl_idname = addon_name

	tab_label: StringProperty(
			name="Tab Label",
			description="Evenly redistribute objects in a grid-based pattern",
			default="Redistribute by j-red",
			update=_update_panel_fnc
	)

	def draw(self, context):
		layout = self.layout

		row = layout.row()
		col = row.column()
		col.label(text="Tab Label:")
		col.prop(self, "tab_label", text="")



# ------------------------------------------------------------------------
#   properties visible in the addon-panel 
# ------------------------------------------------------------------------

class PG_MyProperties (PropertyGroup):

	#### my properties
	distribute_meshes : BoolProperty(
		name="Distribute Meshes",
		description="Align meshes to new grid",
		default = True
	)

	distribute_armatures : BoolProperty(
		name="Distribute Armatures",
		description="Align armatures to new grid",
		default = False
	)
	
	distribute_empties : BoolProperty(
		name="Distribute Empties",
		description="Align empty objects to new grid",
		default = False
	)
	
	distribute_other : BoolProperty(
		name="Distribute Other",
		description="Align all other types of objects to new grid",
		default = False
	)
	
	margin_size : FloatProperty(
		name = "Margin Size",
		description = "Spacing between objects aligned to grid",
		default = 5.0,
		min = 0.0,
		max = 1000.0
	)
	
	auto_margins : BoolProperty(
		name="Use Dynamic Margins (EXPERIMENTAL)",
		description="Pack objects into grid based on mesh dimensions",
		default = False
	)
	
	row_size : IntProperty(
		name = "Objects in Row",
		description="The number of objects in a single row",
		default = 10,
		min = 1,
		max = 1000
	)
	
	flexible_grid : BoolProperty(
		name="Flexible grid size",
		description="Automatically assign number of objects in row",
		default = False
	)
	
	#### template
	my_float_vector : FloatVectorProperty(
		name = "Float Vector Value",
		description="Something",
		default=(0.0, 0.0, 0.0), 
		min= 0.0, 
		max = 0.1
	) 

	my_string : StringProperty(
		name="User Input",
		description=":",
		default="",
		maxlen=1024,
		)

	my_enum : EnumProperty(
		name="Dropdown:",
		description="Apply Data to attribute.",
		items=[ ('OP1', "Option 1", ""),
				('OP2', "Option 2", ""),
				('OP3', "Option 3", ""),
			   ]
		)

# ------------------------------------------------------------------------
#   operator(s)
# ------------------------------------------------------------------------
	
class JARED_RedistributeOperator (bpy.types.Operator):
	bl_idname = "jared.redistribute"
	bl_label = "Redistribute Objects"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Distribute objects evenly on a grid"

	def execute(self, context):
		scene = context.scene
		mytool = scene.my_tool
		
		#### get variables from properties
		margin = mytool.margin_size
		row_count = mytool.row_size
		
		
		types = [] # type of objects to operate on
		
		if (mytool.distribute_meshes):
			types.append('MESH')
		if (mytool.distribute_armatures):
			types.append('ARMATURE')
		if (mytool.distribute_empties):
			types.append('EMPTY')
		if (mytool.distribute_other):
			for i in ['CURVE', 'SURFACE', 'META', 'FONT', 'POINTCLOUD', 'VOLUME', 'GPENCIL', 'LATTICE']: # omitting 'CAMERA', 'SPEAKER' 'HAIR', 'LIGHT', and 'LIGHT_PROBE'
				types.append(i)
		
		
		### position containers for consistent alignment
		_x = 0
		_y = 0
		_z = 0
		
		
		for _type in types: # align object types separately
			#### select current type
			bpy.ops.object.select_by_type(type=_type)
			
			#### clear positions
			bpy.ops.object.location_clear(clear_delta=False)
			
			#### get number of selected items to identify optimal grid size
			num_selected = len(bpy.context.selected_objects)
			
			#### redistribute objects
			for obj in bpy.context.selected_objects:
				
				# bpy.context.object.location = Vector([_x, _y, _z]) * _margin # set position explicitly
				obj.location = Vector([_x, _y, _z]) * margin # set position explicitly
				
				_x += 1
				
				if (_x >= row_count): # how many objects per row
					_x = 0
					_y += 1
			
		
		bpy.ops.object.select_all(action='DESELECT')

		return {'FINISHED'} # end redistribute operator

	
# ------------------------------------------------------------------------
#   menus
# ------------------------------------------------------------------------

class MT_BasicMenu (bpy.types.Menu):
	bl_idname = "OBJECT_MT_select_test"
	bl_label = "Select"

	def draw(self, context):
		layout = self.layout

		# built-in example operators
		layout.operator("object.select_all", text="Select/Deselect All").action = 'TOGGLE'
		layout.operator("object.select_all", text="Inverse").action = 'INVERT'
		layout.operator("object.select_random", text="Random")


# ------------------------------------------------------------------------
#   addon - panel -- visible in objectmode
# ------------------------------------------------------------------------

class OBJECT_PT_my_panel (Panel):
	bl_idname = "OBJECT_PT_my_panel"
	bl_label = "Redistribute Objects"
	bl_space_type = "VIEW_3D"   
	bl_region_type = "UI"
	bl_category = "Tool"  # note: replaced by preferences-setting in register function 
	bl_context = "objectmode"   


	def __init__(self):
		super(self, Panel).__init__()
		bl_category = bpy.context.preferences.addons[__name__].preferences.category 

	@classmethod
	def poll(self,context):
		return context.object is not None

	def draw(self, context):
		layout = self.layout
		scene = context.scene
		mytool = scene.my_tool
		
		layout.prop( mytool, "margin_size" )
		# layout.prop( mytool, "auto_margins" ) # dynamic margins checkbox
		# layout.menu( "OBJECT_MT_select_test", text="Presets", icon="SCENE")
		
		#### Create two columns, by using a split layout.
		split = layout.split()

		#### First column
		col = split.column()
		col.prop( mytool, "distribute_meshes" )
		col.prop( mytool, "distribute_armatures" )
		
		#### Second column, aligned
		col = split.column(align=True)
		col.prop( mytool, "distribute_empties" )
		col.prop( mytool, "distribute_other" )
	
		#### Row size parametrs
		split = layout.split()
		col = split.column() # First column
		col.prop( mytool, "row_size")
	
		#### Big button
		row = layout.row()
		row.scale_y = 2.0
		row.operator(JARED_RedistributeOperator.bl_idname)


# ------------------------------------------------------------------------
# register and unregister
# ------------------------------------------------------------------------

classes = (
	PG_MyProperties,
	#
	JARED_RedistributeOperator,
	MT_BasicMenu,
	OBJECT_PT_my_panel, 
	#
	PREFS_PT_MyPrefs, 
)

def register():
	#
	for cls in classes:
		register_class(cls)
	#
	bpy.types.Scene.my_tool = PointerProperty(type=PG_MyProperties)

	#

def unregister():
	for cls in reversed(classes):
		unregister_class(cls)

	del bpy.types.Scene.my_tool  # remove PG_MyProperties 


if __name__ == "__main__":
	register()
