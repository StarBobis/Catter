import bpy
import os

from ..migoto.migoto_utils import *
from ..config.main_config import * 
from ..generate_mod.m_export_mod import *

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
    

class CatterConfigUI(bpy.types.Panel):
    bl_label = "Config"
    bl_idname = "CATTER_PT_CONFIG_UI"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Catter'

    def draw(self, context):
        layout = self.layout
        dbmt_config = context.scene.dbmt
        # Path button to choose DBMT-GUI.exe location folder.
        row = layout.row()
        row.operator("object.select_dbmt_folder")

        # 获取DBMT.exe的路径
        dbmt_gui_exe_path = os.path.join(context.scene.dbmt.path, "DBMT.exe")
        if not os.path.exists(dbmt_gui_exe_path):
            layout.label(text="Error:Please select DBMT.exe location ", icon='ERROR')
        
        row = layout.row()
        MainConfig.read_from_main_json()
        row.label(text="Current Game: " + MainConfig.gamename)

        draw_seperator(self)
      
        layout.prop(dbmt_config,"import_merged_vgmap")
        

class PanelModelWorkSpaceIO(bpy.types.Panel):
    bl_label = "Import Model" 
    bl_idname = "VIEW3D_PT_CATTER_WorkSpace_IO_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Catter'

    def draw(self, context):
        layout = self.layout
        dbmt_config = context.scene.dbmt
        MainConfig.read_from_main_json()
        layout.label(text="Current WorkSpace: " + MainConfig.workspacename)
        layout.prop(dbmt_config,"model_scale")
        #import_flip_coordinate_x 
        layout.prop(dbmt_config,"import_flip_scale_x")
        layout.prop(dbmt_config,"import_delete_loose")
        
        draw_seperator(self)
        operator_import_ib_vb = layout.operator("import_mesh.migoto_raw_buffers_mmt", text="Import .ib.vb.fmt Model Manually")
        operator_import_ib_vb.filepath = MainConfig.path_workspace_folder()

        layout.operator("dbmt.import_all_from_workspace", text="Import All From WorkSpace")


class PanelGenerateMod(bpy.types.Panel):
    bl_label = "Generate Mod" 
    bl_idname = "VIEW3D_PT_CATTER_GenerateMod_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Catter'

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene.dbmt_generatemod, "open_generate_mod_folder_after_run")
        layout.prop(context.scene.dbmt_generatemod, "export_same_number")
        layout.prop(context.scene.dbmt_generatemod, "hash_style_auto_texture")
        layout.prop(context.scene.dbmt_generatemod, "forbid_auto_texture_ini")
        layout.prop(context.scene.dbmt_generatemod, "generate_to_seperate_folder")
        layout.prop(context.scene.dbmt_generatemod, "recalculate_tangent")
        layout.prop(context.scene.dbmt_generatemod, "recalculate_color")
        layout.prop(context.scene.dbmt_generatemod, "position_override_filter_draw_type")
        layout.prop(context.scene.dbmt_generatemod, "vertex_limit_raise_add_filter_index")
        layout.prop(context.scene.dbmt_generatemod, "slot_style_texture_add_filter_index")
        
        if MainConfig.get_game_category() == GameCategory.UnityVS:
            layout.operator("dbmt.export_unity_vs_mod_to_workspace_fast")
        elif MainConfig.get_game_category() == GameCategory.UnityCS:
            layout.operator("dbmt.export_unity_cs_mod_to_workspace_fast")
        else:
            layout.label(text= MainConfig.get_game_category() + " Not Supported Yet.")


class MigotoAttributePanel(bpy.types.Panel):
    bl_label = "Object Properties" 
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
            layout.row().label(text=f"obj name: {selected_obj.name}")
            layout.row().label(text=f"mesh name: {selected_obj.data.name}")
            draw_seperator(self)
            gametypename = selected_obj.get("3DMigoto:GameTypeName",None)
            if gametypename is not None:
                row = layout.row()
                row.label(text=f"GameType: " + str(gametypename))
            draw_seperator(self)

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
            row.label(text="doesn't select any object.")


