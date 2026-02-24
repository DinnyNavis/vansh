import { Link } from 'react-router-dom';
import { BookOpen, Instagram, Twitter, Mail } from 'lucide-react';

export default function Footer() {
    return (
        <footer className="py-20 mt-20" style={{ background: 'var(--color-midnight)', color: 'var(--color-ivory)' }}>
            <div className="container">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-16">
                    <div className="col-span-1 md:col-span-1">
                        <Link to="/" className="flex items-center gap-2 no-underline text-ivory mb-6">
                            <BookOpen size={28} className="text-gold" />
                            <span className="font-serif text-2xl font-bold tracking-tight">VANSH</span>
                        </Link>
                        <p className="text-sm opacity-60 leading-relaxed font-body">
                            Preserving human stories through the marriage of ancient heritage and modern intelligence.
                        </p>
                    </div>

                    <div>
                        <h4 className="font-serif text-lg mb-6">Studio</h4>
                        <ul className="list-none space-y-3 p-0">
                            <li><Link to="/" className="text-sm no-underline text-ivory opacity-60 hover:opacity-100 transition-opacity">Our Heritage</Link></li>
                            <li><Link to="/" className="text-sm no-underline text-ivory opacity-60 hover:opacity-100 transition-opacity">Expert Writing</Link></li>
                            <li><Link to="/" className="text-sm no-underline text-ivory opacity-60 hover:opacity-100 transition-opacity">AI Technology</Link></li>
                        </ul>
                    </div>

                    <div>
                        <h4 className="font-serif text-lg mb-6">Support</h4>
                        <ul className="list-none space-y-3 p-0">
                            <li><Link to="/" className="text-sm no-underline text-ivory opacity-60 hover:opacity-100 transition-opacity">Help Center</Link></li>
                            <li><Link to="/" className="text-sm no-underline text-ivory opacity-60 hover:opacity-100 transition-opacity">Privacy Policy</Link></li>
                            <li><Link to="/" className="text-sm no-underline text-ivory opacity-60 hover:opacity-100 transition-opacity">Contact Us</Link></li>
                        </ul>
                    </div>

                    <div>
                        <h4 className="font-serif text-lg mb-6">Stay Connected</h4>
                        <div className="flex gap-4">
                            <a href="#" className="p-2 rounded-full border border-white/10 hover:border-gold/50 transition-colors text-ivory">
                                <Instagram size={18} />
                            </a>
                            <a href="#" className="p-2 rounded-full border border-white/10 hover:border-gold/50 transition-colors text-ivory">
                                <Twitter size={18} />
                            </a>
                            <a href="#" className="p-2 rounded-full border border-white/10 hover:border-gold/50 transition-colors text-ivory">
                                <Mail size={18} />
                            </a>
                        </div>
                    </div>
                </div>

                <div className="pt-8 border-t border-white/5 text-center">
                    <p className="text-xs opacity-40 font-accent uppercase tracking-widest">
                        © {new Date().getFullYear()} VANSH STORY STUDIO. ALL RIGHTS RESERVED.
                    </p>
                </div>
            </div>
        </footer>
    );
}
