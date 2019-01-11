#  xcstrings.py
#
#  Created by Artem Shimanski on 12/29/18.
#  Copyright © 2018 Artem Shimanski.
#  License: MIT.


import re
import os
import subprocess
import tempfile
import sys
import getopt

help = "xcstrings.py -i <source_dir> [-i <source_dir>] -o <output_dir> [--ignore <keyword>] [--init] [--sort]"

try:
    opts, args = getopt.getopt(sys.argv[1:],"i:o:",["ignore=", "init", "sort"])

    input = [arg for opt, arg in opts if opt == "-i"]
    output = next((arg for opt, arg in opts if opt == "-o"), None)
    ignore = next((arg for opt, arg in opts if opt == "--ignore"), "#ignore")
    init = any(True for opt, arg in opts if opt == "--init")
    sortAll = any(True for opt, arg in opts if opt == "--sort")
    if not input or not output:
        print(help)
        exit(2)

except getopt.GetoptError:
    print(help)
    exit(2)


class LocalizedString:
    def __init__(self, match):
        self.comment = match[0] if match[0] != "" else None
        self.key = match[1]
        self.value = match[2]

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '/* {} */\n"{}" = "{}";'.format(self.comment, self.key, self.value)

pattern = re.compile(r'(?:/\*\s*(.*?)\s*\*/\n+)?\s*"((?:[^\\"]|\\.)*)"\s*=\s*"((?:[^\\"]|\\.)*)"\s*;', re.MULTILINE | re.DOTALL)
def load(filePath):
    encoding = subprocess.check_output(["file", "-b", "--mime-encoding", filePath]).decode("utf-8").strip(" \n")
    with open(filePath, "r", encoding = "utf-8" if encoding == "binary" else encoding) as f:
        return [LocalizedString(x) for x in pattern.findall(f.read())]

def save(filePath, strings):
    s = "\n" + "\n\n".join([i.__str__() for i in strings])
    with open(filePath, "w", encoding="utf-8") as f:
        f.write(s)

with tempfile.TemporaryDirectory() as tmp:
    paths = [os.path.join(folder, file) for folder, sub, files in os.walk(output) for file in files]
    paths = [i for i in paths if re.match(r".*\.lproj/[^/]*\.strings", i, re.IGNORECASE)]

    if not paths:
        print ("error: *.strings files not found")
        exit(2)

    files = [os.path.join(folder, file) for x in input for folder, sub, files in os.walk(x) for file in files]
    files = set(files)

    sources = [i for i in files if re.match(r".*\.((swift)|(h)|(m{1,2}))$", i, re.IGNORECASE)]
    interfaces = [i for i in files if re.match(r".*Base\.lproj/[^/]*\.((storyboard)|(xib))$", i, re.IGNORECASE)]

    if not sources and not interfaces:
        print ("error: source files not found")
        exit(2)

    subprocess.run(["xcrun", "extractLocStrings", "-o", tmp] + sources)
    for file in interfaces:
        dir, name = os.path.split(file)
        name, ext = os.path.splitext(name)
        subprocess.run(["ibtool", "--generate-strings-file", os.path.join(tmp, name + ".strings"), file])
    newStrings = {file: load(os.path.join(tmp, file)) for file in os.listdir(tmp)}


    for path in paths:
        strings = load(path) if not init else []
        try:
            new = newStrings[os.path.split(path)[1]]
        except:
            continue
        for string in strings:
            a = next((i for i in new if i.key == string.key), None)
            if a:
                string.comment = a.comment or string.comment
            elif "#unused" not in (string.comment or ""):
                string.comment = "#unused; " + (string.comment or "")

        new = [i for i in new if next((j for j in strings if i.key == j.key), None) is None]
        if sortAll:
            strings = strings + new
            strings = sorted(strings, key=lambda x: x.key)
        else:
            new = sorted(new, key=lambda x: x.key)
            strings = strings + new

        strings = [i for i in strings if ignore not in i.comment]
        save(path, strings)
