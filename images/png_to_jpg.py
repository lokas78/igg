#!/usr/local/bin/python3
import cv2, os

files = os.listdir()
for file in files:
    if file.endswith('.png'):
        img = cv2.imread(file)
        cv2.imwrite('{}.jpg'.format(file[:-4]), img)
