#-----------INTELLI MEDIA PLAYER---------------

#Group Number - 07

import tkinter as tk
import vlc
from tkinter import filedialog
from datetime import timedelta
from tkinter import ttk
from tkinter import BooleanVar
import cv2 as cv
import time
import numpy as np
import HandTrackingModule as htm
import threading
import EyeDetect

################################
wCam, hCam = 1280, 720
################################

# Define color constants
YELLOW = (0, 247, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

fonts = cv.FONT_HERSHEY_COMPLEX

cap = cv.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
pTime = 0

#Define the no. of hands detected
detector = htm.handDetector(detectionCon=0.7, maxHands=1)

vol = 0
volBar = 400
volPer = 0
area = 0
colorVol = (255, 0, 0)
getvol =0
start_init = False
prev = -1
prev1 = -1
cnt =0
test =0
eyeChoice = 1
handChoice = 1

#GUI
class StyledButton(ttk.Button):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            style="StyledButton.TButton",  # Set the style to use for the button
        )

class ModernStyledButton(ttk.Button):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            style="ModernStyledButton.TButton",  # Set the style to use for the button
        )

#Media player thread
class MediaPlayerApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Media Player")
        self.geometry("800x560")
        self.initialize_player()
        self.initialize_updater()

        # Add a frame to hold the checkboxes
        checkbox_frame = ttk.Frame(self)
        checkbox_frame.pack(pady=5)

        # Add a checkbox for eye detection
        self.eye_detection_enabled = BooleanVar()
        self.eye_detection_enabled.set(True)
        self.eye_detection_checkbox = ttk.Checkbutton(
            checkbox_frame, text="Enable Eye Detection", variable=self.eye_detection_enabled,
            command=self.toggle_eye_detection
        )
        self.eye_detection_checkbox.grid(row=0, column=0, padx=5)

        # Add a checkbox for hand gesture
        self.hand_gesture_enabled = BooleanVar()
        self.hand_gesture_enabled.set(True)
        self.hand_gesture_checkbox = ttk.Checkbutton(
            checkbox_frame, text="Enable Gesture Control", variable=self.hand_gesture_enabled,
            command=self.toggle_hand_gesture
        )
        self.hand_gesture_checkbox.grid(row=0, column=1, padx=5)

        # Define styles for themed buttons
        self.style = ttk.Style()
        self.style.configure(
            "StyledButton.TButton",  # Style for StyledButton
            font=("Arial", 12, "bold"),
            relief=tk.FLAT,
            highlightthickness=0,
            bd=0,
            pady=5,
        )
        self.style.configure(
            "ModernStyledButton.TButton",  # Style for ModernStyledButton
            font=("Arial", 12),
            relief=tk.FLAT,
            highlightthickness=0,
            bd=0,
            pady=5,
            background="#3498db",  # Change the background color here
            foreground="black",  # Change the text color here
        )

    def toggle_eye_detection(self):
        global eyeChoice
        if self.eye_detection_enabled.get():
            eyeChoice = 1
            print("eye enabled")
        else:
            eyeChoice = 0
            print("eye disabled")

    def toggle_hand_gesture(self):
        global handChoice
        if self.hand_gesture_enabled.get():
            handChoice = 1
            print("hand enabled")
        else:
            handChoice = 0
            print("hand disabled")

    def initialize_updater(self):
        self.update_cnt()  # Initial call
        self.after(1000, self.initialize_updater)  # Schedule the next call after 1000ms

    def update_cnt(self):
        global start_init, prev,start_time,prev1
        self.after(1000, self.update_cnt)

        #define Gestures
        end_time = time.time()
        if not (prev == cnt and prev1 == test):
            if not (start_init):
                start_time = time.time()
                start_init = True

            elif (end_time - start_time) > 0.1:
                #play and pause with hand
                if cnt == 1:
                    print("pause")
                    self.pause_video()

                # play and pause with eye
                if test == 6:
                    print("pause")
                    self.pause_video()

                if test == 5:
                    print("play")
                    self.pause_video()

                #stop
                if cnt == 2:
                    print("stop")
                    self.stop()

                prev = cnt
                prev1 = test
                start_init = False

        if not (start_init):
            start_time = time.time()
            start_init = True

        if (end_time - start_time) > 0.2:
            #rewind
            if cnt == 3:
                print("previous")
                self.rewind()

            #fastforward
            if cnt == 4:
                print("next")
                self.fast_forward()

            start_init = False

        #volume
        self.set_volume(getvol)

    def initialize_player(self):
        self.instance = vlc.Instance("--no-xlib")
        self.media_player = self.instance.media_player_new()
        self.current_file = None
        self.playing_video = False
        self.video_paused = False
        self.create_widgets()

    def create_widgets(self):
        self.media_canvas = tk.Canvas(self, bg="black", width=800, height=400)
        self.media_canvas.pack(pady=5, fill=tk.BOTH, expand=True)

        self.time_label = tk.Label(
            self,
            text="00:00:00 / 00:00:00",
            font=("Arial", 12, "bold"),
            fg="#555555",
            bg=self.cget("background"),
        )
        self.time_label.pack(pady=5)

        # Timing Slider (Progress Bar)
        self.progress_bar = tk.Scale(
            self,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            length=800,
            command=self.set_video_position,
            bg="#3498db",  # Adjust color to match the theme
            highlightthickness=0,
        )
        self.progress_bar.pack(fill=tk.X, padx=10, pady=5)

        # Volume Slider
        self.volume_slider = tk.Scale(
            self,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.set_volume,
            bg=self.cget("background"),
            troughcolor="#2C3E50",
            activebackground="#3498db",  # Adjust color to match the theme
            highlightthickness=0,
        )
        self.volume_slider.set(100)  # Start with full volume
        self.volume_slider.pack(pady=5)

        # Store a reference to the volume slider
        self.volume_slider_ref = self.volume_slider

        self.control_buttons_frame = tk.Frame(self, bg=self.cget("background"))
        self.control_buttons_frame.pack(pady=5)

        self.select_file_button = ModernStyledButton(
            self.control_buttons_frame, text="Select File", command=self.select_file
        )
        self.select_file_button.pack(side=tk.LEFT, padx=10, pady=5)

        self.play_button = ModernStyledButton(
            self.control_buttons_frame, text="Play", command=self.play_video
        )
        self.play_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.pause_button = ModernStyledButton(
            self.control_buttons_frame, text="Pause", command=self.pause_video
        )
        self.pause_button.pack(side=tk.LEFT, padx=10, pady=5)
        self.stop_button = ModernStyledButton(
            self.control_buttons_frame, text="Stop", command=self.stop
        )
        self.stop_button.pack(side=tk.LEFT, pady=5)
        self.fast_forward_button = ModernStyledButton(
            self.control_buttons_frame, text="Fast Forward", command=self.fast_forward
        )
        self.fast_forward_button.pack(side=tk.LEFT, padx=10, pady=5)
        self.rewind_button = ModernStyledButton(
            self.control_buttons_frame, text="Rewind", command=self.rewind
        )
        self.rewind_button.pack(side=tk.LEFT, pady=5)

    def select_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Media Files", "*.mp4 *.avi *.mp3")]
        )
        if file_path:
            self.current_file = file_path
            self.time_label.config(text="00:00:00 / " + self.get_duration_str())
            self.play_video()

    def get_duration_str(self):
        if self.playing_video:
            total_duration = self.media_player.get_length()
            total_duration_str = str(timedelta(milliseconds=total_duration))[:-3]
            return total_duration_str
        return "00:00:00"

    def play_video(self):
        if not self.playing_video:
            media = self.instance.media_new(self.current_file)
            self.media_player.set_media(media)
            self.media_player.set_hwnd(self.media_canvas.winfo_id())
            self.media_player.play()
            self.playing_video = True
            self.after(1000, self.update_video_progress)

    def fast_forward(self):
        if self.playing_video:
            current_time = self.media_player.get_time() + 10000
            self.media_player.set_time(current_time)

    def rewind(self):
        if self.playing_video:
            current_time = self.media_player.get_time() - 10000
            self.media_player.set_time(current_time)

    def set_volume(self, value):
        if self.playing_video:
            new_volume = int(int(value)*2)
            self.media_player.audio_set_volume(new_volume)
            self.volume_slider_ref.set(int(value))  # Update volume slider
            global getvol  # Add this line to access the global variable
            getvol = int(value)

    def pause_video(self):
        if self.playing_video:
            if self.video_paused:
                print('player play')
                self.media_player.play()
                self.video_paused = False
                self.pause_button.config(text="Pause")
            else:
                print('player pause')
                self.media_player.pause()
                self.video_paused = True
                self.pause_button.config(text="Resume")

    def stop(self):
        if self.playing_video:
            print("player stop")
            self.media_player.stop()
            self.playing_video = False
        self.time_label.config(text="00:00:00 / " + self.get_duration_str())

    def set_video_position(self, value):
        if self.playing_video:
            total_duration = self.media_player.get_length()
            position = int((float(value) / 100) * total_duration)
            self.media_player.set_time(position)

    def update_video_progress(self):
        if self.playing_video:
            total_duration = self.media_player.get_length()
            current_time = self.media_player.get_time()
            progress_percentage = (current_time / total_duration) * 100
            self.progress_bar.set(progress_percentage)
            current_time_str = str(timedelta(milliseconds=current_time))[:-3]
            total_duration_str = str(timedelta(milliseconds=total_duration))[:-3]
            self.time_label.config(
                text=f"{current_time_str} / {total_duration_str}"
            )
            self.after(1000, self.update_video_progress)

#Hand gesture thread
def run_hand_gesture():
    global start_init,prev,cnt,volPer,getvol,colorVol,pTime,volBar,handChoice
    while True:
        if handChoice == 0:
            time.sleep(1)
            continue

        success, img = cap.read()

        # Find Hand
        img = detector.findHands(img)
        lmList, bbox = detector.findPosition(img, draw=True)
        if len(lmList) != 0:
            # Filter based on size
            area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) // 100
            # print(area)
            if 250 < area < 1300:
                # Find Distance between index and Thumb
                length, img, lineInfo = detector.findDistance(4, 8, img)
                # print(length)

                # Convert Volume
                volPer = np.interp(length, [50, 250], [0, 100])

                # Reduce Resolution to make it smoother
                smoothness = 5
                volPer = smoothness * round(volPer / smoothness)

                # Check fingers up
                fingers = detector.fingersUp()

                # If pinky is down set volume
                if fingers[4] and not fingers[3] and not fingers[2]:
                    #volume.SetMasterVolumeLevelScalar(volPer / 100, None)
                    getvol = volPer
                    cv.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 255, 0), cv.FILLED)
                    colorVol = (0, 255, 0)
                else:
                    colorVol = (255, 0, 0)

                #Gestures

                #0 - 4 = 5 fingers up
                #5 - 8 = 4 fingers pointing left
                #9 - 12 = 4 fingers pointing right
                #13 to check 7th below 5 for previous gesture

                #pause gesture

                if fingers[0] and fingers[1] and fingers[2] and fingers[3] and fingers[4]:
                    cnt = 1

                #stop gesture
                if fingers[1] and fingers[2] and not fingers[3] and not fingers[4]:
                    cnt = 2

                #previous gesture
                if fingers[5] and fingers[6] and fingers[7] and fingers[8] and fingers[13] and not fingers[2] and not fingers[3]:
                    cnt = 3

                #next gesture
                if fingers[9] and fingers[10] and fingers[11] and fingers[12] and not fingers[2] and not fingers[3]:
                    cnt = 4
        else:
            cnt = 0

        # Drawings
        cv.putText(
            img,
            f"Vol Set: {int(getvol)}",
            (400, 50),
            cv.FONT_HERSHEY_COMPLEX,
            1,
            colorVol,
            3,
        )

        cv.imshow("Img", img)
        if cv.waitKey(1) == 27:
            cv.destroyAllWindows()
            cap.release()
            break

#eye detection thread
def run_eye_detection():
    global test,eyeChoice
    while True:
        # ------------eye------------------
        if eyeChoice == 0:  # Check if eye detection is enabled
            time.sleep(1)  # If not enabled, wait for a while and check again
            continue
        # getting frame from camera
        ret, frame = cap.read()

        # converting frame into grayscale image
        grayFrame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

        # calling the face detector function
        image, faces = EyeDetect.faceDetector(frame, grayFrame)

        if len(faces) == 0:
            # print("no face")
            test = 5

        for face in faces:
            image, pointList = EyeDetect.facialLandmarkDetector(frame, grayFrame, face, False)
            # Right eye landmarks
            rightEyePoint = pointList[36:42]
            rightRatio, rTop, rBottom = EyeDetect.blinkDetector(rightEyePoint)
            cv.circle(image, rTop, 2, YELLOW, -1)
            cv.circle(image, rBottom, 2, YELLOW, -1)

            mask, posRight, colorRight = EyeDetect.eyetracking(frame, grayFrame, rightEyePoint)

            # Left eye landmarks
            leftEyePoint = pointList[42:48]
            leftRatio, lTop, lBottom = EyeDetect.blinkDetector(leftEyePoint)
            cv.circle(image, lTop, 2, YELLOW, -1)
            cv.circle(image, lBottom, 2, YELLOW, -1)

            mask, posLeft, colorLeft = EyeDetect.eyetracking(frame, grayFrame, leftEyePoint)

            if posRight != "CENTER" or posLeft != "CENTER":
                #print('look away')
                test = 5
            else:
                #print("eql")
                test = 6

        cv.imshow('Frame', image)

        # defining the key to quite the loop
        if cv.waitKey(1) == 27:
            cv.destroyAllWindows()
            cap.release()
            break

def run_media_player():
    app = MediaPlayerApp()
    app.update_video_progress()
    app.mainloop()

#Running 3 threads simultaneously
if __name__ == "__main__":
    hand_gesture_thread = threading.Thread(target=run_hand_gesture)
    media_player_thread = threading.Thread(target=run_media_player)
    eye_detection_thread = threading.Thread(target=run_eye_detection)

    hand_gesture_thread.start()
    media_player_thread.start()
    eye_detection_thread.start()

    hand_gesture_thread.join()
    media_player_thread.join()
    eye_detection_thread.join()
