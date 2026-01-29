
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
    // V3200: Winner Effect
    status?: string;
    pnl?: number;
    // V3800: Real-Time Ticker
    livePrice?: number;
}

const SignalCard: React.FC<SignalProps & { compact?: boolean }> = ({
    symbol, price, rsi, signal_type, confidence, timestamp, stop_loss, take_profit, atr_value, volume_ratio, imbalance, depth_score, audit_alert, onViewChart, onConsultAI, compact = false, status, pnl, livePrice
}) => {

    // V2400: VISUAL REPLICATION + HOT ZONE
    const { isVip, loading: profileLoading } = useProfile();
    const [showPaymentModal, setShowPaymentModal] = useState(false);

    // VIP Signal Detection (Confidence >= 75)
    // Adjusted per user feedback (79% should be VIP)
    const isVipSignal = confidence >= 75;
    const isLocked = !isVip && isVipSignal && !profileLoading;

    const isBuy = signal_type.includes('BUY');
    const isSell = signal_type.includes('SELL');
    const isHot = confidence >= 75;
    const isAuditing = !!audit_alert; // True if AI just updated this

    // V2800: Robust Logo Logic (Strip '1000' prefix, etc.)
    const cleanSymbol = symbol ? symbol.split('/')[0].replace('1000', '') : 'BTC';

    // V2802: Reliable Icon Source (CoinCap Assets)
    const baseIcon = `https://assets.coincap.io/assets/icons/${cleanSymbol.toLowerCase()}@2x.png`;
    const logoUrl = baseIcon;

    // PRICES LOGIC
    // Prefer Live Price if available, else static entry
    const currentPrice = livePrice || price;
    // Calculate PnL vs Entry for Color
    const entryPrice = price;
    const pnlPct = entryPrice > 0 ? ((currentPrice - entryPrice) / entryPrice) * 100 : 0;

    // Determine color based on Direction vs Movement
    const isProfitable = (isBuy && currentPrice > entryPrice) || (isSell && currentPrice < entryPrice);
    const tickColor = isProfitable ? 'text-[#00ffa3]' : (currentPrice === entryPrice ? 'text-gray-400' : 'text-[#ff4d4d]');

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

    // V3200: WINNER EFFECT (User Request)
    // If signal closed in profit, show Gold Glow then disappear.
    const [isVisible, setIsVisible] = useState(true);
    // Check if WIN (Closed + Profit)
    const isWin = status === 'CLOSED' && (pnl || 0) > 0;

    // Auto-Disappear Logic
    React.useEffect(() => {
        if (isWin) {
            // Wait 5 seconds to show off the win, then hide
            const timer = setTimeout(() => setIsVisible(false), 5000);
            return () => clearTimeout(timer);
        }
    }, [isWin]);

    if (!isVisible) return null;

    if (isWin) {
        glowClass = 'border-yellow-500/50 shadow-[0_0_50px_-5px_rgba(234,179,8,0.6)] animate-pulse';
        borderColor = 'border-yellow-500';
    }

    const formatPrice = (p: number | undefined) =>
        p ? `$${Number(p).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })}` : '---';

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
                relative overflow-hidden group transition-all duration-200 cursor-pointer
                ${compact
                        ? `mb-2 bg-[#0a0a0c] border border-[#1d1f23] rounded-lg hover:border-[#333]`
                        : `bg-[#0a0a0c] border border-[#1d1f23] rounded-xl hover:border-[#333] shadow-sm`}
                ${isHot ? 'bg-gradient-to-br from-[#0a0a0c] to-yellow-900/10 border-yellow-500/30' : ''}
                ${isHot ? 'border-orange-900/30' : ''}
                ${isAuditing ? 'border-blue-900/30' : ''}
                ${glowClass} 
            `}
            >
                {/* === HOVER OVERLAY: AI ACTION (View Internal Chart) === */}
                {/* Removed external link. Touching card now updates main chart via onSelectSymbol/onViewChart */}

                {/* === V3200: WINNER OVERLAY === */}
                {isWin && (
                    <div className="absolute inset-x-0 top-0 bg-yellow-500/20 text-yellow-500 text-[10px] font-black uppercase tracking-widest text-center py-1 z-20 backdrop-blur-sm animate-in slide-in-from-top-2">
                        🏆 WINNER TARGET HIT
                    </div>
                )}

                {/* === VIP / HOT ZONE HEADER === */}
                {isHot && !isAuditing && !isWin && (
                    <>
                        {/* Gold Gradient Border for Premium Feel */}
                        <div className="absolute inset-0 border-2 border-yellow-500/50 rounded-xl z-20 pointer-events-none animate-pulse"></div>
                        <div className="absolute inset-x-0 top-0 bg-gradient-to-b from-yellow-500/20 to-transparent h-12 z-0 pointer-events-none"></div>

                        <div className="w-full h-1.5 bg-gradient-to-r from-yellow-600 via-yellow-400 to-yellow-600 animate-shimmer bg-[length:200%_100%]"></div>
                        <div className="absolute top-2 right-2 z-30">
                            <span className="bg-yellow-500 text-black text-[10px] font-black px-2 py-0.5 rounded shadow-[0_0_15px_rgba(234,179,8,0.8)] flex items-center gap-1">
                                <Flame size={10} fill="black" /> VIP ALPHA
                            </span>
                        </div>
                    </>
                )}

                {/* === AI AUDIT HEADER (Overrides HOT) === */}
                {isAuditing && (
                    <div className="w-full h-1 bg-blue-600/50 animate-pulse"></div>
                )}

                {/* === MAIN CONTENT === */}
                <div className={`${compact ? 'p-3' : 'p-5'}`}>

                    {/* HEADLINE: Symbol & Status */}
                    <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-[#16181c] p-0.5 border border-[#2f3336] flex items-center justify-center overflow-hidden">
                                <img src={logoUrl} alt={symbol} className="w-full h-full object-cover" />
                            </div>
                            <div className="flex flex-col">
                                <h3 className="text-sm font-black text-[#E7E9EA] leading-none tracking-tight">{symbol}</h3>
                                <div className="flex flex-col gap-0.5 mt-0.5">
                                    <div className="flex items-center gap-2">
                                        <span className="text-[9px] text-gray-500 font-bold uppercase">ENTRY</span>
                                        <span className="text-[10px] font-mono font-bold text-gray-300">{formatPrice(entryPrice)}</span>
                                    </div>
                                    {livePrice && (
                                        <div className="flex items-center gap-2">
                                            <span className="text-[9px] text-gray-500 font-bold uppercase">LIVE</span>
                                            <span className={`text-[10px] font-mono font-bold ${tickColor}`}>{formatPrice(currentPrice)}</span>
                                            <span className={`text-[8px] font-mono px-1 rounded ${isProfitable ? 'bg-[#00ffa3]/10 text-[#00ffa3]' : 'bg-red-500/10 text-red-500'}`}>
                                                {isProfitable ? '+' : ''}{isBuy ? pnlPct.toFixed(2) : (pnlPct * -1).toFixed(2)}%
                                            </span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                        {isLocked ? (
                            <Lock size={12} className="text-[#00ffa3]" />
                        ) : (
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${isBuy ? 'text-[#00ffa3] border-[#00ffa3]/20 bg-[#00ffa3]/5' : 'text-[#ff4d4d] border-[#ff4d4d]/20 bg-[#ff4d4d]/5'}`}>
                                {actionText}
                            </span>
                        )}
                    </div>

                    {/* === METRICS GRID (Expanded) === */}
                    <div className="grid grid-cols-4 gap-2 mt-3 bg-white/[0.03] p-2.5 rounded-lg border border-white/5 relative overflow-hidden">

                        {/* Decorative Gradient Background */}
                        <div className={`absolute inset-0 opacity-10 ${isBuy ? 'bg-gradient-to-br from-[#00ffa3] to-transparent' : 'bg-gradient-to-br from-[#ff4d4d] to-transparent'}`}></div>

                        {/* CONFIDENCE */}
                        <div className="flex flex-col relative z-10">
                            <span className="text-[9px] text-gray-400 font-black uppercase tracking-wider">AI Conf</span>
                            <span className={`text-sm font-black ${confidence >= 80 ? 'text-[#00ffa3] drop-shadow-[0_0_5px_rgba(0,255,163,0.5)]' : 'text-gray-200'}`}>{confidence}%</span>
                        </div>

                        {/* RSI (Fixed Precision) */}
                        <div className="flex flex-col relative z-10">
                            <span className="text-[9px] text-gray-400 font-black uppercase tracking-wider">RSI</span>
                            <span className={`text-sm font-bold ${rsi > 70 || rsi < 30 ? 'text-orange-400' : 'text-white'}`}>
                                {Math.round(rsi)} <span className="text-[9px] text-gray-500 font-normal">/ 100</span>
                            </span>
                        </div>

                        {/* SENTIMENT (New) */}
                        <div className="flex flex-col relative z-10">
                            <span className="text-[9px] text-gray-400 font-black uppercase tracking-wider">Sentiment</span>
                            <span className={`text-[10px] font-bold mt-0.5 ${isBuy ? 'text-green-400' : 'text-red-400'}`}>
                                {confidence > 85 ? 'EXTREME' : 'STRONG'}
                            </span>
                        </div>

                        {/* TIME */}
                        <div className="flex flex-col text-right relative z-10">
                            <span className="text-[9px] text-gray-400 font-black uppercase tracking-wider">Time</span>
                            <span className="text-xs font-mono text-gray-300">{new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                    </div>

                    {/* === PRICES ROW === */}
                    <div className="mt-3 pt-3 border-t border-[#1d1f23] grid grid-cols-2 gap-4">

                        <div className="flex flex-col">
                            <span className="text-[10px] text-gray-500 font-bold uppercase mb-0.5">Target</span>
                            {isLocked ? (
                                <div className="relative group/lock">
                                    <div className="h-5 w-16 bg-[#1d1f23] rounded flex items-center justify-center border border-white/5">
                                        <Lock size={10} className="text-gray-600 group-hover/lock:text-[#00ffa3] transition-colors" />
                                    </div>
                                    <div className="absolute inset-0 backdrop-blur-[2px] cursor-not-allowed"></div>
                                </div>
                            ) : (
                                <span className="text-xs font-mono font-bold text-[#00ffa3]">{formatPrice(take_profit)}</span>
                            )}
                        </div>

                        <div className="flex flex-col text-right items-end">
                            <span className="text-[10px] text-gray-500 font-bold uppercase mb-0.5">Stop</span>
                            {isLocked ? (
                                <div className="relative group/lock">
                                    <div className="h-5 w-16 bg-[#1d1f23] rounded flex items-center justify-center border border-white/5">
                                        <Lock size={10} className="text-gray-600 group-hover/lock:text-[#ff4d4d] transition-colors" />
                                    </div>
                                    <div className="absolute inset-0 backdrop-blur-[2px] cursor-not-allowed"></div>
                                </div>
                            ) : (
                                <span className="text-xs font-mono font-bold text-[#ff4d4d]">{formatPrice(stop_loss)}</span>
                            )}
                        </div>

                    </div>
                </div>
            </div>
        </>
    );
};

export default SignalCard;
