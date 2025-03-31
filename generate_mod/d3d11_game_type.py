
import os
import json

from typing import List,Dict
from dataclasses import dataclass, field

from ..utils.file_utils import FileUtils


@dataclass
class D3D11Element:
    SemanticName:str
    SemanticIndex:int
    Format:str
    ByteWidth:int
    # Which type of slot and slot number it use? eg:vb0
    ExtractSlot:str
    # Is it from pointlist or trianglelist or compute shader?
    ExtractTechnique:str
    # Human named category, also will be the buf file name suffix.
    Category:str

    # Fixed items
    InputSlot:str = field(default="0", init=False, repr=False)
    InputSlotClass:str = field(default="per-vertex", init=False, repr=False)
    InstanceDataStepRate:str = field(default="0", init=False, repr=False)

    # Generated Items
    ElementNumber:int = field(init=False,default=0)
    AlignedByteOffset:int
    ElementName:str = field(init=False,default="")

    def __post_init__(self):
        self.ElementName = self.get_indexed_semantic_name()

    def get_indexed_semantic_name(self)->str:
        if self.SemanticIndex == 0:
            return self.SemanticName
        else:
            return self.SemanticName + str(self.SemanticIndex)



# Designed to read from json file for game type config
@dataclass
class D3D11GameType:
    # Read config from json file, easy to modify and test.
    FilePath:str = field(repr=False)

    # Original file name.
    FileName:str = field(init=False,repr=False)
    # The name of the game type, usually the filename without suffix.
    GameTypeName:str = field(init=False)
    # Is GPU-PreSkinning or CPU-PreSkinning
    GPU_PreSkinning:bool = field(init=False,default=False)
    # All d3d11 element,should be already ordered in config json.
    D3D11ElementList:list[D3D11Element] = field(init=False,repr=False)
    # Ordered ElementName list.
    OrderedFullElementList:list[str] = field(init=False,repr=False)
    # 按顺序排列的CategoryName
    OrderedCategoryNameList:list[str] = field(init=False,repr=False)
    # Category name and draw category name, used to decide the category should draw on which category's TextureOverrideVB.
    CategoryDrawCategoryDict:Dict[str,str] = field(init=False,repr=False)
    # TexcoordPatchNull
    TexcoordPatchNull:bool = field(init=False,repr=False)
    # UE4PatchNullInBlend
    UE4PatchNullInBlend:bool =  field(init=False,repr=False)
    # RootComputeShaderHash
    RootComputeShaderHash:str =  field(init=False,repr=False)


    # Generated
    ElementNameD3D11ElementDict:Dict[str,D3D11Element] = field(init=False,repr=False)
    CategoryExtractSlotDict:Dict[str,str] =  field(init=False,repr=False)
    CategoryExtractTechniqueDict:Dict[str,str] =  field(init=False,repr=False)
    CategoryStrideDict:Dict[str,int] =  field(init=False,repr=False)

    def __post_init__(self):
        self.FileName = os.path.basename(self.FilePath)
        self.GameTypeName = os.path.splitext(self.FileName)[0]
        

        self.OrderedFullElementList = []
        self.OrderedCategoryNameList = []
        self.D3D11ElementList = []

        self.CategoryDrawCategoryDict = {}
        self.CategoryExtractSlotDict = {}
        self.CategoryExtractTechniqueDict = {}
        self.CategoryStrideDict = {}
        self.ElementNameD3D11ElementDict = {}

        # read config from json file.
        with open(self.FilePath, 'r', encoding='utf-8') as f:
            game_type_json = json.load(f)
        
        self.GPU_PreSkinning = game_type_json.get("GPU-PreSkinning",False)
        self.TexcoordPatchNull = game_type_json.get("TexcoordPatchNull",False)
        self.UE4PatchNullInBlend = game_type_json.get("UE4PatchNullInBlend",False)
        self.RootComputeShaderHash = game_type_json.get("RootComputeShaderHash","")

        self.GameTypeName = game_type_json.get("WorkGameType","")

        # self.OrderedFullElementList = game_type_json.get("OrderedFullElementList",[])
        self.CategoryDrawCategoryDict = game_type_json.get("CategoryDrawCategoryMap",{})
        d3d11_element_list_json = game_type_json.get("D3D11ElementList",[])
        aligned_byte_offset = 0
        for d3d11_element_json in d3d11_element_list_json:
            d3d11_element = D3D11Element(
                SemanticName=d3d11_element_json.get("SemanticName",""),
                SemanticIndex=int(d3d11_element_json.get("SemanticIndex","")),
                Format=d3d11_element_json.get("Format",""),
                ByteWidth=int(d3d11_element_json.get("ByteWidth",0)),
                ExtractSlot=d3d11_element_json.get("ExtractSlot",""),
                ExtractTechnique=d3d11_element_json.get("ExtractTechnique",""),
                Category=d3d11_element_json.get("Category",""),
                AlignedByteOffset=aligned_byte_offset
            )
            aligned_byte_offset = aligned_byte_offset + d3d11_element.ByteWidth
            self.D3D11ElementList.append(d3d11_element)

            # 这俩常用
            self.OrderedFullElementList.append(d3d11_element.get_indexed_semantic_name())
            if d3d11_element.Category not in self.OrderedCategoryNameList:
                self.OrderedCategoryNameList.append(d3d11_element.Category)
        
        for d3d11_element in self.D3D11ElementList:
            self.CategoryExtractSlotDict[d3d11_element.Category] = d3d11_element.ExtractSlot
            self.CategoryExtractTechniqueDict[d3d11_element.Category] = d3d11_element.ExtractTechnique
            self.CategoryStrideDict[d3d11_element.Category] = self.CategoryStrideDict.get(d3d11_element.Category,0) + d3d11_element.ByteWidth
            self.ElementNameD3D11ElementDict[d3d11_element.ElementName] = d3d11_element
    
    def get_real_category_stride_dict(self) -> dict:
        new_dict = {}
        for categoryname,category_stride in self.CategoryStrideDict.items():
            new_dict[categoryname] = category_stride
        return new_dict

  
