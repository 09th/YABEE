""" 
    Part of the YABEE
    rev 1
"""
import bpy
from mathutils import *

class TBNGenerator():
    
    def __init__(self,obj):
        self.obj_ref = obj
        self.triangles = None
        self.uv_layers = None
        
    def generate(self):
        tris = []
        fidxs = 0
        for face in self.obj_ref.data.faces:            
            tris.append((face.vertices[0], 
                         face.vertices[1], 
                         face.vertices[2]))
            if len(face.vertices) > 3:
                tris.append((face.vertices[0], 
                             face.vertices[3], 
                             face.vertices[2]))
        uv_layers = []
        for uv_layer in self.obj_ref.data.uv_textures:
            layer = []
            for uv_face in uv_layer.data:
                layer.append((uv_face.uv[0],
                              uv_face.uv[1],
                              uv_face.uv[2]))
                if len(uv_face.uv) > 3:
                    layer.append((uv_face.uv[0],
                                  uv_face.uv[3],
                                  uv_face.uv[2]))
            uv_layers.append(layer)
        self.triangles = tris
        self.uv_layers = uv_layers
        vtx_tb = []
        for vtx in self.obj_ref.data.vertices:
            t_res = []
            b_res = []
            for tidx in range(len(self.triangles)):
                tr = self.triangles[tidx]
                if ((vtx.index == tr[0]) or 
                    (vtx.index == tr[1]) or 
                    (vtx.index == tr[2])):
                    tbs = self.get_triangle_basis(tidx)
                    for l in range(len(tbs)):
                        t,b = tbs[l]
                        if len(t_res) < l + 1:
                            t_res.append(t)
                            b_res.append(b)
                        else:
                            t_res[l] += t
                            b_res[l] += b
            for i in range(len(t_res)):
                t_res[i] /= len(t_res)
                t_res[i] = self.ortogonalize(vtx.normal, t_res[i])
                b_res[i] /= len(b_res)
                b_res[i] = self.ortogonalize(vtx.normal, b_res[i])
            vtx_tb.append((t_res,b_res))
        return vtx_tb
                             
   
    def get_triangle_basis(self, idx):
        tbs = []
        triangle = self.triangles[idx]
        c_mat = self.obj_ref.matrix_world.to_euler().to_matrix()
        #vtx0 = self.obj_ref.data.vertices[triangle[0]].co * c_mat
        #vtx1 = self.obj_ref.data.vertices[triangle[1]].co * c_mat
        #vtx2 = self.obj_ref.data.vertices[triangle[2]].co * c_mat
        vtx0 = c_mat * self.obj_ref.data.vertices[triangle[0]].co 
        vtx1 = c_mat * self.obj_ref.data.vertices[triangle[1]].co
        vtx2 = c_mat * self.obj_ref.data.vertices[triangle[2]].co
        v1 = vtx1 - vtx0
        v2 = vtx2 - vtx0
        vtxMat = (v1,v2)
        for layer in self.uv_layers:
            uvs = layer[idx]
            #uvs = sorted(uvs, key = lambda uv: Vector(uv).length)
            v1_u = uvs[1][0] - uvs[0][0]
            v1_v = uvs[1][1] - uvs[0][1]
            v2_u = uvs[2][0] - uvs[0][0]
            v2_v = uvs[2][1] - uvs[0][1]
            tmp = 1.0 / ((v1_u * v2_v) - (v2_u * v1_v))
            uvMat = ((v2_v * tmp, -v1_v * tmp),
                     (-v2_u * tmp, v1_u * tmp))
            tbMat = []
            tbMat.append([])
            #tbMatrix[0][0] = stMatrix[0][0] * pqMatrix[0][0] + stMatrix[0][1] * pqMatrix[1][0];
            tbMat[0].append(uvMat[0][0] * vtxMat[0][0] + uvMat[0][1] * vtxMat[1][0])
            #tbMatrix[0][1] = stMatrix[0][0] * pqMatrix[0][1] + stMatrix[0][1] * pqMatrix[1][1];
            tbMat[0].append(uvMat[0][0] * vtxMat[0][1] + uvMat[0][1] * vtxMat[1][1])
            #tbMatrix[0][2] = stMatrix[0][0] * pqMatrix[0][2] + stMatrix[0][1] * pqMatrix[1][2];
            tbMat[0].append(uvMat[0][0] * vtxMat[0][2] + uvMat[0][1] * vtxMat[1][2])
            tbMat.append([])
            #tbMatrix[1][0] = stMatrix[1][0] * pqMatrix[0][0] + stMatrix[1][1] * pqMatrix[1][0];
            tbMat[1].append(uvMat[1][0] * vtxMat[0][0] + uvMat[1][1] * vtxMat[1][0])
            #tbMatrix[1][1] = stMatrix[1][0] * pqMatrix[0][1] + stMatrix[1][1] * pqMatrix[1][1];
            tbMat[1].append(uvMat[1][0] * vtxMat[0][1] + uvMat[1][1] * vtxMat[1][1])
            #tbMatrix[1][2] = stMatrix[1][0] * pqMatrix[0][2] + stMatrix[1][1] * pqMatrix[1][2];
            tbMat[1].append(uvMat[1][0] * vtxMat[0][2] + uvMat[1][1] * vtxMat[1][2])
            tangent = Vector((tbMat[0][0],
                              tbMat[0][1],
                              tbMat[0][2]))
            binormal = Vector((tbMat[1][0],
                               tbMat[1][1],
                               tbMat[1][2]))
            tangent.normalize()
            #tangent.negate()
            binormal.normalize()
            #binormal.negate()
            tbs.append((tangent, binormal))
        return tbs
        
    def get_closest_point(self, a, b, p):
        c = p - a
        v = b - a
        d = v.length
        v.normalize()
        t = v.dot(c)
        if t < 0.0:
            return a
        if t > d:
            return b
        v *= t
        return a + v
        
    def ortogonalize(self, v1, v2):
        v2_proj_v1 = self.get_closest_point( v1, -v1, v2 )
        res = v2 - v2_proj_v1
        res.normalize()
        return res

if __name__ == "__main__":
    tbng = TBNGenerator(bpy.context.selected_objects[0])
    print(tbng.generate())
