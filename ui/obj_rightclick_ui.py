from ..utils.shapekey_utils import *
from ..utils.obj_utils import SmoothNormal,ObjUtils
import bmesh
from mathutils import Vector

from bpy.props import BoolProperty,  CollectionProperty

class RemoveAllVertexGroupOperator(bpy.types.Operator):
    bl_idname = "object.remove_all_vertex_group"
    bl_label = "移除所有顶点组"
    bl_description = "移除当前选中obj的所有顶点组"

    def execute(self, context):
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                for x in obj.vertex_groups:
                    obj.vertex_groups.remove(x)

        return {'FINISHED'}

class RemoveUnusedVertexGroupOperator(bpy.types.Operator):
    bl_idname = "object.remove_unused_vertex_group"
    bl_label = "移除未使用的空顶点组"
    bl_description = "移除当前选中obj的所有空顶点组，也就是移除未使用的顶点组"

    def execute(self, context):
        # Originally design from https://blenderartists.org/t/batch-delete-vertex-groups-script/449881/23
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                # obj = bpy.context.active_object
                obj.update_from_editmode()
                vgroup_used = {i: False for i, k in enumerate(obj.vertex_groups)}

                for v in obj.data.vertices:
                    for g in v.groups:
                        if g.weight > 0.0:
                            vgroup_used[g.group] = True

                for i, used in sorted(vgroup_used.items(), reverse=True):
                    if not used:
                        obj.vertex_groups.remove(obj.vertex_groups[i])

        return {'FINISHED'}



class MergeVertexGroupsWithSameNumber(bpy.types.Operator):
    bl_idname = "object.merge_vertex_group_with_same_number"
    bl_label = "合并具有相同数字前缀名称的顶点组"
    bl_description = "把当前选中obj的所有数字前缀名称相同的顶点组进行合并"

    def execute(self, context):
        # Author: SilentNightSound#7430
        # Combines vertex groups with the same prefix into one, a fast alternative to the Vertex Weight Mix that works for multiple groups
        # You will likely want to use blender_fill_vg_gaps.txt after this to fill in any gaps caused by merging groups together
        # Nico: we only need mode 3 here.

        import bpy
        import itertools
        class Fatal(Exception):
            pass

        selected_obj = [obj for obj in bpy.context.selected_objects]
        vgroup_names = []

        ##### USAGE INSTRUCTIONS
        # MODE 1: Runs the merge on a specific list of vertex groups in the selected object(s). Can add more names or fewer to the list - change the names to what you need
        # MODE 2: Runs the merge on a range of vertex groups in the selected object(s). Replace smallest_group_number with the lower bound, and largest_group_number with the upper bound
        # MODE 3 (DEFAULT): Runs the merge on ALL vertex groups in the selected object(s)

        # Select the mode you want to run:
        mode = 3

        # Required data for MODE 1:
        vertex_groups = ["replace_with_first_vertex_group_name", "second_vertex_group_name", "third_name_etc"]

        # Required data for MODE 2:
        smallest_group_number = 000
        largest_group_number = 999

        ######

        if mode == 1:
            vgroup_names = [vertex_groups]
        elif mode == 2:
            vgroup_names = [[f"{i}" for i in range(smallest_group_number, largest_group_number + 1)]]
        elif mode == 3:
            vgroup_names = [[x.name.split(".")[0] for x in y.vertex_groups] for y in selected_obj]
        else:
            raise Fatal("Mode not recognized, exiting")

        if not vgroup_names:
            raise Fatal(
                "No vertex groups found, please double check an object is selected and required data has been entered")

        for cur_obj, cur_vgroup in zip(selected_obj, itertools.cycle(vgroup_names)):
            for vname in cur_vgroup:
                relevant = [x.name for x in cur_obj.vertex_groups if x.name.split(".")[0] == f"{vname}"]

                if relevant:

                    vgroup = cur_obj.vertex_groups.new(name=f"x{vname}")

                    for vert_id, vert in enumerate(cur_obj.data.vertices):
                        available_groups = [v_group_elem.group for v_group_elem in vert.groups]

                        combined = 0
                        for v in relevant:
                            if cur_obj.vertex_groups[v].index in available_groups:
                                combined += cur_obj.vertex_groups[v].weight(vert_id)

                        if combined > 0:
                            vgroup.add([vert_id], combined, 'ADD')

                    for vg in [x for x in cur_obj.vertex_groups if x.name.split(".")[0] == f"{vname}"]:
                        cur_obj.vertex_groups.remove(vg)

                    for vg in cur_obj.vertex_groups:
                        if vg.name[0].lower() == "x":
                            vg.name = vg.name[1:]

            bpy.context.view_layer.objects.active = cur_obj
            bpy.ops.object.vertex_group_sort()
        return {'FINISHED'}


class FillVertexGroupGaps(bpy.types.Operator):
    bl_idname = "object.fill_vertex_group_gaps"
    bl_label = "填充数字顶点组的间隙"
    bl_description = "把当前选中obj的所有数字顶点组的间隙用数字命名的空顶点组填补上，比如有顶点组1,2,5,8则填补后得到1,2,3,4,5,6,7,8"

    def execute(self, context):
        # Author: SilentNightSound#7430
        # Fills in missing vertex groups for a model so there are no gaps, and sorts to make sure everything is in order
        # Works on the currently selected object
        # e.g. if the selected model has groups 0 1 4 5 7 2 it adds an empty group for 3 and 6 and sorts to make it 0 1 2 3 4 5 6 7
        # Very useful to make sure there are no gaps or out-of-order vertex groups

        # Can change this to another number in order to generate missing groups up to that number
        # e.g. setting this to 130 will create 0,1,2...130 even if the active selected object only has 90
        # Otherwise, it will use the largest found group number and generate everything up to that number
        largest = 0

        ob = bpy.context.active_object
        ob.update_from_editmode()

        for vg in ob.vertex_groups:
            try:
                if int(vg.name.split(".")[0]) > largest:
                    largest = int(vg.name.split(".")[0])
            except ValueError:
                print("Vertex group not named as integer, skipping")

        missing = set([f"{i}" for i in range(largest + 1)]) - set([x.name.split(".")[0] for x in ob.vertex_groups])
        for number in missing:
            ob.vertex_groups.new(name=f"{number}")

        bpy.ops.object.vertex_group_sort()
        return {'FINISHED'}


class AddBoneFromVertexGroup(bpy.types.Operator):
    bl_idname = "object.add_bone_from_vertex_group"
    bl_label = "根据顶点组自动生成骨骼"
    bl_description = "把当前选中的obj的每个顶点组都生成一个默认位置的骨骼，方便接下来手动调整骨骼位置和父级关系来绑骨"
    def execute(self, context):
        # 获取当前选中的物体
        selected_object = bpy.context.object

        # 创建骨骼
        bpy.ops.object.armature_add()
        armature_object = bpy.context.object
        armature = armature_object.data

        # 切换到编辑模式
        bpy.ops.object.mode_set(mode='EDIT')

        # 遍历所有的顶点组
        for vertex_group in selected_object.vertex_groups:
            # 获取顶点组的名称
            vertex_group_name = vertex_group.name

            # 创建骨骼
            bone = armature.edit_bones.new(vertex_group_name)

            # 根据顶点组位置生成骨骼
            for vertex in selected_object.data.vertices:
                for group_element in vertex.groups:
                    if group_element.group == vertex_group.index:
                        # 获取顶点位置
                        vertex_position = selected_object.matrix_world @ vertex.co

                        # 设置骨骼位置
                        bone.head = vertex_position
                        bone.tail = Vector(vertex_position) + Vector((0, 0, 0.1))  # 设置骨骼长度

                        # 分配顶点到骨骼
                        bone_vertex_group = selected_object.vertex_groups[vertex_group_name]
                        bone_vertex_group.add([vertex.index], 0, 'ADD')

        # 刷新场景
        bpy.context.view_layer.update()

        # 切换回对象模式
        bpy.ops.object.mode_set(mode='OBJECT')

        # 选择骨骼并绑定物体到骨骼
        # bpy.context.view_layer.objects.active = armature_object  # 激活骨骼
        # bpy.ops.object.select_all(action='DESELECT')  # 取消选择所有
        # selected_object.select_set(True)  # 选择物体
        # bpy.ops.object.parent_set(type='ARMATURE_AUTO')  # 绑定物体到骨骼

        # 刷新场景
        bpy.context.view_layer.update()

        return {'FINISHED'}


class RemoveNotNumberVertexGroup(bpy.types.Operator):
    bl_idname = "object.remove_not_number_vertex_group"
    bl_label = "移除非数字名称的顶点组"
    bl_description = "把当前选中的obj的所有不是纯数字命名的顶点组都移除"

    def execute(self, context):
        for obj in bpy.context.selected_objects:
            for vg in reversed(obj.vertex_groups):
                if vg.name.isdecimal():
                    continue
                # print('Removing vertex group', vg.name)
                obj.vertex_groups.remove(vg)
        return {'FINISHED'}


class ConvertToFragmentOperator(bpy.types.Operator):
    bl_idname = "object.convert_to_fragment"
    bl_label = "转换为一个3Dmigoto碎片用于合并"
    bl_description = "把当前选中的obj删除所有顶点，用于合并到这个空的obj上使你的模型获取此obj的3Dmigoto属性"
    
    def execute(self, context):
        # 获取当前选中的对象
        selected_objects = bpy.context.selected_objects

        # 检查是否选中了一个Mesh对象
        if len(selected_objects) != 1 or selected_objects[0].type != 'MESH':
            raise ValueError("请选中一个Mesh对象")

        # 获取选中的网格对象
        mesh_obj = selected_objects[0]
        mesh = mesh_obj.data

        # 遍历所有面
        selected_face_index = -1
        for i, face in enumerate(mesh.polygons):
            # 检查当前面是否已经是一个三角形
            if len(face.vertices) == 3:
                selected_face_index = i
                break

        if selected_face_index == -1:
            raise ValueError("没有选中的三角形面")

        # 选择指定索引的面
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')

        # 选择指定面的所有顶点
        bpy.context.tool_settings.mesh_select_mode[0] = True
        bpy.context.tool_settings.mesh_select_mode[1] = False
        bpy.context.tool_settings.mesh_select_mode[2] = False

        bpy.ops.object.mode_set(mode='OBJECT')

        # 获取选中面的所有顶点索引
        selected_face = mesh.polygons[selected_face_index]
        selected_vertices = [v for v in selected_face.vertices]

        # 删除非选定面的顶点
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')

        bpy.context.tool_settings.mesh_select_mode[0] = True
        bpy.context.tool_settings.mesh_select_mode[1] = False
        bpy.context.tool_settings.mesh_select_mode[2] = False

        bpy.ops.object.mode_set(mode='OBJECT')

        for vertex in mesh.vertices:
            if vertex.index not in selected_vertices:
                vertex.select = True

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.delete(type='VERT')

        # 切换回对象模式
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # 顶点位置全部归0，这样就不会显示出来了
        for v_index in selected_vertices:
            mesh.vertices[v_index].co = (0, 0, 0)

        # 移除这些顶点的权重数据，这样即使动画中发生了很大的位置偏移，这三个顶点由于没有权重也不会显示。
        for v_index in selected_vertices:
            for group in mesh_obj.vertex_groups:
                try:
                    group.remove([v_index])
                except RuntimeError:
                    # 如果顶点不在该顶点组中，则会抛出异常，我们只需要忽略它
                    pass

        # 更新网格数据
        mesh_obj.data.update()

        return {'FINISHED'}


class MMTDeleteLoose(bpy.types.Operator):
    bl_idname = "object.mmt_delete_loose"
    bl_label = "删除物体的松散点"
    bl_description = "把当前选中的obj的所有松散点都删除"
    
    def execute(self, context):
        ObjUtils.selected_obj_delete_loose()
        return {'FINISHED'}


class MMTResetRotation(bpy.types.Operator):
    bl_idname = "object.mmt_reset_rotation"
    bl_label = "重置x,y,z的旋转角度为0 (UE Model)"
    bl_description = "把当前选中的obj的x,y,z的旋转角度全部归0"
    
    def execute(self, context):
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                # 将旋转角度归零
                obj.rotation_euler[0] = 0.0  # X轴
                obj.rotation_euler[1] = 0.0  # Y轴
                obj.rotation_euler[2] = 0.0  # Z轴

                # 应用旋转变换
                # bpy.context.view_layer.objects.active = obj
                # bpy.ops.object.transform_apply(rotation=True)
        return {'FINISHED'}
        # return mmt_reset_rotation(self, context)



class SplitMeshByCommonVertexGroup(bpy.types.Operator):
    bl_idname = "object.split_mesh_by_common_vertex_group"
    bl_label = "根据相同的顶点组分割物体"
    bl_description = "把当前选中的obj按顶点组进行分割，适用于部分精细刷权重并重新组合模型的场景"
    
    def execute(self, context):
        # Code copied and modified from @Kail_Nethunter, very useful in some special meets.
        # https://blenderartists.org/t/split-a-mesh-by-vertex-groups/438990/11

        for obj in bpy.context.selected_objects:
            origin_name = obj.name
            keys = obj.vertex_groups.keys()
            real_keys = []
            for gr in keys:
                bpy.ops.object.mode_set(mode="EDIT")
                # Set the vertex group as active
                bpy.ops.object.vertex_group_set_active(group=gr)

                # Deselect all verts and select only current VG
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.vertex_group_select()
                # bpy.ops.mesh.select_all(action='INVERT')
                try:
                    bpy.ops.mesh.separate(type="SELECTED")
                    real_keys.append(gr)
                except:
                    pass
            for i in range(1, len(real_keys) + 1):
                bpy.data.objects['{}.{:03d}'.format(origin_name, i)].name = '{}.{}'.format(
                    origin_name, real_keys[i - 1])

        return {'FINISHED'}


class RecalculateTANGENTWithVectorNormalizedNormal(bpy.types.Operator):
    bl_idname = "object.recalculate_tangent_arithmetic_average_normal"
    bl_label = "使用向量相加归一化算法重计算TANGENT"
    bl_description = "近似修复轮廓线算法，可以达到99%的轮廓线相似度，适用于GI,HSR,ZZZ,HI3 2.0之前的老角色" 
    def execute(self, context):
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                if obj.get("3DMigoto:RecalculateTANGENT",False):
                    obj["3DMigoto:RecalculateTANGENT"] = not obj["3DMigoto:RecalculateTANGENT"]
                else:
                    obj["3DMigoto:RecalculateTANGENT"] = True
                self.report({'INFO'},"重计算TANGENT设为:" + str(obj["3DMigoto:RecalculateTANGENT"]))
        return {'FINISHED'}


class RecalculateCOLORWithVectorNormalizedNormal(bpy.types.Operator):
    bl_idname = "object.recalculate_color_arithmetic_average_normal"
    bl_label = "使用算术平均归一化算法重计算COLOR"
    bl_description = "近似修复轮廓线算法，可以达到99%的轮廓线相似度，仅适用于HI3 2.0新角色" 

    def execute(self, context):
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                if obj.get("3DMigoto:RecalculateCOLOR",False):
                    obj["3DMigoto:RecalculateCOLOR"] = not obj["3DMigoto:RecalculateCOLOR"]
                else:
                    obj["3DMigoto:RecalculateCOLOR"] = True
                self.report({'INFO'},"重计算COLOR设为:" + str(obj["3DMigoto:RecalculateCOLOR"]))
        return {'FINISHED'}




class PropertyCollectionModifierItem(bpy.types.PropertyGroup):
    checked: BoolProperty(
        name="", 
        default=False
    ) # type: ignore
bpy.utils.register_class(PropertyCollectionModifierItem)

class WWMI_ApplyModifierForObjectWithShapeKeysOperator(bpy.types.Operator):
    bl_idname = "wwmi_tools.apply_modifier_for_object_with_shape_keys"
    bl_label = "Apply Modifiers For Object With Shape Keys"
    bl_description = "Apply selected modifiers and remove from the stack for object with shape keys (Solves 'Modifier cannot be applied to a mesh with shape keys' error when pushing 'Apply' button in 'Object modifiers'). Sourced by Przemysław Bągard"
 
    def item_list(self, context):
        return [(modifier.name, modifier.name, modifier.name) for modifier in bpy.context.object.modifiers]
    
    my_collection: CollectionProperty(
        type=PropertyCollectionModifierItem
    ) # type: ignore
    
    disable_armatures: BoolProperty(
        name="Don't include armature deformations",
        default=True,
    ) # type: ignore
 
    def execute(self, context):
        ob = bpy.context.object
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = ob
        ob.select_set(True)
        
        selectedModifiers = [o.name for o in self.my_collection if o.checked]
        
        if not selectedModifiers:
            self.report({'ERROR'}, 'No modifier selected!')
            return {'FINISHED'}
        
        success, errorInfo = ShapeKeyUtils.apply_modifiers_for_object_with_shape_keys(context, selectedModifiers, self.disable_armatures)
        
        if not success:
            self.report({'ERROR'}, errorInfo)
        
        return {'FINISHED'}
        
    def draw(self, context):
        if context.object.data.shape_keys and context.object.data.shape_keys.animation_data:
            self.layout.separator()
            self.layout.label(text="Warning:")
            self.layout.label(text="              Object contains animation data")
            self.layout.label(text="              (like drivers, keyframes etc.)")
            self.layout.label(text="              assigned to shape keys.")
            self.layout.label(text="              Those data will be lost!")
            self.layout.separator()
        #self.layout.prop(self, "my_enum")
        box = self.layout.box()
        for prop in self.my_collection:
            box.prop(prop, "checked", text=prop["name"])
        #box.prop(self, "my_collection")
        self.layout.prop(self, "disable_armatures")
 
    def invoke(self, context, event):
        self.my_collection.clear()
        for i in range(len(bpy.context.object.modifiers)):
            item = self.my_collection.add()
            item.name = bpy.context.object.modifiers[i].name
            item.checked = False
        return context.window_manager.invoke_props_dialog(self)
    

class SmoothNormalSaveToUV(bpy.types.Operator):
    bl_idname = "object.smooth_normal_save_to_uv"
    bl_label = "平滑法线存UV(近似)"
    bl_description = "平滑法线存UV算法，可用于修复ZZZ,WuWa的某些UV(只是近似实现60%的效果)" 

    def execute(self, context):
        SmoothNormal.smooth_normal_save_to_uv()
        return {'FINISHED'}
 
 
class CatterRightClickMenu(bpy.types.Menu):
    bl_idname = "VIEW3D_MT_object_3Dmigoto"
    bl_label = "3Dmigoto"
    bl_description = "适用于3Dmigoto Mod制作的常用功能"
    
    def draw(self, context):
        layout = self.layout
        # layout.operator(ConvertToFragmentOperator.bl_idname)
        # layout.separator()
        layout.operator(RemoveUnusedVertexGroupOperator.bl_idname)
        layout.operator(MergeVertexGroupsWithSameNumber.bl_idname)
        layout.operator(FillVertexGroupGaps.bl_idname)
        layout.operator(AddBoneFromVertexGroup.bl_idname)
        layout.operator(RemoveNotNumberVertexGroup.bl_idname)
        layout.operator(RemoveAllVertexGroupOperator.bl_idname)
        layout.operator(MMTDeleteLoose.bl_idname)
        layout.operator(MMTResetRotation.bl_idname)
        layout.operator(SplitMeshByCommonVertexGroup.bl_idname)
        layout.operator(WWMI_ApplyModifierForObjectWithShapeKeysOperator.bl_idname)
        layout.operator(SmoothNormalSaveToUV.bl_idname)
        layout.separator()
        layout.operator(RecalculateTANGENTWithVectorNormalizedNormal.bl_idname)
        layout.operator(RecalculateCOLORWithVectorNormalizedNormal.bl_idname)
        


def menu_func_migoto_right_click(self, context):
    self.layout.separator()
    self.layout.menu(CatterRightClickMenu.bl_idname)


