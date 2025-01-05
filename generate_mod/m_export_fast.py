import numpy
import hashlib
import bpy
import collections
import struct
import math

from ..utils.collection_utils import CollectionUtils
from ..utils.json_utils import JsonUtils
from ..utils.obj_utils import ObjUtils
from ..utils.timer_utils import TimerUtils
from ..utils.log_utils import LOG

from ..migoto.d3d11_game_type import D3D11GameType
from ..migoto.migoto_utils import MigotoUtils

from ..config.generate_mod_config import GenerateModConfig


class BufferDataConverter:
    '''
    各种格式转换
    '''
    # 向量归一化
    def vector_normalize(self,v):
        """归一化向量"""
        length = math.sqrt(sum(x * x for x in v))
        if length == 0:
            return v  # 避免除以零
        return [x / length for x in v]
    
    def add_and_normalize_vectors(self,v1, v2):
        """将两个向量相加并规范化(normalize)"""
        # 相加
        result = [a + b for a, b in zip(v1, v2)]
        # 归一化
        normalized_result = self.vector_normalize(result)
        return normalized_result
    
    # 辅助函数：计算两个向量的点积
    def dot_product(self,v1, v2):
        return sum(a * b for a, b in zip(v1, v2))
    
    @classmethod
    def average_normal_tangent(cls,indexed_vertices,d3d11GameType:D3D11GameType):
        '''
        Nico: 米游所有游戏都能用到这个，还有曾经的GPU-PreSkinning的GF2也会用到这个，崩坏三2.0新角色除外。
        
        尽管这个可以起到相似的效果，但是仍然无法完美获取模型本身的TANGENT数据，只能做到身体轮廓线99%近似。
        经过测试，头发轮廓线部分并不是简单的向量归一化，也不是算术平均归一化。

        TODO 这里可能有格式兼容性问题

        TODO 在这里还需要考虑POSITION，NORMAL是长度为3还是4来进行分割的问题
        如果移动到上一步，在收集数据的时候，就直接去计算，就能避免考虑这个长度问题，直接按照elementname获取所有的元素
        而且TANGENT和COLOR如果确定要计算，甚至可以不获取，直接进行计算得出，又能节省部分性能开销。
        '''
        # TODO 有空再实现吧。

        # position_element = d3d11GameType.ElementNameD3D11ElementDict["POSITION"]
        # normal_element = d3d11GameType.ElementNameD3D11ElementDict["NORMAL"]
        # tangent_element = d3d11GameType.ElementNameD3D11ElementDict["TANGENT"]
        

        # for vertex_byte_list in indexed_vertices.keys():
        #     break
        
        return indexed_vertices

    @classmethod
    def average_normal_color(cls,indexed_vertices,d3d11GameType:D3D11GameType):
        '''
        Nico: 算数平均归一化法线，HI3 2.0角色使用的方法

        TODO 这里可能有格式兼容性问题
        '''
        
        return indexed_vertices

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

        self.dtype = None
        self.element_vertex_ndarray  = None
        

    
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
    
    # def split_array_into_chunks_of_n_and_append(self,ndarray, n):
    #     # TODO 必须去掉这个方法，占用时间太长了。架构设计的还是有问题
    #     TimerUtils.Start("Append Data")
    #     # 将所有元素直接追加到一个列表中
    #     for i, element in enumerate(ndarray):
    #         chunk_index = i // n
    #         self.vertexindex_data_dict.setdefault(chunk_index, []).append(element)
    #     TimerUtils.End("Append Data")
        
    def parse_elementname_ravel_ndarray_dict(self,mesh:bpy.types.Mesh) -> dict:
        '''
        注意这里是从mesh.loops中获取数据，而不是从mesh.vertices中获取数据
        所以后续使用的时候要用mesh.loop里的索引来进行获取数据
        '''
        TimerUtils.Start("Parse MeshData")



        mesh_loops = mesh.loops
        mesh_loops_length = len(mesh_loops)
        mesh_vertices = mesh.vertices
        mesh_vertices_length = len(mesh.vertices)

        # Learned from XXMI-Tools, Credit to @leotorrez
        self.dtype = numpy.dtype([])
        for d3d11_element_name in self.d3d11GameType.OrderedFullElementList:
            d3d11_element = self.d3d11GameType.ElementNameD3D11ElementDict[d3d11_element_name]
            np_type = MigotoUtils.get_nptype_from_format(d3d11_element.Format)
            format_len = MigotoUtils.format_components(d3d11_element.Format)
            self.dtype = numpy.dtype(self.dtype.descr + [(d3d11_element_name, (np_type, format_len))])
        self.element_vertex_ndarray = numpy.zeros(mesh_loops_length,dtype=self.dtype)

        # 创建一个包含所有循环顶点索引的NumPy数组
        loop_vertex_indices = numpy.empty(mesh_loops_length, dtype=int)
        mesh_loops.foreach_get("vertex_index", loop_vertex_indices)

        # TimerUtils.Start("GET BLEND") # 0:00:00.141898 
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
        # blendindices_flat = blendindices.reshape(-1)
        # blendweights_flat = blendweights.reshape(-1)

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
        
        # 对每一种Element都获取对应的数据
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

                self.element_vertex_ndarray[d3d11_element_name] = positions
                # TimerUtils.End("Position Get") # 0:00:00.057535 

            elif d3d11_element_name == 'NORMAL':
                # TimerUtils.Start("Get NORMAL")
                loop_normals = numpy.empty(mesh_loops_length * 3, dtype=numpy.float32)
                mesh_loops.foreach_get('normal', loop_normals)

                # 将一维数组 reshape 成 (mesh_loops_length, 3) 形状的二维数组
                loop_normals = loop_normals.reshape(-1, 3)

                # TODO 测试astype能用吗？
                if d3d11_element.Format == 'R16G16B16A16_FLOAT':
                     # 转换数据类型并添加第四列，默认填充为1
                    loop_normals = loop_normals.astype(numpy.float16)
                    new_array = numpy.ones((loop_normals.shape[0], 4), dtype=numpy.float16)
                    new_array[:, :3] = loop_normals
                    loop_normals = new_array

                self.element_vertex_ndarray[d3d11_element_name] = loop_normals

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

                
                # 重塑 output_tangents 成 (mesh_loops_length, 4) 形状的二维数组
                output_tangents = output_tangents.reshape(-1, 4)

                if d3d11_element.Format == 'R16G16B16A16_FLOAT':
                    output_tangents = output_tangents.astype(numpy.float16)
                    

                self.element_vertex_ndarray[d3d11_element_name] = output_tangents

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
                        result = BufferDataConverter.convert_4x_float32_to_r8g8b8a8_unorm(result)

                    self.element_vertex_ndarray[d3d11_element_name] = result

                # TimerUtils.End("Get COLOR") # 0:00:00.030605 
            elif d3d11_element_name.startswith('TEXCOORD') and d3d11_element.Format.endswith('FLOAT'):
                # TimerUtils.Start("GET TEXCOORD")
                for uv_name in ('%s.xy' % d3d11_element_name, '%s.zw' % d3d11_element_name):
                    if uv_name in texcoord_layers:
                        uvs_array = numpy.array(list(texcoord_layers[uv_name].values()),dtype=numpy.float32).flatten()

                        if d3d11_element.Format == 'R16G16_FLOAT':
                            uvs_array = uvs_array.astype(numpy.float16)
                        
                        # 重塑 uvs_array 成 (mesh_loops_length, 2) 形状的二维数组
                        uvs_array = uvs_array.reshape(-1, 2)

                        self.element_vertex_ndarray[d3d11_element_name] = uvs_array 
                        
            elif d3d11_element_name.startswith('BLENDINDICES'):
                # TODO 处理R32_UINT类型 R32G32_FLOAT类型
                self.element_vertex_ndarray[d3d11_element_name] = blendindices
 
            elif d3d11_element_name.startswith('BLENDWEIGHT'):
                # patch时跳过生成数据
                # TODO 处理R32G32_FLOAT类型
                if not self.d3d11GameType.PatchBLENDWEIGHTS:
                    self.element_vertex_ndarray[d3d11_element_name] = blendweights



                # TimerUtils.End("GET TEXCOORD") # 0:00:00.034990
        

        # (2) TODO 重计算TANGENT和重计算COLOR
        # if "TANGENT" in self.d3d11GameType.OrderedFullElementList:
        #     if GenerateModConfig.recalculate_tangent():
        #         indexed_vertices = BufferDataConverter.average_normal_tangent(indexed_vertices,self.d3d11GameType)
        #     elif obj.get("3DMigoto:RecalculateTANGENT",False):
        #         indexed_vertices = BufferDataConverter.average_normal_tangent(indexed_vertices,self.d3d11GameType)

        # if "COLOR" in self.d3d11GameType.OrderedFullElementList:
        #     if GenerateModConfig.recalculate_color():
        #         indexed_vertices = BufferDataConverter.average_normal_color(indexed_vertices,self.d3d11GameType)
        #     elif obj.get("3DMigoto:RecalculateCOLOR",False):
        #         indexed_vertices = BufferDataConverter.average_normal_color(indexed_vertices,self.d3d11GameType)
        TimerUtils.End("Parse MeshData") # 15s

    def calc_index_vertex_buffer(self,mesh:bpy.types.Mesh):
        '''
        计算IndexBuffer和CategoryBufferDict并返回

        This saves me a lot of time to make another wheel,it's already optimized very good.
        Credit to XXMITools for learn the design and copy the original code and modified for our needs.
        https://github.com/leotorrez/XXMITools
        Special Thanks for @leotorrez 
        '''
        # TimerUtils.Start("CalcIndexBuffer")
        # (1) 统计模型的索引和唯一顶点
        mesh_loops = mesh.loops
        indexed_vertices = collections.OrderedDict()
        ib = [[indexed_vertices.setdefault(self.element_vertex_ndarray[blender_lvertex.index].tobytes(), len(indexed_vertices))
                for blender_lvertex in mesh_loops[poly.loop_start:poly.loop_start + poly.loop_total]
                    ]for poly in mesh.polygons]
        # TimerUtils.End("CalcIndexBuffer") # 3.5s
        
        flattened_ib = [item for sublist in ib for item in sublist]
        # print("IndexedVertices Number: " + str(len(indexed_vertices)))
        # TimerUtils.End("Flat IB")

        TimerUtils.Start("ToBytes")
        # (3)这里没办法，只能对CategoryBuf进行逐个顶点追加，是无法避免的开销。
        category_buffer_dict:dict[str,list] = {}
        for categoryname,category_stride in self.d3d11GameType.CategoryStrideDict.items():
            category_buffer_dict[categoryname] = []

        category_stride_dict = self.d3d11GameType.get_real_category_stride_dict()

        for flat_byte_list in indexed_vertices:
            stride_offset = 0
            for categoryname,category_stride in category_stride_dict.items():
                category_buffer_dict[categoryname].extend(flat_byte_list[stride_offset:stride_offset + category_stride])
                stride_offset += category_stride
        
        TimerUtils.End("ToBytes") # 0:00:00.292768  5s
        return flattened_ib,category_buffer_dict

def get_buffer_ib_vb_fast(d3d11GameType:D3D11GameType):
    '''
    使用Numpy直接从mesh中转换数据到目标格式Buffer

    TODO 完成此功能并全流程测试通过后删除上面的get_export_ib_vb函数
    并移除IndexBuffer和VertexBuffer中的部分方法例如encode、pad等，进一步减少复杂度。
    '''
    buffer_model = BufferModel(d3d11GameType=d3d11GameType)

    obj = ObjUtils.get_bpy_context_object()
    buffer_model.check_and_verify_attributes(obj)
    
    # Nico: 通过evaluated_get获取到的是一个新的mesh，用于导出，不影响原始Mesh
    mesh = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()

    ObjUtils.mesh_triangulate(mesh)

    # Calculates tangents and makes loop normals valid (still with our custom normal data from import time):
    # 前提是有UVMap，前面的步骤应该保证了模型至少有一个TEXCOORD.xy
    mesh.calc_tangents()

    # 读取并解析数据
    buffer_model.parse_elementname_ravel_ndarray_dict(mesh)

    return buffer_model.calc_index_vertex_buffer(mesh)




