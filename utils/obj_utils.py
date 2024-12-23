import bpy

from ..migoto.migoto_utils import Fatal

class ObjUtils:

    @classmethod
    def get_bpy_context_object(cls):
        '''
        获取当前场景中的obj对象,如果为None则抛出Fatal异常
        '''
        obj = bpy.context.object
        if obj is None:
            # 为空时不导出
            raise Fatal('No object selected')
        
        return obj