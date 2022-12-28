import time
import cv2
from yolov5 import yolo_detection
from SlowFast.slowfast_detection import SlowFastDetection
from SlowFast.slowfast.utils.misc import get_class_names

def read_frames(frame_q, detect_q, video_path): # 영상의 프레임을 읽어와서 모델 추론을 수행하는 함수
    inference_model_yolo = yolo_detection.ObjectDetection()
    reader = cv2.VideoCapture(video_path)

    nframes = int(reader.get(cv2.CAP_PROP_FRAME_COUNT))

    for ii in range(nframes):   # 영상의 마지막 프레임까지 반복
        while frame_q.qsize() > 64: # frame_q에 50개 이상 frame이 쌓일 경우 sleep
            time.sleep(1)
        _, frame = reader.read()

        frame_q.put(frame)
        # 모델 추론부
        inference_model_yolo.inference_img(frame)
        inference_img = inference_model_yolo.get_data()
        detect_q.put(inference_img)

def slowfast_read_frames(frame_q, action_detect_q, video_path):
    reader = cv2.VideoCapture(video_path)

    nframes = int(reader.get(cv2.CAP_PROP_FRAME_COUNT))

    inference_model_slowfast = SlowFastDetection()
    inference_model_slowfast.video_path_input(reader, video_path)
    class_names_path = inference_model_slowfast.cfg.DEMO.LABEL_FILE_PATH

    class_names, _, _ = get_class_names(class_names_path, None, None)
    print("action_class_names : ", class_names)

    frames_list = []

    for ii in range(nframes):  # 영상의 마지막 프레임까지 반복
        # while frame_q.qsize() > inference_model_slowfast.seq_length:
        #     time.sleep(1)
        _, frame = reader.read()

        # frame_q.put(frame)
        frames_list.append(frame)
        if len(frames_list) == inference_model_slowfast.seq_length:
            for task in inference_model_slowfast.run_model(frames_list):

                action_confidence_list = task.action_preds.tolist()
                print(action_confidence_list)

                for frame in task.frames[task.num_buffer_frames :]:
                    action_detect_q.put(frame)
            frames_list.clear()