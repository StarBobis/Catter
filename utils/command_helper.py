# The helper class helps us to execute outside programs.
import subprocess

from .global_config import *


class CommandHelper:

    @classmethod
    def OpenGeneratedModFolder(cls):
        '''
        This will be call after generate mod, it will open explorer and shows the result mod files generated.
        '''
        if GenerateModConfig.open_generated_mod_folder_after_run():
            subprocess.run(['explorer',MainConfig.path_generate_mod_folder()])



