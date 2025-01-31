import shutil
import math

from .m_ini_builder import *
from .m_drawib_model import *


class M_UnityIniModelSeperated:
    '''
    This used in :
    Unity VertexShader PreSkinning
    Unity ComputeShader PreSkinning
    Unity CPU PreSkinning
    '''
    drawib_drawibmodel_dict:dict[str,DrawIBModel] = {}

    global_key_index_constants = 0
    global_key_index_logic = 0
    global_generate_mod_number = 0

    vlr_filter_index_indent = ""

    # 贴图filter_index功能
    texture_hash_filter_index_dict = {}


    @classmethod
    def initialzie(cls):
        '''
        You have to call this to clean cache data before generate mod.
        '''
        cls.drawib_drawibmodel_dict = {}
        
        cls.global_key_index_constants = 0
        cls.global_key_index_logic = 0
        cls.global_generate_mod_number = 0

        cls.vlr_filter_index_indent = ""

        cls.texture_hash_filter_index_dict = {}


    @classmethod
    def add_constants_present_sections(cls,ini_builder,draw_ib_model:DrawIBModel):
        if draw_ib_model.key_number != 0:
            # 声明Constants变量
            constants_section = M_IniSection(M_SectionType.Constants)
            constants_section.append("global $active" + str(cls.global_generate_mod_number))
            for i in range(draw_ib_model.key_number):
                key_str = "global persist $swapkey" + str(i + cls.global_key_index_constants) + " = 0"
                constants_section.append(key_str) 

            ini_builder.append_section(constants_section)

            # 声明$active激活变量
            present_section = M_IniSection(M_SectionType.Present)
            present_section.append("post $active" + str(cls.global_generate_mod_number) + " = 0")

            ini_builder.append_section(present_section)

            # 声明按键切换和按键开关的变量
            for component_name, model_collection_list in draw_ib_model.componentname_modelcollection_list_dict.items():
                toggle_type_number = 0
                switch_type_number = 0
                
                for toggle_model_collection in model_collection_list:
                    if toggle_model_collection.type == "toggle":
                        toggle_type_number = toggle_type_number + 1
                    elif toggle_model_collection.type == "switch":
                        switch_type_number = switch_type_number + 1

                if toggle_type_number >= 2:
                    key_section = M_IniSection(M_SectionType.Key)
                    key_section.append("[KeySwap" + str(cls.global_key_index_constants) + "]")

                    if draw_ib_model.d3d11GameType.GPU_PreSkinning:
                        key_section.append("condition = $active" + str(cls.global_generate_mod_number) + " == 1")
                    key_section.append("key = " + DrawIBHelper.get_mod_switch_key(cls.global_key_index_constants))
                    key_section.append("type = cycle")
                    
                    key_cycle_str = ""
                    for i in range(toggle_type_number):
                        if i < toggle_type_number + 1:
                            key_cycle_str = key_cycle_str + str(i) + ","
                        else:
                            key_cycle_str = key_cycle_str + str(i)

                    key_section.append("$swapkey" + str(cls.global_key_index_constants) + " = " + key_cycle_str)
                    key_section.new_line()

                    ini_builder.append_section(key_section)
                    cls.global_key_index_constants = cls.global_key_index_constants + 1
                
                if switch_type_number >= 1:
                    for i in range(switch_type_number):
                        key_section = M_IniSection(M_SectionType.Key)
                        key_section.append("[KeySwap" + str(cls.global_key_index_constants) + "]")
                        if draw_ib_model.d3d11GameType.GPU_PreSkinning:
                            key_section.append("condition = $active" + str(cls.global_generate_mod_number) + " == 1")
                        key_section.append("key = " + DrawIBHelper.get_mod_switch_key(cls.global_key_index_constants))
                        key_section.append("type = cycle")
                        key_section.append("$swapkey" + str(cls.global_key_index_constants) + " = 1,0")
                        key_section.new_line()

                        ini_builder.append_section(key_section)
                        cls.global_key_index_constants = cls.global_key_index_constants + 1

    @classmethod
    def add_unity_vs_texture_override_vb_sections(cls,config_ini_builder:M_IniBuilder,commandlist_ini_builder:M_IniBuilder,draw_ib_model:DrawIBModel):
        # 声明TextureOverrideVB部分，只有使用GPU-PreSkinning时是直接替换hash对应槽位
        d3d11GameType = draw_ib_model.d3d11GameType
        draw_ib = draw_ib_model.draw_ib

        if d3d11GameType.GPU_PreSkinning:
            texture_override_vb_section = M_IniSection(M_SectionType.TextureOverrideVB)
            texture_override_vb_section.append("; " + draw_ib + " ----------------------------")
            for category_name in d3d11GameType.OrderedCategoryNameList:
                category_hash = draw_ib_model.category_hash_dict[category_name]
                category_slot = d3d11GameType.CategoryExtractSlotDict[category_name]

                texture_override_vb_name_suffix = "VB_" + draw_ib + "_" + category_name
                texture_override_vb_section.append("[TextureOverride_" + texture_override_vb_name_suffix + "]")
                texture_override_vb_section.append("hash = " + category_hash)

                # Call CommandList
                texture_override_vb_section.append("run = CommandList_" + texture_override_vb_name_suffix)
                texture_override_vb_section.new_line()

                # Initialize CommandList
                texture_override_vb_commandlist_section = M_IniSection(M_SectionType.CommandList)
                texture_override_vb_commandlist_section.append("[CommandList_" + texture_override_vb_name_suffix + "]")
                
                drawtype_indent_prefix = ""
                if GenerateModConfig.position_override_filter_draw_type():
                    if category_name == d3d11GameType.CategoryDrawCategoryDict["Position"]:
                        drawtype_indent_prefix = "  "
                        texture_override_vb_commandlist_section.append("if DRAW_TYPE == 1")
                
                # 如果出现了VertexLimitRaise，Texcoord槽位需要检测filter_index才能替换
                filterindex_indent_prefix = ""
                if GenerateModConfig.vertex_limit_raise_add_filter_index():
                    if category_name == d3d11GameType.CategoryDrawCategoryDict["Texcoord"]:
                        if cls.vlr_filter_index_indent != "":
                            texture_override_vb_commandlist_section.append("if vb0 == " + str(3000 + cls.global_generate_mod_number))
                            filterindex_indent_prefix = "  "

                # 遍历获取所有在当前分类hash下进行替换的分类，并添加对应的资源替换
                for original_category_name, draw_category_name in d3d11GameType.CategoryDrawCategoryDict.items():
                    if category_name == draw_category_name:
                        category_original_slot = d3d11GameType.CategoryExtractSlotDict[original_category_name]
                        texture_override_vb_commandlist_section.append(filterindex_indent_prefix + drawtype_indent_prefix + category_original_slot + " = Resource" + draw_ib + original_category_name)

                # draw一般都是在Blend槽位上进行的，所以我们这里要判断确定是Blend要替换的hash才能进行draw。
                if category_name == d3d11GameType.CategoryDrawCategoryDict["Blend"]:
                    texture_override_vb_commandlist_section.append(drawtype_indent_prefix + "handling = skip")
                    texture_override_vb_commandlist_section.append(drawtype_indent_prefix + "draw = " + str(draw_ib_model.draw_number) + ", 0")

                if GenerateModConfig.position_override_filter_draw_type():
                    # 对应if DRAW_TYPE == 1的结束
                    if category_name == d3d11GameType.CategoryDrawCategoryDict["Position"]:
                        texture_override_vb_commandlist_section.append("endif")
                
                if GenerateModConfig.vertex_limit_raise_add_filter_index():
                    # 对应if vb0 == 3000的结束
                    if category_name == d3d11GameType.CategoryDrawCategoryDict["Texcoord"]:
                        if cls.vlr_filter_index_indent != "":
                            texture_override_vb_commandlist_section.append("endif")
                
                # 分支架构，如果是Position则需提供激活变量
                if category_name == d3d11GameType.CategoryDrawCategoryDict["Position"]:
                    if draw_ib_model.key_number != 0:
                        texture_override_vb_commandlist_section.append("$active" + str(cls.global_generate_mod_number) + " = 1")

                texture_override_vb_commandlist_section.new_line()
                commandlist_ini_builder.append_section(texture_override_vb_commandlist_section)

            config_ini_builder.append_section(texture_override_vb_section)

    @classmethod
    def add_unity_vs_texture_override_ib_sections(cls,config_ini_builder:M_IniBuilder,commandlist_ini_builder:M_IniBuilder,draw_ib_model:DrawIBModel):
        texture_override_ib_section = M_IniSection(M_SectionType.TextureOverrideIB)
        texture_override_ib_commandlist_section = M_IniSection(M_SectionType.CommandList)
        draw_ib = draw_ib_model.draw_ib
        d3d11GameType = draw_ib_model.d3d11GameType

        for count_i in range(len(draw_ib_model.part_name_list)):
            match_first_index = draw_ib_model.match_first_index_list[count_i]
            part_name = draw_ib_model.part_name_list[count_i]

            style_part_name = DrawIBHelper.get_style_alias(part_name)

            texture_override_name_suffix = "IB_" + draw_ib + "_" + style_part_name

            # 读取使用的IBResourceName，如果读取不到，就使用默认的
            ib_resource_name = ""
            if draw_ib_model.single_ib:
                ib_resource_name = draw_ib_model.PartName_IBResourceName_Dict.get("1",None)
            else:
                ib_resource_name = draw_ib_model.PartName_IBResourceName_Dict.get(part_name,None)
            

            texture_override_ib_section.append("[TextureOverride_" + texture_override_name_suffix + "]")
            texture_override_ib_section.append("hash = " + draw_ib)
            texture_override_ib_section.append("match_first_index = " + match_first_index)

            if cls.vlr_filter_index_indent != "":
                texture_override_ib_section.append("if vb0 == " + str(3000 + cls.global_generate_mod_number))

            texture_override_ib_section.append(cls.vlr_filter_index_indent + "handling = skip")

            # If ib buf is emprt, continue to avoid add ib resource replace.
            ib_buf = draw_ib_model.componentname_ibbuf_dict.get("Component " + part_name,None)
            if ib_buf is None or len(ib_buf) == 0:
                texture_override_ib_section.new_line()
                continue

            # if ZZZ ,use run = CommandListSkinTexture solve slot check problems.
            if MainConfig.gamename == "ZZZ" :
                texture_override_ib_section.append(cls.vlr_filter_index_indent + "run = CommandListSkinTexture")
            # Add texture slot check, hash style texture also need this.
            # 根据用户反馈，默认删掉了，因为其它游戏用不到，ZZZ用的是run = CommandListSkinTexture
            # elif not GenerateModConfig.forbid_auto_texture_ini():
            #     texture_override_ib_section.append(cls.vlr_filter_index_indent + "; Add more slot check here to compatible with XXMI if you manually add more slot replace.")
            #     slot_texturereplace_dict = draw_ib_model.PartName_SlotTextureReplaceDict_Dict.get(part_name,None)

            #     # It may not have auto texture
            #     if slot_texturereplace_dict is not None:
            #         for slot in slot_texturereplace_dict.keys():
            #             texture_override_ib_section.append(cls.vlr_filter_index_indent  + "checktextureoverride = " + slot)



            # Add ib replace
            texture_override_ib_section.append(cls.vlr_filter_index_indent + "ib = " + ib_resource_name)

            # Add slot style texture slot replace.
            if not GenerateModConfig.forbid_auto_texture_ini() and not GenerateModConfig.hash_style_auto_texture():
                slot_texture_replace_dict:dict[str,TextureReplace] = draw_ib_model.PartName_SlotTextureReplaceDict_Dict.get(part_name,None)
                # It may not have auto texture
                if slot_texture_replace_dict is not None:
                    for slot,texture_replace in slot_texture_replace_dict.items():
                        texture_filter_index_indent = ""
                        if GenerateModConfig.slot_style_texture_add_filter_index():
                            texture_override_ib_section.append("if " + slot + " == " + str(cls.texture_hash_filter_index_dict[texture_replace.hash]))
                            texture_filter_index_indent = "  "

                        texture_override_ib_section.append(texture_filter_index_indent + cls.vlr_filter_index_indent + slot + " = " + texture_replace.resource_name)

                        if GenerateModConfig.slot_style_texture_add_filter_index():
                            texture_override_ib_section.append("endif")

            # 如果不使用GPU-Skinning即为Object类型，此时需要在ib下面替换对应槽位
            if not d3d11GameType.GPU_PreSkinning:
                for category_name in d3d11GameType.OrderedCategoryNameList:
                    category_hash = draw_ib_model.category_hash_dict[category_name]
                    category_slot = d3d11GameType.CategoryExtractSlotDict[category_name]

                    for original_category_name, draw_category_name in d3d11GameType.CategoryDrawCategoryDict.items():
                        if original_category_name == draw_category_name:
                            category_original_slot = d3d11GameType.CategoryExtractSlotDict[original_category_name]
                            texture_override_ib_section.append(cls.vlr_filter_index_indent + category_original_slot + " = Resource" + draw_ib + original_category_name)

            
            # prepare data
            component_name = "Component " + part_name 
            model_collection_list = draw_ib_model.componentname_modelcollection_list_dict[component_name]

            toggle_type_number = 0
            switch_type_number = 0

            toggle_model_collection_list:list[ModelCollection] = []
            switch_model_collection_list:list[ModelCollection] = []

            for toggle_model_collection in model_collection_list:
                if toggle_model_collection.type == "toggle":
                    toggle_type_number = toggle_type_number + 1
                    toggle_model_collection_list.append(toggle_model_collection)
                elif toggle_model_collection.type == "switch":
                    switch_type_number = switch_type_number + 1
                    switch_model_collection_list.append(toggle_model_collection)

            # Call CommandList
            texture_override_ib_section.append("run = CommandList_" + texture_override_name_suffix)
            texture_override_ib_section.new_line()

            # CommandList initialize
            texture_override_ib_commandlist_section.append("[CommandList_" + texture_override_name_suffix + "]")

            # Component DrawIndexed输出
            # 输出按键切换的DrawIndexed
            if toggle_type_number >= 2:
                for toggle_count in range(toggle_type_number):
                    if toggle_count == 0:
                        texture_override_ib_commandlist_section.append(cls.vlr_filter_index_indent + "if $swapkey" + str(cls.global_key_index_logic) + " == " + str(toggle_count))
                    else:
                        texture_override_ib_commandlist_section.append(cls.vlr_filter_index_indent + "else if $swapkey" + str(cls.global_key_index_logic) + " == " + str(toggle_count))

                    toggle_model_collection = toggle_model_collection_list[toggle_count]
                    for obj_name in toggle_model_collection.obj_name_list:
                        m_drawindexed = draw_ib_model.obj_name_drawindexed_dict[obj_name]
                        texture_override_ib_commandlist_section.append(cls.vlr_filter_index_indent + "; " + m_drawindexed.AliasName)
                        texture_override_ib_commandlist_section.append(cls.vlr_filter_index_indent  + m_drawindexed.get_draw_str())

                texture_override_ib_commandlist_section.append("endif")
                texture_override_ib_commandlist_section.new_line()

                cls.global_key_index_logic = cls.global_key_index_logic + 1
            elif toggle_type_number != 0:
                for toggle_model_collection in toggle_model_collection_list:
                    for obj_name in toggle_model_collection.obj_name_list:
                        m_drawindexed = draw_ib_model.obj_name_drawindexed_dict[obj_name]
                        texture_override_ib_commandlist_section.append(cls.vlr_filter_index_indent + "; " + m_drawindexed.AliasName)
                        texture_override_ib_commandlist_section.append(cls.vlr_filter_index_indent + m_drawindexed.get_draw_str())
                        texture_override_ib_commandlist_section.new_line()

            # 输出按键开关的DrawIndexed
            for switch_model_collection in switch_model_collection_list:
                texture_override_ib_commandlist_section.append(cls.vlr_filter_index_indent + "if $swapkey" + str(cls.global_key_index_logic) + "  == 1")
                for obj_name in switch_model_collection.obj_name_list:
                    m_drawindexed = draw_ib_model.obj_name_drawindexed_dict[obj_name]
                    texture_override_ib_commandlist_section.append(cls.vlr_filter_index_indent + "; " + m_drawindexed.AliasName)
                    texture_override_ib_commandlist_section.append(cls.vlr_filter_index_indent  + m_drawindexed.get_draw_str())
                    texture_override_ib_commandlist_section.new_line()
                texture_override_ib_commandlist_section.append(cls.vlr_filter_index_indent + "endif")
                texture_override_ib_commandlist_section.new_line()
                cls.global_key_index_logic = cls.global_key_index_logic + 1
            
            if cls.vlr_filter_index_indent:
                texture_override_ib_section.append("endif")
                texture_override_ib_section.new_line()
            
        config_ini_builder.append_section(texture_override_ib_section)
        commandlist_ini_builder.append_section(texture_override_ib_commandlist_section)

    @classmethod
    def add_unity_vs_texture_override_vlr_section(cls,config_ini_builder:M_IniBuilder,commandlist_ini_builder:M_IniBuilder,draw_ib_model:DrawIBModel):
        '''
        Add VertexLimitRaise section, UnityVS style.
        Only Unity VertexShader GPU-PreSkinning use this.

        格式问题：
        override_byte_stride = 40
        override_vertex_count = 14325
        由于这个格式并未添加到CommandList的解析中，所以没法单独写在CommandList里，只能写在TextureOverride下面
        所以我们这个VertexLimitRaise部分直接整体写入CommandList.ini中

        这个部分由于有一个Hash值，所以如果需要加密Mod并且让Hash值修复脚本能够运作的话，
        可以在最终制作完成Mod后，手动把这个VertexLimitRaise部分放到Config.ini中
        '''
        d3d11GameType = draw_ib_model.d3d11GameType
        draw_ib = draw_ib_model.draw_ib
        if d3d11GameType.GPU_PreSkinning:
            vertexlimit_section = M_IniSection(M_SectionType.TextureOverrideVertexLimitRaise)
            

            vertexlimit_section_name_suffix =  draw_ib + "_VertexLimitRaise"
            vertexlimit_section.append("[TextureOverride_" + vertexlimit_section_name_suffix + "]")
            vertexlimit_section.append("hash = " + draw_ib_model.vertex_limit_hash)

            # Call CommandList
            # vertexlimit_section.append("run = CommandList_" + vertexlimit_section_name_suffix)
            # vertexlimit_section.new_line()

            # Initialize CommandList
            # vertexlimit_commandlist_section = M_IniSection(M_SectionType.CommandList)
            # vertexlimit_commandlist_section.append("[CommandList_" + vertexlimit_section_name_suffix + "]" )
            
            
            if GenerateModConfig.vertex_limit_raise_add_filter_index():
                # 用户可能已经习惯了3000
                vertexlimit_section.append("filter_index = " + str(3000 + cls.global_generate_mod_number))
                cls.vlr_filter_index_indent = "  "

            vertexlimit_section.append("override_byte_stride = " + str(d3d11GameType.CategoryStrideDict["Position"]))
            vertexlimit_section.append("override_vertex_count = " + str(draw_ib_model.draw_number))
            vertexlimit_section.new_line()

            # config_ini_builder.append_section(vertexlimit_section)
            # commandlist_ini_builder.append_section(vertexlimit_commandlist_section)
            commandlist_ini_builder.append_section(vertexlimit_section)

    @classmethod
    def add_unity_vs_resource_vb_sections(cls,ini_builder,draw_ib_model:DrawIBModel):
        '''
        Add Resource VB Section
        '''
        resource_vb_section = M_IniSection(M_SectionType.ResourceBuffer)
        for category_name in draw_ib_model.d3d11GameType.OrderedCategoryNameList:
            resource_vb_section.append("[Resource" + draw_ib_model.draw_ib + category_name + "]")
            resource_vb_section.append("type = Buffer")

            if category_name == "Blend" and draw_ib_model.d3d11GameType.PatchBLENDWEIGHTS:
                blend_stride = draw_ib_model.d3d11GameType.ElementNameD3D11ElementDict["BLENDINDICES"].ByteWidth
                resource_vb_section.append("stride = " + str(blend_stride))
            else:
                resource_vb_section.append("stride = " + str(draw_ib_model.d3d11GameType.CategoryStrideDict[category_name]))
            
            resource_vb_section.append("filename = Buffer/" + draw_ib_model.draw_ib + "-" + category_name + ".buf")
            # resource_vb_section.append(";VertexCount: " + str(draw_ib_model.draw_number))
            resource_vb_section.new_line()
        
        '''
        Add Resource IB Section

        We default use R32_UINT because R16_UINT have a very small number limit.
        '''

        for partname, ib_filename in draw_ib_model.PartName_IBBufferFileName_Dict.items():
            ib_resource_name = draw_ib_model.PartName_IBResourceName_Dict.get(partname,None)
            resource_vb_section.append("[" + ib_resource_name + "]")
            resource_vb_section.append("type = Buffer")
            resource_vb_section.append("format = DXGI_FORMAT_R32_UINT")
            resource_vb_section.append("filename = Buffer/" + ib_filename)
            resource_vb_section.new_line()

        ini_builder.append_section(resource_vb_section)

    @classmethod
    def add_resource_ib_sections(cls,ini_builder,draw_ib_model):
        '''
        Add Resource IB Section

        We default use R32_UINT because R16_UINT have a very small number limit.
        '''
        for count_i in range(len(draw_ib_model.part_name_list)):
            partname = draw_ib_model.part_name_list[count_i]
            style_partname = DrawIBHelper.get_style_alias(partname)
            ib_resource_name = "Resource_" + draw_ib_model.draw_ib + "_" + style_partname

            resource_ib_section = M_IniSection(M_SectionType.ResourceBuffer)
            resource_ib_section.append("[" + ib_resource_name + "]")
            resource_ib_section.append("type = Buffer")
            resource_ib_section.append("format = DXGI_FORMAT_R32_UINT")
            resource_ib_section.append("filename = Buffer/" + draw_ib_model.draw_ib + "-" + style_partname + ".buf")
            resource_ib_section.new_line()

            ini_builder.append_section(resource_ib_section)

    @classmethod
    def add_resource_texture_sections(cls,ini_builder,draw_ib_model:DrawIBModel):
        '''
        Add texture resource.
        '''
        if GenerateModConfig.forbid_auto_texture_ini():
            return 
        
        # Hash style won't generate in here
        if GenerateModConfig.hash_style_auto_texture():
            return
        
        resource_texture_section = M_IniSection(M_SectionType.ResourceTexture)
        for resource_name, texture_filename in draw_ib_model.TextureResource_Name_FileName_Dict.items():
           
            resource_texture_section.append("[" + resource_name + "]")
            resource_texture_section.append("filename = Texture/" + texture_filename)
            resource_texture_section.new_line()

        ini_builder.append_section(resource_texture_section)

    @classmethod
    def move_slot_style_textures(cls,draw_ib_model:DrawIBModel):
        '''
        Move all textures from extracted game type folder to generate mod Texture folder.
        Only works in default slot style texture.
        '''
        if GenerateModConfig.forbid_auto_texture_ini():
            return
        
        if GenerateModConfig.hash_style_auto_texture():
            return
        
        for texture_filename in draw_ib_model.TextureResource_Name_FileName_Dict.values():
                target_path = MainConfig.path_generatemod_texture_folder(draw_ib=draw_ib_model.draw_ib) + texture_filename
                source_path = draw_ib_model.extract_gametype_folder_path + texture_filename
                
                # only overwrite when there is no texture file exists.
                if not os.path.exists(target_path):
                    shutil.copy2(source_path,target_path)

    @classmethod
    def generate_hash_style_texture_ini(cls):
        '''
        Generate Hash style TextureReplace.ini
        '''
        if GenerateModConfig.forbid_auto_texture_ini():
            return
        
        if not GenerateModConfig.hash_style_auto_texture():
            return 
        
        texture_ini_builder = M_IniBuilder()
        hash_texture_filename_dict:dict[str,str] = {}

        for draw_ib_model in cls.drawib_drawibmodel_dict.values():
            for texture_file_name in draw_ib_model.TextureResource_Name_FileName_Dict.values():
                texture_hash = texture_file_name.split("-")[1]
                hash_texture_filename_dict[texture_hash] = texture_file_name
        
        if len(hash_texture_filename_dict) == 0:
            return
        
        for draw_ib,draw_ib_model in cls.drawib_drawibmodel_dict.items():
            for texture_hash, texture_file_name in hash_texture_filename_dict.items():
                original_texture_file_path = draw_ib_model.extract_gametype_folder_path + texture_file_name

                # same hash usually won't exists in two folder.
                if not os.path.exists(original_texture_file_path):
                    continue

                # new_texture_file_name = draw_ib + "_" + texture_hash + "_" + texture_file_name.split("-")[3]
                new_texture_file_name = texture_hash + "_" + texture_file_name.split("-")[3]
                
                target_texture_file_path = MainConfig.path_generatemod_texture_folder(draw_ib=draw_ib) + new_texture_file_name
                
                resource_and_textureoverride_texture_section = M_IniSection(M_SectionType.ResourceAndTextureOverride_Texture)
                resource_and_textureoverride_texture_section.append("[Resource_Texture_" + texture_hash + "]")
                resource_and_textureoverride_texture_section.append("filename = Texture/" + new_texture_file_name)
                resource_and_textureoverride_texture_section.new_line()

                resource_and_textureoverride_texture_section.append("[TextureOverride_" + texture_hash + "]")
                resource_and_textureoverride_texture_section.append("; " + new_texture_file_name)
                resource_and_textureoverride_texture_section.append("hash = " + texture_hash)
                resource_and_textureoverride_texture_section.append("this = Resource_Texture_" + texture_hash)
                resource_and_textureoverride_texture_section.new_line()

                texture_ini_builder.append_section(resource_and_textureoverride_texture_section)

                # copy only if target not exists avoid overwrite texture manually replaced by mod author.
                if not os.path.exists(target_texture_file_path):
                    shutil.copy2(original_texture_file_path,target_texture_file_path)

        texture_ini_builder.save_to_file(MainConfig.path_generate_mod_folder() + "TextureReplace.ini")


    @classmethod
    def add_unity_cs_texture_override_vb_sections(cls,config_ini_builder:M_IniBuilder,commandlist_ini_builder:M_IniBuilder,draw_ib_model:DrawIBModel):
        # 声明TextureOverrideVB部分，只有使用GPU-PreSkinning时是直接替换hash对应槽位
        d3d11GameType = draw_ib_model.d3d11GameType
        draw_ib = draw_ib_model.draw_ib

        if d3d11GameType.GPU_PreSkinning:
            texture_override_vb_section = M_IniSection(M_SectionType.TextureOverrideVB)
            texture_override_vb_section.append("; " + draw_ib + " ----------------------------")
            for category_name in d3d11GameType.OrderedCategoryNameList:
                category_hash = draw_ib_model.category_hash_dict[category_name]
                category_slot = d3d11GameType.CategoryExtractSlotDict[category_name]
                texture_override_vb_namesuffix = "VB_" + draw_ib + "_" + category_name
                texture_override_vb_section.append("[TextureOverride_" + texture_override_vb_namesuffix + "]")
                texture_override_vb_section.append("hash = " + category_hash)
                
                # Initialize CommandList
                texture_override_vb_commandlist_section = M_IniSection(M_SectionType.CommandList)
                texture_override_vb_commandlist_section.append("[CommandList_" + texture_override_vb_namesuffix + "]")

                # Call CommandList
                texture_override_vb_section.append("run = CommandList_" + texture_override_vb_namesuffix)
                texture_override_vb_section.new_line()
                
                # 如果出现了VertexLimitRaise，Texcoord槽位需要检测filter_index才能替换
                filterindex_indent_prefix = ""
                if category_name == d3d11GameType.CategoryDrawCategoryDict["Texcoord"]:
                    if cls.vlr_filter_index_indent != "":
                        texture_override_vb_commandlist_section.append("if vb0 == " + str(3000 + cls.global_generate_mod_number))

                # 遍历获取所有在当前分类hash下进行替换的分类，并添加对应的资源替换
                for original_category_name, draw_category_name in d3d11GameType.CategoryDrawCategoryDict.items():
                    if category_name == draw_category_name:
                        if original_category_name == "Position":
                            texture_override_vb_commandlist_section.append("cs-cb0 = Resource_" + draw_ib + "_VertexLimit")
                            texture_override_vb_commandlist_section.append("cs-t0 = Resource" + draw_ib + "Position")
                            texture_override_vb_commandlist_section.append("cs-t1 = Resource" + draw_ib + "Blend")
                            texture_override_vb_commandlist_section.append("handling = skip")

                            dispatch_number = int(math.ceil(draw_ib_model.draw_number / 64)) + 1
                            texture_override_vb_commandlist_section.append("dispatch = " + str(dispatch_number) + ",1,1")
                        elif original_category_name != "Blend":
                            category_original_slot = d3d11GameType.CategoryExtractSlotDict[original_category_name]
                            texture_override_vb_commandlist_section.append(filterindex_indent_prefix  + category_original_slot + " = Resource" + draw_ib + original_category_name)

                # 对应if vb0 == 3000的结束
                if category_name == d3d11GameType.CategoryDrawCategoryDict["Texcoord"]:
                    if cls.vlr_filter_index_indent != "":
                        texture_override_vb_commandlist_section.append("endif")
                
                # 分支架构，如果是Position则需提供激活变量
                if category_name == d3d11GameType.CategoryDrawCategoryDict["Position"]:
                    if draw_ib_model.key_number != 0:
                        texture_override_vb_commandlist_section.append("$active" + str(cls.global_generate_mod_number) + " = 1")

                texture_override_vb_commandlist_section.new_line()
                commandlist_ini_builder.append_section(texture_override_vb_commandlist_section)
            config_ini_builder.append_section(texture_override_vb_section)
            
            
    @classmethod
    def add_unity_cs_texture_override_ib_sections(cls,config_ini_builder:M_IniBuilder,commandlist_ini_builder:M_IniBuilder,draw_ib_model:DrawIBModel):
        texture_override_ib_section = M_IniSection(M_SectionType.TextureOverrideIB)
        draw_ib = draw_ib_model.draw_ib
        d3d11GameType = draw_ib_model.d3d11GameType

        for count_i in range(len(draw_ib_model.part_name_list)):
            match_first_index = draw_ib_model.match_first_index_list[count_i]
            part_name = draw_ib_model.part_name_list[count_i]

            style_part_name = DrawIBHelper.get_style_alias(part_name)
            ib_resource_name = "Resource_" + draw_ib + "_" + style_part_name
            texture_override_ib_namesuffix = "IB_" + draw_ib + "_" + style_part_name
            texture_override_ib_section.append("[TextureOverride_" + texture_override_ib_namesuffix + "]")
            texture_override_ib_section.append("hash = " + draw_ib)
            texture_override_ib_section.append("match_first_index = " + match_first_index)
            texture_override_ib_section.append("checktextureoverride = vb1")

            if cls.vlr_filter_index_indent != "":
                texture_override_ib_section.append("if vb0 == " + str(3000 + cls.global_generate_mod_number))

            texture_override_ib_section.append(cls.vlr_filter_index_indent + "handling = skip")


            # If ib buf is emprt, continue to avoid add ib resource replace.
            ib_buf = draw_ib_model.componentname_ibbuf_dict.get("Component " + part_name,None)
            if ib_buf is None or len(ib_buf) == 0:
                texture_override_ib_section.new_line()
                continue

            # Add texture slot check, hash style texture also need this.
            # 根据用户反馈，默认删掉了，因为其它游戏用不到，ZZZ用的是run = CommandListSkinTexture
            # if not GenerateModConfig.forbid_auto_texture_ini():
            #     texture_override_ib_section.append(cls.vlr_filter_index_indent + "; Add more slot check here to compatible with XXMI if you manually add more slot replace.")
            #     slot_texturereplace_dict = draw_ib_model.PartName_SlotTextureReplaceDict_Dict.get(part_name,None)

            #     # It may not have auto texture
            #     if slot_texturereplace_dict is not None:
            #         for slot in slot_texturereplace_dict.keys():
            #             texture_override_ib_section.append(cls.vlr_filter_index_indent  + "checktextureoverride = " + slot)

            # Add ib replace
            texture_override_ib_section.append(cls.vlr_filter_index_indent + "ib = " + ib_resource_name)

            # Add slot style texture slot replace.
            if not GenerateModConfig.forbid_auto_texture_ini() and not GenerateModConfig.hash_style_auto_texture():
                slot_texturereplace_dict = draw_ib_model.PartName_SlotTextureReplaceDict_Dict.get(part_name,None)
                # It may not have auto texture
                if slot_texturereplace_dict is not None:
                    for slot,texture_replace_obj in slot_texturereplace_dict.items():
                        texture_override_ib_section.append(cls.vlr_filter_index_indent + slot + " = " + texture_replace_obj.resource_name)

            # 如果不使用GPU-Skinning即为Object类型，此时需要在ib下面替换对应槽位
            if not d3d11GameType.GPU_PreSkinning:
                for category_name in d3d11GameType.OrderedCategoryNameList:
                    category_hash = draw_ib_model.category_hash_dict[category_name]
                    category_slot = d3d11GameType.CategoryExtractSlotDict[category_name]

                    for original_category_name, draw_category_name in d3d11GameType.CategoryDrawCategoryDict.items():
                        if original_category_name == draw_category_name:
                            category_original_slot = d3d11GameType.CategoryExtractSlotDict[original_category_name]
                            texture_override_ib_section.append(cls.vlr_filter_index_indent + category_original_slot + " = Resource" + draw_ib + original_category_name)

            # Component DrawIndexed输出
            component_name = "Component " + part_name 
            model_collection_list = draw_ib_model.componentname_modelcollection_list_dict[component_name]

            toggle_type_number = 0
            switch_type_number = 0

            toggle_model_collection_list:list[ModelCollection] = []
            switch_model_collection_list:list[ModelCollection] = []

            for toggle_model_collection in model_collection_list:
                if toggle_model_collection.type == "toggle":
                    toggle_type_number = toggle_type_number + 1
                    toggle_model_collection_list.append(toggle_model_collection)
                elif toggle_model_collection.type == "switch":
                    switch_type_number = switch_type_number + 1
                    switch_model_collection_list.append(toggle_model_collection)

            # Initialize CommandList
            texture_override_ib_commandlist_section = M_IniSection(M_SectionType.CommandList)
            texture_override_ib_commandlist_section.append("[CommandList_" + texture_override_ib_namesuffix + "]")

            # Call CommandList
            texture_override_ib_section.append("run = CommandList_" + texture_override_ib_namesuffix)
            texture_override_ib_section.new_line()

            # 输出按键切换的DrawIndexed
            if toggle_type_number >= 2:
                for toggle_count in range(toggle_type_number):
                    if toggle_count == 0:
                        texture_override_ib_commandlist_section.append(cls.vlr_filter_index_indent + "if $swapkey" + str(cls.global_key_index_logic) + " == " + str(toggle_count))
                    else:
                        texture_override_ib_commandlist_section.append(cls.vlr_filter_index_indent + "else if $swapkey" + str(cls.global_key_index_logic) + " == " + str(toggle_count))

                    toggle_model_collection = toggle_model_collection_list[toggle_count]
                    for obj_name in toggle_model_collection.obj_name_list:
                        m_drawindexed = draw_ib_model.obj_name_drawindexed_dict[obj_name]
                        texture_override_ib_commandlist_section.append(cls.vlr_filter_index_indent + "; " + m_drawindexed.AliasName)
                        texture_override_ib_commandlist_section.append(cls.vlr_filter_index_indent  + m_drawindexed.get_draw_str())

                texture_override_ib_commandlist_section.append("endif")
                texture_override_ib_commandlist_section.new_line()

                cls.global_key_index_logic = cls.global_key_index_logic + 1
            elif toggle_type_number != 0:
                for toggle_model_collection in toggle_model_collection_list:
                    for obj_name in toggle_model_collection.obj_name_list:
                        m_drawindexed = draw_ib_model.obj_name_drawindexed_dict[obj_name]
                        texture_override_ib_commandlist_section.append(cls.vlr_filter_index_indent + "; " + m_drawindexed.AliasName)
                        texture_override_ib_commandlist_section.append(cls.vlr_filter_index_indent + m_drawindexed.get_draw_str())
                        texture_override_ib_commandlist_section.new_line()

            # 输出按键开关的DrawIndexed
            for switch_model_collection in switch_model_collection_list:
                texture_override_ib_commandlist_section.append(cls.vlr_filter_index_indent + "if $swapkey" + str(cls.global_key_index_logic) + "  == 1")
                for obj_name in switch_model_collection.obj_name_list:
                    m_drawindexed = draw_ib_model.obj_name_drawindexed_dict[obj_name]
                    texture_override_ib_commandlist_section.append(cls.vlr_filter_index_indent + "; " + m_drawindexed.AliasName)
                    texture_override_ib_commandlist_section.append(cls.vlr_filter_index_indent  + m_drawindexed.get_draw_str())
                    texture_override_ib_commandlist_section.new_line()
                texture_override_ib_commandlist_section.append(cls.vlr_filter_index_indent + "endif")
                texture_override_ib_commandlist_section.new_line()
                cls.global_key_index_logic = cls.global_key_index_logic + 1
            
            if cls.vlr_filter_index_indent:
                texture_override_ib_commandlist_section.append("endif")
                texture_override_ib_commandlist_section.new_line()

            commandlist_ini_builder.append_section(texture_override_ib_commandlist_section)

        config_ini_builder.append_section(texture_override_ib_section)

    @classmethod
    def add_unity_cs_resource_vb_sections(cls,config_ini_builder:M_IniBuilder,draw_ib_model:DrawIBModel):
        '''
        Add Resource VB Section (UnityCS)
        '''
        resource_vb_section = M_IniSection(M_SectionType.ResourceBuffer)
        for category_name in draw_ib_model.d3d11GameType.OrderedCategoryNameList:
            resource_vb_section.append("[Resource" + draw_ib_model.draw_ib + category_name + "]")

            if draw_ib_model.d3d11GameType.GPU_PreSkinning:
                if category_name == "Position" or category_name == "Blend":
                    resource_vb_section.append("type = ByteAddressBuffer")
                else:
                    resource_vb_section.append("type = Buffer")
            else:
                resource_vb_section.append("type = Buffer")

            if category_name == "Blend" and draw_ib_model.d3d11GameType.PatchBLENDWEIGHTS:
                blend_stride = draw_ib_model.d3d11GameType.ElementNameD3D11ElementDict["BLENDINDICES"].ByteWidth
                resource_vb_section.append("stride = " + str(blend_stride))
            else:
                resource_vb_section.append("stride = " + str(draw_ib_model.d3d11GameType.CategoryStrideDict[category_name]))
            
            resource_vb_section.append("filename = Buffer/" + draw_ib_model.draw_ib + "-" + category_name + ".buf")
            # resource_vb_section.append(";VertexCount: " + str(draw_ib_model.draw_number))
            resource_vb_section.new_line()
        
        '''
        Add Resource IB Section

        We default use R32_UINT because R16_UINT have a very small number limit.
        '''
        for count_i in range(len(draw_ib_model.part_name_list)):
            partname = draw_ib_model.part_name_list[count_i]
            style_partname = DrawIBHelper.get_style_alias(partname)
            ib_resource_name = "Resource_" + draw_ib_model.draw_ib + "_" + style_partname

            
            resource_vb_section.append("[" + ib_resource_name + "]")
            resource_vb_section.append("type = Buffer")
            resource_vb_section.append("format = DXGI_FORMAT_R32_UINT")
            resource_vb_section.append("filename = Buffer/" + draw_ib_model.draw_ib + "-" + style_partname + ".buf")
            resource_vb_section.new_line()
        
        config_ini_builder.append_section(resource_vb_section)
    
    @classmethod
    def add_unity_cs_resource_vertexlimit(cls,commandlist_ini_builder:M_IniBuilder,draw_ib_model:DrawIBModel):
        '''
        此部分由于顶点数变化后会刷新，应该写在CommandList.ini中
        '''
        resource_vertex_limit_section = M_IniSection(M_SectionType.ResourceBuffer)
        resource_vertex_limit_section.append("[Resource_" + draw_ib_model.draw_ib + "_VertexLimit]")
        resource_vertex_limit_section.append("type = Buffer")
        resource_vertex_limit_section.append("format = R32G32B32A32_UINT")
        resource_vertex_limit_section.append("data = " + str(draw_ib_model.draw_number) + " 0 0 0")
        resource_vertex_limit_section.new_line()

        commandlist_ini_builder.append_section(resource_vertex_limit_section)

    @classmethod
    def add_texture_filter_index(cls,ini_builder:M_IniBuilder):
        if not GenerateModConfig.slot_style_texture_add_filter_index():
            return 

        filter_index_count = 0
        for draw_ib, draw_ib_model in cls.drawib_drawibmodel_dict.items():
            for partname,slot_texture_replace_dict in draw_ib_model.PartName_SlotTextureReplaceDict_Dict.items():
                for slot, texture_replace in slot_texture_replace_dict.items():
                    if texture_replace.hash in cls.texture_hash_filter_index_dict:
                        continue
                    else:
                        filter_index = 6000 + filter_index_count
                        filter_index_count = filter_index_count + 1
                        cls.texture_hash_filter_index_dict[texture_replace.hash] = filter_index
        

        texture_filter_index_section = M_IniSection(M_SectionType.TextureOverrideTexture)
        for hash_value, filter_index in cls.texture_hash_filter_index_dict.items():
            texture_filter_index_section.append("[TextureOverride_Texture_" + hash_value + "]")
            texture_filter_index_section.append("hash = " + hash_value)
            texture_filter_index_section.append("filter_index = " + str(filter_index))
            texture_filter_index_section.new_line()

        ini_builder.append_section(texture_filter_index_section)

    @classmethod
    def generate_unity_cs_config_ini(cls):
        '''
        test
        '''
        config_ini_builder = M_IniBuilder()
        resource_ini_builder = M_IniBuilder()
        commandlist_ini_builder = M_IniBuilder()

        if not GenerateModConfig.generate_to_seperate_folder():
            if GenerateModConfig.generate_to_seperate_ini():
                cls.add_namespace_sections_merged(ini_builder=config_ini_builder)
                cls.add_namespace_sections_merged(ini_builder=resource_ini_builder)
                cls.add_namespace_sections_merged(ini_builder=commandlist_ini_builder)


        if GenerateModConfig.slot_style_texture_add_filter_index():
            cls.add_texture_filter_index(ini_builder= config_ini_builder)

        for draw_ib, draw_ib_model in cls.drawib_drawibmodel_dict.items():
            if GenerateModConfig.generate_to_seperate_folder():
                if GenerateModConfig.generate_to_seperate_ini():
                    cls.add_namespace_sections_seperated(ini_builder=config_ini_builder,draw_ib_model=draw_ib_model)
                    cls.add_namespace_sections_seperated(ini_builder=resource_ini_builder,draw_ib_model=draw_ib_model)
                    cls.add_namespace_sections_seperated(ini_builder=commandlist_ini_builder,draw_ib_model=draw_ib_model)

            cls.add_constants_present_sections(ini_builder=config_ini_builder,draw_ib_model=draw_ib_model) 

            if GenerateModConfig.generate_to_seperate_ini():
                cls.add_unity_vs_texture_override_vlr_section(config_ini_builder=config_ini_builder,commandlist_ini_builder=commandlist_ini_builder,draw_ib_model=draw_ib_model) 
                cls.add_unity_cs_texture_override_vb_sections(config_ini_builder=config_ini_builder,commandlist_ini_builder=commandlist_ini_builder,draw_ib_model=draw_ib_model) 
                cls.add_unity_cs_texture_override_ib_sections(config_ini_builder=config_ini_builder,commandlist_ini_builder=commandlist_ini_builder,draw_ib_model=draw_ib_model) 

                # CommandList.ini
                cls.add_unity_cs_resource_vertexlimit(commandlist_ini_builder=commandlist_ini_builder,draw_ib_model=draw_ib_model)
                # Resource.ini
                cls.add_unity_cs_resource_vb_sections(config_ini_builder=resource_ini_builder,draw_ib_model=draw_ib_model)
                cls.add_resource_texture_sections(ini_builder=resource_ini_builder,draw_ib_model=draw_ib_model)
            else:
                cls.add_unity_vs_texture_override_vlr_section(config_ini_builder=config_ini_builder,commandlist_ini_builder=config_ini_builder,draw_ib_model=draw_ib_model) 
                cls.add_unity_cs_texture_override_vb_sections(config_ini_builder=config_ini_builder,commandlist_ini_builder=config_ini_builder,draw_ib_model=draw_ib_model) 
                cls.add_unity_cs_texture_override_ib_sections(config_ini_builder=config_ini_builder,commandlist_ini_builder=config_ini_builder,draw_ib_model=draw_ib_model) 

                # CommandList.ini
                cls.add_unity_cs_resource_vertexlimit(commandlist_ini_builder=config_ini_builder,draw_ib_model=draw_ib_model)
                # Resource.ini
                cls.add_unity_cs_resource_vb_sections(config_ini_builder=config_ini_builder,draw_ib_model=draw_ib_model)
                cls.add_resource_texture_sections(ini_builder=config_ini_builder,draw_ib_model=draw_ib_model)

            cls.move_slot_style_textures(draw_ib_model=draw_ib_model)

            cls.global_generate_mod_number = cls.global_generate_mod_number + 1

            if GenerateModConfig.generate_to_seperate_folder():
                draw_ib_output_folder = MainConfig.path_generate_mod_folder() + draw_ib + "\\"
                if not os.path.exists(draw_ib_output_folder):
                    os.makedirs(draw_ib_output_folder)

                config_ini_builder.save_to_file(draw_ib_output_folder + "Config.ini")
                config_ini_builder.clear()
                if GenerateModConfig.generate_to_seperate_ini():
                    resource_ini_builder.save_to_file(draw_ib_output_folder + "Resource.ini")
                    resource_ini_builder.clear()
                    commandlist_ini_builder.save_to_file(draw_ib_output_folder + "CommandList.ini")
                    commandlist_ini_builder.clear()
                else:
                    if os.path.exists(MainConfig.path_generate_mod_folder() + "Resource.ini"):
                        os.remove(MainConfig.path_generate_mod_folder() + "Resource.ini")
                    if os.path.exists(MainConfig.path_generate_mod_folder() + "CommandList.ini"):
                        os.remove(MainConfig.path_generate_mod_folder() + "CommandList.ini")

        cls.generate_hash_style_texture_ini()

        if not GenerateModConfig.generate_to_seperate_folder():
            config_ini_builder.save_to_file(MainConfig.path_generate_mod_folder() + "Config.ini")
            if GenerateModConfig.generate_to_seperate_ini():
                resource_ini_builder.save_to_file(MainConfig.path_generate_mod_folder() + "Resource.ini")
                commandlist_ini_builder.save_to_file(MainConfig.path_generate_mod_folder() + "CommandList.ini")
            else:
                if os.path.exists(MainConfig.path_generate_mod_folder() + "Resource.ini"):
                    os.remove(MainConfig.path_generate_mod_folder() + "Resource.ini")
                if os.path.exists(MainConfig.path_generate_mod_folder() + "CommandList.ini"):
                    os.remove(MainConfig.path_generate_mod_folder() + "CommandList.ini")

    @classmethod
    def add_namespace_sections_merged(cls,ini_builder:M_IniBuilder):
        '''
        Generate a namespace = xxxxx to let different ini work together.
        combine multiple drawib together use [_]
        for this, we use namespace = [drawib][_][drawib][_]...
        '''
        draw_ib_str = ""
        for draw_ib, draw_ib_model in cls.drawib_drawibmodel_dict.items():
            draw_ib_str = draw_ib_str + draw_ib + "_"

        namespace_section = M_IniSection(M_SectionType.NameSpace)
        namespace_section.append("namespace = " + draw_ib_str)
        namespace_section.new_line()

        ini_builder.append_section(namespace_section)
    
    @classmethod
    def add_namespace_sections_seperated(cls,ini_builder,draw_ib_model:DrawIBModel):
        '''
        Generate a namespace = xxxxx to let different ini work together.
        for this, we use namespace = [drawib]
        '''
        namespace_section = M_IniSection(M_SectionType.NameSpace)
        namespace_section.append("namespace = " + draw_ib_model.draw_ib)
        namespace_section.new_line()

        ini_builder.append_section(namespace_section)

    @classmethod
    def generate_unity_vs_config_ini(cls):
        # TimerUtils.Start("generate_unity_vs_config_ini")
        '''
        Supported Games:
        - Genshin Impact
        - Honkai Impact 3rd
        - Honkai StarRail
        - Zenless Zone Zero
        - Bloody Spell
        - Unity-CPU-PreSkinning (All DX11 Unity games who allow 3Dmigoto inject, mostly used by GF2 now.)
        '''
        config_ini_builder = M_IniBuilder()
        resource_ini_builder = M_IniBuilder()
        commandlist_ini_builder = M_IniBuilder()

        # Add namespace 
        if not GenerateModConfig.generate_to_seperate_folder():
            if GenerateModConfig.generate_to_seperate_ini():
                cls.add_namespace_sections_merged(ini_builder=config_ini_builder)
                cls.add_namespace_sections_merged(ini_builder=resource_ini_builder)
                cls.add_namespace_sections_merged(ini_builder=commandlist_ini_builder)

        if GenerateModConfig.slot_style_texture_add_filter_index():
            cls.add_texture_filter_index(ini_builder= config_ini_builder)

        for draw_ib, draw_ib_model in cls.drawib_drawibmodel_dict.items():

            # Add namespace
            if GenerateModConfig.generate_to_seperate_folder():
                if GenerateModConfig.generate_to_seperate_ini():
                    cls.add_namespace_sections_seperated(ini_builder=config_ini_builder,draw_ib_model=draw_ib_model)
                    cls.add_namespace_sections_seperated(ini_builder=resource_ini_builder,draw_ib_model=draw_ib_model)
                    cls.add_namespace_sections_seperated(ini_builder=commandlist_ini_builder,draw_ib_model=draw_ib_model)

            # add variable, key
            cls.add_constants_present_sections(ini_builder=config_ini_builder,draw_ib_model=draw_ib_model)

            if GenerateModConfig.generate_to_seperate_ini():
                cls.add_unity_vs_texture_override_vlr_section(config_ini_builder=config_ini_builder,commandlist_ini_builder=commandlist_ini_builder,draw_ib_model=draw_ib_model)
                cls.add_unity_vs_texture_override_vb_sections(config_ini_builder=config_ini_builder,commandlist_ini_builder=commandlist_ini_builder,draw_ib_model=draw_ib_model)
                cls.add_unity_vs_texture_override_ib_sections(config_ini_builder=config_ini_builder,commandlist_ini_builder=commandlist_ini_builder,draw_ib_model=draw_ib_model)
                cls.add_unity_vs_resource_vb_sections(ini_builder=resource_ini_builder,draw_ib_model=draw_ib_model)
                cls.add_resource_texture_sections(ini_builder=resource_ini_builder,draw_ib_model=draw_ib_model)
            else:
                cls.add_unity_vs_texture_override_vlr_section(config_ini_builder=config_ini_builder,commandlist_ini_builder=config_ini_builder,draw_ib_model=draw_ib_model)
                cls.add_unity_vs_texture_override_vb_sections(config_ini_builder=config_ini_builder,commandlist_ini_builder=config_ini_builder,draw_ib_model=draw_ib_model)
                cls.add_unity_vs_texture_override_ib_sections(config_ini_builder=config_ini_builder,commandlist_ini_builder=config_ini_builder,draw_ib_model=draw_ib_model)
                cls.add_unity_vs_resource_vb_sections(ini_builder=config_ini_builder,draw_ib_model=draw_ib_model)
                cls.add_resource_texture_sections(ini_builder=config_ini_builder,draw_ib_model=draw_ib_model)

            cls.move_slot_style_textures(draw_ib_model=draw_ib_model)

            cls.global_generate_mod_number = cls.global_generate_mod_number + 1

            if GenerateModConfig.generate_to_seperate_folder():
                draw_ib_output_folder = MainConfig.path_generate_mod_folder() + draw_ib + "\\"
                if not os.path.exists(draw_ib_output_folder):
                    os.makedirs(draw_ib_output_folder)

                config_ini_builder.save_to_file(draw_ib_output_folder + "Config.ini")
                config_ini_builder.clear()
                if GenerateModConfig.generate_to_seperate_ini():
                    resource_ini_builder.save_to_file(draw_ib_output_folder + "Resource.ini")
                    resource_ini_builder.clear()
                    commandlist_ini_builder.save_to_file(draw_ib_output_folder + "CommandList.ini")
                    commandlist_ini_builder.clear()
                else:
                    if os.path.exists(MainConfig.path_generate_mod_folder() + "Resource.ini"):
                        os.remove(MainConfig.path_generate_mod_folder() + "Resource.ini")
                    if os.path.exists(MainConfig.path_generate_mod_folder() + "CommandList.ini"):
                        os.remove(MainConfig.path_generate_mod_folder() + "CommandList.ini")

        cls.generate_hash_style_texture_ini()

        if not GenerateModConfig.generate_to_seperate_folder():
            config_ini_builder.save_to_file(MainConfig.path_generate_mod_folder() + "Config.ini")
            if GenerateModConfig.generate_to_seperate_ini():
                resource_ini_builder.save_to_file(MainConfig.path_generate_mod_folder() + "Resource.ini")
                commandlist_ini_builder.save_to_file(MainConfig.path_generate_mod_folder() + "CommandList.ini")
            else:
                if os.path.exists(MainConfig.path_generate_mod_folder() + "Resource.ini"):
                    os.remove(MainConfig.path_generate_mod_folder() + "Resource.ini")
                if os.path.exists(MainConfig.path_generate_mod_folder() + "CommandList.ini"):
                    os.remove(MainConfig.path_generate_mod_folder() + "CommandList.ini")
        # TimerUtils.End("generate_unity_vs_config_ini")