from ..utils.dbmt_utils import *
from ..utils.collection_utils import *
from ..migoto.migoto_export import get_export_ib_vb
from ..migoto.index_buffer import *
from ..migoto.vertex_buffer import *
from ..migoto.input_layout import *
from ..utils.json_utils import *

from dataclasses import dataclass, field
from ..core.common.d3d11_game_type import D3D11Element,D3D11GameType
from ..utils.command_helper import *

# from enum import StrEnum

import bpy
import shutil

from .m_draw_type import *
from .m_ini_builder import *
from .m_drawib_model import *


# 这个代表了整个Mod的导出模型，数据来源为一个命名空间,形态键数据要放到这里才行
class ModModel:
    drawib_drawibmodel_dict:dict[str,DrawIBModel] = {}
    shapekeys = {}


    @classmethod
    def initialzie(cls):
        cls.drawib_drawibmodel_dict = {}
        cls.shapekeys = {}

    @classmethod
    def path_generatemod_buffer_folder(cls,draw_ib:str):
        if GenerateModConfig.generate_to_seperate_folder():
            buffer_path = os.path.join(MainConfig.path_generate_mod_folder(),draw_ib + "\\Buffer\\")
        else:
            buffer_path = os.path.join(MainConfig.path_generate_mod_folder(),"Buffer\\")
        if not os.path.exists(buffer_path):
            os.makedirs(buffer_path)
        return buffer_path
    
    @classmethod
    def path_generatemod_texture_folder(cls,draw_ib:str):
        if GenerateModConfig.generate_to_seperate_folder():
            texture_path = os.path.join(MainConfig.path_generate_mod_folder(),draw_ib + "\\Texture\\")
        else:
            texture_path = os.path.join(MainConfig.path_generate_mod_folder(),"Texture\\")
        if not os.path.exists(texture_path):
            os.makedirs(texture_path)
        return texture_path


    @classmethod
    def get_style_alias(cls,partname:str):
        '''
        把当前PartName转为GIMI风格的命名，因为用户已经习惯了这种命名风格
        具体哪种风格还是要看DBMT里的配置
        '''
        partname_gimi_alias_dict = {
            "1":"Head","2":"Body","3":"Dress","4":"Extra"
            ,"5":"Extra1","6":"Extra2","7":"Extra3","8":"Extra4","9":"Extra5"
            ,"10":"Extra6","11":"Extra7","12":"Extra8"}
        
        return partname_gimi_alias_dict.get(partname,partname)

    @classmethod
    def export_buffer_files(cls):
        # 输出IB和Category Buffer文件
        for draw_ib, draw_ib_model in cls.drawib_drawibmodel_dict.items():
            # 输出各个IB文件
            for partname in draw_ib_model.part_name_list:
                component_name = "Component " + partname
                ib_buf = draw_ib_model.componentname_ibbuf_dict.get(component_name,None)
                if ib_buf is None:
                    print("Export Failed, Can't get ib buf for partname: " + partname)
                else:
                    ib_path = cls.path_generatemod_buffer_folder(draw_ib=draw_ib) + draw_ib + "-" + cls.get_style_alias(partname) + ".buf"
                    with open(ib_path, 'wb') as ibf:
                        for ib_byte_number in ib_buf:
                            ibf.write(ib_byte_number) 
            # 输出各个Category的Buffer到文件
            for category_name, category_buf in draw_ib_model.categoryname_bytelist_dict.items():
                buf_path = cls.path_generatemod_buffer_folder(draw_ib=draw_ib) + draw_ib + "-" + category_name + ".buf"
                buf_bytearray = bytearray(category_buf)
                with open(buf_path, 'wb') as ibf:
                    ibf.write(buf_bytearray)
        
        # 如果shapekey存在的话，输出shapekey (WWMI会用到)
        
    @classmethod
    def get_mod_switch_key(cls,key_index:int):
        key_list = ["x","c","v","b","n","m","j","k","l","o","p","[","]",
                    "x","c","v","b","n","m","j","k","l","o","p","[","]",
                    "x","c","v","b","n","m","j","k","l","o","p","[","]"]
        return key_list[key_index]

    @classmethod
    def generate_unity_vs_config_ini(cls):
        ini_builder = M_IniBuilder()     

        global_key_index_constants = 0
        global_key_index_logic = 0
        generate_mod_number = 0

        for draw_ib, draw_ib_model in cls.drawib_drawibmodel_dict.items():
            d3d11GameType = draw_ib_model.d3d11GameType

            if draw_ib_model.key_number != 0:
                # 声明Constants变量
                constants_section = M_IniSection(M_SectionType.Constants)
                constants_section.append("[Constants]")
                constants_section.append("global $active" + str(generate_mod_number))
                for i in range(draw_ib_model.key_number):
                    key_str = "global persist $swapkey" + str(i + global_key_index_constants) + " = 0"
                    constants_section.append(key_str) 
                constants_section.new_line()

                ini_builder.append_section(constants_section)

                # 声明$active激活变量
                present_section = M_IniSection(M_SectionType.Present)
                present_section.append("[Present]")
                present_section.append("post $active" + str(generate_mod_number) + " = 0")
                present_section.new_line()

                ini_builder.append_section(present_section)

                # 声明按键切换和按键开关的变量
                for component_name, model_collection_list in draw_ib_model.componentname_modelcollection_list_dict:
                    toggle_type_number = 0
                    switch_type_number = 0
                    
                    for toggle_model_collection in model_collection_list:
                        if toggle_model_collection.type == "toggle":
                            toggle_type_number = toggle_type_number + 1
                        elif toggle_model_collection.type == "switch":
                            switch_type_number = switch_type_number + 1

                    if toggle_type_number >= 2:
                        key_section = M_IniSection(M_SectionType.Key)
                        key_section.append("[KeySwap" + str(global_key_index_constants) + "]")
                        key_section.append("condition = $active" + str(generate_mod_number) + " == 1")
                        key_section.append("key = " + cls.get_mod_switch_key(global_key_index_constants))
                        key_section.append("type = cycle")
                        
                        key_cycle_str = ""
                        for i in range(toggle_type_number):
                            if i < toggle_type_number + 1:
                                key_cycle_str = key_cycle_str + str(i) + ","
                            else:
                                key_cycle_str = key_cycle_str + str(i)

                        key_section.append("$swapkey" + str(global_key_index_constants) + " = " + key_cycle_str)
                        key_section.new_line()

                        ini_builder.append_section(key_section)
                        global_key_index_constants = global_key_index_constants + 1
                    
                    if switch_type_number >= 1:
                        for i in range(switch_type_number):
                            key_section = M_IniSection(M_SectionType.Key)
                            key_section.append("[KeySwap" + str(global_key_index_constants) + "]")
                            key_section.append("condition = $active" + str(generate_mod_number) + " == 1")
                            key_section.append("key = " + cls.get_mod_switch_key(global_key_index_constants))
                            key_section.append("type = cycle")
                            key_section.append("$swapkey" + str(global_key_index_constants) + " = 1,0")
                            key_section.new_line()

                            ini_builder.append_section(key_section)
                            global_key_index_constants = global_key_index_constants + 1
            
            vertex_limit_raise_filter_index = cls.add_vertex_limit_raise_section(ini_builder=ini_builder,draw_ib_model=draw_ib_model,generate_mod_number=generate_mod_number)
            
            # 声明TextureOverrideVB部分，只有使用GPU-PreSkinning时是直接替换hash对应槽位
            if d3d11GameType.GPU_PreSkinning:
                texture_override_vb_section = M_IniSection(M_SectionType.TextureOverrideVB)
                texture_override_vb_section.append("; " + draw_ib + " ----------------------------")
                for category_name in d3d11GameType.OrderedCategoryNameList:
                    category_hash = draw_ib_model.category_hash_dict[category_name]
                    category_slot = d3d11GameType.CategoryExtractSlotDict[category_name]
                    texture_override_vb_section.append("[TextureOverride_VB_" + draw_ib + "_" + category_name + "]")
                    texture_override_vb_section.append("hash = " + category_hash)
                    
                    drawtype_indent_prefix = ""
                    if category_name == d3d11GameType.CategoryDrawCategoryDict["Position"]:
                        drawtype_indent_prefix = "  "
                        texture_override_vb_section.append("if DRAW_TYPE == 1")
                    
                    # 如果出现了VertexLimitRaise，Texcoord槽位需要检测filter_index才能替换
                    filterindex_indent_prefix = ""
                    if category_name == d3d11GameType.CategoryDrawCategoryDict["Texcoord"]:
                        if vertex_limit_raise_filter_index:
                            filterindex_indent_prefix = "  "
                            texture_override_vb_section.append("if vb0 == " + str(3000 + generate_mod_number))

                    # 遍历获取所有在当前分类hash下进行替换的分类，并添加对应的资源替换
                    for original_category_name, draw_category_name in d3d11GameType.CategoryDrawCategoryDict.items():
                        if category_name == draw_category_name:
                            category_original_slot = d3d11GameType.CategoryExtractSlotDict[original_category_name]
                            texture_override_vb_section.append(filterindex_indent_prefix + drawtype_indent_prefix + category_original_slot + " = Resource" + draw_ib + original_category_name)

                    # draw一般都是在Blend槽位上进行的，所以我们这里要判断确定是Blend要替换的hash才能进行draw。
                    if category_name == d3d11GameType.CategoryDrawCategoryDict["Blend"]:
                        texture_override_vb_section.append(drawtype_indent_prefix + "handling = skip")
                        texture_override_vb_section.append(drawtype_indent_prefix + "draw = " + str(draw_ib_model.draw_number) + ", 0")

                    # 对应if DRAW_TYPE == 1的结束
                    if category_name == d3d11GameType.CategoryDrawCategoryDict["Position"]:
                        texture_override_vb_section.append("endif")
                    

                    # 对应if vb0 == 3000的结束
                    if category_name == d3d11GameType.CategoryDrawCategoryDict["Texcoord"]:
                        if vertex_limit_raise_filter_index:
                            texture_override_vb_section.append("endif")
                    
                    # 分支架构，如果是Position则需提供激活变量
                    if category_name == d3d11GameType.CategoryDrawCategoryDict["Position"]:
                        if draw_ib_model.key_number != 0:
                            texture_override_vb_section.append("$active" + str(generate_mod_number) + " = 1")

                    texture_override_vb_section.new_line()

                ini_builder.append_section(texture_override_vb_section)


            
            texture_override_ib_section = M_IniSection(M_SectionType.TextureOverrideIB)
            for count_i in range(len(draw_ib_model.part_name_list)):
                match_first_index = draw_ib_model.match_first_index_list[count_i]
                part_name = draw_ib_model.part_name_list[count_i]

                style_part_name = cls.get_style_alias(part_name)
                ib_resource_name = "Resource_" + draw_ib + "_" + style_part_name

                texture_override_ib_section.append("[TextureOverride_IB_" + draw_ib + "_" + style_part_name + "]")
                texture_override_ib_section.append("hash = " + draw_ib)
                texture_override_ib_section.append("match_first_index = " + match_first_index)

                vlr_filterindex_indent = ""
                if vertex_limit_raise_filter_index:
                    vlr_filterindex_indent = "  "
                
                if vertex_limit_raise_filter_index:
                    texture_override_ib_section.append("if vb0 == " + str(3000 + generate_mod_number))

                texture_override_ib_section.append(vlr_filterindex_indent + "handling = skip")

                # Add texture slot check, hash style texture also need this.
                if not GenerateModConfig.forbid_auto_texture_ini():
                    texture_override_ib_section.append(vlr_filterindex_indent + "; Add more slot check here to compatible with XXMI if you manually add more slot replace.")
                    slot_replace_dict = draw_ib_model.PartName_SlotReplaceDict_Dict.get(part_name,None)

                    # It may not have auto texture
                    if slot_replace_dict is not None:
                        for slot,resource_name in slot_replace_dict.items():
                            texture_override_ib_section.append(vlr_filterindex_indent  + "checktextureoverride = " + slot)

                # Add ib replace
                texture_override_ib_section.append(vlr_filterindex_indent + "ib = " + ib_resource_name)

                # Add slot style texture slot replace.
                if not GenerateModConfig.forbid_auto_texture_ini() and not GenerateModConfig.hash_style_auto_texture():
                    slot_replace_dict = draw_ib_model.PartName_SlotReplaceDict_Dict.get(part_name,None)
                    # It may not have auto texture
                    if slot_replace_dict is not None:
                        for slot,resource_name in slot_replace_dict.items():
                            texture_override_ib_section.append(vlr_filterindex_indent + slot + " = " + resource_name)

                # 如果不使用GPU-Skinning即为Object类型，此时需要在ib下面替换对应槽位
                if not d3d11GameType.GPU_PreSkinning:
                    for category_name in d3d11GameType.OrderedCategoryNameList:
                        category_hash = draw_ib_model.category_hash_dict[category_name]
                        category_slot = d3d11GameType.CategoryExtractSlotDict[category_name]

                        for original_category_name, draw_category_name in d3d11GameType.CategoryDrawCategoryDict.items():
                            if original_category_name == draw_category_name:
                                category_original_slot = d3d11GameType.CategoryExtractSlotDict[original_category_name]
                                texture_override_ib_section.append(vlr_filterindex_indent + category_original_slot + " = Resource" + draw_ib + original_category_name)

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

                # 输出按键切换的DrawIndexed
                if toggle_type_number >= 2:
                    for toggle_count in range(toggle_type_number):
                        if toggle_count == 0:
                            texture_override_ib_section.append(vlr_filterindex_indent + "if $swapkey" + str(global_key_index_logic) + " == " + toggle_count)
                        else:
                            texture_override_ib_section.append(vlr_filterindex_indent + "else if $swapkey" + str(global_key_index_logic) + " == " + toggle_count)

                        toggle_model_collection = toggle_model_collection_list[toggle_count]
                        for obj_name in toggle_model_collection.obj_name_list:
                            m_drawindexed = draw_ib_model.obj_name_drawindexed_dict[obj_name]
                            texture_override_ib_section.append(vlr_filterindex_indent + "; " + m_drawindexed.AliasName)
                            texture_override_ib_section.append(vlr_filterindex_indent  + m_drawindexed.get_draw_str())

                    texture_override_ib_section.append("endif")
                    texture_override_ib_section.new_line()

                    global_key_index_logic = global_key_index_logic + 1
                elif toggle_type_number != 0:
                    for toggle_model_collection in toggle_model_collection_list:
                        for obj_name in toggle_model_collection.obj_name_list:
                            m_drawindexed = draw_ib_model.obj_name_drawindexed_dict[obj_name]
                            texture_override_ib_section.append(vlr_filterindex_indent + "; " + m_drawindexed.AliasName)
                            texture_override_ib_section.append(vlr_filterindex_indent + m_drawindexed.get_draw_str())
                            texture_override_ib_section.new_line()

                # 输出按键开关的DrawIndexed
                for switch_model_collection in switch_model_collection_list:
                    texture_override_ib_section.append(vlr_filterindex_indent + "if $swapkey" + str(global_key_index_logic) + "  == 1")
                    for obj_name in switch_model_collection.obj_name_list:
                        m_drawindexed = draw_ib_model.obj_name_drawindexed_dict[obj_name]
                        texture_override_ib_section.append(vlr_filterindex_indent + "; " + m_drawindexed.AliasName)
                        texture_override_ib_section.append(vlr_filterindex_indent  + m_drawindexed.get_draw_str())
                        texture_override_ib_section.new_line()
                    texture_override_ib_section.append(vlr_filterindex_indent + "endif")
                    texture_override_ib_section.new_line()
                    global_key_index_logic = global_key_index_logic + 1
                
                if vlr_filterindex_indent:
                    texture_override_ib_section.append("endif")
                    texture_override_ib_section.new_line()

            ini_builder.append_section(texture_override_ib_section)

            cls.add_resource_vb_sections(ini_builder=ini_builder,draw_ib_model=draw_ib_model)
            cls.add_resource_ib_sections(ini_builder=ini_builder,draw_ib_model=draw_ib_model)
            cls.add_resource_texture_sections(ini_builder=ini_builder,draw_ib_model=draw_ib_model)
            cls.move_slot_style_textures(draw_ib_model=draw_ib_model)
                
            generate_mod_number = generate_mod_number + 1

            if GenerateModConfig.generate_to_seperate_folder():
                draw_ib_output_folder = MainConfig.path_generate_mod_folder() + draw_ib + "\\"
                if not os.path.exists(draw_ib_output_folder):
                    os.makedirs(draw_ib_output_folder)
                ini_builder.save_to_file(draw_ib_output_folder + "Config.ini")
                ini_builder.ini_section_list.clear()
                ini_builder.line_list.clear()
            
        # TODO 添加Hash方式的贴图ini生成方法
        
        cls.generate_hash_style_texture_ini()

        if not GenerateModConfig.generate_to_seperate_folder():
            ini_builder.save_to_file(MainConfig.path_generate_mod_folder() + "Config.ini")
    
    @classmethod
    def add_vertex_limit_raise_section(cls,ini_builder,draw_ib_model:DrawIBModel,generate_mod_number:int) -> bool:
        '''
        Add vertex_limit_raise
        only GPU-PreSkinning need this.
        '''
        d3d11GameType = draw_ib_model.d3d11GameType
        draw_ib = draw_ib_model.draw_ib
        vertex_limit_raise_filter_index = False
        if d3d11GameType.GPU_PreSkinning:
            vertexlimit_section = M_IniSection(M_SectionType.TextureOverrideVB)
            vertexlimit_section.append("[TextureOverride_" + draw_ib + "_VertexLimitRaise]")
            vertexlimit_section.append("hash = " +draw_ib_model.vertex_limit_hash)
            
            # (为啥是3000？因为和WWMI学的，用户可能已经习惯了3000开头，用户体验的优先级最高)
            vertexlimit_section.append("filter_index = " + str(3000 + generate_mod_number))
            vertex_limit_raise_filter_index = True

            vertexlimit_section.append("override_byte_stride = " + str(d3d11GameType.CategoryStrideDict["Position"]))
            vertexlimit_section.append("override_vertex_count = " + str(draw_ib_model.draw_number))
            vertexlimit_section.new_line()

            ini_builder.append_section(vertexlimit_section)
        return vertex_limit_raise_filter_index

    @classmethod
    def add_resource_vb_sections(cls,ini_builder,draw_ib_model):
            '''
            Add Resource VB Section
            '''
            resource_vb_section = M_IniSection(M_SectionType.ResourceVB)
            for category_name in draw_ib_model.d3d11GameType.OrderedCategoryNameList:
                resource_vb_section.append("[Resource" + draw_ib_model.draw_ib + category_name + "]")
                resource_vb_section.append("type = Buffer")

                if category_name == "Blend" and draw_ib_model.d3d11GameType.PatchBLENDWEIGHTS:
                    blend_stride = draw_ib_model.d3d11GameType.ElementNameD3D11ElementDict["BLENDINDICES"].ByteWidth
                    resource_vb_section.append("stride = " + str(blend_stride))
                else:
                    resource_vb_section.append("stride = " + str(draw_ib_model.d3d11GameType.CategoryStrideDict[category_name]))
                
                resource_vb_section.append("filename = Buffer/" + draw_ib_model.draw_ib + "-" + category_name + ".buf")
                resource_vb_section.append(";VertexCount: " + str(draw_ib_model.draw_number))
            
            ini_builder.append_section(resource_vb_section)

    @classmethod
    def add_resource_ib_sections(cls,ini_builder,draw_ib_model):
        '''
        Add Resource IB Section

        We default use R32_UINT because R16_UINT have a very small number limit.
        '''
        for count_i in range(len(draw_ib_model.part_name_list)):
            partname = draw_ib_model.part_name_list[count_i]
            style_partname = cls.get_style_alias(partname)
            ib_resource_name = "Resource_" + draw_ib_model.draw_ib + "_" + style_partname

            resource_ib_section = M_IniSection(M_SectionType.ResourceIB)
            resource_ib_section.append("[" + ib_resource_name + "]")
            resource_ib_section.append("type = Buffer")
            resource_ib_section.append("format = DXGI_FORMAT_R32_UINT")
            resource_ib_section.append("filename = Buffer/" + draw_ib_model.draw_ib + "-" + style_partname + ".buf")
            resource_ib_section.new_line()

            ini_builder.append_section(resource_ib_section)

    @classmethod
    def add_resource_texture_sections(cls,ini_builder,draw_ib_model):
        '''
        add texture resource.
        '''
        if GenerateModConfig.forbid_auto_texture_ini():
            return 
        
        # Hash style won't generate in here
        if GenerateModConfig.hash_style_auto_texture():
            return
        
        for resource_name, texture_filename in draw_ib_model.TextureResource_Name_FileName_Dict.items():
            resource_texture_section = M_IniSection(M_SectionType.ResourceTexture)
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
                target_path = cls.path_generatemod_texture_folder(draw_ib=draw_ib_model.draw_ib) + texture_filename
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

                new_texture_file_name = draw_ib + "_" + texture_hash + "_" + texture_file_name.split("-")[3]
                target_texture_file_path = cls.path_generatemod_texture_folder(draw_ib=draw_ib) + new_texture_file_name
                
                resource_texture_section = M_IniSection(M_SectionType.ResourceTexture)
                resource_texture_section.append("[Resource_Texture_" + texture_hash + "]")
                resource_texture_section.append("filename = Texture/" + new_texture_file_name)
                resource_texture_section.new_line()

                texture_ini_builder.append_section(resource_texture_section)

                texture_override_texture_section = M_IniSection(M_SectionType.TextureOverrideTexture)
                texture_override_texture_section.append("[TextureOverride_" + texture_hash + "]")
                texture_override_texture_section.append("hash = " + texture_hash)
                texture_override_texture_section.append("this = Resource_Texture_" + texture_hash)
                texture_override_texture_section.new_line()

                texture_ini_builder.append_section(texture_override_texture_section)

                # copy only if target not exists avoid overwrite texture manually replaced by mod author.
                if not os.path.exists(target_texture_file_path):
                    shutil.copy2(original_texture_file_path,target_texture_file_path)

        texture_ini_builder.save_to_file(MainConfig.path_generate_mod_folder() + "TextureReplace.ini")



        

class DBMTExportModToWorkSpace(bpy.types.Operator):
    bl_idname = "dbmt.export_mod_to_workspace"
    bl_label = "Export mod in workspace collection to current WorkSpace"
    bl_description = "一键导出当前工作空间集合中的Mod，隐藏显示的模型不会被导出，隐藏的DrawIB为名称的集合不会被导出。"

    def execute(self, context):
        # GlobalTimer.Start("GenerateMod")
        ModModel.initialzie()

        workspace_collection = bpy.context.collection
        for draw_ib_collection in workspace_collection.children:
            # Skip hide collection.
            if not CollectionUtils.is_collection_visible(draw_ib_collection.name):
                continue

            # get drawib
            draw_ib = CollectionUtils.get_clean_collection_name(draw_ib_collection.name)
            if "." in draw_ib:
                self.report({'ERROR'},"当前选中集合中的DrawIB集合名称被意外修改导致无法识别到DrawIB，请不要修改导入时以draw_ib为名称的集合")
                return {'FINISHED'}
        
            # 如果当前集合没有子集合，说明不是一个合格的分支Mod
            if len(draw_ib_collection.children) == 0:
                self.report({'ERROR'},"当前选中集合不是一个标准的分支模型集合，请检查您是否以分支集合方式导入了模型。")
                return {'FINISHED'}
            
            draw_ib_model = DrawIBModel(draw_ib_collection)
            ModModel.drawib_drawibmodel_dict[draw_ib] = draw_ib_model

        # ModModel填充完毕后，开始输出Mod
        ModModel.export_buffer_files()
        ModModel.generate_unity_vs_config_ini()

        self.report({'INFO'},"Generate Mod Success!")

        CommandHelper.OpenGeneratedModFolder()
        # GlobalTimer.End()  经过测试，效率和直接一键导出工作空间集合中的模型基本一样，相差400ms
        return {'FINISHED'}
    
