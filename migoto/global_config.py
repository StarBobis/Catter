import os
import re

from dataclasses import dataclass, field
from typing import List,Dict
from enum import Enum

from ..utils.file_utils import FileUtils
from .d3d11_game_type import D3D11GameType,D3D11Element,D3D11GameTypeLv2
from ..utils.log_utils import LOG

# Nico: Thanks for SpectrumQT's WWMI project, I learned how to use @dataclass to save my time 
# and lots of other python features so use python can works as good as C++ and better and faster.

class HashType(Enum):
    Texture = "-ps-t"
    VertexBuffer = "-vb"
    ConstantBuffer = "-cb"

    ComputeShader = "-cs="
    VertexShader = "-vs="
    PixelShader = "-ps="


@dataclass
class ResourceFile:
    FilePath:str

    FileName:str = field(init=False)
    TypeSlot:str = field(init=False)

    def __post_init__(self):
        self.FileName = os.path.basename(self.FilePath)
        self.TypeSlot = self.get_type_slot()

    def get_hash(self,hash_type:str,hash_length:int)->str:
        if hash_type not in self.FileName:
            return ""
            
        if "=" in hash_type:
            split_right_str = self.FileName.split(hash_type)[1]
            return split_right_str[0:hash_length]
        else:
            split_right_str = self.FileName.split(hash_type)[1]
            equal_index = split_right_str.find('=')
            start_index = equal_index + 1
            end_index = equal_index + hash_length
            return split_right_str[start_index:end_index]
        
    def get_type_slot(self)->str:
        if "=" in self.FileName:
            split_first = self.FileName.split("=")[0]

        return split_first[len("000001-"):]


@dataclass
class FrameAnalysisData:
    WorkFolder:str

    FileNameList:list[str] = field(init=False)
    DedupedFileNameList:list[str] = field(init=False)

    def __post_init__(self):
        self.FileNameList = FileUtils.list_files(self.WorkFolder)
        self.DedupedFileNameList = FileUtils.list_files(os.path.join(self.WorkFolder,"deduped\\"))

    def filter_filename(self,contain:str,suffix:str) -> list[str]:
        new_filename_list = []
        for file_name in self.FileNameList:
            if contain in file_name and file_name.endswith(suffix):
                new_filename_list.append(file_name)
        return new_filename_list
    
    def get_indexlist_by_drawib(self,drawib:str) -> list[str]:
        indexlist = []
        ib_related_filename_list = self.filter_filename(contain=drawib,suffix=".buf")
        for ib_related_filename in ib_related_filename_list:
            indexlist.append(ib_related_filename[0:6])
        return indexlist
    
    def get_deduped_filename_by_hash(self,file_hash:str)->str:
        for deduped_filename in self.DedupedFileNameList:
            if file_hash in deduped_filename:
                return deduped_filename
        return ""

    

@dataclass
class FrameAnalysisLog:
    WorkFolder:str

    LogFilePath:str = field(init=False)

    def __post_init__(self):
        self.LogFilePath = os.path.join(self.WorkFolder,"log.txt")



@dataclass
class GlobalConfig:
    # We put all loader in a fixed folder structure so can locate them only by game name.
    GameName:str
    # This folder contains all 3dmigoto loader seperated by game name.
    GameLoaderPath:str
    # This folder contains all config json file.
    ConfigFolderPath:str

    # Where 3Dmigoto's d3d11.dll located.
    LoaderFolder:str = field(init=False)
    # eg: FrameAnalysis-2024-10-30-114032.
    FrameAnalysisFolder:str = field(init=False)
    # path of 3Dmigoto's d3d11.dll located folder + current work frame analysis folder.
    WorkFolder:str = field(init=False)
    # deduped folder path of current frame analysis folder.
    DedupedFolder:str= field(init=False)

    # wrapper config for all d3d11 game type.
    D3D11GameTypeConfig:D3D11GameTypeLv2 = field(init=False,repr=False)

    FAData:FrameAnalysisData = field(init=False,repr=False)
    FALog:FrameAnalysisLog = field(init=False,repr=False)

    def __post_init__(self):

        self.initialize_folder_path()
        self.initialize_d3d11_gametype()

    def initialize_folder_path(self):
        self.LoaderFolder = os.path.join(self.GameLoaderPath,self.GameName + "\\3Dmigoto\\")
        if not os.path.exists(self.LoaderFolder):
            LOG.log_warning_str("LoaderFolder doesn't exists. " + self.LoaderFolder)

        self.FrameAnalysisFolder = self.find_latest_frameanalysis_folder()
        if self.FrameAnalysisFolder == "":
            LOG.log_warning_str("Latest FrameAnalysis folder not found. WorkFolder will not exists.")
        else:
            self.WorkFolder = os.path.join(self.LoaderFolder, self.FrameAnalysisFolder + "\\") 
            LOG.log_warning_str("Current WorkFolder: " + self.WorkFolder)

            self.DedupedFolder =os.path.join(self.WorkFolder, "deduped\\")
            if not os.path.exists(self.DedupedFolder):
                LOG.log_warning_str("Current DedupedFolder not exists: " + self.DedupedFolder)
            
            self.FAData = FrameAnalysisData(WorkFolder=self.WorkFolder)
            self.FALog = FrameAnalysisLog(WorkFolder=self.WorkFolder)

    def find_latest_frameanalysis_folder(self):
        frame_analysis_folder_list = []

        # return default "" if the LoaderFolder not exists.
        if not os.path.exists(self.LoaderFolder):
            return ""
        
        folder_list = os.listdir(self.LoaderFolder)
        for folder_name in folder_list:
            if "FrameAnalysis-" in folder_name:
                frame_analysis_folder_list.append(folder_name)
            
        frame_analysis_folder_list.sort(reverse=True)
        if len(frame_analysis_folder_list) != 0:
            return frame_analysis_folder_list[0]
        else:
            return ""

    def initialize_d3d11_gametype(self):
        gametype_folder_path = os.path.join(self.ConfigFolderPath, "gametypes\\" + self.GameName + "\\")
        self.D3D11GameTypeConfig = D3D11GameTypeLv2(GameTypeConfigFolderPath=gametype_folder_path)
