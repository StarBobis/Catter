from datetime import datetime


class TimerUtils:
    run_start = None
    run_end = None
    current_execute_methodname = ""

    @classmethod
    def Start(cls,func_name:str):
        # 清空run_start和run_end，并将run_start设为当前时间
        cls.run_start = datetime.now()
        cls.run_end = None
        cls.current_execute_methodname = func_name
        print("\n" +cls.current_execute_methodname + f" started at: {cls.run_start} ")

    @classmethod
    def End(cls):
        if cls.run_start is None:
            print("Timer has not been started. Call Start() first.")
            return
        
        # 将run_end设为当前时间
        cls.run_end = datetime.now()
        
        # 计算时间差
        time_diff = cls.run_end - cls.run_start
        
        # 打印时间差
        print(cls.current_execute_methodname + f" time elapsed: {time_diff} \n")
        
        # 将run_start更新为当前时间
        cls.run_start = cls.run_end
        # print(f"Timer updated start to: {cls.run_start}")
