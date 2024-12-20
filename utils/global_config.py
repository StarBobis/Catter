import bpy
import os
import json
from datetime import datetime

class GlobalTimer:
    run_start = None
    run_end = None
    current_execute_methodname = ""

    @classmethod
    def Start(cls,func_name:str):
        # 清空run_start和run_end，并将run_start设为当前时间
        cls.run_start = datetime.now()
        cls.run_end = None
        cls.current_execute_methodname = func_name
        print("\n" +cls.current_execute_methodname + f" started at: {cls.run_start} ")

    @classmethod
    def End(cls):
        if cls.run_start is None:
            print("Timer has not been started. Call Start() first.")
            return
        
        # 将run_end设为当前时间
        cls.run_end = datetime.now()
        
        # 计算时间差
        time_diff = cls.run_end - cls.run_start
        
        # 打印时间差
        print(cls.current_execute_methodname + f" time elapsed: {time_diff} \n")
        
        # 将run_start更新为当前时间
        cls.run_start = cls.run_end
        # print(f"Timer updated start to: {cls.run_start}")


# 生成Mod时的配置类，通过易懂的方法名获取一大长串难记的Blender属性值
# 这样开发的时候方便了反正
class GenerateModConfig:

    @classmethod
    def open_generated_mod_folder_after_run(cls):
        '''
        bpy.context.scene.dbmt_generatemod.open_generate_mod_folder_after_run
        '''
        return bpy.context.scene.dbmt_generatemod.open_generate_mod_folder_after_run
    
    @classmethod
    def hash_style_auto_texture(cls):
        '''
        bpy.context.scene.dbmt_generatemod.hash_style_auto_texture
        '''
        return bpy.context.scene.dbmt_generatemod.hash_style_auto_texture
    
    
    @classmethod
    def forbid_auto_texture_ini(cls):
        '''
        bpy.context.scene.dbmt_generatemod.forbid_auto_texture_ini
        '''
        return bpy.context.scene.dbmt_generatemod.forbid_auto_texture_ini
    
    @classmethod
    def generate_to_seperate_folder(cls):
        '''
        bpy.context.scene.dbmt_generatemod.generate_to_seperate_folder
        '''
        return bpy.context.scene.dbmt_generatemod.generate_to_seperate_folder
    
    @classmethod
    def author_name(cls):
        '''
        bpy.context.scene.dbmt_generatemod.credit_info_author_name
        '''
        return bpy.context.scene.dbmt_generatemod.credit_info_author_name
    
    @classmethod
    def author_link(cls):
        '''
        bpy.context.scene.dbmt_generatemod.credit_info_author_social_link
        '''
        return bpy.context.scene.dbmt_generatemod.credit_info_author_social_link
    
    @classmethod
    def export_same_number(cls):
        '''
        bpy.context.scene.dbmt_generatemod.export_same_number
        '''
        return bpy.context.scene.dbmt_generatemod.export_same_number
    
    

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

    @classmethod
    def get_game_category(cls) -> str:
        if cls.gamename in ["GI","HSR","HI3","ZZZ","BloodySpell","Unity-CPU-PreSkinning"]:
            return GameCategory.UnityVS
        
        elif cls.gamename in ["Game001","LiarsBar","Mecha"]:
            return GameCategory.UnityCS
        
        elif cls.gamename in ["WWMI","SnowBreak"]:
            return GameCategory.UnrealVS
        
        elif cls.gamename in ["TowerOfFantacy"]:
            return GameCategory.UnrealCS
        else:
            return GameCategory.Unknown
        

    # Read Main.json from DBMT folder and then get current workspace name.
    @classmethod
    def read_from_main_json(cls) :
        main_json_path = MainConfig.path_main_json()
        if os.path.exists(main_json_path):
            main_setting_file = open(main_json_path)
            main_setting_json = json.load(main_setting_file)
            main_setting_file.close()
            cls.workspacename = main_setting_json.get("WorkSpaceName","")
            cls.gamename = main_setting_json.get("GameName","")

    @classmethod
    def base_path(cls):
        return bpy.context.scene.dbmt.path
    
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
    def path_output_folder(cls):
        return os.path.join(MainConfig.path_current_game_folder(),"3Dmigoto\\Mods\\output\\") 
    
    @classmethod
    def path_workspace_folder(cls):
        return os.path.join(MainConfig.path_output_folder(), MainConfig.workspacename + "\\")
    
    @classmethod
    def path_generate_mod_folder(cls):
        # 确保用的时候直接拿到的就是已经存在的目录
        generate_mod_folder_path = os.path.join(MainConfig.path_workspace_folder(),"GeneratedMod\\")
        if not os.path.exists(generate_mod_folder_path):
            os.makedirs(generate_mod_folder_path)
        return generate_mod_folder_path
    
    @classmethod
    def path_extract_types_folder(cls):
        return os.path.join(MainConfig.path_configs_folder(),"ExtractTypes\\")
    
    @classmethod
    def path_current_game_type_folder(cls):
        return os.path.join(MainConfig.path_extract_types_folder(),MainConfig.gamename + "\\")
    
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
    
    # 定义Json文件路径---------------------------------------------------------------------------------
    @classmethod
    def path_main_json(cls):
        return os.path.join(MainConfig.path_configs_folder(), "Main.json")
    
    


    