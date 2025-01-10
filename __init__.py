from .ui.panel_ui import * 
from .ui.collection_rightclick_ui import *
from .ui.obj_rightclick_ui import *

from .config.catter_properties import *
from .import_model.migoto_import import *
from .generate_mod.m_export_mod import *

# Compatible with all version start from Blender 3.6 LTS To 4.2LTS To Latest version.
bl_info = {
    "name": "Catter",
    "description": "A blender plugin for game mod with 3Dmigoto.",
    "blender": (3, 6, 0),
    "version": (1, 0, 7, 2),
    "location": "View3D",
    "category": "Generic",
    "tracker_url":"https://github.com/StarBobis/Catter"
}

register_classes = (
    # Global Property Config
    CatterPropertiesImportModel,
    CatterPropertiesGenerateMod,

    # 3Dmigoto Import Model & Generate Mod
    Import3DMigotoRaw,
    DBMTImportAllFromCurrentWorkSpace,
    DBMTExportUnityVSModToWorkSpaceFast,
    DBMTExportUnityVSModToWorkSpaceSeperated,
    DBMTExportUnityCSModToWorkSpaceFast,

    # 右键菜单栏
    RemoveAllVertexGroupOperator,
    RemoveUnusedVertexGroupOperator,
    MergeVertexGroupsWithSameNumber,
    FillVertexGroupGaps,
    AddBoneFromVertexGroup,
    RemoveNotNumberVertexGroup,
    # ConvertToFragmentOperator,
    MMTDeleteLoose,
    MMTResetRotation,
    CatterRightClickMenu,
    SplitMeshByCommonVertexGroup,
    RecalculateTANGENTWithVectorNormalizedNormal,
    RecalculateCOLORWithVectorNormalizedNormal,
    WWMI_ApplyModifierForObjectWithShapeKeysOperator,
    SmoothNormalSaveToUV,
    
    # Collection's right click menu item.
    Catter_MarkCollection_Switch,
    Catter_MarkCollection_Toggle,

    # UI
    CatterConfigUI,
    PanelModelWorkSpaceIO,
    PanelGenerateMod,
    MigotoAttributePanel,
    # DeveloperPanel,

    # Select DBMT Path op
    OBJECT_OT_select_dbmt_folder
)

def register():
    for cls in register_classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.dbmt = bpy.props.PointerProperty(type=CatterPropertiesImportModel)
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