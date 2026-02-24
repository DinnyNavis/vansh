import { useState, useRef, useCallback, useEffect } from 'react';
import { useToast } from '../../context/ToastContext';
import { useSocket } from '../../context/SocketContext';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Square, Upload, Loader2, CheckCircle2 } from 'lucide-react';
import { API_BASE } from '../../utils/api';

export default function AudioRecorder({ projectId, autoGenerate = false, onTranscriptReady }) {
    const { addToast } = useToast();
    const { socketRef, connected } = useSocket();
    const [status, setStatus] = useState('idle'); // idle, recording, uploading, done
    const [duration, setDuration] = useState(0);
    const [levels, setLevels] = useState(Array(20).fill(8));

    const mediaRecorderRef = useRef(null);
    const chunksRef = useRef([]);
    const timerRef = useRef(null);
    const streamRef = useRef(null);
    const audioContextRef = useRef(null);
    const analyserRef = useRef(null);
    const animationFrameRef = useRef(null);

    const startRecording = useCallback(async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            streamRef.current = stream;

            // Audio Visualizer Setup
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const source = audioContext.createMediaStreamSource(stream);
            const analyser = audioContext.createAnalyser();
            analyser.fftSize = 64;
            source.connect(analyser);

            audioContextRef.current = audioContext;
            analyserRef.current = analyser;

            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);

            const updateVisualizer = () => {
                analyser.getByteFrequencyData(dataArray);
                // Map the frequency data to 20 bars
                const newLevels = [];
                for (let i = 0; i < 20; i++) {
                    const val = dataArray[i % bufferLength] || 0;
                    newLevels.push(8 + (val / 255) * 50);
                }
                setLevels(newLevels);
                animationFrameRef.current = requestAnimationFrame(updateVisualizer);
            };
            updateVisualizer();

            // Real-time: Notify backend to start Deepgram session
            if (socketRef.current?.connected) {
                socketRef.current.emit('start_transcription', { project_id: projectId });
            }

            const mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus',
                audioBitsPerSecond: 128000 // Higher quality for Crystal Clear accuracy
            });

            chunksRef.current = [];

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    chunksRef.current.push(e.data);
                    // Real-time: Stream chunk to backend
                    if (socketRef.current?.connected) {
                        socketRef.current.emit('audio_chunk', e.data);
                    }
                }
            };

            mediaRecorder.onstop = () => {
                clearInterval(timerRef.current);
                if (streamRef.current) {
                    streamRef.current.getTracks().forEach((t) => t.stop());
                }
                // Real-time: Notify backend to finalize
                if (socketRef.current?.connected) {
                    socketRef.current.emit('stop_transcription', { project_id: projectId });
                }
            };


            mediaRecorder.start(250); // Small chunks for real-time feel
            mediaRecorderRef.current = mediaRecorder;
            setStatus('recording');
            setDuration(0);

            timerRef.current = setInterval(() => {
                setDuration((d) => d + 1);
            }, 1000);
        } catch (err) {
            console.error('Microphone access denied:', err);
            addToast('Please allow microphone access to record audio.', 'error');
        }
    }, [projectId, socketRef]);

    const stopRecording = useCallback(() => {
        if (mediaRecorderRef.current?.state === 'recording') {
            mediaRecorderRef.current.stop();
        }
        if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
        if (audioContextRef.current) {
            try { audioContextRef.current.close(); } catch (e) { }
        }

        clearInterval(timerRef.current);
        setStatus('idle');
    }, []);

    const uploadRecording = useCallback(async () => {
        if (chunksRef.current.length === 0) return;

        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('audio', blob, 'recording.webm');
        formData.append('project_id', projectId);
        formData.append('auto_generate', autoGenerate);

        setStatus('uploading');

        try {
            const token = localStorage.getItem('vansh_token');
            const url = API_BASE;
            const res = await fetch(`${url}/api/unguided/transcribe`, {
                method: 'POST',
                headers: { Authorization: `Bearer ${token}` },
                body: formData,
            });

            if (!res.ok) throw new Error('Upload failed');

            setStatus('done');
            addToast('Recording sent successfully!', 'success');
            onTranscriptReady?.();
        } catch (err) {
            console.error('Upload error:', err);
            setStatus('idle');
            addToast('Failed to upload recording. Please try again.', 'error');
        }
    }, [projectId, autoGenerate, onTranscriptReady]);

    const formatTime = (seconds) => {
        const m = Math.floor(seconds / 60).toString().padStart(2, '0');
        const s = (seconds % 60).toString().padStart(2, '0');
        return `${m}:${s}`;
    };

    return (
        <div className="flex flex-col items-center gap-6 py-8">
            {/* Waveform Visualization */}
            <AnimatePresence mode="wait">
                {status === 'recording' && (
                    <motion.div
                        className="flex items-center gap-1 h-16"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                    >
                        {levels.map((height, i) => (
                            <motion.div
                                key={i}
                                className="w-1 rounded-full"
                                style={{
                                    background: 'var(--color-gold)',
                                    height: `${height}px`
                                }}
                                transition={{
                                    type: 'spring',
                                    stiffness: 300,
                                    damping: 30
                                }}
                            />
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Timer */}
            {(status === 'recording' || chunksRef.current.length > 0) && (
                <div className="font-mono text-3xl font-light" style={{ color: 'var(--color-charcoal)' }}>
                    {formatTime(duration)}
                </div>
            )}

            {/* Controls */}
            <div className="flex items-center gap-4">
                {status === 'idle' && chunksRef.current.length === 0 && (
                    <motion.button
                        onClick={startRecording}
                        className="w-20 h-20 rounded-full flex items-center justify-center cursor-pointer border-none"
                        style={{
                            background: 'linear-gradient(135deg, var(--color-gold), var(--color-gold-light))',
                            boxShadow: '0 4px 20px rgba(201, 168, 76, 0.3)',
                        }}
                        whileHover={{ scale: 1.08 }}
                        whileTap={{ scale: 0.95 }}
                    >
                        <Mic size={32} style={{ color: 'var(--color-midnight)' }} />
                    </motion.button>
                )}

                {status === 'recording' && (
                    <motion.button
                        onClick={stopRecording}
                        className="w-20 h-20 rounded-full flex items-center justify-center cursor-pointer border-none"
                        style={{
                            background: 'linear-gradient(135deg, #f87171, #ef4444)',
                            boxShadow: '0 4px 20px rgba(248, 113, 113, 0.3)',
                        }}
                        whileHover={{ scale: 1.08 }}
                        whileTap={{ scale: 0.95 }}
                        animate={{ scale: [1, 1.05, 1] }}
                        transition={{ duration: 1.5, repeat: Infinity }}
                    >
                        <Square size={24} fill="#fff" style={{ color: '#fff' }} />
                    </motion.button>
                )}

                {status === 'idle' && chunksRef.current.length > 0 && (
                    <>
                        <motion.button
                            onClick={startRecording}
                            className="w-14 h-14 rounded-full flex items-center justify-center cursor-pointer border-none"
                            style={{ background: 'rgba(0,0,0,0.05)', border: '2px solid rgba(0,0,0,0.1)' }}
                            whileHover={{ scale: 1.05 }}
                        >
                            <Mic size={22} style={{ color: 'var(--color-charcoal)' }} />
                        </motion.button>
                        <motion.button
                            onClick={uploadRecording}
                            className="btn-primary"
                            style={{ padding: '0.85rem 2rem', fontSize: '1rem' }}
                            whileHover={{ scale: 1.03 }}
                        >
                            <Upload size={18} /> Send for Transcription
                        </motion.button>
                    </>
                )}

                {status === 'uploading' && (
                    <div className="flex items-center gap-3">
                        <Loader2 size={24} className="animate-spin" style={{ color: 'var(--color-gold)' }} />
                        <span style={{ color: 'var(--color-warm-gray)' }}>Uploading & transcribing...</span>
                    </div>
                )}

                {status === 'done' && (
                    <div className="flex items-center gap-2">
                        <CheckCircle2 size={24} style={{ color: 'var(--color-success)' }} />
                        <span style={{ color: 'var(--color-success)' }}>Recording sent! Check progress below.</span>
                    </div>
                )}
            </div>

            {/* Hint */}
            {status === 'idle' && chunksRef.current.length === 0 && (
                <p className="text-sm text-center max-w-sm" style={{ color: 'var(--color-warm-gray)' }}>
                    Click the microphone to start recording your story.
                    Speak naturally — we'll handle the rest.
                </p>
            )}
        </div>
    );
}
