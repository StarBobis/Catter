import bpy

# Simple Class to get attributes.
# easy to use, safe to modifiy.
# TODO 使用@property装饰器，将这些方法转换为属性，方便调用，而不是每次调用都得加()
class GenerateModConfig:

    @classmethod
    def open_generated_mod_folder_after_run(cls):
        '''
        bpy.context.scene.dbmt_generatemod.open_generate_mod_folder_after_run
        '''
        return bpy.context.scene.dbmt_generatemod.open_generate_mod_folder_after_run
    
    @classmethod
    def hash_style_auto_texture(cls):
        '''
        bpy.context.scene.dbmt_generatemod.hash_style_auto_texture
        '''
        return bpy.context.scene.dbmt_generatemod.hash_style_auto_texture
    
    
    @classmethod
    def forbid_auto_texture_ini(cls):
        '''
        bpy.context.scene.dbmt_generatemod.forbid_auto_texture_ini
        '''
        return bpy.context.scene.dbmt_generatemod.forbid_auto_texture_ini
    
    @classmethod
    def generate_to_seperate_folder(cls):
        '''
        bpy.context.scene.dbmt_generatemod.generate_to_seperate_folder
        '''
        return bpy.context.scene.dbmt_generatemod.generate_to_seperate_folder
    
    @classmethod
    def author_name(cls):
        '''
        bpy.context.scene.dbmt_generatemod.credit_info_author_name
        '''
        return bpy.context.scene.dbmt_generatemod.credit_info_author_name
    
    @classmethod
    def author_link(cls):
        '''
        bpy.context.scene.dbmt_generatemod.credit_info_author_social_link
        '''
        return bpy.context.scene.dbmt_generatemod.credit_info_author_social_link
    
    @classmethod
    def export_same_number(cls):
        '''
        bpy.context.scene.dbmt_generatemod.export_same_number
        '''
        return bpy.context.scene.dbmt_generatemod.export_same_number
    
    @classmethod
    def recalculate_tangent(cls):
        '''
        bpy.context.scene.dbmt_generatemod.recalculate_tangent
        '''
        return bpy.context.scene.dbmt_generatemod.recalculate_tangent
    
    @classmethod
    def recalculate_color(cls):
        '''
        bpy.context.scene.dbmt_generatemod.recalculate_color
        '''
        return bpy.context.scene.dbmt_generatemod.recalculate_color
    

    @classmethod
    def position_override_filter_draw_type(cls):
        '''
        bpy.context.scene.dbmt_generatemod.position_override_filter_draw_type
        '''
        return bpy.context.scene.dbmt_generatemod.position_override_filter_draw_type
    
    @classmethod
    def vertex_limit_raise_add_filter_index(cls):
        '''
        bpy.context.scene.dbmt_generatemod.vertex_limit_raise_add_filter_index
        '''
        return bpy.context.scene.dbmt_generatemod.vertex_limit_raise_add_filter_index


    @classmethod
    def slot_style_texture_add_filter_index(cls):
        '''
        bpy.context.scene.dbmt_generatemod.slot_style_texture_add_filter_index
        '''
        return bpy.context.scene.dbmt_generatemod.slot_style_texture_add_filter_index
    

    # @classmethod
    # def fast_color_rgb_r(cls):
    #     '''
    #     bpy.context.scene.dbmt_generatemod.fast_color_rgb_r
    #     '''
    #     return bpy.context.scene.dbmt_generatemod.fast_color_rgb_r
    
    # @classmethod
    # def fast_color_rgb_g(cls):
    #     '''
    #     bpy.context.scene.dbmt_generatemod.fast_color_rgb_g
    #     '''
    #     return bpy.context.scene.dbmt_generatemod.fast_color_rgb_g
    
    # @classmethod
    # def fast_color_rgb_b(cls):
    #     '''
    #     bpy.context.scene.dbmt_generatemod.fast_color_rgb_b
    #     '''
    #     return bpy.context.scene.dbmt_generatemod.fast_color_rgb_b
    
    # @classmethod
    # def fast_color_rgb_a(cls):
    #     '''
    #     bpy.context.scene.dbmt_generatemod.fast_color_rgb_a
    #     '''
    #     return bpy.context.scene.dbmt_generatemod.fast_color_rgb_a
    
    # @classmethod
    # def use_fast_color_rgba(cls):
    #     '''
    #     bpy.context.scene.dbmt_generatemod.use_fast_color_rgba
    #     '''
    #     return bpy.context.scene.dbmt_generatemod.use_fast_color_rgba