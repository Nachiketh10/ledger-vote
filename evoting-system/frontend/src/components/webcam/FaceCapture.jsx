import { useCallback, useRef, useState } from "react";
import Webcam from "react-webcam";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import Button from "../ui/Button";

/**
 * Captures a burst of frames from the webcam over `seconds` at `fps`,
 * showing a live feed + progress the whole time (so the voter can SEE
 * their face is actually being captured, not just get a result after
 * the fact). Calls onComplete(frames) with an array of base64 JPEG
 * data URLs once done, and — if onComplete returns a Promise (it
 * usually does, since it triggers an API call) — shows a "Processing"
 * state until that resolves, so there's never a moment where nothing
 * on screen indicates work is happening.
 */
export default function FaceCapture({ seconds = 4, fps = 4, prompt, buttonLabel, onComplete }) {
  const webcamRef = useRef(null);
  const [capturing, setCapturing] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [totalFrames, setTotalFrames] = useState(0);
  const [done, setDone] = useState(false);

  const startCapture = useCallback(async () => {
    setCapturing(true);
    setDone(false);
    const total = Math.floor(seconds * fps);
    setTotalFrames(total);
    setProgress(0);

    const frames = [];
    const interval = 1000 / fps;
    for (let i = 0; i < total; i++) {
      const shot = webcamRef.current?.getScreenshot();
      if (shot) frames.push(shot);
      setProgress(i + 1);
      // eslint-disable-next-line no-await-in-loop
      await new Promise((r) => setTimeout(r, interval));
    }

    setCapturing(false);
    setProcessing(true);
    try {
      await onComplete(frames);
    } finally {
      setProcessing(false);
      setDone(true);
    }
  }, [seconds, fps, onComplete]);

  return (
    <div className="flex flex-col items-center gap-3">
      <div
        className={`relative overflow-hidden rounded-lg border-4 transition-colors duration-150 ${
          capturing ? "border-seal" : "border-line"
        }`}
      >
        <Webcam
          ref={webcamRef}
          audio={false}
          screenshotFormat="image/jpeg"
          width={280}
          height={210}
          videoConstraints={{ width: 280, height: 210, facingMode: "user" }}
          className="block"
        />
        {capturing && (
          <motion.div
            className="absolute inset-0 border-2 border-white/70"
            animate={{ opacity: [1, 0.3, 1] }}
            transition={{ duration: 0.6, repeat: Infinity }}
          />
        )}
        {processing && (
          <div className="absolute inset-0 flex items-center justify-center bg-ink/50">
            <Loader2 size={28} className="animate-spin text-white" />
          </div>
        )}
      </div>

      {capturing && (
        <div className="w-full max-w-[280px]">
          <div className="mb-1 flex justify-between text-xs text-muted">
            <span>{prompt}</span>
            <span>
              {progress}/{totalFrames}
            </span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-ink/10 dark:bg-white/10">
            <motion.div
              className="h-full bg-seal"
              animate={{ width: `${(progress / totalFrames) * 100}%` }}
              transition={{ duration: 0.15 }}
            />
          </div>
        </div>
      )}

      {processing && <p className="text-xs text-muted">Verifying and saving...</p>}

      {!capturing && !processing && (
        <Button onClick={startCapture} variant={done ? "outline" : "primary"}>
          {done ? "Recapture" : buttonLabel}
        </Button>
      )}
    </div>
  );
}
