/**
 * DeviceSettingsPanel — Mic + Camera selectie voor privé-bellen.
 *
 * Puur lokaal: gebruikt navigator.mediaDevices.enumerateDevices() (browser API,
 * geen cloud). Slaat gekozen deviceId + label op in user-prefs zodat de
 * PriveCallBark straks direct de juiste input pakt.
 *
 * Test-knoppen openen tijdelijk een lokale stream om te tonen dat het apparaat
 * werkt (mic → VU-balk, cam → mini-preview). Streams worden meteen weer
 * gesloten (geen achtergrond-capture).
 */
import React, { useEffect, useRef, useState } from 'react';
import { Mic, Video, Camera, CheckCircle2, AlertTriangle, RefreshCw } from 'lucide-react';

export function DeviceSettingsPanel({ prefs, updatePref, savePrefs, saving }) {
  const [audioDevices, setAudioDevices] = useState([]);
  const [videoDevices, setVideoDevices] = useState([]);
  const [permError, setPermError] = useState(null);
  const [enumerated, setEnumerated] = useState(false);
  const [micTesting, setMicTesting] = useState(false);
  const [micLevel, setMicLevel] = useState(0);
  const [camTesting, setCamTesting] = useState(false);
  const videoRef = useRef(null);
  const micStreamRef = useRef(null);
  const camStreamRef = useRef(null);
  const audioCtxRef = useRef(null);
  const rafRef = useRef(null);

  const useDefault = prefs?.use_default_devices !== false;
  const audioId = prefs?.audio_input_device_id || 'default';
  const videoId = prefs?.video_input_device_id || 'default';

  const enumerate = async (askPermission = false) => {
    try {
      if (askPermission) {
        // Eenmalig toestemming vragen — anders zijn de labels leeg
        const s = await navigator.mediaDevices.getUserMedia({ audio: true, video: true });
        s.getTracks().forEach((t) => t.stop());
      }
      const list = await navigator.mediaDevices.enumerateDevices();
      setAudioDevices(list.filter((d) => d.kind === 'audioinput'));
      setVideoDevices(list.filter((d) => d.kind === 'videoinput'));
      setEnumerated(true);
      setPermError(null);
    } catch (e) {
      setPermError(e?.message || 'Kon apparaten niet ophalen');
      setEnumerated(true);
    }
  };

  useEffect(() => {
    enumerate(false);
    return () => stopAllStreams();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const stopAllStreams = () => {
    try { micStreamRef.current?.getTracks().forEach((t) => t.stop()); } catch { /* silent */ }
    try { camStreamRef.current?.getTracks().forEach((t) => t.stop()); } catch { /* silent */ }
    try { audioCtxRef.current?.close(); } catch { /* silent */ }
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    micStreamRef.current = null;
    camStreamRef.current = null;
    audioCtxRef.current = null;
    rafRef.current = null;
    setMicTesting(false);
    setCamTesting(false);
    setMicLevel(0);
  };

  const testMic = async () => {
    stopAllStreams();
    try {
      const constraints = {
        audio: useDefault || audioId === 'default' ? true : { deviceId: { exact: audioId } },
      };
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      micStreamRef.current = stream;
      const AC = window.AudioContext || window.webkitAudioContext;
      const ctx = new AC();
      audioCtxRef.current = ctx;
      const src = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 512;
      src.connect(analyser);
      const buf = new Uint8Array(analyser.frequencyBinCount);
      setMicTesting(true);
      const tick = () => {
        analyser.getByteTimeDomainData(buf);
        let peak = 0;
        for (let i = 0; i < buf.length; i++) {
          const v = Math.abs(buf[i] - 128);
          if (v > peak) peak = v;
        }
        setMicLevel(Math.min(1, peak / 128));
        rafRef.current = requestAnimationFrame(tick);
      };
      tick();
      // Auto-stop na 4s
      setTimeout(stopAllStreams, 4000);
    } catch (e) {
      setPermError(`Mic-test faalde: ${e.message}`);
    }
  };

  const testCam = async () => {
    stopAllStreams();
    try {
      const constraints = {
        video: useDefault || videoId === 'default' ? true : { deviceId: { exact: videoId } },
      };
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      camStreamRef.current = stream;
      setCamTesting(true);
      // Wacht 1 tick op mount van <video>
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play().catch(() => {});
        }
      }, 50);
      // Auto-stop na 5s
      setTimeout(stopAllStreams, 5000);
    } catch (e) {
      setPermError(`Camera-test faalde: ${e.message}`);
    }
  };

  const onSelectAudio = (id) => {
    const dev = audioDevices.find((d) => d.deviceId === id);
    const label = dev?.label || (id === 'default' ? 'Systeem-standaard microfoon' : 'Onbekend');
    updatePref('audio_input_device_id', id);
    updatePref('audio_input_label', label);
    savePrefs({ audio_input_device_id: id, audio_input_label: label });
  };

  const onSelectVideo = (id) => {
    const dev = videoDevices.find((d) => d.deviceId === id);
    const label = dev?.label || (id === 'default' ? 'Systeem-standaard camera' : 'Onbekend');
    updatePref('video_input_device_id', id);
    updatePref('video_input_label', label);
    savePrefs({ video_input_device_id: id, video_input_label: label });
  };

  const onToggleUseDefault = (checked) => {
    updatePref('use_default_devices', checked);
    const patch = { use_default_devices: checked };
    if (checked) {
      patch.audio_input_device_id = 'default';
      patch.video_input_device_id = 'default';
      patch.audio_input_label = 'Systeem-standaard microfoon';
      patch.video_input_label = 'Systeem-standaard camera';
      updatePref('audio_input_device_id', 'default');
      updatePref('video_input_device_id', 'default');
    }
    savePrefs(patch);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4" data-testid="devices-panel">
      <div className="flex items-center gap-2 mb-3">
        <Camera className="w-4 h-4 text-sky-400" />
        <h3 className="text-sm font-semibold text-white">Beeld & Geluid — Apparaten voor bellen</h3>
        <button
          data-testid="devices-refresh"
          onClick={() => enumerate(true)}
          className="ml-auto flex items-center gap-1 text-[10px] text-sky-300 hover:text-sky-200"
          title="Toestemming vragen + apparatenlijst verversen"
        >
          <RefreshCw className="w-3 h-3" /> Ververs
        </button>
      </div>
      <p className="text-[11px] text-slate-400 mb-3">
        Kies welke microfoon en camera je gebruikt bij privé-bellen. Volledig lokaal — geen data
        gaat naar de cloud. Als je het aan Spark overlaat pakt hij automatisch je systeem-standaard.
      </p>

      {permError && (
        <div className="mb-3 flex items-start gap-2 p-2 rounded-lg bg-red-500/10 border border-red-500/30">
          <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
          <div className="text-[11px] text-red-200">
            {permError}
            <div className="text-[10px] text-red-300/70 mt-1">
              Tip: klik &quot;Ververs&quot; en geef eenmalig toestemming voor mic + cam om de namen zichtbaar te maken.
            </div>
          </div>
        </div>
      )}

      {/* Systeem-default toggle */}
      <label className="flex items-center justify-between gap-3 p-2.5 rounded-lg bg-slate-800/40 border border-slate-800 cursor-pointer mb-3">
        <div>
          <p className="text-xs font-medium text-white">Gebruik systeem-standaard apparaten</p>
          <p className="text-[10px] text-slate-500">Aangeraden — Spark pakt automatisch je actieve mic + cam</p>
        </div>
        <input
          type="checkbox"
          data-testid="use-default-devices"
          checked={useDefault}
          onChange={(e) => onToggleUseDefault(e.target.checked)}
          className="w-4 h-4 accent-sky-500"
        />
      </label>

      {/* Microfoon */}
      <div className={`mb-3 ${useDefault ? 'opacity-50 pointer-events-none' : ''}`}>
        <div className="flex items-center gap-2 mb-1.5">
          <Mic className="w-3.5 h-3.5 text-slate-400" />
          <label className="text-[11px] font-medium text-slate-300">Microfoon</label>
        </div>
        <div className="flex items-center gap-2">
          <select
            data-testid="mic-select"
            value={audioId}
            onChange={(e) => onSelectAudio(e.target.value)}
            disabled={saving || useDefault}
            className="flex-1 px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-white"
          >
            <option value="default">Systeem-standaard microfoon</option>
            {audioDevices.map((d, i) => (
              <option key={d.deviceId} value={d.deviceId}>
                {d.label || `Microfoon ${i + 1}`}
              </option>
            ))}
          </select>
          <button
            data-testid="mic-test-btn"
            onClick={testMic}
            className="px-3 py-1.5 rounded bg-sky-500/20 border border-sky-500/40 text-sky-200 hover:bg-sky-500/30 text-xs font-medium"
          >
            Test
          </button>
        </div>
        {micTesting && (
          <div className="mt-2" data-testid="mic-vu-meter">
            <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
              <div
                className="h-full transition-all"
                style={{
                  width: `${Math.round(micLevel * 100)}%`,
                  background: 'linear-gradient(90deg, #34d399, #22d3ee, #f59e0b)',
                }}
              />
            </div>
            <p className="text-[10px] text-slate-500 mt-1">Spreek nu — je moet de balk zien bewegen (4s)</p>
          </div>
        )}
      </div>

      {/* Camera */}
      <div className={useDefault ? 'opacity-50 pointer-events-none' : ''}>
        <div className="flex items-center gap-2 mb-1.5">
          <Video className="w-3.5 h-3.5 text-slate-400" />
          <label className="text-[11px] font-medium text-slate-300">Camera</label>
        </div>
        <div className="flex items-center gap-2">
          <select
            data-testid="cam-select"
            value={videoId}
            onChange={(e) => onSelectVideo(e.target.value)}
            disabled={saving || useDefault}
            className="flex-1 px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-white"
          >
            <option value="default">Systeem-standaard camera</option>
            {videoDevices.map((d, i) => (
              <option key={d.deviceId} value={d.deviceId}>
                {d.label || `Camera ${i + 1}`}
              </option>
            ))}
          </select>
          <button
            data-testid="cam-test-btn"
            onClick={testCam}
            className="px-3 py-1.5 rounded bg-sky-500/20 border border-sky-500/40 text-sky-200 hover:bg-sky-500/30 text-xs font-medium"
          >
            Test
          </button>
        </div>
        {camTesting && (
          <div className="mt-2 rounded-lg overflow-hidden border border-slate-700" data-testid="cam-preview">
            <video
              ref={videoRef}
              className="w-full max-w-xs mx-auto block bg-black"
              autoPlay
              muted
              playsInline
              style={{ maxHeight: '180px' }}
            />
            <p className="text-[10px] text-slate-500 text-center py-1 bg-slate-900">Live preview (5s)</p>
          </div>
        )}
      </div>

      {enumerated && !audioDevices.length && !videoDevices.length && !permError && (
        <div className="mt-3 flex items-center gap-2 p-2 rounded bg-slate-800/40 text-[11px] text-slate-400">
          <CheckCircle2 className="w-3.5 h-3.5 text-slate-500" />
          Klik &quot;Ververs&quot; en geef toestemming voor mic + cam om apparaten te zien.
        </div>
      )}

      <p className="text-[10px] text-slate-500 mt-3">
        Huidige keuze: <span className="text-slate-300">{prefs?.audio_input_label || 'Systeem-standaard microfoon'}</span>
        {' · '}
        <span className="text-slate-300">{prefs?.video_input_label || 'Systeem-standaard camera'}</span>
      </p>
    </div>
  );
}
