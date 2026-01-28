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
            title_login: 'Sign in to Nexus',
            title_register: 'Join Nexus',
            subtitle_login: 'Enter your details to access the terminal.',
            subtitle_register: 'Create your institutional account.',
            email_label: 'Email',
            email_placeholder: 'name@company.com',
            pass_label: 'Password',
            pass_placeholder: '••••••••',
            btn_login: 'Sign In',
            btn_register: 'Create Account',
            switch_to_register: 'Don\'t have an account?',
            switch_to_login: 'Already have an account?',
            switch_action_register: 'Sign up',
            switch_action_login: 'Sign in',
            or_text: 'or',
            google_btn: 'Continue with Google',
            terms_text: 'By signing up, you agree to our',
            terms_link: 'Terms',
            privacy_link: 'Privacy',
            risk_link: 'Risk',
            footer: '© 2024 Nexus AI. Institutional Grade Execution.'
        },
        es: {
            title_login: 'Iniciar sesión en Nexus',
            title_register: 'Unirse a Nexus',
            subtitle_login: 'Introduce tus datos para acceder al terminal.',
            subtitle_register: 'Crea tu cuenta institucional.',
            email_label: 'Correo',
            email_placeholder: 'nombre@empresa.com',
            pass_label: 'Contraseña',
            pass_placeholder: '••••••••',
            btn_login: 'Entrar',
            btn_register: 'Crear Cuenta',
            switch_to_register: '¿No tienes cuenta?',
            switch_to_login: '¿Ya tienes cuenta?',
            switch_action_register: 'Regístrate',
            switch_action_login: 'Inicia sesión',
            or_text: 'o',
            google_btn: 'Continuar con Google',
            terms_text: 'Al registrarte, aceptas nuestros',
            terms_link: 'Términos',
            privacy_link: 'Privacidad',
            risk_link: 'Riesgos',
            footer: '© 2024 Nexus AI. Ejecución de Grado Institucional.'
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
                setMessage({ type: 'success', text: lang === 'en' ? 'Check your email to confirm.' : 'Verifica tu correo para confirmar.' });
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
        <div className="min-h-screen bg-black text-white font-sans flex items-center justify-center relative overflow-hidden selection:bg-[#00ffa3] selection:text-black">
            <LegalModal isOpen={!!legalModal} onClose={() => setLegalModal(null)} type={legalModal || 'terms'} />

            {/* Language Switch */}
            <div className="absolute top-6 right-8 z-50">
                <div className="flex bg-[#16181c] rounded-full p-1 border border-[#2f3336]">
                    <button
                        onClick={() => setLang('en')}
                        className={`px-4 py-1.5 rounded-full text-[11px] font-bold transition-all ${lang === 'en' ? 'bg-[#E7E9EA] text-black' : 'text-[#71767B] hover:text-[#E7E9EA]'}`}
                    >
                        EN
                    </button>
                    <button
                        onClick={() => setLang('es')}
                        className={`px-4 py-1.5 rounded-full text-[11px] font-bold transition-all ${lang === 'es' ? 'bg-[#E7E9EA] text-black' : 'text-[#71767B] hover:text-[#E7E9EA]'}`}
                    >
                        ES
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="w-full max-w-[400px] p-6 z-10 animate-fade-in">

                {/* Logo */}
                <div className="flex justify-center mb-10">
                    <div className="w-20 h-20 bg-black rounded-xl flex items-center justify-center border border-[#1d1f23] shadow-2xl shadow-[#00ffa3]/10">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src="/nexus-logo.png" alt="Nexus AI" className="w-16 h-16 object-contain" />
                    </div>
                </div>

                <div className="mb-8 text-center">
                    <h1 className="text-3xl font-bold tracking-tight text-[#E7E9EA] mb-2">
                        {isRegistering ? t.title_register : t.title_login}
                    </h1>
                    <p className="text-[#71767B] text-sm">
                        {isRegistering ? t.subtitle_register : t.subtitle_login}
                    </p>
                </div>

                <form onSubmit={handleAuth} className="space-y-5">

                    {/* Inputs */}
                    <div className="space-y-4">
                        <div className="group">
                            <input
                                type="email"
                                required
                                placeholder={t.email_placeholder}
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full bg-black border border-[#333639] focus:border-[#00ffa3] rounded-md px-4 py-3.5 text-[#E7E9EA] placeholder-[#71767B] outline-none transition-colors text-[15px]"
                            />
                        </div>

                        <div className="relative group">
                            <input
                                type={showPassword ? 'text' : 'password'}
                                required
                                minLength={6}
                                placeholder={t.pass_placeholder}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full bg-black border border-[#333639] focus:border-[#00ffa3] rounded-md px-4 py-3.5 text-[#E7E9EA] placeholder-[#71767B] outline-none transition-colors text-[15px] pr-10"
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#71767B] hover:text-[#E7E9EA] transition-colors"
                            >
                                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>
                    </div>

                    {isRegistering && (
                        <div className="flex items-start gap-3 mt-2">
                            <input
                                type="checkbox"
                                required
                                className="mt-1 w-4 h-4 rounded-sm border-[#333639] bg-black checked:bg-[#00ffa3] checked:border-[#00ffa3] focus:ring-0 focus:ring-offset-0 cursor-pointer appearance-none border"
                            />
                            <p className="text-[12px] text-[#71767B] leading-snug">
                                {t.terms_text} <span onClick={(e) => { e.preventDefault(); setLegalModal('terms'); }} className="text-[#00ffa3] hover:underline cursor-pointer">{t.terms_link}</span> & <span onClick={(e) => { e.preventDefault(); setLegalModal('privacy'); }} className="text-[#00ffa3] hover:underline cursor-pointer">{t.privacy_link}</span>.
                            </p>
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-white hover:bg-[#E7E9EA] text-black font-bold py-3.5 rounded-full transition-all disabled:opacity-50 text-[15px] shadow-[0_4px_14px_0_rgba(255,255,255,0.15)]"
                    >
                        {loading ? <Loader2 className="animate-spin mx-auto" size={20} /> : (isRegistering ? t.btn_register : t.btn_login)}
                    </button>
                </form>

                <div className="relative my-8">
                    <div className="absolute inset-0 flex items-center">
                        <div className="w-full border-t border-[#2f3336]"></div>
                    </div>
                    <div className="relative flex justify-center text-xs uppercase tracking-wider">
                        <span className="bg-black px-3 text-[#71767B]">{t.or_text}</span>
                    </div>
                </div>

                <div className="space-y-3">
                    <button
                        onClick={handleGoogleLogin}
                        className="w-full bg-black border border-[#2f3336] hover:bg-[#16181c] text-[#E7E9EA] font-medium py-3.5 rounded-full transition-all flex items-center justify-center gap-2 text-[15px]"
                    >
                        <Chrome size={18} />
                        {t.google_btn}
                    </button>
                </div>

                <div className="mt-10 text-center">
                    <p className="text-[#71767B] text-[15px]">
                        {isRegistering ? t.switch_to_register : t.switch_to_login}{' '}
                        <button
                            onClick={() => {
                                setIsRegistering(!isRegistering);
                                setMessage(null);
                            }}
                            className="text-[#00ffa3] hover:underline font-medium"
                        >
                            {isRegistering ? t.switch_action_login : t.switch_action_register}
                        </button>
                    </p>
                </div>

                {/* Status Messages */}
                {message && (
                    <div className={`mt-6 p-4 rounded-md border text-sm font-medium text-center ${message.type === 'success'
                        ? 'bg-[#00ffa3]/10 border-[#00ffa3]/20 text-[#00ffa3]'
                        : 'bg-red-500/10 border-red-500/20 text-red-500'
                        }`}>
                        {message.text}
                    </div>
                )}

            </div>

            {/* Footer */}
            <div className="absolute bottom-6 w-full text-center">
                <p className="text-[11px] text-[#2f3336] uppercase tracking-widest font-semibold">{t.footer}</p>
            </div>

        </div>
    );
}
