# The helper class helps us to execute outside programs.
import subprocess

from ..config.main_config import *


class CommandUtils:

    @classmethod
    def OpenGeneratedModFolder(cls):
        '''
        This will be call after generate mod, it will open explorer and shows the result mod files generated.
        '''
        if GenerateModConfig.open_generated_mod_folder_after_run():
            generated_mod_folder_path = MainConfig.path_generate_mod_folder()
            # if " " in generated_mod_folder_path:
            #     generated_mod_folder_path = '"{}"'.format(generated_mod_folder_path)
            # print("generated_mod_folder_path: " + generated_mod_folder_path)
            # subprocess.run(['explorer',generated_mod_folder_path])
            os.startfile(generated_mod_folder_path)



