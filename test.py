import cv2
import requests
import json
import time


if __name__ == '__main__':
    img = cv2.imread('test1.jpg')
    img_r1 = cv2.pyrDown(img)
    img_r2 = cv2.pyrDown(img_r1)

    s = time.time()
    data = json.dumps(img_r2.tolist(), separators=(',', ':'), sort_keys=True, indent=4)
    resp = requests.post(url='http://localhost:10008/api/v1/fire/detect', json={'image': data})
    resp_data = json.loads(resp.content)['data']

    print('detect image time = %.2f' % (time.time() - s))

    if resp_data['is_fire']:
        red = (0, 0, 255)
        box = resp_data['box']
        left, top, right, bottom = box[0] * 2, box[1] * 2, box[2] * 2, box[3] * 2

        img_r1 = cv2.rectangle(img_r1, (left, top), (right, bottom), red, 4)
        img_r1 = cv2.putText(img_r1, 'Fire', (left, top - 10), cv2.FONT_HERSHEY_COMPLEX, 1.2, red, 1)

        s = time.time()

        data = json.dumps(img_r1.tolist(), separators=(',', ':'), sort_keys=True, indent=4)
        resp = requests.post(url='http://localhost:10008/api/v1/fire/upload', json={'is_fire': True, 'image': data})

        print('upload image time = %.2f' % (time.time() - s))
