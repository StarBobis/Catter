import io

from ..migoto.migoto_utils import *


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