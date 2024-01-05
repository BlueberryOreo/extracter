import cv2
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
import os, shutil

from util import zip_file, get_imgfile_dict


def solve_conf(conf_file, file_path):
    """
        {
            image_width,
            image_height,
            images: {
                ev_label: {sub_ev_label: {}, sub_ev_label: {}, ...},
                ev_label: {sub_ev_label: {}, sub_ev_label: {}, ...},
                ...
            }
        }
    """
    assert conf_file.endswith("txt"), "Error: the config file is not a text file"
    ret = {}
    imgfile_dict = get_imgfile_dict(file_path)
    with open(conf_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        img_info = lines[0].strip().split(':') + lines[1].strip().split(':')
        ret[img_info[0]] = int(img_info[1])
        ret[img_info[2]] = int(img_info[3])
        # print(ret)
        ret["images"] = {}
        tmp_info = {}
        for line in lines[2:]:
            line = line.strip()
            if not line:
                if tmp_info:
                    label = tmp_info["name"]
                    tmp_info["name"] = imgfile_dict[tmp_info["layer_id"]]
                    if not ret["images"].get(label[0]):
                        ret["images"][label[0]] = {label[1]: tmp_info.copy()}
                    else:
                        ret["images"][label[0]][label[1]] = tmp_info.copy()
                tmp_info.clear()
                continue
            left, right = map(str.strip, line.split(':'))

            try:
                right = int(right)
            except:
                pass

            tmp_info[left] = right
        
    return ret

def merge_img(fimg1, fimg2, posx, posy) -> Image:
    """
        paste img2 to img1[posx, posy]
    """
    img1 = Image.open(fimg1)
    img2 = Image.open(fimg2)

    # 确保第一张图片的模式为 "RGBA"，带有透明通道
    if img1.mode != 'RGBA':
        img1 = img1.convert('RGBA')

    # 确保第二张图片的模式为 "RGBA"，带有透明通道
    if img2.mode != 'RGBA':
        img2 = img2.convert('RGBA')
    # print(posx, posy)
    img1.paste(img2, (posx, posy), img2)
    return img1

def merge(file_path, out_path):
    conf_file = list(filter(lambda x: x.strip().endswith(".txt"), os.listdir(file_path)))[0]
    # print(conf_file)
    conf = solve_conf(os.path.join(file_path, conf_file), file_path)
    if not os.path.exists(out_path):
        os.mkdir(out_path)
    # img_width, img_height = conf["image_width"], conf["image_height"]
    images = conf["images"]
    for label, set_image in images.items():
        raw_image = set_image['a']
        # print(raw_image)
        raw_path = os.path.join(file_path, raw_image["name"])
        shutil.copy(raw_path, os.path.join(out_path, label + "a.png"))
        for k in set_image:
            if k == 'a':
                continue
            image = set_image[k]
            iamge_path = os.path.join(file_path, image["name"])
            res = merge_img(raw_path, iamge_path, posx=image["left"], posy=image["top"])
            out_f = os.path.join(out_path, label + k + ".png")
            if os.path.exists(out_f):
                os.remove(out_f)
            res.save(out_f)
    zip_out = os.path.join(file_path, "{}.zip".format(os.path.basename(file_path)))
    print("zipping: {}".format(zip_out))
    zip_file(zip_out, [out_path])
    shutil.rmtree(out_path)

if __name__ == "__main__":
    # merge("./", "./")
    # exit()
    # conf = solve_conf("./ev101a+pimg+layers.txt", "./")
    # img_width, img_height = conf["image_width"], conf["image_height"]
    # images = conf["images"]
    # out_path = "./"
    # for label, set_image in images.items():
    #     raw_image = set_image['a']
    #     # print(raw_image)
    #     for k in set_image:
    #         if k == 'a':
    #             continue
    #         image = set_image[k]
    #         res = merge_img(raw_image["name"], image["name"], posx=image["left"], posy=image["top"])
    #         out_f = os.path.join(out_path, label + k + ".png")
    #         if os.path.exists(out_f):
    #             os.remove(out_f)
    #         res.save(out_f)
    merge("../evimage1080/ev110a.pimg_ext", "../evimage1080/ev110a.pimg_ext/merge_out")
    pass
