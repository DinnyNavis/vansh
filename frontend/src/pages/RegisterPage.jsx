import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { BookOpen, User, Mail, Lock, ArrowRight, Loader2, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';

export default function RegisterPage() {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const { register } = useAuth();
    const { addToast } = useToast();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            await register(name, email, password);
            addToast('Welcome to Vansh. Your legacy begins here.', 'success');
            navigate('/dashboard');
        } catch (err) {
            setError(err.response?.data?.message || 'Registration failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-ivory flex items-center justify-center px-6 py-20 relative overflow-hidden">
            {/* Background Decor */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full bg-gold/5 blur-[120px] pointer-events-none" />

            <motion.div
                className="w-full max-w-md"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
            >
                <div className="text-center mb-10">
                    <Link to="/" className="inline-flex items-center gap-2 no-underline mb-6">
                        <BookOpen size={32} className="text-gold" />
                        <span className="font-serif text-3xl font-bold text-midnight tracking-tight">VANSH</span>
                    </Link>
                    <h2 className="text-3xl font-serif text-midnight">Begin Your Legacy</h2>
                    <p className="text-sm text-warm-gray mt-2">Create an account to preserve your stories forever.</p>
                </div>

                <div className="glass-card p-8 md:p-10">
                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div>
                            <label className="block text-xs font-accent font-bold uppercase tracking-widest mb-2 text-charcoal">Full Name</label>
                            <div className="relative">
                                <User className="absolute left-3 top-1/2 -translate-y-1/2 text-gold opacity-50" size={18} />
                                <input
                                    type="text"
                                    required
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    className="w-full pl-10 pr-4 py-3 bg-white border border-black/5 rounded-xl outline-none focus:border-gold transition-colors text-sm"
                                    placeholder="John Doe"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-xs font-accent font-bold uppercase tracking-widest mb-2 text-charcoal">Email Address</label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gold opacity-50" size={18} />
                                <input
                                    type="email"
                                    required
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full pl-10 pr-4 py-3 bg-white border border-black/5 rounded-xl outline-none focus:border-gold transition-colors text-sm"
                                    placeholder="john@example.com"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-xs font-accent font-bold uppercase tracking-widest mb-2 text-charcoal">Password</label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gold opacity-50" size={18} />
                                <input
                                    type="password"
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full pl-10 pr-4 py-3 bg-white border border-black/5 rounded-xl outline-none focus:border-gold transition-colors text-sm"
                                    placeholder="Min. 8 characters"
                                />
                            </div>
                        </div>

                        <div className="flex items-start gap-3 p-3 bg-cream rounded-lg mb-6">
                            <ShieldCheck size={18} className="text-gold shrink-0 mt-0.5" />
                            <p className="text-[10px] text-warm-gray leading-relaxed">By creating an account, you agree to our <strong>Terms of Legacy Preservation</strong> and <strong>Privacy Shield</strong> standards.</p>
                        </div>

                        {error && (
                            <motion.div
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                                className="p-3 bg-error/10 border border-error/20 rounded-lg text-error text-xs text-center"
                            >
                                {error}
                            </motion.div>
                        )}

                        <button
                            onClick={handleSubmit}
                            disabled={loading}
                            className="btn-primary w-full justify-center group"
                            style={{ padding: '1rem' }}
                        >
                            {loading ? (
                                <Loader2 size={20} className="animate-spin" />
                            ) : (
                                <>Establish Your Archive <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" /></>
                            )}
                        </button>
                    </form>

                    <div className="mt-8 pt-8 border-t border-black/5 text-center">
                        <p className="text-sm text-warm-gray">
                            Already have an archive?{' '}
                            <Link to="/login" className="text-gold font-bold no-underline hover:underline">
                                Sign In
                            </Link>
                        </p>
                    </div>
                </div>
            </motion.div>
        </div>
    );
}
