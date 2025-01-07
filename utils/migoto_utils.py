import re
import numpy
import struct

from glob import glob


# This used to catch any exception in run time and raise it to blender output console.
class Fatal(Exception):
    pass


class MigotoUtils:
    f32_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD]32)+_FLOAT''')
    f16_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD]16)+_FLOAT''')
    u32_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD]32)+_UINT''')
    u16_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD]16)+_UINT''')
    u8_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD]8)+_UINT''')
    s32_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD]32)+_SINT''')
    s16_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD]16)+_SINT''')
    s8_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD]8)+_SINT''')
    unorm16_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD]16)+_UNORM''')
    unorm8_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD]8)+_UNORM''')
    snorm16_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD]16)+_SNORM''')
    snorm8_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD]8)+_SNORM''')

    misc_float_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD][0-9]+)+_(?:FLOAT|UNORM|SNORM)''')
    misc_int_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD][0-9]+)+_[SU]INT''')

    components_pattern = re.compile(r'''(?<![0-9])[0-9]+(?![0-9])''')

    @classmethod
    def get_nptype_from_format(cls,fmt):
        '''
        解析DXGI Format字符串，返回numpy的数据类型
        '''
        if cls.f32_pattern.match(fmt):
            return numpy.float32
        elif cls.f16_pattern.match(fmt):
            return numpy.float16
        elif cls.u32_pattern.match(fmt):
            return numpy.uint32
        elif cls.u16_pattern.match(fmt):
            return numpy.uint16
        elif cls.u8_pattern.match(fmt):
            return numpy.uint8
        elif cls.s32_pattern.match(fmt):
            return numpy.int32
        elif cls.s16_pattern.match(fmt):
            return numpy.int16
        elif cls.s8_pattern.match(fmt):
            return numpy.int8

        elif cls.unorm16_pattern.match(fmt):
            return numpy.uint16
        elif cls.unorm8_pattern.match(fmt):
            return numpy.uint8
        elif cls.snorm16_pattern.match(fmt):
            return numpy.int16
        elif cls.snorm8_pattern.match(fmt):
            return numpy.int8

        raise Fatal('Mesh uses an unsupported DXGI Format: %s' % fmt)

    @classmethod
    def EncoderDecoder(cls,fmt):
        '''
        转换效率极低，不建议使用
        有条件还是调用numpy的astype方法
        '''
        if cls.f32_pattern.match(fmt):
            return (lambda data: b''.join(struct.pack('<f', x) for x in data),
                    lambda data: numpy.frombuffer(data, numpy.float32).tolist())
        if cls.f16_pattern.match(fmt):
            return (lambda data: numpy.fromiter(data, numpy.float16).tobytes(),
                    lambda data: numpy.frombuffer(data, numpy.float16).tolist())
        if cls.u32_pattern.match(fmt):
            return (lambda data: numpy.fromiter(data, numpy.uint32).tobytes(),
                    lambda data: numpy.frombuffer(data, numpy.uint32).tolist())
        if cls.u16_pattern.match(fmt):
            return (lambda data: numpy.fromiter(data, numpy.uint16).tobytes(),
                    lambda data: numpy.frombuffer(data, numpy.uint16).tolist())
        if cls.u8_pattern.match(fmt):
            return (lambda data: numpy.fromiter(data, numpy.uint8).tobytes(),
                    lambda data: numpy.frombuffer(data, numpy.uint8).tolist())
        if cls.s32_pattern.match(fmt):
            return (lambda data: numpy.fromiter(data, numpy.int32).tobytes(),
                    lambda data: numpy.frombuffer(data, numpy.int32).tolist())
        if cls.s16_pattern.match(fmt):
            return (lambda data: numpy.fromiter(data, numpy.int16).tobytes(),
                    lambda data: numpy.frombuffer(data, numpy.int16).tolist())
        if cls.s8_pattern.match(fmt):
            return (lambda data: numpy.fromiter(data, numpy.int8).tobytes(),
                    lambda data: numpy.frombuffer(data, numpy.int8).tolist())

        if cls.unorm16_pattern.match(fmt):
            return (
                lambda data: numpy.around((numpy.fromiter(data, numpy.float32) * 65535.0)).astype(numpy.uint16).tobytes(),
                lambda data: (numpy.frombuffer(data, numpy.uint16) / 65535.0).tolist())
        if cls.unorm8_pattern.match(fmt):
            return (lambda data: numpy.around((numpy.fromiter(data, numpy.float32) * 255.0)).astype(numpy.uint8).tobytes(),
                    lambda data: (numpy.frombuffer(data, numpy.uint8) / 255.0).tolist())
        if cls.snorm16_pattern.match(fmt):
            return (
                lambda data: numpy.around((numpy.fromiter(data, numpy.float32) * 32767.0)).astype(numpy.int16).tobytes(),
                lambda data: (numpy.frombuffer(data, numpy.int16) / 32767.0).tolist())
        if cls.snorm8_pattern.match(fmt):
            return (lambda data: numpy.around((numpy.fromiter(data, numpy.float32) * 127.0)).astype(numpy.int8).tobytes(),
                    lambda data: (numpy.frombuffer(data, numpy.int8) / 127.0).tolist())
        # print(fmt)
        raise Fatal('File uses an unsupported DXGI Format: %s' % fmt)


    @classmethod
    def format_components(cls,fmt):
        '''
        输入FORMAT返回该FORMAT的元素个数
        例如输入R32G32B32_FLOAT 返回元素个数：3
        这里R32G32B32_FLOAT的元素个数是3，所以就返回3
        '''
        return len(cls.components_pattern.findall(fmt))

    @classmethod
    def format_size(cls,fmt):
        matches = cls.components_pattern.findall(fmt)
        return sum(map(int, matches)) // 8





