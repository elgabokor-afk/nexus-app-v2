
import React, { useState } from 'react';
import { ArrowUpRight, ArrowDownRight, Activity, Brain, BarChart2, Flame, Lock, Copy, Check, Bot, ExternalLink } from 'lucide-react';
import { useProfile } from '@/hooks/useProfile';

interface SignalProps {
    symbol: string;
    price: number;
    rsi: number;
    signal_type: string;
    confidence: number;
    timestamp: string;
    stop_loss?: number;
    take_profit?: number;
    atr_value?: number;
    volume_ratio?: number;
    imbalance?: number;
    depth_score?: number;
    // V2700: AUDIT ALERT (AI Live Changes)
    audit_alert?: string; // 'TAKE_PROFIT_TIGHTEN', 'RISK_FREE', 'WARNING'
    onViewChart?: (symbol: string) => void;
    onConsultAI?: (signal: any) => void;
}

const SignalCard: React.FC<SignalProps & { compact?: boolean }> = ({
    symbol, price, rsi, signal_type, confidence, timestamp, stop_loss, take_profit, atr_value, volume_ratio, imbalance, depth_score, audit_alert, onViewChart, onConsultAI, compact = false
}) => {

    // V2400: VISUAL REPLICATION + HOT ZONE
    // V1800: PAYWALL & VIP LOGIC
    const { isVip, loading: profileLoading } = useProfile();
    const [showPaymentModal, setShowPaymentModal] = useState(false);

    // VIP Signal Detection (Confidence >= 80)
    const isVipSignal = confidence >= 80;
    const isLocked = !isVip && isVipSignal && !profileLoading;

    const isBuy = signal_type.includes('BUY');
    const isSell = signal_type.includes('SELL');
    const isHot = confidence >= 80;
    const isAuditing = !!audit_alert; // True if AI just updated this

    const coin = symbol ? symbol.split('/')[0] : 'BTC';
    const logoUrl = coin ? `https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/${coin.toLowerCase()}.png` : '';

    let borderColor = 'border-white/5';
    let textColor = 'text-white'; // Default to white
    let actionText = 'WAITING';
    let glowClass = '';

    if (isBuy) {
        textColor = 'text-[#00ffa3]';
        borderColor = 'border-[#00ffa3]/20';
        actionText = 'LONG';
        if (isHot) glowClass = 'shadow-[0_0_30px_-10px_rgba(0,255,163,0.3)] border-[#00ffa3]/50';
    } else if (isSell) {
        textColor = 'text-[#ff4d4d]';
        borderColor = 'border-[#ff4d4d]/20';
        actionText = 'SHORT';
        if (isHot) glowClass = 'shadow-[0_0_30px_-10px_rgba(255,77,77,0.3)] border-[#ff4d4d]/50';
    }

    // V2700: Audit Flash Effect
    if (isAuditing) {
        glowClass = 'animate-pulse border-blue-500/50 shadow-[0_0_30px_-5px_rgba(59,130,246,0.5)]';
        if (audit_alert === 'RISK_FREE') borderColor = 'border-green-500';
        if (audit_alert === 'WARNING') borderColor = 'border-orange-500';
    }

    const formatPrice = (p: number | undefined) =>
        p ? `$${Number(p).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '---';

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
                        <h3 className="text-xl font-black text-white mb-2 uppercase tracking-wide">Unlock VIP Signals</h3>
                        <p className="text-gray-400 text-xs mb-6 leading-relaxed">
                            Get instant access to high-precision signals (80%+ win rate), deep AI analytics, and ad-free experience.
                        </p>

                        <div className="w-full bg-black/40 border border-white/5 rounded-xl p-3 mb-4">
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

                        <div className="w-full">
                            <label className="text-[10px] text-gray-500 uppercase font-bold mb-1 block text-left">Verify Transaction (TXID)</label>
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    placeholder="Paste TXID here..."
                                    className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[#00ffa3]/50"
                                />
                                <button className="px-3 py-2 bg-[#00ffa3] text-black text-xs font-bold rounded-lg hover:bg-[#00ffa3]/90 transition-colors">
                                    Check
                                </button>
                            </div>
                            <p className="text-[9px] text-gray-600 mt-2 text-left">
                                *System automatically scans for incoming payments every 30s. Manual check is optional.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    return (
        <>
            {showPaymentModal && <PaymentModal />}

            <div
                onClick={() => {
                    if (isLocked) {
                        setShowPaymentModal(true);
                    } else if (onViewChart) {
                        onViewChart(symbol);
                    }
                }}
                className={`
                relative overflow-hidden group transition-all duration-300
                ${compact
                        ? `mb-3 cursor-pointer bg-[#0e0e10] border ${borderColor} rounded-2xl hover:bg-white/[0.02] active:scale-[0.98]`
                        : `backdrop-blur-xl bg-[#0e0e10]/90 border ${borderColor} rounded-3xl hover:border-white/10 shadow-2xl`}
                ${isHot ? glowClass : ''}
                ${isAuditing ? glowClass : ''} 
            `}
            >
                {/* === HOVER OVERLAY: AI ACTION (View Internal Chart) === */}
                {/* Removed external link. Touching card now updates main chart via onSelectSymbol/onViewChart */}

                {/* === HOT ZONE HEADER (Only for Elite Signals) === */}
                {isHot && !isAuditing && (
                    <div className={`
                    w-full py-1.5 px-4 flex items-center gap-2 
                    bg-gradient-to-r from-red-500/10 to-transparent border-b border-red-500/10
                `}>
                        <Flame size={12} className="text-orange-500 fill-orange-500" />
                        <span className="text-[9px] font-black uppercase tracking-[0.15em] text-orange-400">HOT ZONE - ELITE SIGNALS</span>
                    </div>
                )}

                {/* === AI AUDIT HEADER (Overrides HOT) === */}
                {isAuditing && (
                    <div className={`
                    w-full py-1.5 px-4 flex items-center gap-2 
                    bg-gradient-to-r from-blue-500/10 to-transparent border-b border-blue-500/10
                    animate-pulse
                `}>
                        <Brain size={12} className="text-blue-500 fill-blue-500/50" />
                        <span className="text-[9px] font-black uppercase tracking-[0.15em] text-blue-400">
                            {audit_alert === 'RISK_FREE' ? 'AI: SECURING PROFIT' : 'AI AUDITING LIVE'}
                        </span>
                    </div>
                )}

                {/* === MAIN CONTENT === */}
                <div className={`${compact ? 'p-4' : 'p-6'}`}>

                    {/* HEADLINE: Symbol & Status */}
                    <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-white/5 p-1">
                                <img src={logoUrl} alt={coin} className="w-full h-full object-contain opacity-80" />
                            </div>
                            <div>
                                <h3 className="text-sm font-bold text-white leading-none">{symbol}</h3>
                                <p className="text-[9px] text-gray-500 font-mono mt-0.5">{new Date(timestamp).toLocaleTimeString()}</p>
                            </div>
                        </div>
                        {isLocked && <Lock size={14} className="text-[#00ffa3] animate-pulse" />}
                    </div>

                    {/* === METRICS GRID === */}
                    <div className="grid grid-cols-2 gap-4 mt-2 mb-4">
                        {/* CONFIDENCE */}
                        <div className="bg-black/40 rounded-2xl p-3 border border-white/5">
                            <div className="flex items-center gap-2 mb-1">
                                <Brain size={12} className="text-[#7c3aed]" />
                                <span className="text-[9px] font-black text-gray-500 uppercase">AI Confidence</span>
                            </div>
                            <div className="text-lg font-black text-white">{confidence}%</div>
                            <div className="w-full bg-gray-800 h-1 rounded-full mt-2 overflow-hidden">
                                <div className="h-full bg-[#7c3aed]" style={{ width: `${confidence}%` }}></div>
                            </div>
                        </div>

                        {/* RISK/REWARD */}
                        <div className="bg-black/40 rounded-2xl p-3 border border-white/5 relative overflow-hidden">
                            {isLocked && (
                                <div className="absolute inset-0 bg-black/60 backdrop-blur-[2px] z-10 flex items-center justify-center cursor-pointer" onClick={() => setShowPaymentModal(true)}>
                                    <Lock size={14} className="text-gray-500" />
                                </div>
                            )}
                            <div className="flex items-center gap-2 mb-1">
                                <Activity size={12} className="text-blue-500" />
                                <span className="text-[9px] font-black text-gray-500 uppercase">Risk : Reward</span>
                            </div>
                            <div className="text-lg font-black text-white">1 : 2.0</div>
                            <div className="text-[9px] text-gray-500 mt-1">Strict Institutional Ratio</div>
                        </div>
                    </div>

                    {/* === PRICES ROW === */}
                    <div className="grid grid-cols-3 gap-2 bg-black/40 rounded-2xl p-3 border border-white/5 relative overflow-hidden group/prices">

                        {/* PAYWALL OVERLAY FOR PRICES */}
                        {isLocked && (
                            <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-black/40 backdrop-blur-md transition-all group-hover/prices:bg-black/50 cursor-pointer" onClick={() => setShowPaymentModal(true)}>
                                <div className="flex items-center gap-2 px-3 py-1.5 bg-[#00ffa3] rounded-full shadow-[0_0_15px_rgba(0,255,163,0.4)] mb-1">
                                    <Lock size={10} className="text-black" />
                                    <span className="text-[9px] font-black text-black uppercase tracking-widest leading-none">HIGH CONFIDENCE (85%+)</span>
                                </div>
                                <p className="text-[9px] text-gray-300 font-medium mt-1 text-center px-4">
                                    Desbloquea para ver TP/SL <br />
                                    <span className="text-[#00ffa3] underline">Click to Upgrade</span>
                                </p>
                            </div>
                        )}

                        {/* ENTRY */}
                        <div className={`flex flex-col ${isLocked ? 'blur-sm opacity-50' : ''}`}>
                            <span className="text-[9px] font-black text-gray-500 uppercase mb-1">Entry Zone</span>
                            <span className="text-sm font-bold text-white font-mono">{formatPrice(price)}</span>
                        </div>

                        {/* TP */}
                        <div className={`flex flex-col ${isLocked ? 'blur-sm opacity-50' : ''}`}>
                            <span className="text-[9px] font-black text-[#00ffa3] uppercase mb-1">Take Profit</span>
                            <span className="text-sm font-bold text-[#00ffa3] font-mono">{formatPrice(take_profit)}</span>
                        </div>

                        {/* SL */}
                        <div className={`flex flex-col ${isLocked ? 'blur-sm opacity-50' : ''}`}>
                            <span className="text-[9px] font-black text-[#ff4d4d] uppercase mb-1">Stop Loss</span>
                            <span className="text-sm font-bold text-[#ff4d4d] font-mono">{formatPrice(stop_loss)}</span>
                        </div>
                    </div>

                    {/* FOOTER */}
                    <div className="mt-4 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <span className={`text-[9px] font-bold px-2 py-0.5 rounded-md border ${isBuy ? 'bg-[#00ffa3]/10 border-[#00ffa3]/20 text-[#00ffa3]' : 'bg-[#ff4d4d]/10 border-[#ff4d4d]/20 text-[#ff4d4d]'}`}>
                                {actionText}
                            </span>
                        </div>

                        {!compact && (
                            <div className="flex items-center gap-2">
                                <span className="text-[9px] text-gray-600 font-mono uppercase tracking-wider">Vol Ratio</span>
                                <span className="text-[10px] font-bold text-white">{volume_ratio?.toFixed(2) || '1.24'}x</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </>
    );
};

export default SignalCard;
