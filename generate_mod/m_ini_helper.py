import os
import shutil

from .m_ini_builder import *
from ..utils.json_utils import JsonUtils
from ..config.main_config import MainConfig, GenerateModConfig
from .m_drawib_model import DrawIBModel


class M_IniHelper:
    '''
    This is a ini generate helper class to reuse functions.
    '''
    key_list = ["x","c","v","b","n","m","j","k","l","o","p","[","]",
                "x","c","v","b","n","m","j","k","l","o","p","[","]",
                "x","c","v","b","n","m","j","k","l","o","p","[","]"]

    @classmethod
    def get_mod_switch_key(cls,key_index:int):
        '''
        Default mod switch/toggle key.
        '''
        
        # 尝试读取Setting.json里的设置，解析错误就还使用默认的
        try:
            setting_json_dict = JsonUtils.LoadFromFile(MainConfig.path_setting_json())
            print(setting_json_dict)
            mod_switch_key = str(setting_json_dict["ModSwitchKey"])
            mod_switch_key_list = mod_switch_key.split(",")
            print(mod_switch_key_list)
            switch_key_list:list[str] = []
            for switch_key_str in mod_switch_key_list:
                switch_key_list.append(switch_key_str[1:-1])
            cls.key_list = switch_key_list
        except Exception:
            print("解析自定义SwitchKey失败")

        return cls.key_list[key_index]
    

    @classmethod
    def add_namespace_sections_merged(cls,ini_builder:M_IniBuilder,drawib_drawibmodel_dict:dict[str,DrawIBModel]):
        '''
        Generate a namespace = xxxxx to let different ini work together.
        combine multiple drawib together use [_]
        for this, we use namespace = [drawib][_][drawib][_]...
        '''
        draw_ib_str = ""
        for draw_ib, draw_ib_model in drawib_drawibmodel_dict.items():
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
        这里是分开生成到不同的draw_ib文件夹中时使用的
        '''
        namespace_section = M_IniSection(M_SectionType.NameSpace)
        namespace_section.append("namespace = " + draw_ib_model.draw_ib)
        namespace_section.new_line()

        ini_builder.append_section(namespace_section)


    @classmethod
    def add_switchkey_constants_section(cls,ini_builder,draw_ib_model:DrawIBModel,global_generate_mod_number,global_key_index_constants):
        '''
        声明SwitchKey的Constants变量
        '''
        if draw_ib_model.key_number != 0:
            constants_section = M_IniSection(M_SectionType.Constants)
            constants_section.append("global $active" + str(global_generate_mod_number))
            for i in range(draw_ib_model.key_number):
                key_str = "global persist $swapkey" + str(i + global_key_index_constants) + " = 0"
                constants_section.append(key_str) 

            ini_builder.append_section(constants_section)
    
    @classmethod
    def add_switchkey_present_section(cls,ini_builder,draw_ib_model:DrawIBModel,global_generate_mod_number):
        '''
        声明$active激活变量
        '''
        if draw_ib_model.key_number != 0:
            present_section = M_IniSection(M_SectionType.Present)
            present_section.append("post $active" + str(global_generate_mod_number) + " = 0")
            ini_builder.append_section(present_section)

    @classmethod
    def add_switchkey_sections(cls,ini_builder,draw_ib_model:DrawIBModel,global_generate_mod_number,input_global_key_index_constants):
        '''
        声明按键切换和按键开关的变量 Key Section
        '''
        if draw_ib_model.key_number != 0:
            # 
            global_key_index_constants = input_global_key_index_constants
            for model_collection_list in draw_ib_model.componentname_modelcollection_list_dict.values():
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

                    if draw_ib_model.d3d11GameType.GPU_PreSkinning:
                        key_section.append("condition = $active" + str(global_generate_mod_number) + " == 1")
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
                        if draw_ib_model.d3d11GameType.GPU_PreSkinning:
                            key_section.append("condition = $active" + str(global_generate_mod_number) + " == 1")
                        key_section.append("key = " + cls.get_mod_switch_key(global_key_index_constants))
                        key_section.append("type = cycle")
                        key_section.append("$swapkey" + str(global_key_index_constants) + " = 1,0")
                        key_section.new_line()

                        ini_builder.append_section(key_section)
                        global_key_index_constants = global_key_index_constants + 1
            
            # 返回，因为修改后要赋值给全局的
            return global_key_index_constants
        else:
            # 如果没有任何按键则直接返回原始数量
            return input_global_key_index_constants
        
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
    def generate_hash_style_texture_ini(cls,drawib_drawibmodel_dict:dict[str,DrawIBModel]):
        '''
        Generate Hash style TextureReplace.ini
        '''
        if GenerateModConfig.forbid_auto_texture_ini():
            return
        
        if not GenerateModConfig.hash_style_auto_texture():
            return 
        
        texture_ini_builder = M_IniBuilder()
        hash_texture_filename_dict:dict[str,str] = {}

        for draw_ib_model in drawib_drawibmodel_dict.values():
            for texture_file_name in draw_ib_model.TextureResource_Name_FileName_Dict.values():
                texture_hash = texture_file_name.split("-")[1]
                hash_texture_filename_dict[texture_hash] = texture_file_name
        
        if len(hash_texture_filename_dict) == 0:
            return
        
        for draw_ib,draw_ib_model in drawib_drawibmodel_dict.items():
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
