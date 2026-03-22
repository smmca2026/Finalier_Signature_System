import cv2
import numpy as np

def compare_signatures(img1_path, img2_path):

    img1 = cv2.imread(img1_path,0)
    img2 = cv2.imread(img2_path,0)

    img1 = cv2.resize(img1,(300,150))
    img2 = cv2.resize(img2,(300,150))

    orb = cv2.ORB_create()

    kp1, des1 = orb.detectAndCompute(img1,None)
    kp2, des2 = orb.detectAndCompute(img2,None)

    if des1 is None or des2 is None:
        return 0

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    matches = bf.match(des1,des2)

    similarity = len(matches) / max(len(kp1), len(kp2))

    score = similarity * 100

    return score