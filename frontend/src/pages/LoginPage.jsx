import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { BookOpen, Mail, Lock, ArrowRight, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const { login } = useAuth();
    const { addToast } = useToast();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            await login(email, password);
            addToast('Welcome back to the archives.', 'success');
            navigate('/dashboard');
        } catch (err) {
            setError('Invalid email or password. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-ivory flex items-center justify-center px-6 py-20 relative overflow-hidden">
            {/* Background Decor */}
            <div className="absolute -top-24 -left-24 w-96 h-96 bg-gold/5 rounded-full blur-3xl" />
            <div className="absolute -bottom-24 -right-24 w-96 h-96 bg-midnight/5 rounded-full blur-3xl" />

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
                    <h2 className="text-3xl font-serif text-midnight">Welcome Back</h2>
                    <p className="text-sm text-warm-gray mt-2">Enter your credentials to access your archive.</p>
                </div>

                <div className="glass-card p-8 md:p-10">
                    <form onSubmit={handleSubmit} className="space-y-6">
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
                                    placeholder="name@example.com"
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
                                    placeholder="••••••••"
                                />
                            </div>
                        </div>

                        {error && (
                            <motion.div
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
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
                                <>Sign In to Studio <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" /></>
                            )}
                        </button>
                    </form>

                    <div className="mt-8 pt-8 border-t border-black/5 text-center">
                        <p className="text-sm text-warm-gray">
                            Don't have an archive?{' '}
                            <Link to="/register" className="text-gold font-bold no-underline hover:underline">
                                Start Your Legacy
                            </Link>
                        </p>
                    </div>
                </div>
            </motion.div>
        </div>
    );
}
