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
            title_login: 'Welcome Back',
            title_register: 'Create Information',
            subtitle_login: 'Log in with your email and password.',
            subtitle_register: 'Register a new account.',
            email_label: 'Email',
            email_placeholder: 'Enter your email',
            pass_label: 'Password',
            pass_placeholder: 'Enter your password',
            btn_login: 'Log In',
            btn_register: 'Register',
            switch_to_register: 'Not registered yet? Create an Account',
            switch_to_login: 'Already have an account? Log In',
            or_text: 'Or continue with',
            google_btn: 'Google',
            terms_text: 'By registering, I agree to the',
            terms_link: 'Terms of Use',
            privacy_link: 'Privacy Policy',
            risk_link: 'Risk Disclosure',
            marketing_text: 'I agree to receive marketing updates.',
            footer_copy: '© 2024 Nexus AI. All rights reserved.'
        },
        es: {
            title_login: 'Bienvenido de nuevo',
            title_register: 'Crear Información',
            subtitle_login: 'Inicia sesión con tu correo y contraseña.',
            subtitle_register: 'Registra una nueva cuenta.',
            email_label: 'Correo Electrónico',
            email_placeholder: 'Introduce tu correo',
            pass_label: 'Contraseña',
            pass_placeholder: 'Introduce tu contraseña',
            btn_login: 'Iniciar Sesión',
            btn_register: 'Registrarse',
            switch_to_register: '¿No estás registrado? Crear Cuenta',
            switch_to_login: '¿Ya tienes cuenta? Iniciar Sesión',
            or_text: 'O continúa con',
            google_btn: 'Google',
            terms_text: 'Al registrarme, acepto los',
            terms_link: 'Términos de Uso',
            privacy_link: 'Política de Privacidad',
            risk_link: 'Divulgación de Riesgos',
            marketing_text: 'Acepto recibir actualizaciones de marketing.',
            footer_copy: '© 2024 Nexus AI. Todos los derechos reservados.'
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
        <div className="min-h-screen bg-[#181A20] text-[#EAECEF] font-sans flex relative overflow-hidden">
            <LegalModal isOpen={!!legalModal} onClose={() => setLegalModal(null)} type={legalModal || 'terms'} />

            {/* Language Switch */}
            <div className="absolute top-6 right-6 z-50">
                <div className="flex bg-[#2B3139] rounded-md p-1">
                    <button
                        onClick={() => setLang('en')}
                        className={`px-3 py-1 rounded text-xs font-bold transition-all ${lang === 'en' ? 'bg-[#FCD535] text-black' : 'text-[#848E9C] hover:text-[#EAECEF]'}`}
                    >
                        EN
                    </button>
                    <button
                        onClick={() => setLang('es')}
                        className={`px-3 py-1 rounded text-xs font-bold transition-all ${lang === 'es' ? 'bg-[#FCD535] text-black' : 'text-[#848E9C] hover:text-[#EAECEF]'}`}
                    >
                        ES
                    </button>
                </div>
            </div>

            {/* Left Side: Exchange Visual (Desktop) */}
            <div className="hidden lg:flex flex-col justify-center items-center w-1/2 p-16 relative bg-[#0b0e11]">
                {/* Decorative Globe/Grid */}
                <div className="absolute inset-0 opacity-20 pointer-events-none bg-[url('https://upload.wikimedia.org/wikipedia/commons/e/ec/World_map_blank_without_borders.svg')] bg-no-repeat bg-center bg-contain filter invert"></div>

                <div className="z-10 text-center max-w-lg">
                    <h1 className="text-5xl font-bold mb-6 text-[#EAECEF] tracking-tight">
                        Trading, <span className="text-[#FCD535]">Simplified.</span>
                    </h1>
                    <p className="text-[#848E9C] text-lg leading-relaxed mb-10">
                        Join the world's leading crypto automation platform.
                        Trade with confidence, precision, and institutional-grade tools.
                    </p>

                    {/* Trust Badges */}
                    <div className="grid grid-cols-3 gap-8 border-t border-[#2B3139] pt-8">
                        <div>
                            <div className="text-2xl font-bold text-[#EAECEF]">2.4M</div>
                            <div className="text-xs text-[#848E9C] uppercase tracking-wide mt-1">Users</div>
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-[#EAECEF]">$12B</div>
                            <div className="text-xs text-[#848E9C] uppercase tracking-wide mt-1">Volume</div>
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-[#EAECEF]">&lt; 50ms</div>
                            <div className="text-xs text-[#848E9C] uppercase tracking-wide mt-1">Latency</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Right Side: Form */}
            <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-[#181A20]">
                <div className="w-full max-w-[420px]">

                    {/* Header Mobile */}
                    <div className="lg:hidden mb-8 text-center">
                        <div className="inline-flex items-center justify-center w-12 h-12 bg-[#FCD535] rounded-xl mb-4">
                            <Zap className="text-black" size={24} fill="black" />
                        </div>
                    </div>

                    <div className="mb-8">
                        <div className="hidden lg:block mb-6 text-[#FCD535]">
                            <Zap size={32} fill="#FCD535" />
                        </div>
                        <h2 className="text-3xl font-bold mb-2 text-[#EAECEF]">
                            {isRegistering ? t.title_register : t.title_login}
                        </h2>
                        <p className="text-[#848E9C]">
                            {isRegistering ? t.subtitle_register : t.subtitle_login}
                        </p>
                    </div>

                    <form onSubmit={handleAuth} className="space-y-6">

                        {/* Email Input */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-[#EAECEF]">{t.email_label}</label>
                            <div className="relative">
                                <input
                                    type="email"
                                    required
                                    placeholder={t.email_placeholder}
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full bg-[#2B3139] border border-transparent hover:border-[#474D57] focus:border-[#FCD535] rounded-lg px-4 py-3 text-[#EAECEF] placeholder-[#474D57] outline-none transition-all text-sm font-medium"
                                />
                            </div>
                        </div>

                        {/* Password Input */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-[#EAECEF]">{t.pass_label}</label>
                            <div className="relative">
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    required
                                    minLength={6}
                                    placeholder={t.pass_placeholder}
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full bg-[#2B3139] border border-transparent hover:border-[#474D57] focus:border-[#FCD535] rounded-lg px-4 py-3 text-[#EAECEF] placeholder-[#474D57] outline-none transition-all text-sm font-medium pr-10"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[#848E9C] hover:text-[#EAECEF]"
                                >
                                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                </button>
                            </div>
                        </div>

                        {/* Terms Checkbox (Register Only) */}
                        {isRegistering && (
                            <div className="space-y-4">
                                <label className="flex items-start gap-3 cursor-pointer group">
                                    <input
                                        type="checkbox"
                                        required
                                        className="mt-1 w-4 h-4 rounded border-[#474D57] bg-transparent text-[#FCD535] focus:ring-0 focus:ring-offset-0 cursor-pointer"
                                    />
                                    <div className="text-xs text-[#848E9C] leading-snug group-hover:text-[#b7bdc6] transition-colors">
                                        {t.terms_text} <span onClick={(e) => { e.preventDefault(); setLegalModal('terms'); }} className="text-[#FCD535] hover:underline">{t.terms_link}</span> & <span onClick={(e) => { e.preventDefault(); setLegalModal('privacy'); }} className="text-[#FCD535] hover:underline">{t.privacy_link}</span>.
                                    </div>
                                </label>
                                <label className="flex items-start gap-3 cursor-pointer group">
                                    <input
                                        type="checkbox"
                                        className="mt-1 w-4 h-4 rounded border-[#474D57] bg-transparent text-[#FCD535] focus:ring-0 focus:ring-offset-0 cursor-pointer"
                                    />
                                    <div className="text-xs text-[#848E9C] leading-snug group-hover:text-[#b7bdc6] transition-colors">
                                        {t.marketing_text}
                                    </div>
                                </label>
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-[#FCD535] hover:bg-[#F0C930] text-[#181A20] font-bold py-3 rounded-lg transition-colors disabled:opacity-50 text-base"
                        >
                            {loading ? <Loader2 className="animate-spin mx-auto" size={20} /> : (isRegistering ? t.btn_register : t.btn_login)}
                        </button>
                    </form>

                    <div className="relative my-8">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-[#2B3139]"></div>
                        </div>
                        <div className="relative flex justify-center text-sm">
                            <span className="bg-[#181A20] px-4 text-[#848E9C]">{t.or_text}</span>
                        </div>
                    </div>

                    <button
                        onClick={handleGoogleLogin}
                        className="w-full bg-[#2B3139] hover:bg-[#343a41] text-[#EAECEF] font-medium py-3 rounded-lg transition-colors flex items-center justify-center gap-3 text-sm"
                    >
                        <Chrome size={20} />
                        {t.google_btn}
                    </button>

                    <div className="mt-8 text-center bg-[#2b3139]/20 p-4 rounded-lg">
                        <button
                            onClick={() => {
                                setIsRegistering(!isRegistering);
                                setMessage(null);
                            }}
                            className="text-[#FCD535] hover:text-[#F0C930] text-sm font-bold transition-colors"
                        >
                            {isRegistering ? t.switch_to_login : t.switch_to_register}
                        </button>
                    </div>

                    {message && (
                        <div className={`mt-4 p-3 rounded-lg text-sm text-center ${message.type === 'success' ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-500'}`}>
                            {message.text}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
