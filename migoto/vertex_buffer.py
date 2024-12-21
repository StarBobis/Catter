
from ..utils.migoto_utils import *
from .input_layout import *

class VertexBuffer(object):
    vb_elem_pattern = re.compile(r'''vb\d+\[\d*\]\+\d+ (?P<semantic>[^:]+): (?P<data>.*)$''')

    # Python gotcha - do not set layout=InputLayout() in the default function
    # parameters, as they would all share the *same* InputLayout since the
    # default values are only evaluated once on file load
    def __init__(self, f=None, layout=None):
        self.vertices = []
        self.layout = layout and layout or InputLayout()
        self.first = 0
        self.vertex_count = 0
        self.offset = 0
        self.topology = 'trianglelist'

        if f is not None:
            self.parse_vb_txt(f)

    def parse_vb_txt(self, f):
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

    def parse_vertex_element(self, match):
        fields = match.group('data').split(',')

        if self.layout[match.group('semantic')].Format.endswith('INT'):
            return tuple(map(int, fields))

        return tuple(map(float, fields))
    

    # 还有个问题，就是Buffer是需要组合在一起的，所以先按vertex转为一个整体的buf文件
    # 再根据数据类型的步长，一点点读取每个vertex转为的buf，追加到每个Category的Buf里
    # 最后输出每个Category的Buf文件。
    def convert_to_elementname_byteslist_dict(self):
        '''
        要特别注意，返回的是ElementName, List[Int]类型的bytelist，写出的时候需要转换为bytearray
        '''
        model_elementname_buf_dict = {}

        # 根据数据类型的CategoryStrideDict，截取后追加到每个Category的Buf里
        for vertex in self.vertices:
            vertex_elementname_bytelist_dict = self.layout.get_elementname_bytelist_dict_of_vertex(vertex)
            for elementname, bytelist in vertex_elementname_bytelist_dict.items():
                if elementname not in model_elementname_buf_dict:
                    model_elementname_buf_dict[elementname] = []
                model_elementname_buf_dict[elementname].extend(bytelist)

        # print(type(model_elementname_buf_dict["POSITION"]))
        return model_elementname_buf_dict

        

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
    

        # 向量归一化
    def vector_normalize(self,v):
        """归一化向量"""
        length = math.sqrt(sum(x * x for x in v))
        if length == 0:
            return v  # 避免除以零
        return [x / length for x in v]
    
    def add_and_normalize_vectors(self,v1, v2):
        """将两个向量相加并规范化(normalize)"""
        # 相加
        result = [a + b for a, b in zip(v1, v2)]
        # 归一化
        normalized_result = self.vector_normalize(result)
        return normalized_result
    
    # Nico: 向量相加归一化法线 
    def get_position_normalizednormal_dict(self,vertices):
        position_normal_dict = {}
        for vertex in vertices:
            position = vertex["POSITION"]
            position_str = str(position[0]) + "_" + str(position[1]) + "_" + str(position[2])

            normal = vertex["NORMAL"]
            if position_str in position_normal_dict:
                normalized_normal = self.add_and_normalize_vectors(normal,position_normal_dict[position_str])
                position_normal_dict[position_str] = normalized_normal
            else:
                position_normal_dict[position_str] = normal

        
        return position_normal_dict
    
    # Nico: 算数平均归一化法线，HI3 2.0角色使用的方法
    def get_position_averagenormal_dict(self,vertices):
        position_normal_sum_dict = {}
        position_normal_number_dict = {}

        for vertex in vertices:
            position = vertex["POSITION"]
            position_str = str(position[0]) + "_" + str(position[1]) + "_" + str(position[2])
            normal = vertex["NORMAL"]
            if position_str in position_normal_sum_dict:
                normal_sum = [a + b for a, b in zip(normal, position_normal_sum_dict[position_str])]
                position_normal_sum_dict[position_str] = normal_sum
                position_normal_number_dict[position_str] = position_normal_number_dict[position_str] + 1
            else:
                position_normal_sum_dict[position_str] = normal
                position_normal_number_dict[position_str] = 1

        
        position_normal_dict = {}
        for k, v in position_normal_sum_dict.items():
            number = float(position_normal_number_dict[k])
            # Nico: 平均后的值+1后再除以2，就归一化到[0,1]了 这个归一化是逆向分析HI3 2.0新角色模型得到的。
            average_normal = [((x / number) + 1 ) / 2 for x in v] 
            position_normal_dict[k] = average_normal

        return position_normal_dict

    # 辅助函数：计算两个向量的点积
    def dot_product(self,v1, v2):
        return sum(a * b for a, b in zip(v1, v2))

    # Nico: 米游所有游戏都能用到这个，还有曾经的GPU-PreSkinning的GF2也会用到这个，崩坏三2.0新角色除外。
    # TODO 尽管这个可以起到相似的效果，但是仍然无法完美获取模型本身的TANGENT数据，只能做到99%近似。
    # 经过测试，头发部分并不是简单的向量归一化，也不是算术平均归一化。
    def vector_normalized_normal_to_tangent(self):
        position_normal_dict = self.get_position_normalizednormal_dict(self.vertices)
        new_vertices = []


        for vertex in self.vertices:
            position = vertex["POSITION"]
            position_str = str(position[0]) + "_" + str(position[1]) + "_" + str(position[2])
            if position_str in position_normal_dict:
                normalized_normal = position_normal_dict[position_str]

                # 计算副切线
                tangent = vertex["TANGENT"][:3]
                binormal = self.vector_normalize([
                    normalized_normal[1] * tangent[2] - normalized_normal[2] * tangent[1],
                    normalized_normal[2] * tangent[0] - normalized_normal[0] * tangent[2],
                    normalized_normal[0] * tangent[1] - normalized_normal[1] * tangent[0]
                ])
                # 确定W分量
                w = 1.0 if self.dot_product(binormal, vertex.get("BINORMAL", [0, 0, 1])) >= 0.0 else -1.0
                    
                # 最终赋值
                vertex["TANGENT"][0] = normalized_normal[0]
                vertex["TANGENT"][1] = normalized_normal[1]
                vertex["TANGENT"][2] = normalized_normal[2]
                if bpy.context.scene.dbmt.flip_tangent_w:
                    vertex["TANGENT"][3] = -1 * w
                else:
                    vertex["TANGENT"][3] = w
                new_vertices.append(vertex)

        self.vertices = new_vertices

    def arithmetic_average_normal_to_attribute(self,attribute):
        position_normal_dict = self.get_position_averagenormal_dict(self.vertices)
        new_vertices = []
        for vertex in self.vertices:
            position = vertex["POSITION"]
            position_str = str(position[0]) + "_" + str(position[1]) + "_" + str(position[2])
            if position_str in position_normal_dict:
                normalized_normal = position_normal_dict[position_str]
                vertex[attribute][0] = normalized_normal[0]
                vertex[attribute][1] = normalized_normal[1]
                vertex[attribute][2] = normalized_normal[2]
                new_vertices.append(vertex)

        self.vertices = new_vertices

    # Nico: 目前出现的游戏中只有崩坏三2.0新角色会用到这个
    def arithmetic_average_normal_to_color(self):
        self.arithmetic_average_normal_to_attribute("COLOR")

