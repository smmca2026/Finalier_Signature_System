import cv2
import os

reference_folder="static/reference"

def orb_predict(test_image):

    orb = cv2.ORB_create(1000)

    test = cv2.imread(test_image,0)
    kp2, des2 = orb.detectAndCompute(test,None)

    scores=[]

    for file in os.listdir(reference_folder):

        path=os.path.join(reference_folder,file)

        ref=cv2.imread(path,0)

        kp1, des1 = orb.detectAndCompute(ref,None)

        bf=cv2.BFMatcher(cv2.NORM_HAMMING)

        matches=bf.match(des1,des2)

        matches=sorted(matches,key=lambda x:x.distance)

        score=len(matches)/max(len(kp1),1)

        scores.append(score)

    return max(scores)