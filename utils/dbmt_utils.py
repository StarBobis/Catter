import os
import bpy
import json
import subprocess
from .global_config import *


class DBMTUtils:

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

    # Get drawib list from Game's Config.json.
    @classmethod
    def get_extract_drawib_list_from_workspace_config_json(cls)->list:
        workspace_path = MainConfig.path_workspace_folder()

        game_config_path = os.path.join(workspace_path,"Config.json")
        game_config_file = open(game_config_path)
        game_config_json = json.load(game_config_file)
        game_config_file.close()

        # draw_ib_list =game_config_json["DrawIBList"]
        draw_ib_list = []
        for item in game_config_json:
            drawib_value = item["DrawIB"]
            draw_ib_list.append(drawib_value)

        return draw_ib_list


    @classmethod
    def get_import_drawib_folder_path_dict_with_first_match_type(cls,workspace_folder_path:str)->list:
        output_folder_path = workspace_folder_path
        draw_ib_list = DBMTUtils.get_extract_drawib_list_from_workspace_config_json()
        
        final_import_folder_path_dict = {}

        for draw_ib in draw_ib_list:
            gpu_import_folder_path_list = []
            cpu_import_folder_path_list = []

            # print("DrawIB:", draw_ib)
            import_drawib_folder_path = os.path.join(output_folder_path, draw_ib)

            if not os.path.exists(import_drawib_folder_path):
                continue

            dirs = os.listdir(import_drawib_folder_path)
            for dirname in dirs:
                if not dirname.startswith("TYPE_"):
                    continue
                final_import_folder_path = os.path.join(import_drawib_folder_path,dirname)
                if dirname.startswith("TYPE_GPU"):
                    gpu_import_folder_path_list.append(final_import_folder_path)
                elif dirname.startswith("TYPE_CPU"):
                    cpu_import_folder_path_list.append(final_import_folder_path)

            if len(gpu_import_folder_path_list) != 0:
                final_import_folder_path_dict[draw_ib] = gpu_import_folder_path_list[0]
            elif len(cpu_import_folder_path_list) != 0:
                final_import_folder_path_dict[draw_ib] = cpu_import_folder_path_list[0]
            else:
                pass
                # raise ImportError()

        return final_import_folder_path_dict


    # Read import model name list from tmp.json.
    @classmethod
    def get_prefix_list_from_tmp_json(cls,import_folder_path:str) ->list:
        
        tmp_json_path = os.path.join(import_folder_path, "tmp.json")

        drawib = os.path.basename(import_folder_path)

        if os.path.exists(tmp_json_path):
            tmp_json_file = open(tmp_json_path)
            tmp_json = json.load(tmp_json_file)
            tmp_json_file.close()
            import_prefix_list = tmp_json["ImportModelList"]
            if len(import_prefix_list) == 0:
                import_partname_prefix_list = []
                partname_list = tmp_json["PartNameList"]
                for partname in partname_list:
                    import_partname_prefix_list.append(drawib + "-" + partname)
                return import_partname_prefix_list
            else:
                # import_prefix_list.sort() it's naturally sorted in DBMT so we don't need sort here.
                return import_prefix_list
        else:
            return []


    # Read model prefix attribute in fmt file to locate .ib and .vb file.
    # Save lots of space when reverse mod which have same stride but different kinds of D3D11GameType.
    @classmethod
    def get_model_prefix_from_fmt_file(cls,fmt_file_path:str)->str:
        with open(fmt_file_path, 'r') as file:
            for i in range(10):  
                line = file.readline().strip()
                if not line:
                    continue
                if line.startswith('prefix:'):
                    return line.split(':')[1].strip()  
        return ""  

