import bpy
import sys

classlist = []

# =============================================================================

class DMR_PoseApply(bpy.types.Operator):
    bl_label = "Apply Pose"
    bl_idname = 'dmr.pose_apply'
    bl_description = 'Applies pose in pose library to current armature pose'
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        lastmode = bpy.context.active_object.mode
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
        oldactive = context.active_object
        
        findarmature = oldactive
        if findarmature and findarmature.type == 'ARMATURE': findarmature = findarmature
        elif findarmature.parent and findarmature.parent.type == 'ARMATURE': findarmature = findarmature.parent
        elif findarmature.data.modifiers and 'ARMATURE' in [x.type for x in findarmature.data.modifiers] and [x for x in findarmature.data.modifiers if x.type == 'ARMATURE'][0].object:
            findarmature = [x for x in findarmature.data.modifiers if x.type == 'ARMATURE'][0].object
        else: findarmature = None
        
        target = findarmature
        
        poselib = target.pose_library
        poseindex = poselib.pose_markers.active_index
        marker = poselib.pose_markers[poseindex]
        
        for obj in context.selected_objects[:] + [target]:
            if obj.type != 'ARMATURE':
                continue
            print(obj.name)
            targethidden = obj.hide_get()
            obj.hide_set(False)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode = 'POSE')
            
            bones = obj.data.bones
            selected = []
            hidden = []
            for b in bones:
                if b.hide:
                    hidden.append(b)
                    b.hide = False
                if b.select:
                    selected.append(b)
            
            bpy.ops.pose.select_all(action='SELECT')
            bpy.ops.poselib.apply_pose(pose_index=poseindex)
            bpy.ops.pose.select_all(action='DESELECT')
            
            for b in selected:
                b.select = True
            for b in hidden:
                b.hide = True
            target.hide_set(targethidden)
        
        bpy.ops.object.mode_set(mode = lastmode)
        bpy.context.view_layer.objects.active = oldactive
        
        self.report({'INFO'}, 'Pose read from "%s"' % marker.name)
        
        return {'FINISHED'}

classlist.append(DMR_PoseApply)

# =============================================================================

class DMR_PoseReplace(bpy.types.Operator):
    bl_label = "Replace Pose"
    bl_idname = 'dmr.pose_replace'
    bl_description = 'Overwrites pose in pose library with current armature pose'
    bl_options = {'REGISTER', 'UNDO'}
    
    allbones : bpy.props.BoolProperty(name='All Bones', default=0)
    
    def execute(self, context):
        lastmode = bpy.context.active_object.mode
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
        oldactive = context.active_object
        armobj = context.object
        armobj = armobj if (armobj and armobj.type == 'ARMATURE') else [m for m in armobj.modifiers if m.type == 'ARMATURE'][0].object
        bpy.context.view_layer.objects.active = armobj
        poselib = armobj.pose_library
        poseindex = poselib.pose_markers.active_index
        marker = poselib.pose_markers[poseindex]
        
        bpy.ops.object.mode_set(mode = 'POSE')
        
        for obj in context.selected_objects:
            if obj.type != 'ARMATURE':
                continue
            
            # All bones
            if self.allbones:
                bones = obj.data.bones
                selected = [b for b in bones if b.select]
                hidden = [b for b in bones if b.hide]
                
                for b in hidden: 
                    b.hide = False
                
                bpy.ops.pose.select_all(action='SELECT')
                bpy.ops.poselib.pose_add(frame = marker.frame, name = marker.name)
                bpy.ops.pose.select_all(action='DESELECT')
                
                for b in selected: 
                    b.select = True
                for b in hidden: 
                    b.hide = False
            # Selected Only
            else:
                bpy.ops.poselib.pose_add(frame = marker.frame, name = marker.name)
        
        poselib.pose_markers.active_index = poseindex
        bpy.ops.object.mode_set(mode = lastmode)
        bpy.context.view_layer.objects.active = oldactive
        self.report({'INFO'}, 'Pose written to "%s"' % marker.name)
        
        return {'FINISHED'}

classlist.append(DMR_PoseReplace)

# =============================================================================

class DMR_PoseBoneToView(bpy.types.Operator):
    bl_label = "Align Bone to View"
    bl_idname = 'dmr.pose_bone_to_view'
    bl_description = "Sets Pose bone's location and rotation to Viewport's"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod 
    def poll(self, context):
        active = context.active_object
        if active:
            if active.type == 'ARMATURE':
                if active.mode == 'EDIT' or active.mode == 'POSE':
                    return 1
        return None
    
    def execute(self, context):
        depsgraph = context.evaluated_depsgraph_get()
        scene = context.scene
        
        ray = scene.ray_cast(depsgraph, (1, 1, 1), (-1,-1,-1) )
        
        object = context.object
        bones = object.data.bones
        pbones = object.pose.bones
        bone = [x for x in bones if x.select]
        
        if len(bone) == 0:
            self.report({'WARNING'}, 'No bones selected')
            return {'FINISHED'}
        
        pbone = pbones[bone[0].name]
        
        rdata = context.region_data
        rot = rdata.view_rotation.copy()
        loc = rdata.view_location.copy()
        pbone.location = loc
        pbone.rotation_quaternion = rot
        bpy.ops.transform.translate(value=(0, 0, rdata.view_distance), 
            orient_type='LOCAL', 
            orient_matrix_type='LOCAL', 
            constraint_axis=(False, False, True), 
            )
        
        return {'FINISHED'}

classlist.append(DMR_PoseBoneToView)

# =============================================================================

class DMR_FixRightBoneNames(bpy.types.Operator):
    bl_label = "Fix Right Bone Names"
    bl_idname = 'dmr.fix_right_bone_names'
    bl_description = "Corrects newly created right side bones' names to their left counterpart"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.object.type == 'ARMATURE')
    
    def execute(self, context):
        active = bpy.context.view_layer.objects.active
        if active:
            lastobjectmode = bpy.context.active_object.mode
            bpy.ops.object.mode_set(mode = 'OBJECT') # Update selected
            
            bones = active.data.bones
            thresh = 0.01
            leftbones = [b for b in bones if b.head_local[0] >= thresh]
            rightbones = [b for b in bones if b.head_local[0] <= -thresh]
            for b in rightbones:
                loc = b.head_local.copy()
                loc[0] *= -1
                currdist = 100
                currbone = None
                for b2 in leftbones:
                    b2dist = (b2.head_local - loc).length
                    if b2dist < currdist:
                        currbone = b2
                        currdist = b2dist
                if currbone != None:
                    b.name = currbone.name[:-1] + 'r'
            bpy.ops.object.mode_set(mode = lastobjectmode)
                        
        return {'FINISHED'}
classlist.append(DMR_FixRightBoneNames)

# =============================================================================

class DMR_BoneNamesByPosition(bpy.types.Operator):
    bl_idname = "dmr.bone_names_by_position"
    bl_label = "Bone Names by Position"
    bl_description = "Set bone names by order in armature or order in parent-child chain"
    bl_options = {'REGISTER', 'UNDO'}
    
    basename : bpy.props.StringProperty(
        name="Format Name", default = 'link_%s'
    )
    
    locationtype: bpy.props.EnumProperty(
        name="Location Method",
        description="Method to sort bone names",
        items = (
            ('armature', 'Default', 'Sort using armature hierarchy'),
            ('x', 'X Location', 'Sort using X'),
            ('y', 'Y Location', 'Sort using Y'),
            ('z', 'Z Location', 'Sort using Z'),
        ),
        default='armature',
    )
    
    bonesuffix: bpy.props.EnumProperty(
        name="Bone Suffix",
        description="String to append to the end of bone name",
        items = (
            ('upper', 'Uppercase', 'Suffix = "A", "B", "C", ...'),
            ('lower', 'Lowercase', 'Suffix = "a", "b", "c", ...'),
            ('zero', 'From 0', 'Suffix = "0", "1", "2", ...'),
            ('one', 'From 1', 'Suffix = "1", "2", "3", ...'),
        ),
        default='zero',
    )
    
    reversedsort: bpy.props.BoolProperty(
        name="Reverse Sort",
        description="Reverse order of location method",
        default=False,
    )
    
    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.object.type == 'ARMATURE')
    
    def execute(self, context):
        if '%s' not in self.basename:
            return {'FINISHED'}
        
        object = context.object
        bones = object.data.bones
        
        lastobjectmode = object.mode
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
        targetbones = [b for b in bones if b.select]
        
        # Sort bones
        ltype = self.locationtype
        if ltype == 'x':
            targetbones.sort(key = lambda b: b.head_local[0])
        elif ltype == 'y':
            targetbones.sort(key = lambda b: b.head_local[1])
        elif ltype == 'z':
            targetbones.sort(key = lambda b: b.head_local[2])
        
        if self.reversedsort:
            targetbones.reversed()
        
        # Generate suffixes
        suffixmode = self.bonesuffix
        if suffixmode == 'upper':
            suffixlist = list('ABCDEFG')
        elif suffixmode == 'lower':
            suffixlist = list('abcdefg')
        elif suffixmode == 'zero':
            suffixlist = range(0, 10)
        elif suffixmode == 'one':
            suffixlist = range(1, 10)
        
        oldnames = [b.name for b in targetbones]
        newnames = [(self.basename % suffixlist[i]) for i in range(0, len(targetbones))]
        
        for i, b in enumerate(targetbones):
            b.name = '__temp%s__' % i
        
        for i, b in enumerate(targetbones):
            print("%s -> %s" % (oldnames[i], newnames[i]))
            b.name = newnames[i]
        print()
        
        bpy.ops.object.mode_set(mode = lastobjectmode)
        
        return {'FINISHED'}
classlist.append(DMR_BoneNamesByPosition)

# =============================================================================

class DMR_BoneSelectMore(bpy.types.Operator):
    bl_label = "Select More Bones"
    bl_idname = 'dmr.bone_select_more'
    bl_description = "Selects more connected child bones"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (context.object is not None and
               context.object.type == 'ARMATURE' and
               context.object.mode == 'POSE')
    
    def execute(self, context):
        active = bpy.context.view_layer.objects.active
        if active:
            lastobjectmode = bpy.context.active_object.mode
            bpy.ops.object.mode_set(mode = 'OBJECT') # Update selected
            bones = [b for b in active.data.bones if b.select]
            for b in bones:
                for c in b.children:
                    if c.use_connect:
                        c.select = True
            bpy.ops.object.mode_set(mode = lastobjectmode)
                        
        return {'FINISHED'}
classlist.append(DMR_BoneSelectMore)

# =============================================================================

class DMR_BoneSelectMoreParent(bpy.types.Operator):
    """Tooltip"""
    bl_label = "Select More Parent Bones"
    bl_idname = 'dmr.bone_select_more_parent'
    bl_description = "Selects more connected parent bones"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (context.object is not None and
               context.object.type == 'ARMATURE' and
               context.object.mode == 'POSE')
    
    def execute(self, context):
        active = bpy.context.view_layer.objects.active
        if active:
            lastobjectmode = bpy.context.active_object.mode
            bpy.ops.object.mode_set(mode = 'OBJECT') # Update selected
            bones = [b for b in active.data.bones if b.select]
            newselect = []
            for b in bones:
                if b.parent and b.use_connect:
                    newselect.append(b.parent)
            for b in newselect:
                b.select = True
            bpy.ops.object.mode_set(mode = lastobjectmode)
                        
        return {'FINISHED'}
classlist.append(DMR_BoneSelectMoreParent)

# =============================================================================

class DMR_BoneSelectLess(bpy.types.Operator):
    bl_label = "Select Less Bones"
    bl_idname = 'dmr.bone_select_less'
    bl_description = "Selects less connected child bones"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (context.object is not None and
               context.object.type == 'ARMATURE' and
               context.object.mode == 'POSE')
    
    def execute(self, context):
        def FindEndofChain(b):
            if b.children:
                for c in b.children:
                    if c.select:
                        return FindEndofChain(c)
            return b
        
        active = bpy.context.view_layer.objects.active
        if active:
            lastobjectmode = bpy.context.active_object.mode
            bpy.ops.object.mode_set(mode = 'OBJECT') # Update selected
            bones = [b for b in active.data.bones if b.select]
            endbones = []
            
            for b in bones:
                endbones.append(FindEndofChain(b))
            for b in endbones:
                b.select = False
            bpy.ops.object.mode_set(mode = lastobjectmode)
                        
        return {'FINISHED'}
classlist.append(DMR_BoneSelectLess)

# =============================================================================

class DMR_BoneSelectLessParent(bpy.types.Operator):
    bl_label = "Select Less Parent Bones"
    bl_idname = 'dmr.bone_select_less_parent'
    bl_description = "Selects less connected parent bones"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (context.object is not None and
               context.object.type == 'ARMATURE' and
               context.object.mode == 'POSE')
    
    def execute(self, context):
        active = bpy.context.view_layer.objects.active
        if active:
            lastobjectmode = bpy.context.active_object.mode
            bpy.ops.object.mode_set(mode = 'OBJECT') # Update selected
            bones = [b for b in active.data.bones if b.select]
            endbones = []
            
            for b in bones:
                if b.use_connect:
                    if b.parent:
                        if not b.parent.select:
                            endbones.append(b)
                    else:
                        endbones.append(b)
                else:
                    endbones.append(b)
            for b in endbones:
                b.select = False
            bpy.ops.object.mode_set(mode = lastobjectmode)
                        
        return {'FINISHED'}
classlist.append(DMR_BoneSelectLessParent)

# =============================================================================

class DMR_BoneGroupIsolate(bpy.types.Operator):
    bl_label = "Isolate Bone Group"
    bl_idname = 'dmr.bone_group_isolate'
    bl_description = "Hides all bones not in bone group. Unhides if only those in group are shown"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (context.object is not None and
               context.object.type == 'ARMATURE' and
               context.object.mode == 'POSE')
    
    def execute(self, context):
        active = bpy.context.view_layer.objects.active
        if active:
            lastobjectmode = bpy.context.active_object.mode
            bpy.ops.object.mode_set(mode = 'OBJECT') # Update selected
            
            bonegroup = active.pose.bone_groups.active
            bones = [active.data.bones[pb.name] for pb in active.pose.bones if pb.bone_group != bonegroup]
            groupbones = [active.data.bones[pb.name] for pb in active.pose.bones if pb.bone_group == bonegroup]
            
            if len([b for b in bones if not b.hide]) > 0:
                for b in bones:
                    b.hide = True
            else:
                for b in [b for b in active.data.bones if b not in groupbones]:
                    b.hide = False
            for b in groupbones:
                b.hide = False
            bpy.ops.object.mode_set(mode = lastobjectmode)
                        
        return {'FINISHED'}
classlist.append(DMR_BoneGroupIsolate)

# =============================================================================

addon_keymaps = []
def register():
    for c in classlist:
        bpy.utils.register_class(c)
    
    # Add hotkeys
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new(DMR_BoneSelectMore.bl_idname, type='NUMPAD_PLUS', value='PRESS', ctrl=True, shift=False)
        kmi = km.keymap_items.new(DMR_BoneSelectLess.bl_idname, type='NUMPAD_MINUS', value='PRESS', ctrl=True, shift=False)
        kmi = km.keymap_items.new(DMR_BoneSelectMoreParent.bl_idname, type='NUMPAD_PLUS', value='PRESS', ctrl=True, shift=True)
        kmi = km.keymap_items.new(DMR_BoneSelectLessParent.bl_idname, type='NUMPAD_MINUS', value='PRESS', ctrl=True, shift=True)
        addon_keymaps.append((km, kmi))

def unregister():
    for c in reversed(classlist):
        bpy.utils.unregister_class(c)
    
    # Remove hotkeys
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
    register()