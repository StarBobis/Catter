import numpy
import struct
import re

from .m_export import get_buffer_ib_vb_fast

from .d3d11_game_type import *

from ..utils.collection_utils import *
from ..config.main_config import *
from ..utils.json_utils import *
from ..utils.timer_utils import *
from ..utils.migoto_utils import Fatal
from ..utils.obj_utils import ObjUtils

from .m_ini_helper import *

class M_DrawIndexed:

    def __init__(self) -> None:
        self.DrawNumber = ""
        self.DrawOffsetIndex = ""
        self.DrawStartIndex = "0"

        # 代表一个obj具体的draw_indexed
        self.AliasName = "" 

        # 代表这个obj的顶点数
        self.UniqueVertexCount = 0 
    
    def get_draw_str(self) ->str:
        return "drawindexed = " + self.DrawNumber + "," + self.DrawOffsetIndex +  "," + self.DrawStartIndex


class TextureReplace:
    def  __init__(self):
        self.resource_name = ""
        self.filter_index = 0
        self.hash = ""
        

class ModelCollection:
    def __init__(self):
        self.type = ""
        self.model_collection_name = ""
        self.obj_name_list = []

# 这个代表了一个DrawIB的Mod导出模型
# 后面的Mod导出都可以调用这个模型来进行业务逻辑部分
class DrawIBModel:
    # 通过default_factory让每个类的实例的变量分割开来，不再共享类的静态变量
    def __init__(self,draw_ib_collection):
        '''
        single_ib_file 一般这个选项Unity游戏都可以填False，虚幻游戏我们沿用WWMI的传统，先使用True试验。

        TODO 后续WWMI支持添加完成后，测试并使single_ib_file变为可选项。
        '''
        self.single_ib = GenerateModConfig.every_drawib_single_ib_file()
        self.__obj_name_ib_dict:dict[str,list] = {} 
        self.__obj_name_category_buffer_list_dict:dict[str,list] =  {} 
        # self.__obj_name_index_vertex_id_dict:dict[str,dict] = {}
        self.componentname_ibbuf_dict = {} # 每个Component都生成一个IndexBuffer文件，或者所有Component共用一个IB文件。
        self.__categoryname_bytelist_dict = {} # 每个Category都生成一个CategoryBuffer文件。

        # 生成Mod的ini时要使用的内容
        self.draw_ib = CollectionUtils.get_clean_collection_name(draw_ib_collection.name).split("_")[0]
        self.d3d11GameType:D3D11GameType = None

        self.draw_number = 0 # 每个DrawIB都有总的顶点数，对应CategoryBuffer里的顶点数。
        self.obj_name_drawindexed_dict:dict[str,M_DrawIndexed] = {} # 给每个obj的属性统计好，后面就能直接用了。
        self.category_hash_dict = {}
        self.match_first_index_list = []
        self.part_name_list = []
        self.vertex_limit_hash = ""
        self.key_number = 0
        self.componentname_modelcollection_list_dict:dict[str,list[ModelCollection]] = {}
        self.extract_gametype_folder_path = ""

        self.shapekey_offsets = []
        self.shapekey_vertex_ids = []
        self.shapekey_vertex_offsets = []

        # 用于自动贴图
        self.PartName_SlotTextureReplaceDict_Dict:dict[str,dict[str,TextureReplace]] = {}
        self.TextureResource_Name_FileName_Dict:dict[str,str] = {}

        # 按顺序执行
        self.__read_gametype_from_import_json()
        self.__parse_drawib_collection_architecture(draw_ib_collection=draw_ib_collection)
        self.__parse_key_number()

        # obj转换为指定格式备用
        self.__parse_obj_name_ib_category_buffer_dict()
        


        # 构建IndexBuffer
        if self.single_ib:
            self.__read_component_ib_buf_dict_merged()
        else:
            self.__read_component_ib_buf_dict_seperated()
        
        # 目前只有WWMI会需要读取ShapeKey数据
        if MainConfig.gamename == "WWMI":
            self.__read_shapekey_cateogry_buf_dict()

        # 构建每个Category的VertexBuffer
        self.__read_categoryname_bytelist_dict()

        # 读取tmp.json中用于导出的数据
        self.__read_tmp_json()


        # 用于写出时便于使用
        self.PartName_IBResourceName_Dict = {}
        self.PartName_IBBufferFileName_Dict = {}

        # Export Index Buffer files.
        self.write_ib_files()
        # Export Category Buffer files.
        self.write_category_buffer_files()
        # Export ShapeKey Buffer Files.(WWMI)
        if MainConfig.gamename == "WWMI":
            pass


    def __read_gametype_from_import_json(self):
        workspace_import_json_path = os.path.join(MainConfig.path_workspace_folder(), "Import.json")
        draw_ib_gametypename_dict = JsonUtils.LoadFromFile(workspace_import_json_path)
        gametypename = draw_ib_gametypename_dict.get(self.draw_ib,"")

        # 新版本中，我们把数据类型的信息写到了tmp.json中，这样我们就能够读取tmp.json中的内容来决定生成Mod时的数据类型了。
        self.extract_gametype_folder_path = MainConfig.path_extract_gametype_folder(draw_ib=self.draw_ib,gametype_name=gametypename)
        tmp_json_path = os.path.join(self.extract_gametype_folder_path,"tmp.json")
        if os.path.exists(tmp_json_path):
            self.d3d11GameType:D3D11GameType = D3D11GameType(tmp_json_path)
        else:
            raise Fatal("Can't find your tmp.json for generate mod:" + tmp_json_path)




    def __parse_drawib_collection_architecture(self,draw_ib_collection):
        # TimerUtils.Start("__parse_drawib_collection_architecture")

        LOG.info("DrawIB: " + self.draw_ib)
        LOG.info("Visiable: " + str(CollectionUtils.is_collection_visible(draw_ib_collection.name)))

        '''
        解析工作空间集合架构，得到方便后续访问使用的抽象数据类型。
        '''
        for component_collection in draw_ib_collection.children:
            # 从集合名称中获取导出后部位的名称，如果有.001这种自动添加的后缀则去除掉
            component_name = CollectionUtils.get_clean_collection_name(component_collection.name)

            model_collection_list = []
            for m_collection in component_collection.children:
                # 如果模型不可见则跳过。
                if not CollectionUtils.is_collection_visible(m_collection.name):
                    LOG.info("Skip " + m_collection.name + " because it's invisiable.")
                    continue

                LOG.info("Current Processing Collection: " + m_collection.name)

                # 声明一个model_collection对象
                model_collection = ModelCollection()
                model_collection.model_collection_name = m_collection.name

                # 先根据颜色确定是什么类型的集合 03黄色是开关 04绿色是分支
                model_collection_type = "default"
                if m_collection.color_tag == "COLOR_03":
                    model_collection_type = "switch"
                elif m_collection.color_tag == "COLOR_04":
                    model_collection_type = "toggle"
                model_collection.type = model_collection_type

                # 集合中的模型列表
                for obj in m_collection.objects:
                    # 判断对象是否为网格对象，并且不是隐藏状态
                    if obj.type == 'MESH' and obj.hide_get() == False:
                        model_collection.obj_name_list.append(obj.name)

                model_collection_list.append(model_collection)

            self.componentname_modelcollection_list_dict[component_name] = model_collection_list
        # TimerUtils.End("__parse_drawib_collection_architecture")

    def __parse_key_number(self):
        '''
        提前统计好有多少个Key要声明
        '''
        tmp_number = 0
        for model_collection_list in self.componentname_modelcollection_list_dict.values():
            toggle_number = 0 # 切换
            switch_number = 0 # 开关
            for model_collection in model_collection_list:
                if model_collection.type == "toggle":
                    toggle_number = toggle_number + 1
                elif model_collection.type == "switch":
                    switch_number = switch_number + 1
            
            tmp_number = tmp_number + switch_number
            if toggle_number >= 2:
                tmp_number = tmp_number + 1
        self.key_number = tmp_number

    def __parse_obj_name_ib_category_buffer_dict(self):
        # TimerUtils.Start("__parse_obj_name_ib_vb_dict")
        '''
        把之前统计的所有obj都转为ib和category_buffer_dict格式备用
        '''
        for model_collection_list in self.componentname_modelcollection_list_dict.values():
            for model_collection in model_collection_list:
                for obj_name in model_collection.obj_name_list:
                    obj = bpy.data.objects[obj_name]
                    
                    # 选中当前obj对象
                    bpy.context.view_layer.objects.active = obj

                    # 对当前obj对象执行权重规格化
                    if GenerateModConfig.export_normalize_all():
                        if "Blend" in self.d3d11GameType.OrderedCategoryNameList:
                            ObjUtils.normalize_all(obj)

                    ib, category_buffer_dict = get_buffer_ib_vb_fast(self.d3d11GameType)

                    self.__obj_name_ib_dict[obj.name] = ib
                    self.__obj_name_category_buffer_list_dict[obj.name] = category_buffer_dict
                    # self.__obj_name_index_vertex_id_dict[obj.name] = index_vertex_id_dict
        
        # TimerUtils.End("__parse_obj_name_ib_vb_dict")


    def __read_component_ib_buf_dict_merged(self):
        '''
        所有Component共享整体的IB文件。
        是游戏原本的做法，但是不分开的话整体会遇到135W上限。
        '''
        vertex_number_ib_offset = 0
        ib_buf = []
        draw_offset = 0
        for component_name, moel_collection_list in self.componentname_modelcollection_list_dict.items():
            for model_collection in moel_collection_list:
                for obj_name in model_collection.obj_name_list:
                    print("processing: " + obj_name)
                    ib = self.__obj_name_ib_dict.get(obj_name,None)

                    # ib的数据类型是list[int]
                    unique_vertex_number_set = set(ib)
                    unique_vertex_number = len(unique_vertex_number_set)

                    if ib is None:
                        print("Can't find ib object for " + obj_name +",skip this obj process.")
                        continue

                    offset_ib = []
                    for ib_number in ib:
                        offset_ib.append(ib_number + vertex_number_ib_offset)
                    
                    print("Component name: " + component_name)
                    print("Draw Offset: " + str(vertex_number_ib_offset))
                    ib_buf.extend(offset_ib)

                    drawindexed_obj = M_DrawIndexed()
                    draw_number = len(offset_ib)
                    drawindexed_obj.DrawNumber = str(draw_number)
                    drawindexed_obj.DrawOffsetIndex = str(draw_offset)
                    drawindexed_obj.UniqueVertexCount = unique_vertex_number
                    drawindexed_obj.AliasName = "[" + model_collection.model_collection_name + "] [" + obj_name + "]  (" + str(unique_vertex_number) + ")"
                    self.obj_name_drawindexed_dict[obj_name] = drawindexed_obj
                    draw_offset = draw_offset + draw_number

                    # Add UniqueVertexNumber to show vertex count in mod ini.
                    print("Draw Number: " + str(unique_vertex_number))
                    vertex_number_ib_offset = vertex_number_ib_offset + unique_vertex_number

                    LOG.newline()


        for component_name, moel_collection_list in self.componentname_modelcollection_list_dict.items():
            # Only export if it's not empty.
            if len(ib_buf) != 0:
                self.componentname_ibbuf_dict[component_name] = ib_buf
            else:
                LOG.warning(self.draw_ib + " collection: " + component_name + " is hide, skip export ib buf.")

    def __read_component_ib_buf_dict_seperated(self):
        '''
        每个Component都有一个单独的IB文件。
        所以每个Component都有135W上限。
        '''
        vertex_number_ib_offset = 0
        for component_name, moel_collection_list in self.componentname_modelcollection_list_dict.items():
            ib_buf = []
            offset = 0
            for model_collection in moel_collection_list:
                for obj_name in model_collection.obj_name_list:
                    print("processing: " + obj_name)
                    ib = self.__obj_name_ib_dict.get(obj_name,None)

                    # ib的数据类型是list[int]
                    unique_vertex_number_set = set(ib)
                    unique_vertex_number = len(unique_vertex_number_set)

                    if ib is None:
                        print("Can't find ib object for " + obj_name +",skip this obj process.")
                        continue

                    offset_ib = []
                    for ib_number in ib:
                        offset_ib.append(ib_number + vertex_number_ib_offset)
                    
                    print("Component name: " + component_name)
                    print("Draw Offset: " + str(vertex_number_ib_offset))
                    ib_buf.extend(offset_ib)

                    drawindexed_obj = M_DrawIndexed()
                    draw_number = len(offset_ib)
                    drawindexed_obj.DrawNumber = str(draw_number)
                    drawindexed_obj.DrawOffsetIndex = str(offset)
                    drawindexed_obj.UniqueVertexCount = unique_vertex_number
                    drawindexed_obj.AliasName = "[" + model_collection.model_collection_name + "] [" + obj_name + "]  (" + str(unique_vertex_number) + ")"
                    self.obj_name_drawindexed_dict[obj_name] = drawindexed_obj
                    offset = offset + draw_number

                    # Add UniqueVertexNumber to show vertex count in mod ini.
                    print("Draw Number: " + str(unique_vertex_number))
                    vertex_number_ib_offset = vertex_number_ib_offset + unique_vertex_number

                    LOG.newline()
            
            # Only export if it's not empty.
            if len(ib_buf) != 0:
                self.componentname_ibbuf_dict[component_name] = ib_buf
            else:
                LOG.warning(self.draw_ib + " collection: " + component_name + " is hide, skip export ib buf.")

    def __read_shapekey_cateogry_buf_dict(self):
        '''
        读取形态键部分

        我也不想重写一遍的，但是WWMI的架构要求先合并obj，我们的架构实在是做不到优雅的合并obj
        所以只能参照他的方法重写一份了。
        '''
        TimerUtils.Start("read shapekey data")

        shapekey_index_list = []
        shapekey_data = {}

        vertex_count_offset = 0

        for obj_name, drawindexed_obj in self.obj_name_drawindexed_dict.items():
            obj = bpy.data.objects[obj_name]
            # LOG.newline()
            # print("Processing obj: " + obj_name)
            # obj_index_vertex_id_dict = self.__obj_name_index_vertex_id_dict[obj_name]
            mesh = obj.data
            
            # 如果这个obj的mesh没有形态键，那就直接跳过不处理
            mesh_shapekeys = mesh.shape_keys
            if mesh_shapekeys is None:
                print("obj: " + obj_name + " doesn't have any ShapeKey data, skip it.")

                # 即使跳过了这个obj，这个顶点数偏移依然要加上，否则得到的结果是不正确的
                vertex_count_offset = vertex_count_offset + drawindexed_obj.UniqueVertexCount
                continue   

            print(obj_name + "'s shapekey number: " + str(len(mesh.shape_keys.key_blocks)))

            base_data = mesh_shapekeys.key_blocks['Basis'].data
            for shapekey in mesh_shapekeys.key_blocks:
                # print(shapekey.name)
                # 截取形态键名称中的形态键shapekey_id，获取不到就跳过
                shapekey_pattern = re.compile(r'.*(?:deform|custom)[_ -]*(\d+).*')
                match = shapekey_pattern.findall(shapekey.name.lower())
                
                if len(match) == 0:
                    continue
                shapekey_index = int(match[0])
                # print(shapekey_index)
                # 因为WWMI的形态键数量只有128个，这里shapekey_id是从0开始的，所以到127结束，所以不能大于等于128
                if shapekey_index >= 128:
                    break

                if shapekey_index not in shapekey_index_list:
                    shapekey_index_list.append(shapekey_index)

                # 对于这个obj的每个顶点，我们都要尝试从当前shapekey中获取数据，如果获取到了，就放入缓存

                # 获取此obj的ib buf的值
                # ib_list = self.__obj_name_ib_dict[obj_name] 
                # ib_list中的每个值都是vertex_index，所以可以直接用来从形态键中获取数据
                # for draw_index in ib_list:
                for draw_index in range(len(mesh.vertices)):

                    # vertex_index = obj_index_vertex_id_dict[draw_index]
                    vertex_index = draw_index

                    base_vertex_coords = base_data[vertex_index].co
                    shapekey_vertex_coords = shapekey.data[vertex_index].co
                    vertex_offset = shapekey_vertex_coords - base_vertex_coords
                    # 到这里已经有vertex_id、shapekey_id、vertex_offset了，就不用像WWMI一样再从缓存读取了
                    offseted_vertex_index = vertex_index + vertex_count_offset

                    if offseted_vertex_index not in shapekey_data:
                        shapekey_data[offseted_vertex_index] = {}

                    # 如果相差太小，说明无效或者是一样的，说明这个顶点没有ShapeKey，此时向ShapeKeyOffsets中添加空的0
                    if vertex_offset.length < 0.00000001:
                        continue

                    # 此时如果能获取到，说明有效，此时可以直接放入准备好的字典
                    shapekey_data[offseted_vertex_index][shapekey_index] = list(vertex_offset)

                    

                # break
            # 对于每一个obj的每个顶点，都从0到128获取它的形态键对应偏移值
            vertex_count_offset = vertex_count_offset + drawindexed_obj.UniqueVertexCount
        
        # TODO 这里需要排序吗？还不确定，只能等写完ini支持再测试了
        # shapekey_index_list.sort()

        # LOG.newline()
        # print("shapekeys: " + str(len(shapekey_index_list))) # 3
        # print(shapekey_index_list)
        shapekey_cache = {shapekey_id:{} for shapekey_id in shapekey_index_list}

        for i in range(vertex_count_offset):
            vertex_shapekey_data = shapekey_data.get(i, None)
            if vertex_shapekey_data is not None:
                for shapekey_index,vertex_offsets in vertex_shapekey_data.items():
                    shapekey_cache[shapekey_index][i] = vertex_offsets

        




        shapekey_verts_count = 0
        # 从0到128去获取ShapeKey的Index，有就直接加到
        for group_id in range(128):

            shapekey = shapekey_cache.get(group_id, None)
            if shapekey is None or len(shapekey_cache[group_id]) == 0:
                self.shapekey_offsets.extend([shapekey_verts_count if shapekey_verts_count != 0 else 0])
                continue

            self.shapekey_offsets.extend([shapekey_verts_count])

            for draw_index, vertex_offsets in shapekey.items():
                self.shapekey_vertex_ids.extend([draw_index])
                self.shapekey_vertex_offsets.extend(vertex_offsets + [0, 0, 0])
                shapekey_verts_count += 1

        LOG.newline()
        # TODO 这里的数字和WWMI导出的对不上，咱也不知道为啥，也许是WWMI中合并了一些顶点所以导致最后的形态键的顶点数量减少了？
        # 暂时无法确定，但是我们得到的内容和游戏中提取出来的一模一样，感觉90%以上的概率应该是正确的。
        # 使用大草神测试 DrawIB:94517393
        print(self.shapekey_offsets[0])
        print(self.shapekey_vertex_ids[0])
        print(self.shapekey_vertex_offsets[0])

        print("shapekey_offsets: " + str(len(self.shapekey_offsets))) # 128 WWMI:128
        print("shapekey_vertex_ids: " + str(len(self.shapekey_vertex_ids))) # 29161 WWMI:29404
        print("shapekey_vertex_offsets: " + str(len(self.shapekey_vertex_offsets))) # 174966  WWMI:29404 * 6  = 176424 * 2 = 352848
        TimerUtils.End("read shapekey data")


    def __read_categoryname_bytelist_dict(self):
        # TimerUtils.Start("__read_categoryname_bytelist_dict")
        for component_name, model_collection_list in self.componentname_modelcollection_list_dict.items():
            for model_collection in model_collection_list:
                for obj_name in model_collection.obj_name_list:
                    category_buffer_list = self.__obj_name_category_buffer_list_dict.get(obj_name,None)
                    
                    if category_buffer_list is None:
                        print("Can't find vb object for " + obj_name +",skip this obj process.")
                        continue

                    for category_name in self.d3d11GameType.OrderedCategoryNameList:
                        

                        if category_name not in self.__categoryname_bytelist_dict:
                            self.__categoryname_bytelist_dict[category_name] =  category_buffer_list[category_name]
                        else:
                            existing_array = self.__categoryname_bytelist_dict[category_name]
                            buffer_array = category_buffer_list[category_name]

                            # 确保两个数组都是NumPy数组
                            existing_array = numpy.asarray(existing_array)
                            buffer_array = numpy.asarray(buffer_array)

                            # 使用 concatenate 连接两个数组，确保传递的是一个序列（如列表或元组）
                            concatenated_array = numpy.concatenate((existing_array, buffer_array))

                            # 更新字典中的值
                            self.__categoryname_bytelist_dict[category_name] = concatenated_array


                            # self.__categoryname_bytelist_dict[category_name] = numpy.concatenate(self.__categoryname_bytelist_dict[category_name],category_buffer_list[category_name])
        
        # 顺便计算一下步长得到总顶点数
        # print(self.d3d11GameType.CategoryStrideDict)
        position_stride = self.d3d11GameType.CategoryStrideDict["Position"]
        position_bytelength = len(self.__categoryname_bytelist_dict["Position"])
        self.draw_number = int(position_bytelength/position_stride)

        # TimerUtils.End("__read_categoryname_bytelist_dict")  
        # 耗时大概1S左右



    def __read_tmp_json(self):
        self.extract_gametype_folder_path = MainConfig.path_extract_gametype_folder(draw_ib=self.draw_ib,gametype_name=self.d3d11GameType.GameTypeName)
        tmp_json_path = os.path.join(self.extract_gametype_folder_path,"tmp.json")
        tmp_json_dict = JsonUtils.LoadFromFile(tmp_json_path)

        self.category_hash_dict = tmp_json_dict["CategoryHash"]
        self.import_model_list = tmp_json_dict["ImportModelList"]
        self.match_first_index_list = tmp_json_dict["MatchFirstIndex"]
        self.part_name_list = tmp_json_dict["PartNameList"]
        # print(self.partname_textureresourcereplace_dict)
        self.vertex_limit_hash = tmp_json_dict["VertexLimitVB"]
        self.work_game_type = tmp_json_dict["WorkGameType"]

        # 自动贴图依赖于这个字典
        partname_textureresourcereplace_dict:dict[str,str] = tmp_json_dict["PartNameTextureResourceReplaceList"]
        for partname, texture_resource_replace_list in partname_textureresourcereplace_dict.items():
            slot_texture_replace_dict = {}
            for texture_resource_replace in texture_resource_replace_list:
                splits = texture_resource_replace.split("=")
                slot_name = splits[0].strip()
                texture_filename = splits[1].strip()

                resource_name = "Resource_" + os.path.splitext(texture_filename)[0]

                filename_splits = os.path.splitext(texture_filename)[0].split("-")
                texture_hash = filename_splits[1]

                texture_replace = TextureReplace()
                texture_replace.hash = texture_hash
                texture_replace.resource_name = resource_name

                slot_texture_replace_dict[slot_name] = texture_replace

                self.TextureResource_Name_FileName_Dict[resource_name] = texture_filename

            self.PartName_SlotTextureReplaceDict_Dict[partname] = slot_texture_replace_dict

    def write_ib_files(self):
        for partname in self.part_name_list:
            style_part_name = M_IniHelper.get_style_alias(partname)
            component_name = "Component " + partname
            ib_buf = self.componentname_ibbuf_dict.get(component_name,None)

            ib_resource_name = "Resource_" + self.draw_ib + "_" + style_part_name
            ib_buf_filename = self.draw_ib + "-" + style_part_name + ".buf"

            self.PartName_IBResourceName_Dict[partname] = ib_resource_name
            self.PartName_IBBufferFileName_Dict[partname] = ib_buf_filename

            if ib_buf is None:
                print("Export Skip, Can't get ib buf for partname: " + partname)
            else:
                ib_path = MainConfig.path_generatemod_buffer_folder(draw_ib=self.draw_ib) + ib_buf_filename

                packed_data = struct.pack(f'<{len(ib_buf)}I', *ib_buf)
                with open(ib_path, 'wb') as ibf:
                    ibf.write(packed_data) 
            
            if self.single_ib:
                break

    def write_category_buffer_files(self):
        buf_output_folder = MainConfig.path_generatemod_buffer_folder(draw_ib=self.draw_ib)
        # Export category buffer files.
        for category_name, category_buf in self.__categoryname_bytelist_dict.items():
            buf_path = buf_output_folder + self.draw_ib + "-" + category_name + ".buf"
            # print(type(category_buf[0]))
             # 将 list 转换为 numpy 数组
            # category_array = numpy.array(category_buf, dtype=numpy.uint8)
            with open(buf_path, 'wb') as ibf:
                category_buf.tofile(ibf)

        # TODO 后面新增了ShapeKey之后，在这里新增ShapeKey三个Buffer的导出
        if len(self.shapekey_offsets) != 0:
            with open(buf_output_folder + self.draw_ib + "-" + "ShapeKeyOffset.buf", 'wb') as file:
                for number in self.shapekey_offsets:
                    # 假设数字是32位整数，使用'i'格式符
                    # 根据实际需要调整数字格式和相应的格式符
                    data = struct.pack('i', number)
                    file.write(data)
        
        if len(self.shapekey_vertex_ids) != 0:
            with open(buf_output_folder + self.draw_ib + "-" + "ShapeKeyVertexId.buf", 'wb') as file:
                for number in self.shapekey_vertex_ids:
                    # 假设数字是32位整数，使用'i'格式符
                    # 根据实际需要调整数字格式和相应的格式符
                    data = struct.pack('i', number)
                    file.write(data)
        
        if len(self.shapekey_vertex_offsets) != 0:
            # 将列表转换为numpy数组，并改变其数据类型为float16
            float_array = numpy.array(self.shapekey_vertex_offsets, dtype=numpy.float32).astype(numpy.float16)
            
            # 以二进制模式写入文件
            with open(buf_output_folder + self.draw_ib + "-" + "ShapeKeyVertexOffset.buf", 'wb') as file:
                float_array.tofile(file)

