# Designed for ShapeKey reverse technique for SinsOfSeven's SliderImpact project.
# First you reverse Base, then you reverse a shapekey (it will need vertex count match)
# so you can click "Join As ShapeKey" in Blender to reverse add the Shapekey back to Base model.

import os
import shutil

from .buffer_file import IndexBufferBufFile,FmtFile
from ..migoto.global_config import GlobalConfig
from ..utils.log_utils import log_newline


# Manually reverse mod to 3D model file, only support unity vertex shader preskinning mod reverse.
# Current stable supported game list: GenshinImpact, Honkai StarRail,Honkai Impact 3, Zenless Zone Zero.
if __name__ == "__main__":
    # How to manually reverse a mod ? read these code and follow the steps in comments.

    # 1.where is your mod file located? fill it into mod_root_folder.
    mod_root_folder = "C:\\Users\\Administrator\\Desktop\\XianyunMod0\\"

    # 2.add your index buffer file path into index_buffer_filepath_list.
    index_buffer_filepath_list = []
    index_buffer_filepath_list.append(os.path.join(mod_root_folder,"XianyunBody.ib"))
    index_buffer_filepath_list.append(os.path.join(mod_root_folder,"XianyunDress.ib"))
    index_buffer_filepath_list.append(os.path.join(mod_root_folder,"XianyunHead.ib"))
    # 3.fill a dict thant contains category name and buf file path
    # in hoyoverse games there is only 3 possible category name: Position, Texcoord, Blend
    category_name_buf_file_path_dict = {}
    category_name_buf_file_path_dict["Position"] = os.path.join(mod_root_folder, "XianyunPosition.buf")
    # category_name_buf_file_path_dict["Position"] = os.path.join(mod_root_folder, "FireflyBodyPosition.BOOBS.buf")
    category_name_buf_file_path_dict["Texcoord"] = os.path.join(mod_root_folder, "XianyunTexcoord.buf")
    category_name_buf_file_path_dict["Blend"] = os.path.join(mod_root_folder, "XianyunBlend.buf")

    # trigger auto game type detect to know all the possible GameType it use.
    # we need a global config here to read gametype config json for us.
    # you only need to fill [GameName], it's the folder name in our Configs\GameTypes\ folder
    # our Configs\GameTypes\ folder contains every game's d3d11 gametype.
    g = GlobalConfig(
        # must specify gamename, which is your gametype config folder name.
        GameName="GI",
        # must specify where your config file is.
        ConfigFolderPath="D:\\Dev\\DBMT\\configs\\",
        # this GameLoaderPath is not necessary in mod reverse,but need it to create this class.
        GameLoaderPath="C:\\Users\\Administrator\\Desktop\\LoadersDev\\"
        )
    
    matched_gametypename_list = g.D3D11GameTypeConfig.detect_game_type(category_name_buf_file_path_dict=category_name_buf_file_path_dict,reverse=True)
    print(matched_gametypename_list)


    # Create mod output folder.
    output_folder_path = mod_root_folder + "Reverse\\"
    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)

    # combine fmt file for each game type and output final .vb file and just move ib file to there.
    for gametypename in matched_gametypename_list:
        d3d11gametype = g.D3D11GameTypeConfig.GameTypeName_D3D11GameType_Dict[gametypename]
        vb_bytearray = d3d11gametype.combine_buf_files_to_vb_file_bytearray(category_name_buf_file_path_dict)

        for ib_file_path in index_buffer_filepath_list:
            ib_filename = os.path.basename(ib_file_path)
            filename_prefix = d3d11gametype.GameTypeName + "-" + os.path.splitext(ib_filename)[0]

            # copy every ib file we specified to mod reverse folder.
            shutil.copy2(ib_file_path, os.path.join(output_folder_path,filename_prefix + ".ib"))

            # write our vb file, we only need 1 vb file for all .ib and .fmt file.
            # You may wonder why i use complete vb file? 
            # this will take more disk space and import extra vertices and more time spend on import, 
            # why i don't split it just like my other reverse tool?
            # Because I'm lazy! haha, will do it later, so add a TODO here.

            output_vb_filepath = os.path.join(output_folder_path,filename_prefix + ".vb")
            with open(output_vb_filepath, 'wb') as vb_file:  
                vb_file.write(vb_bytearray)  

            # write fmt file.
            output_fmt_filepath = os.path.join(output_folder_path, filename_prefix + ".fmt")
            fmt_file = FmtFile()
            fmt_file.D3d11GameTypeObj = d3d11gametype
            fmt_file.write_to_file(write_file_path=output_fmt_filepath,ib_stride=4,prefix=filename_prefix)


    

    