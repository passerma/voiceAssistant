import snowboydecoder
import signal
import wave
import sys
import json
import requests
import time
import os
import base64
from pyaudio import PyAudio, paInt16
import webbrowser
from fetchToken import fetch_token

interrupted = False  # snowboy监听唤醒结束标志
endSnow = False  # 程序结束标志

framerate = 16000  # 采样率
num_samples = 2000  # 采样点
channels = 1  # 声道
sampwidth = 2  # 采样宽度2bytes
FILEPATH = './audio/audio.wav'  # 录制完成存放音频路径

TTS_URL = 'http://tsn.baidu.com/text2audio'  # 文字转语音接口

music_exit = './audio/exit.wav'  # 唤醒系统退出语音
music_open = './audio/open.wav'  # 唤醒系统打开语音
os.close(sys.stderr.fileno())


def signal_handler(signal, frame):
    """
    监听键盘结束
    """
    global interrupted
    interrupted = True


def interrupt_callback():
    """
    监听唤醒
    """
    global interrupted
    return interrupted


def detected():
    """
    唤醒成功
    """
    print('唤醒成功')
    play('./audio/open.wav')
    global interrupted
    interrupted = True
    detector.terminate()


def play(filename):
    """
    播放音频
    """
    wf = wave.open(filename, 'rb')  # 打开audio.wav
    p = PyAudio()                   # 实例化 pyaudio
    # 打开流
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)
    data = wf.readframes(1024)
    while data != b'':
        data = wf.readframes(1024)
        stream.write(data)
    # 释放IO
    stream.stop_stream()
    stream.close()
    p.terminate()


def save_wave_file(filepath, data):
    """
    存储文件
    """
    wf = wave.open(filepath, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(sampwidth)
    wf.setframerate(framerate)
    wf.writeframes(b''.join(data))
    wf.close()


def my_record():
    """
    录音
    """
    pa = PyAudio()
    stream = pa.open(format=paInt16, channels=channels,
                     rate=framerate, input=True, frames_per_buffer=num_samples)
    my_buf = []
    # count = 0
    t = time.time()
    print('开始录音...')
    while time.time() < t + 4:  # 秒
        string_audio_data = stream.read(num_samples)
        my_buf.append(string_audio_data)
    print('录音结束!')
    save_wave_file(FILEPATH, my_buf)
    stream.close()


def speech2text(speech_data, token, dev_pid=1537):
    """
    音频转文字
    """
    FORMAT = 'wav'
    RATE = '16000'
    CHANNEL = 1
    CUID = 'baidu_workshop'
    SPEECH = base64.b64encode(speech_data).decode('utf-8')
    data = {
        'format': FORMAT,
        'rate': RATE,
        'channel': CHANNEL,
        'cuid': CUID,
        'len': len(speech_data),
        'speech': SPEECH,
        'token': token,
        'dev_pid': dev_pid
    }
    url = 'https://vop.baidu.com/pro_api'
    headers = {'Content-Type': 'application/json'}
    print('正在识别...')
    r = requests.post(url, json=data, headers=headers)
    Result = r.json()
    if 'result' in Result:
        return Result['result'][0]
    else:
        return Result


def get_audio(file):
    """
    获取音频文件
    """
    with open(file, 'rb') as f:
        data = f.read()
    return data


def identifyComplete(text):
    """
    识别成功
    """
    print('识别内容成功，内容为:' + text)
    maps = {
        '打开百度': ['打开百度。', '打开百度', '打开百度，', 'baidu']
    }
    if (text == '再见。' or text == '拜拜。'):
        play(music_exit)  # 关闭系统播放反馈语音
        exit()
    if text in maps['打开百度']:
        webbrowser.open_new_tab('https://www.baidu.com')
        play('./audio/openbaidu.wav')  # 识别到播放反馈语音
    else:
        play('./audio/none.wav')  # 未匹配口令播放反馈语音
    print('操作完成')


if __name__ == "__main__":
    while endSnow == False:
        interrupted = False
        detector = snowboydecoder.HotwordDetector('xm.pmdl', sensitivity=0.5)
        print('等待唤醒')
        detector.start(detected_callback=detected,
                       interrupt_check=interrupt_callback,
                       sleep_time=0.03)
        my_record()
        TOKEN = fetch_token()
        speech = get_audio(FILEPATH)
        result = speech2text(speech, TOKEN, int(80001))
        if type(result) == str:
            identifyComplete(result)
