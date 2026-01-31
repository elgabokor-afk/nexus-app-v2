'use client';

import { useState } from 'react';
import { Check, Lock, Zap, ArrowRight, ShieldCheck } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function WelcomePage() {
    const router = useRouter();
    const [step, setStep] = useState(1);

    return (
        <div className="min-h-screen bg-[#050505] text-white font-sans flex items-center justify-center p-6 relative overflow-hidden">

            {/* Background Ambient */}
            <div className="absolute top-0 left-0 w-full h-full pointer-events-none">
                <div className="absolute top-[-20%] left-[-20%] w-[800px] h-[800px] bg-[#00ffa3]/5 rounded-full blur-[150px]"></div>
                <div className="absolute bottom-[-20%] right-[-20%] w-[600px] h-[600px] bg-[#7c3aed]/5 rounded-full blur-[150px]"></div>
            </div>

            <div className="relative z-10 max-w-2xl w-full">

                {/* Header */}
                <div className="text-center mb-12">
                    <h1 className="text-4xl md:text-5xl font-black tracking-tighter mb-4">
                        WELCOME TO <span className="text-[#00ffa3]">NEXUS</span>
                    </h1>
                    <p className="text-gray-500 text-sm tracking-widest uppercase font-bold">The Institutional Grade AI Assistant</p>
                </div>

                {/* Steps Container */}
                <div className="grid gap-6">

                    {/* STEP 1: REGISTRATION (Done) */}
                    <div className={`
                        p-6 rounded-3xl border transition-all duration-500
                        ${step >= 1 ? 'bg-white/[0.03] border-[#00ffa3]/30' : 'bg-transparent border-white/5 opacity-50'}
                    `}>
                        <div className="flex items-center gap-4">
                            <div className="w-10 h-10 rounded-full bg-[#00ffa3]/10 flex items-center justify-center border border-[#00ffa3]/30">
                                <Check size={20} className="text-[#00ffa3]" />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-white">Account Created</h3>
                                <p className="text-gray-500 text-xs mt-1">Your secure terminal ID has been generated.</p>
                            </div>
                        </div>
                    </div>

                    {/* STEP 2: VIP ACTIVATION (Interactive) */}
                    <div className={`
                        p-6 rounded-3xl border transition-all duration-500 group cursor-pointer
                        ${step === 2 ? 'bg-[#00ffa3]/5 border-[#00ffa3] shadow-[0_0_30px_rgba(0,255,163,0.1)]' : 'bg-white/[0.02] border-white/5'}
                    `} onClick={() => router.push('/dashboard')}>
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className={`w-10 h-10 rounded-full flex items-center justify-center border ${step === 2 ? 'bg-[#00ffa3] border-[#00ffa3] animate-pulse' : 'bg-white/5 border-white/10'}`}>
                                    <Lock size={18} className={step === 2 ? "text-black" : "text-gray-500"} />
                                </div>
                                <div>
                                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                                        Activate VIP Access
                                        {step === 2 && <span className="text-[10px] bg-[#00ffa3] text-black px-2 py-0.5 rounded font-black uppercase">RECOMMENDED</span>}
                                    </h3>
                                    <p className="text-gray-500 text-xs mt-1">Unlock real-time institutional signals & AI auto-trading.</p>
                                </div>
                            </div>
                            {step === 2 && <ArrowRight className="text-[#00ffa3]" />}
                        </div>
                    </div>

                    {/* STEP 3: LIVE SYSTEM */}
                    <div className={`
                        p-6 rounded-3xl border transition-all duration-500
                        ${step === 3 ? 'bg-white/[0.03]' : 'bg-transparent border-white/5 opacity-50'}
                    `}>
                        <div className="flex items-center gap-4">
                            <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center border border-white/10">
                                <Zap size={20} className="text-gray-500" />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-gray-500">Live Trading</h3>
                                <p className="text-gray-600 text-xs mt-1">Waiting for activation...</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="mt-12 flex justify-center">
                    <button
                        onClick={() => router.push('/dashboard')}
                        className="px-8 py-4 bg-[#00ffa3] text-black font-black tracking-wider rounded-xl hover:bg-[#00ce82] transition-colors shadow-[0_0_20px_rgba(0,255,163,0.4)] flex items-center gap-3"
                    >
                        ENTER TERMINAL
                        <ArrowRight size={18} />
                    </button>
                </div>

            </div>
        </div>
    );
}
