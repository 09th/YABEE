""" 
    Part of the YABEE
    rev 1.2
"""
import bpy
if __name__ != '__main__':
    from io_scene_egg.yabee_libs.utils import convertFileNameToPanda, save_image

BAKE_TYPES = {'diffuse': ('TEXTURE', 'MODULATE'),
              'normal': ('NORMALS', 'NORMAL'),
              'gloss': ('SPEC_INTENSITY', 'GLOSS'),
              'glow': ('EMIT', 'GLOW'),
              }

class SimpleTextures():
    
    def __init__(self, obj_list, uv_img_as_texture, copy_tex, file_path, tex_path):
        self.obj_list = obj_list[:]
        self.uv_img_as_texture = uv_img_as_texture
        self.copy_tex = copy_tex
        self.file_path = file_path
        self.tex_path = tex_path
        
    def get_used_textures(self):
        """ Collect images from the UV images and Material texture slots 
        tex_list structure:
            image_name: { 'scalars': [(name, val), (name, val), ...],
                          'path': 'path/to/texture'
                        }
        """
        tex_list = {}
        for obj in self.obj_list:
            if obj.type == 'MESH':
                # Texture from UV image
                if self.uv_img_as_texture:
                    for num, uv in enumerate(obj.data.uv_textures):
                        for f in uv.data:
                            #if f.use_image:
                            if f.image.source == 'FILE':
                                if not f.image.name in tex_list:
                                    name = uv.name
                                    if num == 0: name = ''
                                    t_path = bpy.path.abspath(f.image.filepath)
                                    if self.copy_tex:
                                        t_path = save_image(f.image, self.file_path, self.tex_path)
                                    #tex_list[f.image.name] = (name, t_path, 'MODULATE')
                                    tex_list[f.image.name] = {'path': t_path,
                                                              'scalars': [] }
                                    tex_list[f.image.name]['scalars'].append(('envtype', 'MODULATE'))
                                    if name:
                                        tex_list[f.image.name]['scalars'].append(('uv-name', name))
                # General textures
                for f in obj.data.faces:
                    if f.material_index < len(obj.data.materials):
                        for tex in obj.data.materials[f.material_index].texture_slots:
                            if ((tex) and (not tex.texture.use_nodes)):
                                if tex.texture_coords == 'UV' and obj.data.uv_textures:
                                    if tex.uv_layer:
                                        uv_name = tex.uv_layer
                                        if not [uv.name for uv in obj.data.uv_textures].index(uv_name):
                                            uv_name = ''
                                    else:
                                        uv_name = '' #obj.data.uv_textures[0].name
                                    if tex.texture.image and tex.texture.image.source == 'FILE':
                                        if not tex.texture.name in list(tex_list.keys()):
                                            #try:
                                                envtype = 'MODULATE'
                                                if tex.use_map_normal:
                                                    envtype = 'NORMAL'
                                                if tex.use_map_emit:
                                                    envtype = 'GLOW'
                                                if tex.use_map_specular:
                                                    envtype = 'GLOSS'
                                                t_path = bpy.path.abspath(tex.texture.image.filepath)
                                                if self.copy_tex:
                                                    t_path = save_image(tex.texture.image, self.file_path, self.tex_path)
                                                #tex_list[tex.texture.name] = (uv_name, t_path, envtype)
                                                tex_list[tex.texture.name] = {'path': t_path,
                                                                              'scalars': [] }
                                                tex_list[tex.texture.name]['scalars'].append(('envtype', envtype))
                                                if uv_name:
                                                    tex_list[tex.texture.name]['scalars'].append(('uv-name', uv_name))
                                            #except:
                                            #    print('ERROR: can\'t get texture image on %s.' % tex.texture.name)
        return tex_list
        

class TextureBaker():
    
    def __init__(self, obj_list, file_path, tex_path):
        self.saved_objs = {}
        self.rendered_images = {}
        self.obj_list = obj_list[:]
        self.file_path = file_path
        self.tex_path = tex_path
        
    def get_active_uv(self, obj):
        auv = [uv for uv in obj.data.uv_textures if uv.active]
        if auv:
            return auv[0]
        else:
            return None
        
    def _save_obj_props(self, obj):
        props = {'uvs':[], 'textures':{}}
        active_uv = self.get_active_uv(obj)
        if active_uv:
            for uvd in active_uv.data:
                #props['uvs'].append((uvd.use_image, uvd.image))
                props['uvs'].append(uvd.image)
        self.saved_objs[obj.name] = props
        
    def _restore_obj_props(self, obj):
        if obj.name in self.saved_objs.keys():
            props = self.saved_objs[obj.name]
            active_uv = self.get_active_uv(obj)
            if active_uv:
                for id, uvs in enumerate(props['uvs']):
                    uvd = active_uv.data[id]
                    #uvd.use_image, uvd.image = uvs
                    uvd.image = uvs

    def _prepare_images(self, btype, tsizex, tsizey):
        assigned_data = {}
        for obj in self.obj_list:
            if obj.type == 'MESH' and self.get_active_uv(obj):
                self._save_obj_props(obj)
                img = bpy.data.images.new(obj.name + '_' + btype, tsizex, tsizey)
                self.rendered_images[obj.name] = img.name
                active_uv = self.get_active_uv(obj)
                active_uv_idx = obj.data.uv_textures[:].index(active_uv)
                if active_uv:
                    for uvd in active_uv.data:
                        #uvd.use_image = True
                        uvd.image = img
                    assigned_data[obj.name + '_' + btype] = (active_uv, img, active_uv_idx, BAKE_TYPES[btype][1])
                else:
                    print('ERROR: %s have not active UV layer' % obj.name)
                    return None
        return assigned_data
        
    def _clear_images(self):
        for iname in self.rendered_images.values():
            img = bpy.data.images[iname]
            img.user_clear()
            bpy.data.images.remove(img)
        self.rendred_images = []
        
    def _save_rendered(self, spath):
        for oname, iname in self.rendered_images.items():
            img = bpy.data.images[iname]
            img.save_render(spath + iname + '.' + bpy.context.scene.render.file_format.lower())
            
    def _save_images(self):
        paths = {}
        for oname, iname in self.rendered_images.items():
            img = bpy.data.images[iname]
            paths[iname] = save_image(img, self.file_path, self.tex_path)
        return paths
        
    def _select(self, obj):
        obj.select = True
        
    def _deselect(self, obj):
        obj.select = False

               
    def bake(self, bake_layers):
        tex_list = {}
        for btype, params in bake_layers.items():
            if len(params) == 2:
                params = (params[0], params[0], params[1])
            if params[2]:
                if btype in BAKE_TYPES.keys():
                    paths = None
                    if len(self.obj_list) == 0:
                        return False
                    assigned_data = self._prepare_images(btype, params[0], params[1])
                    if assigned_data:
                        old_selected =  bpy.context.selected_objects[:]
                        #bpy.ops.object.select_all(action = 'DESELECT')
                        map(self._deselect, old_selected)
                        bpy.context.scene.render.bake_type = BAKE_TYPES[btype][0]
                        bpy.context.scene.render.bake_margin = 5
                        bpy.context.scene.render.image_settings.color_mode = 'RGBA'
                        bpy.context.scene.render.bake_normal_space = 'TANGENT'
                        #print(bpy.context.selected_objects[:])
                        map(self._select, self.obj_list)
                        #bpy.context.scene.update()
                        #print(bpy.context.selected_objects[:])
                        bpy.ops.object.bake_image()
                        #bpy.ops.object.select_all(action = 'DESELECT')
                        map(self._deselect, self.obj_list)
                        map(self._select, old_selected)
                        #self._save_rendered(save_path)
                        #self._save_rendered(bpy.app.tempdir)
                        paths = self._save_images()
                    for obj in self.obj_list:
                        self._restore_obj_props(obj)
                    self._clear_images()
                    for key, val in assigned_data.items():
                        uv_name = val[0].name
                        if val[2] == 0:
                            uv_name = ''
                        #img_path = bpy.app.tempdir + val[1].name + '.' + bpy.context.scene.render.file_format.lower()
                        #print('+++' + str(paths))
                        envtype = val[3]
                        if paths:
                            img_path = paths[key]
                        else:
                            img_path = self.tex_path + val[1].name + '.' + bpy.context.scene.render.file_format.lower()
                        #tex_list[key] = (uv_name, img_path, envtype)
                        # Texture information dict
                        tex_list[key] = {'path': img_path,
                                         'scalars': [] }
                        tex_list[key]['scalars'].append(('envtype', envtype))
                        if uv_name:
                            tex_list[key]['scalars'].append(('uv-name', uv_name))
                        if envtype in ('GLOW', 'GLOSS'):
                            tex_list[key]['scalars'].append(('alpha-file', '"' + img_path + '"'))
                else:
                    print('WARNING: unknown bake layer "%s"' % btype)
        return tex_list
                    
if __name__ == '__main__':
    import os, sys
    
    def convertFileNameToPanda(filename):
      """ (Get from Chicken) Converts Blender filenames to Panda 3D filenames.
      """
      path =  filename.replace('//', './').replace('\\', '/')
      if os.name == 'nt' and path.find(':') != -1:
        path = '/'+ path[0].lower() + path[2:]
      return path
      
    def save_image(img, file_path, text_path):
        oldpath = bpy.path.abspath(img.filepath)
        old_dir, old_f = os.path.split(convertFileNameToPanda(oldpath))
        f_names = [s.lower() for s in old_f.split('.')]
        if not f_names[-1] in ('jpg', 'png', 'tga', 'tiff', 'dds', 'bmp') and img.is_dirty:
            old_f += ('.' + bpy.context.scene.render.image_settings.file_format.lower())
        rel_path = os.path.join(text_path, old_f)
        if os.name == 'nt':
            rel_path = rel_path.replace('\\','/')
        new_dir, eg_f = os.path.split(file_path)
        new_dir = os.path.abspath(os.path.join(new_dir, text_path))
        if not os.path.exists(new_dir):
            os.makedirs(new_dir)
        if img.is_dirty:
            r_path = os.path.abspath(os.path.join(new_dir, old_f))
            img.save_render(r_path)
            print('RENDER IMAGE to %s; rel path: %s' % (r_path, rel_path))
        else:
            if os.path.exists(oldpath):
                #oldf = convertFileNameToPanda(oldpath)
                newf = os.path.join(new_dir, old_f)
                if oldpath != newf:
                    shutil.copyfile(oldpath, newf)
                    print('COPY IMAGE %s to %s; rel path %s' % (oldpath, newf, rel_path))
            else:
                if img.has_data:
                    img.filepath = os.path.abspath(os.path.join(new_dir, old_f))
                    print('SAVE IMAGE to %s; rel path: %s' % (img.filepath, rel_path))
                    img.save()
                    img.filepath == oldpath
        return rel_path
        
        
    tb = TextureBaker(bpy.context.selected_objects,'./exp_test/test.egg', './tex')
    print(tb.bake())
    st = SimpleTextures(bpy.context.selected_objects, False, False, './exp_test/test.egg', './tex')
    print(st.get_used_textures())
