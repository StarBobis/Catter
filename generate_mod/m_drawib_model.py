from ..import_model.vertex_buffer import *
from ..import_model.index_buffer import *
from .m_export import get_export_ib_vb

from ..migoto.global_config import *

from .m_draw_type import *

from ..utils.collection_utils import *
from ..config.main_config import *
from ..utils.json_utils import *
from ..utils.timer_utils import *

from .m_ini_helper import *

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
        self.__obj_name_ib_dict:dict[str,IndexBuffer] = {} 
        self.__obj_name_vb_dict:dict[str,VertexBuffer] =  {} 
        self.componentname_ibbuf_dict = {} # 每个Component都生成一个IndexBuffer文件。
        self.__categoryname_bytelist_dict = {} # 每个Category都生成一个CategoryBuffer文件。
        # TODO 每个DrawIB，都应该有它所有的obj组合成的ShapeKey数据，在读取完每个obj的drawindexed对象后进行获取

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

        # 用于自动贴图
        self.PartName_SlotTextureReplaceDict_Dict:dict[str,dict[str,TextureReplace]] = {}
        self.TextureResource_Name_FileName_Dict:dict[str,str] = {}

        # 按顺序执行
        self.__read_gametype_from_import_json()
        self.__parse_drawib_collection_architecture(draw_ib_collection=draw_ib_collection)
        self.__parse_key_number()
        self.__parse_obj_name_ib_vb_dict()
        self.__read_component_ib_buf_dict()
        self.__read_categoryname_bytelist_dict()
        self.__read_tmp_json()

    def __read_gametype_from_import_json(self):
        workspace_import_json_path = os.path.join(MainConfig.path_workspace_folder(), "Import.json")
        draw_ib_gametypename_dict = JsonUtils.LoadFromFile(workspace_import_json_path)
        gametypename = draw_ib_gametypename_dict.get(self.draw_ib,"")
        gametype_file_path = os.path.join(MainConfig.path_current_game_type_folder(), gametypename + ".json")
        if os.path.exists(gametype_file_path):
            self.d3d11GameType:D3D11GameType = D3D11GameType(gametype_file_path)
        else:
            raise Fatal("Please do a reimport model from your workspace at least once to generate a Import.json in your WorkSpace folder, because the Import.json in your WorkSpace is not found.")

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

    def __parse_obj_name_ib_vb_dict(self):
        # TimerUtils.Start("__parse_obj_name_ib_vb_dict")
        '''
        把之前统计的所有obj都转为ib和vb格式备用
        '''
        for model_collection_list in self.componentname_modelcollection_list_dict.values():
            for model_collection in model_collection_list:
                for obj_name in model_collection.obj_name_list:
                    obj = bpy.data.objects[obj_name]
                    bpy.context.view_layer.objects.active = obj
                    ib,vb = get_export_ib_vb(bpy.context,self.d3d11GameType)

                    self.__obj_name_ib_dict[obj.name] = ib
                    self.__obj_name_vb_dict[obj.name] = vb
        
        # TimerUtils.End("__parse_obj_name_ib_vb_dict")

    def __read_component_ib_buf_dict(self):
        vertex_number_ib_offset = 0
        for component_name, moel_collection_list in self.componentname_modelcollection_list_dict.items():
            ib_buf = []
            offset = 0
            for model_collection in moel_collection_list:
                for obj_name in model_collection.obj_name_list:
                    print("processing: " + obj_name)
                    ib = self.__obj_name_ib_dict.get(obj_name,None)
                    unique_vertex_number = ib.get_unique_vertex_number()

                    if ib is None:
                        print("Can't find ib object for " + obj_name +",skip this obj process.")
                        continue
                    
                    print("component name: " + component_name)
                    print("vertex_number_ib_offset: " + str(vertex_number_ib_offset))
                    obj_ib_buf = ib.get_index_buffer(vertex_number_ib_offset)
                    ib_buf.extend(obj_ib_buf)

                    drawindexed_obj = M_DrawIndexed()
                    draw_number = len(obj_ib_buf) * 3
                    drawindexed_obj.DrawNumber = str(draw_number)
                    drawindexed_obj.DrawOffsetIndex = str(offset)
                    drawindexed_obj.UniqueVertexCount = unique_vertex_number
                    drawindexed_obj.AliasName = "collection name: [" + model_collection.model_collection_name + "] obj name: [" + obj_name + "]  (VertexCount:" + str(unique_vertex_number) + ")"
                    self.obj_name_drawindexed_dict[obj_name] = drawindexed_obj
                    offset = offset + draw_number

                    # Add UniqueVertexNumber to show vertex count in mod ini.
                    print(unique_vertex_number)
                    vertex_number_ib_offset = vertex_number_ib_offset + unique_vertex_number
            
            # Only export if it's not empty.
            if len(ib_buf) != 0:
                self.componentname_ibbuf_dict[component_name] = ib_buf
            else:
                LOG.warning(self.draw_ib + " collection: " + component_name + " is hide, skip export ib buf.")
    
    
    def __read_categoryname_bytelist_dict(self):
        for component_name, model_collection_list in self.componentname_modelcollection_list_dict.items():
            for model_collection in model_collection_list:
                for obj_name in model_collection.obj_name_list:
                    vb = self.__obj_name_vb_dict.get(obj_name,None)
                    if vb is None:
                        print("Can't find vb object for " + obj_name +",skip this obj process.")
                        continue

                    vb_elementname_bytelist_dict = vb.convert_to_elementname_byteslist_dict()
                    obj = bpy.data.objects[obj_name]

                    # 如果patchBLENDWEIGHTS则移除BLENWEIGHTS
                    # TODO 检查BLENDWEIGHT和BLENDWEIGHTS读取到Blender的处理方式是否相同，如果相同则全部变为BLENDWEIGHTS
                    # 数据类型里面也得改
                    blendweights_name = ""
                    if self.d3d11GameType.PatchBLENDWEIGHTS:
                        if "BLENDWEIGHTS" in vb_elementname_bytelist_dict:
                            del vb_elementname_bytelist_dict["BLENDWEIGHTS"]
                            blendweights_name = "BLENDWEIGHTS"
                        elif "BLENDWEIGHT" in vb_elementname_bytelist_dict:
                            del vb_elementname_bytelist_dict["BLENDWEIGHT"]
                            blendweights_name = "BLENDWEIGHT"

                    tmp_categoryname_bytelist_dict:dict[str,list] = {}
                    for element_name in self.d3d11GameType.OrderedFullElementList:
                        
                        # process PatchBLENDWEIGHTS
                        if self.d3d11GameType.PatchBLENDWEIGHTS and element_name == blendweights_name:
                            continue

                        d3d11Element = self.d3d11GameType.ElementNameD3D11ElementDict[element_name]
                        category_name = d3d11Element.Category
                        element_stride = d3d11Element.ByteWidth

                        add_byte_list = vb_elementname_bytelist_dict[element_name]
                        vertex_number = int(len(add_byte_list) / element_stride)
                        LOG.newline()
                        print("add_byte_list length:" + str(len(add_byte_list)))
                        print("element_name:" + element_name)
                        print("element_stride:" + str(element_stride))
                        print("vertex_number:" + str(vertex_number))

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
                    for category_name in self.d3d11GameType.OrderedCategoryNameList:
                        # 防止空的
                        if category_name not in self.__categoryname_bytelist_dict:
                            self.__categoryname_bytelist_dict[category_name] = []
                        
                        # 追加数据
                        self.__categoryname_bytelist_dict[category_name].extend(tmp_categoryname_bytelist_dict[category_name])
        
        # 顺便计算一下步长得到总顶点数
        position_stride = self.d3d11GameType.CategoryStrideDict["Position"]
        position_bytelength = len(self.__categoryname_bytelist_dict["Position"])
        self.draw_number = int(position_bytelength/position_stride)

    def __read_shapekey_data(self):
        # 这里不用担心循环obj_name时顺序是否正确，因为python3.7版本之后dict会保留插入时的顺序。
        for obj_name, drawindexed_obj in self.obj_name_drawindexed_dict.items():
            obj = bpy.data.objects[obj_name]

            # TODO 先完成WWMI一键导入，再完成这里的ShapeKey读取部分
            base_data = obj.data.shape_keys.key_blocks['Basis'].data
            shapekey_pattern = re.compile(r'.*(?:deform|custom)[_ -]*(\d+).*')

            shapekeys = []
            for shapekey in obj.data.shape_keys.key_blocks:
                match = shapekey_pattern.findall(shapekey.name.lower())
                if len(match) == 0:
                    continue
                shapekey_id = int(match[0])
                shapekeys.append((shapekey_id, shapekey))

            shapekey_data = {}
            for vertex_id in range(len(obj.data.vertices)):
                base_vertex_coords = base_data[vertex_id].co
                shapekey_data[vertex_id] = {}
                for (shapekey_id, shapekey) in shapekeys:
                    shapekey_vertex_coords = shapekey.data[vertex_id].co
                    vertex_offset = shapekey_vertex_coords - base_vertex_coords
                    if vertex_offset.length < 0.00000001:
                        continue
                    shapekey_data[vertex_id][shapekey_id] = list(vertex_offset)


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



    
    

    def write_buffer_files(self):
        '''
        用于导出IndexBuffer文件和CategoryBuffer文件
        TODO 后面新增了ShapeKey之后，在这里新增ShapeKey三个Buffer的导出
        '''
        # Export IndexBuffer files.
        for partname in self.part_name_list:
            component_name = "Component " + partname
            ib_buf = self.componentname_ibbuf_dict.get(component_name,None)
            if ib_buf is None:
                print("Export Skip, Can't get ib buf for partname: " + partname)
            else:
                ib_path = MainConfig.path_generatemod_buffer_folder(draw_ib=self.draw_ib) + self.draw_ib + "-" + M_IniHelper.get_style_alias(partname) + ".buf"
                with open(ib_path, 'wb') as ibf:
                    for ib_byte_number in ib_buf:
                        ibf.write(ib_byte_number) 

        # Export category buffer files.
        for category_name, category_buf in self.__categoryname_bytelist_dict.items():
            buf_path = MainConfig.path_generatemod_buffer_folder(draw_ib=self.draw_ib) + self.draw_ib + "-" + category_name + ".buf"
            buf_bytearray = bytearray(category_buf)
            with open(buf_path, 'wb') as ibf:
                ibf.write(buf_bytearray)
