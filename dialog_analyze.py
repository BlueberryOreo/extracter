import json
import os
import re
from tqdm import tqdm

from util import get_config, solve_scn

class Script:
    def __init__(self, character, comment, content) -> None:
        self.character = character
        self.comment = comment
        self.content = content
    
    def __str__(self) -> str:
        text = None
        if self.character or self.comment:
            speaker = self.character
            if self.comment:
                speaker = "【{}】".format(self.comment)
            text = "{:<6}:{:<}".format(speaker, self.content)
        else:
            text = "  {}".format(self.content)
        text = text.replace(" ", "　")
        return text

class Node:
    def __init__(self, block: dict) -> None:
        self.label = block.get("label")
        self.target = [(nxt["storage"], nxt.get("target")) for nxt in block["nexts"]]
        self.indegree = 0

class SelectNode:
    def __init__(self, text, storage, target) -> None:
        self.text = text
        self.target = (storage, target)
    
    def __str__(self) -> str:
        ret = "{} => {}:{}".format(self.text, *self.target)
        return ret.replace(" ", "　")

class TextNode(Node):
    def __init__(self, block: dict) -> None:
        texts = block.get("texts")
        assert texts, "The block {} does not contain dialogs.".format(block.get("label"))
        super().__init__(block)
        # self.label = block.get("label")
        self.texts: list = self.get_texts(texts)
        # self.target = (block["nexts"][0]["storage"], block["nexts"][0]["target"])
        # self.indegree = 0

    def get_texts(self, texts) -> list:
        # print(len(texts))
        ret = []
        for text in texts:
            ret.append(Script(*text[:3]))
        return ret

class Selections:
    def __init__(self, block: dict) -> None:
        selects = block.get("selects")
        assert selects, "The block {} does not contain selection.".format(block.get("label"))
        self.label = block.get("label")
        self.selections: list = self.get_selects(selects)
        self.indegree = 0

    def __str__(self) -> str:
        ret = "<====selection====>\n"
        for idx, selection in enumerate(self.selections):
            ret += "{}: {}\n".format(idx + 1, selection)
        ret += "<=================>"
        return ret.replace(" ", "　")
    
    def get_selects(self, selects) -> list:
        ret = []
        for select in selects:
            ret.append(SelectNode(select["text"], select["storage"], select["target"]))
        return ret

def get_dialogs(scenes, current_file) -> (dict, str):
    ret = {}
    start = None
    # print(len(scenes))
    for scene in scenes:
        if scene.get("texts"):
            text_node = TextNode(scene)
            ret[text_node.label] = text_node
            # for text in text_node.texts:
            #     print(text_node.label, text)
            if not start:
                start = text_node.label
        elif scene.get("selects"):
            selects = Selections(scene)
            ret[selects.label] = selects
        else:
            node = Node(scene)
            ret[node.label] = node
    # print(current_file, ret.keys())
    # exit()
    for nodek in ret:
        # print(nodek, ret[nodek])
        node = ret[nodek]
        # print(node.label, node.target)
        if isinstance(node, Selections):
            for select_node in node.selections:
                if select_node.target[0] != current_file:
                    continue
                ret[select_node.target[1]].indegree += 1
        else:
            for target in node.target:
                if target[0] != current_file:
                    continue
                ret[target[1]].indegree += 1
    # exit()
    return ret, start

def generate(dialogs, current_key, outf, select_label=None, select_text=None):
    node = dialogs[current_key]
    node.indegree -= 1
    if node.indegree > 0:
        return
    
    if isinstance(node, TextNode):
        if select_label:
            outf.write("{} - {}:\n".format(select_label, select_text))
        for text in node.texts:
            outf.write("{}\n".format(text))
        if select_label:
            outf.write("<{}>\n".format("=" * 20))
    elif isinstance(node, Selections):
        outf.write("\n{}\n\n".format(node))
        for select in node.selections:
            # outf.write("<{}>\n".format("=" * 20))
            if select.target[0] != dialogs["current_file"]:
                outf.write("=>To Chapter: {}\n".format(select.target[0]))
            else:
                generate(dialogs, select.target[1], outf, select.target[1], select.text)
        return

    # print(node.target)
    for target in node.target:
        if target[0] != dialogs["current_file"]:
            outf.write("~ Next Chapter: {}\n".format(target[0]))
            continue
        generate(dialogs, target[1], outf)

def solve_dialogs(file_path, out_path):
    assert os.path.exists(file_path), "Cannot find dialog file {}".format(file_path)
    
    with open(file_path, encoding="utf-8") as d:
        data = json.load(d)
    # print(data.keys())
    scenes = data["scenes"]
    # print(len(scenes))
    # for scene in scenes:
    #     if not scene.get("texts"):
    #         continue
    #     print(scene.get("texts")[0])
    # return
    
    current_file = ".".join(os.path.basename(file_path).split(".")[:-1])
    chapter_name = current_file.split("ver")[0]
    chapter_name = chapter_name.split("・")[-1]
    chapter = scenes[-1]["title"].replace("　", " ")
    next_chap = scenes[-1]["nexts"][0]["storage"].split("var")[0]
    next_chap = next_chap.split("・")[-1]
    dialogs, start = get_dialogs(scenes, current_file)
    dialogs["current_file"] = current_file
    # print(dialogs)
    out_file = os.path.join(out_path, "{}・{}.txt".format(chapter, chapter_name))
    # print(out_file)
    with open(out_file, "wt", encoding="utf-8") as outf:
        outf.write("{} —— {}\n\n".format(chapter, chapter_name))
        generate(dialogs, start, outf)
        # outf.write("~ Next Chapter: {}\n".format(next_chap))
    # print(next_chaps)
    

def extract_dialogs(root_path, out_path):
    if not os.path.exists(out_path):
        os.mkdir(out_path)

    files = list(filter(lambda x: x.endswith(".ks.scn"), os.listdir(root_path)))
    config = get_config()
    psb_decompiler = config["psb_decompile"]
    print("Decompiling dialog files...")
    for file in tqdm(files):
        file_path = os.path.join(root_path, file)
        assert not solve_scn(psb_decompiler, file_path), "Decompiler Error: file {}.".format(file_path)
        json_name = ".".join(file.split(".")[:-1]) + ".json"
        json_path = os.path.join(root_path, json_name)
        solve_dialogs(json_path, out_path)
    
    print("Deleting temp files...")
    for file in tqdm(os.listdir(root_path)):
        if file.endswith(".json"):
            os.remove(os.path.join(root_path, file))
    pass

if __name__ == "__main__":
    extract_dialogs("../patch", "../dialog_out")
    # solve_dialogs("./FreeMoteToolkit/013・欠片集めver1.06.ks.json", "../dialog_out")
    pass

"""
scn file format:
{
    hash,
    name, - file name
    outlines,
    scenes:[
        {
            label, - the label of the scene
            nexts:[
                {
                    storage, - target file name
                    target, - target label
                    ...,
                },
                {
                    storage,
                    target,
                    ...,
                },
                ...
            ], - if current scene has more than one next scenes, then len(nexts) > 1
            (selects), - if the scene is a selection
            (texts), - if the scene has dialogs
            ...
        },
        {...},
        {...},
        ...
    ]
}
"""