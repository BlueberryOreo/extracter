import os
import shutil
import subprocess
import json
from util import *
from tqdm import tqdm

def extract(file_path, conf, tmp_dir="tmp", ext="pimg"):
    files = os.listdir(file_path)
    os.makedirs(tmp_dir, exist_ok=True)

    expimg = conf["expimg"]
    tlg2png = conf["tlg2png"]

    for f_raw in tqdm(files):
        if not f_raw.endswith(ext):
            continue
        
        out_path = os.path.join(file_path, os.path.basename(f_raw) + "_ext")
        os.makedirs(out_path, exist_ok=True)
        clear_dir(tmp_dir)
        clear_dir(out_path)

        shutil.copy(os.path.join(file_path, f_raw), os.path.join(tmp_dir, f_raw))
        # subprocess.run([expimg, os.path.join(tmp_dir, f_raw)])
        solve_pimg(expimg, os.path.join(tmp_dir, f_raw))
        os.remove(os.path.join(tmp_dir, f_raw))
        for f_mid in os.listdir(tmp_dir):
            # result = subprocess.run([tlg2png, os.path.join(tmp_dir, f_mid), os.path.join(out_path, os.path.basename(f_mid) + ".png")],
            #                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if solve_tlg(tlg2png, os.path.join(tmp_dir, f_mid), os.path.join(out_path, os.path.basename(f_mid) + ".png")):
                shutil.copy(os.path.join(tmp_dir, f_mid), os.path.join(out_path, f_mid))
    shutil.rmtree(tmp_dir)

if __name__ == "__main__":
    data_path = "../evimage1080"
    config = get_config()
    extract(data_path, config)
    # clear_dir("tmp")
