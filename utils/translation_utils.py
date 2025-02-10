import bpy


'''
使用字典翻译，简洁而优雅，一用一个不吱声。
'''
class TR:
    cn_to_en_dict:dict[str:str] = {
        # -----------------------------------------------------------------------------
        "特殊属性面板":"Properties",
        "当前未选中任何物体":"doesn't select any object yet",
        # -----------------------------------------------------------------------------
        "导入模型配置":"Import Model Config",
        "模型导入大小比例":"Import Model Scale",
        "设置Scale的X分量为-1避免模型镜像":"Set Scale.X to -1 to avoid mirror",
        "使用融合统一顶点组":"Use Merged VGMaps",
        # -----------------------------------------------------------------------------
        "生成Mod配置":"Generate Mod Config",
        "使用共享TANGENT避免增加顶点数":"Stay Vertex Number Same",
        "只使用标记过的贴图":"Only Use Marked Texture",
        "禁止自动贴图流程":"Forbid Auto Texture Ini",
        "生成到分开的DrawIB文件夹":"Generate To Seperate DrawIB Folder",
        "向量归一化法线存入TANGENT(全局)":"AverageNormal To TANGENT (Global)",
        "算术平均归一化法线存入COLOR(全局)":"AverageNormal To COLOR (Global)",
        "Position替换添加DRAW_TYPE=1判断":"Position Replace Add DRAW_TYPE = 1",
        "VertexLimitRaise添加filter_index过滤器":"VertexLimitRaise Add filter_index",
        "槽位风格贴图添加filter_index过滤器":"Slot Style Texture Add filter_index",
        "每个DrawIB仅使用一个IB文件":"Every DrawIB Single IB File",
        "使用多个ini文件架构":"Generate To Seperate Ini",
        # -----------------------------------------------------------------------------
        "选择DBMT所在文件夹":"Select DBMT Folder",
        "使用指定的DBMT路径":"Use Specified DBMT Path",
        "DBMT路径: ":"DBMT Path: ",
        "当前游戏: ":"Current Game: ",
        "当前工作空间: ":"Current WorkSpace: ",

        "一键导入当前工作空间内容":"Import All From WorkSpace",
        "导入.ib .vb .fmt格式模型":"Import .ib .vb .fmt model",
        "生成Mod":"Generate Mod",
    }


    @classmethod
    def translate(cls,chinese_txt) -> str:
        current_language = bpy.app.translations.locale
        # 中文是zh_HANS
        if current_language != "zh_HANS":
            # 获取尝试获取英文翻译，如果没有的话，就直接返回原字符串
            return cls.cn_to_en_dict.get(chinese_txt,chinese_txt)
        else:
            return chinese_txt