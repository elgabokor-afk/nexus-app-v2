'use client';

import { useState } from 'react';
import { supabase } from '@/lib/supabaseClient';
import { Zap, Mail, Chrome, ArrowRight, Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isRegistering, setIsRegistering] = useState(false);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
    const router = useRouter();

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
                setMessage({ type: 'success', text: 'Account created! Check email to confirm.' });
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
        <div className="min-h-screen bg-[#050505] flex items-center justify-center p-4 relative overflow-hidden">
            {/* Background Effects */}
            <div className="absolute top-0 left-0 w-full h-full opacity-20 pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-[#00ffa3]/20 rounded-full blur-[120px]"></div>
                <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-500/10 rounded-full blur-[120px]"></div>
            </div>

            <div className="w-full max-w-[440px] z-10">
                <div className="bg-[#0a0a0c]/80 backdrop-blur-3xl border border-white/10 rounded-[2.5rem] p-8 md:p-12 shadow-2xl relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[#00ffa3]/30 to-transparent"></div>

                    {/* Header */}
                    <div className="flex flex-col items-center text-center mb-8">
                        <div className="w-16 h-16 bg-[#00ffa3] rounded-2xl flex items-center justify-center shadow-[0_0_30px_rgba(0,255,163,0.4)] mb-6 rotate-3 hover:rotate-0 transition-transform duration-500">
                            <Zap size={32} className="text-black fill-black" strokeWidth={2.5} />
                        </div>
                        <h1 className="text-2xl font-black tracking-tighter text-white mb-1">
                            {isRegistering ? 'INITIALIZE NODE' : 'ACCESS TERMINAL'}
                        </h1>
                        <p className="text-gray-500 text-xs font-bold uppercase tracking-widest">
                            {isRegistering ? 'Create your secure identity' : 'Enter credentials to proceed'}
                        </p>
                    </div>

                    {/* Auth Form */}
                    <div className="space-y-6">
                        <form onSubmit={handleAuth} className="space-y-4">
                            <div className="space-y-3">
                                <div className="relative group">
                                    <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-500 group-focus-within:text-[#00ffa3] transition-colors">
                                        <Mail size={18} />
                                    </div>
                                    <input
                                        type="email"
                                        placeholder="Email Address"
                                        required
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        className="w-full bg-white/5 border border-white/10 rounded-2xl py-3.5 pl-12 pr-4 text-white focus:outline-none focus:border-[#00ffa3]/50 focus:ring-1 focus:ring-[#00ffa3]/20 transition-all font-medium text-sm"
                                    />
                                </div>
                                <div className="relative group">
                                    <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-500 group-focus-within:text-[#00ffa3] transition-colors">
                                        <div className="w-4 h-4 border-2 border-current rounded-sm"></div>
                                    </div>
                                    <input
                                        type="password"
                                        placeholder="Password"
                                        required
                                        minLength={6}
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        className="w-full bg-white/5 border border-white/10 rounded-2xl py-3.5 pl-12 pr-4 text-white focus:outline-none focus:border-[#00ffa3]/50 focus:ring-1 focus:ring-[#00ffa3]/20 transition-all font-medium text-sm"
                                    />
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full bg-[#00ffa3] hover:bg-[#00ffa3]/90 text-black font-black py-4 rounded-2xl flex items-center justify-center gap-2 transition-all active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100 uppercase tracking-wider text-sm mt-2 shadow-[0_0_20px_rgba(0,255,163,0.3)] hover:shadow-[0_0_30px_rgba(0,255,163,0.5)]"
                            >
                                {loading ? (
                                    <Loader2 className="animate-spin" size={18} />
                                ) : (
                                    <>
                                        {isRegistering ? 'DEPLOY ACCOUNT' : 'AUTHENTICATE'} <ArrowRight size={18} />
                                    </>
                                )}
                            </button>
                        </form>

                        <div className="text-center">
                            <button
                                onClick={() => {
                                    setIsRegistering(!isRegistering);
                                    setMessage(null);
                                }}
                                className="text-xs font-bold text-gray-500 hover:text-white transition-colors uppercase tracking-widest"
                            >
                                {isRegistering ? 'Already have a node? Login' : 'New System? Initialize'}
                            </button>
                        </div>

                        <div className="relative flex items-center justify-center py-2">
                            <div className="absolute w-full h-[1px] bg-white/5"></div>
                            <span className="relative bg-[#0d0d0f] px-4 text-[10px] text-gray-600 font-black uppercase tracking-widest">or integrate with</span>
                        </div>

                        <button
                            onClick={handleGoogleLogin}
                            className="w-full bg-white/[0.03] hover:bg-white/[0.06] border border-white/10 text-white font-bold py-4 rounded-2xl flex items-center justify-center gap-3 transition-all active:scale-[0.98]"
                        >
                            <Chrome size={18} />
                            Continue with Google
                        </button>

                        {/* Status Messages */}
                        {message && (
                            <div className={`mt-2 p-4 rounded-2xl border text-xs font-bold text-center animate-in fade-in slide-in-from-top-2 duration-300 ${message.type === 'success'
                                    ? 'bg-green-500/10 border-green-500/20 text-green-400'
                                    : 'bg-red-500/10 border-red-500/20 text-red-400'
                                }`}>
                                {message.text}
                            </div>
                        )}
                    </div>
                </div>

                {/* Footer Footer */}
                <p className="text-center mt-8 text-[10px] text-gray-600 font-bold uppercase tracking-[0.3em]">
                    Institutional Grade Execution • Optimized for Kraken
                </p>
            </div>
        </div>
    );
}
