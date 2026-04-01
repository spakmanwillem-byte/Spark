import React, { useState, useRef, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import {
  Mic, MicOff, Volume2, Square, Play, Loader2,
  Languages, Settings, Sparkles
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export function VoicePage({ onNavigate }) {
  const [voices, setVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState('nova');
  const [ttsText, setTtsText] = useState('');
  const [ttsLoading, setTtsLoading] = useState(false);
  const [ttsAudio, setTtsAudio] = useState(null);

  // STT
  const [recording, setRecording] = useState(false);
  const [sttResult, setSttResult] = useState('');
  const [sttLoading, setSttLoading] = useState(false);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const audioRef = useRef(null);

  useEffect(() => {
    fetch(`${API}/api/voice/voices`).then(r => r.json()).then(d => setVoices(d.voices || [])).catch(() => {});
  }, []);

  // TTS
  const speak = async () => {
    if (!ttsText.trim() || ttsLoading) return;
    setTtsLoading(true); setTtsAudio(null);
    const res = await fetch(`${API}/api/voice/tts`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: ttsText, voice: selectedVoice, format: 'base64' }),
    }).then(r => r.json()).catch(() => ({ success: false }));
    if (res.success && res.audio_base64) {
      const audioUrl = `data:audio/mpeg;base64,${res.audio_base64}`;
      setTtsAudio(audioUrl);
      const a = new Audio(audioUrl);
      a.play();
    }
    setTtsLoading(false);
  };

  // STT
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setSttLoading(true);
        const fd = new FormData();
        fd.append('audio', blob, 'recording.webm');
        fd.append('language', 'nl');
        const res = await fetch(`${API}/api/voice/stt`, { method: 'POST', body: fd }).then(r => r.json()).catch(() => ({ success: false }));
        if (res.success) setSttResult(res.text);
        else setSttResult(`Fout: ${res.error || 'Onbekend'}`);
        setSttLoading(false);
      };
      mediaRecorder.start();
      setRecording(true);
    } catch (e) {
      setSttResult('Microfoon toegang geweigerd');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  return (
    <MainLayout activePage="voice" onNavigate={onNavigate}>
      <div data-testid="voice-page" className="p-4 md:p-6 max-w-3xl mx-auto space-y-6">

        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-600 flex items-center justify-center">
            <Volume2 className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Voice</h1>
            <p className="text-xs text-slate-400">Speech-to-Text & Text-to-Speech</p>
          </div>
        </div>

        {/* TTS Section */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-800 flex items-center gap-2">
            <Volume2 className="w-4 h-4 text-violet-400" />
            <h2 className="text-sm font-semibold text-white">Text-to-Speech</h2>
          </div>
          <div className="p-4 space-y-3">
            <textarea data-testid="tts-input" value={ttsText} onChange={e => setTtsText(e.target.value)}
              placeholder="Typ tekst die je wilt laten voorlezen..."
              className="w-full h-24 px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-violet-500 resize-none"
            />
            <div className="flex items-center gap-3">
              <select data-testid="voice-select" value={selectedVoice} onChange={e => setSelectedVoice(e.target.value)}
                className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-violet-500">
                {voices.map(v => (
                  <option key={v.id} value={v.id}>{v.name} - {v.description}</option>
                ))}
              </select>
              <button data-testid="tts-speak" onClick={speak} disabled={ttsLoading || !ttsText.trim()}
                className="flex items-center gap-2 px-5 py-2 bg-violet-500 hover:bg-violet-600 text-white font-medium rounded-xl transition-colors disabled:opacity-50">
                {ttsLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                {ttsLoading ? 'Genereren...' : 'Voorlezen'}
              </button>
            </div>
            {ttsAudio && (
              <audio ref={audioRef} controls src={ttsAudio} className="w-full mt-2 rounded-xl" />
            )}
          </div>
        </div>

        {/* STT Section */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-800 flex items-center gap-2">
            <Mic className="w-4 h-4 text-rose-400" />
            <h2 className="text-sm font-semibold text-white">Speech-to-Text</h2>
            <span className="text-[10px] text-slate-500 ml-auto flex items-center gap-1"><Languages className="w-3 h-3" /> Nederlands</span>
          </div>
          <div className="p-4 space-y-4">
            <div className="flex flex-col items-center gap-4">
              <button data-testid="stt-record" onClick={recording ? stopRecording : startRecording}
                className={`w-20 h-20 rounded-full flex items-center justify-center transition-all ${
                  recording ? 'bg-red-500 animate-pulse scale-110 shadow-lg shadow-red-500/30' : 'bg-slate-800 hover:bg-slate-700 border border-slate-700'
                }`}>
                {sttLoading ? <Loader2 className="w-8 h-8 text-white animate-spin" />
                  : recording ? <Square className="w-8 h-8 text-white" />
                  : <Mic className="w-8 h-8 text-rose-400" />}
              </button>
              <p className="text-xs text-slate-400">
                {recording ? 'Opnemen... Klik om te stoppen' : sttLoading ? 'Transcriberen...' : 'Klik om op te nemen'}
              </p>
            </div>
            {sttResult && (
              <div data-testid="stt-result" className="p-4 bg-slate-800/50 rounded-xl">
                <p className="text-[10px] text-slate-500 mb-1">Resultaat:</p>
                <p className="text-sm text-white">{sttResult}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

export default VoicePage;
