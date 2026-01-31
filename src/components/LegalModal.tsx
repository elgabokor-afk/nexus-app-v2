
'use client';

import { X, Shield, FileText } from 'lucide-react';
import { LEGAL_TEXT } from '@/config/legal_text';

interface LegalModalProps {
    isOpen: boolean;
    onClose: () => void;
    type: 'terms' | 'privacy' | 'risk';
}

export default function LegalModal({ isOpen, onClose, type }: LegalModalProps) {
    if (!isOpen) return null;

    const content = {
        terms: { title: 'Términos de Servicio', text: LEGAL_TEXT.TERMS_AND_CONDITIONS, icon: FileText },
        privacy: { title: 'Política de Privacidad', text: LEGAL_TEXT.PRIVACY_POLICY, icon: Shield },
        risk: { title: 'Aviso de Riesgo', text: LEGAL_TEXT.RISK_DISCLAIMER, icon: Shield },
    }[type];

    const Icon = content.icon;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-300">
            <div className="bg-[#0a0a0c] border border-white/10 rounded-3xl max-w-2xl w-full shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">

                {/* Header */}
                <div className="p-6 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-[#00ffa3]/10 flex items-center justify-center">
                            <Icon className="text-[#00ffa3]" size={20} />
                        </div>
                        <h2 className="text-lg font-bold text-white">{content.title}</h2>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-full transition-colors text-gray-500 hover:text-white">
                        <X size={20} />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 overflow-y-auto custom-scrollbar">
                    <div
                        className="text-sm text-gray-400 font-mono leading-relaxed space-y-4"
                        dangerouslySetInnerHTML={{
                            __html: content.text
                                .replace(/\n/g, '<br/>')
                                .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white">$1</strong>')
                                .replace(/### (.*?)$/gm, '<h3 class="text-[#00ffa3] font-bold text-lg mt-4 mb-2">$1</h3>')
                        }}
                    />
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-white/5 bg-white/[0.02] flex justify-end">
                    <button
                        onClick={onClose}
                        className="px-6 py-2 bg-white/5 hover:bg-white/10 text-white text-xs font-bold rounded-xl transition-colors uppercase tracking-widest"
                    >
                        Cerrar Ventana
                    </button>
                </div>
            </div>
        </div>
    );
}
