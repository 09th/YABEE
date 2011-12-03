""" 
    Part of the YABEE
    rev 1
"""
import bpy, os, sys, shutil

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
        old_f += ('.' + bpy.context.scene.render.file_format.lower())
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
            img.filepath = os.path.abspath(os.path.join(new_dir, old_f))
            print('SAVE IMAGE to %s; rel path: %s' % (img.filepath, rel_path))
            img.save()
            img.filepath == oldpath
    return rel_path

def get_active_uv(obj):
    auv = [uv for uv in obj.data.uv_textures if uv.active]
    if auv:
        return auv[0]
    else:
        return None
