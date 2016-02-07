"""
    Part of the YABEE rev 12.1
"""
import bpy, os, sys, shutil
import bpy_extras

def convertFileNameToPanda(filename):
  """ (Get from Chicken) Converts Blender filenames to Panda 3D filenames.
  """
  path =  filename.replace('//', './').replace('\\', '/')
  if os.name == 'nt' and path.find(':') != -1:
    path = '/'+ path[0].lower() + path[2:]
  return path

def save_image(img, file_path, text_path):
    if img.filepath:
        oldpath = bpy.path.abspath(img.filepath)
        old_dir, old_f = os.path.split(convertFileNameToPanda(oldpath))
        f_names = [s.lower() for s in old_f.split('.')]
        if not f_names[-1] in ('jpg', 'png', 'tga', 'tiff', 'dds', 'bmp') and img.is_dirty:
            old_f += ('.' + bpy.context.scene.render.image_settings.file_format.lower())
    else:
        oldpath = ''
        old_dir = ''
        old_f = img.name + '.' + bpy.context.scene.render.image_settings.file_format.lower()
    rel_path = os.path.join(text_path, old_f)
    if os.name == 'nt':
        rel_path = rel_path.replace(r"\\",r"/").replace('\\', '/')
    new_dir, eg_f = os.path.split(file_path)
    new_dir = os.path.abspath(os.path.join(new_dir, text_path))
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
    #print('IMG', img, img.packed_file)
    if img.is_dirty or bool(img.packed_file):
        try:
            bpy.context.scene.render.image_settings.color_mode = 'RGBA'
        except:
            bpy.context.scene.render.image_settings.color_mode = 'RGB'
        r_path = os.path.abspath(os.path.join(new_dir, old_f))
        img.save_render(r_path)
        print('RENDER IMAGE to %s; rel path: %s' % (r_path, rel_path))
    #elif bool(img.packed_file):
    #    r_path = os.path.abspath(os.path.join(new_dir, old_f))
    #    img.filepath = r_path
    #    img.unpack()
    #    img.filepath = oldpath
    #    print('UNPACK IMAGE to %s; rel path: %s' % (r_path, rel_path))
    else:
        newf = os.path.join(new_dir, old_f)
        if oldpath != newf:
            bpy_extras.io_utils.path_reference_copy(((oldpath.replace(r"\\", r"/"), newf),), report = print)
            print('COPY IMAGE %s to %s; rel path %s' % (oldpath, newf, rel_path))
    return rel_path

def get_active_uv(obj):
    auv = [uv for uv in obj.data.uv_textures if uv.active]
    if auv:
        return auv[0]
    else:
        return None

def eggSafeName(s):
    """ (Get from Chicken) Function that converts names into something
    suitable for the egg file format - simply puts " around names that
    contain spaces and prunes bad characters, replacing them with an
    underscore.
    """
    s = str(s).replace('"','_') # Sure there are more bad characters, but this will do for now.
    if ' ' in s:
      return '"' + s + '"'
    else:
      return s
