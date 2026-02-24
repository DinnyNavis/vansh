import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { BookOpen } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function Navbar() {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    return (
        <nav className="fixed top-0 left-0 right-0 z-50 transition-all">
            <div className="glass-card mx-6 my-4 px-6 py-3 flex items-center justify-between rounded-xl">
                <Link to="/" className="flex items-center gap-2 no-underline group">
                    <motion.div
                        whileHover={{ rotate: 15 }}
                        transition={{ type: 'spring', stiffness: 300 }}
                    >
                        <BookOpen size={28} className="text-gold" />
                    </motion.div>
                    <span className="font-serif text-2xl font-bold text-midnight tracking-tight">VANSH</span>
                </Link>

                <div className="hidden md:flex items-center gap-8">
                    <a href="/#how-it-works" className="text-sm font-accent font-medium text-charcoal hover:text-gold transition-colors">How it Works</a>
                    <a href="/#pricing" className="text-sm font-accent font-medium text-charcoal hover:text-gold transition-colors">Pricing</a>
                    <a href="/#contact" className="text-sm font-accent font-medium text-charcoal hover:text-gold transition-colors">Contact</a>
                </div>

                <div className="flex items-center gap-4">
                    {user ? (
                        <>
                            <Link to="/dashboard" className="text-sm font-accent font-semibold text-midnight no-underline">Dashboard</Link>
                            <button
                                onClick={() => { logout(); navigate('/'); }}
                                className="btn-secondary"
                                style={{ padding: '0.5rem 1.2rem', fontSize: '0.8rem' }}
                            >
                                Sign Out
                            </button>
                        </>
                    ) : (
                        <>
                            <Link to="/login" className="text-sm font-accent font-semibold text-midnight no-underline hover:text-gold transition-colors">Sign In</Link>
                            <Link to="/register" className="btn-primary no-underline" style={{ padding: '0.6rem 1.5rem', fontSize: '0.85rem' }}>
                                Start Your Legacy
                            </Link>
                        </>
                    )}
                </div>
            </div>
        </nav>
    );
}
