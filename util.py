import json
import os, shutil
import subprocess
import zipfile

def get_config(path="./config.json"):
    return json.load(open(path))

def clear_dir(path):
    for file in os.listdir(path):
        f = os.path.join(path, file)
        if os.path.isfile(f):
            os.remove(f)
        elif os.path.isdir(f):
            shutil.rmtree(f)

def solve_pimg(process: str, img_path) -> int:
    result = subprocess.run([process, img_path])
    return result.returncode

def solve_tlg(process: str, img_path, out_path) -> int:
    result = subprocess.run([process, img_path, out_path],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode

def solve_scn(process: str, file_path) -> int:
    result = subprocess.run([process, file_path],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode

def get_imgfile_dict(file_path, ext="png"):
    files = os.listdir(file_path)
    ret = {}
    for file in files:
        if not file.endswith(ext):
            continue
        try:
            file_id = int((file.split(".")[0]).split("+")[-1])
            # print(file_id, file)
            ret[file_id] = file
        except:
            pass
    return ret

def zip_file(out_path, files):
    with zipfile.ZipFile(out_path, "w") as zipf:
        for file_path in files:
            if os.path.isdir(file_path):
                for root, dirs, files in os.walk(file_path):
                    for file in files:
                        file_full_path = os.path.join(root, file)
                        arc_name = os.path.relpath(file_full_path, file_path)
                        zipf.write(file_full_path, arc_name)
            else:
                zipf.write(file_path, os.path.basename(file_path))