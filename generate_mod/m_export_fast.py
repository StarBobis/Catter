import numpy
import hashlib
import bpy
import collections

from ..utils.collection_utils import CollectionUtils
from ..utils.json_utils import JsonUtils
from ..utils.obj_utils import ObjUtils
from ..utils.timer_utils import TimerUtils
from ..utils.log_utils import LOG

from ..migoto.d3d11_game_type import D3D11GameType
from ..migoto.migoto_utils import MigotoUtils

class BufferModel:
    
    def __init__(self) -> None:
        self.d3d11GameType:D3D11GameType = None
        self.elementname_data_dict = {}
        self.elementname_bytesdata_dict = {}

    def show(self):
        '''
        展示所有数据，仅用于测试开发
        '''
        for element_name,value in self.elementname_data_dict.items():
            print("key: " + element_name + " value: " + str(type(value)) + " data:" + str(type(value[0])) + " len:" + str(len(value)) + " shape: " + str(value.shape))
        LOG.newline()

        for element_name,value in self.elementname_bytesdata_dict.items():
            print("key: " + element_name + " value: " + str(type(value)) + " data:" + str(type(value[0])) + " len:" + str(len(value)) + " shape: " + str(value.shape))
        LOG.newline()
    
    def check_and_verify_attributes(self,obj:bpy.types.Object):
        '''
        校验并补全部分元素
        COLOR
        TEXCOORD、TEXCOORD1、TEXCOORD2、TEXCOORD3
        '''
        for d3d11_element_name in self.d3d11GameType.OrderedFullElementList:
            d3d11_element = self.d3d11GameType.ElementNameD3D11ElementDict[d3d11_element_name]
            # 校验并补全所有COLOR的存在
            if d3d11_element_name.startswith("COLOR"):
                if d3d11_element_name not in obj.data.vertex_colors:
                    obj.data.vertex_colors.new(name=d3d11_element_name)
                    print("当前obj ["+ obj.name +"] 缺少游戏渲染所需的COLOR: ["+  "COLOR" + "]，已自动补全")
            
            # 校验TEXCOORD是否存在
            if d3d11_element_name.startswith("TEXCOORD"):
                if d3d11_element_name + ".xy" not in obj.data.uv_layers:
                    # 此时如果只有一个UV，则自动改名为TEXCOORD.xy
                    if len(obj.data.uv_layers) == 1 and d3d11_element_name == "TEXCOORD":
                            obj.data.uv_layers[0].name = d3d11_element_name + ".xy"
                    else:
                        # 否则就自动补一个UV，防止后续calc_tangents失败
                        obj.data.uv_layers.new(name=d3d11_element_name + ".xy")
    
    def parse_elementname_ravel_ndarray_dict(self,mesh:bpy.types.Mesh) -> dict:
        '''
        这里转换出来基本上都是float32类型，占4个字节，只有BLENDINDICES是uint32类型，也占4个字节
        '''
        # Nico: 提前拼凑texcoord层级，有几个UVMap就拼出几个来，略微提升速度(虽然只提升几十毫秒。。)
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
        for d3d11_element_name in self.d3d11GameType.OrderedFullElementList:
            d3d11_element = self.d3d11GameType.ElementNameD3D11ElementDict[d3d11_element_name]
            if d3d11_element_name == 'POSITION':
                positions = numpy.empty(len(vertices)*3, dtype=MigotoUtils.get_dtype_from_format(d3d11_element.Format))
                for i, v in enumerate(vertices):
                    positions[i*3:(i+1)*3] = v.co[:]
                
                positions_data = positions.ravel()
                elementname_data_dict[d3d11_element_name] = positions_data

            elif d3d11_element_name == 'NORMAL':
                normals = numpy.empty(len(vertices)*3, dtype=MigotoUtils.get_dtype_from_format(d3d11_element.Format))
                for i, v in enumerate(vertices):
                    normals[i*3:(i+1)*3] = v.normal[:]
                
                normals_data = normals.ravel()
                elementname_data_dict[d3d11_element_name] = normals_data

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

            elif d3d11_element_name.startswith('COLOR'):
                if d3d11_element_name in mesh.vertex_colors:
                    numpy_dtype = MigotoUtils.get_dtype_from_format(d3d11_element.Format)
                    # 因为COLOR属性存储在Blender里固定是float32类型所以这里只能用numpy.float32
                    result = numpy.zeros(len(mesh.loops), dtype=(numpy.float32, 4))
                    mesh.vertex_colors[d3d11_element_name].data.foreach_get("color", result.ravel())

                    color_data = result.ravel()
                    elementname_data_dict[d3d11_element_name] = color_data
            elif d3d11_element_name.startswith('BLENDINDICES'):
                numpy_dtype = MigotoUtils.get_dtype_from_format(d3d11_element.Format)
                blendindices = numpy.empty(len(vertices) * 4, dtype=numpy_dtype)

                for i, v in enumerate(vertices):
                    sorted_groups = sorted(v.groups, key=lambda x: x.weight, reverse=True)
                    indices = [x.group for x in sorted_groups] + [0] * max(0, 4 - len(sorted_groups))
                    blendindices[i*4:(i+1)*4] = indices[:4]

                blendindices_data = blendindices.ravel()
                elementname_data_dict[d3d11_element_name] = blendindices_data

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

            elif d3d11_element_name.startswith('TEXCOORD') and d3d11_element.Format.endswith('FLOAT'):
                for uv_name in ('%s.xy' % d3d11_element_name, '%s.zw' % d3d11_element_name):
                    if uv_name in texcoord_layers:
                        uvs_array = numpy.array(list(texcoord_layers[uv_name].values()),dtype=numpy.float32).flatten()
                        elementname_data_dict[d3d11_element_name] = uvs_array.ravel()
        
        self.elementname_data_dict = elementname_data_dict

    def convert_ndarray_to_bytes(self):
        '''
        数据全部编码为目标格式
        '''
        elementname_bytesdata_dict = {}

        for element_name,value in self.elementname_data_dict.items():
            d3d11_element = self.d3d11GameType.ElementNameD3D11ElementDict[element_name]
            print("key: " + element_name + " value: " + str(type(value)) + " data:" + str(type(value[0])) + " len:" + str(len(value)) + " shape: " + str(value.shape))

            if element_name == 'POSITION':
                if d3d11_element.Format == 'R16G16B16A16_FLOAT':
                    # TODO 需要测试astype是否正常工作
                    elementname_bytesdata_dict[element_name] = value.astype(numpy.float16)
                else:
                    elementname_bytesdata_dict[element_name] = value
            elif element_name == 'NORMAL':
                if d3d11_element.Format == 'R16G16B16A16_FLOAT':
                    elementname_bytesdata_dict[element_name] = value.astype(numpy.float16)
                else:
                    elementname_bytesdata_dict[element_name] = value
            elif element_name == 'TANGENT':
                if d3d11_element.Format == 'R16G16B16A16_FLOAT':
                    elementname_bytesdata_dict[element_name] = value.astype(numpy.float16)
                else:
                    elementname_bytesdata_dict[element_name] = value
            elif element_name.startswith('COLOR'):
                if d3d11_element.Format == 'R16G16B16A16_FLOAT':
                    elementname_bytesdata_dict[element_name] = value.astype(numpy.float16)
                elif d3d11_element.Format == 'R8G8B8A8_UNORM':
                    elementname_bytesdata_dict[element_name] = value.astype(numpy.uint8)
                else:
                    elementname_bytesdata_dict[element_name] = value
            elif element_name.startswith('BLENDINDICES'):
                if d3d11_element.Format == 'R16G16B16A16_FLOAT':
                    elementname_bytesdata_dict[element_name] = value.astype(numpy.float16)
                else:
                    elementname_bytesdata_dict[element_name] = value
            elif element_name.startswith('BLENDWEIGHT'):
                if d3d11_element.Format == 'R16G16B16A16_FLOAT':
                    elementname_bytesdata_dict[element_name] = value.astype(numpy.float16)
                else:
                    elementname_bytesdata_dict[element_name] = value
            elif element_name.startswith('TEXCOORD'):
                if d3d11_element.Format == 'R16G16_FLOAT':
                    elementname_bytesdata_dict[element_name] = value.astype(numpy.float16)
                else:
                    elementname_bytesdata_dict[element_name] = value

        self.elementname_bytesdata_dict = elementname_bytesdata_dict
    
    def patch_data(self):
        '''
        补全数据，例如POSITION默认只有3个元素，如果Format为R16G16B16A16_FLOAT则需要补全为4个元素，末尾补0
        例如NROMAL只有3个元素，部分游戏Format为R16G16B16A16_FLOAT需要第四位补1
        '''


    def average_normal_tangent(self):
        '''
        TODO
        重计算TANGENT
        
        # 含有这个属性的情况下才能计算这个属性。
        # if layout.contains("TANGENT"):
        #     if GenerateModConfig.recalculate_tangent():
        #         vb.vector_normalized_normal_to_tangent()
        #     elif obj.get("3DMigoto:RecalculateTANGENT",False):
        #         vb.vector_normalized_normal_to_tangent()
        '''
        pass

    def average_normal_color(self):
        '''
        TODO
        重计算COLOR

        # if layout.contains("COLOR"):
        #     if GenerateModConfig.recalculate_color():
        #         vb.arithmetic_average_normal_to_color()
        #     elif obj.get("3DMigoto:RecalculateCOLOR",False):
        #         vb.arithmetic_average_normal_to_color()
        '''
        pass

    def calc_index_buffer(self,mesh:bpy.types.Mesh):
        '''
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
        '''
           # 假设 elementname_data_dict 已经填充完毕，它包含了所有需要参与哈希计算的元素
        elements_to_hash = list(self.elementname_bytesdata_dict.keys())
        # 创建一个新的有序字典来存储唯一的顶点和它们对应的索引
        indexed_vertices = collections.OrderedDict()

        # 预先计算所有元素的 stride
        # 预先计算所有元素的 stride (即每个元素的字节长度)
        strides = {}
        for element_name in elements_to_hash:
            # 获取当前元素名称对应的 NumPy 数组
            data_array = self.elementname_bytesdata_dict[element_name]
            
            # 使用 .itemsize 属性获取数组中每个元素占用的字节数
            byte_width = len(data_array) 
            
            # 将元素名称和对应的字节宽度存入 strides 字典
            strides[element_name] = byte_width

        # 如果可能，预估索引缓冲区的大小
        estimated_size = sum(poly.loop_total for poly in mesh.polygons)
        index_buffer_array = numpy.empty(estimated_size, dtype=numpy.uint32)

        # 使用计数器跟踪当前索引位置
        current_index = 0

        # 缓存已计算的顶点哈希值
        vertex_cache = {}

        for poly in mesh.polygons:
            for blender_lvertex in mesh.loops[poly.loop_start:poly.loop_start + poly.loop_total]:
                vertex_index = blender_lvertex.vertex_index
                
                # 检查是否已经计算过该顶点的哈希值
                if vertex_index not in vertex_cache:
                    # 构建顶点数据字节串
                    vertex_data_bytes = b''.join(
                        self.elementname_bytesdata_dict[element_name][vertex_index * stride:(vertex_index + 1) * stride].tobytes()
                        for element_name, stride in strides.items()
                    )
                    
                    # 计算哈希值
                    hash_value = hashlib.md5(vertex_data_bytes).hexdigest().encode()
                    vertex_cache[vertex_index] = hash_value
                else:
                    hash_value = vertex_cache[vertex_index]

                # 使用哈希值作为键设置或获取索引
                index = indexed_vertices.setdefault(hash_value, len(indexed_vertices))
                
                # 直接写入预分配的NumPy数组
                index_buffer_array[current_index] = index
                current_index += 1

        # 调整数组大小以匹配实际使用的索引数量
        index_buffer_array.resize(current_index, refcheck=False)

        # 输出结果
        print("Unique Vertices:", len(indexed_vertices))
        print("Index Buffer Length:", len(index_buffer_array))
    

def get_buffer_ib_vb_fast(d3d11GameType:D3D11GameType):
    '''
    使用Numpy直接从mesh中转换数据到目标格式Buffer

    TODO 完成此功能并全流程测试通过后删除上面的get_export_ib_vb函数
    并移除IndexBuffer和VertexBuffer中的部分方法例如encode、pad等，进一步减少复杂度。
    '''
    TimerUtils.Start("GetExportIBVB Fast")
    # 获取Mesh
    obj = ObjUtils.get_bpy_context_object()

    buffer_model = BufferModel(d3d11GameType=d3d11GameType)
    buffer_model.check_and_verify_attributes(obj)
    
    # Nico: 通过evaluated_get获取到的是一个新的mesh，用于导出，不影响原始Mesh
    mesh = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()

    ObjUtils.mesh_triangulate(mesh)

    # Calculates tangents and makes loop normals valid (still with our custom normal data from import time):
    # 前提是有UVMap，前面的步骤应该保证了模型至少有一个TEXCOORD.xy
    mesh.calc_tangents()

    # 读取并解析数据到ndarray中，全部都是ravel()过的
    buffer_model.parse_elementname_ravel_ndarray_dict(mesh)
    buffer_model.convert_ndarray_to_bytes()
    buffer_model.show()
    buffer_model.calc_index_buffer(mesh)

    TimerUtils.End("GetExportIBVB Fast")




