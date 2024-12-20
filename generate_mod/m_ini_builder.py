

class M_SectionType:
    Present = "Present"
    Constants = "Constants"
    Key = "Key"
    TextureOverrideIB = "TextureOverrideIB"
    TextureOverrideVB = "TextureOverrideVB"
    TextureOverrideTexture = "TextureOverrideTexture"
    IBSkip = "IBSkip"
    ResourceVB = "ResourceVB"
    ResourceIB = "ResourceIB"
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

        self.__append_section_line(M_SectionType.ResourceIB)
        self.__append_section_line(M_SectionType.ResourceVB)
        self.__append_section_line(M_SectionType.ResourceTexture)

        self.__append_section_line(M_SectionType.TextureOverrideTexture)
        self.__append_section_line(M_SectionType.VSHashCheck)

        self.__append_section_line(M_SectionType.CreditInfo)

        with open(config_ini_path,"w") as f:
            f.writelines(self.line_list)



