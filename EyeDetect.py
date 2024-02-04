import cv2 as cv
import numpy as np
import dlib
import math

# Define color constants
YELLOW = (0, 247, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


def midpoint(pts1, pts2):
    x, y = pts1
    x1, y1 = pts2
    return (int((x + x1) / 2), int((y1 + y) / 2))


def euclideanDistance(pts1, pts2):
    x, y = pts1
    x1, y1 = pts2
    return math.sqrt((x1 - x) ** 2 + (y1 - y) ** 2)


# face detector obj
detectFace = dlib.get_frontal_face_detector()

# calling the pre-trained model
predictor = dlib.shape_predictor("predictor/shape_predictor_68_face_landmarks.dat")


def faceDetector(image, gray, Draw=True):
    cordFace1 = (0, 0)
    cordFace2 = (0, 0)

    # getting faces from face detector
    faces = detectFace(gray)

    face = None

    for face in faces:
        cordFace1 = (face.left(), face.top())
        cordFace2 = (face.right(), face.bottom())
        if Draw:
            cv.rectangle(image, cordFace1, cordFace2, YELLOW, 2)
    return image, faces


def facialLandmarkDetector(image, gray, face, Draw=True):
    landmarks = predictor(gray, face)
    pointList = [(landmarks.part(n).x, landmarks.part(n).y) for n in range(68)]
    if Draw:
        for point in pointList:
            cv.circle(image, point, 3, YELLOW, 1)
    return image, pointList


# Define a function to detect blinks using eye landmarks
def blinkDetector(eyePoints):
    top = eyePoints[1:3]
    bottom = eyePoints[4:6]

    # finding midpoints of above points using midpoint function
    # points 38 and 39
    topMid = midpoint(top[0], top[1])
    # points 42 and 41
    bottomMid = midpoint(bottom[0], bottom[1])

    # getting actual width and height
    verticalDistance = euclideanDistance(topMid, bottomMid)
    HorizontalDistance = euclideanDistance(eyePoints[0], eyePoints[3])

    blinkRatio = (HorizontalDistance / verticalDistance) / 2
    return blinkRatio, topMid, bottomMid


def eyetracking(image, gray, eyePoints):
    # getting dimensions of image
    dim = gray.shape

    # creating mask
    mask = np.zeros(dim, dtype=np.uint8)
    # converting eyepoints into  numpy array
    pollyPoints = np.array(eyePoints, dtype=np.int32)
    # filling eye portion with white color
    cv.fillPoly(mask, [pollyPoints], 255)

    # writing gray image where color is white in the using bitwise and operator
    eyeImage = cv.bitwise_and(gray, gray, mask=mask)

    # getting the max and min points of eye inorder to crop the eyes from eye image
    maxX = (max(eyePoints, key=lambda item: item[0]))[0]
    minX = (min(eyePoints, key=lambda item: item[0]))[0]
    maxY = (max(eyePoints, key=lambda item: item[1]))[1]
    minY = (min(eyePoints, key=lambda item: item[1]))[1]

    # other then eye area will black , making it white
    eyeImage[mask == 0] = 255

    cropedEye = eyeImage[minY:maxY, minX:maxX]
    # getting width and height of the cropped eye
    if cropedEye is not None:
        height, width = cropedEye.shape
        divPart = int(width / 3)

        # applying threshold to eye
        ret, thresholdEye = cv.threshold(cropedEye, 100, 255, cv.THRESH_BINARY)

        # dividing eye into three parts
        rightPart = thresholdEye[0:height, 0:divPart]
        centerPart = thresholdEye[0:height, divPart : divPart + divPart]
        leftPart = thresholdEye[0:height, divPart + divPart : width]

        # counting black pixel in each part using numpy
        rightBlackpx = np.sum(rightPart == 0)
        centerBlackpx = np.sum(centerPart == 0)
        leftBlackPx = np.sum(leftPart == 0)

        pos, color = position([rightBlackpx, centerBlackpx, leftBlackPx])
    else:
        # Handle the case where cropped Eye is None
        pos = "EYE CLOSED"
        print("eye closed")
        color = [BLACK, WHITE]

    # print(pos)
    return mask, pos, color


# Define a function to determine eye position and press the space key accordingly
def position(valueList):
    global prevEyePosition
    maxIndex = valueList.index(max(valueList))
    posEye = ""
    prevEyePosition = "CENTER"
    color = [WHITE, BLACK]
    if maxIndex == 0:
        posEye = "RIGHT"

    elif maxIndex == 1:
        posEye = "CENTER"

    elif maxIndex == 2:
        posEye = "LEFT"

    else:
        posEye = "EYE CLOSED"

    # Update the previous eye position
    prevEyePosition = posEye

    return posEye, color
