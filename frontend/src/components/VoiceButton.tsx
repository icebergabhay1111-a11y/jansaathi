"use client";
import { useEffect, useRef, useState } from "react";
import { Loader2, Mic, Square } from "lucide-react";
import { api } from "@/lib/api";

export type VoiceLang = "en" | "hi" | "ta";
export const VOICE_LANGS: { code: VoiceLang; label: string; bcp47: string }[] = [
  { code: "hi", label: "हिन्दी", bcp47: "hi-IN" },
  { code: "ta", label: "தமிழ்", bcp47: "ta-IN" },
  { code: "en", label: "English", bcp47: "en-IN" },
];

type SR = {
  lang: string; interimResults: boolean; continuous: boolean; maxAlternatives: number;
  start: () => void; stop: () => void; abort: () => void;
  onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }> & { isFinal: boolean }> }) => void) | null;
  onerror: ((e: { error: string }) => void) | null;
  onend: (() => void) | null;
};

function getSR(): (new () => SR) | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as { SpeechRecognition?: new () => SR; webkitSpeechRecognition?: new () => SR };
  return w.SpeechRecognition || w.webkitSpeechRecognition || null;
}

const MAX_SECONDS = 45;
const ERR: Record<string, string> = {
  "not-allowed": "Microphone permission was blocked. Allow the microphone for this site in your browser settings.",
  "service-not-allowed": "Microphone permission was blocked. Allow the microphone for this site in your browser settings.",
  "no-speech": "We didn't hear anything. Tap the mic and speak again.",
  "audio-capture": "No microphone was found on this device.",
  network: "Voice recognition needs an internet connection.",
  "language-not-supported": "This browser can't recognise that language — trying the JanSaathi voice service instead.",
};

/**
 * Voice input. Uses the browser's speech recognition when it supports the chosen language
 * (Chrome/Edge/Android), otherwise records a short clip and sends it to /api/assistant/transcribe
 * (Gemini) — only for transcription, nothing is stored. Calls onText with the recognised text.
 */
export function VoiceButton({ lang, onText, onInterim, className = "" }: {
  lang: VoiceLang; onText: (t: string) => void; onInterim?: (t: string) => void; className?: string;
}) {
  const [state, setState] = useState<"idle" | "listening" | "recording" | "transcribing">("idle");
  const [error, setError] = useState<string | null>(null);
  const [supported, setSupported] = useState(true);
  const recRef = useRef<SR | null>(null);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const forceServer = useRef(false);

  useEffect(() => {
    const ok = !!getSR() || (typeof navigator !== "undefined" && !!navigator.mediaDevices?.getUserMedia && typeof MediaRecorder !== "undefined");
    setSupported(ok);
    return () => { recRef.current?.abort(); mediaRef.current?.stream.getTracks().forEach((t) => t.stop()); if (timerRef.current) clearTimeout(timerRef.current); };
  }, []);

  const bcp47 = VOICE_LANGS.find((l) => l.code === lang)!.bcp47;

  function startBrowser(SRClass: new () => SR) {
    const rec = new SRClass();
    rec.lang = bcp47; rec.interimResults = true; rec.continuous = false; rec.maxAlternatives = 1;
    let finalText = "";
    rec.onresult = (e) => {
      let interim = "";
      for (let i = 0; i < e.results.length; i++) {
        const r = e.results[i];
        if (r.isFinal) finalText += r[0].transcript; else interim += r[0].transcript;
      }
      onInterim?.(finalText + interim);
    };
    rec.onerror = (e) => {
      if (e.error === "language-not-supported" || (e.error === "service-not-allowed" && lang !== "en")) {
        forceServer.current = true;
        setState("idle");
        startRecording();
        return;
      }
      if (e.error !== "aborted") setError(ERR[e.error] || "Voice input stopped. Please try again or type.");
    };
    rec.onend = () => {
      setState((s) => (s === "listening" ? "idle" : s));
      if (finalText.trim()) onText(finalText.trim());
    };
    recRef.current = rec;
    setState("listening");
    rec.start();
  }

  async function startRecording() {
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setError("Voice input isn't supported in this browser. Please type, or try Chrome.");
      return;
    }
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setError(ERR["not-allowed"]);
      return;
    }
    const mime = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/mp4"].find((m) => MediaRecorder.isTypeSupported?.(m)) || "";
    const rec = new MediaRecorder(stream, mime ? { mimeType: mime, audioBitsPerSecond: 32000 } : undefined);
    const chunks: Blob[] = [];
    rec.ondataavailable = (e) => { if (e.data.size) chunks.push(e.data); };
    rec.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      if (timerRef.current) clearTimeout(timerRef.current);
      const blob = new Blob(chunks, { type: rec.mimeType || mime || "audio/webm" });
      if (blob.size < 500) { setState("idle"); setError(ERR["no-speech"]); return; }
      setState("transcribing");
      try {
        const b64 = await new Promise<string>((resolve, reject) => {
          const fr = new FileReader();
          fr.onload = () => resolve(String(fr.result).split(",")[1] || "");
          fr.onerror = () => reject(fr.error);
          fr.readAsDataURL(blob);
        });
        const r = await api<{ text: string }>("/assistant/transcribe", { method: "POST", json: { audio_base64: b64, mime_type: blob.type || "audio/webm", lang } });
        onText(r.text);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Could not understand the recording.");
      } finally {
        setState("idle");
      }
    };
    mediaRef.current = rec;
    rec.start();
    setState("recording");
    timerRef.current = setTimeout(() => rec.state === "recording" && rec.stop(), MAX_SECONDS * 1000);
  }

  function toggle() {
    setError(null);
    if (state === "listening") { recRef.current?.stop(); return; }
    if (state === "recording") { mediaRef.current?.stop(); return; }
    if (state === "transcribing") return;
    const SRClass = getSR();
    if (SRClass && !forceServer.current) startBrowser(SRClass);
    else startRecording();
  }

  if (!supported) return null;
  const active = state === "listening" || state === "recording";
  const label = state === "transcribing" ? "Converting speech to text" : active ? "Stop recording" : `Speak (${VOICE_LANGS.find((l) => l.code === lang)!.label})`;
  return (
    <span className={`relative inline-flex flex-col items-center ${className}`}>
      <button type="button" onClick={toggle} aria-label={label} title={label} aria-pressed={active}
        className={`grid h-11 w-11 shrink-0 place-items-center rounded-full transition ${active ? "animate-pulse bg-red-600 text-white" : "bg-navy-100 text-navy-900 hover:bg-navy-900 hover:text-white"}`}>
        {state === "transcribing" ? <Loader2 size={18} className="animate-spin" aria-hidden /> : active ? <Square size={16} aria-hidden /> : <Mic size={18} aria-hidden />}
      </button>
      <span role="status" aria-live="polite" className="sr-only">{active ? "Listening" : state === "transcribing" ? "Converting" : ""}</span>
      {error && <span role="alert" className="absolute right-0 top-12 z-20 w-64 rounded-lg bg-red-50 p-2 text-xs text-red-800 shadow ring-1 ring-red-200">{error}</span>}
    </span>
  );
}
