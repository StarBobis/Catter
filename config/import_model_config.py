import bpy

# Simple Class to get attributes.
# easy to use, safe to modifiy.
class ImportModelConfig:

    @classmethod
    def import_flip_scale_x(cls):
        '''
        bpy.context.scene.dbmt.import_flip_scale_x
        '''
        return bpy.context.scene.dbmt.import_flip_scale_x
    
    # import_merged_vgmap
    @classmethod
    def import_merged_vgmap(cls):
        '''
        bpy.context.scene.dbmt.import_merged_vgmap
        '''
        return bpy.context.scene.dbmt.import_merged_vgmap
