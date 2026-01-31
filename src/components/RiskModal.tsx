
'use client';

import { useState, useEffect } from 'react';
import { AlertTriangle, ShieldCheck, X } from 'lucide-react';
import { LEGAL_TEXT } from '@/config/legal_text';

export default function RiskModal() {
    const [isOpen, setIsOpen] = useState(false);

    useEffect(() => {
        // Check if user has already accepted the risk warning
        const hasAccepted = localStorage.getItem('NEXUS_RISK_ACCEPTED_V1');
        if (!hasAccepted) {
            setIsOpen(true);
        }
    }, []);

    const handleAccept = () => {
        localStorage.setItem('NEXUS_RISK_ACCEPTED_V1', 'true');
        setIsOpen(false);
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-300">
            <div className="bg-[#0a0a0c] border border-red-500/30 rounded-3xl max-w-lg w-full shadow-[0_0_50px_rgba(255,0,0,0.1)] overflow-hidden flex flex-col max-h-[80vh]">

                {/* Header */}
                <div className="p-6 bg-red-500/10 border-b border-red-500/20 flex items-center gap-4">
                    <div className="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center shrink-0">
                        <AlertTriangle className="text-red-500 animate-pulse" size={24} />
                    </div>
                    <div>
                        <h2 className="text-lg font-black text-white tracking-tight uppercase">Aviso de Alto Riesgo</h2>
                        <p className="text-xs text-red-400 font-bold">Lectura Obligatoria antes de continuar</p>
                    </div>
                </div>

                {/* Content */}
                <div className="p-6 overflow-y-auto custom-scrollbar space-y-4 text-sm text-gray-300 leading-relaxed font-mono">
                    <div dangerouslySetInnerHTML={{ __html: LEGAL_TEXT.RISK_DISCLAIMER.replace(/\n/g, '<br/>').replace(/\*\*(.*?)\*\*/g, '<strong class="text-white">$1</strong>') }} />

                    <div className="h-px bg-white/10 my-4" />

                    <div dangerouslySetInnerHTML={{ __html: LEGAL_TEXT.AI_DISCLAIMER.replace(/\n/g, '<br/>').replace(/\*\*(.*?)\*\*/g, '<strong class="text-white">$1</strong>') }} />
                </div>

                {/* Footer */}
                <div className="p-6 border-t border-white/5 bg-white/[0.02]">
                    <button
                        onClick={handleAccept}
                        className="w-full bg-red-600 hover:bg-red-500 text-white font-black py-4 rounded-xl flex items-center justify-center gap-2 transition-all shadow-[0_0_20px_rgba(220,38,38,0.4)] hover:shadow-[0_0_30px_rgba(220,38,38,0.6)] uppercase tracking-wider text-xs"
                    >
                        <ShieldCheck size={16} />
                        He leído, entiendo y acepto los riesgos
                    </button>
                    <p className="text-center text-[9px] text-gray-600 mt-3 font-bold uppercase tracking-widest">
                        Nexus Crypto Signals • Software Educativo
                    </p>
                </div>
            </div>
        </div>
    );
}
