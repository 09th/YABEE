""" YABEE rev 12.0
"""
# -------------- Change this to setup parameters -----------------------
#: file name to write
FILE_PATH = './exp_test/test.egg'

#: { 'animation_name' : (start_frame, end_frame, frame_rate) }
ANIMATIONS = {'anim1':(0,10,5),
              }
ANIMS_FROM_ACTIONS = False

#: 'True' to interprete an image in the uv layer as the texture
EXPORT_UV_IMAGE_AS_TEXTURE = False

#: 'True' to copy texture images together with main.egg
COPY_TEX_FILES = True

#: Path for the copied textures. Relative to the main EGG file dir.
#: For example if main file path is '/home/username/test/test.egg',
#: texture path is './tex', then the actual texture path is
#: '/home/username/test/tex'
TEX_PATH = './tex'

#: 'True' to write an animation data into the separate files
SEPARATE_ANIM_FILE = True

#: 'True' to write only animation data
ANIM_ONLY = False

#: number of sign after point
FLOATING_POINT_ACCURACY = 3

#: Enable tangent space calculation. Tangent space needed for some
# shaders/autoshaders, but increase exporting time
# 'NO', 'INTERNAL', 'PANDA'
# 'INTERNAL' - use internal TBS calculation
# 'PANDA' - use egg-trans to calculate TBS
# 'NO' - do not calc TBS
CALC_TBS = 'PANDA'

#: Type of texture processing. May be 'SIMPLE' or 'BAKE'.
# 'SIMPLE' - export all texture layers as MODULATE.
# Exceptions:
#   use map normal == NORMAL
#   use map specular == GLOSS
#   use map emit == GLOW
# 'BAKE' - bake textures. BAKE_LAYERS setting up what will be baked.
# Also diffuse color of the material would set to (1,1,1) in the
# 'BAKE' mode
TEXTURE_PROCESSOR = 'BAKE'
#TEXTURE_PROCESSOR = 'SIMPLE'

# type: (size, do_bake)
BAKE_LAYERS = {'diffuse':(512, True),
               'normal':(512, True),
               'gloss': (512, True),    # specular
               'glow': (512, False)      # emission
               }
# ----------------------------------------------------------------------

import bpy, os, sys


if __name__ == '__main__':
    # Dirty hack. I can't get the script dir through the sys.argv[0] or __file__
    try:
        for text in bpy.data.texts:
            dir = os.path.dirname(text.filepath)
            if os.name == 'nt':
                dir = os.path.abspath(dir + '\\..')
            else:
                dir = os.path.abspath(dir + '/..')
            if dir not in sys.path:
                sys.path.append(os.path.abspath(dir))
    except:
        print('Error while trying to add a paths in the sys.path')

    import io_scene_egg.yabee_libs.egg_writer
    #from io_scene_egg.yabee_libs import egg_writer
    print('RELOADING MODULES')
    import imp
    imp.reload(io_scene_egg.yabee_libs.egg_writer)
    egg_writer = io_scene_egg.yabee_libs.egg_writer

    egg_write.write_out(FILE_PATH,
                        ANIMATIONS, ANIMS_FROM_ACTIONS,
                        EXPORT_UV_IMAGE_AS_TEXTURE,
                        SEPARATE_ANIM_FILE,
                        ANIM_ONLY,
                        COPY_TEX_FILES,
                        TEX_PATH,
                        CALC_TBS,
                        TEXTURE_PROCESSOR,
                        BAKE_LAYERS,
                        True, True, True,  # MERGE_ACTOR_MESH, APPLY_MOD, PVIEW
                        False, False, # USE_LOOP_NORMALS, EXPORT_PBS
                        False) # FORCE_EXPORT_VERTEX_COLORS
