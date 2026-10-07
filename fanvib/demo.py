"""A deterministic synthetic camera-shake + known target-motion example."""
from pathlib import Path
import json
import cv2
import numpy as np


def generate_demo(directory, frames=480, capture_fps=120.0, frequency=23.4):
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
    base = np.full((240,320,3),35,np.uint8)
    rng = np.random.default_rng(4)
    for lo,hi in [(5,75),(245,315)]:
        for _ in range(65):
            x,y = int(rng.integers(lo,hi)),int(rng.integers(10,230))
            cv2.rectangle(base,(x,y),(x+3,y+3),(230,230,230),-1)
    obj = np.full((90,110,3),65,np.uint8)
    for x in range(10,105,15):
        for y in range(10,85,15): cv2.rectangle(obj,(x,y),(x+4,y+4),(250,250,250),-1)
    video = directory/"synthetic.avi"
    writer = cv2.VideoWriter(str(video),cv2.VideoWriter_fourcc(*"MJPG"),30,(320,240))
    if not writer.isOpened(): raise RuntimeError("MJPG writer unavailable")
    try:
        for i in range(frames):
            t=i/capture_fps
            shift=1.8*np.sin(2*np.pi*frequency*t)
            frame=base.copy(); frame[75:165,105:215]=obj
            # Move only the object subimage; fractional-pixel interpolation.
            shifted=cv2.warpAffine(frame,np.array([[1,0,shift],[0,1,0]],float),(320,240))
            frame[70:170,95:225]=shifted[70:170,95:225]
            camera_x=2*np.sin(2*np.pi*.8*t); camera_y=np.sin(2*np.pi*.5*t)
            frame=cv2.warpAffine(frame,np.array([[1,0,camera_x],[0,1,camera_y]],float),(320,240),borderMode=cv2.BORDER_REFLECT)
            writer.write(frame)
    finally: writer.release()
    config={"capture_fps":capture_fps,"frame_size":[320,240],"nperseg":256,"rois":[
        {"id":"head","role":"target","shape":"rectangle","bounds":[105,75,110,90]},
        {"id":"background_left","role":"background","shape":"rectangle","bounds":[5,5,75,230]},
        {"id":"background_right","role":"background","shape":"rectangle","bounds":[240,5,75,230]}],"relative_pairs":[]}
    config_path=directory/"synthetic.json"; config_path.write_text(json.dumps(config,indent=2),encoding="utf-8")
    return video,config_path,config
