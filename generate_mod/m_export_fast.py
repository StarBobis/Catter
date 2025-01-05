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


class NumpyTypeConverter:

    @classmethod
    def convert_4x_float32_to_r8g8b8a8_snorm(cls, input_array):
        # 确保数据在 [-1, 1] 范围内（如果已经是则可以跳过这一步）
        normalized = numpy.clip(input_array, -1.0, 1.0)

        # 将 [-1, 1] 范围内的浮点数缩放到 [-128, 127]
        scaled = (normalized * 127).round()

        return scaled.astype(numpy.int8)
     
    @classmethod
    def convert_4x_float32_to_r8g8b8a8_unorm(cls,input_array):
        # 确保数据在 [0, 1] 范围内（如果已经是则可以跳过这一步）
        normalized = numpy.clip(input_array, 0.0, 1.0)

        # 将 [0, 1] 范围内的浮点数缩放到 [0, 255]
        scaled = (normalized * 255).round()

        return scaled.astype(numpy.uint8)


class BufferModel:
    '''
    BufferModel用于抽象每一个obj的mesh对象中的数据，加快导出速度。
    '''
    
    def __init__(self,d3d11GameType:D3D11GameType) -> None:
        self.d3d11GameType:D3D11GameType = d3d11GameType
        self.vertexindex_data_dict = {}
    
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
    
    def split_array_into_chunks_of_n_and_append(self,ndarray, n):
        # 将所有元素直接追加到一个列表中
        for i, element in enumerate(ndarray):
            chunk_index = i // n
            self.vertexindex_data_dict.setdefault(chunk_index, []).append(element)
        

    def parse_elementname_ravel_ndarray_dict(self,mesh:bpy.types.Mesh) -> dict:
        '''
        注意这里是从mesh.loops中获取数据，而不是从mesh.vertices中获取数据
        所以后续使用的时候要用mesh.loop里的索引来进行获取数据
        这里转换出来基本上都是float32类型，占4个字节，只有BLENDINDICES是uint32类型，也占4个字节
        顶点数计算公式： ndarray长度 / 元素个数 = 顶点数 （这里的顶点数是len(mesh.loops)的数量）
        '''
        mesh_loops = mesh.loops
        mesh_loops_length = len(mesh_loops)
        mesh_vertices = mesh.vertices
        mesh_vertices_length = len(mesh.vertices)

        # 创建一个包含所有循环顶点索引的NumPy数组
        loop_vertex_indices = numpy.empty(mesh_loops_length, dtype=int)
        mesh_loops.foreach_get("vertex_index", loop_vertex_indices)

        # TimerUtils.Start("GET BLEND") 0:00:00.141898 
        # 准备一个空数组用于存储结果，形状为(mesh_loops_length, 4)
        blendindices = numpy.zeros((mesh_loops_length, 4), dtype=int)
        blendweights = numpy.zeros((mesh_loops_length, 4), dtype=numpy.float32)

        # 提取所有顶点的骨骼权重索引和权重，并限制每个顶点最多4个非零权重
        vertex_info = {}
        for v in mesh_vertices:
            sorted_groups = sorted(v.groups, key=lambda x: x.weight, reverse=True)[:4]
            vertex_info[v.index] = {
                'groups': [g.group for g in sorted_groups],
                'weights': [g.weight for g in sorted_groups]
            }

        # 填充blendindices和blendweights数组
        for i, vertex_index in enumerate(loop_vertex_indices):
            info = vertex_info.get(vertex_index, {'groups': [], 'weights': []})
            groups = info['groups']
            weights = info['weights']
            blendindices[i, :len(groups)] = groups[:4]
            blendweights[i, :len(weights)] = weights[:4]

        # 展平为一维数组
        blendindices_flat = blendindices.reshape(-1)
        blendweights_flat = blendweights.reshape(-1)

        # TimerUtils.End("GET BLEND")

        # Nico: 提前拼凑texcoord层级，有几个UVMap就拼出几个来，略微提升速度(虽然只提升几十毫秒。。)
        texcoord_layers = {}
        for uv_layer in mesh.uv_layers:
            texcoords = {}
            flip_uv = lambda uv: (uv[0], 1.0 - uv[1])
            for l in mesh_loops:
                uv = flip_uv(uv_layer.data[l.index].uv)
                texcoords[l.index] = uv
            texcoord_layers[uv_layer.name] = texcoords
        

        for d3d11_element_name in self.d3d11GameType.OrderedFullElementList:
            d3d11_element = self.d3d11GameType.ElementNameD3D11ElementDict[d3d11_element_name]

            if d3d11_element_name == 'POSITION':
                # TimerUtils.Start("Position Get")
                vertex_coords = numpy.empty(mesh_vertices_length * 3, dtype=numpy.float32)
                mesh_vertices.foreach_get('co', vertex_coords)

                positions = vertex_coords.reshape(-1, 3)[loop_vertex_indices]

                # TODO 测试astype能用吗？
                if d3d11_element.Format == 'R16G16B16A16_FLOAT':
                    positions = positions.astype(numpy.float16)
                    new_array = numpy.zeros((positions.shape[0], 4))
                    new_array[:, :3] = positions
                    positions = new_array

                positions_bytes = positions.ravel()

                # 将位置数据存入字典
                self.split_array_into_chunks_of_n_and_append(positions_bytes, 3)

                # TimerUtils.End("Position Get") # 0:00:00.057535 

            elif d3d11_element_name == 'NORMAL':
                # TimerUtils.Start("Get NORMAL")

                loop_normals = numpy.empty(mesh_loops_length * 3, dtype=numpy.float32)
                mesh_loops.foreach_get('normal', loop_normals)


                # TODO 测试astype能用吗？
                if d3d11_element.Format == 'R16G16B16A16_FLOAT':
                    loop_normals = loop_normals.astype(numpy.float16)
                    new_array = numpy.zeros((loop_normals.shape[0], 4))
                    new_array[:, :3] = loop_normals
                    loop_normals = new_array

                loop_normals_bytes = loop_normals.ravel()
                self.split_array_into_chunks_of_n_and_append(loop_normals_bytes, 3)

                # TimerUtils.End("Get NORMAL") # 0:00:00.029400 

            elif d3d11_element_name == 'TANGENT':
                # TimerUtils.Start("Get TANGENT")
                output_tangents = numpy.empty(mesh_loops_length * 4, dtype=numpy.float32)

                # 使用 foreach_get 批量获取切线和副切线符号数据
                tangents = numpy.empty(mesh_loops_length * 3, dtype=numpy.float32)
                bitangent_signs = numpy.empty(mesh_loops_length, dtype=numpy.float32)

                mesh_loops.foreach_get("tangent", tangents)
                mesh_loops.foreach_get("bitangent_sign", bitangent_signs)

                # 将副切线符号乘以 -1（因为在导入时翻转了UV，所以导出时必须翻转bitangent_signs）
                bitangent_signs *= -1

                # 将切线分量放置到输出数组中
                output_tangents[0::4] = tangents[0::3]  # x 分量
                output_tangents[1::4] = tangents[1::3]  # y 分量
                output_tangents[2::4] = tangents[2::3]  # z 分量
                output_tangents[3::4] = bitangent_signs  # w 分量 (副切线符号)
                tangents_data = output_tangents.ravel()

                if d3d11_element.Format == 'R16G16B16A16_FLOAT':
                    tangents_data = tangents_data.astype(numpy.float16)
                    

                self.split_array_into_chunks_of_n_and_append(tangents_data, 4)

                # TimerUtils.End("Get TANGENT") # 0:00:00.030449
            elif d3d11_element_name.startswith('COLOR'):
                # TimerUtils.Start("Get COLOR")

                if d3d11_element_name in mesh.vertex_colors:
                    # 因为COLOR属性存储在Blender里固定是float32类型所以这里只能用numpy.float32
                    result = numpy.zeros(mesh_loops_length, dtype=(numpy.float32, 4))
                    mesh.vertex_colors[d3d11_element_name].data.foreach_get("color", result.ravel())
                    
                    if d3d11_element.Format == 'R16G16B16A16_FLOAT':
                        result = result.astype(numpy.float16)
                    elif d3d11_element.Format == 'R8G8B8A8_UNORM':
                        result = NumpyTypeConverter.convert_4x_float32_to_r8g8b8a8_unorm(result)

                    color_data = result.ravel()

                    self.split_array_into_chunks_of_n_and_append(color_data, 4)

                # TimerUtils.End("Get COLOR") # 0:00:00.030605 

            elif d3d11_element_name.startswith('BLENDINDICES'):
                # TODO 处理R32_UINT类型 R32G32_FLOAT类型
                self.split_array_into_chunks_of_n_and_append(blendindices_flat, 4)
 
            elif d3d11_element_name.startswith('BLENDWEIGHT'):
                # patch时跳过生成数据
                # TODO 处理R32G32_FLOAT类型
                if not self.d3d11GameType.PatchBLENDWEIGHTS:
                    self.split_array_into_chunks_of_n_and_append(blendweights_flat, 4)

            elif d3d11_element_name.startswith('TEXCOORD') and d3d11_element.Format.endswith('FLOAT'):
                # TimerUtils.Start("GET TEXCOORD")
                for uv_name in ('%s.xy' % d3d11_element_name, '%s.zw' % d3d11_element_name):
                    if uv_name in texcoord_layers:
                        uvs_array = numpy.array(list(texcoord_layers[uv_name].values()),dtype=numpy.float32).flatten()

                        if d3d11_element.Format == 'R16G16_FLOAT':
                            uvs_array = uvs_array.astype(numpy.float16)

                        self.split_array_into_chunks_of_n_and_append(uvs_array, 2)
                # TimerUtils.End("GET TEXCOORD") # 0:00:00.034990
        

        # TimerUtils.Start("ConvertToBytes")
        for key, arrays in self.vertexindex_data_dict.items():
            self.vertexindex_data_dict[key] = tuple(arrays)
        # TimerUtils.End("ConvertToBytes") # 0:00:00.014523


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
        mesh_loops = mesh.loops
        indexed_vertices = collections.OrderedDict()
        ib = [[indexed_vertices.setdefault(self.vertexindex_data_dict[blender_lvertex.index], len(indexed_vertices))
                for blender_lvertex in mesh_loops[poly.loop_start:poly.loop_start + poly.loop_total]
                    ]for poly in mesh.polygons]
        print("IndexedVertices Number: " + str(len(indexed_vertices)))
        # print(len(ib)) # 这里ib的长度是三角形的个数，每个三角形有三个顶点索引，所以一共1014个数据，符合预期
        # TimerUtils.End("CalcIndexBuffer") # Very Fast in 0.1s

        # TimerUtils.Start("ToBytes")
        # 这里没办法，只能对CategoryBuf进行逐个顶点追加，是无法避免的开销。
        category_buffer_dict:dict[str,list] = {}
        for categoryname,category_stride in self.d3d11GameType.CategoryStrideDict.items():
            category_buffer_dict[categoryname] = []

        for indexed_vertex_data in indexed_vertices.keys():
            flat_byte_list = [
                byte_val for val in indexed_vertex_data
                for byte_val in val.tobytes()
            ]

            stride_offset = 0
            for categoryname,category_stride in self.d3d11GameType.CategoryStrideDict.items():
                split_category_stride = category_stride
                if categoryname == "Blend" and self.d3d11GameType.PatchBLENDWEIGHTS:
                    split_category_stride = self.d3d11GameType.ElementNameD3D11ElementDict["BLENDINDICES"].ByteWidth

                category_buffer_dict[categoryname].extend(flat_byte_list[stride_offset:stride_offset + split_category_stride])
                stride_offset += split_category_stride

        flattened_ib = [item for sublist in ib for item in sublist]
        # TimerUtils.End("ToBytes") # 0:00:00.292768 
        return flattened_ib,category_buffer_dict

    

def get_buffer_ib_vb_fast(d3d11GameType:D3D11GameType):
    '''
    使用Numpy直接从mesh中转换数据到目标格式Buffer

    TODO 完成此功能并全流程测试通过后删除上面的get_export_ib_vb函数
    并移除IndexBuffer和VertexBuffer中的部分方法例如encode、pad等，进一步减少复杂度。
    '''
    # TimerUtils.Start("GetExportIBVB Fast")
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
    # buffer_model.show(obj,to_files=True)

    # TimerUtils.End("GetExportIBVB Fast")
    return buffer_model.calc_index_vertex_buffer(mesh)




