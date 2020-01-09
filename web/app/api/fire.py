import cv2
import json
import uuid
import numpy as np
from . import api
from web.app.api.response import response
from web.app.api.config import status_code, API_V1_PREFIX
from flask import request
from fire_net.yolo import detect_fire


@api.route(API_V1_PREFIX['fire'] + '/detect', methods=['POST'])
def api_v1_detect():
    request_data = request.get_json()

    if 'image' not in request_data:
        return response(status_code.DATA_FORMAT_ERROR, message='Cannot find image')

    if request_data['image']:
        img = request_data['image']
    else:
        raise ValueError('image is none')
    img = np.array(json.loads(img), dtype=np.uint8)

    detect_data = detect_fire(img)

    if not detect_data['is_fire']:
        return response(status_code.SUCCESS, message='Cannot detect fire', response_data={'is_fire': False})

    response_data = {'is_fire': True, 'box': detect_data['box']}

    return response(status_code.SUCCESS, message='Detect fire!', response_data=response_data)


@api.route(API_V1_PREFIX['fire'] + '/upload', methods=['POST'])
def api_v1_upload():
    request_data = request.get_json()

    if 'image' not in request_data or 'is_fire' not in request_data:
        return response(status_code.DATA_FORMAT_ERROR, message='Cannot find image')

    status_file = 'web/app/data/status.txt'
    img_name = str(uuid.uuid4())

    with open(status_file, 'w') as f:
        status = 1 if request_data['is_fire'] else 0
        f.write('Fire=%dxxxx\nName=%s\n' % (status, img_name))
        f.close()

    if not request_data['is_fire']:
        return response(status_code.SUCCESS, message='Upload status to NO FIRE')

    img = np.array(json.loads(request_data['image']), dtype=np.uint8)

    cv2.imwrite('web/app/data/%s.jpg' % img_name, img)

    return response(status_code.SUCCESS, message='Upload status to FIRE')
