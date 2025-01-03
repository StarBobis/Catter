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
    '''
    根据循环顶点中的顶点索引来从总的顶点中获取对应的顶点
    这里是对每个顶点都执行一次，所以资源消耗非常敏感，不能再这里加任何额外的判断。
    '''
    blender_vertex = mesh.vertices[blender_loop_vertex.vertex_index]
    vertex_groups = sorted(blender_vertex.groups, key=lambda x: x.weight, reverse=True)

    vertex = {}
    for elem in layout:
        # TODO 只处理per-vertex的，这里凭白多一个判断，浪费时间，InputSlotClass永远都是per-vertex没必要再判断
        # 后期在完全移除InputSlotClass后，再把这里的注释去掉
        # if elem.InputSlotClass != 'per-vertex':
        #     continue
        if elem.name == 'POSITION':
            vertex[elem.name] = elem.pad(list(blender_vertex.undeformed_co), 1.0)
        elif elem.name == 'NORMAL':
            vertex[elem.name] = elem.pad(list(blender_loop_vertex.normal), 0.0)

            # XXX 对于NORMAL的x,y,z,w翻转测试，只有开发时会出现，不应该让用户体验到计算延迟
            # 所以注释掉，只在测试的时候打开
            # if GenerateModConfig.flip_normal_x():
            #     vertex[elem.name][0] = -1 * vertex[elem.name][0]
            # if GenerateModConfig.flip_normal_y():
            #     vertex[elem.name][1] = -1 * vertex[elem.name][1]
            # if GenerateModConfig.flip_normal_z():
            #     vertex[elem.name][2] = -1 * vertex[elem.name][2]
            # if GenerateModConfig.flip_normal_w():
            #     if len(vertex[elem.name]) == 4:
            #         vertex[elem.name][3] = -1 * vertex[elem.name][3]

        elif elem.name.startswith('TANGENT'):
            # Nico: Unity games need to flip TANGENT.w to get perfect shadow.
            vertex[elem.name] = elem.pad(list(blender_loop_vertex.tangent), blender_loop_vertex.bitangent_sign)

            # XXX 对于TANGENT的x,y,z翻转测试，只有开发时会出现，不应该让用户体验到计算延迟
            # 所以注释掉，只在测试的时候打开
            # if GenerateModConfig.flip_tangent_x():
            #     vertex[elem.name][0] = -1 * vertex[elem.name][0]
            # if GenerateModConfig.flip_tangent_y():
            #     vertex[elem.name][1] = -1 * vertex[elem.name][1]
            # if GenerateModConfig.flip_tangent_z():
            #     vertex[elem.name][2] = -1 * vertex[elem.name][2]

            if GenerateModConfig.flip_tangent_w():
                vertex[elem.name][3] = -1 * vertex[elem.name][3]
        elif elem.name.startswith('COLOR'):
            if elem.name not in mesh.vertex_colors:
                raise Fatal("当前obj ["+ obj.name +"] 缺少游戏渲染所需的COLOR: ["+  elem.name + "]")
            
            if elem.name in mesh.vertex_colors:
                vertex[elem.name] = elem.clip(list(mesh.vertex_colors[elem.name].data[blender_loop_vertex.index].color))
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
                # 这里如果找不到对应TEXCOORD的话，就提示用户补充
                elif uv_name.endswith('.zw'):
                    # 不需要考虑.zw的情况
                    pass
                else:
                    raise Fatal("当前obj ["+ obj.name +"] 缺少游戏渲染所需的UV: ["+  uv_name + "]")
            vertex[elem.name] = uvs
        # Nico: 不需要考虑BINORMAL，现代游戏的渲染基本上不会使用BINORMAL这种过时的渲染方案
        # TODO 燕云十六声使用了BINORMAL
        # elif elem.name.startswith('BINORMAL'):
        #     # Some DOA6 meshes (skirts) use BINORMAL, but I'm not certain it is
        #     # actually the binormal. These meshes are weird though, since they
        #     # use 4 dimensional positions and normals, so they aren't something
        #     # we can really deal with at all. Therefore, the below is untested,
        #     # FIXME: So find a mesh where this is actually the binormal,
        #     # uncomment the below code and test.
        #     # normal = blender_loop_vertex.normal
        #     # tangent = blender_loop_vertex.tangent
        #     # binormal = numpy.cross(normal, tangent)
        #     # XXX: Does the binormal need to be normalised to a unit vector?
        #     # binormal = binormal / numpy.linalg.norm(binormal)
        #     # vertex[elem.name] = elem.pad(list(binormal), 0.0)
        #     pass
        # else:
            # 如果属性不在已知范围内，不做任何处理。
            # pass
        
        # 这里资源紧张，不应该浪费时间打印这个，每个点都打印一次那得多少次啊。
        # 而且走DBMT标准流程得到的内容，ELementName一定会在vertex里出现
        # if elem.name not in vertex:
        #     print('NOTICE: Unhandled vertex element: %s' % elem.name)
        # else:
        #    print('%s: %s' % (elem.name, repr(vertex[elem.name])))

    return vertex


class HashableVertex(dict):
    # 旧的代码注释掉了，不过不删，留着用于参考防止忘记原本的设计
    def __hash__(self):
        # Convert keys and values into immutable types that can be hashed
        immutable = tuple((k, tuple(v)) for k, v in sorted(self.items()))
        return hash(immutable)

    # 这里将步骤拆分开来，更易于理解，不要删这段代码，留着参考来理解原理
    # def __hash__(self):
    #     
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
    TimerUtils.Start("GetExportIBVB")

    # 获取Mesh并三角化
    obj = ObjUtils.get_bpy_context_object()

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

        # 校验并补全所有COLOR的存在
        if d3d11_element_name.startswith("COLOR"):
            if d3d11_element_name not in obj.data.vertex_colors and input_layout_elems.get(d3d11_element_name,None) is not None:
                obj.data.vertex_colors.new(name=d3d11_element_name)
                print("当前obj ["+ obj.name +"] 缺少游戏渲染所需的COLOR: ["+  "COLOR" + "]，已自动补全")
        
        # 校验TEXCOORD是否存在
        if d3d11_element_name.startswith("TEXCOORD"):
            if d3d11_element_name + ".xy" not in obj.data.uv_layers:
                # 此时如果只有一个UV，则自动改名为TEXCOORD.xy
                if len(obj.data.uv_layers) == 1 and d3d11_element_name == "TEXCOORD":
                        obj.data.uv_layers[0].name = d3d11_element_name + ".xy"
                else:
                    obj.data.uv_layers.new(name=d3d11_element_name + ".xy")
                    # raise Fatal("当前obj ["+ obj.name +"] 缺少游戏渲染所需的UV: ["+  d3d11_element_name + ".xy" + "] 请手动设置一下")

    layout = InputLayout()
    layout.elems = input_layout_elems
    layout.stride = tmp_stride

    # Nico: 通过evaluated_get获取到的是一个新的mesh
    mesh = obj.evaluated_get(context.evaluated_depsgraph_get()).to_mesh()
    # 注意这个三角化之后就变成新的mesh了
    mesh_triangulate(mesh)
    # Calculates tangents and makes loop normals valid (still with our custom normal data from import time):
    mesh.calc_tangents()

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


    TimerUtils.End("GetExportIBVB")
    return ib, vb


