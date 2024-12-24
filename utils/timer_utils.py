from datetime import datetime

from .log_utils import LOG

class TimerUtils:
    run_start = None
    run_end = None

    methodname_runstart_dict = {}

    @classmethod
    def Start(cls,func_name:str):
        # 清空run_start和run_end，并将run_start设为当前时间
        cls.run_start = datetime.now()
        cls.run_end = None
        cls.methodname_runstart_dict[func_name] = cls.run_start
        LOG.newline()
        print("[" + func_name + f"] started at: {cls.run_start} ")
        LOG.newline()

    @classmethod
    def End(cls,func_name:str = ""):
        if cls.run_start is None:
            print("Timer has not been started. Call Start() first.")
            return
        
        # 将run_end设为当前时间
        cls.run_end = datetime.now()

        LOG.newline()
        if func_name == "":
            # 计算时间差
            time_diff = cls.run_end - cls.run_start
            
            # 打印时间差
            print(f"last function time elapsed: {time_diff} ")
        else:
            time_diff = cls.run_end - cls.methodname_runstart_dict.get(func_name,0)

            # 打印时间差
            print("[" + func_name + f"] time elapsed: {time_diff} ")
        LOG.newline()
        # 将run_start更新为当前时间
        cls.run_start = cls.run_end
        # print(f"Timer updated start to: {cls.run_start}")
