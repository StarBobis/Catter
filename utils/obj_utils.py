import bpy

from mathutils import Matrix 
from mathutils import Vector
from mathutils import *
from math import * 
import math
import bmesh

from .migoto_utils import Fatal

class ObjUtils:

    @classmethod
    def normalize_all(cls,obj):
        '''
        调用前需确保选中了这个obj，也就是当前的active对象是这个obj
        '''
        print("Normalize All Weights For: " + obj.name)
        # 选择你要操作的对象，这里假设场景中只有一个导入的OBJ对象
        if obj and obj.type == 'MESH':
            # 进入权重编辑模式（如果需要）
            bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
            
            # 确保该对象是活动的，并且被选中
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            
            # 对所有顶点组应用 Normalize All
            bpy.ops.object.vertex_group_normalize_all()

            # 回到物体模式
            bpy.ops.object.mode_set(mode='OBJECT')
        else:
            print("没有找到合适的网格对象来执行规范化操作。")

    @classmethod
    def mesh_triangulate(cls,me):
        '''
        三角化一个mesh
        注意这个三角化之后就变成新的mesh了
        '''
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()

    @classmethod
    def get_bpy_context_object(cls):
        '''
        获取当前场景中的obj对象,如果为None则抛出Fatal异常
        '''
        obj = bpy.context.object
        if obj is None:
            # 为空时不导出
            raise Fatal('No object selected')
        
        return obj

    @classmethod
    def selected_obj_delete_loose(cls):
        # 获取当前选中的对象
        selected_objects = bpy.context.selected_objects
        # 检查是否选中了一个Mesh对象
        for obj in selected_objects:
            if obj.type == 'MESH':
                # 设置当前对象为活动对象 （不设置的话后面没法切换编辑模式，就会报错）
                bpy.context.view_layer.objects.active = obj
                # 获取选中的网格对象
                bpy.ops.object.mode_set(mode='EDIT')
                # 选择所有的顶点
                bpy.ops.mesh.select_all(action='SELECT')
                # 执行删除孤立顶点操作
                bpy.ops.mesh.delete_loose()
                # 切换回对象模式
                bpy.ops.object.mode_set(mode='OBJECT')
    


class SmoothNormal:
    '''
    SmoothNormal Algorithm.
    SupportedGame: GI,HI3,HSR,ZZZ,WuWa
    Designed For: ZZZ,WuWa 

    Nico：此方法不知道为什么只能近似还原TEXCOORD1中内容，猜测是缺少了加权平均？
    缺少相关知识太多了，暂时放着

    # 代码版权与来源：
    # function 
    # https://www.bilibili.com/video/BV13G411u75s/?spm_id_from=333.999.0.0 
    # by 给你柠檬椰果养乐多你会跟我玩吗

    # 将法线XY分量存储到UV贴图的坐标(X:法线x, Y:法线y)
    # 灵感来自smoothtool from github 
    # by dashu04

    # 整合 by 失乡のKnight
    # 拆解信息链、重构为工具类 by NicoMico
    '''
    @classmethod
    def vector_cross_product(cls,v1,v2):
        '''
        叉乘 (Cross Product): 两个不平行的三维向量的叉乘会生成一个新的向量，这个新向量与原来的两个向量都垂直。
        因此，对于给定的三角形，使用其两边进行叉乘可以得到一个垂直于该三角形平面的向量，这就是所谓的法线向量。
        '''
        return Vector((v1.y*v2.z-v2.y*v1.z,v1.z*v2.x-v2.z*v1.x,v1.x*v2.y-v2.x*v1.y))
    
    @classmethod
    def vector_dot_product (cls,a,b):
        return a.x*b.x+a.y*b.y+a.z*b.z
    
    @classmethod
    def vector_calc_length(cls,v):
        return sqrt(v.x*v.x+v.y*v.y+v.z*v.z)
    
    @classmethod
    def vector_normalize(cls,v):
        '''
        归一化 (Normalization): 
        之后对叉乘结果进行归一化（normalize），即调整法线向量的长度为1，这样可以确保法线向量只表示方向而不带有长度信息。
        这一步很重要，因为光照计算通常依赖于单位长度的法线向量来保证正确性。
        '''
        L = cls.vector_calc_length(v)
        if L != 0 :
            return v/L
        return 0
    
    @classmethod
    def vector_to_string(cls,v):
        '''
        把Vector变为string，方便放入dict
        '''
        return "x=" + str(v.x) + ",y=" + str(v.y) + ",z=" + str(v.z)
    
    @classmethod
    def need_outline(cls,vertex):
        '''
        仅用于测试，实际使用中应永远返回True
        '''
        need = False
        for g in vertex.groups:
            if g.group == 446:
                need = True
                break
        return True
    
    @classmethod
    def calculate_angle_between_vectors (cls,v1,v2):
        ASIZE = cls.vector_calc_length(v1)
        BSIZE = cls.vector_calc_length(v2)
        D = ASIZE*BSIZE
        if D != 0:
            degree = math.acos(cls.vector_dot_product(v1,v2)/(ASIZE*BSIZE))
            #S = ASIZE*BSIZE*math.sin(degree)
            return degree
        return 0
    
    @classmethod
    def smooth_normal_save_to_uv(cls):
        mesh = bpy.context.active_object.data
        uvdata = mesh.uv_layers.active.data

        # TODO 这里只计算一个UV和不填任何参数结果有什么区别？需要测试
        mesh.calc_tangents(uvmap="TEXCOORD.xy")
        # mesh.calc_tangents()

        co_str_data_dict = {}

        # 开始
        for vertex in mesh.vertices:
            co = vertex.co
            co_str = cls.vector_to_string(co)
            co_str_data_dict[co_str] = []
        print("========")

        for poly in mesh.polygons:
            # 获取三角形的三个顶点
            loop_0 = mesh.loops[poly.loop_start]
            loop_1 = mesh.loops[poly.loop_start+1]
            loop_2 = mesh.loops[poly.loop_start + 2]

            # 获取顶点数据
            vertex_loop0 = mesh.vertices[loop_0.vertex_index]
            vertex_loop1 = mesh.vertices[loop_1.vertex_index]
            vertex_loop2 = mesh.vertices[loop_2.vertex_index]

            # 顶点数据转换为字符串格式
            co0_str = cls.vector_to_string(vertex_loop0.co)
            co1_str = cls.vector_to_string(vertex_loop1.co)
            co2_str = cls.vector_to_string(vertex_loop2.co)

            # 使用CorssProduct计算法线
            normal_vector = cls.vector_cross_product(vertex_loop1.co-vertex_loop0.co,vertex_loop2.co-vertex_loop0.co)
            # 法线归一化使其长度保持为1
            normal_vector = cls.vector_normalize(normal_vector)

            if co0_str in co_str_data_dict and cls.need_outline(vertex_loop0):
                w = cls.calculate_angle_between_vectors(vertex_loop2.co-vertex_loop0.co,vertex_loop1.co-vertex_loop0.co)
                co_str_data_dict[co0_str].append({"n":normal_vector,"w":w,"l":loop_0})
            if co1_str in co_str_data_dict and cls.need_outline(vertex_loop1):
                w = cls.calculate_angle_between_vectors(vertex_loop2.co-vertex_loop1.co,vertex_loop0.co-vertex_loop1.co)
                co_str_data_dict[co1_str].append({"n":normal_vector,"w":w,"l":loop_1})
            if co2_str in co_str_data_dict and cls.need_outline(vertex_loop0):
                w = cls.calculate_angle_between_vectors(vertex_loop1.co-vertex_loop2.co,vertex_loop0.co-vertex_loop2.co)
                co_str_data_dict[co2_str].append({"n":normal_vector,"w":w,"l":loop_2})

        # 存入UV
        uv_layer = mesh.uv_layers.new(name="SmoothNormalMap")
        for poly in mesh.polygons:
            for loop_index in range(poly.loop_start,poly.loop_start+poly.loop_total):
                vertex_index=mesh.loops[loop_index].vertex_index
                vertex = mesh.vertices[vertex_index]

                # 初始化平滑法线和平滑权重
                smoothnormal=Vector((0,0,0))
                weight = 0

                # 基于相邻面的法线加权平均计算平滑法线
                if cls.need_outline(vertex):
                    costr=cls.vector_to_string(vertex.co)

                    if costr in co_str_data_dict:
                        a = co_str_data_dict[costr]
                        # 对于共享此顶点的所有面的数据，遍历它们
                        for d in a:
                            # 分别获取面的法线和权重
                            normal_vector=d['n']
                            w = d['w']
                            # 累加加权法线和权重
                            smoothnormal  += normal_vector*w
                            weight  += w
                if smoothnormal != Vector((0,0,0)):
                    smoothnormal /= weight
                    smoothnormal = cls.vector_normalize(smoothnormal)

                loop_normal = mesh.loops[loop_index].normal
                loop_tangent = mesh.loops[loop_index].tangent
                loop_bitangent = mesh.loops[loop_index].bitangent

                tx = cls.vector_dot_product(loop_tangent,smoothnormal)
                ty = cls.vector_dot_product(loop_bitangent,smoothnormal)
                tz = cls.vector_dot_product(loop_normal,smoothnormal)

                normalT=Vector((tx,ty,tz))
                # print("nor:",smoothnormal)

                # 将法线XY分量存储到UV贴图的坐标 (X:法线x, Y:法线y)
                # 需要根据实际调整，例如UE为（x,1+y）

                # uv = (normalT.x, 1 + normalT.y) 
                uv = (normalT.x, 1 + normalT.y) 
                uv_layer.data[loop_index].uv = uv

        # 重新计算物体的UV贴图以应用更改
        # bpy.ops.object.mode_set(mode="EDIT")
        # bpy.ops.uv.unwrap(method='ANGLE_BASED')
        # bpy.ops.object.mode_set(mode="OBJECT")