import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Plus, BookOpen, Mic, FileText, Video, Clock, ChevronRight, LogOut, Trash2,
    Search, Sparkles, Filter, Music, Loader2
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import api from '../utils/api';

const inputTypes = [
    { value: 'audio', label: 'Record Audio', icon: Mic, desc: 'Narrate your story', emoji: '🎤' },
    { value: 'text', label: 'Write Text', icon: FileText, desc: 'Type or paste content', emoji: '⌨️' },
    { value: 'upload-audio', label: 'Upload Audio', icon: Music, desc: 'From voice memos', emoji: '🎵' },
    { value: 'video', label: 'Upload Video', icon: Video, desc: 'From a recording', emoji: '🎥' },
];

const statusStyles = {
    created: { bg: 'rgba(211, 211, 211, 0.1)', color: '#A0A0A0', label: 'Draft' },
    transcribing: { bg: 'rgba(201, 168, 76, 0.1)', color: 'var(--color-gold)', label: 'Transcribing' },
    transcribed: { bg: 'rgba(74, 222, 128, 0.1)', color: '#27AE60', label: 'Ready for Review' },
    writing: { bg: 'rgba(201, 168, 76, 0.1)', color: 'var(--color-gold)', label: 'Drafting Book' },
    chapters_ready: { bg: 'rgba(201, 168, 76, 0.15)', color: 'var(--color-gold-dark)', label: 'Manuscript Ready' },
    complete: { bg: 'rgba(26, 31, 44, 0.1)', color: 'var(--color-midnight)', label: 'Published' },
};

const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
};

export default function Dashboard() {
    const { user, logout } = useAuth();
    const { addToast } = useToast();
    const navigate = useNavigate();
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showCreate, setShowCreate] = useState(false);
    const [newTitle, setNewTitle] = useState('');
    const [newType, setNewType] = useState('audio');
    const [creating, setCreating] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        fetchProjects();
    }, []);

    const fetchProjects = async () => {
        try {
            const res = await api.get('/projects');
            setProjects(res.data.projects);
        } catch (err) {
            console.error('Failed to fetch projects:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async () => {
        if (!newTitle.trim()) return;
        setCreating(true);
        try {
            const res = await api.post('/projects', { title: newTitle, input_type: newType });
            addToast('Legacy established successfully.', 'success');
            navigate(`/workspace/${res.data.project._id}`);
        } catch (err) {
            console.error('Failed to create project:', err);
            addToast('Architectural error: Could not create legacy.', 'error');
        } finally {
            setCreating(false);
        }
    };

    const handleDelete = async (e, projectId) => {
        e.stopPropagation();
        if (!window.confirm('Are you sure you want to delete this legacy? This action is irreversible.')) return;
        try {
            await api.delete(`/projects/${projectId}`);
            setProjects((prev) => prev.filter((p) => p._id !== projectId));
            addToast('Legacy removed from archives.', 'success');
        } catch (err) {
            console.error('Failed to delete project:', err);
            addToast('Failed to archive legacy.', 'error');
        }
    };

    const filteredProjects = projects.filter(p =>
        p.title.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="min-h-screen bg-ivory pb-20">
            {/* Top Bar */}
            <nav className="sticky top-0 z-40 glass-card" style={{ borderBottom: '1px solid rgba(0,0,0,0.06)', borderRadius: 0 }}>
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <Link to="/" className="flex items-center gap-3 no-underline">
                        <BookOpen size={24} className="text-gold" />
                        <span className="font-serif text-xl font-bold text-midnight tracking-tight">VANSH</span>
                    </Link>

                    <div className="flex items-center gap-6">
                        <span className="hidden sm:inline text-xs font-accent font-bold uppercase tracking-widest text-warm-gray">
                            Archivist: <span className="text-midnight">{user?.name}</span>
                        </span>
                        <button
                            onClick={logout}
                            className="p-2 rounded-full hover:bg-black/5 transition-colors border-none bg-transparent cursor-pointer group"
                            title="Sign Out"
                        >
                            <LogOut size={20} className="text-warm-gray group-hover:text-midnight transition-colors" />
                        </button>
                    </div>
                </div>
            </nav>

            <div className="max-w-7xl mx-auto px-6 pt-12">
                {/* Welcome Section */}
                <header className="mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6">
                    <div>
                        <h1 className="text-4xl md:text-5xl text-midnight mb-2">My Legacies</h1>
                        <p className="text-warm-gray font-body font-medium italic">Preserving {projects.length} family stories for history.</p>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gold opacity-100" size={16} />
                            <input
                                type="text"
                                placeholder="Find a story..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="pl-10 pr-4 py-2 bg-white border border-black/5 rounded-xl outline-none focus:border-gold transition-colors text-sm w-48 md:w-64"
                            />
                        </div>
                        <button onClick={() => setShowCreate(!showCreate)} className="btn-primary btn-gold">
                            {showCreate ? 'Close Studio' : <><Plus size={18} /> New Legacy</>}
                        </button>
                    </div>
                </header>

                {/* Create Legacy Panel */}
                <AnimatePresence>
                    {showCreate && (
                        <motion.div
                            className="glass-card mb-12 p-10 overflow-hidden"
                            initial={{ height: 0, opacity: 0, marginBottom: 0 }}
                            animate={{ height: 'auto', opacity: 1, marginBottom: 48 }}
                            exit={{ height: 0, opacity: 0, marginBottom: 0 }}
                            transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
                        >
                            <div className="max-w-3xl">
                                <div className="flex items-center gap-3 mb-8">
                                    <Sparkles size={24} className="text-gold" />
                                    <h2 className="text-2xl text-midnight">Start a New Chapter</h2>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                                    <div className="space-y-6">
                                        <div>
                                            <label className="block text-xs font-accent font-bold uppercase tracking-widest mb-3 text-charcoal">Story Title</label>
                                            <input
                                                type="text"
                                                value={newTitle}
                                                onChange={(e) => setNewTitle(e.target.value)}
                                                placeholder="e.g., The Silk Road Journey"
                                                className="w-full px-4 py-3 bg-white border border-black/10 rounded-xl outline-none focus:border-gold transition-colors text-sm font-serif italic text-lg shadow-inner"
                                            />
                                        </div>

                                        <div className="flex gap-3 pt-4">
                                            <button onClick={handleCreate} disabled={creating || !newTitle.trim()} className="btn-primary flex-1 justify-center">
                                                {creating ? <Loader2 className="animate-spin" /> : 'Establish Legacy'}
                                            </button>
                                            <button onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
                                        </div>
                                    </div>

                                    <div>
                                        <label className="block text-xs font-accent font-bold uppercase tracking-widest mb-4 text-charcoal">Primary Input Method</label>
                                        <div className="grid grid-cols-2 gap-3">
                                            {inputTypes.map((type) => (
                                                <button
                                                    key={type.value}
                                                    onClick={() => setNewType(type.value)}
                                                    className={`flex flex-col items-center gap-2 p-4 rounded-xl transition-all border-2 text-center ${newType === type.value
                                                        ? 'bg-gold/10 border-gold shadow-gold-sm'
                                                        : 'bg-white border-black/5 hover:border-black/10'
                                                        }`}
                                                >
                                                    <span className="text-xl mb-1">{type.emoji}</span>
                                                    <span className={`text-xs font-bold uppercase tracking-tight ${newType === type.value ? 'text-gold' : 'text-warm-gray'}`}>
                                                        {type.label}
                                                    </span>
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Projects Grid */}
                {loading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="glass-card h-64 animate-pulse opacity-50" />
                        ))}
                    </div>
                ) : filteredProjects.length === 0 ? (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="text-center py-32 glass-card bg-cream/50"
                    >
                        <BookOpen size={64} className="text-gold mx-auto mb-6 opacity-30" />
                        <h3 className="text-2xl text-midnight font-serif mb-3">The archives are waiting.</h3>
                        <p className="text-warm-gray mb-8 max-w-sm mx-auto">You haven't established any legacies yet. Start preserving your history today.</p>
                        <button onClick={() => setShowCreate(true)} className="btn-primary">
                            <Plus size={18} /> Establish Your First Legacy
                        </button>
                    </motion.div>
                ) : (
                    <motion.div
                        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
                        initial="hidden"
                        animate="visible"
                        variants={{ visible: { transition: { staggerChildren: 0.1 } } }}
                    >
                        {filteredProjects.map((project) => {
                            const style = statusStyles[project.status] || statusStyles.created;
                            return (
                                <motion.div
                                    key={project._id}
                                    variants={cardVariants}
                                    whileHover={{ y: -8, transition: { duration: 0.3 } }}
                                    className="glass-card group cursor-pointer border border-black/5 hover:border-gold/30 hover:shadow-gold transition-all relative overflow-hidden"
                                    onClick={() => navigate(`/workspace/${project._id}`)}
                                >
                                    <div className="p-8 h-full flex flex-col">
                                        <div className="flex justify-between items-start mb-6">
                                            <span
                                                className="px-3 py-1 rounded-full text-[10px] font-accent font-bold uppercase tracking-widest"
                                                style={{ background: style.bg, color: style.color }}
                                            >
                                                {style.label}
                                            </span>
                                            <button
                                                onClick={(e) => handleDelete(e, project._id)}
                                                className="opacity-0 group-hover:opacity-100 p-2 rounded-lg bg-error/10 text-error hover:bg-error transition-all border-none bg-transparent cursor-pointer hover:text-white"
                                                title="Archive Legacy (Delete)"
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </div>

                                        <h3 className="text-2xl md:text-3xl text-midnight font-serif leading-tight mb-4 group-hover:text-gold transition-colors">
                                            {project.title}
                                        </h3>

                                        <div className="mt-auto pt-8 border-t border-black/5 flex items-center justify-between">
                                            <div className="flex items-center gap-4 text-[10px] font-accent font-bold uppercase tracking-widest text-warm-gray">
                                                <span className="flex items-center gap-1.5"><Clock size={14} className="text-gold/50" /> {new Date(project.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}</span>
                                                <span className="flex items-center gap-1.5 uppercase tracking-tighter">
                                                    {project.input_type === 'audio' ? <Mic size={14} className="text-gold/50" /> : project.input_type === 'text' ? <FileText size={14} className="text-gold/50" /> : <Video size={14} className="text-gold/50" />}
                                                    {project.input_type}
                                                </span>
                                            </div>
                                            <ChevronRight className="text-gold opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
                                        </div>
                                    </div>
                                </motion.div>
                            );
                        })}
                    </motion.div>
                )}
            </div>
        </div>
    );
}
