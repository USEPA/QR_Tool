import argparse
import imutils
import time
import cv2
from datetime import datetime
from imutils.video import VideoStream

show_video = True
camera_warmup_time = 2.5
delta_thresh = 50   # How big the difference in pixels must be to pick up motion
resolution = [640, 480]
fps = 16
weight = 0.0001  # affects how long before objects get added to background, lower = longer
min_area = 10000  # how big a difference needs to be to get picked up
avg = None

ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="path to the video file")
ap.add_argument("-a", "--min-area", type=int, default=500, help="minimum area size")
args = vars(ap.parse_args())
# if the video argument is None, then we are reading from webcam
if args.get("video", None) is None:
    vs = VideoStream(src=0).start()
    time.sleep(camera_warmup_time)
# otherwise, we are reading from a video file
else:
    vs = cv2.VideoCapture(args["video"])


while True:
    # grab the frame from the threaded video stream and resize it to have a maximum width of 400 pixels
    frame = None
    try:  # if the video stream stops working or is changed
        frame = vs.read()
        frame = imutils.resize(frame, width=500)
    except:  # then catch and break the loop, and do clean up
        break
    timestamp = datetime.now()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    # if the average frame is None, initialize it
    if avg is None:
        print("[INFO] starting background model...")
        avg = gray.copy().astype("float")
        continue

    cv2.accumulateWeighted(gray, avg, weight)  # 3rd value affects how long before objects get added to background,
    # lower = longer
    frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

    thresh = cv2.threshold(frameDelta, delta_thresh, 255,
                           cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=3)  # 'iterations' determines how smoothed, but higher takes more time
    contour = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                               cv2.CHAIN_APPROX_SIMPLE)
    contour = imutils.grab_contours(contour)

    text = ""

    for c in contour:
        # if the contour is too small, ignore it
        if cv2.contourArea(c) < min_area:
            continue
        # compute the bounding box for the contour, draw it on the frame,
        # and update the text
        (x, y, w, h) = cv2.boundingRect(c)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        text = "Occupied"

    ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
    cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
                0.35, (0, 0, 255), 1)

    if show_video:
        # display the security feed
        cv2.imshow("Gray Frame", gray)
        cv2.imshow("Delta Frame", frameDelta)
        cv2.imshow("Threshold Frame", thresh)
        cv2.imshow("Motion Capture", frame)

        key = cv2.waitKey(1) & 0xFF
        # if the `q` key is pressed, break from the loop
        if key == ord("q"):
            break
