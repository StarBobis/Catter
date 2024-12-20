import bpy

from ..utils.command_helper import *
from ..generate_mod.m_mod_model import *
        

class DBMTExportUnityVSModToWorkSpace(bpy.types.Operator):
    bl_idname = "dbmt.export_unity_vs_mod_to_workspace"
    bl_label = "生成二创模型"
    bl_description = "一键导出当前工作空间集合中的Mod，隐藏显示的模型不会被导出，隐藏的DrawIB为名称的集合不会被导出。"

    def execute(self, context):
        # GlobalTimer.Start("GenerateMod")
        M_ModModel.initialzie()

        workspace_collection = bpy.context.collection
        for draw_ib_collection in workspace_collection.children:
            # Skip hide collection.
            if not CollectionUtils.is_collection_visible(draw_ib_collection.name):
                continue

            # get drawib
            draw_ib = CollectionUtils.get_clean_collection_name(draw_ib_collection.name)
            if "." in draw_ib:
                self.report({'ERROR'},"当前选中集合中的DrawIB集合名称被意外修改导致无法识别到DrawIB，请不要修改导入时以draw_ib为名称的集合")
                return {'FINISHED'}
        
            # 如果当前集合没有子集合，说明不是一个合格的分支Mod
            if len(draw_ib_collection.children) == 0:
                self.report({'ERROR'},"当前选中集合不是一个标准的分支模型集合，请检查您是否以分支集合方式导入了模型。")
                return {'FINISHED'}
            
            draw_ib_model = DrawIBModel(draw_ib_collection)
            M_ModModel.drawib_drawibmodel_dict[draw_ib] = draw_ib_model

        # ModModel填充完毕后，开始输出Mod
        M_ModModel.export_buffer_files()
        M_ModModel.generate_unity_vs_config_ini()

        self.report({'INFO'},"Generate Mod Success!")

        CommandHelper.OpenGeneratedModFolder()
        # GlobalTimer.End()  经过测试，效率和直接一键导出工作空间集合中的模型基本一样，相差400ms
        return {'FINISHED'}
    

