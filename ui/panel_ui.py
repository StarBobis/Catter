import bpy
import os

from ..utils.migoto_utils import *
from ..config.main_config import * 
from ..generate_mod.m_export_mod import *
from ..config.import_model_config import ImportModelConfig

# 用于绘制分割线，由于3.6和4.2行为不一样所以做了包装方法
def draw_seperator(self):
    layout = self.layout

    if bpy.app.version < (4,2,0):
        layout.separator()
    else:
        layout.separator(type="LINE")

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
            MainConfig.save_dbmt_path()
            
            self.report({'INFO'}, f"Folder selected: {self.directory}")
        else:
            self.report({'WARNING'}, "No folder selected.")
        
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
class MigotoAttributePanel(bpy.types.Panel):
    bl_label = "特殊属性面板" 
    bl_idname = "VIEW3D_PT_CATTER_MigotoAttribute_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Catter'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        # 检查是否有选中的对象
        if len(context.selected_objects) > 0:
            # 获取第一个选中的对象
            selected_obj = context.selected_objects[0]
            
            # 显示对象名称
            # layout.row().label(text=f"obj name: {selected_obj.name}")
            # layout.row().label(text=f"mesh name: {selected_obj.data.name}")
            gametypename = selected_obj.get("3DMigoto:GameTypeName",None)
            if gametypename is not None:
                row = layout.row()
                row.label(text=f"GameType: " + str(gametypename))

            # 示例：显示位置信息
            recalculate_tangent = selected_obj.get("3DMigoto:RecalculateTANGENT",None)
            if recalculate_tangent is not None:
                row = layout.row()
                row.label(text=f"Recalculate TANGENT:" + str(recalculate_tangent))

            recalculate_color = selected_obj.get("3DMigoto:RecalculateCOLOR",None)
            if recalculate_color is not None:
                row = layout.row()
                row.label(text=f"Recalculate COLOR:" + str(recalculate_color))

        else:
            # 如果没有选中的对象，则显示提示信息
            row = layout.row()
            row.label(text="当前未选中任何物体")


class PanelModelImportConfig(bpy.types.Panel):
    bl_label = "导入模型配置" 
    bl_idname = "VIEW3D_PT_CATTER_WorkSpace_IO_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Catter'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene.dbmt,"model_scale")
        layout.prop(context.scene.dbmt,"import_flip_scale_x")

        if MainConfig.get_game_category() == GameCategory.UnrealVS or MainConfig.get_game_category() == GameCategory.UnrealCS:
            layout.prop(context.scene.dbmt_import_config_unreal,"import_merged_vgmap")



class PanelGenerateModConfig(bpy.types.Panel):
    bl_label = "生成Mod配置" 
    bl_idname = "VIEW3D_PT_CATTER_GenerateMod_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Catter'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        # 根据当前游戏类型判断哪些应该显示哪些不显示。
        # 因为UnrealVS显然无法支持这里所有的特性，每个游戏只能支持一部分特性。
        if MainConfig.get_game_category() == GameCategory.UnityVS or MainConfig.get_game_category() == GameCategory.UnityCS:
            layout.prop(context.scene.dbmt_generatemod, "export_same_number")
            layout.prop(context.scene.dbmt_generatemod, "forbid_auto_texture_ini")
            layout.prop(context.scene.dbmt_generatemod, "generate_to_seperate_folder")
            layout.prop(context.scene.dbmt_generatemod, "recalculate_tangent")

            # 只有崩坏三2.0可能会用到重计算COLOR值
            if MainConfig.gamename == "HI3":
                layout.prop(context.scene.dbmt_generatemod, "recalculate_color")

            layout.prop(context.scene.dbmt_generatemod, "position_override_filter_draw_type")
            layout.prop(context.scene.dbmt_generatemod, "vertex_limit_raise_add_filter_index")
            layout.prop(context.scene.dbmt_generatemod, "slot_style_texture_add_filter_index")
            # every_drawib_single_ib_file
            layout.prop(context.scene.dbmt_generatemod, "every_drawib_single_ib_file")
            # generate_to_seperate_ini
            layout.prop(context.scene.dbmt_generatemod, "generate_to_seperate_ini")
        elif MainConfig.get_game_category() == GameCategory.UnrealVS or MainConfig.get_game_category() == GameCategory.UnrealCS:
            layout.prop(context.scene.dbmt_generatemod, "forbid_auto_texture_ini")
            



class PanelButtons(bpy.types.Panel):
    bl_label = "Catter" 
    bl_idname = "VIEW3D_PT_CATTER_Buttons_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Catter'
    

    def draw(self, context):
        layout = self.layout


        # use_sepecified_dbmt
        layout.prop(context.scene.dbmt, "use_specified_dbmt")

        if ImportModelConfig.use_specified_dbmt():

            # Path button to choose DBMT-GUI.exe location folder.
            row = layout.row()
            row.operator("object.select_dbmt_folder")

            # 获取DBMT.exe的路径
            dbmt_gui_exe_path = os.path.join(context.scene.dbmt.path, "DBMT.exe")
            if not os.path.exists(dbmt_gui_exe_path):
                layout.label(text="Error:Please select DBMT.exe location ", icon='ERROR')
        
        MainConfig.read_from_main_json()

        layout.label(text="DBMT路径: " + MainConfig.dbmtlocation)
        # print(MainConfig.dbmtlocation)

        layout.label(text="当前游戏: " + MainConfig.gamename)
        layout.label(text="当前工作空间: " + MainConfig.workspacename)

        operator_import_ib_vb = layout.operator("import_mesh.migoto_raw_buffers_mmt")
        operator_import_ib_vb.filepath = MainConfig.path_workspace_folder()

        layout.operator("dbmt.import_all_from_workspace")

        if MainConfig.get_game_category() == GameCategory.UnityVS:
            layout.operator("dbmt.export_unity_vs_mod_to_workspace_seperated")
        elif MainConfig.get_game_category() == GameCategory.UnityCS:
            layout.operator("dbmt.export_unity_cs_mod_to_workspace_seperated")
        elif MainConfig.get_game_category() == GameCategory.UnrealVS:
            layout.operator("dbmt.export_unreal_vs_mod_to_workspace")
        elif MainConfig.get_game_category() == GameCategory.UnrealCS:
            layout.operator("dbmt.export_unreal_cs_mod_to_workspace")
        else:
            layout.label(text= "Generate Mod for " + MainConfig.gamename + " Not Supported Yet.")



