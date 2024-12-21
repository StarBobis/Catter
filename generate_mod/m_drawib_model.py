from ..migoto.vertex_buffer import *
from ..migoto.index_buffer import *
from ..migoto.migoto_export import get_export_ib_vb

from ..core.common.global_config import *

from .m_draw_type import *

from ..utils.collection_utils import *
from ..config.global_config import *
from ..utils.json_utils import *

from .m_ini_helper import *


# TODO remove this later.
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
        self.draw_ib = ""

        self.export_json_dict = {} 
        self.obj_name_ib_dict:dict[str,IndexBuffer] = {} 
        self.obj_name_vb_dict:dict[str,VertexBuffer] =  {} 
        self.d3d11GameType:D3D11GameType = None 

        # 输出Mod时用的
        self.componentname_ibbuf_dict = {}
        self.categoryname_bytelist_dict = {}
        self.draw_number = 0
        self.obj_name_drawindexed_dict:dict[str,M_DrawIndexed] = {}

        # tmp.json的内容
        self.category_hash_dict = {}
        self.match_first_index_list = []
        self.part_name_list = []
        self.vertex_limit_hash = ""

        # 按键切换ini生成使用
        self.key_number = 0

        self.componentname_modelcollection_list_dict:dict[str,list[ModelCollection]] = {}
        self.PartName_SlotReplaceDict_Dict = {}
        self.TextureResource_Name_FileName_Dict:dict[str,str] = {}
        self.extract_gametype_folder_path = ""

        self.__parse_drawib_collection(draw_ib_collection=draw_ib_collection)
        self.__read_component_ib_buf_dict()
        self.__read_categoryname_bytelist_dict()
        self.__read_tmp_json()


    def __parse_drawib_collection(self,draw_ib_collection):
        self.draw_ib = CollectionUtils.get_clean_collection_name(draw_ib_collection.name)
        # 构建一个export.json，记录当前集合所有object层级关系
        self.export_json_dict = CollectionUtils.parse_drawib_collection_to_export_json(draw_ib_collection)

        # 转换为更加好读的形式：
        for component_name, model_collection_dict in self.export_json_dict.items():
            model_collection_list = []
            for model_collection_name,model_dict in model_collection_dict.items():
                model_collection = ModelCollection()
                model_collection.type = model_dict["type"]
                model_collection.model_collection_name = model_collection_name
                model_collection.obj_name_list = model_dict["model"]
                model_collection_list.append(model_collection)
            
            self.componentname_modelcollection_list_dict[component_name] = model_collection_list

        # 分析并提取key结构,首先统计一共有几个key
        tmp_number = 0
        for component_name, model_collection_dict in self.export_json_dict.items():
            toggle_number = 0 # 切换
            switch_number = 0 # 开关
            for model_collection_name,model_dict in model_collection_dict.items():
                if model_dict["type"] == "toggle":
                    toggle_number = toggle_number + 1
                elif model_dict["type"] == "switch":
                    switch_number = switch_number + 1
            
            tmp_number = tmp_number + switch_number
            if toggle_number >= 2:
                tmp_number = tmp_number + 1
        self.key_number = tmp_number
        

        # 随后所有模型转为ib vb格式放入集合备用
        for export_component_collection in draw_ib_collection.children:
            for model_collection in export_component_collection.children:
                # 如果模型不可见则跳过。
                if not CollectionUtils.is_collection_visible(model_collection.name):
                    continue
                
                for obj in model_collection.objects:
                    # 判断对象是否为网格对象
                    if obj.type == 'MESH' and obj.hide_get() == False:
                        bpy.context.view_layer.objects.active = obj
                        ib,vb = get_export_ib_vb(bpy.context)

                        self.obj_name_ib_dict[obj.name] = ib
                        self.obj_name_vb_dict[obj.name] = vb


    def __read_component_ib_buf_dict(self):
        for component_name, component_value in self.export_json_dict.items():
            ib_buf = []
            offset = 0

            number_sum = 0
            for model_name, model_value in component_value.items():
                model_list = model_value["model"]
                for obj_name in model_list:
                    print("processing: " + obj_name)
                    ib = self.obj_name_ib_dict.get(obj_name,None)
                    unique_vertex_number = ib.get_unique_vertex_number()

                    if ib is None:
                        print("Can't find ib object for " + obj_name +",skip this obj process.")
                        continue
                    obj_ib_buf = ib.get_index_buffer(number_sum)
                    ib_buf.extend(obj_ib_buf)

                    drawindexed_obj = M_DrawIndexed()
                    draw_number = len(obj_ib_buf) * 3
                    drawindexed_obj.DrawNumber = str(draw_number)
                    drawindexed_obj.DrawOffsetIndex = str(offset)
                    drawindexed_obj.AliasName = "collection name: [" + model_name + "] obj name: [" + obj_name + "]  (VertexCount:" + str(unique_vertex_number) + ")"
                    self.obj_name_drawindexed_dict[obj_name] = drawindexed_obj
                    offset = offset + draw_number

                    # Add UniqueVertexNumber to show vertex count in mod ini.
                    print(unique_vertex_number)
                    number_sum = number_sum + unique_vertex_number

            self.componentname_ibbuf_dict[component_name] = ib_buf
    
    
    def __read_categoryname_bytelist_dict(self):
        for component_name, component_value in self.export_json_dict.items():
            for model_name, model_value in component_value.items():
                model_list = model_value["model"]
                for obj_name in model_list:
                    # print("processing: " + obj_name)
                    vb = self.obj_name_vb_dict.get(obj_name,None)
                    if vb is None:
                        print("Can't find vb object for " + obj_name +",skip this obj process.")
                        continue

                    vb_elementname_bytelist_dict = vb.convert_to_elementname_byteslist_dict()
                    obj = bpy.data.objects[obj_name]
                    gametypename = obj.get("3DMigoto:GameTypeName",None)
                    gametype_file_path = os.path.join(MainConfig.path_current_game_type_folder(), gametypename + ".json")
                    d3d11gametype = D3D11GameType(gametype_file_path)
                    self.d3d11GameType = d3d11gametype


                    # 如果patchBLENDWEIGHTS则移除BLENWEIGHTS
                    # TODO 检查BLENDWEIGHT和BLENDWEIGHTS读取到Blender的处理方式是否相同，如果相同则全部变为BLENDWEIGHTS
                    # 数据类型里面也得改
                    blendweights_name = ""
                    if d3d11gametype.PatchBLENDWEIGHTS:
                        if "BLENDWEIGHTS" in vb_elementname_bytelist_dict:
                            del vb_elementname_bytelist_dict["BLENDWEIGHTS"]
                            blendweights_name = "BLENDWEIGHTS"
                        elif "BLENDWEIGHT" in vb_elementname_bytelist_dict:
                            del vb_elementname_bytelist_dict["BLENDWEIGHT"]
                            blendweights_name = "BLENDWEIGHT"

                    tmp_categoryname_bytelist_dict:dict[str,list] = {}
                    for element_name in d3d11gametype.OrderedFullElementList:
                        
                        # process PatchBLENDWEIGHTS
                        if d3d11gametype.PatchBLENDWEIGHTS and element_name == blendweights_name:
                            continue

                        d3d11Element = d3d11gametype.ElementNameD3D11ElementDict[element_name]
                        category_name = d3d11Element.Category
                        element_stride = d3d11Element.ByteWidth

                        add_byte_list = vb_elementname_bytelist_dict[element_name]
                        vertex_number = int(len(add_byte_list) / element_stride)
                        # print(vertex_number)

                        # 防止没被初始化
                        if category_name not in tmp_categoryname_bytelist_dict:
                            tmp_categoryname_bytelist_dict[category_name] = []

                        old_byte_list = tmp_categoryname_bytelist_dict[category_name]
                        old_stride = int(len(old_byte_list) / vertex_number)

                        category_new_bytelist = []
                        
                        for i in range(vertex_number):
                            old_start_index = i * old_stride
                            old_end_index = old_start_index + old_stride
                            # print(old_start_index)

                            already_byte_list_some = old_byte_list[old_start_index:old_end_index]

                            add_start_index = i * element_stride
                            add_end_index = add_start_index + element_stride
                            add_byte_list_some = add_byte_list[add_start_index:add_end_index]

                            already_byte_list_some.extend(add_byte_list_some)
                            category_new_bytelist.extend(already_byte_list_some)

                        
                        tmp_categoryname_bytelist_dict[category_name] = category_new_bytelist
                    
                    # 获取完临时的，就拼接到完整的
                    for category_name in d3d11gametype.OrderedCategoryNameList:
                        # 防止空的
                        if category_name not in self.categoryname_bytelist_dict:
                            self.categoryname_bytelist_dict[category_name] = []
                        
                        # 追加数据
                        self.categoryname_bytelist_dict[category_name].extend(tmp_categoryname_bytelist_dict[category_name])
        
        # 顺便计算一下步长得到总顶点数
        position_stride = d3d11gametype.CategoryStrideDict["Position"]
        position_bytelength = len(self.categoryname_bytelist_dict["Position"])
        self.draw_number = int(position_bytelength/position_stride)

        

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

        partname_textureresourcereplace_dict:dict[str,str] = tmp_json_dict["PartNameTextureResourceReplaceList"]
        for partname, texture_resource_replace_list in partname_textureresourcereplace_dict.items():
            slot_replace_dict = {}
            for texture_resource_replace in texture_resource_replace_list:
                splits = texture_resource_replace.split("=")
                slot_name = splits[0].strip()
                texture_filename = splits[1].strip()
                resource_name = "Resource_" + os.path.splitext(texture_filename)[0]
                slot_replace_dict[slot_name] = resource_name

                self.TextureResource_Name_FileName_Dict[resource_name] = texture_filename
            self.PartName_SlotReplaceDict_Dict[partname] = slot_replace_dict
    
    def write_buffer_files(self):
        # Export IndexBuffer files.
        for partname in self.part_name_list:
            component_name = "Component " + partname
            ib_buf = self.componentname_ibbuf_dict.get(component_name,None)
            if ib_buf is None:
                print("Export Failed, Can't get ib buf for partname: " + partname)
            else:
                ib_path = MainConfig.path_generatemod_buffer_folder(draw_ib=self.draw_ib) + self.draw_ib + "-" + M_IniHelper.get_style_alias(partname) + ".buf"
                with open(ib_path, 'wb') as ibf:
                    for ib_byte_number in ib_buf:
                        ibf.write(ib_byte_number) 

        # Export category buffer files.
        for category_name, category_buf in self.categoryname_bytelist_dict.items():
            buf_path = MainConfig.path_generatemod_buffer_folder(draw_ib=self.draw_ib) + self.draw_ib + "-" + category_name + ".buf"
            buf_bytearray = bytearray(category_buf)
            with open(buf_path, 'wb') as ibf:
                ibf.write(buf_bytearray)
