import bpy


class Catter_MarkCollection_Switch(bpy.types.Operator):
    bl_idname = "object.mark_collection_switch"
    bl_label = "分支:标记为按键切换类型"
    bl_description = "把当前选中集合标记为按键切换分支集合"

    def execute(self, context):
        if context.collection:
            context.collection.color_tag = "COLOR_04"
        return {'FINISHED'}


class Catter_MarkCollection_Toggle(bpy.types.Operator):
    bl_idname = "object.mark_collection_toggle"
    bl_label = "分支:标记为按键开关类型"
    bl_description = "把当前选中集合标记为按键开关分支集合"

    def execute(self, context):
        if context.collection:
            context.collection.color_tag = "COLOR_03"
        return {'FINISHED'}


def menu_dbmt_mark_collection_switch(self, context):
    self.layout.separator()
    self.layout.operator(Catter_MarkCollection_Toggle.bl_idname)
    self.layout.operator(Catter_MarkCollection_Switch.bl_idname)