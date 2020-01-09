import logging
from . import api
from web.app.api.response import response
from web.app.api.config import status_code, API_V1_PREFIX
from flask import request
from fire_net.yolo import detect_fire


@api.route(API_V1_PREFIX['fire'] + '/detect', methods=['POST'])
def api_v1_upload_img():
    request_data = request.get_json()
    img = request_data['image']

    detect_data = detect_fire(img)

    if not detect_data['is_fire']:
        return response(status_code.SUCCESS, message='Cannot detect fire', response_data={'is_fire': False})

    return response(status_code.SUCCESS, message='Detect fire!', response_data={'is_fire': True, 'box': detect_data['box']})
