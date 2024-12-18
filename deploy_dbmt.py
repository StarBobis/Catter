# Nico: Deploy our C++/C# design mod tool to release folder.

import shutil
import os



# deploy to release folder.
if __name__ == '__main__':
    release_package_plugins_path = "C:\\Users\\Administrator\\Desktop\\ReleasePackage\\Plugins\\"
    dev_plugins_path = "C:\\Users\\Administrator\\source\\repos\\StarBobis\\DirectX-BufferModTool\\DBMT\\DBMT\\bin\\x64\\Release\\net8.0-windows10.0.22621.0\\Plugins\\"
    test_plugins_path = "C:\\Users\\Administrator\\Desktop\\net8.0-windows10.0.22621.0\\Plugins\\"

    dbmt_source_path = "C:\\Users\\Administrator\\source\\repos\\mmt-community\\x64\\Release\\"

    shutil.copyfile(dbmt_source_path + "DBMT.exe", release_package_plugins_path + "DBMT.exe")
    shutil.copyfile(dbmt_source_path + "DBMT.exe", dev_plugins_path + "DBMT.exe")
    shutil.copyfile(dbmt_source_path + "DBMT.exe", test_plugins_path + "DBMT.exe")



