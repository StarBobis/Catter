from ..utils.collection_utils import *
from ..utils.json_utils import *
from ..utils.obj_utils import ObjUtils
from ..utils.timer_utils import *

from ..import_model.input_layout import *
from ..import_model.vertex_buffer import *
from ..import_model.index_buffer import *

from ..migoto.d3d11_game_type import D3D11GameType

import numpy
import hashlib



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

def get_buffer_ib_vb_fast(d3d11GameType:D3D11GameType):
    '''
    使用Numpy直接从mesh中转换数据到目标格式Buffer
    TODO 完成此功能并全流程测试通过后删除上面的get_export_ib_vb函数
    并移除IndexBuffer和VertexBuffer中的部分方法例如encode、pad等，进一步减少复杂度。
    '''
    TimerUtils.Start("GetExportIBVB Fast")

    obj = ObjUtils.get_bpy_context_object()
    # Nico: 通过evaluated_get获取到的是一个新的mesh
    mesh = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    # 注意这个三角化之后就变成新的mesh了
    ObjUtils.mesh_triangulate(mesh)
    # Calculates tangents and makes loop normals valid (still with our custom normal data from import time):
    # 前提是有UVMap，否则会报错
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

    # 获取顶点位置数据
    vertices = mesh.vertices
    elementname_data_dict = {}
    for d3d11_element_name in d3d11GameType.OrderedFullElementList:
        d3d11_element = d3d11GameType.ElementNameD3D11ElementDict[d3d11_element_name]
        if d3d11_element_name == 'POSITION':
            positions = numpy.empty(len(vertices)*3, dtype=MigotoUtils.get_dtype_from_format(d3d11_element.Format))
            for i, v in enumerate(vertices):
                positions[i*3:(i+1)*3] = v.co[:]
            
            positions_data = positions.ravel()
            elementname_data_dict[d3d11_element_name] = positions_data
            # print("POSITION " + str(len(positions) * 4 / 12 )) 2807
            # write_to_file_test(obj.name + "-POSITION.buf", positions_data)
            # 已测试通过，数据正常
        elif d3d11_element_name == 'NORMAL':
            normals = numpy.empty(len(vertices)*3, dtype=MigotoUtils.get_dtype_from_format(d3d11_element.Format))
            for i, v in enumerate(vertices):
                normals[i*3:(i+1)*3] = v.normal[:]
            
            normals_data = normals.ravel()
            elementname_data_dict[d3d11_element_name] = normals_data
            # print("NORMAL " + str(len(normals) * 4 / 12)) 2807
            # write_to_file_test(obj.name + "-NORMAL.buf", normals_data)
            # 已测试通过，数据正常
        elif d3d11_element_name == 'TANGENT':
            numpy_dtype = MigotoUtils.get_dtype_from_format(d3d11_element.Format)
            loop_count = len(mesh.loops)

            # 预先创建输出数组
            output_tangents = numpy.empty(loop_count * 4, dtype=numpy_dtype)

            # 使用 foreach_get 批量获取切线和副切线符号数据
            tangents = numpy.empty(loop_count * 3, dtype=numpy_dtype)
            bitangent_signs = numpy.empty(loop_count, dtype=numpy_dtype)

            mesh.loops.foreach_get("tangent", tangents)
            mesh.loops.foreach_get("bitangent_sign", bitangent_signs)

            # 将副切线符号乘以 -1（因为在导入时翻转了UV，所以导出时必须翻转bitangent_signs）
            bitangent_signs *= -1

            # 将切线分量放置到输出数组中
            output_tangents[0::4] = tangents[0::3]  # x 分量
            output_tangents[1::4] = tangents[1::3]  # y 分量
            output_tangents[2::4] = tangents[2::3]  # z 分量
            output_tangents[3::4] = bitangent_signs  # w 分量 (副切线符号)
            tangents_data = output_tangents.ravel()
            elementname_data_dict[d3d11_element_name] = tangents_data
            # write_to_file_test(obj.name + "-TANGENT.buf", tangents_data)
            # 已测试通过，数据正常
        elif d3d11_element_name.startswith('COLOR'):
            if d3d11_element_name in mesh.vertex_colors:
                numpy_dtype = MigotoUtils.get_dtype_from_format(d3d11_element.Format)

                # 因为COLOR属性存储在Blender里固定是float32类型所以这里只能用numpy.float32
                result = numpy.zeros(len(mesh.loops), dtype=(numpy.float32, 4))
                mesh.vertex_colors[d3d11_element_name].data.foreach_get("color", result.ravel())

                # 我们需要转换为目标类型，所以获取encoder
                encoder, decoder = MigotoUtils.EncoderDecoder(d3d11_element.Format)
                # 将 result 展平为一维数组
                flat_result = result.ravel()
                # 编码为目标格式
                color_data = encoder(flat_result)
                elementname_data_dict[d3d11_element_name] = color_data
                # write_to_file_test(obj.name + "-"+ d3d11_element_name +".buf", color_data)
                # 已测试通过，数据正常
        elif d3d11_element_name.startswith('BLENDINDICES'):
            numpy_dtype = MigotoUtils.get_dtype_from_format(d3d11_element.Format)
            
            # 初始化 NumPy 数组用于存放混合索引数据
            blendindices = numpy.empty(len(vertices) * 4, dtype=numpy_dtype)

            # 将混合索引数据填充到 NumPy 数组中
            for i, v in enumerate(vertices):
                # 获取并排序顶点组中的索引，按照权重大小降序排列
                sorted_groups = sorted(v.groups, key=lambda x: x.weight, reverse=True)
                
                # 提取索引并确保我们总是有 4 个索引值，如果不足则用 0 填充
                indices = [x.group for x in sorted_groups] + [0] * max(0, 4 - len(sorted_groups))
                
                # 确保只取前 4 个索引值，以确保不会超出范围
                blendindices[i*4:(i+1)*4] = indices[:4]

            blendindices_data = blendindices.ravel()
            elementname_data_dict[d3d11_element_name] = blendindices_data
            # write_to_file_test(obj.name + "-"+ d3d11_element_name +".buf", blendindices_data)
            # 已测试通过，数据正常
        elif d3d11_element_name.startswith('BLENDWEIGHT'):
            numpy_dtype = MigotoUtils.get_dtype_from_format(d3d11_element.Format)
    
            # 初始化 NumPy 数组用于存放混合权重数据
            blendweights = numpy.empty(len(vertices) * 4, dtype=numpy_dtype)

            # 将混合权重数据填充到 NumPy 数组中
            for i, v in enumerate(vertices):
                # 获取并排序顶点组中的权重，按照权重大小降序排列
                sorted_weights = sorted((x.weight for x in v.groups), reverse=True)
                
                # 使用列表推导式确保我们总是有 4 个权重值，如果不足则用 0.0 填充
                weights = sorted_weights + [0.0] * max(0, 4 - len(sorted_weights))
                
                # 确保只取前 4 个权重值，以确保不会超出范围
                blendweights[i*4:(i+1)*4] = weights[:4]

            blendweights_data = blendweights.ravel()
            elementname_data_dict[d3d11_element_name] = blendweights_data
            # write_to_file_test(obj.name + "-"+ d3d11_element_name +".buf", blendweights_data)
            # 已测试通过，数据正常
        elif d3d11_element_name.startswith('TEXCOORD') and d3d11_element.Format.endswith('FLOAT'):
            # TODO 就剩TEXCOORD了
            for uv_name in ('%s.xy' % d3d11_element_name, '%s.zw' % d3d11_element_name):
                if uv_name in texcoord_layers:
                    print(uv_name) # TEXCOORD.xy
                    uv = numpy.empty(len(vertices)*2, dtype=numpy.float32)
                    for i, v in enumerate(texcoord_layers[uv_name].values()):
                        uv[i*2:(i+1)*2] = v[:]
                    elementname_data_dict[d3d11_element_name] = uv
    
    print(elementname_data_dict.keys())

    # # 假设 elementname_data_dict 已经根据上面的代码填充完毕
    # # 我们将创建一个新的字典来存储唯一的顶点和它们对应的索引
    # unique_vertices = {}
    # index_buffer = []

    # # 首先，我们需要确定哪些元素应该参与哈希计算。
    # # 这通常包括位置（POSITION）、法线（NORMAL）、纹理坐标（TEXCOORD）等。
    # # 在这里我们假设所有在elementname_data_dict中的元素都应该参与哈希计算。
    # elements_to_hash = list(elementname_data_dict.keys())

    # # 然后遍历所有的顶点
    # for vertex_index in range(len(vertices)):
    #     # 创建一个空字符串用于拼接顶点属性
    #     vertex_data_str = b''

    #     # 对于每个需要参与哈希计算的元素
    #     for element_name in elements_to_hash:
    #         # 获取该元素的数据
    #         data = elementname_data_dict[element_name]
    #         stride = d3d11GameType.ElementNameD3D11ElementDict[element_name].ByteWidth
            
    #         # 每个顶点的元素数据是连续存储的，所以我们可以直接切片获取对应的数据
    #         vertex_element_data = data[vertex_index*stride:(vertex_index+1)*stride]

    #         # 将顶点元素数据转换为字节串并添加到vertex_data_str中
    #         vertex_data_str += vertex_element_data.tobytes()

    #     # 使用哈希函数生成一个唯一的哈希值
    #     hash_value = hashlib.md5(vertex_data_str).hexdigest()

    #     if hash_value not in unique_vertices:
    #         # 如果哈希值不在unique_vertices中，则添加它，并分配一个新的索引
    #         new_index = len(unique_vertices)
    #         unique_vertices[hash_value] = new_index
    #     else:
    #         # 否则，使用已有的索引
    #         new_index = unique_vertices[hash_value]

    #     # 添加索引到索引缓冲区
    #     index_buffer.append(new_index)

    # # 将索引缓冲区转换为NumPy数组以方便后续使用
    # index_buffer_array = numpy.array(index_buffer, dtype=numpy.uint32)

    # # 输出结果
    # print("Index Buffer:", str(len(index_buffer_array)))

    # TODO 这里的问题在于，最终得到的数量比旧的方法生成的顶点索引数要少
    # 如果Hash方法没出问题的话，那就是生成每个Element数据的方法出问题了。
    # 先完成每个CategoryBuffer的输出，这样就能验证了，先确保每个CategoryBuffer的输出都是正确的。

    # 打开文件准备写入二进制数据  
    # 已测试，写入没问题


    TimerUtils.End("GetExportIBVB Fast")


    # # 通过d3d11GameType来获取layout，解决每个物体的3Dmigoto属性不一致的问题。
    # tmp_stride = 0
    # input_layout_elems = collections.OrderedDict()
    # for d3d11_element_name in d3d11GameType.OrderedFullElementList:
    #     d3d11_element = d3d11GameType.ElementNameD3D11ElementDict[d3d11_element_name]
    #     input_layout_element = InputLayoutElement()
    #     input_layout_element.SemanticName = d3d11_element.SemanticName
    #     input_layout_element.SemanticIndex = d3d11_element.SemanticIndex
    #     input_layout_element.Format = d3d11_element.Format
    #     input_layout_element.AlignedByteOffset = tmp_stride
    #     tmp_stride = tmp_stride + d3d11_element.ByteWidth
    #     input_layout_element.InputSlotClass = d3d11_element.InputSlotClass
    #     input_layout_element.ElementName = d3d11_element.ElementName
    #     input_layout_element.format_len = MigotoUtils.format_components(input_layout_element.Format)

    #     input_layout_element.initialize_encoder_decoder()

    #     input_layout_elems[input_layout_element.ElementName] = input_layout_element
    #     # 校验并补全所有COLOR的存在
    #     if d3d11_element_name.startswith("COLOR"):
    #         if d3d11_element_name not in obj.data.vertex_colors and input_layout_elems.get(d3d11_element_name,None) is not None:
    #             obj.data.vertex_colors.new(name=d3d11_element_name)
    #             print("当前obj ["+ obj.name +"] 缺少游戏渲染所需的COLOR: ["+  "COLOR" + "]，已自动补全")
        
    #     # 校验TEXCOORD是否存在
    #     if d3d11_element_name.startswith("TEXCOORD"):
    #         if d3d11_element_name + ".xy" not in obj.data.uv_layers:
    #             # 此时如果只有一个UV，则自动改名为TEXCOORD.xy
    #             if len(obj.data.uv_layers) == 1 and d3d11_element_name == "TEXCOORD":
    #                     obj.data.uv_layers[0].name = d3d11_element_name + ".xy"
    #             else:
    #                 obj.data.uv_layers.new(name=d3d11_element_name + ".xy")
    #                 # raise Fatal("当前obj ["+ obj.name +"] 缺少游戏渲染所需的UV: ["+  d3d11_element_name + ".xy" + "] 请手动设置一下")

    # layout = InputLayout()
    # layout.elems = input_layout_elems
    # layout.stride = tmp_stride



    # indexed_vertices = collections.OrderedDict()
    # unique_position_vertices = {}
    # ib = IndexBuffer()
    # for poly in mesh.polygons:
    #     face = []
    #     for blender_lvertex in mesh.loops[poly.loop_start:poly.loop_start + poly.loop_total]:
    #         vertex = blender_vertex_to_3dmigoto_vertex(mesh, blender_lvertex, layout, texcoord_layers)
    #         if GenerateModConfig.export_same_number():
    #             if "POSITION" in vertex and "NORMAL" in vertex and "TANGENT" in vertex :
    #                 if tuple(vertex["POSITION"] + vertex["NORMAL"] ) in unique_position_vertices:
    #                     tangent_var = unique_position_vertices[tuple(vertex["POSITION"] + vertex["NORMAL"])]
    #                     vertex["TANGENT"] = tangent_var
    #                 else:
    #                     tangent_var = vertex["TANGENT"]
    #                     unique_position_vertices[tuple(vertex["POSITION"] + vertex["NORMAL"])] = tangent_var
    #                     vertex["TANGENT"] = tangent_var
    #         face.append(indexed_vertices.setdefault(HashableVertex(vertex), len(indexed_vertices)))
    #     ib.append(face)
    # print("IndexedVertices Number: " + str(len(indexed_vertices)))
    # vb = VertexBuffer(layout=layout)
    # for vertex in indexed_vertices:
    #     vb.append(vertex)
  
    # # Nico: 重计算TANGENT
    # # 含有这个属性的情况下才能计算这个属性。
    # if layout.contains("TANGENT"):
    #     if GenerateModConfig.recalculate_tangent():
    #         vb.vector_normalized_normal_to_tangent()
    #     elif obj.get("3DMigoto:RecalculateTANGENT",False):
    #         vb.vector_normalized_normal_to_tangent()

    # # Nico: 重计算COLOR
    # if layout.contains("COLOR"):
    #     if GenerateModConfig.recalculate_color():
    #         vb.arithmetic_average_normal_to_color()
    #     elif obj.get("3DMigoto:RecalculateCOLOR",False):
    #         vb.arithmetic_average_normal_to_color()


    # return ib, vb
