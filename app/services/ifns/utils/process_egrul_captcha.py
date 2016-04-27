# -*- coding: utf-8 -*-
import os
import shlex
import shutil
import subprocess
import tempfile
import requests
from PIL import Image

def recognize_captcha(token):
    url = u"http://egrul.nalog.ru/static/captcha.html?a=" + token
    LEVEL = 1275
    ITERATIONS = 2
    GLOBAL_ITERATIONS = 10
    letters_result = [{}, {}, {}, {}, {}, {}]

    gi = 0
    while gi < GLOBAL_ITERATIONS:
        result = requests.get(url, stream=True, timeout=2)
        if not result or result.status_code!=200:
            print(u"Failed to load captcha image")
            return

        t_file_out = tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".gif")
        full_name = t_file_out.name
        t_file_out.close()
        file_path = full_name
        with open(file_path, 'wb') as f:
            result.raw.decode_content = True
            shutil.copyfileobj(result.raw, f)

        img = Image.open(file_path)
        img = img.convert("RGB")
        pixdata = img.load()

        width = img.size[0]
        height = img.size[1]
        for i in xrange(ITERATIONS):
            layer = []
            for x in xrange(1, width - 1):
                for y in xrange(1, height -1):
                    if pixdata[x, y][0] < 50:
                        continue
                    count = pixdata[x, y - 1][0]
                    count += pixdata[x, y + 1][0]
                    count += pixdata[x - 1, y - 1][0]
                    count += pixdata[x + 1, y - 1][0]
                    count += pixdata[x - 1, y + 1][0]
                    count += pixdata[x + 1, y + 1][0]
                    count += pixdata[x - 1, y][0]
                    count += pixdata[x + 1, y][0]
                    if count < LEVEL:
                        layer.append((x, y))

            for x, y in layer:
                pixdata[x, y] = (40, 40, 40, 255)

        t_file_out = tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".gif")
        out_full_name = t_file_out.name
        t_file_out.close()
        img.save(out_full_name)

        t_file_out = tempfile.NamedTemporaryFile(mode="w+", delete=True)
        text_full_name = t_file_out.name
        t_file_out.close()

        subprocess.call(shlex.split("tesseract -psm 7 %s %s digits" % (out_full_name, text_full_name)))
        os.unlink(file_path)
        os.unlink(out_full_name)
        with open(text_full_name + '.txt', 'r') as f:
            word = f.read().strip()
            if not word.isdigit() or len(word) != 6:
                pass
            else:
                print("Hit: %s" % word)
                gi += 1
                j = 0
                for letter in word:
                    if letter not in letters_result[j]:
                        letters_result[j][letter] = 1
                    else:
                        letters_result[j][letter] += 1

                    j += 1
        os.unlink(text_full_name + '.txt')
    word = ""
    for x in letters_result:
        c = sorted(x.items(), key = lambda y: y[1])
        word += c[-1][0]
    print(word)
    return word
