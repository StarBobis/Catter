import bpy

from ..config.main_config import MainConfig

from bpy.props import FloatProperty, IntProperty

class CatterPropertiesGenerateMod(bpy.types.PropertyGroup):
    open_generate_mod_folder_after_run: bpy.props.BoolProperty(
        name="打开生成的Mod文件夹",
        description="生成Mod后打开生成的Mod文件夹",
        default=True
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
        description="在NPC与VAT-PreSKinning的NPC冲突时会用到此技术，例如HSR匹诺康尼NPC\n格式：\nif DRAW_TYPE == 1\n  ........\nendif",
        default=False
    ) # type: ignore

    vertex_limit_raise_add_filter_index:bpy.props.BoolProperty(
        name="VertexLimitRaise添加filter_index标识",
        description="在NPC与VAT-PreSKinning的NPC冲突时会用到此技术，例如HSR匹诺康尼NPC\n格式:\nfilter_index = 3000\n\n....\n\nif vb0 == 3000\n  ........\nendif",
        default=False
    ) # type: ignore


    slot_style_texture_add_filter_index:bpy.props.BoolProperty(
        name="槽位风格贴图添加filter_index标识",
        description="可解决HSR知更鸟多层渲染问题，可解决ZZZ NPC贴图俯视仰视槽位不一致问题",
        default=False
    ) # type: ignore

    




class CatterPropertiesCreditInfo(bpy.types.PropertyGroup):
    '''
    I don't think write author name and author link and other information on blender panel is a good idea.
    Mod author should add it manually into mod, if they really care credits they will add more complicated credit info.
    So default add is not a good idea, not goods enough to let every author happy.
    But keep these code here, maybe will use it in the future.
    '''

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

    import_delete_loose :bpy.props.BoolProperty(
        name="导入模型时删除模型松散点",
        description="勾选后在导入模型时会把松散点删除，进入编辑模式就不会看见松散的没用的点影响Mod制作了，由于很常用所以默认是勾选的。",
        default=True
    ) # type: ignore