

class M_DrawIndexed:

    def __init__(self) -> None:
        self.DrawNumber = ""
        self.DrawOffsetIndex = ""
        self.DrawStartIndex = "0"
        self.AliasName = "" # 代表一个obj具体的draw_indexed
    
    def get_draw_str(self) ->str:
        return "drawindexed = " + self.DrawNumber + "," + self.DrawOffsetIndex +  "," + self.DrawStartIndex
