import bpy.props

from .ui.panel_ui import * 

from .ui.rightclick_ui import *

from .migoto.migoto_import import *
from .migoto.migoto_export import *


bl_info = {
    "name": "Catter",
    "description": "A blender plugin for game mod with 3Dmigoto.",
    "blender": (4, 2, 3),
    "version": (1, 0, 2, 3),
    "location": "View3D",
    "category": "Generic",
    "tracker_url":"https://github.com/StarBobis/Catter"
}


class CatterProperties(bpy.types.PropertyGroup):
    path: bpy.props.StringProperty(
        name="主路径",
        description="选择DBMT的主路径",
        default=load_dbmt_path(),
        subtype='DIR_PATH'
    ) # type: ignore

    generate_mod_after_export: bpy.props.BoolProperty(
        name="",
        description="",
        default=False
    ) # type: ignore

    export_same_number: bpy.props.BoolProperty(
        name="",
        description="",
        default=False
    ) # type: ignore

    flip_tangent_w:bpy.props.BoolProperty(
        name="",
        description="",
        default=False
    ) # type: ignore

    flip_tangent_z:bpy.props.BoolProperty(
        name="",
        description="",
        default=False
    ) # type: ignore

    flip_tangent_y:bpy.props.BoolProperty(
        name="",
        description="",
        default=False
    ) # type: ignore

    flip_tangent_x:bpy.props.BoolProperty(
        name="",
        description="",
        default=False
    ) # type: ignore

    flip_normal_w:bpy.props.BoolProperty(
        name="",
        description="",
        default=False
    ) # type: ignore

    flip_normal_z:bpy.props.BoolProperty(
        name="",
        description="",
        default=False
    ) # type: ignore

    flip_normal_y:bpy.props.BoolProperty(
        name="",
        description="",
        default=False
    ) # type: ignore

    flip_normal_x:bpy.props.BoolProperty(
        name="",
        description="",
        default=False
    ) # type: ignore

    def __init__(self) -> None:
        super().__init__()
        # self.subtype = 'DIR_PATH'


register_classes = (
    # 全局属性
    CatterProperties,

    # 3Dmigoto ib和vb格式导入导出
    Import3DMigotoRaw,
    Export3DMigoto,
    # MMT的一键快速导入导出
    MMTImportAllVbModel,
    MMTExportAllIBVBModel,
    # 多合一的一键快速导入导出
    DBMTImportAllVbModelMerged,
    DBMTExportMergedModVBModel,

    # 右键菜单栏
    RemoveUnusedVertexGroupOperator,
    MergeVertexGroupsWithSameNumber,
    FillVertexGroupGaps,
    AddBoneFromVertexGroup,
    RemoveNotNumberVertexGroup,
    ConvertToFragmentOperator,
    MMTDeleteLoose,
    MMTResetRotation,
    CatterRightClickMenu,
    SplitMeshByCommonVertexGroup,
    RecalculateTANGENTWithVectorNormalizedNormal,
    RecalculateCOLORWithVectorNormalizedNormal,
    # Collection's right click menu item.
    Catter_MarkCollection_Switch,
    Catter_MarkCollection_Toggle,

    # UI
    CatterConfigUI,
    MigotoIOPanel,
)


def register():
    for cls in register_classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.dbmt = bpy.props.PointerProperty(type=CatterProperties)

    bpy.types.VIEW3D_MT_object_context_menu.append(menu_func_migoto_right_click)
    bpy.types.OUTLINER_MT_collection.append(menu_dbmt_mark_collection_switch)


    bpy.types.Scene.mmt_mmd_animation_mod_start_frame = bpy.props.IntProperty(name="Start Frame")
    bpy.types.Scene.mmt_mmd_animation_mod_end_frame = bpy.props.IntProperty(name="End Frame")
    bpy.types.Scene.mmt_mmd_animation_mod_play_speed = bpy.props.FloatProperty(name="Play Speed")


def unregister():
    for cls in reversed(register_classes):
        bpy.utils.unregister_class(cls)

    bpy.types.VIEW3D_MT_object_context_menu.remove(menu_func_migoto_right_click)
    bpy.types.OUTLINER_MT_collection.remove(menu_dbmt_mark_collection_switch)


if __name__ == "__main__":
    register()