# -*- coding: utf-8 -*-
# # *****************************************************
# システム名称：  センシングアップサンプルプログラム
#
# 改定履歴：     2021年 7月 16日 基本システム
#
# Copyright(C)  giaie inc.  ALL Right Reserved.
# *****************************************************

import base64
import json
import urllib.request
from datetime import datetime

import time
import serial
import binascii
import struct
import math
import traceback

from decimal import Decimal
from urllib.error import HTTPError

# 以下XXX部分には指定された文字と置き換え下さい。
URL = "https://XXXX.sensingapp.io/api/data/"

# ユーザーアカウント情報です。XXX部分を置き換え下さい。
user = "XXXXX@XXXXXX.XXX"
password = "XXXXXXXX"

# ユーザーID情報です。XXX部分を置き換え下さい。
USER_ID = "XXXXXXXXXX"

# 設定したセンサーの種別と番号にXX部分を置き換えて下さい。
ITEM = "XX"
ITEM_NUM = "XX"

# センシング間隔（秒）  必要に応じて変更してください。
INTERVAL_TIME = 60    # 1分ごと

# USBポート１つだけ利用することを前提としています。
SENSOR_USB = "/dev/ttyUSB0"

# センシングデータをTOCH指示計から取得
def get_data(device):

    try:
        ser = serial.Serial(device, baudrate='9600', timeout=None, stopbits=1, bytesize=8, parity='N')

        #print(ser) # for debug

        # Connect TOCH Sensors (pH, MLSS, DO)
        CMD = bytes.fromhex('0103000000044409')

        ser.write(CMD)
        time.sleep(1)
        data_all = ser.read_all()

        print(data_all) # for debug

        data_hex = binascii.hexlify(data_all)

        worker_id = int.from_bytes(binascii.a2b_hex(data_hex[0:2]),"little")
        func_cd = int.from_bytes(binascii.a2b_hex(data_hex[2:4]),"little")
        data_size = int.from_bytes(binascii.a2b_hex(data_hex[4:6]),"little")

        data_float = hex_to_float((data_hex[10:14]+data_hex[6:10]).decode())
        data = math.floor(data_float * 10 ** 2) / (10 ** 2)

        ser.close()

    except Exception:
        data = 0
        print(traceback.format_exc())  # for debug

    return data


def hex_to_float(s):
    if s.startswith('0x'):
        s = s[2:]
    s = s.replace(' ', '')
    return struct.unpack('>f', binascii.unhexlify(s))[0]


# センシングデータをサーバに送信
def send_data(data):

    obj = {
        "user_id": USER_ID,
        "item": ITEM,
        "item_num": ITEM_NUM,
        "regist_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "sensing_data": str(data),
    }
    json_data = json.dumps(obj).encode("utf-8")

    print(json_data) # for debug

    credentials = ('%s:%s' % (user, password))
    encoded_credentials = base64.b64encode(credentials.encode('ascii'))

    # httpリクエストを準備してPOST
    request = urllib.request.Request(URL, data=json_data, method="POST", headers={"Content-Type": "application/json", })
    request.add_header('Authorization', 'Basic %s' % encoded_credentials.decode("ascii"))

    try:
        with urllib.request.urlopen(request) as response:
            response_data = response.read().decode("utf-8")

    except Exception:
        response_data = 0
        print(traceback.format_exc())  # for debug

    return response_data


# 決められた時間間隔でのセンシング
def main():

    try:
        while True:
            # 開始時刻を記録
            start_time = time.time()

            sensing_data = get_data(SENSOR_USB) # 指定のUSBからのデータを取得する。
            print(sensing_data)  # for debug

            if sensing_data != 0 : # 正常に数値を取得したらデータを処理する。
                response_data = send_data(sensing_data)  # データをクラウドに送信する。
                print(response_data) # for debug
                # 終了時刻を記録
                stop_time = time.time()
                # (INTERVAL_TIME - 送信にかかった時間)秒待ってループ
                wait = start_time - stop_time + INTERVAL_TIME
                if wait > 0:
                    time.sleep(wait)

            # キーボード例外を検出
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
