import os
import subprocess
import base64
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="将修改后的 dump.txt 转换为 Base64 代码文本")
    parser.add_argument("-i", "--input", default="dump.txt", help="输入的 dump 文本文件路径 (默认: dump.txt)")
    parser.add_argument("-o", "--output", default="output_base64.txt", help="输出的 Base64 文本文件路径 (默认: output_base64.txt)")
    
    args = parser.parse_args()
    
    input_file = args.input
    output_file = args.output
    temp_bin = "temp_payload.bin"
    
    # 注入一个基础的 Vega10 二进制骨架，因为 upp undump 需要修改现有的 bin 文件而不是从零创建
    skeleton_b64 = "pwIIAQBcAO8GAAAOLAAAGwBIAAAAgKkDAPBJAgDO/wgAAAAAAAAAAAAAAAAAAAIBXABAAjcClACPAbQAHgF6AIwArQEAAAAAYwIAAJAAmQJeATQBiAFoNgIAcQICAgAAAAAAAAgAAAAAAAAABQAHAAMABQAAAAAAAAABCCADhAO2A+gDGgRMBH4EsAQBAeIEAQGEAwAGYOoAAABAGQEAAdxKAQACAHcBAAOQkQEABWywAQAHAQjQTAEAAACAAAAAAAAAHIMBAAEAAAAAAAAAAPCaAQABAAAAAAAAAAB4rgEAAgAAAAAAAAAAAMIBAAIAAAAAAAAAAADCAQACAAAAAAEAAAAAwgEAAgAAAAABAAAAAMIBAAIAAAAAAQAAAAAEYOoAAABAGQEAANxKAQAAkF8BAAAACChuAAAALMkAAAH4CwEAAoA4AQADkF8BAAT0kQEABdCwAQAGwNQBAAcACGw5AAAAJF4AAAH8hQAAAqy8AAADNNAAAARobgEABQiXAQAG7KMBAAcAAWg8AQAAAQQ8QQAAAAAAUMMAAAAAAFDDAAAAAABQwwAAAAAAAQgAmIUAAEC1AABg6gAAUMMAAAGAuwAAYOoAAJQLAQBQwwAAAnj/AABAGQEAtCcBAFDDAAADtCcBANxKAQDcSgEAUMMAAASAOAEAkF8BANxKAQBQwwAABdxKAQAAdwEAkF8BAFDDAAAGAHcBAAB3AQCQXwEAUMMAAAcAdwEAkJEBAAB3AQBQwwAAARgAAAAAAAAAC+QSYAlgCUsACgBUA5ABkAGQAZABkAGQAZABAAAAAAACBDEHpQClAKUALAEAAFkAaQBKAEoAXwBzAHMAZABAAJCSl2CWAJBVAAAAAAAAAAAAAAAAAAAAAAACAtQwAAACEGDqAAACEA=="
    with open(temp_bin, "wb") as f:
        f.write(base64.b64decode(skeleton_b64))
    
    if not os.path.exists(input_file):
        print(f"错误: 找不到输入文件 '{input_file}'")
        sys.exit(1)
        
    print(f"正在读取 '{input_file}' 并通过 upp 重新封包...")
    
    # 使用我们在聊天文件夹下创建的虚拟环境中的 upp 绝对路径
    upp_path = "/Users/qian/Desktop/聊天/venv/bin/upp"
    
    if not os.path.exists(upp_path):
        print(f"错误: 找不到 upp 执行文件。请确保虚拟环境存在于: {upp_path}")
        sys.exit(1)

    try:
        subprocess.run([upp_path, "-p", temp_bin, "undump", "-d", input_file, "--write"], check=True)
    except subprocess.CalledProcessError:
        print("错误: upp 打包失败！请检查您的 dump.txt 格式是否被破坏，或者确保 upp 工具已安装并可用。")
        sys.exit(1)
    except FileNotFoundError:
        print("错误: 找不到 'upp' 命令。请确保当前环境已安装并激活了 upp。")
        sys.exit(1)
        
    print("打包成功，正在生成 Base64 代码...")
    
    # 读取生成的二进制文件并转换为 Base64
    try:
        with open(temp_bin, "rb") as f:
            binary_data = f.read()
            
        b64_encoded = base64.b64encode(binary_data).decode('utf-8')
        
        # 写入最终的文本文件
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(b64_encoded)
            
        print(f"\n🎉 转换完成！\n全新的 Base64 代码已保存至: {os.path.abspath(output_file)}")
        print(f"您可以直接打开该文件并复制里面的代码。")
        
    except Exception as e:
        print(f"转换 Base64 时发生错误: {e}")
    finally:
        # 清理临时生成的 bin 文件
        if os.path.exists(temp_bin):
            os.remove(temp_bin)

if __name__ == "__main__":
    main()
