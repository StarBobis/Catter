import bpy
import os
import json

from .generate_mod_config import *
from .import_model_config import ImportModelConfig

class GameCategory:
    UnityVS = "UnityVS"
    UnityCS = "UnityCS"
    UnrealCS = "UnrealCS"
    UnrealVS = "UnrealVS"
    Unknown = "Unknown"

# 全局配置类，使用字段默认为全局可访问的唯一静态变量的特性，来实现全局变量
# 可减少从Main.json中读取的IO消耗
class MainConfig:
    # 全局静态变量,任何地方访问到的值都是唯一的
    gamename = ""
    workspacename = ""
    dbmtlocation = ""

    @classmethod
    def get_game_category(cls) -> str:
        if cls.gamename in ["GI","HSR","HI3","ZZZ","BloodySpell","Unity-CPU-PreSkinning"]:
            return GameCategory.UnityVS
        
        elif cls.gamename in ["Game001"]:
            return GameCategory.UnityCS
        
        elif cls.gamename in ["WWMI","Game002"]:
            return GameCategory.UnrealVS
        
        elif cls.gamename in ["Game003"]:
            return GameCategory.UnrealCS
        else:
            return GameCategory.Unknown
        
    @classmethod
    def save_dbmt_path(cls):
        # 获取当前脚本文件的路径
        script_path = os.path.abspath(__file__)

        # 获取当前插件的工作目录
        plugin_directory = os.path.dirname(script_path)

        # 构建保存文件的路径
        config_path = os.path.join(plugin_directory, 'Config.json')

        # 创建字典对象
        config = {'dbmt_path': bpy.context.scene.dbmt.path}

        # 将字典对象转换为 JSON 格式的字符串
        json_data = json.dumps(config)

        # 保存到文件
        with open(config_path, 'w') as file:
            file.write(json_data)

    @classmethod
    def load_dbmt_path(cls):
        # 获取当前脚本文件的路径
        script_path = os.path.abspath(__file__)

        # 获取当前插件的工作目录
        plugin_directory = os.path.dirname(script_path)

        # 构建配置文件的路径
        config_path = os.path.join(plugin_directory, 'Config.json')

        # 读取文件
        with open(config_path, 'r') as file:
            json_data = file.read()

        # 将 JSON 格式的字符串解析为字典对象
        config = json.loads(json_data)

        # 读取保存的路径
        return config['dbmt_path']

    @classmethod
    def read_from_main_json(cls) :
        main_json_path = MainConfig.path_main_json()
        if os.path.exists(main_json_path):
            main_setting_file = open(main_json_path)
            main_setting_json = json.load(main_setting_file)
            main_setting_file.close()
            cls.workspacename = main_setting_json.get("WorkSpaceName","")
            cls.gamename = main_setting_json.get("GameName","")
            cls.dbmtlocation = main_setting_json.get("DBMTLocation","") + "\\"
        else:
            print("Can't find: " + main_json_path)

    @classmethod
    def base_path(cls):
        return cls.dbmtlocation
    
    @classmethod
    def path_configs_folder(cls):
        return os.path.join(MainConfig.base_path(),"Configs\\")
    
    @classmethod
    def path_games_folder(cls):
        return os.path.join(MainConfig.base_path(),"Games\\")
    
    @classmethod
    def path_current_game_folder(cls):
        return os.path.join(MainConfig.path_games_folder(), MainConfig.gamename + "\\")
    
    @classmethod
    def path_mods_folder(cls):
        return os.path.join(MainConfig.path_current_game_folder(),"3Dmigoto\\Mods\\") 

    @classmethod
    def path_output_folder(cls):
        return os.path.join(MainConfig.path_current_game_folder(),"3Dmigoto\\Mods\\output\\") 
    
    @classmethod
    def path_workspace_folder(cls):
        return os.path.join(MainConfig.path_output_folder(), MainConfig.workspacename + "\\")
    
    @classmethod
    def path_generate_mod_folder(cls):
        # 确保用的时候直接拿到的就是已经存在的目录
        generate_mod_folder_path = os.path.join(MainConfig.path_mods_folder(),"Mod_"+MainConfig.workspacename + "\\")
        if not os.path.exists(generate_mod_folder_path):
            os.makedirs(generate_mod_folder_path)
        return generate_mod_folder_path
    
    @classmethod
    def path_extract_gametype_folder(cls,draw_ib:str,gametype_name:str):
        return os.path.join(MainConfig.path_workspace_folder(), draw_ib + "\\TYPE_" + gametype_name + "\\")
    
    @classmethod
    def path_generatemod_buffer_folder(cls,draw_ib:str):
        if GenerateModConfig.generate_to_seperate_folder():
            buffer_path = os.path.join(MainConfig.path_generate_mod_folder(),draw_ib + "\\Buffer\\")
        else:
            buffer_path = os.path.join(MainConfig.path_generate_mod_folder(),"Buffer\\")
        if not os.path.exists(buffer_path):
            os.makedirs(buffer_path)
        return buffer_path
    
    @classmethod
    def path_generatemod_texture_folder(cls,draw_ib:str):
        if GenerateModConfig.generate_to_seperate_folder():
            texture_path = os.path.join(MainConfig.path_generate_mod_folder(),draw_ib + "\\Texture\\")
        else:
            texture_path = os.path.join(MainConfig.path_generate_mod_folder(),"Texture\\")
        if not os.path.exists(texture_path):
            os.makedirs(texture_path)
        return texture_path
    
    @classmethod
    def path_appdata_local(cls):
        return os.path.join(os.environ['LOCALAPPDATA'])
    
    # 定义基础的Json文件路径---------------------------------------------------------------------------------
    @classmethod
    def path_main_json(cls):
        if ImportModelConfig.use_specified_dbmt():
            return os.path.join(ImportModelConfig.path(),"Configs\\Main.json")
        else:
            return os.path.join(MainConfig.path_appdata_local(), "DBMT-Main.json")
    
    @classmethod
    def path_setting_json(cls):
        if ImportModelConfig.use_specified_dbmt():
            return os.path.join(ImportModelConfig.path(),"Configs\\Setting.json")
        else:
            return os.path.join(MainConfig.path_appdata_local(), "DBMT-Setting.json")
    