# 直接导出生成Mod
import bpy

class DBMTExportMergedModVBModel(bpy.types.Operator):
    bl_idname = "dbmt.generate_mod"
    bl_label = "DBMTGenerateMod"
    bl_description = "Directly generate mod files from blender model"

    def execute(self, context):


         return {'FINISHED'}