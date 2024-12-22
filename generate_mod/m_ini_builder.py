import hashlib

class M_SectionType:
    Present = "Present"
    Constants = "Constants"
    Key = "Key"
    TextureOverrideIB = "TextureOverrideIB"
    TextureOverrideVB = "TextureOverrideVB"
    TextureOverrideTexture = "TextureOverrideTexture"
    IBSkip = "IBSkip"
    ResourceBuffer = "ResourceBuffer"
    ResourceTexture = "ResourceTexture"
    CreditInfo = "CreditInfo"
    VSHashCheck = "VSHashCheck"


class M_IniSection:
    def __init__(self,section_type:M_SectionType) -> None:
        self.SectionType = section_type
        self.SectionName = ""
        self.SectionLineList = []

    def append(self,line:str):
        self.SectionLineList.append(line)

    def new_line(self):
        self.SectionLineList.append("")


class M_IniBuilder:
    def __init__(self):
        self.line_list = []
        self.ini_section_list:list[M_IniSection] = []
    
    def clear(self):
        self.line_list.clear()
        self.ini_section_list.clear()

    def __append_section_line(self,ini_section_type:M_SectionType):
        '''
        Only can be legally call in M_IniBuilder.
        '''
        for ini_section in self.ini_section_list:
            if ini_section.SectionType == ini_section_type:
                self.line_list.append("\n\n;----------------------------------------------------------\n; >>>>>> Start of "+ ini_section_type +" <<<<<<\n")
                for line in ini_section.SectionLineList:
                    self.line_list.append(line + "\n")
                self.line_list.append("; >>>>>> End of " + ini_section_type + " <<<<<<\n;----------------------------------------------------------\n")

    def append_section(self,m_inisection:M_IniSection):
        self.ini_section_list.append(m_inisection)

    def save_to_file(self,config_ini_path:str):
        self.__append_section_line(M_SectionType.Constants)
        self.__append_section_line(M_SectionType.Present)
        self.__append_section_line(M_SectionType.Key)

        self.__append_section_line(M_SectionType.IBSkip)

        self.__append_section_line(M_SectionType.TextureOverrideVB)
        self.__append_section_line(M_SectionType.TextureOverrideIB)

        self.__append_section_line(M_SectionType.ResourceBuffer)
        self.__append_section_line(M_SectionType.ResourceTexture)

        self.__append_section_line(M_SectionType.TextureOverrideTexture)
        self.__append_section_line(M_SectionType.VSHashCheck)

        self.__append_section_line(M_SectionType.CreditInfo)

        sha256 = self.calculate_sha256_for_list(self.line_list)
        # print("sha256: " + sha256)

        # Add after sha256 calculation.
        self.line_list.append("\n;sha256=" + sha256 + "\n\n") 

        # Read ini and find sha256, if not same then write ini, if same do nothing.
        ini_sha256 = self.get_sha256_from_ini(config_ini_path)
        # print("old ini sha256: " + ini_sha256)
        # print("new ini sha256: " + sha256)
        if ini_sha256 != sha256:
            print("Write new mod ini because sha256 is not same.")
            with open(config_ini_path,"w") as f:
                f.writelines(self.line_list)
        else:
            print("Skip write mod ini becuase sha256 is same, ini file content not changed so we are safe to skip.")


    def calculate_sha256_for_list(self,string_list):
        # 创建一个新的sha256哈希对象
        sha256_hash = hashlib.sha256()
        
        # 将列表中的每个字符串编码为字节，并更新哈希对象
        for line in string_list:
            byte_line = line.encode('utf-8')
            sha256_hash.update(byte_line)
        
        # 获取十六进制格式的哈希值
        hex_digest = sha256_hash.hexdigest()
        
        return hex_digest

    def get_sha256_from_ini(self,ini_file_path:str):
        """
        读取指定路径的INI文件，找到以;sha256=开头的行，
        并返回该行中;sha256=后面的内容（去除前后空白字符）。
        找不到或者出错则返回空字符串
        """
        sha256_value = ""
        
        try:
            with open(ini_file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    # 去除行首尾的空白字符
                    stripped_line = line.strip()
                    
                    # 检查行是否以";sha256="开头
                    if stripped_line.startswith(";sha256="):
                        # 提取";sha256="后面的内容，并去除前后空白字符
                        sha256_value = stripped_line[len(";sha256="):].strip()
                        break  # 找到后停止循环，假设只有一行匹配
                        
        except FileNotFoundError:
            print(f"Error: The file at {ini_file_path} was not found.")
            return ""
        except Exception as e:
            print(f"An error occurred: {e}")
            return ""
            
        return sha256_value

