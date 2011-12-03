bl_info = {
    "name": "Panda3d EGG format",
    "author": "Andrey (Ninth) Arbuzov",
    "blender": (2, 6, 0),
    "api": 41226,
    "location": "File > Import-Export",
    "description": ("Export to Panda3D EGG: meshes, uvs, materials, textures, "
                    "armatures, animation and curves"),
    "warning": "May contain bugs. Make backup of your file before use.",
    "wiki_url": ("http://www.panda3d.org/forums/viewtopic.php?t=11441"),
    "tracker_url": "yabee.googlecode.com",
    "category": "Import-Export"}

if "bpy" in locals():
    import imp
    imp.reload(io_scene_egg.yabee_libs.egg_writer)

import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.props import *

# --------------- Properties --------------------

class EGGBakeProperty(bpy.types.PropertyGroup):
    ''' Texture baker settings '''
    res_x = IntProperty(name = "Res. X", default=512)
    res_y = IntProperty(name = "Res. Y", default=512)
    export = BoolProperty(default = False)
    
    def draw(self, row, name):
        row.prop(self, "res_x")
        row.prop(self, "res_y")
        row.prop(self, "export")
        row.label(name)

class EGGAnimationProperty(bpy.types.PropertyGroup):
    ''' One animation record '''
    name = StringProperty(name="Name", default="Unknown")
    from_frame = IntProperty(name="From", default=1)
    to_frame = IntProperty(name="To", default=2)
    fps = IntProperty(name="FPS", default=24)
    
    def __get_idx(self):
        return list(bpy.context.scene.yabee_settings.opt_anim_list.anim_collection).index(self)
        
    index = property(__get_idx)

class EGGAnimList(bpy.types.PropertyGroup):
    ''' Animations list settings '''
    active_index = IntProperty()
    anim_collection = CollectionProperty(type=EGGAnimationProperty)
    
    def get_anim_dict(self):
        d = {}
        for anim in self.anim_collection:
            d[anim.name] = (anim.from_frame, anim.to_frame, anim.fps)
        return d


class YABEEProperty(bpy.types.PropertyGroup):
    ''' Main YABEE class for store settings '''
    opt_tex_proc = EnumProperty(
            name="Tex. processing",
            description="Export all textures as MODULATE or bake texture layers",
            items=(('SIMPLE', "Simple", "Export all texture layers."),
                   ('BAKE', "Bake", "Bake textures.")),
            default='BAKE',
            )
            
    opt_bake_diffuse = PointerProperty(type=EGGBakeProperty)
    opt_bake_normal = PointerProperty(type=EGGBakeProperty)
    opt_bake_gloss = PointerProperty(type=EGGBakeProperty)
    opt_bake_glow = PointerProperty(type=EGGBakeProperty)
    
            
    opt_tbs_proc = EnumProperty(
            name="TBS generation",
            description="Export all textures as MODULATE or bake texture layers",
            items=(('PANDA', "Panda", "Use egg-trans to calculate TBS (Need installed Panda3D)."),
                   ('INTERNAL', "Internal", "Use internal YABEE TBS generator"),
                   ('NO', "No", "Do not generate TBS.")),
            default='NO',
            )
            

    opt_export_uv_as_texture = BoolProperty(
            name="UV as texture",
            description="export uv image as texture",
            default=False,
            )
    
    opt_copy_tex_files = BoolProperty(
            name="Copy texture files",
            description="Copy texture files together with EGG",
            default=True,
            )
    
    opt_separate_anim_files = BoolProperty(
            name="Separate animation files",
            description="Write an animation data into the separate files",
            default=True,
            )

    opt_anim_only = BoolProperty(
            name="Animation only",
            description="Write only animation data",
            default=False,
            )

    opt_tex_path = StringProperty(
            name="Tex. path",
            description="Path for the copied textures. Relative to the main EGG file dir.",
            default='./tex',
            )
            
    opt_anim_list = PointerProperty(type=EGGAnimList)
    
    first_run = BoolProperty(default = True)
    
    def draw(self, layout):
        row = layout.row()
        row.operator("export.yabee_reset_defaults", icon="FILE_REFRESH", text="Reset to defaults")
        row.operator("export.yabee_help", icon="URL", text="Help")
        layout.row().label('Animation:')
        row = layout.row()
        row.template_list(self.opt_anim_list, 
                          "anim_collection", 
                          self.opt_anim_list, 
                          "active_index", 
                          rows=2)
        col = row.column(align=True)
        col.operator("export.egg_anim_add", icon='ZOOMIN', text="")
        col.operator("export.egg_anim_remove", icon='ZOOMOUT', text="")
        sett = self.opt_anim_list
        if len(sett.anim_collection):
            p = sett.anim_collection[sett.active_index]
            layout.row().prop(p, 'name')
            row = layout.row(align = True)
            row.prop(p, 'from_frame')
            row.prop(p, 'to_frame')
            row.prop(p, 'fps')
        layout.separator()
        layout.row().label('Options:')
        layout.row().prop(self, 'opt_anim_only')
        layout.row().prop(self, 'opt_separate_anim_files')
        if not self.opt_anim_only:
            if self.opt_tex_proc == 'SIMPLE':
                layout.row().prop(self, 'opt_export_uv_as_texture')
            if self.opt_copy_tex_files:
                box = layout.box()
                box.row().prop(self, 'opt_copy_tex_files')
                box.row().prop(self, 'opt_tex_path')
            else:
                layout.row().prop(self, 'opt_copy_tex_files')
            if self.opt_tex_proc == 'BAKE':
                box = layout.box()
                box.row().prop(self, 'opt_tex_proc')
                self.opt_bake_diffuse.draw(box.row(align = True), "Diffuse")
                self.opt_bake_normal.draw(box.row(align = True), "Normal")
                self.opt_bake_gloss.draw(box.row(align = True), "Gloss")
                self.opt_bake_glow.draw(box.row(align = True), "Glow")
            else:
                layout.row().prop(self, 'opt_tex_proc')
            layout.row().prop(self, 'opt_tbs_proc')
    
    def get_bake_dict(self):
        d = {}
        opts = ((self.opt_bake_diffuse, 'diffuse'),
                (self.opt_bake_normal, 'normal'),
                (self.opt_bake_gloss, 'gloss'),
                (self.opt_bake_glow, 'glow')
                )
        for opt, name in opts:
            d[name] = (opt.res_x, opt.res_y, opt.export)
        return d
    
    def check_warns(self, context):
        warns = []
        if len(context.selected_objects) == 0:
            warns.append('Nothing to export. Please, select "Mesh", \n' + \
                         '"Armature" or "Curve" objects.')
        return warns
        
    def reset_defaults(self):        
        self.opt_tex_proc = 'BAKE'
        self.opt_tbs_proc = 'NO'
        self.opt_bake_diffuse.export = True
        self.opt_bake_diffuse.res_x, self.opt_bake_diffuse.res_y = 512, 512
        self.opt_bake_normal.export = False
        self.opt_bake_normal.res_x, self.opt_bake_normal.res_y = 512, 512
        self.opt_bake_gloss.export = False
        self.opt_bake_gloss.res_x, self.opt_bake_gloss.res_y = 512, 512
        self.opt_bake_glow.export = False
        self.opt_bake_glow.res_x, self.opt_bake_glow.res_y = 512, 512
        self.opt_export_uv_as_texture = False
        self.opt_copy_tex_files = True
        self.opt_separate_anim_files = True
        self.opt_anim_only = False
        self.opt_tex_path = './tex'
        while self.opt_anim_list.anim_collection[:]:
            bpy.ops.export.egg_anim_remove('INVOKE_DEFAULT')
        self.first_run = False
    

#def write_some_data(context, filepath, use_some_setting):
#    print("running write_some_data...")
#    f = open(filepath, 'w')
#    f.write("Hello World %s" % use_some_setting)
#    f.close()

#    return {'FINISHED'}


# ------------------ Operators ----------------------------------
class YABEEHelp(bpy.types.Operator):
    bl_idname = "export.yabee_help"
    bl_label = "YABEE Help."
    
    def execute(self, context):
        bpy.ops.wm.url_open("INVOKE_DEFAULT", url="http://www.panda3d.org/forums/viewtopic.php?t=11441")
        return {"FINISHED"}
    
    
class WarnDialog(bpy.types.Operator):
    ''' Warning messages operator '''
    bl_idname = "export.yabee_warnings"
    bl_label = "YABEE Warnings."

    def draw(self, context):
        warns = context.scene.yabee_settings.check_warns(context)
        for warn in warns:
            for n, line in enumerate(warn.splitlines()):
                if n == 0:
                    self.layout.row().label(line, icon="ERROR")
                else:
                    self.layout.row().label('    ' + line, icon="NONE")

    def execute(self, context):
        #print("Dialog Runs")
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self) 


class ResetDefault(bpy.types.Operator):
    ''' Reset YABEE settings to default operator '''
    bl_idname = "export.yabee_reset_defaults"
    bl_label = "YABEE reset default settings"
    
    def execute(self, context):
        context.scene.yabee_settings.reset_defaults()
        return {'FINISHED'}


class AddAnim(bpy.types.Operator):
    ''' Add animation record operator '''
    bl_idname = "export.egg_anim_add"
    bl_label = "Add EGG animation"
    
    def execute(self, context):
        prop = context.scene.yabee_settings.opt_anim_list.anim_collection.add()
        prop.name = 'Anim'+str(prop.index)
        return {'FINISHED'}


class RemoveAnim(bpy.types.Operator):
    ''' Remove active animation record operator '''
    bl_idname = "export.egg_anim_remove"
    bl_label = "Remove EGG animation"
    
    def execute(self, context):
        sett = context.scene.yabee_settings.opt_anim_list
        sett.anim_collection.remove(sett.active_index)
        if len(sett.anim_collection):
            if sett.active_index not in [p.index for p in sett.anim_collection]:
                sett.active_index = sett.anim_collection[-1].index
        return {'FINISHED'}


class ExportPanda3DEGG(bpy.types.Operator, ExportHelper):
    ''' Export selected to the Panda3D EGG format '''
    bl_idname = "export.panda3d_egg"  
    bl_label = "Export to Panda3D EGG"

    # ExportHelper mixin class uses this
    filename_ext = ".egg"

    filter_glob = StringProperty(
            default="*.egg",
            options={'HIDDEN'},
            )

    #@classmethod       
    #def poll(cls, context):
    #    #return context.active_object is not None
    #    return len(context.selected_objects) > 0

    def execute(self, context):
        #return write_some_data(context, self.filepath, self.use_setting)
        import io_scene_egg.yabee_libs.egg_writer
        sett = context.scene.yabee_settings
        io_scene_egg.yabee_libs.egg_writer.write_out(self.filepath, 
                            sett.opt_anim_list.get_anim_dict(),
                            sett.opt_export_uv_as_texture, 
                            sett.opt_separate_anim_files, 
                            sett.opt_anim_only,
                            sett.opt_copy_tex_files, 
                            sett.opt_tex_path, 
                            3,
                            sett.opt_tbs_proc,
                            sett.opt_tex_proc,
                            sett.get_bake_dict())
        return {'FINISHED'}
        
    def invoke(self, context, evt):
        if context.scene.yabee_settings.first_run:
            context.scene.yabee_settings.reset_defaults()
        return ExportHelper.invoke(self, context, evt)
        
    def draw(self, context):
        warns = context.scene.yabee_settings.check_warns(context)
        if warns:
            self.layout.row().operator('export.yabee_warnings', icon='ERROR', text='Warning!')
        context.scene.yabee_settings.draw(self.layout)
        


def menu_func_export(self, context):
    self.layout.operator(ExportPanda3DEGG.bl_idname, text="Panda3D (.egg)")


def register():
    bpy.utils.register_module(__name__)

    # Good or bad, but I'll store settings in the scene
    bpy.types.Scene.yabee_settings = PointerProperty(type=YABEEProperty)

    bpy.types.INFO_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()

    # test call
    #bpy.ops.export.panda3d_egg('INVOKE_DEFAULT')
