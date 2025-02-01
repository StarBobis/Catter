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
