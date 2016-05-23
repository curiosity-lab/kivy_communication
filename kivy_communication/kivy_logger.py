#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import socket

is_pycrypto = True
try:
    from Crypto.PublicKey import RSA
except:
    print('no pycrypto')
    is_pycrypto = False
from datetime import datetime
from kivy.logger import Logger
from kivy.storage.jsonstore import JsonStore
from kivy.uix.widget import Widget
from os.path import join


class DataMode:
    file = 'file'
    encrypted = 'encrypted'
    communication = 'communication'


class LogAction:
    none = 'none'
    press = 'press'
    play = 'play'
    stop = 'stop'
    move = 'move'
    down = 'down'
    up = 'up'
    text = 'text'
    spinner = 'spinner'
    data = 'data'


class KL:
    log = None

    @staticmethod
    def start(mode=None, pathname=''):
        KL.log = KivyLogger
        KL.log.pathname = pathname
        print(pathname)
        if mode is None:
            mode = []
            Logger.info("KL mode:" + str(mode))
        KL.log.set_mode(mode)


class KivyLogger:
    logs = []
    t0 = None
    base_mode = []
    socket = None
    public_key = None
    filename = None
    pathname = ''
    store = None

    @staticmethod
    def __init__():
        KivyLogger.logs = []
        KivyLogger.t0 = datetime.now()


    @staticmethod
    def __del__():
        if KivyLogger.socket is not None:
            KivyLogger.socket.close()


    @staticmethod
    def set_mode(mode):
        KivyLogger.base_mode = mode
        KivyLogger.t0 = datetime.now()
        if DataMode.file in KivyLogger.base_mode:
            KivyLogger.filename = join(KivyLogger.pathname,
                                       KivyLogger.t0.strftime('%Y_%m_%d_%H_%M_%S_%f') + '.log')
            KivyLogger.store = JsonStore(KivyLogger.filename)
            Logger.info("KivyLogger: " + str(KivyLogger.filename))

        if DataMode.communication in KivyLogger.base_mode:
            KivyLogger.connect()

        if not is_pycrypto:
            if DataMode.encrypted in KivyLogger.base_mode:
                KivyLogger.base_mode.remove(DataMode.encrypted)

        if DataMode.encrypted in KivyLogger.base_mode:
            KivyLogger.get_public_key()
            KivyLogger.save('public_key:' + KivyLogger.public_key.exportKey("PEM"))

    @staticmethod
    def connect():
        try:
            KivyLogger.socket = socket.socket()
            host = socket.gethostbyaddr('192.168.43.70')
            Logger.info(("host:" + str(host)))
            port = 12345
            KivyLogger.socket.connect((host[0], port))
        except:
            KivyLogger.base_mode.remove(DataMode.communication)
            Logger.info("connect: fail")
        pass

    @staticmethod
    def get_public_key():
        if DataMode.communication in KivyLogger.base_mode:
            # get from communication
            pub_pem = KivyLogger.socket.recv(1024)
        else:
            private_key = RSA.generate(2048, e=65537)
            prv_pem = private_key.exportKey("PEM")
            store = JsonStore(KivyLogger.filename + '.enc')
            store.put('private_key', pem=prv_pem)

            pub_pem = private_key.publickey().exportKey("PEM")

        KivyLogger.public_key = RSA.importKey(pub_pem)
        pass

    @staticmethod
    def reset():
        KivyLogger.logs = []
        KivyLogger.t0 = datetime.now()

    @staticmethod
    def insert(action=LogAction.none, obj='', comment='', t=None, mode=None):
        if t is None:
            t = datetime.now()
        data = {'time':t, 'action':action, 'obj':obj, 'comment':comment}
        KivyLogger.logs.append(data)
        if not mode:
            mode = KivyLogger.base_mode

        data_str = KivyLogger.to_str(data)

        if DataMode.encrypted in mode:
            data_str = KivyLogger.encrypt(data_str)

        if DataMode.communication in mode:
            KivyLogger.send_data(data_str)

        if DataMode.file in mode:
            KivyLogger.save(data_str)


    @staticmethod
    def save(data_str):
        #print(data_str)
        try:
            if DataMode.encrypted in KivyLogger.base_mode:
                KivyLogger.store.put(datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f'),
                                     data=str(data_str).encode('ascii'))
            else:
                KivyLogger.store.put(datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f'),
                                     data=data_str)
            Logger.info("save:" + str(KivyLogger.filename))
        except:
            Logger.info("save: did not work")

    @staticmethod
    def to_str(log):
        data = {'time': log['time'].strftime('%Y_%m_%d_%H_%M_%S_%f'),
                'action': log['action'],
                'obj': log['obj'],
                'comment': log['comment']}
        return str(json.dumps(data))

    @staticmethod
    def encrypt(data_str):
        if DataMode.encrypted in KivyLogger.base_mode:
            data_str = KivyLogger.public_key.encrypt(data_str, 32)
            return data_str
        return data_str

    @staticmethod
    def send_data(data_str):
        if DataMode.communication in KivyLogger.base_mode:
            KivyLogger.socket.send(data_str.encode())
        pass


class WidgetLogger(Widget):
    name = ''

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.log_touch(LogAction.down, touch)
            super(WidgetLogger, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            #self.log_touch(LogAction.move, touch)
            super(WidgetLogger, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            self.log_touch(LogAction.up, touch)
            super(WidgetLogger, self).on_touch_up(touch)

    def on_press(self, *args):
        super(WidgetLogger, self).on_press(*args)
        KL.log.insert(action=LogAction.press, obj=self.name, comment='')

    def log_touch(self, action, touch):
        if KL.log is not None:
            Logger.info("KivyLogger log_touch:" + str(touch.profile))
            comment = {}
            if 'angle' in touch.profile:
                comment['angle'] = touch.a
            if 'pos' in touch.profile:
                comment['pos'] = str(touch.pos)
            if 'button' in touch.profile:
                comment['button'] = touch.button

            KL.log.insert(action=action, obj=self.name, comment=json.dumps(comment))

    def on_play_wl(self, filename):
        KL.log.insert(action=LogAction.play, obj=self.name, comment=filename)

    def on_stop_wl(self, filename):
        KL.log.insert(action=LogAction.stop, obj=self.name, comment=filename)

    def on_text_change(self, instance, value):
        KL.log.insert(action=LogAction.text, obj=self.name, comment=self.text)

    def on_spinner_text(self, instance, value):
        KL.log.insert(action=LogAction.spinner, obj=self.name, comment=value)
