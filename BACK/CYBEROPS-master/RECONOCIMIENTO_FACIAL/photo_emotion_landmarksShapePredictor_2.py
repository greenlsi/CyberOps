# TAKE PHOTOS EACH 1 MINUTE- PYTHON FILE
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import csv
import glob
import json
import math
import os
import time
import datetime
import cv2
import dlib
import numpy as np
from kafka import KafkaProducer
from sklearn.externals import joblib
import settings as settings


# CREATING FUNCTION TO GET LANDMARKS FROM THE PHOTOS

def get_landmarks(image,predictor,detector):
    data = {}  # Make dictionary for all values

    detections = detector(image, 1)
    for k, d in enumerate(detections):  # For all detected face instances individually
        shape = predictor(image, d)  # Draw Facial Landmarks with the predictor class
        xlist = []
        ylist = []
        for i in range(1, 68):  # Store X and Y coordinates in two lists
            xlist.append(float(shape.part(i).x))
            ylist.append(float(shape.part(i).y))

        xmean = np.mean(xlist)
        ymean = np.mean(ylist)
        xcentral = [(x - xmean) for x in xlist]
        ycentral = [(y - ymean) for y in ylist]

        landmarks_vectorised = []
        for x, y, w, z in zip(xcentral, ycentral, xlist, ylist):
            landmarks_vectorised.append(w)
            landmarks_vectorised.append(z)
            meannp = np.asarray((ymean, xmean))
            coornp = np.asarray((z, w))
            dist = np.linalg.norm(coornp - meannp)
            landmarks_vectorised.append(dist)
            landmarks_vectorised.append((math.atan2(y, x) * 360) / (2 * math.pi))

        data['landmarks_vectorised'] = landmarks_vectorised
    if len(detections) < 1:
        data['landmarks_vectorised'] = "error"
    return  data

# LOADING AND DEFINING INITIAL VARIABLES
def emotion(producer, employee, topic_emotion, PATH, camera_open=0):
    video_mode = 0
    camera = cv2.VideoCapture(video_mode)

    if not camera.isOpened():
        camera.open(camera_open)

    # PATH = os.getcwd()  # /home/marta/PycharmProjects/CYBEROPS/RECONOCIMIENTO_FACIAL
    faceDet = cv2.CascadeClassifier(PATH+settings.operative_system+"OpenCV_FaceCascade"+settings.operative_system+"haarcascade_frontalface_default.xml")
    faceDet_two = cv2.CascadeClassifier(PATH + settings.operative_system+"OpenCV_FaceCascade"+settings.operative_system+"haarcascade_frontalface_alt2.xml")
    faceDet_three = cv2.CascadeClassifier(PATH + settings.operative_system+"OpenCV_FaceCascade"+settings.operative_system+"haarcascade_frontalface_alt.xml")
    faceDet_four = cv2.CascadeClassifier(PATH + settings.operative_system+"OpenCV_FaceCascade"+settings.operative_system+"haarcascade_frontalface_alt_tree.xml")

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))  # Contrast Limited Adaptive Histogram Equalization
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(
        PATH + settings.operative_system+"MODELOS"+settings.operative_system+"shape_predictor_68_face_landmarks.dat")  # Or set this to whatever you named the downloaded file


    prediction_data = []
    voted_class_list = []
    flag=1

    def classifier(gray):

        # Detect face using 4 different classifiers
        face = faceDet.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=10, minSize=(5, 5),
                                        flags=cv2.CASCADE_SCALE_IMAGE)
        face_two = faceDet_two.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=10, minSize=(5, 5),
                                                flags=cv2.CASCADE_SCALE_IMAGE)
        face_three = faceDet_three.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=10, minSize=(5, 5),
                                                    flags=cv2.CASCADE_SCALE_IMAGE)
        face_four = faceDet_four.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=10, minSize=(5, 5),
                                                  flags=cv2.CASCADE_SCALE_IMAGE)

        # Go over detected faces, stop at first detected face, return empty if no face.
        if len(face) == 1:
            facefeatures = face
        elif len(face_two) == 1:
            facefeatures = face_two
        elif len(face_three) == 1:
            facefeatures = face_three
        elif len(face_four) == 1:
            facefeatures = face_four
        else:
            print("no face detected in file: %s" % picture)
            emotion = None
            return emotion

        # Cut and save face
        for (x, y, w, h) in facefeatures:  # get coordinates and size of rectangle containing face
            print("face found in file: %s" % picture)
            gray = gray[y:y + h, x:x + w]  # Cut the frame to size
            try:
                out = cv2.resize(gray, (350, 350))  # Resize face so all images have same size
                if not os.path.exists(PATH + settings.operative_system+"Webcam_photos"+settings.operative_system+"Classifier"):
                    os.makedirs(PATH + settings.operative_system+"Webcam_photos"+settings.operative_system+"Classifier")
                cv2.imwrite(PATH + settings.operative_system+"Webcam_photos"+settings.operative_system+"Classifier"+settings.operative_system+"%s" % filename, out)  # Write image
            except:
                pass  # If error, pass file

        # Pass classifier

        gray_picture = PATH + settings.operative_system+"Webcam_photos"+settings.operative_system+"Classifier"+settings.operative_system + filename

        gray_image = cv2.imread(gray_picture)  # open photo
        img_grey = cv2.cvtColor(gray_image, cv2.COLOR_BGR2GRAY)

        clahe_image = clahe.apply(img_grey)  # Aplying Contrast Limited Adaptive Histogram Equalization to create a grater contrast b/w on the photo
        data = get_landmarks(clahe_image, predictor, detector)  # getting landmarks from photo

        if data['landmarks_vectorised'] == "error":
            print("no emotion detected on this one")
            emotion = None

        else:
            # cv2.imwrite("/home/marta/Webcam/dataset/%s" % (clahe_image, out)) # Write image

            prediction_data.append(data['landmarks_vectorised'])
            clf1 = joblib.load(PATH + settings.operative_system+'MODELOS'+settings.operative_system+'SVC_own_dataset_Classifier_py35.pkl')
            clf2 = joblib.load(PATH + settings.operative_system+'MODELOS'+settings.operative_system+'RF_own_dataset_Classifier_py35.pkl')
            clf3 = joblib.load(PATH + settings.operative_system+'MODELOS'+settings.operative_system+'ET_own_dataset_Classifier_py35.pkl')
            clf4 = joblib.load(PATH + settings.operative_system+'MODELOS'+settings.operative_system+'GB_own_dataset_Classifier_py35.pkl')
            clf5 = joblib.load(PATH + settings.operative_system+'MODELOS'+settings.operative_system+'DT_own_dataset_Classifier_py35.pkl')
            clf6 = joblib.load(PATH + settings.operative_system+'MODELOS'+settings.operative_system+'BC_own_dataset_Classifier_py35.pkl')
            voted_classifier = joblib.load(PATH + settings.operative_system+'MODELOS'+settings.operative_system+'MLP_own_dataset_prediction_Classifier_py35.pkl')

            prediction1 = int(clf1.predict(prediction_data))
            prediction2 = int(clf2.predict(prediction_data))
            prediction3 = int(clf3.predict(prediction_data))
            prediction4 = int(clf4.predict(prediction_data))
            prediction5 = int(clf5.predict(prediction_data))
            prediction6 = int(clf6.predict(prediction_data))
            voted_class_list.append([prediction1, prediction2, prediction3, prediction4, prediction5, prediction6])
            voted_classifier_prediction = voted_classifier.predict(voted_class_list)

            # print(voted_classifier_prediction)

            # emotions_trained_model=["anger"-0, "happy"-1, "neutral"-2, "sadness"-3, "surprise"-4]
            if voted_classifier_prediction == 0:
                emotion = "anger"
                print(emotion)
            elif voted_classifier_prediction == 1:
                emotion = "happy"
                print(emotion)
            elif voted_classifier_prediction == 2:
                emotion = "neutral"
                print(emotion)
            elif voted_classifier_prediction == 3:
                emotion = "sadness"
                print(emotion)
            elif voted_classifier_prediction == 4:
                emotion = "surprise"
                print(emotion)

            prediction_data.pop()  # delating previous prediction appended to data_prediction array
            voted_class_list.pop()

        # write timestamp and emotion in csv file
        with open(PATH + settings.operative_system+'Webcam_photos'+settings.operative_system+'emotions_landmarks.csv', 'a') as csvfile:
            writer = csv.writer(csvfile, delimiter=';', lineterminator='\n')
            writer.writerow([filename[0:19], emotion])

        return emotion

    def delete(files, gray_files):
        # Delete files when they exceed a number
        file_count = len(files)
        file_count_gray = len(gray_files)

        tupla = []
        tupla_gray = []

        if file_count > 3:  # Defining the maximum number of saved photos (3)
            for picture in files:
                date = os.path.getctime(picture)
                array = [date, picture]
                tupla.append(array)
            older_file = sorted(tupla)
            deletepath = older_file[0][1]
            os.remove(deletepath)

        if file_count_gray > 3:  # Defining the maximum number of saved photos (3)
            for picture in gray_files:
                date = os.path.getctime(picture)
                array_gray = [date, picture]
                tupla_gray.append(array_gray)
            older_gray_file = sorted(tupla_gray)
            deletepath_gray = older_gray_file[0][1]
            os.remove(deletepath_gray)

    # DEFINING LOOP TO TAKE AND ANALYZE PHOTOS

    while(True):

        if flag==1:

            return_value, image = camera.read()
            tm = datetime.datetime.now()
            filename = tm.strftime("%Y-%m-%d_%H_%M_%S") + ".png"
            timestamp_rounded = tm - datetime.timedelta(seconds=tm.second, microseconds=tm.microsecond)
            cv2.imwrite(PATH+settings.operative_system+'Webcam_photos'+settings.operative_system + filename, image)
            camera.release()

            flag=0 # Activate flag to enter in "else" loop after the first photo

            # Modify image for classification
            files = glob.glob(PATH+settings.operative_system+"Webcam_photos"+settings.operative_system+"*.png")

            picture = PATH + settings.operative_system+'Webcam_photos'+settings.operative_system + filename
            frame = cv2.imread(picture)  # Open image
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Convert image to grayscale

            emotion = classifier(gray)

            # Send to Kafka
            data2send = {"timestamp": timestamp_rounded.strftime("%Y-%m-%d %H:%M:%S"),  # redondeado
                         "emotion": emotion,
                         "employeeAlias": employee}
            producer.send(topic_emotion, json.dumps(data2send).encode('utf-8'))

            # DELETE EXTRA PHOTOS
            gray_files = glob.glob(PATH + settings.operative_system+"Webcam_photos"+settings.operative_system+"Classifier"+settings.operative_system+"*.png")
            delete(files, gray_files)


        else:

            time.sleep(60.0) #time in seconds between 2 photos
            camera = cv2.VideoCapture(video_mode)
            return_value, image = camera.read()
            tm = datetime.datetime.now()
            filename = tm.strftime("%Y-%m-%d_%H_%M_%S") + ".png"
            timestamp_rounded = tm - datetime.timedelta(seconds=tm.second, microseconds=tm.microsecond)
            cv2.imwrite(PATH+settings.operative_system+'Webcam_photos'+settings.operative_system + filename, image)
            camera.release()

            # Modify image for classification
            files = glob.glob(PATH+settings.operative_system+'Webcam_photos'+settings.operative_system+'*.png')

            picture = PATH + settings.operative_system+'Webcam_photos'+settings.operative_system + filename
            frame = cv2.imread(picture)  # Open image
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Convert image to grayscale

            emotion = classifier(gray)

            # Send to Kafka
            data2send = {"timestamp": timestamp_rounded.strftime("%Y-%m-%d %H:%M:%S"), #redondeado
                         "emotion": emotion,
                         "employeeAlias": employee}
            producer.send(topic_emotion, json.dumps(data2send).encode('utf-8'))


            # Delete files when they exceed a number
            gray_files = glob.glob(PATH + settings.operative_system+"Webcam_photos"+settings.operative_system+"Classifier"+settings.operative_system+"*.png")
            delete(files, gray_files)

    del(camera)


if __name__ == "__main__":
    producer = KafkaProducer(bootstrap_servers=settings.ip_kafka_DCOS, api_version=(0, 10, 1))
    PATH = os.getcwd()+settings.operative_system+"RECONOCIMIENTO_FACIAL"
    emotion(producer=producer, employee=settings.employee_name, topic_emotion="cyberops_emotion", PATH=PATH,camera_open=settings.camera_mode)
    producer.close()