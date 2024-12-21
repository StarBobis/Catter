
class M_IniHelper:

    @classmethod
    def get_style_alias(cls,partname:str):
        '''
        Convert to GIMI name style because it's widely used by Mod author.
        '''
        partname_gimi_alias_dict = {
            "1":"Head","2":"Body","3":"Dress","4":"Extra"
            ,"5":"Extra1","6":"Extra2","7":"Extra3","8":"Extra4","9":"Extra5"
            ,"10":"Extra6","11":"Extra7","12":"Extra8"}
        return partname_gimi_alias_dict.get(partname,partname)
    
    