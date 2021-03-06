
import io
import os
import time
import base64
import cStringIO
from threading import Thread
from itertools import cycle

import numpy as np

from PIL import Image

import config


class BaseCamera(object):

    def __init__(self, resolution=config.CAMERA_RESOLUTION):
        self.resolution = resolution
        self.frame = np.zeros(
            shape=(
                self.resolution[1],
                self.resolution[0],
                3))
        self.frame_time = 0
        self.base64_time = 0

    def start(self):
        # start the thread to read frames from the video stream
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        time.sleep(1)
        return self

    def update(self):
        while True:
            pass

    def read(self):
        return self.frame

    def capture_arr(self):
        return self.read()

    def capture_img(self):
        arr = self.capture_arr()
        img = Image.fromarray(arr, 'RGB')
        return img

    def capture_base64(self):
        if self.frame_time > self.base64_time:
            buffer = cStringIO.StringIO()
            img = self.capture_img()
            img.save(buffer, format="JPEG")
            base64_buffer = base64.b64encode(buffer.getvalue())
            self.base64_buffer = base64_buffer
            self.base64_time = time.time()
        else:
            base64_buffer = self.base64_buffer    
        return base64_buffer



class PiVideoStream(BaseCamera):
    def __init__(self, resolution=config.CAMERA_RESOLUTION, 
                framerate=config.CAMERA_FRAMERATE, **kwargs):
        from picamera.array import PiRGBArray
        from picamera import PiCamera

        super(PiVideoStream, self).__init__(resolution, **kwargs)

        # initialize the camera and stream
        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        self.camera.rotation = 90  # TODO: move to settings
        self.rawCapture = PiRGBArray(self.camera, size=resolution)

        # initialize the frame and the variable used to indicate
        # if the thread should be stopped
        self.frame = None
        self.stopped = False

        print('PiVideoStream loaded.. .warming camera')

        time.sleep(2)
        self.start()

    def update(self):
        # keep looping infinitely until the thread is stopped
        for f in self.camera.capture_continuous(
                self.rawCapture, format="rgb", use_video_port=True):
            # grab the frame from the stream and clear the stream in
            # preparation for the next frame
            self.frame = f.array
            self.rawCapture.truncate(0)
            self.frame_time = time.time()

            # if the thread indicator variable is set, stop the thread
            # and resource camera resources
            if self.stopped:
                self.stream.close()
                self.rawCapture.close()
                self.camera.close()
                return

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True

