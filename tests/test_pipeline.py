import tempfile
import unittest
from pathlib import Path
import numpy as np
from fanvib.demo import generate_demo
from fanvib.pipeline import analyze_video,roi_mask

class PipelineTest(unittest.TestCase):
    def test_known_motion_with_camera_shake_and_slow_playback(self):
        with tempfile.TemporaryDirectory() as tmp:
            video,_,config=generate_demo(tmp,frames=300)
            r=analyze_video(video,config,Path(tmp)/"out")
            self.assertEqual(r["metadata"]["playback_fps"],30)
            self.assertEqual(r["metadata"]["capture_fps"],120)
            self.assertEqual(r["metadata"]["nyquist_hz"],60)
            peaks=r["regions"]["head"]["translation"]["welch_candidate_peaks"]
            self.assertLess(abs(peaks[0]["hz"]-23.4),.6)
            self.assertIsNone(r["diagnosis"]["fault_source"])
            signals=np.load(Path(tmp)/"out/signals.npz")
            self.assertEqual(signals["head__translation"].shape,(300,2))
            for name in ["analysis.json","signals.npz","roi.png","spectra.png"]:
                self.assertTrue((Path(tmp)/"out"/name).is_file())
    def test_missing_capture_timebase_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"capture_fps"):
            analyze_video("missing.avi",{},"unused")
    def test_outside_roi_is_rejected(self):
        with self.assertRaises(ValueError):
            roi_mask((100,100),{"shape":"rectangle","bounds":[90,0,30,40]})
    def test_invalid_roi_ids_are_rejected(self):
        with self.assertRaisesRegex(ValueError,"ROI ids"):
            analyze_video("missing.avi",{"capture_fps":240,"rois":[{"id":"same"},{"id":"same"}]},"unused")

if __name__=="__main__": unittest.main()
