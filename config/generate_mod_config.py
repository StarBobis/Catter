import bpy

# 生成Mod时的配置类，通过易懂的方法名获取一大长串难记的Blender属性值
# 这样开发的时候方便了反正
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
    