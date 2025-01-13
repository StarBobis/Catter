import os
import struct

from dataclasses import dataclass, field

from .d3d11_game_type import D3D11GameType

@dataclass
class IndexBufferBufFile:
    FilePath:str
    Stride:int
    FileName:str = field(init=False)
    NumberList:list[int] = field(init=False,repr=False)

    # useful attributes
    UniqueNumberList:set[int] = field(init=False,repr=False)
    MaxNumber:int = field(init=False)
    MinNumber:int = field(init=False)
    IndexCount:int = field(init=False)
    UniqueNumberCount:int = field(init=False)

    def __post_init__(self):
        self.FileName = os.path.basename(self.FilePath)
        self.NumberList = self.parse_bin_data(self.Stride)
        # calculate number
        self.UniqueNumberList = set(self.NumberList)
        self.MaxNumber = max(self.NumberList)
        self.MinNumber = min(self.NumberList)
        self.IndexCount = len(self.NumberList)
        self.UniqueNumberCount = len(self.UniqueNumberList)
        
    def parse_bin_data(self, stride):
        if stride not in [2, 4]:
            raise ValueError("Stride must be either 2 or 4")

        format_char = 'H' if stride == 2 else 'I'  # H for unsigned short, I for unsigned int
        with open(self.FilePath, 'rb') as file:
            byte_data = file.read()
            count = len(byte_data) // stride
            unpacked_data = struct.unpack(f'<{count}{format_char}', byte_data[:count*stride])
        
        return list(unpacked_data)
    

class VertexBufferBufFile:
    FilePath:str
    Stride:int
    FileName:str = field(init=False)
    
    def __post_init__(self):
        self.FileName = os.path.basename(self.FilePath)

    def parse_bin_data():
        pass


@dataclass
class FmtFile:
    FilePath:str = field(init=False)
    FileName:str = field(init=False)
    D3d11GameTypeObj:D3D11GameType = field(init=False)
    Format:str = field(init=False)

    def write_to_file(self,write_file_path:str,ib_stride=4,prefix=""):
        self.Format = "DXGI_FORMAT_R32_UINT"
        if ib_stride == 2:
            self.Format = "DXGI_FORMAT_R16_UINT"

        stride_count = 0
        for element_name in self.D3d11GameTypeObj.OrderedFullElementList:
            d3d11_element = self.D3d11GameTypeObj.ElementNameD3D11ElementDict.get(element_name)
            stride_count += d3d11_element.ByteWidth
        
        fmt_line_list = []
        fmt_line_list.append("stride: " + str(stride_count))
        fmt_line_list.append("topology: trianglelist")
        fmt_line_list.append("format: " + self.Format)
        if prefix != "":
            fmt_line_list.append("prefix: " + prefix)
        
        element_number = 0
        aligned_byte_offset = 0
        for element_name in self.D3d11GameTypeObj.OrderedFullElementList:
            d3d11_element = self.D3d11GameTypeObj.ElementNameD3D11ElementDict.get(element_name)
            fmt_line_list.append("element[" + str(element_number) + "]")
            fmt_line_list.append("  SemanticName: " + d3d11_element.SemanticName)
            fmt_line_list.append("  SemanticIndex: " + str(d3d11_element.SemanticIndex))
            fmt_line_list.append("  Format: " + d3d11_element.Format)
            fmt_line_list.append("  InputSlot: " + d3d11_element.InputSlot)
            fmt_line_list.append("  AlignedByteOffset: " + str(aligned_byte_offset))
            aligned_byte_offset += d3d11_element.ByteWidth
            fmt_line_list.append("  InputSlotClass: " + d3d11_element.InputSlotClass)
            fmt_line_list.append("  InstanceDataStepRate: " + d3d11_element.InstanceDataStepRate)

        with open(write_file_path, 'w', encoding='utf-8') as file:
            file.write('\n'.join(fmt_line_list))  


            