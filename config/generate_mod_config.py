import bpy

# Simple Class to get attributes.
# easy to use, safe to modifiy.
class GenerateModConfig:
    
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
    
    # every_drawib_single_ib_file
    @classmethod
    def every_drawib_single_ib_file(cls):
        '''
        bpy.context.scene.dbmt_generatemod.every_drawib_single_ib_file
        '''
        return bpy.context.scene.dbmt_generatemod.every_drawib_single_ib_file
    
    # generate_to_seperate_ini
    @classmethod
    def generate_to_seperate_ini(cls):
        '''
        bpy.context.scene.dbmt_generatemod.generate_to_seperate_ini
        '''
        return bpy.context.scene.dbmt_generatemod.generate_to_seperate_ini
    