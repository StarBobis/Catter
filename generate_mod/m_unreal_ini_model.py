import shutil

from .m_ini_builder import *
from .m_drawib_model import *
from .m_ini_helper import M_IniHelper



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
    def add_constants_section(cls,ini_builder:M_IniBuilder,draw_ib_model:DrawIBModel):
        constants_section = M_IniSection(M_SectionType.Constants)
        constants_section.append("global $required_wwmi_version = 0.70")

        # object_guid值为原模型的总的index_count 在metadata.json中有记录
        constants_section.append("global $object_guid = " + str(draw_ib_model.extracted_object.index_count))
        # 导出模型的总顶点数
        constants_section.append("global $mesh_vertex_count = " + str(draw_ib_model.draw_number))

        # TODO 我们还没有记录ShapeKey的顶点数，需要在生成ShapeKey的Buffer的时候记录一下
        constants_section.append("global $shapekey_vertex_count = " )


        ini_builder.append_section(constants_section)
        pass


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
            M_IniHelper.add_namespace_sections_merged(ini_builder=config_ini_builder, drawib_drawibmodel_dict=cls.drawib_drawibmodel_dict)
            M_IniHelper.add_namespace_sections_merged(ini_builder=resource_ini_builder, drawib_drawibmodel_dict=cls.drawib_drawibmodel_dict)
            M_IniHelper.add_namespace_sections_merged(ini_builder=commandlist_ini_builder, drawib_drawibmodel_dict=cls.drawib_drawibmodel_dict)


        for draw_ib, draw_ib_model in cls.drawib_drawibmodel_dict.items():
            # Add namespace
            if GenerateModConfig.generate_to_seperate_folder():
                M_IniHelper.add_namespace_sections_seperated(ini_builder=config_ini_builder,draw_ib_model=draw_ib_model)
                M_IniHelper.add_namespace_sections_seperated(ini_builder=resource_ini_builder,draw_ib_model=draw_ib_model)
                M_IniHelper.add_namespace_sections_seperated(ini_builder=commandlist_ini_builder,draw_ib_model=draw_ib_model)

            # XXX 在这里添加主要的ini生成逻辑
            cls.add_constants_section(ini_builder=config_ini_builder,draw_ib_model=draw_ib_model)
            
            # 移动槽位贴图
            M_IniHelper.move_slot_style_textures(draw_ib_model=draw_ib_model)

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

        M_IniHelper.generate_hash_style_texture_ini(drawib_drawibmodel_dict=cls.drawib_drawibmodel_dict)

        if not GenerateModConfig.generate_to_seperate_folder():
            config_ini_builder.save_to_file(MainConfig.path_generate_mod_folder() + "Config.ini")
            resource_ini_builder.save_to_file(MainConfig.path_generate_mod_folder() + "Resource.ini")
            commandlist_ini_builder.save_to_file(MainConfig.path_generate_mod_folder() + "CommandList.ini")
        