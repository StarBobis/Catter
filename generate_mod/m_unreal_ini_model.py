import shutil

from .m_ini_builder import *
from .m_drawib_model import *


class M_UnrealIniModel:
    '''
    Unreal Engine VertexShader PreSkinning
    Unreal Engine ComputeShader PreSkinning
    Unreal Engine CPU PreSkinning
    '''
    drawib_drawibmodel_dict:dict[str,DrawIBModel] = {}
    shapekeys = {}

    global_key_index_constants = 0
    global_key_index_logic = 0
    global_generate_mod_number = 0

    vlr_filter_index_indent = ""

    # for texture filter_index function.
    texture_hash_filter_index_dict = {}


    @classmethod
    def initialzie(cls):
        '''
        You have to call this to clean cache data before generate mod.
        '''
        cls.drawib_drawibmodel_dict = {}
        cls.shapekeys = {}
        
        cls.global_key_index_constants = 0
        cls.global_key_index_logic = 0
        cls.global_generate_mod_number = 0

        cls.vlr_filter_index_indent = ""

        cls.texture_hash_filter_index_dict = {}

    # TODO 重复的方法，能抽象为工具类吗？
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
    
    # TODO 重复的方法，能抽象为工具类吗？
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

    # TODO 重复的方法，能抽象为工具类吗？
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

    # TODO 重复的方法，能抽象为工具类吗？
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
    def generate_unreal_vs_config_ini(cls):
        '''
        Supported Games:
        - Wuthering Waves

        '''
        config_ini_builder = M_IniBuilder()
        resource_ini_builder = M_IniBuilder()
        commandlist_ini_builder = M_IniBuilder()

        # Add namespace 
        if not GenerateModConfig.generate_to_seperate_folder():
            cls.add_namespace_sections_merged(ini_builder=config_ini_builder)
            cls.add_namespace_sections_merged(ini_builder=resource_ini_builder)
            cls.add_namespace_sections_merged(ini_builder=commandlist_ini_builder)


        for draw_ib, draw_ib_model in cls.drawib_drawibmodel_dict.items():
            # Add namespace
            if GenerateModConfig.generate_to_seperate_folder():
                cls.add_namespace_sections_seperated(ini_builder=config_ini_builder,draw_ib_model=draw_ib_model)
                cls.add_namespace_sections_seperated(ini_builder=resource_ini_builder,draw_ib_model=draw_ib_model)
                cls.add_namespace_sections_seperated(ini_builder=commandlist_ini_builder,draw_ib_model=draw_ib_model)

            # XXX 在这里添加主要的ini生成逻辑
            
            
            # 移动槽位贴图
            cls.move_slot_style_textures(draw_ib_model=draw_ib_model)

            cls.global_generate_mod_number = cls.global_generate_mod_number + 1

            if GenerateModConfig.generate_to_seperate_folder():
                draw_ib_output_folder = MainConfig.path_generate_mod_folder() + draw_ib + "\\"
                if not os.path.exists(draw_ib_output_folder):
                    os.makedirs(draw_ib_output_folder)
                config_ini_builder.save_to_file(draw_ib_output_folder + "Config.ini")
                config_ini_builder.clear()
                resource_ini_builder.save_to_file(draw_ib_output_folder + "Resource.ini")
                resource_ini_builder.clear()
                commandlist_ini_builder.save_to_file(draw_ib_output_folder + "CommandList.ini")
                commandlist_ini_builder.clear()

        cls.generate_hash_style_texture_ini()

        if not GenerateModConfig.generate_to_seperate_folder():
            config_ini_builder.save_to_file(MainConfig.path_generate_mod_folder() + "Config.ini")
            resource_ini_builder.save_to_file(MainConfig.path_generate_mod_folder() + "Resource.ini")
            commandlist_ini_builder.save_to_file(MainConfig.path_generate_mod_folder() + "CommandList.ini")
        