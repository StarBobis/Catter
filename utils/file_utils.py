import os

class FileUtils:

    def list_files(directory)->list[str]:
        """ 列出目录下的所有文件，不包括子目录 """
        file_list = []

        for entry in os.listdir(directory):
            full_path = os.path.join(directory, entry)
            if os.path.isfile(full_path):
                file_list.append(entry)
        return file_list

