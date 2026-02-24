import { motion } from 'framer-motion';
import { CheckCircle2, Loader2, AlertCircle } from 'lucide-react';

const stages = [
    { key: 'transcribing', label: 'Transcribing' },
    { key: 'refining', label: 'Refining Text' },
    { key: 'writing', label: 'Writing Book' },
    { key: 'generating_images', label: 'Generating Images' },
    { key: 'generating_pdf', label: 'Creating PDF' },
];

const stageIndex = (stage) => {
    // Map various stage keys to a phase
    if (['uploading', 'extracting', 'transcribing', 'transcribed'].includes(stage)) return 0;
    if (['refining'].includes(stage)) return 1;
    if (['writing', 'chapter_ready', 'chapters_complete'].includes(stage)) return 2;
    if (['generating_image', 'generating_images', 'image_ready', 'all_images_complete'].includes(stage)) return 3;
    if (['generating_pdf', 'pdf_ready'].includes(stage)) return 4;
    return -1;
};

export default function ProgressTracker({ currentStage, progress, message }) {
    const activeIdx = stageIndex(currentStage);
    const isError = currentStage === 'error';

    if (!currentStage) return null;

    return (
        <div className="py-6 px-4">
            <div className="max-w-2xl mx-auto">
                {/* Stage Steps */}
                <div className="flex items-center justify-between mb-8">
                    {stages.map((stage, idx) => {
                        const isDone = idx < activeIdx || currentStage === 'pdf_ready';
                        const isActive = idx === activeIdx && !isError;
                        const isPending = idx > activeIdx;

                        return (
                            <div key={stage.key} className="flex items-center flex-1">
                                <div className="flex flex-col items-center">
                                    <motion.div
                                        className="w-10 h-10 rounded-full flex items-center justify-center mb-2"
                                        style={{
                                            background: isDone
                                                ? 'var(--color-gold)'
                                                : isActive
                                                    ? 'rgba(201, 168, 76, 0.15)'
                                                    : 'rgba(0,0,0,0.04)',
                                            border: isActive ? '2px solid var(--color-gold)' : 'none',
                                        }}
                                        animate={isActive ? { scale: [1, 1.1, 1] } : {}}
                                        transition={{ duration: 1.5, repeat: Infinity }}
                                    >
                                        {isDone ? (
                                            <CheckCircle2 size={20} style={{ color: '#fff' }} />
                                        ) : isActive ? (
                                            <Loader2 size={18} className="animate-spin" style={{ color: 'var(--color-gold)' }} />
                                        ) : (
                                            <span className="text-xs font-bold" style={{ color: 'var(--color-warm-gray)' }}>
                                                {idx + 1}
                                            </span>
                                        )}
                                    </motion.div>
                                    <span
                                        className="text-xs font-medium text-center"
                                        style={{
                                            color: isDone
                                                ? 'var(--color-gold)'
                                                : isActive
                                                    ? 'var(--color-charcoal)'
                                                    : 'var(--color-warm-gray)',
                                            maxWidth: 80,
                                        }}
                                    >
                                        {stage.label}
                                    </span>
                                </div>
                                {idx < stages.length - 1 && (
                                    <div
                                        className="flex-1 h-0.5 mx-2 mt-[-1.5rem]"
                                        style={{
                                            background: idx < activeIdx ? 'var(--color-gold)' : 'rgba(0,0,0,0.08)',
                                        }}
                                    />
                                )}
                            </div>
                        );
                    })}
                </div>

                {/* Progress Bar */}
                {progress > 0 && !isError && (
                    <div className="mb-4">
                        <div className="w-full h-2 rounded-full" style={{ background: 'rgba(0,0,0,0.05)' }}>
                            <motion.div
                                className="h-full rounded-full"
                                style={{ background: 'linear-gradient(90deg, var(--color-gold), var(--color-gold-light))' }}
                                initial={{ width: 0 }}
                                animate={{ width: `${progress}%` }}
                                transition={{ duration: 0.3 }}
                            />
                        </div>
                    </div>
                )}

                {/* Message */}
                {message && (
                    <motion.div
                        key={message}
                        className="flex items-center gap-2 justify-center py-3 px-4 rounded-lg"
                        style={{
                            background: isError ? 'rgba(248, 113, 113, 0.08)' : 'rgba(201, 168, 76, 0.05)',
                            border: `1px solid ${isError ? 'rgba(248, 113, 113, 0.2)' : 'rgba(201, 168, 76, 0.15)'}`,
                        }}
                        initial={{ opacity: 0.8, scale: 0.98 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ type: "spring", stiffness: 300, damping: 20 }}
                    >
                        {isError ? (
                            <AlertCircle size={16} style={{ color: 'var(--color-error)' }} />
                        ) : (
                            <Loader2 size={14} className="animate-spin" style={{ color: 'var(--color-gold)' }} />
                        )}
                        <span className="text-sm" style={{ color: isError ? 'var(--color-error)' : 'var(--color-charcoal)' }}>
                            {message}
                        </span>
                    </motion.div>
                )}
            </div>
        </div>
    );
}
