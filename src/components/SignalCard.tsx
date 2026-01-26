
import React from 'react';
import { ArrowUpRight, ArrowDownRight, Activity, Brain, BarChart2, Flame } from 'lucide-react';

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
    onViewChart?: (symbol: string) => void;
    onConsultAI?: (signal: any) => void;
}

const SignalCard: React.FC<SignalProps & { compact?: boolean }> = ({
    symbol, price, rsi, signal_type, confidence, timestamp, stop_loss, take_profit, atr_value, volume_ratio, imbalance, depth_score, onViewChart, onConsultAI, compact = false
}) => {

    // V2400: VISUAL REPLICATION + HOT ZONE
    // 1. "Hot Zone": If confidence > 90, show the Red Flame Header.
    // 2. "Strict Params": Ensure Vol, ATR, Trend, Stop, Profit are visible exactly as in screenshot.
    // 3. Colors: Darker backgrounds, high contrast text.

    const isBuy = signal_type.includes('BUY');
    const isSell = signal_type.includes('SELL');
    const isHot = confidence >= 90;

    const coin = symbol.split('/')[0];
    const logoUrl = `https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/${coin.toLowerCase()}.png`;

    let borderColor = 'border-white/5';
    let textColor = 'text-gray-400';
    let actionText = 'WAITING';
    let glowClass = '';

    if (isBuy) {
        textColor = 'text-[#00ffa3]';
        actionText = 'LONG';
        if (isHot) glowClass = 'shadow-[0_0_30px_-10px_rgba(0,255,163,0.3)] border-[#00ffa3]/30';
    } else if (isSell) {
        textColor = 'text-[#ff4d4d]';
        actionText = 'SHORT';
        if (isHot) glowClass = 'shadow-[0_0_30px_-10px_rgba(255,77,77,0.3)] border-[#ff4d4d]/30';
    }

    const formatPrice = (p: number | undefined) =>
        p ? `$${Number(p).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '---';

    return (
        <div
            onClick={() => compact && onViewChart && onViewChart(symbol)}
            className={`
                relative overflow-hidden group transition-all duration-300
                ${compact
                    ? `mb-3 cursor-pointer bg-[#0e0e10] border border-white/5 rounded-2xl hover:bg-white/[0.02] active:scale-[0.98]`
                    : 'backdrop-blur-xl bg-[#0e0e10]/90 border border-white/5 rounded-3xl hover:border-white/10 shadow-2xl'}
                ${isHot ? glowClass : ''}
            `}
        >
            {/* === HOVER OVERLAY: AI ACTION === */}
            {onConsultAI && (
                <div className="absolute inset-0 z-30 bg-black/80 backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex flex-col items-center justify-center gap-3 pointer-events-none group-hover:pointer-events-auto">
                    <button
                        onClick={(e) => { e.stopPropagation(); onConsultAI({ symbol, price, confidence, signal_type, rsi, stop_loss, take_profit }); }}
                        className="px-5 py-2 rounded-lg bg-[#7c3aed] text-white font-black uppercase tracking-wider text-xs shadow-lg hover:bg-[#6d28d9] transition-transform hover:scale-105 flex items-center gap-2"
                    >
                        <Brain size={16} />
                        Consult Nexus
                    </button>
                    {!compact && (
                        <button
                            onClick={(e) => { e.stopPropagation(); onViewChart && onViewChart(symbol); }}
                            className="px-5 py-2 rounded-lg bg-white/10 text-white font-black uppercase tracking-wider text-xs hover:bg-white/20 transition-colors"
                        >
                            Open Chart
                        </button>
                    )}
                </div>
            )}

            {/* === HOT ZONE HEADER (Only for Elite Signals) === */}
            {isHot && (
                <div className={`
                    w-full py-1.5 px-4 flex items-center gap-2 
                    bg-gradient-to-r from-red-500/10 to-transparent border-b border-red-500/10
                `}>
                    <Flame size={12} className="text-orange-500 fill-orange-500" />
                    <span className="text-[9px] font-black uppercase tracking-[0.15em] text-orange-400">HOT ZONE - ELITE SIGNALS</span>
                </div>
            )}

            {/* === CARD CONTENT === */}
            <div className={`${compact ? 'p-4' : 'p-6'}`}>

                {/* 1. HEADER: Icon | Symbol | Status | Price */}
                <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center gap-3">
                        {/* Icon Box */}
                        <div className="w-10 h-10 rounded-full bg-[#18181b] flex items-center justify-center p-1.5 border border-white/5 relative">
                            <img src={logoUrl} alt={coin} className="w-full h-full object-contain" onError={(e) => { (e.target as HTMLElement).style.display = 'none'; }} />
                            {/* Status Indicator Dot */}
                            <div className={`absolute -top-0.5 -right-0.5 w-3 h-3 rounded-full border-[3px] border-[#0e0e10] ${isBuy ? 'bg-[#00ffa3]' : 'bg-[#ff4d4d]'}`}></div>
                        </div>

                        {/* Symbol Name & Signal */}
                        <div>
                            <h3 className="text-base font-bold text-white leading-none mb-1">{symbol}</h3>
                            <div className="flex items-center gap-2">
                                <span className={`text-[10px] font-black uppercase ${textColor}`}>{actionText}</span>
                                <div className="h-3 w-px bg-white/10"></div>
                                <span className="text-[9px] font-bold text-gray-500">{confidence}% Conf</span>
                            </div>
                        </div>
                    </div>

                    {/* Price & RSI */}
                    <div className="text-right">
                        <p className="text-base font-mono font-bold text-white mb-0.5">{formatPrice(price)}</p>
                        <p className="text-[9px] text-gray-500 font-mono">RSI: <span className={rsi > 70 || rsi < 30 ? 'text-white' : ''}>{rsi.toFixed(1)}</span></p>
                    </div>
                </div>

                {/* 2. METRICS ROW: Vol | ATR | Trend */}
                <div className="bg-[#18181b] border border-white/5 rounded-lg p-3 grid grid-cols-3 gap-2 mb-4">
                    <div>
                        <p className="text-[7px] text-gray-500 font-black uppercase tracking-wider mb-0.5">VOL PRESSURE</p>
                        <p className="text-[10px] font-bold text-gray-300">{(volume_ratio || 0).toFixed(2)}x</p>
                    </div>
                    <div className="text-center border-l border-white/5 border-r">
                        <p className="text-[7px] text-gray-500 font-black uppercase tracking-wider mb-0.5">ATR RISK</p>
                        <p className="text-[10px] font-bold text-gray-300">{(atr_value || 0).toFixed(2)}</p>
                    </div>
                    <div className="text-right">
                        <p className="text-[7px] text-gray-500 font-black uppercase tracking-wider mb-0.5">TREND STATUS</p>
                        <div className="flex items-center justify-end gap-1">
                            <span className={`text-[9px] font-black ${confidence > 75 ? 'text-[#00ffa3]' : 'text-gray-400'}`}>
                                {confidence > 75 ? 'STRONG' : 'NEUTRAL'}
                            </span>
                        </div>
                    </div>
                </div>

                {/* 3. TARGETS ROW: Stop | Profit */}
                <div className="flex justify-between items-center">
                    <div>
                        <p className="text-[8px] text-gray-600 font-black uppercase tracking-widest mb-0.5">TARGET STOP</p>
                        <p className="text-sm font-mono font-bold text-gray-400">{formatPrice(stop_loss)}</p>
                    </div>
                    <div className="text-right">
                        <p className="text-[8px] text-[#00ffa3]/80 font-black uppercase tracking-widest mb-0.5">TARGET PROFIT</p>
                        <p className="text-sm font-mono font-bold text-white">{formatPrice(take_profit)}</p>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default SignalCard;
