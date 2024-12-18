import bpy.props

from .ui.panel_ui import * 

from .ui.rightclick_ui import *

from .migoto.migoto_import import *
from .migoto.migoto_export import *
from .migoto.migoto_export_mod import *

from .config.catter_properties import *

# Compatible with all version start from Blender 3.6 LTS To 4.2LTS To Latest version.
bl_info = {
    "name": "Catter",
    "description": "A blender plugin for game mod with 3Dmigoto.",
    "blender": (3, 6, 0),
    "version": (1, 0, 3, 8),
    "location": "View3D",
    "category": "Generic",
    "tracker_url":"https://github.com/StarBobis/Catter"
}


register_classes = (
    # 全局属性
    CatterProperties,
    CatterPropertiesGenerateMod,

    # 3Dmigoto ib和vb格式导入导出
    Import3DMigotoRaw,
    Export3DMigoto,
    # MMT的一键快速导入导出
    # MMTImportAllVbModel,
    # MMTExportAllIBVBModel,
    # 多合一的一键快速导入导出
    # DBMTImportAllVbModelMerged,
    # DBMTExportMergedModVBModel,
    DBMTExportModToWorkSpace,

    DBMTImportAllFromCurrentWorkSpace,
    DBMTExportAllToWorkSpace,

    # 右键菜单栏
    RemoveAllVertexGroupOperator,
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
    WWMI_ApplyModifierForObjectWithShapeKeysOperator,
    
    # Collection's right click menu item.
    Catter_MarkCollection_Switch,
    Catter_MarkCollection_Toggle,

    # UI
    CatterConfigUI,
    # PanelModelExtract,
    PanelModelSingleIO,
    # PanelModelFastIO,
    PanelModelWorkSpaceIO,
    PanelGenerateMod,
    MigotoAttributePanel,

    # Select DBMT Path op
    OBJECT_OT_select_dbmt_folder
)


def register():
    for cls in register_classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.dbmt = bpy.props.PointerProperty(type=CatterProperties)
    bpy.types.Scene.dbmt_generatemod = bpy.props.PointerProperty(type=CatterPropertiesGenerateMod)

    bpy.types.VIEW3D_MT_object_context_menu.append(menu_func_migoto_right_click)
    bpy.types.OUTLINER_MT_collection.append(menu_dbmt_mark_collection_switch)



def unregister():
    for cls in reversed(register_classes):
        bpy.utils.unregister_class(cls)

    bpy.types.VIEW3D_MT_object_context_menu.remove(menu_func_migoto_right_click)
    bpy.types.OUTLINER_MT_collection.remove(menu_dbmt_mark_collection_switch)


if __name__ == "__main__":
    register()