import bpy
import os
import json

from ..utils.migoto_utils import *
from ..utils.dbmt_utils import *
from ..migoto.input_layout import InputLayout

from ..utils.global_config import * 

from ..migoto.migoto_export_mod import *


# 用于选择DBMT所在文件夹，主要是这里能自定义逻辑从而实现保存DBMT路径，这样下次打开就还能读取到。
class OBJECT_OT_select_dbmt_folder(bpy.types.Operator):
    bl_idname = "object.select_dbmt_folder"
    bl_label = "Select DBMT Folder"

    directory: bpy.props.StringProperty(
        subtype='DIR_PATH',
        options={'HIDDEN'},
    ) # type: ignore

    def execute(self, context):
        scene = context.scene
        if self.directory:
            scene.dbmt.path = self.directory
            print(f"Selected folder: {self.directory}")
            # 在这里放置你想要执行的逻辑
            # 比如验证路径是否有效、初始化某些资源等
            DBMTUtils.save_dbmt_path()
            
            self.report({'INFO'}, f"Folder selected: {self.directory}")
        else:
            self.report({'WARNING'}, "No folder selected.")
        
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    

class CatterConfigUI(bpy.types.Panel):
    bl_label = "基础配置"
    bl_idname = "CATTER_PT_CONFIG_UI"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Catter'

    def draw(self, context):
        layout = self.layout
        
        # Path button to choose DBMT-GUI.exe location folder.
        row = layout.row()
        row.operator("object.select_dbmt_folder")

        # 获取DBMT.exe的路径
        dbmt_gui_exe_path = os.path.join(context.scene.dbmt.path, "DBMT.exe")
        if not os.path.exists(dbmt_gui_exe_path):
            layout.label(text="错误:请选择DBMT所在路径 ", icon='ERROR')
        
        row = layout.row()
        MainConfig.read_from_main_json()
        row.label(text="当前游戏: " + MainConfig.gamename)

        draw_seperator(self)

        layout.label(text="翻转NORMAL分量")
        row = layout.row()
       
        row.prop(context.scene.dbmt, "flip_normal_x", text="X")
        row.prop(context.scene.dbmt, "flip_normal_y", text="Y")
        row.prop(context.scene.dbmt, "flip_normal_z", text="Z")
        row.prop(context.scene.dbmt, "flip_normal_w", text="W")

        draw_seperator(self)

        layout.label(text="翻转TANGENT分量")
        row = layout.row()
       
        row.prop(context.scene.dbmt, "flip_tangent_x", text="X")
        row.prop(context.scene.dbmt, "flip_tangent_y", text="Y")
        row.prop(context.scene.dbmt, "flip_tangent_z", text="Z")
        row.prop(context.scene.dbmt, "flip_tangent_w", text="W")

        draw_seperator(self)
        
      
        layout.prop(context.scene.dbmt,"import_merged_vgmap",text="使用重映射的全局顶点组")
        layout.prop(context.scene.dbmt,"model_scale")
        


# class PanelModelSingleIO(bpy.types.Panel):
#     bl_label = "模型手动导入导出" 
#     bl_idname = "VIEW3D_PT_CATTER_ModelImport_panel"
#     bl_space_type = 'VIEW_3D'
#     bl_region_type = 'UI'
#     bl_category = 'Catter'

#     def draw(self, context):
#         layout = self.layout
        
#         operator_import_ib_vb = layout.operator("import_mesh.migoto_raw_buffers_mmt", text="手动导入 .ib & .vb 模型文件")
#         operator_import_ib_vb.filepath = MainConfig.path_workspace_folder()
#         # 手动导出同理，点这个之后默认路径为OutputFolder，这样直接就能去导出不用翻很久文件夹找路径了
#         operator_export_ibvb = layout.operator("export_mesh.migoto_mmt", text="手动导出 .ib & .vb 模型文件")
#         operator_export_ibvb.filepath = MainConfig.path_workspace_folder() + "1.vb"


class PanelModelWorkSpaceIO(bpy.types.Panel):
    bl_label = "Model IO" 
    bl_idname = "VIEW3D_PT_CATTER_WorkSpace_IO_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Catter'

    def draw(self, context):
        layout = self.layout

        row = layout.row()

        MainConfig.read_from_main_json()
        row.label(text="当前工作空间: " + MainConfig.workspacename)

        operator_import_ib_vb = layout.operator("import_mesh.migoto_raw_buffers_mmt", text="手动导入 .ib & .vb 模型文件")
        operator_import_ib_vb.filepath = MainConfig.path_workspace_folder()
        # 手动导出同理，点这个之后默认路径为OutputFolder，这样直接就能去导出不用翻很久文件夹找路径了
        operator_export_ibvb = layout.operator("export_mesh.migoto_mmt", text="手动导出 .ib & .vb 模型文件")
        operator_export_ibvb.filepath = MainConfig.path_workspace_folder() + "1.vb"

        draw_seperator(self)

        layout.operator("dbmt.import_all_from_workspace", text="一键导入当前工作空间内容")
        layout.operator("dbmt.export_all_to_workspace", text="一键导出到当前工作空间")


class PanelGenerateMod(bpy.types.Panel):
    bl_label = "Generate Mod" 
    bl_idname = "VIEW3D_PT_CATTER_GenerateMod_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Catter'

    def draw(self, context):
        layout = self.layout
        # Don't add credit info unless mod author think it must be add.
        # layout.prop(context.scene.dbmt_generatemod, "credit_info_author_name")
        # layout.prop(context.scene.dbmt_generatemod, "credit_info_author_social_link")
        layout.prop(context.scene.dbmt_generatemod, "open_generate_mod_folder_after_run")
        layout.prop(context.scene.dbmt_generatemod, "export_same_number")
        layout.prop(context.scene.dbmt_generatemod, "hash_style_auto_texture")
        layout.prop(context.scene.dbmt_generatemod, "forbid_auto_texture_ini")
        layout.prop(context.scene.dbmt_generatemod, "generate_to_seperate_folder")
        
        if MainConfig.get_game_category() == GameCategory.UnityVS:
            layout.operator("dbmt.export_unity_vs_mod_to_workspace",text="Generate Mod")
        else:
            layout.label(text= MainConfig.get_game_category() + " Not Supported Yet.")


class MigotoAttributePanel(bpy.types.Panel):
    bl_label = "3Dmigoto属性" 
    bl_idname = "VIEW3D_PT_CATTER_MigotoAttribute_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Catter'

    def draw(self, context):
        layout = self.layout
        # 检查是否有选中的对象
        if len(context.selected_objects) > 0:
            # 获取第一个选中的对象
            selected_obj = context.selected_objects[0]
            
            # 显示对象名称
            layout.row().label(text=f"当前Object名称: {selected_obj.name}")
            layout.row().label(text=f"对象Data名称: {selected_obj.data.name}")
            draw_seperator(self)

            # 示例：显示位置信息
            recalculate_tangent = selected_obj.get("3DMigoto:RecalculateTANGENT",None)
            if recalculate_tangent is not None:
                row = layout.row()
                row.label(text=f"导出时重计算TANGENT:" + str(recalculate_tangent))

            recalculate_color = selected_obj.get("3DMigoto:RecalculateCOLOR",None)
            if recalculate_color is not None:
                row = layout.row()
                row.label(text=f"导出时重计算COLOR:" + str(recalculate_color))

            draw_seperator(self)


            gametypename = selected_obj.get("3DMigoto:GameTypeName",None)
            if gametypename is not None:
                row = layout.row()
                row.label(text=f"GameType: " + str(gametypename))

            vblayout = selected_obj.get("3DMigoto:VBLayout",None)
            if vblayout is not None:
                for element_property in vblayout:
                    row = layout.row()
                    semantic_index_suffix = ""
                    if element_property["SemanticIndex"] != 0:
                        semantic_index_suffix = str(element_property["SemanticIndex"])
                    row.label(text=element_property["SemanticName"] + semantic_index_suffix +"        " + element_property["Format"] )

            vbstride = selected_obj.get("3DMigoto:VBStride",None)
            if vbstride is not None:
                row = layout.row()
                row.label(text=f"3DMigoto:VBStride: " + str(vbstride))

            firstvertex = selected_obj.get("3DMigoto:FirstVertex",None)
            if firstvertex is not None:
                row = layout.row()
                row.label(text=f"3DMigoto:FirstVertex: " + str(firstvertex))

            ibformat = selected_obj.get("3DMigoto:IBFormat",None)
            if ibformat is not None:
                row = layout.row()
                row.label(text=f"3DMigoto:IBFormat: " + str(ibformat))

            firstindex = selected_obj.get("3DMigoto:FirstIndex",None)
            if firstindex is not None:
                row = layout.row()
                row.label(text=f"3DMigoto:FirstIndex: " + str(firstindex))
            
        else:
            # 如果没有选中的对象，则显示提示信息
            row = layout.row()
            row.label(text="未选中mesh对象")

