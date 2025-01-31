import json
import io

from ..utils.migoto_utils import *

from ..utils.migoto_utils import *
from ..config.generate_mod_config import *
from ..utils.timer_utils import *

from typing import List, Dict, Union
from pathlib import Path
from dataclasses import dataclass, field, asdict
from ..utils.migoto_utils import *

import io
import textwrap
import collections
import math


@dataclass
class ExtractedObjectComponent:
    vertex_offset: int
    vertex_count: int
    index_offset: int
    index_count: int
    vg_offset: int
    vg_count: int
    vg_map: Dict[int, int]


@dataclass
class ExtractedObjectShapeKeys:
    offsets_hash: str = ''
    scale_hash: str = ''
    vertex_count: int = 0
    dispatch_y: int = 0
    checksum: int = 0


@dataclass
class ExtractedObject:
    vb0_hash: str
    cb4_hash: str
    vertex_count: int
    index_count: int
    components: List[ExtractedObjectComponent]
    shapekeys: ExtractedObjectShapeKeys

    def __post_init__(self):
        if isinstance(self.shapekeys, dict):
            self.components = [ExtractedObjectComponent(**component) for component in self.components]
            self.shapekeys = ExtractedObjectShapeKeys(**self.shapekeys)

    def as_json(self):
        return json.dumps(asdict(self), indent=4)

class ExtractedObjectHelper:
    '''
    不用类包起来难受，还是做成工具类好一点。。
    '''
    @classmethod
    def read_metadata(cls,metadata_path: str) -> ExtractedObject:
        with open(metadata_path) as f:
            return ExtractedObject(**json.load(f))
    

class InputLayoutElement(object):
    SemanticName = ""
    SemanticIndex = ""
    Format = ""
    # ByteWidth # 这里没有ByteWidth是因为靠MigotoUtils.EncoderDecoder来控制的
    AlignedByteOffset = ""
    InputSlotClass = ""
    ElementName = ""

    # 固定项
    InputSlot = "0"
    InstanceDataStepRate = "0"

    def __init__(self, arg=None):
        # 不为空的时候说明是从文件或者dict中初始化的
        if arg is not None:
            if isinstance(arg, io.IOBase):
                self.from_file(arg)
            else:
                self.from_dict(arg)

            self.initialize_encoder_decoder()
        
        # 为空的时候说明每一个属性都是我们手动赋值上去的
    
    def initialize_encoder_decoder(self):
        self.encoder, self.decoder = MigotoUtils.EncoderDecoder(self.Format)
    
    def read_attribute_line(self, f) -> bool:
        line = next(f).strip()
        if line.startswith('SemanticName: '):
            self.SemanticName = line[len('SemanticName: ') :]
            # print("SemanticName:" + self.SemanticName)
        elif line.startswith('SemanticIndex: '):
            self.SemanticIndex = line[len('SemanticIndex: ') :]
            # print("SemanticIndex:" + self.SemanticIndex)
            self.SemanticIndex = int(self.SemanticIndex)
        elif line.startswith('Format: '):
            self.Format = line[len('Format: '):]
            # print("Format:" + self.Format)
        elif line.startswith('AlignedByteOffset: '):
            self.AlignedByteOffset = line[len('AlignedByteOffset: ') :]
            # print("AlignedByteOffset:" + self.AlignedByteOffset)
            if self.AlignedByteOffset == 'append':
                raise Fatal('Input layouts using "AlignedByteOffset=append" are not yet supported')
            self.AlignedByteOffset = int(self.AlignedByteOffset)
        elif line.startswith('InputSlotClass: '):
            self.InputSlotClass = line[len('InputSlotClass: ') :]
            # print("InputSlotClass:" + self.InputSlotClass)
            # return false if we meet end of all element
            return False
        return True
        
        
    def from_file(self, f):
        while(self.read_attribute_line(f)):
            pass
        self.format_len = MigotoUtils.format_components(self.Format)
        if self.SemanticIndex != 0:
            self.ElementName = self.SemanticName + str(self.SemanticIndex)
        else:
            self.ElementName = self.SemanticName 

    def to_dict(self):
        d = {'SemanticName': self.SemanticName, 'SemanticIndex': self.SemanticIndex, 'Format': self.Format,
             'AlignedByteOffset': self.AlignedByteOffset,
             'InputSlotClass': self.InputSlotClass,
             'ElementName':self.ElementName}
        return d

    def to_string(self, indent=2):
        return textwrap.indent(textwrap.dedent('''
            SemanticName: %s
            SemanticIndex: %i
            Format: %s
            AlignedByteOffset: %i
            InputSlotClass: %s
            ElementName: %s
        ''').lstrip() % (
            self.SemanticName,
            self.SemanticIndex,
            self.Format,
            self.AlignedByteOffset,
            self.InputSlotClass,
            self.ElementName
        ), ' ' * indent)

    def from_dict(self, d):
        self.SemanticName = d['SemanticName']
        self.SemanticIndex = d['SemanticIndex']
        self.Format = d['Format']
        self.AlignedByteOffset = d['AlignedByteOffset']
        self.InputSlotClass = d['InputSlotClass']
        self.ElementName = d['ElementName']
        self.format_len = MigotoUtils.format_components(self.Format)

    @property
    def name(self):
        if self.SemanticIndex:
            return '%s%i' % (self.SemanticName, self.SemanticIndex)
        return self.SemanticName

    def pad(self, data, val):
        padding = self.format_len - len(data)
        if padding >= 0:
            data.extend([val] * padding)
        return data 

    def clip(self, data):
        return data[:MigotoUtils.format_components(self.Format)]

    def size(self):
        return MigotoUtils.format_size(self.Format)

    def is_float(self):
        return MigotoUtils.misc_float_pattern.match(self.Format)

    def is_int(self):
        return MigotoUtils.misc_int_pattern.match(self.Format)

    # 这个就是elem.encode 返回的是list类型的
    def encode(self, data):
        # print(self.Format, data)
        return self.encoder(data)

    def decode(self, data):
        return self.decoder(data)

    def __eq__(self, other):
        return \
                self.SemanticName == other.SemanticName and \
                self.SemanticIndex == other.SemanticIndex and \
                self.Format == other.Format and \
                self.AlignedByteOffset == other.AlignedByteOffset and \
                self.InputSlotClass == other.InputSlotClass 


class InputLayout(object):
    def __init__(self, custom_prop=[], stride=0):
        # TODO 需要确认一下，我怎么感觉只用到了elems和stride其它的导入的属性都没用上
        self.elems:collections.OrderedDict[str,InputLayoutElement] = collections.OrderedDict()
        self.stride = stride
        if len(custom_prop) != 0:
            for item in custom_prop:
                elem = InputLayoutElement(item)
                self.elems[elem.name] = elem

    def serialise(self):
        return [x.to_dict() for x in self.elems.values()]

    def to_string(self):
        ret = ''
        for i, elem in enumerate(self.elems.values()):
            ret += 'element[%i]:\n' % i
            ret += elem.to_string()
        return ret
    
    def contains(self,element_name:str) ->bool :
        for elem in self.elems:
            # print(elem)
            if elem == element_name:
                # print("contains " + element_name)
                return True
        return False

    def parse_element(self, f):
        elem = InputLayoutElement(f)
        self.elems[elem.name] = elem

    def __iter__(self):
        return iter(self.elems.values())

    def __getitem__(self, semantic):
        return self.elems[semantic]

    def encode(self, vertex) ->bytearray:
        buf = bytearray(self.stride)

        for element_name, data in vertex.items():
            if element_name.startswith('~'):
                continue
            elem = self.elems[element_name]
            data = elem.encode(data)
            buf[elem.AlignedByteOffset:elem.AlignedByteOffset + len(data)] = data

        assert (len(buf) == self.stride)
        return buf
    
    # 这里decode是读取buf文件的时候用的，把二进制数据转换成置顶的类型
    def decode(self, buf):
        vertex = {}
        for elem in self.elems.values():
            data = buf[elem.AlignedByteOffset:elem.AlignedByteOffset + elem.size()]
            vertex[elem.name] = elem.decode(data)
        return vertex

    def __eq__(self, other):
        return self.elems == other.elems



class IndexBuffer(object):
    def __init__(self, *args):
        self.faces = []
        self.first = 0
        self.index_count = 0
        self.format = 'DXGI_FORMAT_UNKNOWN'
        self.gametypename = ""
        self.offset = 0
        self.topology = 'trianglelist'

        # 如果是IOBase类型，说明是以文件名称初始化的，此时fmt要从文件中解析
        if len(args) == 0:
            # 如果不填写参数，则默认为DXGI_FORMAT_R32_UINT类型
            self.format = "DXGI_FORMAT_R32_UINT"
        elif isinstance(args[0], io.IOBase):
            assert (len(args) == 1)
            self.parse_fmt(args[0])
        else:
            self.format, = args

        self.encoder, self.decoder = MigotoUtils.EncoderDecoder(self.format)

    def append(self, face):
        self.faces.append(face)
        self.index_count += len(face)

    def parse_fmt(self, f):
        for line in map(str.strip, f):
            if line.startswith('byte offset:'):
                self.offset = int(line[13:])
            if line.startswith('first index:'):
                self.first = int(line[13:])
            elif line.startswith('index count:'):
                self.index_count = int(line[13:])
            elif line.startswith('topology:'):
                self.topology = line[10:]
                if line != 'topology: trianglelist':
                    raise Fatal('"%s" is not yet supported' % line)
            elif line.startswith('format:'):
                self.format = line[8:]
            elif line.startswith('gametypename:'):
                self.gametypename = line[14:]
            elif line == '':
                    return
        assert (len(self.faces) * 3 == self.index_count)

    def parse_ib_bin(self, f):
        f.seek(self.offset)
        stride = MigotoUtils.format_size(self.format)
        # XXX: Should we respect the first index?
        # f.seek(self.first * stride, whence=1)
        self.first = 0

        face = []
        while True:
            index = f.read(stride)
            if not index:
                break
            face.append(*self.decoder(index))
            if len(face) == 3:
                self.faces.append(tuple(face))
                face = []
        assert (len(face) == 0)

        # We intentionally disregard the index count when loading from a
        # binary file, as we assume frame analysis might have only dumped a
        # partial buffer to the .txt files (e.g. if this was from a dump where
        # the draw call index count was overridden it may be cut short, or
        # where the .txt files contain only sub-meshes from each draw call and
        # we are loading the .buf file because it contains the entire mesh):
        self.index_count = len(self.faces) * 3


    def write(self, output, operator=None):
        for face in self.faces:
            output.write(self.encoder(face))

        msg = 'Wrote %i indices to %s' % (len(self), output.name)
        if operator:
            operator.report({'INFO'}, msg)
        else:
            print(msg)
    
    def __len__(self):
        return len(self.faces) * 3

'''
TODO 

VertexBuffer的这个架构导入实在是太慢了。
但是如果更新到使用Numpy的复杂数据类型，会导致现有的ib和vb架构全部需要推倒重写。
没办法，只能暂时忍受了，反正一般模型导入的时间都不会特别长，在可接受范围内。

'''
class VertexBuffer(object):
    vb_elem_pattern = re.compile(r'''vb\d+\[\d*\]\+\d+ (?P<semantic>[^:]+): (?P<data>.*)$''')

    # Python gotcha - do not set layout=InputLayout() in the default function
    # parameters, as they would all share the *same* InputLayout since the
    # default values are only evaluated once on file load
    def __init__(self, f=None, layout=None):
        # 这里的vertices是3Dmigoto顶点，不是Blender顶点。
        self.vertices = []
        self.layout = layout and layout or InputLayout()
        self.first = 0
        self.vertex_count = 0
        self.offset = 0
        self.topology = 'trianglelist'

        if f is not None:
            for line in map(str.strip, f):
                # print(line)
                if line.startswith('byte offset:'):
                    self.offset = int(line[13:])
                if line.startswith('first vertex:'):
                    self.first = int(line[14:])
                if line.startswith('vertex count:'):
                    self.vertex_count = int(line[14:])
                if line.startswith('stride:'):
                    self.layout.stride = int(line[7:])
                if line.startswith('element['):
                    self.layout.parse_element(f)
                if line.startswith('topology:'):
                    self.topology = line[10:]
                    if line != 'topology: trianglelist':
                        raise Fatal('"%s" is not yet supported' % line)
            assert (len(self.vertices) == self.vertex_count)

    def parse_vb_bin(self, f):
        f.seek(self.offset)
        # XXX: Should we respect the first/base vertex?
        # f.seek(self.first * self.layout.stride, whence=1)
        self.first = 0
        while True:
            vertex = f.read(self.layout.stride)
            if not vertex:
                break
            self.vertices.append(self.layout.decode(vertex))
        self.vertex_count = len(self.vertices)

    def append(self, vertex):
        self.vertices.append(vertex)
        self.vertex_count += 1

    def write(self, output, operator=None):
        for vertex in self.vertices:
            output.write(self.layout.encode(vertex))

        msg = 'Wrote %i vertices to %s' % (len(self), output.name)
        if operator:
            operator.report({'INFO'}, msg)
        else:
            print(msg)

    def __len__(self):
        return len(self.vertices)
    

    
