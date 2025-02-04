import bpy

from ..utils.command_utils import *
from .m_drawib_model import DrawIBModel
from .m_unity_ini_model import *
from .m_unreal_ini_model import M_UnrealIniModel


class DBMTExportUnityVSModToWorkSpaceSeperated(bpy.types.Operator):
    bl_idname = "dbmt.export_unity_vs_mod_to_workspace_seperated"
    bl_label = "生成Mod"
    bl_description = "一键导出当前工作空间集合中的Mod，隐藏显示的模型不会被导出，隐藏的DrawIB为名称的集合不会被导出。"

    def execute(self, context):
        TimerUtils.Start("GenerateMod UnityVS Fast")

        M_UnityIniModel.initialzie()

        workspace_collection = bpy.context.collection

        result = CollectionUtils.is_valid_workspace_collection(workspace_collection)
        if result != "":
            self.report({'ERROR'},result)
            return {'FINISHED'}
        
        for draw_ib_collection in workspace_collection.children:
            # Skip hide collection.
            if not CollectionUtils.is_collection_visible(draw_ib_collection.name):
                continue

            # get drawib
            draw_ib_alias_name = CollectionUtils.get_clean_collection_name(draw_ib_collection.name)
            draw_ib = draw_ib_alias_name.split("_")[0]
            draw_ib_model = DrawIBModel(draw_ib_collection,False)
            M_UnityIniModel.drawib_drawibmodel_dict[draw_ib] = draw_ib_model

        # ModModel填充完毕后，开始输出Mod
        M_UnityIniModel.generate_unity_vs_config_ini()

        self.report({'INFO'},"Generate Mod Success!")
        CommandUtils.OpenGeneratedModFolder()

        TimerUtils.End("GenerateMod UnityVS Fast")
        return {'FINISHED'}
    

class DBMTExportUnityCSModToWorkSpaceSeperated(bpy.types.Operator):
    bl_idname = "dbmt.export_unity_cs_mod_to_workspace_seperated"
    bl_label = "生成Mod"
    bl_description = "一键导出当前工作空间集合中的Mod，隐藏显示的模型不会被导出，隐藏的DrawIB为名称的集合不会被导出。"

    def execute(self, context):
        TimerUtils.Start("GenerateMod UnityCS")

        M_UnityIniModel.initialzie()

        workspace_collection = bpy.context.collection

        result = CollectionUtils.is_valid_workspace_collection(workspace_collection)
        if result != "":
            self.report({'ERROR'},result)
            return {'FINISHED'}
        
        for draw_ib_collection in workspace_collection.children:
            # Skip hide collection.
            if not CollectionUtils.is_collection_visible(draw_ib_collection.name):
                continue

            # get drawib
            draw_ib_alias_name = CollectionUtils.get_clean_collection_name(draw_ib_collection.name)
            draw_ib = draw_ib_alias_name.split("_")[0]
            draw_ib_model = DrawIBModel(draw_ib_collection,False)
            M_UnityIniModel.drawib_drawibmodel_dict[draw_ib] = draw_ib_model

        # ModModel填充完毕后，开始输出Mod
        M_UnityIniModel.generate_unity_cs_config_ini()

        self.report({'INFO'},"Generate Mod Success!")

        CommandUtils.OpenGeneratedModFolder()

        TimerUtils.End("GenerateMod UnityCS")
        return {'FINISHED'}
    

class DBMTExportUnrealVSModToWorkSpace(bpy.types.Operator):
    bl_idname = "dbmt.export_unreal_vs_mod_to_workspace"
    bl_label = "生成Mod"
    bl_description = "一键导出当前工作空间集合中的Mod，隐藏显示的模型不会被导出，隐藏的DrawIB为名称的集合不会被导出。"

    def execute(self, context):
        TimerUtils.Start("GenerateMod UnrealVS")

        M_UnrealIniModel.initialzie()

        workspace_collection = bpy.context.collection

        result = CollectionUtils.is_valid_workspace_collection(workspace_collection)
        if result != "":
            self.report({'ERROR'},result)
            return {'FINISHED'}
        
        # TODO 首先在这里进行融合obj为一个整体
        for draw_ib_collection in workspace_collection.children:
            # Skip hide collection.
            if not CollectionUtils.is_collection_visible(draw_ib_collection.name):
                continue

            # get drawib
            draw_ib_alias_name = CollectionUtils.get_clean_collection_name(draw_ib_collection.name)
            draw_ib = draw_ib_alias_name.split("_")[0]
            draw_ib_model = DrawIBModel(draw_ib_collection,True)
            M_UnrealIniModel.drawib_drawibmodel_dict[draw_ib] = draw_ib_model

        # TODO 融合后对这个obj进行生成Mod，涉及较大的架构变更
        

        # ModModel填充完毕后，开始输出Mod
        M_UnrealIniModel.generate_unreal_vs_config_ini()

        self.report({'INFO'},"Generate Mod Success!")

        CommandUtils.OpenGeneratedModFolder()

        TimerUtils.End("GenerateMod UnrealVS")
        return {'FINISHED'}


class DBMTExportUnrealCSModToWorkSpace(bpy.types.Operator):
    bl_idname = "dbmt.export_unreal_cs_mod_to_workspace"
    bl_label = "生成Mod"
    bl_description = "一键导出当前工作空间集合中的Mod，隐藏显示的模型不会被导出，隐藏的DrawIB为名称的集合不会被导出。"

    def execute(self, context):
        TimerUtils.Start("GenerateMod UnrealCS")

        M_UnrealIniModel.initialzie()

        
        workspace_collection = bpy.context.collection

        result = CollectionUtils.is_valid_workspace_collection(workspace_collection)
        if result != "":
            self.report({'ERROR'},result)
            return {'FINISHED'}
        
        for draw_ib_collection in workspace_collection.children:
            # Skip hide collection.
            if not CollectionUtils.is_collection_visible(draw_ib_collection.name):
                continue

            # get drawib
            draw_ib_alias_name = CollectionUtils.get_clean_collection_name(draw_ib_collection.name)
            draw_ib = draw_ib_alias_name.split("_")[0]
            draw_ib_model = DrawIBModel(draw_ib_collection,True)
            M_UnrealIniModel.drawib_drawibmodel_dict[draw_ib] = draw_ib_model

        # ModModel填充完毕后，开始输出Mod
        M_UnrealIniModel.generate_unreal_vs_config_ini()

        self.report({'INFO'},"Generate Mod Success!")

        CommandUtils.OpenGeneratedModFolder()

        TimerUtils.End("GenerateMod UnrealCS")
        return {'FINISHED'}