import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './VoiceControls.css';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const VoiceControls = ({ onTranscriptReceived, settings, onSettingsChange }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Check if browser supports audio recording
  const isSupported = navigator.mediaDevices && navigator.mediaDevices.getUserMedia;

  const startRecording = async () => {
    if (!isSupported) {
      setError('❌ Je browser ondersteunt geen audio opname');
      return;
    }

    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Use webm for better browser compatibility
      const options = { mimeType: 'audio/webm' };
      mediaRecorderRef.current = new MediaRecorder(stream, options);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await sendAudioToBackend(audioBlob);
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Microphone access error:', err);
      setError('❌ Geen toegang tot microfoon. Geef toestemming in je browser.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsProcessing(true);
    }
  };

  const sendAudioToBackend = async (audioBlob) => {
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');
      formData.append('language', settings?.stt?.language || 'nl');

      const response = await axios.post(`${API}/voice/stt`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      if (response.data.success && response.data.text) {
        onTranscriptReceived(response.data.text);
      } else {
        setError('❌ Geen tekst herkend. Probeer opnieuw.');
      }
    } catch (err) {
      console.error('STT Error:', err);
      setError('❌ Fout bij spraakherkenning. Probeer opnieuw.');
    } finally {
      setIsProcessing(false);
    }
  };

  if (!isSupported) {
    return (
      <div className="voice-controls unsupported">
        <span>❌ Voice input niet ondersteund in deze browser</span>
      </div>
    );
  }

  if (!settings?.stt?.enabled) {
    return null; // Don't show if STT is disabled
  }

  return (
    <div className="voice-controls">
      {error && (
        <div className="voice-error">
          {error}
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}
      
      <button
        className={`voice-button ${isRecording ? 'recording' : ''} ${isProcessing ? 'processing' : ''}`}
        onMouseDown={settings?.stt?.push_to_talk ? startRecording : null}
        onMouseUp={settings?.stt?.push_to_talk ? stopRecording : null}
        onTouchStart={settings?.stt?.push_to_talk ? startRecording : null}
        onTouchEnd={settings?.stt?.push_to_talk ? stopRecording : null}
        onClick={!settings?.stt?.push_to_talk ? (isRecording ? stopRecording : startRecording) : null}
        disabled={isProcessing}
        title={settings?.stt?.push_to_talk ? "Houd vast om te spreken" : "Klik om opname te starten/stoppen"}
      >
        {isProcessing ? (
          <>🔄 Verwerken...</>
        ) : isRecording ? (
          <>🔴 Opnemen...</>
        ) : (
          <>🎤 Spreek</>
        )}
      </button>

      {isRecording && settings?.stt?.push_to_talk && (
        <div className="recording-hint">
          Houd knop vast terwijl je spreekt
        </div>
      )}
    </div>
  );
};

export default VoiceControls;
