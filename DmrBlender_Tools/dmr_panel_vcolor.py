import bpy

classlist = []

# =============================================================================

class DMR_PT_3DViewVertexColors(bpy.types.Panel): # ------------------------------
    bl_label = "Vertex Colors"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Mesh" # Name of sidebar
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod 
    def poll(self, context):
        active = context.active_object
        if active:
            if active.type == 'MESH':
                return active.mode in {'EDIT', 'VERTEX_PAINT', 'OBJECT'}
        return None
    
    def draw(self, context):
        active = context.active_object
        mode = active.mode
        layout = self.layout
        color = bpy.context.scene.editmodecolor
        col255 = [x*255 for x in color[:3]]
        #colhex = '%02x%02x%02x' % (int(color[0]*255), int(color[1]*255), int(color[2]*255))
        #colhex = colhex.upper()
        
        if mode in {'EDIT', 'VERTEX_PAINT'}:
            col = layout.column(align=1)
            
            colorarea = col.row(align = 1)
            row = colorarea.row(align = 1)
            op = row.operator("dmr.set_vertex_color", icon='BRUSH_DATA', text="")
            op.mixamount = 1.0
            op.targetcolor = context.scene.editmodecolor
            row.scale_x = 2
            row.scale_y = 2
            row.prop(context.scene, "editmodecolor", text='')
            row.operator("dmr.pick_vertex_color", icon='EYEDROPPER', text="")
            
            
            row = col.row(align=1)
            row.label(text = '<%d, %d, %d>   A:%.2f' % (col255[0],col255[1],col255[2], color[3]) )
            
            row = col.row(align = 1)
            row.operator("dmr.vc_clear_alpha", icon='MATSPHERE', text="Clear Alpha")
            
            row = layout.row(align = 1)
            r = row.row(align=1)
            r.label(text='Set Channel: ')
            row.operator('dmr.set_vertex_color_channel', text='', icon='COLOR_RED').channelindex = 0
            row.operator('dmr.set_vertex_color_channel', text='', icon='COLOR_GREEN').channelindex = 1
            row.operator('dmr.set_vertex_color_channel', text='', icon='COLOR_BLUE').channelindex = 2
            row.operator('dmr.set_vertex_color_channel', text='', icon='FONT_DATA').channelindex = 3
            
            row = layout.row(align = 1)
            
            #row.label(text = colhex )
        
        me = active.data
        vcolors = me.vertex_colors
        
        row = layout.row(align=0)
        col = row.column()
        col.template_list("MESH_UL_vcols", "vcols", me, "vertex_colors", me.vertex_colors, "active_index", rows=2)
        col = row.column(align=True)
        col.operator("mesh.vertex_color_add", icon='ADD', text="")
        col.operator("mesh.vertex_color_remove", icon='REMOVE', text="")
        col = col.column(align=True)
        col.operator("dmr.vertex_color_move", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("dmr.vertex_color_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

classlist.append(DMR_PT_3DViewVertexColors)

# =============================================================================

def register():
    for c in classlist:
        bpy.utils.register_class(c)
    
    bpy.types.Scene.editmodecolor = bpy.props.FloatVectorProperty(
        name="Paint Color", subtype="COLOR_GAMMA", size=4, min=0.0, max=1.0,
        default=(1.0, 1.0, 1.0, 1.0)
    )

def unregister():
    for c in reversed(classlist):
        bpy.utils.unregister_class(c)
