from ..import_model.input_layout import *
from ..utils.collection_utils import *
from ..utils.json_utils import *
from ..utils.obj_utils import ObjUtils
from ..utils.timer_utils import *

import json
import os.path
import bpy

from bpy_extras.io_utils import ExportHelper
from bpy.props import BoolProperty, StringProperty

from ..import_model.vertex_buffer import *
from ..import_model.index_buffer import *


# from export_obj:
def mesh_triangulate(me):
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()


def blender_vertex_to_3dmigoto_vertex(mesh, obj, blender_loop_vertex, layout:InputLayout, texcoords):
    # 根据循环顶点中的顶点索引来从总的顶点中获取对应的顶点
    blender_vertex = mesh.vertices[blender_loop_vertex.vertex_index]
    vertex = {}

    # ignoring groups with weight=0.0
    vertex_groups = sorted(blender_vertex.groups, key=lambda x: x.weight, reverse=True)

    for elem in layout:
        # 只处理per-vertex的
        if elem.InputSlotClass != 'per-vertex':
            continue

        if elem.name == 'POSITION':
            vertex[elem.name] = elem.pad(list(blender_vertex.undeformed_co), 1.0)


        elif elem.name == 'NORMAL':
            vertex[elem.name] = elem.pad(list(blender_loop_vertex.normal), 0.0)

            if GenerateModConfig.flip_normal_x():
                vertex[elem.name][0] = -1 * vertex[elem.name][0]
            if GenerateModConfig.flip_normal_y():
                vertex[elem.name][1] = -1 * vertex[elem.name][1]
            if GenerateModConfig.flip_normal_z():
                vertex[elem.name][2] = -1 * vertex[elem.name][2]
            if GenerateModConfig.flip_normal_w():
                if len(vertex[elem.name]) == 4:
                    vertex[elem.name][3] = -1 * vertex[elem.name][3]

        elif elem.name.startswith('TANGENT'):
            # Nico: Unity games need to flip TANGENT.w to get perfect shadow.
            vertex[elem.name] = elem.pad(list(blender_loop_vertex.tangent), blender_loop_vertex.bitangent_sign)
            if GenerateModConfig.flip_tangent_x():
                vertex[elem.name][0] = -1 * vertex[elem.name][0]
            if GenerateModConfig.flip_tangent_y():
                vertex[elem.name][1] = -1 * vertex[elem.name][1]
            if GenerateModConfig.flip_tangent_z():
                vertex[elem.name][2] = -1 * vertex[elem.name][2]
            if GenerateModConfig.flip_tangent_w():
                vertex[elem.name][3] = -1 * vertex[elem.name][3]

        elif elem.name.startswith('COLOR'):
            if elem.name in mesh.vertex_colors:
                vertex[elem.name] = elem.clip(list(mesh.vertex_colors[elem.name].data[blender_loop_vertex.index].color))
            else:
                vertex[elem.name] = list(mesh.vertex_colors[elem.name + '.RGB'].data[blender_loop_vertex.index].color)[
                                    :3] + \
                                    [mesh.vertex_colors[elem.name + '.A'].data[blender_loop_vertex.index].color[0]]
                
        elif elem.name.startswith('BLENDINDICES'):
            i = elem.SemanticIndex * 4
            vertex[elem.name] = elem.pad([x.group for x in vertex_groups[i:i + 4]], 0)
        elif elem.name.startswith('BLENDWEIGHT'):
            i = elem.SemanticIndex * 4
            vertex[elem.name] = elem.pad([x.weight for x in vertex_groups[i:i + 4]], 0.0)
        elif elem.name.startswith('TEXCOORD') and elem.is_float():
            # FIXME: Handle texcoords of other dimensions
            uvs = []
            for uv_name in ('%s.xy' % elem.name, '%s.zw' % elem.name):
                if uv_name in texcoords:
                    uvs += list(texcoords[uv_name][blender_loop_vertex.index])
            vertex[elem.name] = uvs
        # Nico: 不需要考虑BINORMAL，现代游戏的渲染基本上不会使用BINORMAL这种过时的渲染方案
        # elif elem.name.startswith('BINORMAL'):
            # Some DOA6 meshes (skirts) use BINORMAL, but I'm not certain it is
            # actually the binormal. These meshes are weird though, since they
            # use 4 dimensional positions and normals, so they aren't something
            # we can really deal with at all. Therefore, the below is untested,
            # FIXME: So find a mesh where this is actually the binormal,
            # uncomment the below code and test.
            # normal = blender_loop_vertex.normal
            # tangent = blender_loop_vertex.tangent
            # binormal = numpy.cross(normal, tangent)
            # XXX: Does the binormal need to be normalised to a unit vector?
            # binormal = binormal / numpy.linalg.norm(binormal)
            # vertex[elem.name] = elem.pad(list(binormal), 0.0)
            # pass

        else:
            # 如果属性不在已知范围内，不做任何处理。
            pass

        if elem.name not in vertex:
            print('NOTICE: Unhandled vertex element: %s' % elem.name)
        # else:
        #    print('%s: %s' % (elem.name, repr(vertex[elem.name])))

    return vertex


class HashableVertex(dict):
    # 旧的代码注释掉了，不过不删，留着用于参考防止忘记原本的设计
    # def __hash__(self):
    #     # Convert keys and values into immutable types that can be hashed
    #     immutable = tuple((k, tuple(v)) for k, v in sorted(self.items()))
    #     return hash(immutable)

    def __hash__(self):
        # 这里将步骤拆分开来，更易于理解
        immutable_items = []
        for k, v in self.items():
            tuple_v = tuple(v)
            pair = (k, tuple_v)
            immutable_items.append(pair)
        sorted_items = sorted(immutable_items)
        immutable = tuple(sorted_items)
        return hash(immutable)

# 这个函数获取当前场景中选中的obj的用于导出的ib和vb文件
def get_export_ib_vb(context):
    obj = ObjUtils.get_bpy_context_object()

    stride = obj['3DMigoto:VBStride']
    layout = InputLayout(obj['3DMigoto:VBLayout'], stride=stride)

    # 获取Mesh
    mesh = obj.evaluated_get(context.evaluated_depsgraph_get()).to_mesh()
    # 使用bmesh复制出一个新mesh并三角化
    mesh_triangulate(mesh)

    # 构建ib
    ib = IndexBuffer("DXGI_FORMAT_R32_UINT")
    ib.gametypename = obj['3DMigoto:GameTypeName']

    # Calculates tangents and makes loop normals valid (still with our custom normal data from import time):
    # Nico: 这一步如果存在TANGENT属性则会导致顶点数量增加
    mesh.calc_tangents()


    # Nico: 拼凑texcoord层级，有几个UVMap就拼出几个来
    # TimerUtils.Start("texcoord_layers")
    texcoord_layers = {}
    for uv_layer in mesh.uv_layers:
        texcoords = {}

        try:
            flip_texcoord_v = obj['3DMigoto:' + uv_layer.name]['flip_v']
            if flip_texcoord_v:
                flip_uv = lambda uv: (uv[0], 1.0 - uv[1])
            else:
                flip_uv = lambda uv: uv
        except KeyError:
            flip_uv = lambda uv: uv

        for l in mesh.loops:
            uv = flip_uv(uv_layer.data[l.index].uv)
            texcoords[l.index] = uv
        texcoord_layers[uv_layer.name] = texcoords
    # TimerUtils.End("texcoord_layers") # 0:00:00.129772 



    # Blender's vertices have unique positions, but may have multiple
    # normals, tangents, UV coordinates, etc - these are stored in the
    # loops. To export back to DX we need these combined together such that
    # a vertex is a unique set of all attributes, but we don't want to
    # completely blow this out - we still want to reuse identical vertices
    # via the index buffer. There might be a convenience function in
    # Blender to do this, but it's easy enough to do this ourselves
    indexed_vertices = collections.OrderedDict()

    unique_position_vertices = {}
    '''
    Nico:
        顶点转换为3dmigoto类型的顶点再经过hashable后，如果存在TANGENT则会导致数量变多，不存在则不会导致数量变多。
        Nico: 初始的Vertex即使是经过TANGENT计算，数量也是和原来一样的
        但是这里使用了blender_lvertex导致了生成的HashableVertex不一样，因为其它都是固定的只有这个blender_lvertex会改变
        需要注意的是如果不计算TANGENT或者没有TANGENT属性时不会额外生成顶点
    '''
    for poly in mesh.polygons:
        face = []
        for blender_lvertex in mesh.loops[poly.loop_start:poly.loop_start + poly.loop_total]:
            #
            vertex = blender_vertex_to_3dmigoto_vertex(mesh, obj, blender_lvertex, layout, texcoord_layers)
            '''
            Nico:
                首先将当前顶点计算为Hash后的顶点然后如果该计算后的Hash顶点不存在，则插入到indexed_vertices里
                随后将该顶点添加到face[]里，索引为该顶点在字典里的索引
                这里我们把获取到的vertex的切线加到一个vertex:切线值的字典中
                如果vertex的顶点在字典中出现了，则返回字典中对应列表和当前值的平均值，否则不进行更新
                这样就能得到每个Position对应的平均切线，在切线值相同的情况下，就不会产生额外的多余顶点了。
                这里我选择简单的使用这个顶点第一次出现的TANGENT作为它的TANGENT，以此避免产生额外多余顶点的问题，后续可以优化为使用平均值作为TANGENT
            '''
            if GenerateModConfig.export_same_number():
                if "POSITION" in vertex and "NORMAL" in vertex and "TANGENT" in vertex :
                    if tuple(vertex["POSITION"] + vertex["NORMAL"]  ) in unique_position_vertices:
                        tangent_var = unique_position_vertices[tuple(vertex["POSITION"] + vertex["NORMAL"])]
                        vertex["TANGENT"] = tangent_var
                    else:
                        tangent_var = vertex["TANGENT"]
                        unique_position_vertices[tuple(vertex["POSITION"] + vertex["NORMAL"])] = tangent_var
                        vertex["TANGENT"] = tangent_var

            indexed_vertex = indexed_vertices.setdefault(HashableVertex(vertex), len(indexed_vertices))
            face.append(indexed_vertex)
        if ib is not None:
            ib.append(face)


    # TimerUtils.Start("get vb")
    vb = VertexBuffer(layout=layout)
    for vertex in indexed_vertices:
        vb.append(vertex)
    # TimerUtils.End("get vb") #  0:00:00.062375 
  
    # Nico: 重计算TANGENT
    if obj.get("3DMigoto:RecalculateTANGENT",False):
        # operator.report({'INFO'},"导出时重新计算TANGENT")
        # print("导出时重新计算TANGENT")
        vb.vector_normalized_normal_to_tangent()
    elif GenerateModConfig.recalculate_tangent():
        # print("导出时重新计算TANGENT(全局设置)")
        vb.vector_normalized_normal_to_tangent()


    # Nico: 重计算COLOR
    if obj.get("3DMigoto:RecalculateCOLOR",False):
        # operator.report({'INFO'},"导出时重新计算COLOR")
        # print("导出时重新计算COLOR")
        vb.arithmetic_average_normal_to_color()
    elif GenerateModConfig.recalculate_color():
        # print("导出时重新计算COLOR(全局设置)")
        vb.arithmetic_average_normal_to_color()
    
    return ib, vb


