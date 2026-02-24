import { useState, useRef, useCallback } from 'react';
import { useToast } from '../../context/ToastContext';
import { motion } from 'framer-motion';
import { Mic, Upload, X, Loader2, CheckCircle2, Music } from 'lucide-react';
import { API_BASE } from '../../utils/api';

export default function AudioUpload({ projectId, autoGenerate = false, onTranscriptReady }) {
    const { addToast } = useToast();
    const [file, setFile] = useState(null);
    const [status, setStatus] = useState('idle'); // idle, uploading, done
    const [progress, setProgress] = useState(0);
    const inputRef = useRef(null);

    const handleFileSelect = useCallback((selectedFile) => {
        const allowed = ['audio/mpeg', 'audio/wav', 'audio/webm', 'audio/ogg', 'audio/x-m4a', 'audio/flac', 'audio/mp3'];
        // Some systems might use generic audio/* or empty strings for some types, so we also check extension
        const extension = selectedFile.name.split('.').pop().toLowerCase();
        const allowedExtensions = ['mp3', 'wav', 'webm', 'ogg', 'm4a', 'flac'];

        if (!allowed.includes(selectedFile.type) && !allowedExtensions.includes(extension)) {
            addToast('Please select a valid audio file (MP3, WAV, M4A, etc.).', 'error');
            return;
        }

        const maxSize = 50 * 1024 * 1024; // 50MB
        if (selectedFile.size > maxSize) {
            addToast('Audio file is too large. Maximum size is 50MB.', 'error');
            return;
        }

        setFile(selectedFile);
    }, []);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        if (e.dataTransfer.files[0]) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    }, [handleFileSelect]);

    const handleUpload = useCallback(async () => {
        if (!file) return;

        const formData = new FormData();
        formData.append('audio', file);
        formData.append('project_id', projectId);
        formData.append('auto_generate', autoGenerate);

        setStatus('uploading');
        setProgress(0);

        try {
            const token = localStorage.getItem('vansh_token');
            const xhr = new XMLHttpRequest();

            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable) {
                    setProgress(Math.round((e.loaded / e.total) * 100));
                }
            };

            await new Promise((resolve, reject) => {
                xhr.onload = () => {
                    if (xhr.status >= 200 && xhr.status < 300) resolve();
                    else reject(new Error('Upload failed'));
                };
                xhr.onerror = reject;
                const url = API_BASE;
                xhr.open('POST', `${url}/api/unguided/transcribe`);
                xhr.setRequestHeader('Authorization', `Bearer ${token}`);
                xhr.send(formData);
            });

            setStatus('done');
            addToast('Audio uploaded successfully!', 'success');
            onTranscriptReady?.();
        } catch (err) {
            console.error('Audio upload error:', err);
            setStatus('idle');
            addToast('Failed to upload audio. Please try again.', 'error');
        }
    }, [file, projectId, autoGenerate, onTranscriptReady]);

    const clearFile = () => {
        setFile(null);
        setStatus('idle');
        setProgress(0);
        if (inputRef.current) inputRef.current.value = '';
    };

    const formatSize = (bytes) => {
        if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
        return `${(bytes / 1024).toFixed(0)} KB`;
    };

    return (
        <div className="py-6 px-2">
            <div className="max-w-2xl mx-auto">
                <div className="flex items-center gap-3 mb-4">
                    <Music size={20} style={{ color: 'var(--color-gold)' }} />
                    <h3 className="font-serif text-lg" style={{ color: 'var(--color-midnight)' }}>
                        Upload Audio File
                    </h3>
                </div>

                <p className="text-sm mb-5" style={{ color: 'var(--color-warm-gray)' }}>
                    Upload an existing audio recording and we'll transcribe it
                    into your story. Perfect for interviews or voice notes.
                </p>

                {!file ? (
                    /* Drop zone */
                    <motion.div
                        className="rounded-xl p-12 text-center cursor-pointer"
                        style={{
                            border: '2px dashed rgba(201, 168, 76, 0.3)',
                            background: 'rgba(201, 168, 76, 0.03)',
                        }}
                        whileHover={{ borderColor: 'var(--color-gold)', background: 'rgba(201, 168, 76, 0.06)' }}
                        onClick={() => inputRef.current?.click()}
                        onDragOver={(e) => e.preventDefault()}
                        onDrop={handleDrop}
                    >
                        <Mic size={48} style={{ color: 'var(--color-gold)', margin: '0 auto 1rem', opacity: 0.5 }} />
                        <p className="font-medium mb-1" style={{ color: 'var(--color-charcoal)' }}>
                            Drag & drop your audio file here
                        </p>
                        <p className="text-sm" style={{ color: 'var(--color-warm-gray)' }}>
                            or click to browse. Max 50MB · MP3, WAV, M4A, FLAC
                        </p>
                    </motion.div>
                ) : (
                    /* File preview */
                    <div className="rounded-xl p-6" style={{ background: '#fff', border: '1px solid rgba(0,0,0,0.08)' }}>
                        <div className="flex items-start justify-between mb-4">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-lg flex items-center justify-center"
                                    style={{ background: 'rgba(201, 168, 76, 0.1)' }}>
                                    <Music size={20} style={{ color: 'var(--color-gold)' }} />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="font-medium text-sm truncate max-w-xs" style={{ color: 'var(--color-charcoal)' }}>
                                        {file.name}
                                    </p>
                                    <p className="text-xs" style={{ color: 'var(--color-warm-gray)' }}>
                                        {formatSize(file.size)}
                                    </p>
                                </div>
                            </div>
                            {status === 'idle' && (
                                <button onClick={clearFile} className="p-1 bg-transparent border-none cursor-pointer">
                                    <X size={18} style={{ color: 'var(--color-warm-gray)' }} />
                                </button>
                            )}
                        </div>

                        {/* Audio Player Preview */}
                        <audio
                            src={URL.createObjectURL(file)}
                            className="w-full mb-4 h-10"
                            controls
                        />

                        {/* Upload progress */}
                        {status === 'uploading' && (
                            <div className="mb-4">
                                <div className="flex items-center justify-between mb-1">
                                    <span className="text-xs" style={{ color: 'var(--color-warm-gray)' }}>Uploading...</span>
                                    <span className="text-xs font-medium" style={{ color: 'var(--color-gold)' }}>{progress}%</span>
                                </div>
                                <div className="w-full h-2 rounded-full" style={{ background: 'rgba(0,0,0,0.05)' }}>
                                    <motion.div
                                        className="h-full rounded-full"
                                        style={{ background: 'linear-gradient(90deg, var(--color-gold), var(--color-gold-light))' }}
                                        initial={{ width: 0 }}
                                        animate={{ width: `${progress}%` }}
                                    />
                                </div>
                            </div>
                        )}

                        {/* Actions */}
                        {status === 'idle' && (
                            <motion.button
                                onClick={handleUpload}
                                className="btn-primary w-full"
                                whileHover={{ scale: 1.02 }}
                            >
                                <Upload size={16} /> Upload & Transcribe Audio
                            </motion.button>
                        )}

                        {status === 'uploading' && progress === 100 && (
                            <div className="flex items-center gap-2 justify-center">
                                <Loader2 size={18} className="animate-spin" style={{ color: 'var(--color-gold)' }} />
                                <span className="text-sm" style={{ color: 'var(--color-warm-gray)' }}>Processing audio...</span>
                            </div>
                        )}

                        {status === 'done' && (
                            <div className="flex items-center gap-2 justify-center">
                                <CheckCircle2 size={18} style={{ color: 'var(--color-success)' }} />
                                <span className="text-sm" style={{ color: 'var(--color-success)' }}>Audio uploaded! Check progress below.</span>
                            </div>
                        )}
                    </div>
                )}

                <input
                    ref={inputRef}
                    type="file"
                    accept="audio/*"
                    className="hidden"
                    onChange={(e) => e.target.files[0] && handleFileSelect(e.target.files[0])}
                />
            </div>
        </div>
    );
}
