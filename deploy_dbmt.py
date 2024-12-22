# Nico: Deploy our C++/C# design mod tool to release folder.

import shutil
import os

class FileUpdate:
    release_package_path =  "C:\\Users\\Administrator\\Desktop\\ReleasePackage\\"
    dev_path = "C:\\Users\\Administrator\\source\\repos\\StarBobis\\DirectX-BufferModTool\\DBMT\\DBMT\\bin\\x64\\Release\\net8.0-windows10.0.22621.0\\"
    test_path = "C:\\Users\\Administrator\\Desktop\\net8.0-windows10.0.22621.0\\"

    dbmt_source_path = "C:\\Users\\Administrator\\source\\repos\\mmt-community\\x64\\Release\\"
    
    @classmethod
    def safe_copy2(cls,filename:str,source_folder_path:str,target_folder_path:str):
        if os.path.exists(source_folder_path) and os.path.exists(target_folder_path):
            shutil.copyfile(source_folder_path + filename, target_folder_path + filename)
        else:
            print("Source file doesn't exisits.")

    @classmethod
    def update_dbmt(cls):
        release_package_plugins_path = cls.release_package_path + "Plugins\\"
        dev_plugins_path = cls.dev_path + "Plugins\\"
        test_plugins_path = cls.test_path + "Plugins\\"

        cls.safe_copy2("DBMT.exe", cls.dbmt_source_path , release_package_plugins_path)
        cls.safe_copy2("DBMT.exe", cls.dbmt_source_path , dev_plugins_path )
        cls.safe_copy2("DBMT.exe", cls.dbmt_source_path , test_plugins_path)

    @classmethod
    def update_3dmigoto_loader(cls):
        target_list = [cls.release_package_path,cls.dev_path,cls.test_path]

        for target_path in target_list:
            target_game_folder_path = target_path + "Games\\"
            # list all gamename directory name.
            dirlist = os.listdir(target_game_folder_path)
            for gamename in dirlist:
                target_3dmigoto_folder_path = target_game_folder_path + gamename + "\\3Dmigoto\\"
                if os.path.exists(target_3dmigoto_folder_path):
                    cls.safe_copy2("3Dmigoto Loader.exe", cls.dbmt_source_path, target_3dmigoto_folder_path)
        
# deploy to release folder.
if __name__ == '__main__':
    # update DBMT core
    FileUpdate.update_dbmt()

    # update 3Dmigoto Loader.exe
    FileUpdate.update_3dmigoto_loader()
    




