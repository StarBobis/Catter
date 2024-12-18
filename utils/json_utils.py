import json

class JsonUtils:


    @classmethod
    def SaveToFile(cls,filepath:str,json_dict:dict):
        # 将字典转换为 JSON 格式的字符串
        json_string = json.dumps(json_dict, ensure_ascii=False, indent=4)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(json_string)
            
    @classmethod
    def LoadFromFile(cls, filepath: str) -> dict:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                # 读取文件内容并解析为字典
                json_dict = json.load(f)
            return json_dict
        except FileNotFoundError:
            print(f"Error: The file at {filepath} was not found.")
            return {}
        except json.JSONDecodeError:
            print(f"Error: The file at {filepath} is not a valid JSON file.")
            return {}