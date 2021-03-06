import bpy
import os

classlist = []

# =============================================================================

class DMR_OP_Reset3DCursor(bpy.types.Operator):
    bl_label = "Reset 3D Cursor"
    bl_idname = 'dmr.reset_3d_cursor'
    bl_description = 'Resets 3D cursor to (0, 0, 0)'
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        context.scene.cursor.location = (0.0, 0.0, 0.0)
        return {'FINISHED'}
classlist.append(DMR_OP_Reset3DCursor)

# =============================================================================

class DMR_OP_Reset3DCursorX(bpy.types.Operator):
    bl_label = "Zero 3D Cursor X"
    bl_idname = 'dmr.reset_3d_cursor_x'
    bl_description = 'Resets x coordinate of 3D Cursor'
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        context.scene.cursor.location[0] = 0.0
        return {'FINISHED'}
classlist.append(DMR_OP_Reset3DCursorX)

# =============================================================================

class DMR_OP_ToggleEditModeWeights(bpy.types.Operator):
    bl_label = "Toggle Edit Mode Weights"
    bl_idname = 'dmr.toggle_editmode_weights'
    bl_description = 'Toggles Weight Display for Edit Mode'
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        bpy.context.scene.tool_settings.vertex_group_user = 'ALL'
        bpy.context.space_data.overlay.show_weight = not bpy.context.space_data.overlay.show_weight
        
        return {'FINISHED'}
classlist.append(DMR_OP_ToggleEditModeWeights)

# =============================================================================

class DMR_OP_ToggleAnimation(bpy.types.Operator):
    bl_label = "Play/Pause Animation"
    bl_idname = 'dmr.play_anim'
    bl_description = 'Toggles animation playback'
    
    def execute(self, context):
        bpy.ops.screen.animation_play()
        return {'FINISHED'}
classlist.append(DMR_OP_ToggleAnimation)

# =============================================================================

class DMR_OP_ImageReloadAll(bpy.types.Operator):
    bl_label = "Reload All Images"
    bl_idname = 'dmr.image_reload'
    bl_description = 'Reloads all images from files'
    
    def execute(self, context):
        for image in bpy.data.images:
            image.reload()
        
        return {'FINISHED'}
classlist.append(DMR_OP_ImageReloadAll)

# =============================================================================

class DMR_OP_RenameNodeInput(bpy.types.Operator):
    bl_label = "Rename Node Input (May not save correctly)"
    bl_idname = 'dmr.rename_node_input'
    bl_description = 'Changes name of node input. (NOTE: may not keep changes after reloading file)'
    bl_options = {'REGISTER', 'UNDO'}
    
    ioindex : bpy.props.EnumProperty(
        name="Target Input",
        description="Name of input to rename",
        items=lambda s, context: [
            ( (str(i), '[%d]: %s' % (i, io.name), 'Rename input %d "%s"' % (i, io.name)) )
            for i, io in enumerate(context.active_node.inputs)
        ])
    
    newname : bpy.props.StringProperty(
        name="New Name", description="New name of input", default='New Name')
    
    def invoke(self, context, event):
        if context.active_node == None:
            self.report({'WARNING'}, 'No active node')
            return {'FINISHED'}
        return context.window_manager.invoke_props_dialog(self)
    
    def execute(self, context):
        [x for x in context.active_node.inputs][int(self.ioindex)].name = self.newname
        return {'FINISHED'}
classlist.append(DMR_OP_RenameNodeInput)

# =============================================================================

class DMR_OP_RenameNodeOutput(bpy.types.Operator):
    bl_label = "Rename Node Output (May not save correctly)"
    bl_idname = 'dmr.rename_node_output'
    bl_description = 'Changes name of node output. (NOTE: may not keep changes after reloading file)'
    bl_options = {'REGISTER', 'UNDO'}
    
    ioindex : bpy.props.EnumProperty(
        name="Target Output",
        description="Name of output to rename",
        items=lambda s, context: [
            ( (str(i), '[%d]: %s' % (i, io.name), 'Rename output %d "%s"' % (i, io.name)) )
            for i, io in enumerate(context.active_node.outputs)
        ])
    
    newname : bpy.props.StringProperty(
        name="New Name", description="New name of output", default='New Name')
    
    def invoke(self, context, event):
        if context.active_node == None:
            self.report({'WARNING'}, 'No active node')
            return {'FINISHED'}
        return context.window_manager.invoke_props_dialog(self)
    
    def execute(self, context):
        [x for x in context.active_node.outputs][int(self.ioindex)].name = self.newname
        return {'FINISHED'}
classlist.append(DMR_OP_RenameNodeOutput)

# =============================================================================

class DMR_OP_FixFileOutputNames(bpy.types.Operator):
    bl_label = "Fix Filename Output"
    bl_idname = 'dmr.fix_filename_output'
    bl_description = "Removes frame count from files exported from File Output Node"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        nodes = scene.node_tree.nodes
        
        framenumber = str(scene.frame_current)
        framenumber = '0'*len(framenumber)+framenumber
        
        for nd in nodes:
            if nd.type == 'OUTPUT_FILE':
                basepath = bpy.path.abspath(nd.base_path)
                for slot in nd.file_slots:
                    ext = slot.format.file_format.lower()
                    fpath = basepath+slot.path+framenumber+'.'+ext
                    
                    if os.path.isfile(fpath):
                        newpath = fpath.replace(framenumber, '')
                        if os.path.isfile(newpath):
                            os.remove(newpath)
                        os.rename(fpath, newpath)
        return {'FINISHED'}
classlist.append(DMR_OP_FixFileOutputNames)

# =============================================================================

class DMR_OP_SetEdgeCrease(bpy.types.Operator):
    bl_label = "Set Crease"
    bl_idname = 'dmr.set_crease'
    bl_description = "Sets edge crease value for selected edges"
    bl_options = {'REGISTER', 'UNDO'}
    
    crease : bpy.props.FloatProperty(
        name="Crease",
        description='Value to set crease to',
        min=-0.0,
        max=1.0, 
    )

    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.object.type == 'MESH' and
                context.object.data.is_editmode)

    def execute(self, context):
        crease = self.crease
        context = bpy.context
        objs = [o for o in context.selected_objects if o.type == 'MESH']
        
        lastobjectmode = bpy.context.active_object.mode
        bpy.ops.object.mode_set(mode = 'OBJECT') # Update selected
        
        for obj in objs:
            edges = [e for e in obj.data.edges if e.select]
            for e in edges:
                e.crease = crease
        
        bpy.ops.object.mode_set(mode = lastobjectmode)
        
        return {'FINISHED'}
classlist.append(DMR_OP_SetEdgeCrease)

# =============================================================================

def register():
    for c in classlist:
        bpy.utils.register_class(c)

def unregister():
    for c in reversed(classlist):
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
