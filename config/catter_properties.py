import bpy

from ..config.main_config import MainConfig

from bpy.props import FloatProperty, IntProperty

class CatterPropertiesGenerateMod(bpy.types.PropertyGroup):
    open_generate_mod_folder_after_run: bpy.props.BoolProperty(
        name="打开生成的Mod文件夹",
        description="生成Mod后打开生成的Mod文件夹",
        default=False
    ) # type: ignore

    hash_style_auto_texture: bpy.props.BoolProperty(
        name="使用Hash风格自动贴图",
        description="在生成Mod时使用Hash风格的自动贴图而不是槽位风格的",
        default=False
    ) # type: ignore

    forbid_auto_texture_ini: bpy.props.BoolProperty(
        name="禁止生成自动贴图ini",
        description="生成Mod时禁止生成贴图相关ini部分",
        default=False
    ) # type: ignore

    generate_to_seperate_folder: bpy.props.BoolProperty(
        name="生成到分开的DrawIB文件夹",
        description="生成Mod时按DrawIB为文件夹名称分开生成而不是全生成到一起，方便进阶制作。",
        default=False
    ) # type: ignore

    export_same_number: bpy.props.BoolProperty(
        name="使用共享TANGENT避免增加顶点数",
        description="使用共享的TANGENT值从而避免hashable计算导致的顶点数增加 (在Unity-CPU-PreSkinning技术中常用，避免顶点数变多导致无法和原本模型顶点数对应)",
        default=False
    ) # type: ignore

    # TODO 完成这个
    export_normalize_all: bpy.props.BoolProperty(
        name="导出时权重自动规格化",
        description="导出时把模型自动规格化权重，防止忘记手动规格化导致模型塌陷问题。",
        default=False
    ) # type: ignore

    recalculate_tangent: bpy.props.BoolProperty(
        name="向量相加归一化重计算TANGENT值(全局)",
        description="使用向量相加归一化重计算所有模型的TANGENT值，勾选此项后无法精细控制具体某个模型是否计算，是偷懒选项,在不勾选时默认使用右键菜单中标记的选项",
        default=False
    ) # type: ignore

    recalculate_color: bpy.props.BoolProperty(
        name="算术平均归一化重计算COLOR值(全局)",
        description="使用算术平均归一化重计算所有模型的COLOR值，勾选此项后无法精细控制具体某个模型是否计算，是偷懒选项,在不勾选时默认使用右键菜单中标记的选项",
        default=False
    ) # type: ignore

    position_override_filter_draw_type :bpy.props.BoolProperty(
        name="Position替换过滤DRAW_TYPE = 1",
        description="在NPC与VAT-PreSKinning的NPC冲突时会用到此技术，例如HSR匹诺康尼NPC",
        default=False
    ) # type: ignore

    # ------------------------------------------------------------------------------------------------------------
    flip_tangent_w:bpy.props.BoolProperty(
        name="翻转TANGENT的W分量",
        description="翻转TANGENT.xyzw的w分量, 目前只有Unity游戏需要翻转这个w分量",
        default=False
    ) # type: ignore

    flip_tangent_z:bpy.props.BoolProperty(
        name="",
        description="翻转TANGENT.xyzw的z分量 (仅用于测试)",
        default=False
    ) # type: ignore

    flip_tangent_y:bpy.props.BoolProperty(
        name="",
        description="翻转TANGENT.xyzw的y分量 (仅用于测试)",
        default=False
    ) # type: ignore

    flip_tangent_x:bpy.props.BoolProperty(
        name="",
        description="翻转TANGENT.xyzw的x分量 (仅用于测试)",
        default=False
    ) # type: ignore
    # ------------------------------------------------------------------------------------------------------------
    flip_normal_w:bpy.props.BoolProperty(
        name="",
        description="翻转NORMAL.xyzw的w分量，只有有w分量的NORMAL才会被翻转w分量，因为大部分游戏的NORMAL都是NORMAL.xyz只有三个分量 (仅用于测试)",
        default=False
    ) # type: ignore

    flip_normal_z:bpy.props.BoolProperty(
        name="",
        description="翻转NORMAL.xyzw的z分量 (仅用于测试)",
        default=False
    ) # type: ignore

    flip_normal_y:bpy.props.BoolProperty(
        name="",
        description="翻转NORMAL.xyzw的y分量 (仅用于测试)",
        default=False
    ) # type: ignore

    flip_normal_x:bpy.props.BoolProperty(
        name="",
        description="翻转NORMAL.xyzw的x分量 (仅用于测试)",
        default=False
    ) # type: ignore


# TODO Deprecated 这么设置不太优雅，应该使用Blender原生方法。
class CatterPropertiesFastColorSettings(bpy.types.PropertyGroup):

    # ---------------COLOR分量快速设置
    fast_color_rgba_r: bpy.props.IntProperty(
        name="RGBA_R",
        description="COLOR的RGBA分量中的R分量",
        default=-1,
        min=-1,  # 最小值
        max=255  # 最大值
    )  # type: ignore

    fast_color_rgba_g: bpy.props.IntProperty(
        name="RGBA_G",
        description="COLOR的RGBA分量中的G分量",
        default=-1,
        min=-1,  # 最小值
        max=255  # 最大值
    )  # type: ignore

    fast_color_rgba_b: bpy.props.IntProperty(
        name="RGBA_B",
        description="COLOR的RGBA分量中的B分量",
        default=-1,
        min=-1,  # 最小值
        max=255  # 最大值
    )  # type: ignore

    fast_color_rgba_a: bpy.props.IntProperty(
        name="RGBA_A",
        description="COLOR的RGBA分量中的A分量",
        default=-1,
        min=-1,  # 最小值
        max=255  # 最大值
    )  # type: ignore

    use_fast_color_rgba:bpy.props.BoolProperty(
        name="快速批量设置COLOR的分量",
        description="注意要有COLOR这个属性才能使用这个，勾选后会将所有COLOR的分量都设为指定值，默认值-1为不设置，只需要修改要设置的值为0到255之间的值即可",
        default=False
    ) # type: ignore




class CatterPropertiesCreditInfo(bpy.types.PropertyGroup):
    # ------------------------------------------------------------------------------------------------------------
    # I don't think write author name and author link and other information on blender panel is a good idea.
    # Mod author should add it manually into mod, if they really care credits they will add more complicated credit info.
    # So default add is not a good idea, not goods enough to let every author happy.
    credit_info_author_name: bpy.props.StringProperty(
        name="作者昵称",
        description="作者的昵称",
        default=""
    ) # type: ignore

    credit_info_author_social_link: bpy.props.StringProperty(
        name="赞助链接",
        description="用于赞助该作者的赞助链接",
        default=""
    ) # type: ignore



class CatterPropertiesImportModel(bpy.types.PropertyGroup):
    # ------------------------------------------------------------------------------------------------------------
    path: bpy.props.StringProperty(
        name="DBMT-GUI.exe所在路径",
        description="插件需要先选择DBMT-GUI.exe的所在路径才能正常工作",
        default=MainConfig.load_dbmt_path(),
        subtype='DIR_PATH'
    ) # type: ignore


    # ------------------------------------------------------------------------------------------------------------
    model_scale: FloatProperty(
        name="导入模型整体缩放比例",
        description="默认为1.0",
        default=1.0,
    ) # type: ignore

    import_merged_vgmap:bpy.props.BoolProperty(
        name="",
        description="导入时是否导入融合后的顶点组 (WWMI的合并顶点组技术会用到)",
        default=False
    ) # type: ignore

    import_flip_scale_x :bpy.props.BoolProperty(
        name="导入模型时Scale X设为-1避免镜像模型",
        description="勾选后在导入模型时把缩放的X分量乘以-1，实现镜像效果，还原游戏中原本的样子，解决导入后镜像对调的问题,与WWMI中mirror mesh选项相同，同样也会导致和部分插件不兼容问题",
        default=False
    ) # type: ignore

