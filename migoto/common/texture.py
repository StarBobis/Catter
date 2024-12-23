
from dataclasses import dataclass, field
from typing import List,Dict

@dataclass
class TextureSlot:
    # ps-t0,ps-t1,etc...
    PixelSlot:str
    # exists in deduped folder.
    Valid:bool

    # Let user decide these:
    # used in auto texture
    Used:bool = field(init=False,default=True)
    # DiffuseMap, LightMap, NormalMap, etc...
    DescName:str = field(init=False,default="")


@dataclass
class TextureLayout:
    SlotList:List[TextureSlot]

    # Nico: It's important,every kinds of texture type have a list of pixel shader hash value.
    PixelShaderHashList:List[str]
