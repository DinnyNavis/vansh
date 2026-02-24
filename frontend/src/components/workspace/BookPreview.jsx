import { useState, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Edit3, Lock, Unlock, Trash2, ImagePlus, RotateCcw,
    ChevronUp, ChevronDown, Save, X, Upload, Sparkles,
} from 'lucide-react';
import { useToast } from '../../context/ToastContext';
import api from '../../utils/api';

const resolveImageUrl = (url) => {
    if (!url) return '';
    if (url.includes('pollinations.ai')) return '';
    if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('blob:')) return url;
    if (url.startsWith('/api/')) {
        const base = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5007';
        return `${base}${url}`;
    }
    return url;
};

export default function BookPreview({
    projectId,
    chapters,
    coverTitle,
    coverSubtitle,
    onUpdate,
}) {
    const { addToast } = useToast();
    const [editingChapter, setEditingChapter] = useState(null);
    const [editTitle, setEditTitle] = useState('');
    const [editContent, setEditContent] = useState('');
    const imageInputRef = useRef(null);
    const [uploadingImageFor, setUploadingImageFor] = useState(null);
    const [generatingImageFor, setGeneratingImageFor] = useState(null);

    useEffect(() => {
        if (generatingImageFor) {
            const ch = chapters.find(c => c.id === generatingImageFor);
            if (ch?.image_url && !ch.image_url.includes('pollinations.ai')) {
                setGeneratingImageFor(null);
            }
        }
    }, [chapters, generatingImageFor]);

    const handleEditStart = (chapter) => {
        if (chapter.locked) return;
        setEditingChapter(chapter.id);
        setEditTitle(chapter.chapter_title);
        setEditContent(chapter.content);
    };

    const handleEditSave = useCallback(async () => {
        if (!editingChapter) return;
        const updatedChapters = chapters.map((ch) =>
            ch.id === editingChapter ? { ...ch, chapter_title: editTitle, content: editContent } : ch
        );
        try {
            await api.put(`/projects/${projectId}`, { chapters: updatedChapters });
            onUpdate?.(updatedChapters);
            addToast('Legacy updated successfully.', 'success');
        } catch (err) {
            console.error(err);
            addToast('Failed to save changes.', 'error');
        }
        setEditingChapter(null);
    }, [editingChapter, editTitle, editContent, chapters, projectId, onUpdate]);

    const handleToggleLock = useCallback(async (chapterId) => {
        const updatedChapters = chapters.map((ch) =>
            ch.id === chapterId ? { ...ch, locked: !ch.locked } : ch
        );
        try {
            await api.put(`/projects/${projectId}`, { chapters: updatedChapters });
            onUpdate?.(updatedChapters);
            const isNowLocked = updatedChapters.find(c => c.id === chapterId)?.locked;
            addToast(isNowLocked ? 'Chapter locked.' : 'Chapter unlocked.', 'success');
        } catch (err) {
            console.error(err);
            addToast('Connection error.', 'error');
        }
    }, [chapters, projectId, onUpdate]);

    const handleDeleteChapter = useCallback(async (chapterId) => {
        if (!window.confirm('Exclue this chapter from your legacy?')) return;
        const updatedChapters = chapters.filter((ch) => ch.id !== chapterId);
        try {
            await api.put(`/projects/${projectId}`, { chapters: updatedChapters });
            onUpdate?.(updatedChapters);
            addToast('Chapter removed from legacy.', 'success');
        } catch (err) {
            console.error(err);
            addToast('Failed to delete chapter.', 'error');
        }
    }, [chapters, projectId, onUpdate]);

    const handleMoveChapter = useCallback(async (index, direction) => {
        const newIdx = index + direction;
        if (newIdx < 0 || newIdx >= chapters.length) return;

        const updated = [...chapters];
        [updated[index], updated[newIdx]] = [updated[newIdx], updated[index]];

        // Optimistic update
        onUpdate?.(updated);

        try {
            await api.put(`/projects/${projectId}`, { chapters: updated });
            addToast('Chapter order preserved.', 'success');
        } catch (err) {
            console.error(err);
            onUpdate?.(chapters); // Rollback
            addToast('Failed to save new order.', 'error');
        }
    }, [chapters, projectId, onUpdate, addToast]);

    const handleGenerateImage = useCallback(async (chapter) => {
        setGeneratingImageFor(chapter.id);
        try {
            await api.post('/unguided/generate-image', {
                project_id: projectId,
                chapter_id: chapter.id,
                chapter_summary: chapter.chapter_summary || chapter.chapter_title,
            });
        } catch (err) { setGeneratingImageFor(null); }
    }, [projectId]);

    const handleUploadImage = useCallback(async (chapterId, file) => {
        const formData = new FormData();
        formData.append('image', file);
        formData.append('project_id', projectId);
        formData.append('chapter_id', chapterId);
        setUploadingImageFor(chapterId);
        try {
            const res = await api.post('/unguided/upload-image', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
            onUpdate?.(chapters.map((ch) => ch.id === chapterId ? { ...ch, image_url: res.data.image_url, image_type: 'manual' } : ch));
        } finally { setUploadingImageFor(null); }
    }, [projectId, chapters, onUpdate]);

    const handleDeleteImage = useCallback(async (chapterId) => {
        const updatedChapters = chapters.map((ch) => ch.id === chapterId ? { ...ch, image_url: null, image_type: null } : ch);
        try {
            await api.put(`/projects/${projectId}`, { chapters: updatedChapters });
            onUpdate?.(updatedChapters);
            addToast('Image removed.', 'success');
        } catch (err) {
            console.error(err);
            addToast('Failed to remove image.', 'error');
        }
    }, [chapters, projectId, onUpdate]);

    if (!chapters || chapters.length === 0) return null;

    return (
        <div className="space-y-16 max-w-5xl mx-auto pb-20">
            {/* Cover Page */}
            <motion.div
                className="book-page book-cover shadow-2xl paper-texture"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <div className="absolute inset-10 border border-gold/30 pointer-events-none" />

                <div className="relative z-10 text-center">
                    <div className="mb-12">
                        <div className="w-16 h-[1px] bg-gold mx-auto mb-6 opacity-60" />
                        <p className="text-[10px] uppercase tracking-[0.5em] text-gold-light font-accent font-bold mb-4">A VANSH LEGACY COLLECTION</p>
                    </div>

                    <h1 className="text-6xl md:text-8xl font-serif leading-tight mb-10 px-4">
                        {coverTitle}
                    </h1>

                    {coverSubtitle && (
                        <div className="relative py-8">
                            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-12 h-[1px] bg-gold/30" />
                            <p className="text-2xl font-serif italic text-ivory/80 max-w-lg mx-auto leading-relaxed px-6">
                                {coverSubtitle}
                            </p>
                            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-12 h-[1px] bg-gold/30" />
                        </div>
                    )}

                    <div className="mt-24">
                        <div className="flex items-center justify-center gap-4 mb-4 opacity-40">
                            <div className="h-[1px] w-8 bg-gold" />
                            <Sparkles size={20} className="text-gold" />
                            <div className="h-[1px] w-8 bg-gold" />
                        </div>
                        <p className="text-[10px] font-accent uppercase tracking-[0.3em] text-gold-light/60">ESTABLISHED MCMLXX / MMXXIV</p>
                    </div>
                </div>
            </motion.div>

            {/* Content Pages */}
            {chapters.map((chapter, idx) => (
                <div key={chapter.id} className="book-spread group">
                    <motion.div
                        className="book-page paper-texture relative overflow-hidden"
                        initial={{ opacity: 0, x: 20 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true, margin: "-100px" }}
                    >
                        {/* Gutter (Spine) Shadow */}
                        <div className="book-gutter" />

                        {/* Page Actions */}
                        <div className="absolute top-8 right-8 flex gap-2 opacity-0 group-hover:opacity-100 transition-all z-20">
                            <button onClick={() => handleToggleLock(chapter.id)} className="p-2 bg-white/90 backdrop-blur rounded-lg shadow-sm border border-black/5 cursor-pointer hover:bg-white transition-colors">
                                {chapter.locked ? <Lock size={14} className="text-gold" /> : <Unlock size={14} className="text-warm-gray" />}
                            </button>
                            {!chapter.locked && (
                                <>
                                    <button onClick={() => handleEditStart(chapter)} className="p-2 bg-white/90 backdrop-blur rounded-lg shadow-sm border border-black/5 cursor-pointer hover:bg-white transition-colors" title="Edit Content"><Edit3 size={14} /></button>
                                    <button onClick={() => handleMoveChapter(idx, -1)} className="p-2 bg-white/90 backdrop-blur rounded-lg shadow-sm border border-black/5 cursor-pointer hover:bg-white transition-colors" title="Move Up"><ChevronUp size={14} /></button>
                                    <button onClick={() => handleMoveChapter(idx, 1)} className="p-2 bg-white/90 backdrop-blur rounded-lg shadow-sm border border-black/5 cursor-pointer hover:bg-white transition-colors" title="Move Down"><ChevronDown size={14} /></button>
                                    <button onClick={() => handleDeleteChapter(chapter.id)} className="p-2 bg-white/90 backdrop-blur rounded-lg shadow-sm border border-black/5 hover:text-error cursor-pointer hover:bg-white transition-colors" title="Delete Chapter"><Trash2 size={14} /></button>
                                </>
                            )}
                        </div>

                        <div className="relative z-10 pl-6">
                            <div className="flex items-center gap-4 mb-8">
                                <span className="text-[10px] font-accent font-bold text-gold uppercase tracking-[0.4em]">CHAPTER {idx + 1}</span>
                                <div className="h-[1px] flex-1 bg-gold/10" />
                            </div>

                            {editingChapter === chapter.id ? (
                                <div className="space-y-8 mt-10">
                                    <input
                                        value={editTitle}
                                        onChange={e => setEditTitle(e.target.value)}
                                        className="w-full text-4xl font-serif text-midnight border-b-2 border-gold/20 py-4 outline-none bg-transparent"
                                        placeholder="Chapter Title"
                                    />
                                    <textarea
                                        value={editContent}
                                        onChange={e => setEditContent(e.target.value)}
                                        className="w-full font-body text-xl leading-[1.8] min-h-[500px] border-none outline-none resize-none bg-transparent p-4 rounded-xl border border-gold/5 focus:border-gold/20 transition-all"
                                        placeholder="Type the story here..."
                                    />
                                    <div className="flex gap-4 pt-4">
                                        <button onClick={handleEditSave} className="btn-primary btn-gold"><Save size={16} /> Save Legacy</button>
                                        <button onClick={() => setEditingChapter(null)} className="btn-secondary">Discard Changes</button>
                                    </div>
                                </div>
                            ) : (
                                <>
                                    <h2 className="text-5xl font-serif text-midnight mb-12 leading-tight tracking-tight">{chapter.chapter_title}</h2>

                                    {/* Image Layout */}
                                    {(chapter.image_url || generatingImageFor === chapter.id) && (
                                        <div className="my-12 rounded-lg overflow-hidden shadow-2xl border-4 border-white ring-1 ring-black/5 group/img relative">
                                            {generatingImageFor === chapter.id ? (
                                                <div className="h-[450px] bg-cream/30 flex flex-col items-center justify-center animate-pulse">
                                                    <Sparkles size={40} className="text-gold/40 mb-4 animate-spin-slow" />
                                                    <p className="text-xs font-accent font-bold uppercase tracking-widest text-gold/60">Painting Memory...</p>
                                                </div>
                                            ) : (
                                                <>
                                                    <div className="book-image-container">
                                                        <img
                                                            src={resolveImageUrl(chapter.image_url)}
                                                            alt=""
                                                            loading="lazy"
                                                            onLoad={(e) => e.target.classList.add('loaded')}
                                                            className="w-full object-cover max-h-[700px] hover:scale-105 transition-transform duration-700"
                                                        />
                                                    </div>
                                                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover/img:opacity-100 transition-all flex items-end justify-center p-8">
                                                        <button
                                                            onClick={() => handleDeleteImage(chapter.id)}
                                                            className="p-4 bg-error/90 backdrop-blur-md rounded-full text-white cursor-pointer hover:bg-error transition-colors shadow-lg"
                                                            title="Remove Image"
                                                        >
                                                            <Trash2 size={24} />
                                                        </button>
                                                    </div>
                                                </>
                                            )}
                                        </div>
                                    )}

                                    {!chapter.image_url && !generatingImageFor && !chapter.locked && (
                                        <div className="flex gap-4 my-12 decorative-actions">
                                            <button
                                                onClick={() => handleGenerateImage(chapter)}
                                                className="btn-secondary border-gold/30 text-gold hover:bg-gold/5 px-6 py-3 rounded-xl transition-all hover:scale-[1.02]"
                                            >
                                                <Sparkles size={16} /> Illustrate Memory
                                            </button>
                                            <button
                                                onClick={() => { setUploadingImageFor(chapter.id); imageInputRef.current?.click(); }}
                                                className="btn-secondary border-black/10 px-6 py-3 rounded-xl transition-all hover:scale-[1.02]"
                                            >
                                                <Upload size={16} /> Upload Heirloom Photo
                                            </button>
                                        </div>
                                    )}

                                    <div className="font-body text-2xl leading-[2] text-charcoal/90 space-y-10 mt-12 pb-12">
                                        {chapter.content.split('\n').map((p, pIdx) => {
                                            const content = p.trim();
                                            if (!content) return null;
                                            return (
                                                <p key={pIdx} className={pIdx === 0 ? "drop-cap" : ""}>
                                                    {content}
                                                </p>
                                            );
                                        })}
                                    </div>

                                    <div className="ornamental-hr">
                                        <span className="flourish">❧</span>
                                    </div>
                                </>
                            )}
                        </div>

                        {/* Page Footer */}
                        <div className="mt-12 pt-10 border-t border-black/5 text-center flex items-center justify-between opacity-30 select-none">
                            <span className="text-[9px] font-accent font-bold tracking-[0.3em] uppercase">{coverTitle}</span>
                            <div className="flex items-center gap-3">
                                <div className="h-[1px] w-4 bg-charcoal" />
                                <span className="text-sm font-serif">{idx + 2}</span>
                                <div className="h-[1px] w-4 bg-charcoal" />
                            </div>
                            <span className="text-[9px] font-accent font-bold tracking-[0.3em] uppercase">VANSH HERITAGE STUDIO</span>
                        </div>
                    </motion.div>
                </div>
            ))}

            <input ref={imageInputRef} type="file" accept="image/*" className="hidden"
                onChange={e => e.target.files[0] && handleUploadImage(uploadingImageFor, e.target.files[0])} />
        </div>
    );
}
