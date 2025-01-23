# XXX 所有的属性都必须放到这个catter_properties.py中，方便统一管理

import bpy
from bpy.props import FloatProperty, IntProperty


class CatterPropertiesImportModel(bpy.types.PropertyGroup):
    # ------------------------------------------------------------------------------------------------------------
    model_scale: FloatProperty(
        name="Import Model Scale",
        description="默认为1.0",
        default=1.0,
    ) # type: ignore

    import_merged_vgmap:bpy.props.BoolProperty(
        name="Use Remapped VGS (UnrealVS)",
        description="导入时是否导入融合后的顶点组 (Unreal的合并顶点组技术会用到)",
        default=False
    ) # type: ignore

    import_flip_scale_x :bpy.props.BoolProperty(
        name="Set Scale's X to -1 to avoid mirror",
        description="勾选后在导入模型时把缩放的X分量乘以-1，实现镜像效果，还原游戏中原本的样子，解决导入后镜像对调的问题",
        default=False
    ) # type: ignore

    import_delete_loose :bpy.props.BoolProperty(
        name="Delete Loose Vertices",
        description="勾选后在导入模型时会把松散点删除，进入编辑模式就不会看见松散的没用的点影响Mod制作了，由于很常用所以默认是勾选的。",
        default=True
    ) # type: ignore


class CatterPropertiesGenerateMod(bpy.types.PropertyGroup):
    open_generate_mod_folder_after_run: bpy.props.BoolProperty(
        name="Auto Open GeneratedMod Folder",
        description="生成Mod后打开生成的Mod文件夹",
        default=False
    ) # type: ignore

    hash_style_auto_texture: bpy.props.BoolProperty(
        name="Use Hash Style Auto Texture",
        description="在生成Mod时使用Hash风格的自动贴图而不是槽位风格的",
        default=False
    ) # type: ignore

    forbid_auto_texture_ini: bpy.props.BoolProperty(
        name="Forbid Auto Texture Ini",
        description="生成Mod时禁止生成贴图相关ini部分",
        default=False
    ) # type: ignore

    generate_to_seperate_folder: bpy.props.BoolProperty(
        name="Generate To Seperate DrawIB Folder",
        description="生成Mod时按DrawIB为文件夹名称分开生成而不是全生成到一起，方便进阶制作。",
        default=False
    ) # type: ignore

    export_same_number: bpy.props.BoolProperty(
        name="Stay Vertex Number Same",
        description="使用共享的TANGENT值从而避免hashable计算导致的顶点数增加 (在Unity-CPU-PreSkinning技术中常用，避免顶点数变多导致无法和原本模型顶点数对应)",
        default=False
    ) # type: ignore

    export_normalize_all: bpy.props.BoolProperty(
        name="Normalize All Weights",
        description="导出时把模型自动规格化权重，模型细分后必须勾选，防止模型塌陷问题。",
        default=True
    ) # type: ignore

    recalculate_tangent: bpy.props.BoolProperty(
        name="AverageNormal To TANGENT (Global)",
        description="使用向量相加归一化重计算所有模型的TANGENT值，勾选此项后无法精细控制具体某个模型是否计算，是偷懒选项,在不勾选时默认使用右键菜单中标记的选项",
        default=False
    ) # type: ignore

    recalculate_color: bpy.props.BoolProperty(
        name="AverageNormal To COLOR (Global)",
        description="使用算术平均归一化重计算所有模型的COLOR值，勾选此项后无法精细控制具体某个模型是否计算，是偷懒选项,在不勾选时默认使用右键菜单中标记的选项",
        default=False
    ) # type: ignore

    position_override_filter_draw_type :bpy.props.BoolProperty(
        name="Position Replace Add DRAW_TYPE = 1",
        description="在NPC与VAT-PreSKinning的NPC冲突时会用到此技术，例如HSR匹诺康尼NPC\n格式：\nif DRAW_TYPE == 1\n  ........\nendif",
        default=False
    ) # type: ignore

    vertex_limit_raise_add_filter_index:bpy.props.BoolProperty(
        name="VertexLimitRaise Add filter_index",
        description="在NPC与VAT-PreSKinning的NPC冲突时会用到此技术，例如HSR匹诺康尼NPC\n格式:\nfilter_index = 3000\n\n....\n\nif vb0 == 3000\n  ........\nendif",
        default=False
    ) # type: ignore


    slot_style_texture_add_filter_index:bpy.props.BoolProperty(
        name="Slot Stype Texture Add filter_index",
        description="可解决HSR知更鸟多层渲染问题，可解决ZZZ NPC贴图俯视仰视槽位不一致问题",
        default=False
    ) # type: ignore

    every_drawib_single_ib_file:bpy.props.BoolProperty(
        name="Every DrawIB Single IB File",
        description="If True, only generate one IndexBuffer file for every DrawIB, if False, generate IB File for every component in a DrawIB.",
        default=False
    ) # type: ignore

    
    generate_to_seperate_ini:bpy.props.BoolProperty(
        name="Generate To Seperate Ini",
        description="Generate mod config to CommandList.ini, Resource.ini and Config.ini for better organization.",
        default=False
    ) # type: ignore
    
