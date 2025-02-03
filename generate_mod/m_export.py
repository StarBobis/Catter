import numpy
import bpy
import collections
import math

from ..utils.obj_utils import ObjUtils
from ..utils.timer_utils import TimerUtils
from ..utils.migoto_utils import Fatal, MigotoUtils

from .d3d11_game_type import D3D11GameType

from ..config.generate_mod_config import GenerateModConfig 
from ..config.main_config import MainConfig,GameCategory

class BufferDataConverter:
    '''
    各种格式转换
    '''
    # 向量归一化
    @classmethod
    def vector_normalize(cls,v):
        """归一化向量"""
        length = math.sqrt(sum(x * x for x in v))
        if length == 0:
            return v  # 避免除以零
        return [x / length for x in v]
    
    @classmethod
    def add_and_normalize_vectors(cls,v1, v2):
        """将两个向量相加并规范化(normalize)"""
        # 相加
        result = [a + b for a, b in zip(v1, v2)]
        # 归一化
        normalized_result = cls.vector_normalize(result)
        return normalized_result
    
    # 辅助函数：计算两个向量的点积
    @classmethod
    def dot_product(cls,v1, v2):
        return sum(a * b for a, b in zip(v1, v2))

    '''
    这四个UNORM和SNORM比较特殊需要这样处理，其它float类型转换直接astype就行
    '''
    @classmethod
    def convert_4x_float32_to_r8g8b8a8_snorm(cls, input_array):
        return numpy.round(input_array * 127).astype(numpy.int8)
    
    @classmethod
    def convert_4x_float32_to_r8g8b8a8_unorm(cls,input_array):
        return numpy.round(input_array * 255).astype(numpy.uint8)
    
    @classmethod
    def convert_4x_float32_to_r16g16b16a16_unorm(cls, input_array):
        return numpy.round(input_array * 65535).astype(numpy.uint16)
    
    @classmethod
    def convert_4x_float32_to_r16g16b16a16_snorm(cls, input_array):
        return numpy.round(input_array * 32767).astype(numpy.uint16)
    
    @classmethod
    def average_normal_tangent(cls,obj,indexed_vertices,d3d11GameType,dtype):
        '''
        Nico: 米游所有游戏都能用到这个，还有曾经的GPU-PreSkinning的GF2也会用到这个，崩坏三2.0新角色除外。
        尽管这个可以起到相似的效果，但是仍然无法完美获取模型本身的TANGENT数据，只能做到身体轮廓线99%近似。
        经过测试，头发轮廓线部分并不是简单的向量归一化，也不是算术平均归一化。
        '''
        # TimerUtils.Start("Recalculate TANGENT")

        if "TANGENT" not in d3d11GameType.OrderedFullElementList:
            return indexed_vertices
        allow_calc = False
        if GenerateModConfig.recalculate_tangent():
            allow_calc = True
        elif obj.get("3DMigoto:RecalculateTANGENT",False): 
            allow_calc = True
        
        if not allow_calc:
            return indexed_vertices
        
        # 不用担心这个转换的效率，速度非常快
        vb = bytearray()
        for vertex in indexed_vertices:
            vb += bytes(vertex)
        vb = numpy.frombuffer(vb, dtype = dtype)

        # 开始重计算TANGENT
        positions = numpy.array([val['POSITION'] for val in vb])
        normals = numpy.array([val['NORMAL'] for val in vb], dtype=float)

        # 对位置进行排序，以便相同的位置会相邻
        sort_indices = numpy.lexsort(positions.T)
        sorted_positions = positions[sort_indices]
        sorted_normals = normals[sort_indices]

        # 找出位置变化的地方，即我们需要分组的地方
        group_indices = numpy.flatnonzero(numpy.any(sorted_positions[:-1] != sorted_positions[1:], axis=1))
        group_indices = numpy.r_[0, group_indices + 1, len(sorted_positions)]

        # 累加法线和计算计数
        unique_positions = sorted_positions[group_indices[:-1]]
        accumulated_normals = numpy.add.reduceat(sorted_normals, group_indices[:-1], axis=0)
        counts = numpy.diff(group_indices)

        # 归一化累积法线向量
        normalized_normals = accumulated_normals / numpy.linalg.norm(accumulated_normals, axis=1)[:, numpy.newaxis]
        normalized_normals[numpy.isnan(normalized_normals)] = 0  # 处理任何可能出现的零向量导致的除零错误

        # 构建结果字典
        position_normal_dict = dict(zip(map(tuple, unique_positions), normalized_normals))

        # TimerUtils.End("Recalculate TANGENT")

        # 获取所有位置并转换为元组，用于查找字典
        positions = [tuple(pos) for pos in vb['POSITION']]

        # 从字典中获取对应的标准化法线
        normalized_normals = numpy.array([position_normal_dict[pos] for pos in positions])

        # 计算 w 并调整 tangent 的第四个分量
        w = numpy.where(vb['TANGENT'][:, 3] >= 0, -1.0, 1.0)

        # 更新 TANGENT 分量，注意这里的切片操作假设 TANGENT 有四个分量
        vb['TANGENT'][:, :3] = normalized_normals
        vb['TANGENT'][:, 3] = w

        # TimerUtils.End("Recalculate TANGENT")

        return vb

    @classmethod
    def average_normal_color(cls,obj,indexed_vertices,d3d11GameType,dtype):
        '''
        Nico: 算数平均归一化法线，HI3 2.0角色使用的方法
        '''
        if "COLOR" not in d3d11GameType.OrderedFullElementList:
            return indexed_vertices
        allow_calc = False
        if GenerateModConfig.recalculate_color():
            allow_calc = True
        elif obj.get("3DMigoto:RecalculateCOLOR",False): 
            allow_calc = True
        if not allow_calc:
            return indexed_vertices

        # 开始重计算COLOR
        TimerUtils.Start("Recalculate COLOR")

        # 不用担心这个转换的效率，速度非常快
        vb = bytearray()
        for vertex in indexed_vertices:
            vb += bytes(vertex)
        vb = numpy.frombuffer(vb, dtype = dtype)

        # 首先提取所有唯一的位置，并创建一个索引映射
        unique_positions, position_indices = numpy.unique(
            [tuple(val['POSITION']) for val in vb], 
            return_inverse=True, 
            axis=0
        )

        # 初始化累积法线和计数器为零
        accumulated_normals = numpy.zeros((len(unique_positions), 3), dtype=float)
        counts = numpy.zeros(len(unique_positions), dtype=int)

        # 累加法线并增加计数（这里假设vb是一个list）
        for i, val in enumerate(vb):
            accumulated_normals[position_indices[i]] += numpy.array(val['NORMAL'], dtype=float)
            counts[position_indices[i]] += 1

        # 对所有位置的法线进行一次性规范化处理
        mask = counts > 0
        average_normals = numpy.zeros_like(accumulated_normals)
        average_normals[mask] = (accumulated_normals[mask] / counts[mask][:, None])

        # 归一化到[0,1]，然后映射到颜色值
        normalized_normals = ((average_normals + 1) / 2 * 255).astype(numpy.uint8)

        # 更新颜色信息
        new_color = []
        for i, val in enumerate(vb):
            color = [0, 0, 0, val['COLOR'][3]]  # 保留原来的Alpha通道
            
            if mask[position_indices[i]]:
                color[:3] = normalized_normals[position_indices[i]]

            new_color.append(color)

        # 将新的颜色列表转换为NumPy数组
        new_color_array = numpy.array(new_color, dtype=numpy.uint8)

        # 更新vb中的颜色信息
        for i, val in enumerate(vb):
            val['COLOR'] = new_color_array[i]

        TimerUtils.End("Recalculate COLOR")
        return vb


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
            
            # Check if BLENDINDICES exists
            if d3d11_element_name.startswith("BLENDINDICES"):
                if not obj.vertex_groups:
                    raise Fatal("your object [" +obj.name + "] need at leat one valid Vertex Group, Please check if your model's Vertex Group is correct.")

    def parse_elementname_ravel_ndarray_dict(self,mesh:bpy.types.Mesh) -> dict:
        '''
        - 注意这里是从mesh.loops中获取数据，而不是从mesh.vertices中获取数据
        - 所以后续使用的时候要用mesh.loop里的索引来进行获取数据
        '''
        # TimerUtils.Start("Parse MeshData")

        mesh_loops = mesh.loops
        mesh_loops_length = len(mesh_loops)
        mesh_vertices = mesh.vertices
        mesh_vertices_length = len(mesh.vertices)

        self.dtype = numpy.dtype([])

        blendweights_formatlen = 0
        for d3d11_element_name in self.d3d11GameType.OrderedFullElementList:
            d3d11_element = self.d3d11GameType.ElementNameD3D11ElementDict[d3d11_element_name]
            np_type = MigotoUtils.get_nptype_from_format(d3d11_element.Format)
            format_len = MigotoUtils.format_components(d3d11_element.Format)

            if d3d11_element_name in ["BLENDWEIGHTS","BLENDWEIGHT"]:
                blendweights_formatlen = format_len

            # patchBLENDWEIGHTS时必须跳过处理，否则会导致步长不正确
            if self.d3d11GameType.PatchBLENDWEIGHTS and d3d11_element_name in ["BLENDWEIGHTS","BLENDWEIGHT"]:
                continue

            # XXX 长度为1时必须手动指定为(1,)否则会变成1维数组
            if format_len == 1:
                self.dtype = numpy.dtype(self.dtype.descr + [(d3d11_element_name, (np_type, (1,)))])
            else:
                self.dtype = numpy.dtype(self.dtype.descr + [(d3d11_element_name, (np_type, format_len))])

        self.element_vertex_ndarray = numpy.zeros(mesh_loops_length,dtype=self.dtype)

        # 创建一个包含所有循环顶点索引的NumPy数组
        loop_vertex_indices = numpy.empty(mesh_loops_length, dtype=int)
        mesh_loops.foreach_get("vertex_index", loop_vertex_indices)

        # TimerUtils.Start("GET BLEND") # 0:00:00.141898 
        max_groups = 4

        # Extract and sort the top 4 groups by weight for each vertex.
        sorted_groups = [
            sorted(v.groups, key=lambda x: x.weight, reverse=True)[:max_groups]
            for v in mesh_vertices
        ]

        # Initialize arrays to hold all groups and weights with zeros.
        all_groups = numpy.zeros((len(mesh_vertices), max_groups), dtype=int)
        all_weights = numpy.zeros((len(mesh_vertices), max_groups), dtype=numpy.float32)


        # Fill the pre-allocated arrays with group indices and weights.
        for v_index, groups in enumerate(sorted_groups):
            num_groups = min(len(groups), max_groups)
            all_groups[v_index, :num_groups] = [g.group for g in groups][:num_groups]
            all_weights[v_index, :num_groups] = [g.weight for g in groups][:num_groups]

        # Initialize the blendindices and blendweights with zeros.
        blendindices = numpy.zeros((mesh_loops_length, max_groups), dtype=numpy.uint32)
        blendweights = numpy.zeros((mesh_loops_length, max_groups), dtype=numpy.float32)

        # Map from loop_vertex_indices to precomputed data using advanced indexing.
        valid_mask = (0 <= numpy.array(loop_vertex_indices)) & (numpy.array(loop_vertex_indices) < len(mesh_vertices))
        valid_indices = loop_vertex_indices[valid_mask]

        blendindices[valid_mask] = all_groups[valid_indices]
        blendweights[valid_mask] = all_weights[valid_indices]

        # XXX 必须对当前obj对象执行权重规格化，否则模型细分后会导致模型坑坑洼洼
        if "Blend" in self.d3d11GameType.OrderedCategoryNameList:
            if blendweights_formatlen > 1:
                blendweights = blendweights / numpy.sum(blendweights, axis=1)[:, None]

        # TimerUtils.End("GET BLEND")

        # 对每一种Element都获取对应的数据
        for d3d11_element_name in self.d3d11GameType.OrderedFullElementList:
            d3d11_element = self.d3d11GameType.ElementNameD3D11ElementDict[d3d11_element_name]

            if d3d11_element_name == 'POSITION':
                # TimerUtils.Start("Position Get")
                vertex_coords = numpy.empty(mesh_vertices_length * 3, dtype=numpy.float32)
                # Notice: 'undeformed_co' is static, don't need dynamic calculate like 'co' so it is faster.
                mesh_vertices.foreach_get('undeformed_co', vertex_coords)

                positions = vertex_coords.reshape(-1, 3)[loop_vertex_indices]
                if d3d11_element.Format == 'R16G16B16A16_FLOAT':
                    positions = positions.astype(numpy.float16)
                    new_array = numpy.zeros((positions.shape[0], 4))
                    new_array[:, :3] = positions
                    positions = new_array

                self.element_vertex_ndarray[d3d11_element_name] = positions
                # TimerUtils.End("Position Get") # 0:00:00.057535 

            elif d3d11_element_name == 'NORMAL':
                if d3d11_element.Format == 'R16G16B16A16_FLOAT':
                    result = numpy.ones(mesh_loops_length * 4, dtype=numpy.float32)
                    normals = numpy.empty(mesh_loops_length * 3, dtype=numpy.float32)
                    mesh_loops.foreach_get('normal', normals)
                    result[0::4] = normals[0::3]
                    result[1::4] = normals[1::3]
                    result[2::4] = normals[2::3]
                    result = result.reshape(-1, 4)

                    result = result.astype(numpy.float16)
                    self.element_vertex_ndarray[d3d11_element_name] = result

                elif d3d11_element.Format == 'R8G8B8A8_SNORM':
                    result = numpy.ones(mesh_loops_length * 4, dtype=numpy.float32)
                    normals = numpy.empty(mesh_loops_length * 3, dtype=numpy.float32)
                    mesh_loops.foreach_get('normal', normals)
                    result[0::4] = normals[0::3]
                    result[1::4] = normals[1::3]
                    result[2::4] = normals[2::3]
                    

                    if MainConfig.get_game_category() == GameCategory.UnrealVS or MainConfig.get_game_category() == GameCategory.UnrealCS:
                        bitangent_signs = numpy.empty(mesh_loops_length, dtype=numpy.float32)
                        mesh_loops.foreach_get("bitangent_sign", bitangent_signs)
                        result[3::4] = bitangent_signs

                        # XXX 3.6和3.2都需要翻转一下，原因未知
                        if bpy.app.version < (4,0,0):
                            result[0::4] *= -1
                            result[1::4] *= -1
                            result[2::4] *= -1
                        print("Unreal: Set NORMAL.W to bitangent_sign")
                    
                    result = result.reshape(-1, 4)

                    self.element_vertex_ndarray[d3d11_element_name] = BufferDataConverter.convert_4x_float32_to_r8g8b8a8_snorm(result)


                elif d3d11_element.Format == 'R8G8B8A8_UNORM':
                    result = numpy.ones(mesh_loops_length * 4, dtype=numpy.float32)
                    normals = numpy.empty(mesh_loops_length * 3, dtype=numpy.float32)
                    mesh_loops.foreach_get('normal', normals)
                    result[0::4] = normals[0::3]
                    result[1::4] = normals[1::3]
                    result[2::4] = normals[2::3]
                    result = result.reshape(-1, 4)

                    self.element_vertex_ndarray[d3d11_element_name] = BufferDataConverter.convert_4x_float32_to_r8g8b8a8_unorm(new_array)

                else:
                    result = numpy.empty(mesh_loops_length * 3, dtype=numpy.float32)
                    mesh_loops.foreach_get('normal', result)
                    # 将一维数组 reshape 成 (mesh_loops_length, 3) 形状的二维数组
                    result = result.reshape(-1, 3)
                    self.element_vertex_ndarray[d3d11_element_name] = result


            elif d3d11_element_name == 'TANGENT':
                result = numpy.empty(mesh_loops_length * 4, dtype=numpy.float32)

                # 使用 foreach_get 批量获取切线和副切线符号数据
                tangents = numpy.empty(mesh_loops_length * 3, dtype=numpy.float32)
                mesh_loops.foreach_get("tangent", tangents)
                # 将切线分量放置到输出数组中
                result[0::4] = tangents[0::3]  # x 分量
                result[1::4] = tangents[1::3]  # y 分量
                result[2::4] = tangents[2::3]  # z 分量

                if MainConfig.get_game_category() == GameCategory.UnityCS or MainConfig.get_game_category() == GameCategory.UnityVS:
                    bitangent_signs = numpy.empty(mesh_loops_length, dtype=numpy.float32)
                    mesh_loops.foreach_get("bitangent_sign", bitangent_signs)
                    # XXX 将副切线符号乘以 -1
                    # 这里翻转（翻转指的就是 *= -1）是因为如果要确保Unity游戏中渲染正确，必须翻转TANGENT的W分量
                    bitangent_signs *= -1
                    result[3::4] = bitangent_signs  # w 分量 (副切线符号)
                elif MainConfig.get_game_category() == GameCategory.UnrealVS or MainConfig.get_game_category() == GameCategory.UnrealCS:
                    # Unreal引擎中这里要填写固定的1
                    tangent_w = numpy.ones(mesh_loops_length, dtype=numpy.float32)
                    result[3::4] = tangent_w
                
                # 重塑 output_tangents 成 (mesh_loops_length, 4) 形状的二维数组
                result = result.reshape(-1, 4)

                if d3d11_element.Format == 'R16G16B16A16_FLOAT':
                    result = result.astype(numpy.float16)

                elif d3d11_element.Format == 'R8G8B8A8_SNORM':
                    result = BufferDataConverter.convert_4x_float32_to_r8g8b8a8_snorm(result)

                elif d3d11_element.Format == 'R8G8B8A8_UNORM':
                    result = BufferDataConverter.convert_4x_float32_to_r8g8b8a8_unorm(result)

                self.element_vertex_ndarray[d3d11_element_name] = result

            elif d3d11_element_name.startswith('COLOR'):
                # TimerUtils.Start("Get COLOR")

                if d3d11_element_name in mesh.vertex_colors:
                    # 因为COLOR属性存储在Blender里固定是float32类型所以这里只能用numpy.float32
                    result = numpy.zeros(mesh_loops_length, dtype=(numpy.float32, 4))
                    mesh.vertex_colors[d3d11_element_name].data.foreach_get("color", result.ravel())
                    
                    if d3d11_element.Format == 'R16G16B16A16_FLOAT':
                        result = result.astype(numpy.float16)
                    elif d3d11_element.Format == "R16G16_FLOAT":
                        result = result[:, :2]
                    elif d3d11_element.Format == 'R8G8B8A8_UNORM':
                        result = BufferDataConverter.convert_4x_float32_to_r8g8b8a8_unorm(result)

                    self.element_vertex_ndarray[d3d11_element_name] = result

                # TimerUtils.End("Get COLOR") # 0:00:00.030605 
            elif d3d11_element_name.startswith('TEXCOORD') and d3d11_element.Format.endswith('FLOAT'):
                # TimerUtils.Start("GET TEXCOORD")
                for uv_name in ('%s.xy' % d3d11_element_name, '%s.zw' % d3d11_element_name):
                    if uv_name in mesh.uv_layers:
                        uvs_array = numpy.empty(mesh_loops_length ,dtype=(numpy.float32,2))
                        mesh.uv_layers[uv_name].data.foreach_get("uv",uvs_array.ravel())
                        uvs_array[:,1] = 1.0 - uvs_array[:,1]

                        if d3d11_element.Format == 'R16G16_FLOAT':
                            uvs_array = uvs_array.astype(numpy.float16)
                        
                        # 重塑 uvs_array 成 (mesh_loops_length, 2) 形状的二维数组
                        # uvs_array = uvs_array.reshape(-1, 2)

                        self.element_vertex_ndarray[d3d11_element_name] = uvs_array 
                # TimerUtils.End("GET TEXCOORD")
                        
            elif d3d11_element_name.startswith('BLENDINDICES'):
                
                if d3d11_element.Format == "R32G32B32A32_SINT":
                    self.element_vertex_ndarray[d3d11_element_name] = blendindices
                elif d3d11_element.Format == "R32G32B32A32_UINT":
                    self.element_vertex_ndarray[d3d11_element_name] = blendindices
                elif d3d11_element.Format == "R32G32_UINT":
                    self.element_vertex_ndarray[d3d11_element_name] = blendindices[:, :2]
                elif d3d11_element.Format == "R32_UINT":
                    self.element_vertex_ndarray[d3d11_element_name] = blendindices[:, :1]
                elif d3d11_element.Format == 'R8G8B8A8_SNORM':
                    self.element_vertex_ndarray[d3d11_element_name] = BufferDataConverter.convert_4x_float32_to_r8g8b8a8_snorm(blendindices)
                elif d3d11_element.Format == 'R8G8B8A8_UNORM':
                    self.element_vertex_ndarray[d3d11_element_name] = BufferDataConverter.convert_4x_float32_to_r8g8b8a8_unorm(blendindices)
                elif d3d11_element.Format == 'R8G8B8A8_UINT':
                    blendindices.astype(numpy.uint8)
                    self.element_vertex_ndarray[d3d11_element_name] = blendindices
                

 
            elif d3d11_element_name.startswith('BLENDWEIGHT'):
                # patch时跳过生成数据
                if not self.d3d11GameType.PatchBLENDWEIGHTS:
                    if d3d11_element.Format == "R32G32B32A32_FLOAT":
                        self.element_vertex_ndarray[d3d11_element_name] = blendweights
                    elif d3d11_element.Format == "R32G32_FLOAT":
                        self.element_vertex_ndarray[d3d11_element_name] = blendweights[:, :2]
                    elif d3d11_element.Format == 'R8G8B8A8_SNORM':
                        self.element_vertex_ndarray[d3d11_element_name] = BufferDataConverter.convert_4x_float32_to_r8g8b8a8_snorm(blendweights)
                    elif d3d11_element.Format == 'R8G8B8A8_UNORM':
                        self.element_vertex_ndarray[d3d11_element_name] = BufferDataConverter.convert_4x_float32_to_r8g8b8a8_unorm(blendweights)
            
                    
                    
                

    def calc_index_vertex_buffer(self,obj,mesh:bpy.types.Mesh):
        '''
        计算IndexBuffer和CategoryBufferDict并返回

        这里是速度瓶颈，23万顶点情况下测试，前面的获取mesh数据只用了1.5秒
        但是这里两个步骤加起来用了6秒，占了4/5运行时间。
        不过暂时也够用了，先不管了。
        '''
        # TimerUtils.Start("Calc IB VB")
        # (1) 统计模型的索引和唯一顶点
        
        
        if GenerateModConfig.export_same_number() and "TANGENT" in self.d3d11GameType.OrderedFullElementList:
            '''
            保持相同顶点数时，让相同顶点使用相同的TANGENT值来避免增加索引数和顶点数。
            这里我们使用每个顶点第一次出现的TANGENT值。
            效率比下面的低50%，不过能使用这个选项的场景只有导入直接导出原模型，所以总运行时间基本都在0.4秒以内，用户感觉不到差距的，没问题。
            '''
            # 创建一个空列表用于存储最终的结果
            # index_vertex_id_dict = {}
            ib = []
            indexed_vertices = collections.OrderedDict()
            # 一个字典确保每个符合条件的position只出现过一次
            position_normal_sharedtangent_dict = {}
            # 遍历每个多边形（polygon）
            for poly in mesh.polygons:
                # 创建一个临时列表用于存储当前多边形的索引
                vertex_indices = []
                
                # 遍历当前多边形中的每一个环（loop），根据多边形的起始环和环总数
                for blender_lvertex in mesh.loops[poly.loop_start:poly.loop_start + poly.loop_total]:
                    vertex_data_get = self.element_vertex_ndarray[blender_lvertex.index].copy()
                    poskey = tuple(vertex_data_get['POSITION'] + vertex_data_get['NORMAL'])
                    if poskey in position_normal_sharedtangent_dict:
                        tangent_var = position_normal_sharedtangent_dict[poskey]
                        vertex_data_get['TANGENT'] = tangent_var
                    else:
                        tangent_var = vertex_data_get['TANGENT']
                        position_normal_sharedtangent_dict[poskey] = tangent_var
                    
                    vertex_data = vertex_data_get.tobytes()
                    index = indexed_vertices.setdefault(vertex_data, len(indexed_vertices))
                    vertex_indices.append(index)
                    # index_vertex_id_dict[index] = blender_lvertex.vertex_index
                
                # 将当前多边形的顶点索引列表添加到最终结果列表中
                ib.append(vertex_indices)

            # print("长度：")
            # print(len(position_normal_sharedtangent_dict))
        else:
            '''
            不保持相同顶点时，仍然使用我们经典而又快速的方法
            '''
            # index_vertex_id_dict = {}
            indexed_vertices = collections.OrderedDict()
            ib = [[indexed_vertices.setdefault(self.element_vertex_ndarray[blender_lvertex.index].tobytes(), len(indexed_vertices))
                    for blender_lvertex in mesh.loops[poly.loop_start:poly.loop_start + poly.loop_total]
                        ]for poly in mesh.polygons] 
            
            # TODO 这里100%会用到，因为必须得到一个loop_vertex_id和普通vertex_id的对应列表。
            
            # 很显然上面注释掉的才是最快的，但是没办法，我们必须得获取每个draw的索引对应的顶点索引
            # ib = []
            # for poly in mesh.polygons:
            #     loop_indices = []
            #     for blender_lvertex in mesh.loops[poly.loop_start:poly.loop_start + poly.loop_total]:
            #         vertex_bytes = self.element_vertex_ndarray[blender_lvertex.index].tobytes()
            #         index = indexed_vertices.setdefault(vertex_bytes, len(indexed_vertices))
            #         loop_indices.append(index)
            #         # 在这里可以执行额外的操作，例如：
            #         # print(f"Processed vertex with bytes {vertex_bytes}")
            #         # 或者更新其他状态
            #         index_vertex_id_dict[index] = blender_lvertex.vertex_index
            #     ib.append(loop_indices)   


        flattened_ib = [item for sublist in ib for item in sublist]
        # TimerUtils.End("Calc IB VB")

        indexed_vertices = BufferDataConverter.average_normal_tangent(obj=obj, indexed_vertices=indexed_vertices, d3d11GameType=self.d3d11GameType,dtype=self.dtype)
        indexed_vertices = BufferDataConverter.average_normal_color(obj=obj, indexed_vertices=indexed_vertices, d3d11GameType=self.d3d11GameType,dtype=self.dtype)

        # (2) 转换为CategoryBufferDict
        # TimerUtils.Start("Calc CategoryBuffer")
        category_stride_dict = self.d3d11GameType.get_real_category_stride_dict()
        category_buffer_dict:dict[str,list] = {}
        for categoryname,category_stride in self.d3d11GameType.CategoryStrideDict.items():
            category_buffer_dict[categoryname] = []

        data_matrix = numpy.array([numpy.frombuffer(byte_data,dtype=numpy.uint8) for byte_data in indexed_vertices])
        stride_offset = 0
        for categoryname,category_stride in category_stride_dict.items():
            category_buffer_dict[categoryname] = data_matrix[:,stride_offset:stride_offset + category_stride].flatten()
            stride_offset += category_stride
        # TimerUtils.End("Calc CategoryBuffer")
        return flattened_ib,category_buffer_dict

def get_buffer_ib_vb_fast(d3d11GameType:D3D11GameType):
    '''
    使用Numpy直接从mesh中转换数据到目标格式Buffer
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

    return buffer_model.calc_index_vertex_buffer(obj, mesh)




