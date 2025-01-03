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
from ..migoto.d3d11_game_type import D3D11GameType

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
    def __hash__(self):
        # Convert keys and values into immutable types that can be hashed
        immutable = tuple((k, tuple(v)) for k, v in sorted(self.items()))
        return hash(immutable)

    # def __hash__(self):
    #     # 这里将步骤拆分开来，更易于理解
    #     immutable_items = []
    #     for k, v in self.items():
    #         tuple_v = tuple(v)
    #         pair = (k, tuple_v)
    #         immutable_items.append(pair)
    #     sorted_items = sorted(immutable_items)
    #     immutable = tuple(sorted_items)
    #     return hash(immutable)

# 这个函数获取当前场景中选中的obj的用于导出的ib和vb文件
def get_export_ib_vb(context,d3d11GameType:D3D11GameType):
    # 获取Mesh并三角化
    obj = ObjUtils.get_bpy_context_object()
    mesh = obj.evaluated_get(context.evaluated_depsgraph_get()).to_mesh()
    mesh_triangulate(mesh)
    # Calculates tangents and makes loop normals valid (still with our custom normal data from import time):
    mesh.calc_tangents()

    # 通过d3d11GameType来获取layout，解决每个物体的3Dmigoto属性不一致的问题。
    tmp_stride = 0
    input_layout_elems = collections.OrderedDict()
    for d3d11_element_name in d3d11GameType.OrderedFullElementList:
        d3d11_element = d3d11GameType.ElementNameD3D11ElementDict[d3d11_element_name]
        input_layout_element = InputLayoutElement()
        input_layout_element.SemanticName = d3d11_element.SemanticName
        input_layout_element.SemanticIndex = d3d11_element.SemanticIndex
        input_layout_element.Format = d3d11_element.Format
        input_layout_element.AlignedByteOffset = tmp_stride
        tmp_stride = tmp_stride + d3d11_element.ByteWidth
        input_layout_element.InputSlotClass = d3d11_element.InputSlotClass
        input_layout_element.ElementName = d3d11_element.ElementName
        input_layout_element.format_len = MigotoUtils.format_components(input_layout_element.Format)

        input_layout_element.initialize_encoder_decoder()

        input_layout_elems[input_layout_element.ElementName] = input_layout_element
    
    # layout = InputLayout(obj['3DMigoto:VBLayout'], stride=tmp_stride)

    layout = InputLayout()
    layout.elems = input_layout_elems
    layout.stride = tmp_stride

    # Nico: 拼凑texcoord层级，有几个UVMap就拼出几个来
    texcoord_layers = {}
    for uv_layer in mesh.uv_layers:
        texcoords = {}
        # 因为导入时固定会翻转UV，所以导出时也要翻转UV
        # 导入时固定会翻转UV的原因是，3Dmigoto Dump出来的贴图都是正好相反的。
        flip_uv = lambda uv: (uv[0], 1.0 - uv[1])
        for l in mesh.loops:
            uv = flip_uv(uv_layer.data[l.index].uv)
            texcoords[l.index] = uv
        texcoord_layers[uv_layer.name] = texcoords

    # print("导出不改变顶点数：" + str(GenerateModConfig.export_same_number()))
    indexed_vertices = collections.OrderedDict()
    unique_position_vertices = {}
    ib = IndexBuffer()
    for poly in mesh.polygons:
        face = []
        for blender_lvertex in mesh.loops[poly.loop_start:poly.loop_start + poly.loop_total]:
            vertex = blender_vertex_to_3dmigoto_vertex(mesh, obj, blender_lvertex, layout, texcoord_layers)
            if GenerateModConfig.export_same_number():
                if "POSITION" in vertex and "NORMAL" in vertex and "TANGENT" in vertex :
                    if tuple(vertex["POSITION"] + vertex["NORMAL"] ) in unique_position_vertices:
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

    # print("IB UniqueVertexCount: " + str(ib.get_unique_vertex_number()))
    # print("IndexedVertices Number: " + str(len(indexed_vertices)))
    # print("unique_position_vertices Number: " + str(len(unique_position_vertices)))
    vb = VertexBuffer(layout=layout)
    for vertex in indexed_vertices:
        vb.append(vertex)
  
    # Nico: 重计算TANGENT
    # 含有这个属性的情况下才能计算这个属性。
    if layout.contains("TANGENT"):
        if GenerateModConfig.recalculate_tangent():
            # print("导出时重新计算TANGENT(全局设置)")
            vb.vector_normalized_normal_to_tangent()
        elif obj.get("3DMigoto:RecalculateTANGENT",False):
            # operator.report({'INFO'},"导出时重新计算TANGENT")
            # print("导出时重新计算TANGENT")
            vb.vector_normalized_normal_to_tangent()

    # Nico: 重计算COLOR
    if layout.contains("COLOR"):
        if GenerateModConfig.recalculate_color():
            # print("导出时重新计算COLOR(全局设置)")
            vb.arithmetic_average_normal_to_color()
        elif obj.get("3DMigoto:RecalculateCOLOR",False):
            # operator.report({'INFO'},"导出时重新计算COLOR")
            # print("导出时重新计算COLOR")
            vb.arithmetic_average_normal_to_color()
    return ib, vb


