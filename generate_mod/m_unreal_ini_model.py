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

       
    @classmethod
    def export_buffer_files(cls):
        '''
        Export to buffer files from ib and vb.
        '''
        for draw_ib_model in cls.drawib_drawibmodel_dict.values():
            draw_ib_model.write_category_buffer_files()

    
    @classmethod
    def generate_unreal_vs_config_ini(cls):
        TimerUtils.Start("generate_unreal_vs_config_ini")
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
            cls.add_namespace_sections_merged(ini_builder=config_ini_builder)
            cls.add_namespace_sections_merged(ini_builder=resource_ini_builder)
            cls.add_namespace_sections_merged(ini_builder=commandlist_ini_builder)

        if GenerateModConfig.slot_style_texture_add_filter_index():
            cls.add_texture_filter_index(ini_builder= config_ini_builder)

        for draw_ib, draw_ib_model in cls.drawib_drawibmodel_dict.items():

            # Add namespace
            if GenerateModConfig.generate_to_seperate_folder():
                cls.add_namespace_sections_seperated(ini_builder=config_ini_builder,draw_ib_model=draw_ib_model)
                cls.add_namespace_sections_seperated(ini_builder=resource_ini_builder,draw_ib_model=draw_ib_model)
                cls.add_namespace_sections_seperated(ini_builder=commandlist_ini_builder,draw_ib_model=draw_ib_model)

            # add variable, key
            cls.add_constants_present_sections(ini_builder=config_ini_builder,draw_ib_model=draw_ib_model)

            cls.add_unity_vs_texture_override_vlr_section(config_ini_builder=config_ini_builder,commandlist_ini_builder=commandlist_ini_builder,draw_ib_model=draw_ib_model)
            cls.add_unity_vs_texture_override_vb_sections(config_ini_builder=config_ini_builder,commandlist_ini_builder=commandlist_ini_builder,draw_ib_model=draw_ib_model)
            cls.add_unity_vs_texture_override_ib_sections(config_ini_builder=config_ini_builder,commandlist_ini_builder=commandlist_ini_builder,draw_ib_model=draw_ib_model)

            # 这俩要放入Resource中
            cls.add_unity_vs_resource_vb_sections(ini_builder=resource_ini_builder,draw_ib_model=draw_ib_model)
            cls.add_resource_texture_sections(ini_builder=resource_ini_builder,draw_ib_model=draw_ib_model)

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
        
        TimerUtils.End("generate_unreal_vs_config_ini")