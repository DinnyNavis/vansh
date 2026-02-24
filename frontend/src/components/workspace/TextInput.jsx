import { useState, useCallback } from 'react';
import { useToast } from '../../context/ToastContext';
import { motion } from 'framer-motion';
import { Send, FileText, Loader2, CheckCircle2 } from 'lucide-react';
import api from '../../utils/api';

export default function TextInput({ projectId, autoGenerate = false, onTranscriptReady }) {
    const { addToast } = useToast();
    const [text, setText] = useState('');
    const [status, setStatus] = useState('idle'); // idle, submitting, done

    const handleSubmit = useCallback(async () => {
        if (!text.trim() || text.trim().length < 50) {
            addToast('Please enter at least 50 characters for your story.', 'error');
            return;
        }

        setStatus('submitting');
        try {
            await api.post('/unguided/process-text', {
                text: text.trim(),
                project_id: projectId,
                auto_generate: autoGenerate,
            });
            setStatus('done');
            addToast('Story processed successfully!', 'success');
            onTranscriptReady?.();
        } catch (err) {
            console.error('Text submit error:', err);
            setStatus('idle');
            addToast('Failed to process text. Please try again.', 'error');
        }
    }, [text, projectId, autoGenerate, onTranscriptReady]);

    const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;

    return (
        <div className="py-6 px-2">
            <div className="max-w-2xl mx-auto">
                {/* Header */}
                <div className="flex items-center gap-3 mb-4">
                    <FileText size={20} style={{ color: 'var(--color-gold)' }} />
                    <h3 className="font-serif text-lg" style={{ color: 'var(--color-midnight)' }}>
                        Write Your Story
                    </h3>
                </div>

                <p className="text-sm mb-5" style={{ color: 'var(--color-warm-gray)' }}>
                    Type or paste your story below. Don't worry about perfect grammar —
                    our AI will refine and polish it into elegant book prose.
                </p>

                {/* Textarea */}
                <div className="relative">
                    <textarea
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        placeholder="Start telling your story here... &#10;&#10;For example: 'My grandfather was born in a small village in 1945. He grew up during a time of great change...'"
                        disabled={status !== 'idle'}
                        className="w-full rounded-xl p-5 text-base outline-none resize-none font-body"
                        style={{
                            minHeight: 280,
                            background: '#fff',
                            border: '1px solid rgba(0,0,0,0.08)',
                            color: 'var(--color-charcoal)',
                            lineHeight: 1.8,
                            transition: 'border-color 0.3s',
                        }}
                        onFocus={(e) => (e.target.style.borderColor = 'var(--color-gold)')}
                        onBlur={(e) => (e.target.style.borderColor = 'rgba(0,0,0,0.08)')}
                    />

                    {/* Word count */}
                    <div className="absolute bottom-3 right-4 text-xs" style={{ color: 'var(--color-warm-gray)' }}>
                        {wordCount} words
                    </div>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-between mt-5">
                    <span className="text-xs" style={{ color: 'var(--color-warm-gray)' }}>
                        Minimum 50 characters recommended
                    </span>

                    {status === 'idle' && (
                        <motion.button
                            onClick={handleSubmit}
                            disabled={text.trim().length < 50}
                            className="btn-primary"
                            style={{ opacity: text.trim().length < 50 ? 0.5 : 1 }}
                            whileHover={{ scale: 1.03 }}
                        >
                            <Send size={16} /> Process Story
                        </motion.button>
                    )}

                    {status === 'submitting' && (
                        <div className="flex items-center gap-2">
                            <Loader2 size={18} className="animate-spin" style={{ color: 'var(--color-gold)' }} />
                            <span className="text-sm" style={{ color: 'var(--color-warm-gray)' }}>Processing...</span>
                        </div>
                    )}

                    {status === 'done' && (
                        <div className="flex items-center gap-2">
                            <CheckCircle2 size={18} style={{ color: 'var(--color-success)' }} />
                            <span className="text-sm" style={{ color: 'var(--color-success)' }}>Text sent! Check progress below.</span>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
