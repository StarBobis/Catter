import numpy
import hashlib
import bpy
import collections
import struct

from ..utils.collection_utils import CollectionUtils
from ..utils.json_utils import JsonUtils
from ..utils.obj_utils import ObjUtils
from ..utils.timer_utils import TimerUtils
from ..utils.log_utils import LOG

from ..migoto.d3d11_game_type import D3D11GameType
from ..migoto.migoto_utils import MigotoUtils

class BufferModel:

    '''
    BufferModel用于抽象每一个obj的mesh对象中的数据，加快导出速度。
    '''
    
    def __init__(self,d3d11GameType:D3D11GameType) -> None:
        self.d3d11GameType:D3D11GameType = d3d11GameType
        self.elementname_data_dict = {}
        self.elementname_bytesdata_dict = {}
        self.vertexindex_data_dict = {}
        self.vertexindex_bytesdata_dict = {}
        self.test_output_path = "C:\\Users\\Administrator\\Desktop\\TestOutput\\"

    def write_to_file_test(self,file_name:str,data):
        file_path = self.test_output_path + file_name
        if isinstance(data,bytes):
            with open(file_path, 'wb') as file:
                file.write(data)
        else:
            with open(file_path, 'wb') as file:
                file.write(data.tobytes())


    def show(self,obj,to_files=False):
        '''
        展示所有数据，仅用于测试开发
        '''
        for element_name,value in self.elementname_data_dict.items():
            d3d11Element = self.d3d11GameType.ElementNameD3D11ElementDict[element_name]
            print("key: " + element_name + " value: " + str(type(value)) + " data:" + str(type(value[0])) + " len:" + str(len(value)) + " shape: " + str(value.shape) + "  ByteWidth:" + str(d3d11Element.ByteWidth))
            
            # 这里写出来得到的结果是正确的，只不过没有得到正确的转换
            if to_files:
                self.write_to_file_test(obj.name + "-" + element_name + ".buf" ,value)
        LOG.newline()

        # for element_name,value in self.elementname_bytesdata_dict.items():
        #     d3d11Element = self.d3d11GameType.ElementNameD3D11ElementDict[element_name]
        #     print("key: " + element_name + " value: " + str(type(value)) + " data:" + str(type(value[0])) + " len:" + str(len(value)) + " shape: " + str(value.shape) + "  ByteWidth:" + str(d3d11Element.ByteWidth))
        #     # if to_files:
        #         # TODO 这里写出来得到的结果是错误的，说明astype有问题
        #         # self.write_to_file_test(obj.name + "-" + element_name + ".buf" ,value)

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
    def convert_to_r8g8b8a8_snorm(self, input_array):
        """
        将输入的 (N, 4) 形状的 float32 ndarray 转换为 R8G8B8A8_SNORM 格式的 int8 ndarray。

        参数:
            input_array (numpy.ndarray): 输入的 (N, 4) 形状的 float32 ndarray，每个元素在 [-1, 1] 范围内。

        返回:
            numpy.ndarray: 转换后的 (N, 4) 形状的 int8 ndarray，符合 R8G8B8A8_SNORM 格式。
        """
        if not isinstance(input_array, numpy.ndarray) or input_array.dtype != numpy.float32 or input_array.shape[-1] != 4:
            raise ValueError("输入必须是形状为 (N, 4) 的 float32 类型的 NumPy 数组")

        # 确保数据在 [-1, 1] 范围内（如果已经是则可以跳过这一步）
        normalized = numpy.clip(input_array, -1.0, 1.0)

        # 将 [-1, 1] 范围内的浮点数缩放到 [-128, 127]
        scaled = (normalized * 127).round()

        # 转换为 int8 类型
        result_int8 = scaled.astype(numpy.int8)

        return result_int8
     
    def convert_to_r8g8b8a8_unorm(self,input_array):
        """
        将输入的 (N, 4) 形状的 float32 ndarray 转换为 R8G8B8A8_UNORM 格式的 uint8 ndarray。

        参数:
            input_array (numpy.ndarray): 输入的 (N, 4) 形状的 float32 ndarray，每个元素在 [0, 1] 范围内。

        返回:
            numpy.ndarray: 转换后的 (N, 4) 形状的 uint8 ndarray，符合 R8G8B8A8_UNORM 格式。
        """
        if not isinstance(input_array, numpy.ndarray) or input_array.dtype != numpy.float32 or input_array.shape[-1] != 4:
            raise ValueError("输入必须是形状为 (N, 4) 的 float32 类型的 NumPy 数组")

        # 确保数据在 [0, 1] 范围内（如果已经是则可以跳过这一步）
        normalized = numpy.clip(input_array, 0.0, 1.0)

        # 将 [0, 1] 范围内的浮点数缩放到 [0, 255]
        scaled = (normalized * 255).round()

        # 转换为 uint8 类型
        result_uint8 = scaled.astype(numpy.uint8)

        return result_uint8

    def split_array_into_chunks(array, n):
        """
        将 NumPy 数组平均分成若干份，每份包含 n 个元素，并存入新的字典中返回。
        
        参数:
            array (numpy.ndarray): 要分割的一维 NumPy 数组。
            n (int): 每份的元素数量。
            
        返回:
            dict: 键是每个分割出来的元素的顺序索引，值是分割的份的内容。
        """
        # 创建一个空字典用于存储分块结果
        chunks_dict = {}
        
        # 确保数组长度是n的倍数，如果不是，则忽略剩余不足n的部分
        num_chunks = len(array) // n
        
        # 使用for循环生成子数组并存入字典中
        for i in range(num_chunks):
            chunk = array[i * n : (i + 1) * n]
            chunks_dict[i] = chunk

        return chunks_dict
    
    def split_array_into_chunks_of_n_and_append(self,array, n):
        """
        将 NumPy 数组平均分成若干份，每份包含 n 个元素，并追加到传入的字典中。
        
        参数:
            array (numpy.ndarray): 要分割的一维 NumPy 数组。
            n (int): 每份的元素数量。
        """
        # 计算总共需要分成多少份
        num_chunks = len(array) // n
        # 使用列表推导式生成子数组并追加到 global_dict 中
        for i in range(num_chunks):
            chunk = array[i * n : (i + 1) * n]
            self.vertexindex_data_dict.setdefault(i, []).append(chunk)

    def parse_elementname_ravel_ndarray_dict(self,mesh:bpy.types.Mesh) -> dict:
        '''
        注意这里是从mesh.loops中获取数据，而不是从mesh.vertices中获取数据
        所以后续使用的时候要用mesh.loop里的索引来进行获取数据
        这里转换出来基本上都是float32类型，占4个字节，只有BLENDINDICES是uint32类型，也占4个字节
        顶点数计算公式： ndarray长度 / 元素个数 = 顶点数 （这里的顶点数是len(mesh.loops)的数量）
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

        elementname_data_dict = {}
        for d3d11_element_name in self.d3d11GameType.OrderedFullElementList:
            d3d11_element = self.d3d11GameType.ElementNameD3D11ElementDict[d3d11_element_name]

            if d3d11_element_name == 'POSITION':
                dtype = MigotoUtils.get_dtype_from_format(d3d11_element.Format)
                # 直接从Blender的API获取所有顶点的位置到一个NumPy数组中
                vertex_coords = numpy.empty(len(mesh.vertices) * 3, dtype=dtype)
                mesh.vertices.foreach_get('co', vertex_coords)

                # 创建一个包含所有循环顶点索引的NumPy数组
                loop_vertex_indices = numpy.empty(len(mesh.loops), dtype=int)
                mesh.loops.foreach_get("vertex_index", loop_vertex_indices)
                # 使用高级索引一次性提取所需的位置数据
                positions = vertex_coords.reshape(-1, 3)[loop_vertex_indices]

                print(str(MigotoUtils.format_size(d3d11_element.Format)))
                # TODO 在这里进行转换
                # if d3d11_element.Format == 'R16G16B16A16_FLOAT':
                #     positions = positions.astype(numpy.float16)
                #     new_array = numpy.zeros((positions.shape[0], 4))
                #     new_array[:, :3] = positions
                #     positions = new_array

                positions_ravel = positions.ravel()

                # 将位置数据存入字典
                elementname_data_dict[d3d11_element_name] = positions_ravel

                self.split_array_into_chunks_of_n_and_append(positions_ravel, 3)

            elif d3d11_element_name == 'NORMAL':
                dtype = MigotoUtils.get_dtype_from_format(d3d11_element.Format)
                
                # 直接从Blender的API获取所有循环的法线到一个NumPy数组中
                num_loops = len(mesh.loops)
                loop_normals = numpy.empty(num_loops * 3, dtype=dtype)
                mesh.loops.foreach_get('normal', loop_normals)

                # 将法线数据存入字典
                elementname_data_dict[d3d11_element_name] = loop_normals.ravel()

                self.split_array_into_chunks_of_n_and_append(loop_normals, 3)

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
                self.split_array_into_chunks_of_n_and_append(tangents_data, 4)

            elif d3d11_element_name.startswith('COLOR'):
                if d3d11_element_name in mesh.vertex_colors:
                    # 因为COLOR属性存储在Blender里固定是float32类型所以这里只能用numpy.float32
                    result = numpy.zeros(len(mesh.loops), dtype=(numpy.float32, 4))
                    mesh.vertex_colors[d3d11_element_name].data.foreach_get("color", result.ravel())
                    
                    if d3d11_element.Format == 'R8G8B8A8_UNORM':
                        result = self.convert_to_r8g8b8a8_unorm(result)

                    color_data = result.ravel()
                    
                    # encoder,decoder = MigotoUtils.EncoderDecoder(d3d11_element.Format)
                    # color_data = encoder(color_data)

                    elementname_data_dict[d3d11_element_name] = color_data
                    self.split_array_into_chunks_of_n_and_append(color_data, 4)

            elif d3d11_element_name.startswith('BLENDINDICES'):
                # 获取骨骼权重索引的数据类型
                dtype = MigotoUtils.get_dtype_from_format(d3d11_element.Format)
                
                # 提取所有顶点的骨骼权重索引，并填充到一个字典中
                vertex_groups = {v.index: sorted(v.groups, key=lambda x: x.weight, reverse=True)[:4] for v in mesh.vertices}

                # 创建一个包含所有循环顶点索引的NumPy数组
                loop_vertex_indices = numpy.empty(len(mesh.loops), dtype=int)
                mesh.loops.foreach_get("vertex_index", loop_vertex_indices)

                # 创建一个函数来获取前4个骨骼索引，不足的部分用0填充
                def get_top_4_indices(vertex_groups, vertex_index):
                    groups = vertex_groups.get(vertex_index, [])
                    indices = [g.group for g in groups] + [0] * (4 - len(groups))
                    return indices[:4]

                # 使用vectorize将Python函数转换为适用于NumPy数组的向量化函数
                vectorized_get_indices = numpy.vectorize(get_top_4_indices, otypes=[object])

                # 应用向量化函数，获取所有循环的骨骼索引
                blendindices_list = vectorized_get_indices(numpy.repeat([vertex_groups], len(mesh.loops), axis=0), loop_vertex_indices)

                # 将结果展平为一维数组
                blendindices = numpy.array(blendindices_list.tolist()).reshape(-1)

                elementname_data_dict[d3d11_element_name] = blendindices
                self.split_array_into_chunks_of_n_and_append(blendindices, 4)

            elif d3d11_element_name.startswith('BLENDWEIGHT'):
                # 获取混合权重的数据类型
                dtype = MigotoUtils.get_dtype_from_format(d3d11_element.Format)

                # 提取所有顶点的骨骼权重，并填充到一个NumPy数组中
                num_vertices = len(mesh.vertices)
                vertex_weights_array = numpy.zeros((num_vertices, 4), dtype=dtype)

                for v in mesh.vertices:
                    weights = sorted((x.weight for x in v.groups), reverse=True)[:4]
                    vertex_weights_array[v.index, :len(weights)] = weights

                # 创建一个包含所有循环顶点索引的NumPy数组
                loop_vertex_indices = numpy.empty(len(mesh.loops), dtype=int)
                mesh.loops.foreach_get("vertex_index", loop_vertex_indices)

                # 使用高级索引一次性提取所需权重数据
                blendweights = vertex_weights_array[loop_vertex_indices].reshape(-1)

                # 将混合权重数据存入字典
                elementname_data_dict[d3d11_element_name] = blendweights
                self.split_array_into_chunks_of_n_and_append(blendweights, 4)

            elif d3d11_element_name.startswith('TEXCOORD') and d3d11_element.Format.endswith('FLOAT'):
                for uv_name in ('%s.xy' % d3d11_element_name, '%s.zw' % d3d11_element_name):
                    if uv_name in texcoord_layers:
                        uvs_array = numpy.array(list(texcoord_layers[uv_name].values()),dtype=numpy.float32).flatten()
                        elementname_data_dict[d3d11_element_name] = uvs_array.ravel()
                        self.split_array_into_chunks_of_n_and_append(uvs_array, 2)
        
        self.elementname_data_dict = elementname_data_dict

        # TODO 后续需要优化
        # 12000顶点0.4秒  如果有12万顶点将消耗4秒
        # TimerUtils.Start("ConvertToBytes")
        for key, arrays in self.vertexindex_data_dict.items():
            self.vertexindex_bytesdata_dict[key] = numpy.concatenate([arr.flatten() for arr in arrays]).tobytes()
        # TimerUtils.End("ConvertToBytes")  


    def convert_ndarray_to_bytes(self):
        '''
        Deprecated

        数据全部编码为目标格式
        TODO 这个要在单独的顶点被统计出来之后再搞，不然没有意义。
        '''
        # TimerUtils.Start("ConvertNDarrayToTargetFormat")
        elementname_bytesdata_dict = {}

        for element_name,value in self.elementname_data_dict.items():
            d3d11_element = self.d3d11GameType.ElementNameD3D11ElementDict[element_name]
            # print("key: " + element_name + " value: " + str(type(value)) + " data:" + str(type(value[0])) + " len:" + str(len(value)) + " shape: " + str(value.shape))

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
        # TimerUtils.End("ConvertNDarrayToTargetFormat")  单纯使用astype速度极快，不到0.001s

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


    def calc_index_vertex_buffer(self,mesh:bpy.types.Mesh):
        '''
        This saves me a lot of time to make another wheel,it's already optimized very good.
        Credit to XXMITools for learn the design and copy the original code
        https://github.com/leotorrez/XXMITools
        Special Thanks for @leotorrez 
        '''
        # TimerUtils.Start("CalcIndexBuffer")
        indexed_vertices = collections.OrderedDict()
        ib = [[indexed_vertices.setdefault(self.vertexindex_bytesdata_dict[blender_lvertex.index], len(indexed_vertices))
                for blender_lvertex in mesh.loops[poly.loop_start:poly.loop_start + poly.loop_total]
                    ]for poly in mesh.polygons]
        print("IndexedVertices Number: " + str(len(indexed_vertices)))
        # print(len(ib)) # 这里ib的长度是三角形的个数，每个三角形有三个顶点索引，所以一共1014个数据，符合预期
        # TimerUtils.End("CalcIndexBuffer") # Very Fast in 0.1s

        # indexed_vertices 中key是字节串，value是顺序索引
        # TODO 所以到这一步之前，就应该已经补全数据并做好了数据转换了

        # TODO 组装后，补全数据，然后将数据转换为list[bytes]


       
        # Step 1: Flatten the list of lists into a single list.
        flattened_ib = [item for sublist in ib for item in sublist]

        # Step 2: Pack the integers directly using the flattened list.
        # '<' means little-endian, 'I' means unsigned int (32 bits).
        packed_data = struct.pack(f'<{len(flattened_ib)}I', *flattened_ib)

        # Write to a binary file.
        
        with open(self.test_output_path + mesh.name + "-IB.buf", 'wb') as f:
            f.write(packed_data)
    

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
    buffer_model.calc_index_vertex_buffer(mesh)

    buffer_model.convert_ndarray_to_bytes()
    buffer_model.show(obj,to_files=True)

    TimerUtils.End("GetExportIBVB Fast")




