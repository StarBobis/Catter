import bpy

def get_current_workspace_name()->str:
    return bpy.context.scene.dbmt.workspace_namelist

def get_mmt_path()->str:
    return bpy.context.scene.dbmt.path