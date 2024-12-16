import os
import shutil
import tkinter as tk
from tkinter import filedialog
from core.common.buffer_file import IndexBufferBufFile, FmtFile
from core.common.global_config import GlobalConfig
from core.utils.dbmt_log_utils import log_newline

#v0.4 由 吃饼喝茶 利用 Microsoft Copilot 改写
#添加了IB文件名识别，现在运行只需要选择正确的目录即可。

# 手动反转3D模型文件，仅支持Unity顶点着色器的预皮肤处理mod反转。
# 原版稳定支持的游戏列表：原神、崩坏：星穹铁道、崩坏3、绝区零。
# 当前版本只在ZZZ环境下测试运行。其它游戏不确定。
def main():
    # 创建一个隐藏的Tkinter根窗口
    root = tk.Tk()
    root.withdraw()

    # 弹出文件夹选择对话框
    mod_root_folder = filedialog.askdirectory(title="请选择你的mod文件夹")

    # 检查目录路径是否存在
    if not os.path.exists(mod_root_folder):
        print(f"目录路径 '{mod_root_folder}' 不存在，程序终止。")
        return

    # 2. 检索当前目录下所有的 .ib 和 .buf 文件
    ib_files = [f for f in os.listdir(mod_root_folder) if f.endswith('.ib')]
    buf_files = [f for f in os.listdir(mod_root_folder) if f.endswith('.buf')]

    # 如果目录下没有 .ib 文件，给出提示并终止程序
    if not ib_files:
        print("目录下没有 .ib 文件，程序终止。")
        return

    # 3. 动态生成包含类别名和缓冲文件路径的字典
    def generate_buf_file_path_dict(ib_filename):
        # 提取文件名前缀（去掉最后的编号）
        base_name = os.path.splitext(ib_filename)[0][:-1]  # 去掉最后一个字符
        prefix = ''.join(filter(str.isalpha, base_name))  # 提取字母部分

        # 根据前缀匹配 .buf 文件
        position_buf = next((f for f in buf_files if f.startswith(prefix) and f.endswith('Position.buf')), None)
        texcoord_buf = next((f for f in buf_files if f.startswith(prefix) and f.endswith('Texcoord.buf')), None)
        blend_buf = next((f for f in buf_files if f.startswith(prefix) and f.endswith('Blend.buf')), None)

        return {
            "Position": os.path.join(mod_root_folder, position_buf) if position_buf else None,
            "Texcoord": os.path.join(mod_root_folder, texcoord_buf) if texcoord_buf else None,
            "Blend": os.path.join(mod_root_folder, blend_buf) if blend_buf else None
        }

    # 触发自动游戏类型检测，以了解它使用的所有可能的GameType。
    g = GlobalConfig(
        #游戏类型-必填项
        GameName="ZZZ",
        #必选目录，请根据源代码包所在路径进行选择-必填项
        ConfigFolderPath="D:\\3d_asset_project\\input_or_output_tools\\DBMT-1.0.9.1\\configs\\",
        #非必填项
        GameLoaderPath="G:\\games\\zzz_tool\\DBMT-Release-V1.0.9.1\\Games\\ZZZ\\3Dmigoto"
    )

    # 对每个索引缓冲区文件分别进行检测和处理
    for ib_filename in ib_files:
        category_name_buf_file_path_dict = generate_buf_file_path_dict(ib_filename)

        # 如果匹配到的 .buf 文件不存在，给出提示，继续运行
        if None in category_name_buf_file_path_dict.values():
            print(f"文件 '{ib_filename}' 没有找到匹配的 .buf 文件，跳过该文件。")
            continue

        matched_gametypename_list = g.D3D11GameTypeConfig.detect_game_type(category_name_buf_file_path_dict=category_name_buf_file_path_dict, reverse=True)
        print(matched_gametypename_list)

        # 创建mod输出文件夹。
        output_folder_path = os.path.join(mod_root_folder, "Reverse")
        os.makedirs(output_folder_path, exist_ok=True)

        # 为每个游戏类型组合fmt文件并输出最终的.vb文件，并将.ib文件移到那里。
        for gametypename in matched_gametypename_list:
            d3d11gametype = g.D3D11GameTypeConfig.GameTypeName_D3D11GameType_Dict[gametypename]
            vb_bytearray = d3d11gametype.combine_buf_files_to_vb_file_bytearray(category_name_buf_file_path_dict)

            filename_prefix = f"{d3d11gametype.GameTypeName}-{os.path.splitext(ib_filename)[0]}"

            # 将我们指定的每个.ib文件复制到mod反转文件夹。
            shutil.copy2(os.path.join(mod_root_folder, ib_filename), os.path.join(output_folder_path, f"{filename_prefix}.ib"))

            # 写入我们的.vb文件，我们只需要1个.vb文件来包含所有.ib和.fmt文件。
            output_vb_filepath = os.path.join(output_folder_path, f"{filename_prefix}.vb")
            with open(output_vb_filepath, 'wb') as vb_file:
                vb_file.write(vb_bytearray)

            # 写入fmt文件。
            output_fmt_filepath = os.path.join(output_folder_path, f"{filename_prefix}.fmt")
            fmt_file = FmtFile()
            fmt_file.D3d11GameTypeObj = d3d11gametype
            fmt_file.write_to_file(write_file_path=output_fmt_filepath, ib_stride=4, prefix=filename_prefix)

if __name__ == "__main__":
    main()
