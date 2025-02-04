import bpy


class ImportModelConfig:

    @classmethod
    def import_flip_scale_x(cls):
        '''
        bpy.context.scene.dbmt.import_flip_scale_x
        '''
        return bpy.context.scene.dbmt.import_flip_scale_x
    


class ImportModelConfigUnreal:
    # import_merged_vgmap
    @classmethod
    def import_merged_vgmap(cls):
        '''
        bpy.context.scene.dbmt_import_config_unreal.import_merged_vgmap
        '''
        return bpy.context.scene.dbmt_import_config_unreal.import_merged_vgmap
    
    