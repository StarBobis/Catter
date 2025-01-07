
from ..migoto.migoto_utils import *
from .input_layout import *
from ..config.generate_mod_config import *
from ..utils.timer_utils import *

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
    

    
