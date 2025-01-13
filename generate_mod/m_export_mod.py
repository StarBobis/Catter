import bpy

from ..utils.command_utils import *
from .m_drawib_model import DrawIBModelFast
from .m_unity_ini_model import *
from .m_unreal_ini_model import M_UnrealIniModel


class DBMTExportUnityVSModToWorkSpaceSeperated(bpy.types.Operator):
    bl_idname = "dbmt.export_unity_vs_mod_to_workspace_seperated"
    bl_label = "Generate Mod"
    bl_description = "一键导出当前工作空间集合中的Mod，隐藏显示的模型不会被导出，隐藏的DrawIB为名称的集合不会被导出。"

    def execute(self, context):
        TimerUtils.Start("GenerateMod UnityVS Fast")

        M_UnityIniModelSeperated.initialzie()

        workspace_collection = bpy.context.collection
        for draw_ib_collection in workspace_collection.children:
            # Skip hide collection.
            if not CollectionUtils.is_collection_visible(draw_ib_collection.name):
                continue

            # get drawib
            draw_ib_alias_name = CollectionUtils.get_clean_collection_name(draw_ib_collection.name)
            if "_" not in draw_ib_alias_name:
                self.report({'ERROR'},"当前选中集合中的DrawIB集合名称被意外修改导致无法识别到DrawIB，请不要修改导入时以drawib_aliasname为名称的集合")
                return {'FINISHED'}
        
            # 如果当前集合没有子集合，说明不是一个合格的分支Mod
            if len(draw_ib_collection.children) == 0:
                self.report({'ERROR'},"当前选中集合不是一个标准的分支模型集合，请检查您是否以分支集合方式导入了模型。")
                return {'FINISHED'}

            draw_ib = draw_ib_alias_name.split("_")[0]
            TimerUtils.Start("DrawIB Combine")
            draw_ib_model = DrawIBModelFast(draw_ib_collection,single_ib_file=True)
            M_UnityIniModelSeperated.drawib_drawibmodel_dict[draw_ib] = draw_ib_model
            TimerUtils.End("DrawIB Combine")

        # ModModel填充完毕后，开始输出Mod
        # M_UnityIniModelSeperated.export_buffer_files()
        M_UnityIniModelSeperated.generate_unity_vs_config_ini()

        self.report({'INFO'},"Generate Mod Success!")

        CommandUtils.OpenGeneratedModFolder()

        TimerUtils.End("GenerateMod UnityVS Fast")
        return {'FINISHED'}
    

class DBMTExportUnityCSModToWorkSpaceSeperated(bpy.types.Operator):
    bl_idname = "dbmt.export_unity_cs_mod_to_workspace_seperated"
    bl_label = "Generate Mod"
    bl_description = "一键导出当前工作空间集合中的Mod，隐藏显示的模型不会被导出，隐藏的DrawIB为名称的集合不会被导出。"

    def execute(self, context):
        TimerUtils.Start("GenerateMod UnityCS")

        M_UnityIniModelSeperated.initialzie()

        workspace_collection = bpy.context.collection
        for draw_ib_collection in workspace_collection.children:
            # Skip hide collection.
            if not CollectionUtils.is_collection_visible(draw_ib_collection.name):
                continue

            
            # get drawib
            draw_ib_alias_name = CollectionUtils.get_clean_collection_name(draw_ib_collection.name)
            if "_" not in draw_ib_alias_name:
                self.report({'ERROR'},"当前选中集合中的DrawIB集合名称被意外修改导致无法识别到DrawIB，请不要修改导入时以drawib_aliasname为名称的集合")
                return {'FINISHED'}
        
            # 如果当前集合没有子集合，说明不是一个合格的分支Mod
            if len(draw_ib_collection.children) == 0:
                self.report({'ERROR'},"当前选中集合不是一个标准的分支模型集合，请检查您是否以分支集合方式导入了模型。")
                return {'FINISHED'}

            draw_ib = draw_ib_alias_name.split("_")[0]
            draw_ib_model = DrawIBModelFast(draw_ib_collection,single_ib_file=False)
            M_UnityIniModelSeperated.drawib_drawibmodel_dict[draw_ib] = draw_ib_model

        # ModModel填充完毕后，开始输出Mod
        # M_UnityIniModelSeperated.export_buffer_files()
        M_UnityIniModelSeperated.generate_unity_cs_config_ini()

        self.report({'INFO'},"Generate Mod Success!")

        CommandUtils.OpenGeneratedModFolder()

        TimerUtils.End("GenerateMod UnityCS")
        return {'FINISHED'}
    

class DBMTExportUnrealVSModToWorkSpace(bpy.types.Operator):
    bl_idname = "dbmt.export_unreal_vs_mod_to_workspace"
    bl_label = "Generate Mod"
    bl_description = "一键导出当前工作空间集合中的Mod，隐藏显示的模型不会被导出，隐藏的DrawIB为名称的集合不会被导出。"

    def execute(self, context):
        TimerUtils.Start("GenerateMod UnrealVS")

        M_UnrealIniModel.initialzie()

        workspace_collection = bpy.context.collection
        for draw_ib_collection in workspace_collection.children:
            # Skip hide collection.
            if not CollectionUtils.is_collection_visible(draw_ib_collection.name):
                continue

            # get drawib
            draw_ib_alias_name = CollectionUtils.get_clean_collection_name(draw_ib_collection.name)
            if "_" not in draw_ib_alias_name:
                self.report({'ERROR'},"当前选中集合中的DrawIB集合名称被意外修改导致无法识别到DrawIB，请不要修改导入时以drawib_aliasname为名称的集合")
                return {'FINISHED'}
        
            # 如果当前集合没有子集合，说明不是一个合格的分支Mod
            if len(draw_ib_collection.children) == 0:
                self.report({'ERROR'},"当前选中集合不是一个标准的分支模型集合，请检查您是否以分支集合方式导入了模型。")
                return {'FINISHED'}

            draw_ib = draw_ib_alias_name.split("_")[0]
            draw_ib_model = DrawIBModelFast(draw_ib_collection,single_ib_file=True)
            M_UnrealIniModel.drawib_drawibmodel_dict[draw_ib] = draw_ib_model

        # ModModel填充完毕后，开始输出Mod
        # M_UnrealIniModel.export_buffer_files()
        M_UnrealIniModel.generate_unity_cs_config_ini()

        self.report({'INFO'},"Generate Mod Success!")

        CommandUtils.OpenGeneratedModFolder()

        TimerUtils.End("GenerateMod UnrealVS")
        return {'FINISHED'}


class DBMTExportUnrealCSModToWorkSpace(bpy.types.Operator):
    bl_idname = "dbmt.export_unreal_cs_mod_to_workspace"
    bl_label = "Generate Mod"
    bl_description = "一键导出当前工作空间集合中的Mod，隐藏显示的模型不会被导出，隐藏的DrawIB为名称的集合不会被导出。"

    def execute(self, context):
        TimerUtils.Start("GenerateMod UnrealCS")

        M_UnrealIniModel.initialzie()

        workspace_collection = bpy.context.collection
        for draw_ib_collection in workspace_collection.children:
            # Skip hide collection.
            if not CollectionUtils.is_collection_visible(draw_ib_collection.name):
                continue

            # get drawib
            draw_ib_alias_name = CollectionUtils.get_clean_collection_name(draw_ib_collection.name)
            if "_" not in draw_ib_alias_name:
                self.report({'ERROR'},"当前选中集合中的DrawIB集合名称被意外修改导致无法识别到DrawIB，请不要修改导入时以drawib_aliasname为名称的集合")
                return {'FINISHED'}
        
            # 如果当前集合没有子集合，说明不是一个合格的分支Mod
            if len(draw_ib_collection.children) == 0:
                self.report({'ERROR'},"当前选中集合不是一个标准的分支模型集合，请检查您是否以分支集合方式导入了模型。")
                return {'FINISHED'}

            draw_ib = draw_ib_alias_name.split("_")[0]
            draw_ib_model = DrawIBModelFast(draw_ib_collection,single_ib_file=True)
            M_UnrealIniModel.drawib_drawibmodel_dict[draw_ib] = draw_ib_model

        # ModModel填充完毕后，开始输出Mod
        # M_UnrealIniModel.export_buffer_files()
        M_UnrealIniModel.generate_unity_cs_config_ini()

        self.report({'INFO'},"Generate Mod Success!")

        CommandUtils.OpenGeneratedModFolder()

        TimerUtils.End("GenerateMod UnrealCS")
        return {'FINISHED'}