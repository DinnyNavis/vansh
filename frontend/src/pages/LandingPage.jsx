import { motion } from 'framer-motion';
import { Sparkles, Mic, BookOpen, Quote, Shield, Zap, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import Navbar from '../components/landing/Navbar';
import Footer from '../components/landing/Footer';

const fadeIn = {
    hidden: { opacity: 0, y: 30 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.8, ease: [0.4, 0, 0.2, 1] } }
};

const stagger = {
    visible: { transition: { staggerChildren: 0.15 } }
};

export default function LandingPage() {
    return (
        <div className="min-h-screen bg-ivory text-charcoal overflow-hidden">
            <Navbar />

            {/* Hero Section */}
            <section className="relative pt-40 pb-20 px-6">
                <div className="container text-center relative z-10">
                    <motion.div
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true }}
                        variants={fadeIn}
                    >
                        <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-gold/10 text-gold text-xs font-bold uppercase tracking-widest mb-6">
                            <Sparkles size={14} /> The Future of Heritage
                        </span>
                        <h1 className="text-6xl md:text-8xl mb-8 leading-[1.05] tracking-tight text-midnight font-serif">
                            Your Stories, <br />
                            <span className="italic text-gold">Eternalized.</span>
                        </h1>
                        <p className="max-w-2xl mx-auto text-lg md:text-xl text-warm-gray mb-12 font-body leading-relaxed">
                            VANSH transforms your family’s oral histories into archival-quality biographies. Speak your legacy, and we’ll weave it into a beautifully illustrated book.
                        </p>
                        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                            <Link to="/register" className="btn-primary" style={{ padding: '1rem 2.5rem', fontSize: '1rem' }}>
                                Start Your First Chapter
                            </Link>
                            <Link to="/#how-it-works" className="btn-secondary" style={{ padding: '1rem 2.5rem', fontSize: '1rem' }}>
                                See How It Works
                            </Link>
                        </div>
                    </motion.div>
                </div>

                {/* Dynamic Background Elements */}
                <div className="absolute top-0 right-0 -z-0 opacity-10 blur-3xl">
                    <div className="w-[600px] h-[600px] bg-gold rounded-full transition-transform" />
                </div>
            </section>

            {/* How it Works Section */}
            <section id="how-it-works" className="py-32 px-6">
                <div className="container">
                    <motion.div
                        className="text-center mb-20"
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true }}
                        variants={fadeIn}
                    >
                        <h2 className="text-4xl md:text-5xl mb-6 text-midnight">The Archive Process</h2>
                        <div className="w-16 h-1 bg-gold mx-auto" />
                    </motion.div>

                    <motion.div
                        className="grid grid-cols-1 md:grid-cols-3 gap-8"
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true, margin: '-100px' }}
                        variants={stagger}
                    >
                        {[
                            {
                                icon: Mic,
                                title: "Voice Collection",
                                desc: "Record your stories naturally. Our studio captures the nuances of your voice and emotion."
                            },
                            {
                                icon: BookOpen,
                                title: "AI Synthesis",
                                desc: "Our Living Legacy engine polishes your narration into structured, high-end prose."
                            },
                            {
                                icon: Sparkles,
                                title: "Artistic Illustration",
                                desc: "Every chapter is paired with AI-generated visuals that reflect your unique heritage."
                            }
                        ].map((step, i) => (
                            <motion.div key={i} variants={fadeIn} className="glass-card p-10 hover:shadow-gold transition-all group">
                                <div className="w-14 h-14 rounded-2xl bg-midnight flex items-center justify-center text-ivory mb-8 group-hover:scale-110 transition-transform">
                                    <step.icon size={28} />
                                </div>
                                <h3 className="text-2xl mb-4 text-midnight">{step.title}</h3>
                                <p className="text-warm-gray leading-relaxed text-sm">{step.desc}</p>
                            </motion.div>
                        ))}
                    </motion.div>
                </div>
            </section>

            {/* Quote Section */}
            <section className="py-20 bg-midnight text-ivory text-center px-6">
                <motion.div
                    className="container"
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true }}
                    variants={fadeIn}
                >
                    <Quote size={48} className="text-gold opacity-30 mx-auto mb-8" />
                    <h2 className="text-2xl md:text-4xl leading-relaxed italic max-w-4xl mx-auto font-serif">
                        "We don't just write books; we craft time machines for the generations to come."
                    </h2>
                </motion.div>
            </section>

            {/* Pricing Section */}
            <section id="pricing" className="py-32 px-6">
                <div className="container max-w-4xl">
                    <motion.div
                        className="text-center mb-16"
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true }}
                        variants={fadeIn}
                    >
                        <h2 className="text-4xl md:text-5xl mb-6 text-midnight">Simple Pricing</h2>
                        <p className="text-warm-gray">No hidden fees. Just heritage.</p>
                    </motion.div>

                    <motion.div
                        className="glass-card overflow-hidden"
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true }}
                        variants={fadeIn}
                    >
                        <div className="grid grid-cols-1 md:grid-cols-2">
                            <div className="p-12 md:border-r border-black/5">
                                <h3 className="text-2xl mb-4 text-midnight">Legacy Starter</h3>
                                <p className="text-sm text-warm-gray mb-8">Perfect for a single life story or biography.</p>
                                <div className="text-5xl font-serif text-midnight mb-8">
                                    ₹2,499 <span className="text-xs font-accent text-warm-gray uppercase tracking-widest">/ Project</span>
                                </div>
                                <ul className="list-none space-y-4 p-0 mb-10">
                                    <li className="flex items-center gap-3 text-sm"><Zap size={16} className="text-gold" /> Unlimited Recordings</li>
                                    <li className="flex items-center gap-3 text-sm"><Zap size={16} className="text-gold" /> AI Chapter Generation</li>
                                    <li className="flex items-center gap-3 text-sm"><Zap size={16} className="text-gold" /> 10+ AI Illustrations</li>
                                    <li className="flex items-center gap-3 text-sm"><Zap size={16} className="text-gold" /> High-Res PDF Export</li>
                                </ul>
                                <Link to="/register" className="btn-primary w-full justify-center">Get Started Now</Link>
                            </div>
                            <div className="p-12 bg-cream flex flex-col justify-center">
                                <div className="mb-8 p-6 bg-gold/10 rounded-xl border border-gold/20">
                                    <h4 className="flex items-center gap-2 font-serif text-gold mb-2"><Shield size={18} /> Heritage Security</h4>
                                    <p className="text-xs text-warm-gray">Your data is encrypted and stored in our secure vault. We never sell your personal history.</p>
                                </div>
                                <p className="text-xs text-center opacity-60">
                                    Need multiple books for your family tree? <br />
                                    <a href="mailto:support@vansh.in" className="text-gold no-underline font-bold hover:underline">Contact for Family Bundles</a>
                                </p>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* Contact Section */}
            <section id="contact" className="py-32 px-6 bg-ivory">
                <div className="container max-w-4xl">
                    <motion.div
                        className="text-center mb-16"
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true }}
                        variants={fadeIn}
                    >
                        <h2 className="text-4xl md:text-5xl mb-6 text-midnight font-serif">Get in Touch</h2>
                        <p className="text-warm-gray max-w-xl mx-auto leading-relaxed">
                            Have questions about our preservation process? We're here to help you begin your family legacy journey.
                        </p>
                    </motion.div>

                    <motion.div
                        className="grid grid-cols-1 md:grid-cols-3 gap-8"
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true }}
                        variants={stagger}
                    >
                        {[
                            {
                                title: "Email Support",
                                value: "support@vansh.in",
                                label: "Send an Email",
                                href: "mailto:support@vansh.in"
                            },
                            {
                                title: "Phone",
                                value: "+91 98765 43210",
                                label: "Call Us",
                                href: "tel:+919876543210"
                            },
                            {
                                title: "Studio Address",
                                value: "Heritage Block, Bangalore",
                                label: "Visit Us",
                                href: "#"
                            }
                        ].map((item, i) => (
                            <motion.div key={i} variants={fadeIn} className="glass-card p-8 text-center border border-gold/10 hover:border-gold/30 transition-all">
                                <h4 className="text-xs font-accent font-bold uppercase tracking-widest text-gold mb-4">{item.title}</h4>
                                <p className="text-lg font-serif text-midnight mb-6">{item.value}</p>
                                <a href={item.href} className="text-sm font-accent font-semibold text-charcoal hover:text-gold transition-colors inline-flex items-center gap-2">
                                    {item.label} <ChevronRight size={14} />
                                </a>
                            </motion.div>
                        ))}
                    </motion.div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="py-20 relative px-6">
                <div className="container text-center">
                    <motion.div
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true }}
                        variants={fadeIn}
                        className="glass-dark p-20 rounded-[40px] text-ivory relative overflow-hidden"
                    >
                        <div className="relative z-10">
                            <h2 className="text-4xl md:text-5xl mb-8 font-serif leading-tight">Start Your Forever <br /> Today.</h2>
                            <Link to="/register" className="btn-primary btn-gold" style={{ padding: '1rem 3rem' }}>
                                Create Your Legacy <ChevronRight size={18} />
                            </Link>
                        </div>
                        {/* Glow */}
                        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full bg-gold/10 blur-[100px] pointer-events-none" />
                    </motion.div>
                </div>
            </section>

            <Footer />
        </div>
    );
}
