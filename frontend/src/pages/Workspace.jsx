import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
    BookOpen, Mic, FileText, Video, ArrowLeft, Sparkles,
    Download, Loader2, ImagePlus, RefreshCw, CheckCircle2, Music
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useSocket } from '../context/SocketContext';
import { useToast } from '../context/ToastContext';
import api from '../utils/api';
import AudioRecorder from '../components/workspace/AudioRecorder';
import AudioUpload from '../components/workspace/AudioUpload';
import TextInput from '../components/workspace/TextInput';
import VideoUpload from '../components/workspace/VideoUpload';
import ProgressTracker from '../components/workspace/ProgressTracker';
import BookPreview from '../components/workspace/BookPreview';
import confetti from 'canvas-confetti';

const inputMethods = [
    { value: 'audio', icon: Mic, label: 'Record Audio', emoji: '🎤' },
    { value: 'upload-audio', icon: Music, label: 'Upload Audio', emoji: '🎵' },
    { value: 'text', icon: FileText, label: 'Write Text', emoji: '⌨️' },
    { value: 'video', icon: Video, label: 'Upload Video', emoji: '🎥' },
];

export default function Workspace() {
    const { projectId } = useParams();
    const navigate = useNavigate();
    const { user } = useAuth();
    const { connected, joinProject, leaveProject, onProgress, onRealtimeTranscript } = useSocket();
    const { addToast } = useToast();

    const [project, setProject] = useState(null);
    const [loading, setLoading] = useState(true);
    const [inputType, setInputType] = useState(null);
    const [autoGenerate, setAutoGenerate] = useState(true);

    // Progress state
    const [progressStage, setProgressStage] = useState(null);
    const [progressPercent, setProgressPercent] = useState(0);
    const [progressMessage, setProgressMessage] = useState('');

    // Action states
    const [generatingBook, setGeneratingBook] = useState(false);
    const [generatingImages, setGeneratingImages] = useState(false);
    const [generatingPdf, setGeneratingPdf] = useState(false);

    useEffect(() => {
        if (projectId && connected) {
            const unsub = onRealtimeTranscript((data) => {
                if (data.project_id !== projectId) return;
                // Append only if it's new/meaningful
                setProject(prev => {
                    const currentText = prev.transcript || "";
                    if (data.is_final) {
                        return { ...prev, transcript: currentText + " " + data.transcript };
                    } else {
                        // For interim results, we could show them in a special way, 
                        // but for now let's just show final snippets to avoid flicker.
                        return prev;
                    }
                });
                // Ensure we stay in transcribing status if we see live words
                setProgressStage('transcribing');
            });
            return () => { unsub(); };
        }
    }, [projectId, connected, onRealtimeTranscript]);

    // Fetch project
    useEffect(() => {
        const fetchProject = async () => {
            try {
                const res = await api.get(`/projects/${projectId}`);
                setProject(res.data.project);
                setInputType(res.data.project.input_type || 'audio');
            } catch (err) {
                console.error('Failed to fetch project:', err);
                navigate('/dashboard');
            } finally {
                setLoading(false);
            }
        };
        fetchProject();
    }, [projectId, navigate]);

    // Socket connections
    useEffect(() => {
        if (projectId && connected) {
            joinProject(projectId);
            addToast('Synchronizing with live server...', 'info');

            const unsub = onProgress((data) => {
                if (data.project_id !== projectId) return;
                setProgressStage(data.stage);
                setProgressPercent(data.progress);
                setProgressMessage(data.message);

                if (data.stage === 'transcribing' && data.data?.raw_transcript) {
                    setProject(prev => ({ ...prev, transcript: data.data.raw_transcript, status: 'transcribing' }));
                }
                if (data.stage === 'transcribed' && data.data?.transcript) {
                    setProject(prev => ({ ...prev, transcript: data.data.transcript, status: 'transcribed' }));
                    setProgressPercent(100);
                    // If auto-gen is coming, show a transition message
                    if (autoGenerate) {
                        setTimeout(() => setProgressMessage("Narrative locked. Initializing chapter transformation..."), 500);
                    }
                }
                if (data.stage === 'chapters_complete') {
                    setProject(prev => ({
                        ...prev,
                        chapters: data.data.chapters,
                        cover_title: data.data.cover_title || prev.cover_title,
                        status: 'chapters_ready'
                    }));
                    setGeneratingBook(false);
                    setProgressStage(null);
                }
                if (data.stage === 'image_ready') {
                    setProject(prev => ({
                        ...prev,
                        chapters: prev.chapters.map(ch => ch.id === data.data.chapter_id ? { ...ch, image_url: data.data.image_url, image_type: 'ai' } : ch)
                    }));
                }
                if (data.stage === 'all_images_complete') {
                    setGeneratingImages(false);
                    refreshProject();
                }
                if (data.stage === 'pdf_ready') {
                    setProject(prev => ({ ...prev, pdf_url: data.data.pdf_url, status: 'complete' }));
                    setGeneratingPdf(false);
                    confetti({ particleCount: 150, spread: 70, origin: { y: 0.6 }, colors: ['#c9a84c', '#e8d48b', '#ffffff'] });
                }
                if (data.stage === 'error') {
                    setGeneratingBook(false); setGeneratingImages(false); setGeneratingPdf(false);
                }
            });
            return () => { unsub(); };
        }
    }, [projectId, joinProject, onProgress, connected]);

    const refreshProject = async () => {
        try {
            const res = await api.get(`/projects/${projectId}`);
            setProject(res.data.project);
        } catch (err) { console.error(err); }
    };

    const handleGenerateBook = async () => {
        setGeneratingBook(true);
        try { await api.post('/unguided/generate-book', { project_id: projectId }); }
        catch (err) { setGeneratingBook(false); }
    };

    const handleGenerateAllImages = async () => {
        setGeneratingImages(true);
        try { await api.post('/unguided/generate-all-images', { project_id: projectId }); }
        catch (err) { setGeneratingImages(false); }
    };

    const handleGeneratePdf = async () => {
        setGeneratingPdf(true);
        try { await api.post('/unguided/generate-pdf', { project_id: projectId }); }
        catch (err) { setGeneratingPdf(false); }
    };

    const handleDownloadPdf = async () => {
        if (!project?.pdf_url) return;
        try {
            const path = project.pdf_url.startsWith('/api') ? project.pdf_url.slice(4) : project.pdf_url;
            const res = await api.get(path, { responseType: 'blob' });
            const blob = new Blob([res.data], { type: 'application/pdf' });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `${project.title || 'book'}.pdf`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        } catch (err) { console.error(err); }
    };

    const handleChaptersUpdate = (updatedChapters) => {
        setProject((prev) => ({ ...prev, chapters: updatedChapters }));
    };

    if (loading) return (
        <div className="min-h-screen flex items-center justify-center bg-ivory">
            <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 2, ease: "linear" }}>
                <BookOpen size={48} className="text-gold opacity-40" />
            </motion.div>
        </div>
    );

    const hasTranscript = project?.transcript || project?.refined_text;
    const hasChapters = project?.chapters?.length > 0;

    return (
        <div className="min-h-screen bg-cream">
            {/* Action Bar / Nav */}
            <nav className="sticky top-0 z-50 glass-card" style={{ borderRadius: 0, borderBottom: '1px solid rgba(0,0,0,0.06)' }}>
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-6">
                        <Link to="/dashboard" className="p-2 hover:bg-black/5 rounded-full transition-colors"><ArrowLeft size={20} className="text-warm-gray" /></Link>
                        <h2 className="text-xl font-serif text-midnight truncate max-w-sm">{project?.title}</h2>
                    </div>

                    <div className="flex items-center gap-4">
                        <button onClick={refreshProject} className="p-2 bg-transparent border-none cursor-pointer text-warm-gray hover:text-gold transition-colors"><RefreshCw size={18} /></button>
                        {project?.pdf_url && (
                            <button onClick={handleDownloadPdf} className="btn-primary btn-gold" style={{ padding: '0.6rem 1.4rem', fontSize: '0.85rem' }}>
                                <Download size={16} /> Download Final PDF
                            </button>
                        )}
                    </div>
                </div>
            </nav>

            <div className="max-w-7xl mx-auto px-6 py-12">
                <main className="grid grid-cols-1 lg:grid-cols-12 gap-10">
                    <div className="lg:col-span-12 xl:col-span-12">
                        <AnimatePresence mode="wait">
                            {/* Step 1: Input Selection */}
                            {!hasTranscript && !hasChapters && !progressStage && (
                                <motion.section
                                    key="input-step"
                                    className="glass-card p-10 mb-10"
                                    initial={{ opacity: 0, y: 30 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -30 }}
                                    transition={{ duration: 0.5, ease: "easeOut" }}
                                >
                                    <div className="flex items-center gap-3 mb-8">
                                        <Sparkles size={24} className="text-gold" />
                                        <h3 className="text-3xl font-serif text-midnight">How shall we record your story?</h3>
                                    </div>

                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
                                        {inputMethods.map((m) => (
                                            <button
                                                key={m.value}
                                                onClick={() => setInputType(m.value)}
                                                className={`p-6 rounded-2xl transition-all border-2 text-center group ${inputType === m.value ? 'bg-gold/10 border-gold' : 'bg-white border-black/5 hover:border-black/10'}`}
                                            >
                                                <span className="text-3xl mb-2 block group-hover:scale-110 transition-transform">{m.emoji}</span>
                                                <span className={`text-xs font-accent font-bold uppercase tracking-widest ${inputType === m.value ? 'text-gold' : 'text-warm-gray'}`}>{m.label}</span>
                                            </button>
                                        ))}
                                    </div>

                                    <div className="flex items-center justify-between mb-8 p-6 bg-gold/5 rounded-2xl border border-gold/10">
                                        <div className="flex items-center gap-4">
                                            <div className="p-3 bg-gold/10 rounded-xl">
                                                <Sparkles size={20} className="text-gold" />
                                            </div>
                                            <div>
                                                <h4 className="text-sm font-bold uppercase tracking-widest text-midnight">Fully Automated Legacy</h4>
                                                <p className="text-xs text-warm-gray">One click to transcribe, draft, and illustrate your book.</p>
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => setAutoGenerate(!autoGenerate)}
                                            className="relative border-none bg-transparent cursor-pointer"
                                        >
                                            <div className={`w-14 h-7 rounded-full transition-colors ${autoGenerate ? 'bg-gold' : 'bg-warm-gray/30'}`}>
                                                <motion.div
                                                    animate={{ x: autoGenerate ? 30 : 4 }}
                                                    className="absolute top-1 w-5 h-5 bg-white rounded-full shadow-sm"
                                                />
                                            </div>
                                        </button>
                                    </div>

                                    <AnimatePresence mode="wait">
                                        <motion.div key={inputType} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                                            {inputType === 'audio' && <AudioRecorder projectId={projectId} autoGenerate={autoGenerate} onTranscriptReady={() => { setProgressStage('uploading'); setProgressPercent(100); setProgressMessage('Audio sent! Starting transcription...'); refreshProject(); }} />}
                                            {inputType === 'upload-audio' && <AudioUpload projectId={projectId} autoGenerate={autoGenerate} onTranscriptReady={() => { setProgressStage('uploading'); setProgressPercent(100); setProgressMessage('Audio uploaded! Processing...'); refreshProject(); }} />}
                                            {inputType === 'text' && <TextInput projectId={projectId} autoGenerate={autoGenerate} onTranscriptReady={() => { setProgressStage('refining'); setProgressPercent(5); setProgressMessage('Text received! Refined manuscript incoming...'); refreshProject(); }} />}
                                            {inputType === 'video' && <VideoUpload projectId={projectId} autoGenerate={autoGenerate} onTranscriptReady={() => { setProgressStage('extracting'); setProgressPercent(5); setProgressMessage('Video uploaded! Extracting audio...'); refreshProject(); }} />}
                                        </motion.div>
                                    </AnimatePresence>
                                </motion.section>
                            )}

                            {/* Step 2: Transcript & Progress */}
                            {(hasTranscript || (progressStage && progressStage !== 'error')) && !hasChapters && (
                                <motion.section
                                    key="transcript-step"
                                    className="grid grid-cols-1 lg:grid-cols-12 gap-10 mb-10"
                                    initial={{ opacity: 0, x: 50 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: -50 }}
                                    transition={{ duration: 0.5, ease: "easeOut" }}
                                >
                                    <div className="lg:col-span-12 xl:col-span-7 glass-card p-10">
                                        <h3 className="text-2xl font-serif text-midnight mb-6">Draft Manuscript</h3>
                                        <div className="max-h-[500px] overflow-y-auto pr-4 font-body text-lg leading-relaxed text-charcoal/80 space-y-4 scroll-slim">
                                            {hasTranscript ? (
                                                (project.refined_text || project.transcript).split('\n').map((p, i) => <p key={i}>{p}</p>)
                                            ) : (
                                                <div className="space-y-4 opacity-30 animate-pulse">
                                                    <div className="h-4 bg-charcoal/20 rounded w-3/4"></div>
                                                    <div className="h-4 bg-charcoal/20 rounded w-5/6"></div>
                                                    <div className="h-4 bg-charcoal/20 rounded w-2/3"></div>
                                                    <p className="italic text-sm pt-4">Your manuscript will appear here shortly...</p>
                                                </div>
                                            )}
                                        </div>
                                        <div className="mt-10 pt-8 border-t border-black/5">
                                            <button
                                                onClick={handleGenerateBook}
                                                disabled={generatingBook}
                                                className="btn-primary w-full justify-center btn-gold text-lg py-4 shadow-xl shadow-gold/20"
                                            >
                                                {generatingBook ? <Loader2 className="animate-spin" /> : <><Sparkles size={20} /> Transform to Chapters</>}
                                            </button>
                                        </div>
                                    </div>
                                    <div className="lg:col-span-12 xl:col-span-5 flex flex-col gap-6">
                                        <AnimatePresence mode="wait">
                                            {progressStage && (
                                                <motion.div
                                                    key="progress-tracker"
                                                    initial={{ opacity: 0, scale: 0.95 }}
                                                    animate={{ opacity: 1, scale: 1 }}
                                                    exit={{ opacity: 0, scale: 0.95 }}
                                                    className="glass-card p-8 border-gold/20"
                                                >
                                                    <ProgressTracker currentStage={progressStage} progress={progressPercent} message={progressMessage} />
                                                </motion.div>
                                            )}
                                        </AnimatePresence>
                                        <div className="glass-dark p-8 rounded-[32px] text-ivory relative overflow-hidden group">
                                            <div className="absolute top-0 right-0 p-10 opacity-5 group-hover:opacity-10 transition-opacity">
                                                <Sparkles size={120} />
                                            </div>
                                            <h4 className="text-xl font-serif mb-4 flex items-center gap-3"><CheckCircle2 className="text-gold" /> The VANSH Process</h4>
                                            <p className="text-sm opacity-60 leading-relaxed mb-6">Our AI is currently analyzing your narration to identify key themes, chronological structures, and emotional peaks to craft your final book chapters.</p>
                                            <div className="flex items-center gap-4 py-3 px-4 bg-white/5 rounded-xl border border-white/5 backdrop-blur-sm">
                                                <Loader2 size={16} className="text-gold animate-spin" />
                                                <span className="text-xs font-accent uppercase tracking-widest opacity-80">Refining Legacy Intelligence...</span>
                                            </div>
                                        </div>
                                    </div>
                                </motion.section>
                            )}

                            {/* Step 3: The Published Book */}
                            {hasChapters && (
                                <motion.div
                                    key="book-step"
                                    className="space-y-12"
                                    initial={{ opacity: 0, y: 50 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.6, ease: "easeOut" }}
                                >
                                    <div className="flex flex-wrap items-center justify-between gap-6 pb-6 border-b border-black/5">
                                        <div>
                                            <h3 className="text-3xl font-serif text-midnight mb-1">Curation Studio</h3>
                                            <p className="text-sm text-warm-gray">Review and refine your manuscript before final publication.</p>
                                        </div>
                                        <div className="flex items-center gap-3">
                                            <button onClick={handleGenerateAllImages} disabled={generatingImages} className="btn-secondary">
                                                {generatingImages ? <Loader2 size={16} className="animate-spin" /> : <><ImagePlus size={16} /> Illustrate All Chapters</>}
                                            </button>
                                            <button onClick={handleGeneratePdf} disabled={generatingPdf} className="btn-primary btn-gold">
                                                {generatingPdf ? <Loader2 size={16} className="animate-spin" /> : <><Sparkles size={16} /> Final Publication</>}
                                            </button>
                                        </div>
                                    </div>
                                    <BookPreview
                                        projectId={projectId} chapters={project.chapters}
                                        coverTitle={project.cover_title} coverSubtitle={project.cover_subtitle}
                                        onUpdate={handleChaptersUpdate}
                                    />
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </main>
            </div>
        </div>
    );
}
