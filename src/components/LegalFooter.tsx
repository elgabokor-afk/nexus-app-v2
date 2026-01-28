
import { LEGAL_TEXT } from '@/config/legal_text';

export default function LegalFooter() {
    return (
        <footer className="mt-12 mb-6 border-t border-white/5 pt-8 px-6 text-center">

            {/* Critical Disclaimer */}
            <div className="max-w-4xl mx-auto mb-6 p-4 rounded-2xl bg-white/[0.02] border border-white/5">
                <p className="text-[10px] text-gray-500 font-mono leading-relaxed uppercase tracking-wide">
                    {LEGAL_TEXT.NO_ADVICE_NOTICE.replace(/\*\*/g, '')}
                </p>
            </div>

            {/* Links */}
            <div className="flex flex-wrap justify-center gap-6 text-[10px] text-gray-600 font-bold uppercase tracking-widest">
                <span className="hover:text-[#00ffa3] cursor-pointer transition-colors">Términos y Condiciones</span>
                <span>•</span>
                <span className="hover:text-[#00ffa3] cursor-pointer transition-colors">Política de Privacidad</span>
                <span>•</span>
                <span className="hover:text-[#00ffa3] cursor-pointer transition-colors">Aviso de Riesgo</span>
                <span>•</span>
                <span className="hover:text-[#00ffa3] cursor-pointer transition-colors">Política de Reembolso</span>
            </div>

            <p className="text-[9px] text-[#00ffa3]/20 font-black tracking-[0.5em] mt-8">
                NEXUS CRYPTO SIGNALS © 2026
            </p>
        </footer>
    );
}
