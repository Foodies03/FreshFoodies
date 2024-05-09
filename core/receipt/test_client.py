from __future__ import print_function
import requests
import json
import cv2
import base64
import io
import numpy as np
from PIL import Image
import random, string

def randomword(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

# addr = 'http://127.0.0.1:5000'
addr = 'exp://192.168.1.34:8081'
test_url = addr + '/api/receipt'

# prepare headers for http request
content_type = 'image/jpeg'
headers = {'content-type': content_type, 'debug': 'true'}

img = cv2.imread('rc_3.jpg')
# encode image as jpeg
_, img_encoded = cv2.imencode('.jpg', img)

# send http request with image and receive response
response = requests.post(test_url, data=base64.b64encode(img_encoded), headers=headers).json()
# decode response

encoded_img_bw = response['img_bw'][1:]

# print(encoded_img[:20])

decoded_bw = base64.b64decode(encoded_img_bw)

with open('test_bw_' + randomword(5) + ".jpg", 'wb') as f_output:
    f_output.write(decoded_bw)

print(response['text'])