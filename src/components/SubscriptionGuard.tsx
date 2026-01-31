'use client';

import { ReactNode, useState } from 'react';
import { useProfile } from '@/hooks/useProfile';
import { Lock, Copy, Check } from 'lucide-react';

interface SubscriptionGuardProps {
    children: ReactNode;
    fallback?: ReactNode;
}

export default function SubscriptionGuard({ children, fallback }: SubscriptionGuardProps) {
    const { isVip, loading } = useProfile();
    const [showPaymentModal, setShowPaymentModal] = useState(false);

    if (loading) return <div className="animate-pulse bg-white/5 h-32 rounded-xl w-full"></div>;

    // Payment Modal Component
    const PaymentModal = () => {
        const [copied, setCopied] = useState(false);
        const wallet = "TC3zTgbRdAXKvy9sikUTeKdAr1bmsqR5p7"; // User provided TRC20

        const copyToClipboard = (e: React.MouseEvent) => {
            e.stopPropagation();
            navigator.clipboard.writeText(wallet);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        };

        return (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in">
                <div
                    onClick={(e) => e.stopPropagation()}
                    className="bg-[#0e0e10] border border-[#00ffa3]/30 rounded-3xl p-6 max-w-sm w-full shadow-[0_0_50px_rgba(0,255,163,0.1)] relative overflow-hidden"
                >
                    <div className="absolute top-0 right-0 p-4">
                        <button onClick={(e) => { e.stopPropagation(); setShowPaymentModal(false); }} className="text-gray-500 hover:text-white transition-colors">✕</button>
                    </div>

                    <div className="flex flex-col items-center text-center">
                        <div className="w-12 h-12 bg-[#00ffa3]/10 rounded-full flex items-center justify-center mb-4">
                            <Lock className="text-[#00ffa3] w-6 h-6" />
                        </div>
                        <h3 className="text-xl font-black text-white mb-2 uppercase tracking-wide">Unlock VIP Analytics</h3>
                        <p className="text-gray-400 text-xs mb-6 leading-relaxed">
                            Access real-time performance stats, win-rates, and institutional-grade portfolio tracking.
                        </p>

                        <div className="w-full bg-black/40 border border-white/5 rounded-xl p-3 mb-6">
                            <p className="text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-2 text-left">USDT (TRC20) Deposit Address</p>
                            <div className="flex items-center justify-between gap-2">
                                <code className="text-[#00ffa3] text-xs font-mono break-all text-left">{wallet}</code>
                                <button
                                    onClick={copyToClipboard}
                                    className="p-2 hover:bg-white/10 rounded-lg transition-colors group/copy"
                                >
                                    {copied ? <Check size={14} className="text-[#00ffa3]" /> : <Copy size={14} className="text-gray-400 group-hover/copy:text-white" />}
                                </button>
                            </div>
                        </div>

                        <div className="w-full p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl mb-4">
                            <p className="text-[10px] text-blue-300">
                                <strong>Auto-Activation:</strong> Send payment and contact support with your TXID.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    if (!isVip) {
        return (
            <>
                {showPaymentModal && <PaymentModal />}
                {fallback || (
                    <div className="relative w-full h-full min-h-[200px] flex flex-col items-center justify-center bg-black/40 border border-white/5 rounded-2xl overflow-hidden group">
                        {/* Background Blur */}
                        <div className="absolute inset-0 bg-[#00ffa3]/5 blur-xl group-hover:bg-[#00ffa3]/10 transition-all"></div>

                        <Lock className="text-[#00ffa3] mb-4 w-8 h-8" />
                        <h3 className="text-white font-black text-xl mb-2">VIP ACCESS ONLY</h3>
                        <p className="text-gray-400 text-xs text-center max-w-[200px] mb-6">
                            Unlock professional-grade analytics and high-precision signals.
                        </p>

                        <button
                            onClick={() => setShowPaymentModal(true)}
                            className="px-6 py-2 bg-[#00ffa3] text-black font-black text-xs uppercase tracking-widest rounded-full hover:scale-105 transition-transform"
                        >
                            Upgrade to VIP
                        </button>
                    </div>
                )}
            </>
        );
    }

    return <>{children}</>;
}
