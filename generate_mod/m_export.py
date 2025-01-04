from ..utils.collection_utils import *
from ..utils.json_utils import *
from ..utils.obj_utils import ObjUtils
from ..utils.timer_utils import *

from ..import_model.input_layout import *
from ..import_model.vertex_buffer import *
from ..import_model.index_buffer import *

from ..migoto.d3d11_game_type import D3D11GameType


def blender_vertex_to_3dmigoto_vertex(mesh, blender_loop_vertex, layout:InputLayout, texcoords):
    blender_vertex = mesh.vertices[blender_loop_vertex.vertex_index]
    vertex_groups = sorted(blender_vertex.groups, key=lambda x: x.weight, reverse=True)
    vertex = {}
    for elem in layout:
        if elem.name == 'POSITION':
            vertex[elem.name] = elem.pad(list(blender_vertex.undeformed_co), 1.0)
        elif elem.name == 'NORMAL':
            vertex[elem.name] = elem.pad(list(blender_loop_vertex.normal), 0.0)
        elif elem.name.startswith('TANGENT'):
            # 由于在导入时翻转了UV，导致计算TANGENT后bitangent_sign的方向是相反的，所以这里导出时必须要翻转bitangent_sign
            vertex[elem.name] = list(blender_loop_vertex.tangent)
            vertex[elem.name].append(-1 * blender_loop_vertex.bitangent_sign)
        elif elem.name.startswith('COLOR'):
            if elem.name in mesh.vertex_colors:
                vertex[elem.name] = elem.clip(list(mesh.vertex_colors[elem.name].data[blender_loop_vertex.index].color))
        elif elem.name.startswith('BLENDINDICES'):
            i = elem.SemanticIndex * 4
            vertex[elem.name] = elem.pad([x.group for x in vertex_groups[i:i + 4]], 0)
        elif elem.name.startswith('BLENDWEIGHT'):
            i = elem.SemanticIndex * 4
            vertex[elem.name] = elem.pad([x.weight for x in vertex_groups[i:i + 4]], 0.0)
        elif elem.name.startswith('TEXCOORD') and elem.is_float():
            uvs = []
            for uv_name in ('%s.xy' % elem.name, '%s.zw' % elem.name):
                if uv_name in texcoords:
                    uvs += list(texcoords[uv_name][blender_loop_vertex.index])
            vertex[elem.name] = uvs
    return vertex


class HashableVertex(dict):
    def __hash__(self):
        # Convert keys and values into immutable types that can be hashed
        immutable = tuple((k, tuple(v)) for k, v in sorted(self.items()))
        return hash(immutable)


def get_export_ib_vb(d3d11GameType:D3D11GameType):
    '''
    这个函数获取当前场景中选中的obj的用于导出的ib和vb文件

    TODO 现有的架构会先转换为.ib .vb格式，随后再转换为Buffer格式，1000个顶点大约需要1秒，在频繁需要刷权重的情况下是无法忍受的
    这个现有的架构已经优化到极限无法在不改变易读性的情况下继续优化执行速度了。
    尤其是对每个顶点进行Hashable操作，而且在每个顶点中都遍历处理一遍layout的每个元素，这相当于把一个简单的事情二维展开，变得非常复杂。
    虽然易于理解，但是执行速度特别慢，所以计算使用numpy，改为从mesh中直接一步得到对应Buffer数据，因为每个Buffer的数据类型是固定的，又可以省去python自带列表的类型推断开销。
    TODO 所以现在应该学习numpy的使用，学会后再来优化这里。
    '''
    # TimerUtils.Start("GetExportIBVB")

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
    mesh = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    # 注意这个三角化之后就变成新的mesh了
    ObjUtils.mesh_triangulate(mesh)
    # Calculates tangents and makes loop normals valid (still with our custom normal data from import time):
    mesh.calc_tangents()

    # Nico: 拼凑texcoord层级，有几个UVMap就拼出几个来
    texcoord_layers = {}
    for uv_layer in mesh.uv_layers:
        texcoords = {}
        flip_uv = lambda uv: (uv[0], 1.0 - uv[1])
        for l in mesh.loops:
            uv = flip_uv(uv_layer.data[l.index].uv)
            texcoords[l.index] = uv
        texcoord_layers[uv_layer.name] = texcoords

    indexed_vertices = collections.OrderedDict()
    unique_position_vertices = {}
    ib = IndexBuffer()
    for poly in mesh.polygons:
        face = []
        for blender_lvertex in mesh.loops[poly.loop_start:poly.loop_start + poly.loop_total]:
            # blender_vertex = mesh.vertices[blender_lvertex.vertex_index]
            vertex = blender_vertex_to_3dmigoto_vertex(mesh, blender_lvertex, layout, texcoord_layers)
            
            if GenerateModConfig.export_same_number():
                if "POSITION" in vertex and "NORMAL" in vertex and "TANGENT" in vertex :
                    if tuple(vertex["POSITION"] + vertex["NORMAL"] ) in unique_position_vertices:
                        tangent_var = unique_position_vertices[tuple(vertex["POSITION"] + vertex["NORMAL"])]
                        vertex["TANGENT"] = tangent_var
                    else:
                        tangent_var = vertex["TANGENT"]
                        unique_position_vertices[tuple(vertex["POSITION"] + vertex["NORMAL"])] = tangent_var
                        vertex["TANGENT"] = tangent_var
            face.append(indexed_vertices.setdefault(HashableVertex(vertex), len(indexed_vertices)))
        ib.append(face)
    print("IndexedVertices Number: " + str(len(indexed_vertices)))
    vb = VertexBuffer(layout=layout)
    for vertex in indexed_vertices:
        vb.append(vertex)
  
    # Nico: 重计算TANGENT
    # 含有这个属性的情况下才能计算这个属性。
    if layout.contains("TANGENT"):
        if GenerateModConfig.recalculate_tangent():
            vb.vector_normalized_normal_to_tangent()
        elif obj.get("3DMigoto:RecalculateTANGENT",False):
            vb.vector_normalized_normal_to_tangent()

    # Nico: 重计算COLOR
    if layout.contains("COLOR"):
        if GenerateModConfig.recalculate_color():
            vb.arithmetic_average_normal_to_color()
        elif obj.get("3DMigoto:RecalculateCOLOR",False):
            vb.arithmetic_average_normal_to_color()

    # TimerUtils.End("GetExportIBVB")
    return ib, vb


def write_to_file_test(file_name:str,data):
    file_path = "C:\\Users\\Administrator\\Desktop\\TestOutput\\" + file_name
    if isinstance(data,bytes):
        with open(file_path, 'wb') as file:
            file.write(data)
    else:
        with open(file_path, 'wb') as file:
            file.write(data.tobytes())

