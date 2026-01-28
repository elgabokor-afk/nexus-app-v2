'use client';

import { useState } from 'react';
import { supabase } from '@/lib/supabaseClient';
import { Zap, Mail, Chrome, ArrowRight, Loader2, Lock, Eye, EyeOff, Globe } from 'lucide-react';
import { useRouter } from 'next/navigation';
import LegalModal from '@/components/LegalModal';

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [isRegistering, setIsRegistering] = useState(false);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
    const [lang, setLang] = useState<'en' | 'es'>('en');
    const [legalModal, setLegalModal] = useState<'terms' | 'privacy' | 'risk' | null>(null);
    const router = useRouter();

    const t = {
        en: {
            title_login: 'Access Terminal',
            title_register: 'Initialize Node',
            subtitle_login: 'Enter credentials to proceed',
            subtitle_register: 'Create your secure identity',
            email_label: 'Email',
            email_placeholder: 'Email Address',
            pass_label: 'Password',
            pass_placeholder: 'Password',
            btn_login: 'Authenticate',
            btn_register: 'Deploy Account',
            switch_to_register: 'New System? Initialize',
            switch_to_login: 'Already have a node? Login',
            or_text: 'or integrate with',
            google_btn: 'Continue with Google',
            terms_text: 'I certify that I have read and accept the',
            terms_link: 'Terms of Service',
            privacy_link: 'Privacy Policy',
            risk_link: 'Risk Disclaimer',
            marketing_text: 'I agree to receive marketing updates.',
            footer: 'Institutional Grade Execution • Optimized for Kraken'
        },
        es: {
            title_login: 'Acceder a Terminal',
            title_register: 'Inicializar Nodo',
            subtitle_login: 'Ingrese credenciales para proceder',
            subtitle_register: 'Cree su identidad segura',
            email_label: 'Correo Electrónico',
            email_placeholder: 'Correo Electrónico',
            pass_label: 'Contraseña',
            pass_placeholder: 'Contraseña',
            btn_login: 'Autenticar',
            btn_register: 'Desplegar Cuenta',
            switch_to_register: '¿Sistema Nuevo? Inicializar',
            switch_to_login: '¿Ya tiene nodo? Ingresar',
            or_text: 'o integrar con',
            google_btn: 'Continuar con Google',
            terms_text: 'Certifico que he leído y acepto el',
            terms_link: 'Términos de Servicio',
            privacy_link: 'Política de Privacidad',
            risk_link: 'Aviso de Riesgo',
            marketing_text: 'Acepto recibir actualizaciones de marketing.',
            footer: 'Ejecución de Grado Institucional • Optimizado para Kraken'
        }
    }[lang];

    const handleAuth = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setMessage(null);

        try {
            if (isRegistering) {
                const { error } = await supabase.auth.signUp({
                    email,
                    password,
                    options: {
                        emailRedirectTo: `${window.location.origin}/auth/callback`,
                    },
                });
                if (error) throw error;
                setMessage({ type: 'success', text: lang === 'en' ? 'Account created! Check email.' : '¡Cuenta creada! Revise su correo.' });
            } else {
                const { error } = await supabase.auth.signInWithPassword({
                    email,
                    password,
                });
                if (error) throw error;
                router.push('/dashboard');
            }
        } catch (error: any) {
            setMessage({ type: 'error', text: error.message });
        } finally {
            setLoading(false);
        }
    };

    const handleGoogleLogin = async () => {
        const { error } = await supabase.auth.signInWithOAuth({
            provider: 'google',
            options: {
                redirectTo: `${window.location.origin}/dashboard`,
            },
        });
        if (error) setMessage({ type: 'error', text: error.message });
    };

    return (
        <div className="min-h-screen bg-[#050505] grid lg:grid-cols-2 relative overflow-hidden font-sans text-white">

            {/* Legal Modal */}
            <LegalModal
                isOpen={!!legalModal}
                onClose={() => setLegalModal(null)}
                type={legalModal || 'terms'}
            />

            {/* Left: Visual Side (Desktop Only) */}
            <div className="hidden lg:flex flex-col justify-between p-12 relative overflow-hidden bg-[#0a0a0c] border-r border-white/5">
                <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10"></div>
                <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-[#00ffa3]/5 rounded-full blur-[120px]"></div>

                <div className="z-10">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-10 h-10 bg-[#00ffa3] rounded-xl flex items-center justify-center rotate-3 shadow-[0_0_15px_rgba(0,255,163,0.4)]">
                            <Zap size={20} className="text-black fill-black" strokeWidth={3} />
                        </div>
                        <span className="font-black text-xl tracking-tighter text-white">NEXUS<span className="text-[#00ffa3]">AI</span></span>
                    </div>
                    <h2 className="text-4xl font-black text-white leading-tight mb-4">
                        Algo-Trading <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#00ffa3] to-emerald-500">
                            Reinvented.
                        </span>
                    </h2>
                    <p className="text-gray-500 max-w-md font-medium">
                        Deploy institutional-grade strategies with zero latency.
                        Powered by Cosmos AI 3.0.
                    </p>
                </div>

                <div className="z-10 bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10">
                    <div className="flex items-center gap-4 mb-3">
                        <div className="flex -space-x-3">
                            {[1, 2, 3].map(i => (
                                <div key={i} className="w-8 h-8 rounded-full bg-gray-800 border-2 border-[#0a0a0c] flex items-center justify-center text-[10px] font-bold text-gray-400">
                                    AI
                                </div>
                            ))}
                        </div>
                        <div className="text-xs text-gray-400">
                            <strong className="text-white">1,200+ Traders</strong> deployed nodes today.
                        </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-white/5">
                        <div>
                            <div className="text-2xl font-bold text-white">&lt; 50ms</div>
                            <div className="text-[10px] text-gray-500 uppercase tracking-widest font-bold mt-1">Latency</div>
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-white">99.9%</div>
                            <div className="text-[10px] text-gray-500 uppercase tracking-widest font-bold mt-1">Uptime</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Right: Auth Side */}
            <div className="flex flex-col items-center justify-center p-6 relative bg-[#050505]">

                {/* Language Switcher */}
                <div className="absolute top-6 right-6 flex gap-2">
                    <button
                        onClick={() => setLang('en')}
                        className={`text-xs font-bold px-3 py-1.5 rounded-lg transition-colors border border-transparent ${lang === 'en' ? 'bg-[#00ffa3]/10 text-[#00ffa3] border-[#00ffa3]/20' : 'text-gray-600 hover:text-white'}`}
                    >
                        EN
                    </button>
                    <button
                        onClick={() => setLang('es')}
                        className={`text-xs font-bold px-3 py-1.5 rounded-lg transition-colors border border-transparent ${lang === 'es' ? 'bg-[#00ffa3]/10 text-[#00ffa3] border-[#00ffa3]/20' : 'text-gray-600 hover:text-white'}`}
                    >
                        ES
                    </button>
                </div>

                <div className="w-full max-w-[400px]">
                    {/* Header (Mobile) */}
                    <div className="lg:hidden flex justify-center mb-8">
                        <div className="w-12 h-12 bg-[#00ffa3] rounded-xl flex items-center justify-center rotate-3 shadow-[0_0_20px_rgba(0,255,163,0.3)]">
                            <Zap size={24} className="text-black fill-black" strokeWidth={3} />
                        </div>
                    </div>

                    <div className="mb-8">
                        <h1 className="text-3xl font-black tracking-tighter text-white mb-2">
                            {isRegistering ? t.title_register : t.title_login}
                        </h1>
                        <p className="text-gray-500 font-medium">
                            {isRegistering ? t.subtitle_register : t.subtitle_login}
                        </p>
                    </div>

                    <form onSubmit={handleAuth} className="space-y-4">
                        <div className="space-y-4">
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-500 group-focus-within:text-[#00ffa3] transition-colors">
                                    <Mail size={18} />
                                </div>
                                <input
                                    type="email"
                                    placeholder={t.email_placeholder}
                                    required
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full bg-[#0a0a0c] border border-white/10 rounded-xl py-4 pl-12 pr-4 text-white focus:outline-none focus:border-[#00ffa3]/50 focus:ring-1 focus:ring-[#00ffa3]/20 transition-all font-medium text-sm placeholder:text-gray-600"
                                />
                            </div>
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-500 group-focus-within:text-[#00ffa3] transition-colors">
                                    <div className="w-4 h-4 border-2 border-current rounded-sm"></div>
                                </div>
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    placeholder={t.pass_placeholder}
                                    required
                                    minLength={6}
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full bg-[#0a0a0c] border border-white/10 rounded-xl py-4 pl-12 pr-12 text-white focus:outline-none focus:border-[#00ffa3]/50 focus:ring-1 focus:ring-[#00ffa3]/20 transition-all font-medium text-sm placeholder:text-gray-600"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white transition-colors"
                                >
                                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                </button>
                            </div>
                        </div>

                        {isRegistering && (
                            <div className="flex items-start gap-3 px-1 py-1">
                                <div className="relative flex items-center pt-0.5">
                                    <input
                                        type="checkbox"
                                        id="terms"
                                        required
                                        className="peer h-4 w-4 shrink-0 cursor-pointer appearance-none rounded border border-gray-600 bg-[#0a0a0c] checked:border-[#00ffa3] checked:bg-[#00ffa3] focus:outline-none focus:ring-1 focus:ring-[#00ffa3]/50 transition-all"
                                    />
                                    <svg className="pointer-events-none absolute left-1/2 top-1/2 -ml-2 -mt-2 hidden h-4 w-4 text-black peer-checked:block" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                </div>
                                <label htmlFor="terms" className="text-[11px] text-gray-400 font-medium leading-tight cursor-pointer select-none">
                                    {t.terms_text}
                                    <span onClick={(e) => { e.preventDefault(); setLegalModal('risk'); }} className="text-[#00ffa3] hover:underline px-1 cursor-pointer">{t.risk_link}</span>
                                    &
                                    <span onClick={(e) => { e.preventDefault(); setLegalModal('terms'); }} className="text-[#00ffa3] hover:underline px-1 cursor-pointer">{t.terms_link}</span>
                                </label>
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-[#00ffa3] hover:bg-[#00ffa3]/90 text-black font-black py-4 rounded-xl flex items-center justify-center gap-2 transition-all active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100 uppercase tracking-wider text-sm shadow-[0_0_20px_rgba(0,255,163,0.3)] hover:shadow-[0_0_30px_rgba(0,255,163,0.5)]"
                        >
                            {loading ? (
                                <Loader2 className="animate-spin" size={18} />
                            ) : (
                                <>
                                    {isRegistering ? t.btn_register : t.btn_login} <ArrowRight size={18} />
                                </>
                            )}
                        </button>
                    </form>

                    <div className="mt-8 text-center">
                        <button
                            onClick={() => {
                                setIsRegistering(!isRegistering);
                                setMessage(null);
                            }}
                            className="text-xs font-bold text-gray-500 hover:text-white transition-colors"
                        >
                            {isRegistering ? t.switch_to_login : t.switch_to_register}
                        </button>
                    </div>

                    <div className="relative flex items-center justify-center py-6">
                        <div className="absolute w-full h-[1px] bg-white/5"></div>
                        <span className="relative bg-[#050505] px-4 text-[10px] text-gray-600 font-bold uppercase tracking-widest">{t.or_text}</span>
                    </div>

                    <button
                        onClick={handleGoogleLogin}
                        className="w-full bg-white/[0.03] hover:bg-white/[0.06] border border-white/10 text-white font-bold py-4 rounded-xl flex items-center justify-center gap-3 transition-all active:scale-[0.98]"
                    >
                        <Chrome size={18} />
                        {t.google_btn}
                    </button>

                    {/* Status Messages */}
                    {message && (
                        <div className={`mt-6 p-4 rounded-xl border text-xs font-bold text-center animate-in fade-in slide-in-from-top-2 duration-300 ${message.type === 'success'
                            ? 'bg-green-500/10 border-green-500/20 text-green-400'
                            : 'bg-red-500/10 border-red-500/20 text-red-400'
                            }`}>
                            {message.text}
                        </div>
                    )}
                </div>

                <p className="mt-auto pt-10 text-center text-[10px] text-gray-700 font-medium">
                    {t.footer}
                </p>
            </div>
        </div>
    );
}
