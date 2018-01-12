""" Part of the YABEE
"""

import bpy
if __name__ != '__main__':
    from .utils import convertFileNameToPanda, save_image

BAKE_TYPES = {'diffuse': ('TEXTURE', 'MODULATE'),
              'normal': ('NORMALS', 'NORMAL'),
              'gloss': ('SPEC_INTENSITY', 'GLOSS'),
              'glow': ('EMIT', 'GLOW'),
              'AO': ('AO', 'MODULATE'),
              'shadow': ('SHADOW', 'MODULATE')
              }

class PbrTextures():
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
                          'path': 'path/to/texture',
                          'transform': [(type, val), (type, val), ...]
                        }
        """
        print("starting texture collection")
        tex_list = {}
        print( self.obj_list)
        for obj in self.obj_list:
            if obj.type == 'MESH':
                print("processing object",obj)
                use_uv_face_tex = False
                use_uv_face_tex_alpha = False
                # General textures
                handled = set()
                for f in obj.data.polygons:
                    #print("processing polygon",f)
                    if f.material_index < len(obj.data.materials):
                        #print("found material index")
                        mat = obj.data.materials[f.material_index]
                        if not mat or mat in handled:
                            continue
                        print("found new material")
                        handled.add(mat)
                        
                        nodeNames={"ColorTex":None, "RoughnessTex":None , "NormalTex":None, "SpecularDummyTex":None} ##we do need an empty for specular but it's added somewhere else
                        #let's crawl all links, find the ones connected to the PandaPBRNode, find the connected textures, use them.
                        for link in mat.node_tree.links:
                            if link.to_node.name == "Panda3D_RP_Diffuse_Mat": #if the link connects to the panda3ddiffuse node
                                print("found new panda3d diffuse node")
                                if link.to_socket.name in nodeNames.keys():  # and it connects to one of our known sockets...
                                    textureNode = link.from_node
                                    
                                    if textureNode.image == None:
                                        print("WARNING: Texture node has no image assigned", obj.name, link.to_socket.name)
                                        continue
                                        
                                    if not textureNode.inputs[0].is_linked:
                                        print("WARNING: Texture has no UV-INPUT", obj.name, link.to_socket.name)
                                        continue
                                    
                                    scalars = []
                                    
                                    for link2 in mat.node_tree.links: #we have to crawl the links again
                                        if link2.to_node == textureNode: #we finally found the uv-map connected to the texture we want
                                            uvNode = link2.from_node
                                            scalars.append(('uv-name', uvNode.uv_map))
                                            scalars.append(('envtype', "Modulate"))
                                            
                                            
                            #if tex.texture_coords == 'UV':
                            #   if tex.uv_layer:
                            #        uv_name = tex.uv_layer
                            #        if uv_name not in [uv.name for uv in obj.data.uv_textures]:
                            #            print("WARNING: Object has no uv-map:", obj.name)
                            #            uv_name = ''
                            
                                    t_path = textureNode.image.filepath
                                    if self.copy_tex:
                                        t_path = save_image(textureNode.image, self.file_path, self.tex_path)

                                    #tex_list[tex.texture.name] = {'path': t_path,
                                    #                              'scalars': scalars, 'transform': transform }
                                    transform = []
                                    

                                    #if(textureNode.use_mipmap): #todo: find the use_mipmap flag
                                    scalars.append(('minfilter', 'LINEAR_MIPMAP_LINEAR'))
                                    scalars.append(('magfilter', 'LINEAR_MIPMAP_LINEAR'))

                                    # Process wrap modes.
                                    if(textureNode.extension == 'EXTEND'):
                                        scalars.append(('wrap', 'CLAMP'))

                                    elif(textureNode.extension in ('CLIP', 'CLIP_CUBE')):
                                        scalars.append(('wrap', 'BORDER_COLOR'))
                                        scalars.append(('borderr', '1'))
                                        scalars.append(('borderg', '1'))
                                        scalars.append(('borderb', '1'))
                                        scalars.append(('bordera', '1'))

                                    elif(textureNode.extension in ('REPEAT', 'CHECKER')):
                                        scalars.append(('wrap', 'REPEAT'))

                                    # Process coordinate mapping using a matrix.
                                    mappings = (textureNode.texture_mapping.mapping_x, textureNode.texture_mapping.mapping_y, textureNode.texture_mapping.mapping_z)

                                    if mappings != ('X', 'Y', 'Z'):
                                        matrix = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]

                                        for col, mapping in enumerate(mappings):
                                            if mapping == 'Z' :
                                                # Z is not present when using UV coordinates. we always use uv for pbr so far
                                                mapping = 'NONE'

                                            if mapping == 'NONE':
                                                # It seems that Blender sets Z to 0.5 when it is not present.
                                                matrix[4 * 3 + col] = 0.5
                                            else:
                                                row = ord(mapping) - ord('X')
                                                matrix[4 * row + col] = 1

                                        transform.append(('Matrix4', matrix))

                                    # Process texture transformations.
                                    if(tuple(textureNode.texture_mapping.scale) != (1.0, 1.0, 1.0)):
                                        # Blender scales from the centre, so shift it before scaling and then shift it back.
                                        transform.append(('Translate', (-0.5, -0.5, -0.5)))
                                        transform.append(('Scale', tex.scale))
                                        transform.append(('Translate', (0.5, 0.5, 0.5)))

                                    if(tuple(textureNode.texture_mapping.translation) != (0.0, 0.0, 0.0)):
                                        transform.append(('Translate', texture_mapping.translation))
                                        
                                    #finally add everything to the list
                                    
                                    tex_list[textureNode.name] = {'path': t_path,
                                                                        'scalars': scalars, 'transform': transform }
                                    #let's not get into alpha with the diffuse material for now.
                                    #if(envtype == 'MODULATE'):
                                    #    if(alpha_tex and not alpha_map_assigned):
                                    #        alpha_map_assigned = True
                                    #        alpha_path = alpha_tex.texture.image.filepath
                                    #        if self.copy_tex:
                                    #            alpha_path = save_image(alpha_tex.texture.image, self.file_path, self.tex_path)
                                    #        scalars.append(('alpha-file', '\"%s\"' % convertFileNameToPanda(alpha_path) ))
                                    #        scalars.append(('alpha-file-channel', '4'))

                                    #        if(mat.game_settings.alpha_blend == 'CLIP'):
                                    #            scalars.append(('alpha', 'BINARY'))
                                    #        elif(mat.game_settings.alpha_blend == 'ADD'):
                                    #            scalars.append(('blend', 'add'))
                                #except:
                                #    print('ERROR: can\'t get texture image on %s.' % tex.texture.name)
        #print ("texture list ",tex_list)
        return tex_list


class SimpleTextures():

    def __init__(self, obj_list, uv_img_as_texture, copy_tex, file_path, tex_path):
        self.obj_list = obj_list[:]
        self.uv_img_as_texture = uv_img_as_texture
        self.copy_tex = copy_tex
        self.file_path = file_path
        self.tex_path = tex_path

    def is_slot_valid(self, tex):
        if ((tex) and (not tex.texture.use_nodes)):
            if tex.texture_coords in ('UV', 'GLOBAL', 'ORCO'):
                if tex.texture.type == 'IMAGE' and tex.texture.image and tex.texture.image.source == 'FILE':
                    return True

        return False

    def get_valid_slots(self, slots):
        valid_slots = []
        for tex in slots:
            if(self.is_slot_valid(tex)):
                valid_slots.append(tex)

        return valid_slots

    def get_alpha_slot(self, slots):
        for tex in slots:
            if(tex.use_map_alpha):
                return tex
        return None

    def get_active_uv_name(self, obj):
        auv = [uv for uv in obj.data.uv_textures if uv.active]
        if auv:
            return auv[0].name
        else:
            return ''

    def get_used_textures(self):
        """ Collect images from the UV images and Material texture slots
        tex_list structure:
            image_name: { 'scalars': [(name, val), (name, val), ...],
                          'path': 'path/to/texture',
                          'transform': [(type, val), (type, val), ...]
                        }
        """
        tex_list = {}
        for obj in self.obj_list:
            if obj.type == 'MESH':
                use_uv_face_tex = False
                use_uv_face_tex_alpha = False
                '''
                # Texture from UV image
                if self.uv_img_as_texture:
                    for num, uv in enumerate(obj.data.uv_textures):
                        for f in uv.data:
                            #if f.use_image:
                            if f.image and f.image.source == 'FILE':
                                #if not f.image.name in tex_list:
                                if not f.image.yabee_name in tex_list:
                                    name = uv.name
                                    if num == 0: name = ''
                                    t_path = bpy.path.abspath(f.image.filepath)
                                    if self.copy_tex:
                                        t_path = save_image(f.image, self.file_path, self.tex_path)
                                    tex_list[f.image.yabee_name] = {'path': t_path,
                                                              'scalars': [] }
                                    tex_list[f.image.yabee_name]['scalars'].append(('envtype', 'MODULATE'))
                                    if name:
                                        tex_list[f.image.yabee_name]['scalars'].append(('uv-name', name))
                '''
                # General textures
                handled = set()
                for f in obj.data.polygons:
                    if f.material_index < len(obj.data.materials):
                        mat = obj.data.materials[f.material_index]
                        if not mat or mat in handled:
                            continue
                        handled.add(mat)

                        valid_slots = self.get_valid_slots(mat.texture_slots)
                        if not valid_slots or mat.use_face_texture:
                            use_uv_face_tex = True
                        if mat.use_face_texture_alpha:
                            use_uv_face_tex_alpha = True
                        alpha_tex = self.get_alpha_slot(valid_slots)
                        alpha_map_assigned = False

                        for tex in valid_slots:
                            scalars = []
                            transform = []

                            if tex.texture_coords == 'UV':
                                if tex.uv_layer:
                                    uv_name = tex.uv_layer
                                    if uv_name not in [uv.name for uv in obj.data.uv_textures]:
                                        print("WARNING: Object has no uv-map:", obj.name)
                                        uv_name = ''
                                else:
                                    uv_name = '' #obj.data.uv_textures[0].name

                                if uv_name and uv_name != self.get_active_uv_name(obj):
                                    scalars.append(('uv-name', uv_name))

                            elif tex.texture_coords == 'ORCO':
                                # We generate a set of UVs for this elsewhere.
                                scalars.append(('uv-name', 'ORCO'))

                            elif tex.texture_coords == 'GLOBAL':
                                scalars.append(('tex-gen', 'WORLD_POSITION'))
                                # Scale to Panda's coordinate system
                                transform.append(('Translate', (1, 1, 1)))
                                transform.append(('Scale', (0.5, 0.5, 0.5)))

                            #if not tex.texture.name in list(tex_list.keys()):
                            if not tex.texture.yabee_name in list(tex_list.keys()):
                                #try:
                                    envtype = 'MODULATE'
                                    if tex.use_map_normal:
                                        envtype = 'NORMAL'
                                    if tex.use_map_emit:
                                        envtype = 'GLOW'
                                    if tex.use_map_specular:
                                        envtype = 'GLOSS'
                                    if tex.use_map_alpha and not tex.use_map_color_diffuse:
                                        continue
                                    scalars.append(('envtype', envtype))

                                    t_path = tex.texture.image.filepath
                                    if self.copy_tex:
                                        t_path = save_image(tex.texture.image, self.file_path, self.tex_path)

                                    #tex_list[tex.texture.name] = {'path': t_path,
                                    #                              'scalars': scalars, 'transform': transform }
                                    tex_list[tex.texture.yabee_name] = {'path': t_path,
                                                                        'scalars': scalars, 'transform': transform }

                                    if(tex.texture.use_mipmap):
                                        scalars.append(('minfilter', 'LINEAR_MIPMAP_LINEAR'))
                                        scalars.append(('magfilter', 'LINEAR_MIPMAP_LINEAR'))

                                    # Process wrap modes.
                                    if(tex.texture.extension == 'EXTEND'):
                                        scalars.append(('wrap', 'CLAMP'))

                                    elif(tex.texture.extension in ('CLIP', 'CLIP_CUBE')):
                                        scalars.append(('wrap', 'BORDER_COLOR'))
                                        scalars.append(('borderr', '1'))
                                        scalars.append(('borderg', '1'))
                                        scalars.append(('borderb', '1'))
                                        scalars.append(('bordera', '1'))

                                    elif(tex.texture.extension in ('REPEAT', 'CHECKER')):
                                        scalars.append(('wrap', 'REPEAT'))

                                    # Process coordinate mapping using a matrix.
                                    mappings = (tex.mapping_x, tex.mapping_y, tex.mapping_z)

                                    if mappings != ('X', 'Y', 'Z'):
                                        matrix = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]

                                        for col, mapping in enumerate(mappings):
                                            if mapping == 'Z' and tex.texture_coords == 'UV':
                                                # Z is not present when using UV coordinates.
                                                mapping = 'NONE'

                                            if mapping == 'NONE':
                                                # It seems that Blender sets Z to 0.5 when it is not present.
                                                matrix[4 * 3 + col] = 0.5
                                            else:
                                                row = ord(mapping) - ord('X')
                                                matrix[4 * row + col] = 1

                                        transform.append(('Matrix4', matrix))

                                    # Process texture transformations.
                                    if(tuple(tex.scale) != (1.0, 1.0, 1.0)):
                                        # Blender scales from the centre, so shift it before scaling and then shift it back.
                                        transform.append(('Translate', (-0.5, -0.5, -0.5)))
                                        transform.append(('Scale', tex.scale))
                                        transform.append(('Translate', (0.5, 0.5, 0.5)))

                                    if(tuple(tex.offset) != (0.0, 0.0, 0.0)):
                                        transform.append(('Translate', tex.offset))

                                    if(envtype == 'MODULATE'):
                                        if(alpha_tex and not alpha_map_assigned):
                                            alpha_map_assigned = True
                                            alpha_path = alpha_tex.texture.image.filepath
                                            if self.copy_tex:
                                                alpha_path = save_image(alpha_tex.texture.image, self.file_path, self.tex_path)
                                            scalars.append(('alpha-file', '\"%s\"' % convertFileNameToPanda(alpha_path) ))
                                            scalars.append(('alpha-file-channel', '4'))

                                            if(mat.game_settings.alpha_blend == 'CLIP'):
                                                scalars.append(('alpha', 'BINARY'))
                                            elif(mat.game_settings.alpha_blend == 'ADD'):
                                                scalars.append(('blend', 'add'))
                                #except:
                                #    print('ERROR: can\'t get texture image on %s.' % tex.texture.name)
                    else:
                        use_uv_face_tex = True

                    # use uv map image texture as face texture if appropriate flag
                    # checked, or material has not valid texture, or object has not material
                    if use_uv_face_tex:
                        for num, uv in enumerate(obj.data.uv_textures):
                            for f in uv.data:
                                if f.image and f.image.source == 'FILE':
                                    tex_name = '%s_%s' % (uv.name, f.image.yabee_name)
                                    if not tex_name in tex_list:
                                        name = uv.name
                                        if num == 0: name = ''
                                        t_path = bpy.path.abspath(f.image.filepath)
                                        if self.copy_tex:
                                            t_path = save_image(f.image, self.file_path, self.tex_path)
                                        tex_list[tex_name] = {'path': t_path, 'scalars': [] }
                                        tex_list[tex_name]['scalars'].append(('envtype', 'MODULATE'))
                                        tex_list[tex_name]['scalars'].append(('minfilter', 'LINEAR_MIPMAP_LINEAR'))
                                        tex_list[tex_name]['scalars'].append(('magfilter', 'LINEAR_MIPMAP_LINEAR'))
                                        tex_list[tex_name]['scalars'].append(('wrap', 'REPEAT'))
                                        if use_uv_face_tex_alpha:
                                            tex_list[tex_name]['scalars'].append(('alpha', 'BINARY'))
                                        if name:
                                            tex_list[tex_name]['scalars'].append(('uv-name', name))

        return tex_list




class RawTextures(SimpleTextures):


    def is_slot_valid(self, tex):
        if tex and tex.texture and tex.texture.type == 'IMAGE' \
               and tex.texture.image \
               and tex.texture.image.source == 'FILE':
            return True

        return False

    '''
    def get_used_textures(self):
        tex_list = {}
        for obj in self.obj_list:
            if obj.type == 'MESH':
                use_uv_face_tex = False
                use_uv_face_tex_alpha = False
                for material in obj.data.materials:
                    valid_slots = self.get_valid_slots(material.texture_slots)
                    if not valid_slots or mat.use_face_texture:
                        use_uv_face_tex = True
                    if mat.use_face_texture_alpha:
                        use_uv_face_tex_alpha = True
                    for tex in valid_slots:
                        scalars = []
                        transform = []
                        if not tex.texture.yabee_name in list(tex_list.keys()):
                            t_path = tex.texture.image.filepath
                            if self.copy_tex:
                                t_path = save_image(tex.texture.image, self.file_path, self.tex_path)

                            tex_list[tex.texture.yabee_name] = {'path': t_path,
                                                                'scalars': scalars,
                                                                'transform': transform }
                            if(tex.texture.use_mipmap):
                                scalars.append(('minfilter', 'LINEAR_MIPMAP_LINEAR'))
                                scalars.append(('magfilter', 'LINEAR_MIPMAP_LINEAR'))

                            # Process wrap modes.
                            if(tex.texture.extension == 'EXTEND'):
                                scalars.append(('wrap', 'CLAMP'))

                            elif(tex.texture.extension in ('CLIP', 'CLIP_CUBE')):
                                scalars.append(('wrap', 'BORDER_COLOR'))
                                scalars.append(('borderr', '1'))
                                scalars.append(('borderg', '1'))
                                scalars.append(('borderb', '1'))
                                scalars.append(('bordera', '1'))

                            elif(tex.texture.extension in ('REPEAT', 'CHECKER')):
                                scalars.append(('wrap', 'REPEAT'))

                            # Process coordinate mapping using a matrix.
                            mappings = (tex.mapping_x, tex.mapping_y, tex.mapping_z)

                            if mappings != ('X', 'Y', 'Z'):
                                matrix = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]

                                for col, mapping in enumerate(mappings):
                                    if mapping == 'Z' and tex.texture_coords == 'UV':
                                        # Z is not present when using UV coordinates.
                                        mapping = 'NONE'

                                    if mapping == 'NONE':
                                        # It seems that Blender sets Z to 0.5 when it is not present.
                                        matrix[4 * 3 + col] = 0.5
                                    else:
                                        row = ord(mapping) - ord('X')
                                        matrix[4 * row + col] = 1

                                transform.append(('Matrix4', matrix))

                            # Process texture transformations.
                            if(tuple(tex.scale) != (1.0, 1.0, 1.0)):
                                # Blender scales from the centre, so shift it before scaling and then shift it back.
                                transform.append(('Translate', (-0.5, -0.5, -0.5)))
                                transform.append(('Scale', tex.scale))
                                transform.append(('Translate', (0.5, 0.5, 0.5)))

                            if(tuple(tex.offset) != (0.0, 0.0, 0.0)):
                                transform.append(('Translate', tex.offset))

                            if(tex.use_map_alpha and material.game_settings.alpha_blend == 'CLIP'):
                                scalars.append(('alpha', 'BINARY'))
                if not obj.data.materials[:]:
                    use_uv_face_tex = True

                # use uv map image texture as face texture if appropriate flag
                # checked, or material has not valid texture, or object has not material
                if use_uv_face_tex:
                    for num, uv in enumerate(obj.data.uv_textures):
                        for f in uv.data:
                            if f.image and f.image.source == 'FILE':
                                #if not f.image.name in tex_list:
                                tex_name = '%s_%s' % (uv.name, f.image.yabee_name)
                                if not tex_name in tex_list:
                                    name = uv.name
                                    if num == 0: name = ''
                                    t_path = bpy.path.abspath(f.image.filepath)
                                    if self.copy_tex:
                                        t_path = save_image(f.image, self.file_path, self.tex_path)
                                    tex_list[tex_name] = {'path': t_path, 'scalars': [] }
                                    tex_list[tex_name]['scalars'].append(('envtype', 'MODULATE'))
                                    tex_list[tex_name]['scalars'].append(('minfilter', 'LINEAR_MIPMAP_LINEAR'))
                                    tex_list[tex_name]['scalars'].append(('magfilter', 'LINEAR_MIPMAP_LINEAR'))
                                    tex_list[tex_name]['scalars'].append(('wrap', 'REPEAT'))
                                    if use_uv_face_tex_alpha:
                                        tex_list[tex_name]['scalars'].append(('alpha', 'BINARY'))
                                    if name:
                                        tex_list[tex_name]['scalars'].append(('uv-name', name))

        return tex_list
        '''


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
        props = {'uvs':[], 'textures':{}, 'active_uv': None}
        active_uv = self.get_active_uv(obj)
        if active_uv:
            props['active_uv'] = active_uv
            for uvd in active_uv.data:
                #props['uvs'].append((uvd.use_image, uvd.image))
                props['uvs'].append(uvd.image)
        self.saved_objs[obj.name] = props

    def _restore_obj_props(self, obj):
        if obj.name in self.saved_objs.keys():
            props = self.saved_objs[obj.name]
            if props['active_uv']:
                obj.data.uv_textures.active = props['active_uv']
                obj.data.update()
                #obj.data.uv_layers.active = props['active_uv']
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
                img = bpy.data.images.new(obj.yabee_name + '_' + btype, tsizex, tsizey)
                self.rendered_images[obj.name] = img.name
                active_uv = self.get_active_uv(obj)
                active_uv_idx = obj.data.uv_textures[:].index(active_uv)
                if active_uv:
                    for uvd in active_uv.data:
                        #uvd.use_image = True
                        uvd.image = img
                    assigned_data[obj.yabee_name + '_' + btype] = (active_uv, img, active_uv_idx, BAKE_TYPES[btype][1])
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
                    if btype in ('AO', 'shadow'):
                        # Switch active UV layer to generated shadow layer
                        for obj in self.obj_list:
                            if obj.type == 'MESH' and 'yabee_shadow' in obj.data.uv_textures.keys():
                                obj.data.uv_textures.active = obj.data.uv_textures['yabee_shadow']
                                obj.data.update()
                                #obj.data.uv_layers.active = obj.data.uv_textures['yabee_shadow']
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
                                         'scalars': [],
                                         'transform': [] }
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
