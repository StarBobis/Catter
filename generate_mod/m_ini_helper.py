from .m_ini_builder import *
from ..utils.json_utils import JsonUtils
from ..config.main_config import MainConfig

class M_IniHelper:
    key_list = ["x","c","v","b","n","m","j","k","l","o","p","[","]",
                    "x","c","v","b","n","m","j","k","l","o","p","[","]",
                    "x","c","v","b","n","m","j","k","l","o","p","[","]"]

    @classmethod
    def get_style_alias(cls,partname:str):
        '''
        Convert to alia name style because it's widely used by Mod author.
        '''
        partname_alias_dict = {
            "1":"Head","2":"Body","3":"Dress","4":"Extra"
            ,"5":"Extra1","6":"Extra2","7":"Extra3","8":"Extra4","9":"Extra5"
            ,"10":"Extra6","11":"Extra7","12":"Extra8"}
        return partname_alias_dict.get(partname,partname)
    
    @classmethod
    def get_mod_switch_key(cls,key_index:int):
        '''
        Default mod switch/toggle key.
        '''
        
        # 尝试读取Setting.json里的设置，解析错误就还使用默认的
        try:
            setting_json_dict = JsonUtils.LoadFromFile(MainConfig.path_setting_json())
            print(setting_json_dict)
            mod_switch_key = str(setting_json_dict["ModSwitchKey"])
            mod_switch_key_list = mod_switch_key.split(",")
            print(mod_switch_key_list)
            switch_key_list:list[str] = []
            for switch_key_str in mod_switch_key_list:
                switch_key_list.append(switch_key_str[1:-1])
            cls.key_list = switch_key_list
        except Exception:
            print("解析自定义SwitchKey失败")

        return cls.key_list[key_index]
    

