import bpy

from ..utils.dbmt_utils import * 

from bpy.props import FloatProperty

class CatterPropertiesGenerateMod(bpy.types.PropertyGroup):
    open_generate_mod_folder_after_run: bpy.props.BoolProperty(
        name="Open GeneratedMod Folder",
        description="Open GeneratedMod folder after run GenerateMod.",
        default=False
    ) # type: ignore

    hash_style_auto_texture: bpy.props.BoolProperty(
        name="Use Hash Style AutoTexture",
        description="Use hash replace style instead of default slot replace style in auto texture ini generate.",
        default=False
    ) # type: ignore

    forbid_auto_texture_ini: bpy.props.BoolProperty(
        name="Forbid Generate Texture Ini",
        description="Forbid to add auto texture ini at generate mod",
        default=False
    ) # type: ignore

    generate_to_seperate_folder: bpy.props.BoolProperty(
        name="Generate To Seperate Folder",
        description="Generate mod to seperated DrawIB folder instaed of put together.",
        default=False
    ) # type: ignore

    # ------------------------------------------------------------------------------------------------------------
    # I don't think write author name and author link and other information on blender panel is a good idea.
    # Mod author should add it manually into mod, if they really care credits they will add more complicated credit info.
    # So default add is not a good idea, not goods enough to let every author happy.
    credit_info_author_name: bpy.props.StringProperty(
        name="Author ",
        description="Author's name.",
        default=""
    ) # type: ignore

    credit_info_author_social_link: bpy.props.StringProperty(
        name="Web Link ",
        description="Author's social link.",
        default=""
    ) # type: ignore



class CatterProperties(bpy.types.PropertyGroup):
    # ------------------------------------------------------------------------------------------------------------
    path: bpy.props.StringProperty(
        name="DBMT-GUI.exe所在路径",
        description="插件需要先选择DBMT-GUI.exe的所在路径才能正常工作",
        default=DBMTUtils.load_dbmt_path(),
        subtype='DIR_PATH'
    ) # type: ignore

    # ------------------------------------------------------------------------------------------------------------
    model_extract_output_path: bpy.props.StringProperty(
        name="",
        description="FrameAnalysis提取出的模型文件默认存放路径",
        default="",
        subtype='DIR_PATH'
    ) # type: ignore


    # ------------------------------------------------------------------------------------------------------------
    model_scale: FloatProperty(
        name="导入模型整体缩放比例",
        description="默认为1.0",
        default=1.0,
    ) # type: ignore

    # ------------------------------------------------------------------------------------------------------------

    export_same_number: bpy.props.BoolProperty(
        name="",
        description="导出时不改变顶点数 (在Unity-CPU-PreSkinning技术中常用，避免导出后顶点数变多导致无法和原本模型顶点数对应)",
        default=False
    ) # type: ignore

    export_normalize_all: bpy.props.BoolProperty(
        name="",
        description="导出时把模型自动规格化权重，防止忘记手动规格化导致模型塌陷问题。",
        default=False
    ) # type: ignore
    # ------------------------------------------------------------------------------------------------------------
    flip_tangent_w:bpy.props.BoolProperty(
        name="",
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

    import_merged_vgmap:bpy.props.BoolProperty(
        name="",
        description="导入时是否导入融合后的顶点组 (WWMI的合并顶点组技术会用到)",
        default=False
    ) # type: ignore

   

    # ------------------------------------------------------------------------------------------------------------
    def __init__(self) -> None:
        super().__init__()
        # self.subtype = 'DIR_PATH'