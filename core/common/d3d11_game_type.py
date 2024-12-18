
import os
import json

from typing import List,Dict
from dataclasses import dataclass, field

from ..utils.dbmt_file_utils import dbmt_fileutil__list_files


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
    # PatchBLENDWEIGHTS
    PatchBLENDWEIGHTS:bool = field(init=False,repr=False)
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
        self.PatchBLENDWEIGHTS = game_type_json.get("PatchBLENDWEIGHTS",False)
        self.TexcoordPatchNull = game_type_json.get("TexcoordPatchNull",False)
        self.UE4PatchNullInBlend = game_type_json.get("UE4PatchNullInBlend",False)
        self.RootComputeShaderHash = game_type_json.get("RootComputeShaderHash","")

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
    

    # used in mod reverse, combine every category's buffer file into a final vertex buffer .vb file.
    # so we can import it into blender.
    def combine_buf_files_to_vb_file_bytearray(self,category_name_buf_file_path_dict:Dict[str,str]):
        vertex_count = 0
        category_vb_bytearray_list_dict = {}

        # category order must be correct, we have already config that correctly in json config file,so don't worry.
        for category in self.CategoryStrideDict:
            category_filepath = category_name_buf_file_path_dict.get(category)
            category_buf_file = open(category_filepath, "rb")
            data = bytearray(category_buf_file.read())
            category_buf_file.close()

            category_bytearray_list = []
            categorty_stride = self.CategoryStrideDict.get(category,0)
            i = 0
            while i < len(data):
                category_bytearray_list.append(data[i:i + categorty_stride])
                i += categorty_stride

            vertex_count = len(category_bytearray_list)
            category_vb_bytearray_list_dict[category] = category_bytearray_list

        # Merge them into a final bytearray
        tmp_vb_file_bytearray = bytearray()
        for i in range(vertex_count):
            for category in category_vb_bytearray_list_dict:
                bytearray_list = category_vb_bytearray_list_dict.get(category)
                add_byte = bytearray_list[i]
                tmp_vb_file_bytearray += add_byte

        return tmp_vb_file_bytearray


@dataclass
class D3D11GameTypeLv2:
    GameTypeConfigFolderPath:str

    CurrentD3D11GameTypeList:List[D3D11GameType] = field(init=False)
    GameTypeName_D3D11GameType_Dict:Dict[str,D3D11GameType] = field(init=False)
    Ordered_GPU_CPU_D3D11GameTypeList:List[D3D11GameType] = field(init=False)

    def __post_init__(self):
        self.CurrentD3D11GameTypeList = []
        self.GameTypeName_D3D11GameType_Dict = {}
        self.Ordered_GPU_CPU_D3D11GameTypeList = []

        filelist = dbmt_fileutil__list_files(self.GameTypeConfigFolderPath)
        for json_file_name in filelist:
            if not json_file_name.endswith(".json"):
                continue
            game_type = D3D11GameType(os.path.join(self.GameTypeConfigFolderPath, json_file_name))
            self.CurrentD3D11GameTypeList.append(game_type)
            game_type_name = os.path.splitext(json_file_name)[0]
            self.GameTypeName_D3D11GameType_Dict[game_type_name] = game_type
        
        # First add GPU-PreSkinning then add CPU-PreSkinning 
        # to make sure auto game type detect will first detect GPU-PreSkinning GameType.
        for game_type in self.CurrentD3D11GameTypeList:
            if game_type.GPU_PreSkinning:
                self.Ordered_GPU_CPU_D3D11GameTypeList.append(game_type)
        for game_type in self.CurrentD3D11GameTypeList:
            if not game_type.GPU_PreSkinning:
                self.Ordered_GPU_CPU_D3D11GameTypeList.append(game_type)

    def get_unique_gametype_list(self) -> List[D3D11GameType]:
        unique_gametype_list:List[D3D11GameType] = []
        for d3d11gametype in self.Ordered_GPU_CPU_D3D11GameTypeList:
            # the first one just add it.
            if len(unique_gametype_list) == 0:
                unique_gametype_list.append(d3d11gametype)
                continue

            contains_this_gametype:bool = False
            for unique_d3d11gametype in unique_gametype_list:
                if d3d11gametype.OrderedFullElementList != unique_d3d11gametype.OrderedFullElementList:
                    continue
                if d3d11gametype.PatchBLENDWEIGHTS != d3d11gametype.PatchBLENDWEIGHTS:
                    continue

                all_element_same:bool = True
                for element_name in d3d11gametype.OrderedFullElementList:
                    element1 = d3d11gametype.ElementNameD3D11ElementDict[element_name]
                    element2 = unique_d3d11gametype.ElementNameD3D11ElementDict[element_name]
                    if element1.ByteWidth != element2.ByteWidth:
                        all_element_same = False
                        break
                if all_element_same:
                    contains_this_gametype = True
                    break
            
            if not contains_this_gametype:
                unique_gametype_list.append(d3d11gametype)

        return unique_gametype_list


    def detect_game_type(self,category_name_buf_file_path_dict:Dict[str,str],reverse=False) -> list[str]:
        matched_gametypename_list:list[str] = []
        # Reverse game type detect will need to remove d3d11gametype which have same d3d11ElementList and same PatcBLENDWEIGHTS.
        gametype_list:List[D3D11GameType] = self.CurrentD3D11GameTypeList
        if reverse:
            gametype_list:List[D3D11GameType] = self.get_unique_gametype_list()

        for d3d11gametype in gametype_list:
            # category number must be qeual
            if len(d3d11gametype.CategoryStrideDict) != len(category_name_buf_file_path_dict):
                continue

            # calculate vertex count by current d3d11gametype's Position stride,
            # if vertex count is correct,then every other category's file stride should match with current category
            # under this vertex count number.
            position_file_path:str = category_name_buf_file_path_dict.get("Position","")
            position_file_size:int = os.path.getsize(position_file_path)
            stride:int = d3d11gametype.CategoryStrideDict.get("Position",0)
            vertex_count = position_file_size / stride
            # print("PositionStride:" + str(stride) + " VertexCount:" + str(vertex_count))

            all_category_match:bool = True
            for category_name in d3d11gametype.CategoryStrideDict:
                category_stride = d3d11gametype.CategoryStrideDict.get(category_name,0)
                category_file_path:str = category_name_buf_file_path_dict.get(category_name,"")
                category_file_size:int = os.path.getsize(category_file_path)
                file_stride = category_file_size / vertex_count
                
                if category_name == "Blend" and d3d11gametype.PatchBLENDWEIGHTS:
                    category_stride = d3d11gametype.ElementNameD3D11ElementDict["BLENDINDICES"]

                if category_stride != file_stride:
                    # print(d3d11gametype.GameTypeName + " can't match: " + category_name + " original_stride:" +str(category_stride) + " file_stride:" + str(file_stride))
                    all_category_match = False
                    break
            if all_category_match:
                matched_gametypename_list.append(d3d11gametype.GameTypeName)
        
        return matched_gametypename_list
                

