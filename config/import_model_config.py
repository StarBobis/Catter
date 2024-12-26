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
    
    @classmethod
    def import_delete_loose(cls):
        '''
        bpy.context.scene.dbmt.import_delete_loose
        '''
        return bpy.context.scene.dbmt.import_delete_loose
    
