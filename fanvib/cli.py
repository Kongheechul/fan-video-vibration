import argparse
import json
from pathlib import Path
import cv2
from .pipeline import analyze_video, read_first_frame


def main():
    p=argparse.ArgumentParser(description="Research video vibration measurements, not fault diagnosis")
    sub=p.add_subparsers(dest="command",required=True)
    inspect=sub.add_parser("inspect",help="Inspect decoded orientation, size and playback FPS")
    inspect.add_argument("video"); inspect.add_argument("--frame",help="Save first frame for ROI annotation")
    analyze=sub.add_parser("analyze",help="Analyze a video with explicitly configured capture FPS and ROIs")
    analyze.add_argument("video"); analyze.add_argument("--config",required=True); analyze.add_argument("--out",default="results/analysis")
    analyze.add_argument("--capture-fps",type=float,help="Override capture timebase, never inferred from playback")
    demo=sub.add_parser("demo",help="Generate synthetic 23.4 Hz data and run the pipeline")
    demo.add_argument("--out",default="results/demo")
    args=p.parse_args()
    try:
        if args.command=="inspect":
            cap,frame,fps=read_first_frame(args.video)
            try: count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            finally: cap.release()
            if args.frame:
                path=Path(args.frame); path.parent.mkdir(parents=True,exist_ok=True)
                if not cv2.imwrite(str(path),frame): raise ValueError("Could not save frame")
            print(json.dumps({"playback_fps":fps,"reported_frame_count":count,"decoded_frame_size":[frame.shape[1],frame.shape[0]],"capture_fps":"not inferred; supply explicitly"},indent=2))
            return
        if args.command=="demo":
            from .demo import generate_demo
            video,_,config=generate_demo(Path(args.out)/"input")
            out=Path(args.out)/"analysis"
        else:
            video=args.video; config=json.loads(Path(args.config).read_text(encoding="utf-8")); out=args.out
            if args.capture_fps is not None: config["capture_fps"]=args.capture_fps
        r=analyze_video(video,config,out)
        print(json.dumps({"status":r["status"],"capture_fps":r["metadata"]["capture_fps"],"output_dir":str(out),"diagnosis":r["diagnosis"]},indent=2))
    except (ValueError,RuntimeError,OSError,KeyError,TypeError) as e:
        p.exit(2,f"Error: {e}\n")

if __name__=="__main__": main()
