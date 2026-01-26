
import React from 'react';
import { ArrowUpRight, ArrowDownRight, Activity, Brain, BarChart2 } from 'lucide-react';

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

    // V2300: VISUAL COMPLIANCE
    // Labels must match screenshot EXACTLY: "VOL PRESSURE", "ATR RISK", "TREND STATUS", "TARGET STOP", "TARGET PROFIT".
    // AI Button: Hidden by default, appears as Overlay on Hover to preserve "Clean Design".

    const isBuy = signal_type.includes('BUY');
    const isSell = signal_type.includes('SELL');

    const coin = symbol.split('/')[0];
    const logoUrl = `https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/${coin.toLowerCase()}.png`;

    let borderColor = 'border-white/5';
    let textColor = 'text-gray-400';
    let actionText = 'WAITING';

    // Matching the glowing text logic
    if (isBuy) {
        borderColor = 'border-[#00ffa3]/30';
        textColor = 'text-[#00ffa3]';
        actionText = 'LONG';
    } else if (isSell) {
        borderColor = 'border-[#ff4d4d]/30';
        textColor = 'text-[#ff4d4d]';
        actionText = 'SHORT';
    }

    const formatPrice = (p: number | undefined) =>
        p ? `$${Number(p).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '---';

    return (
        <div
            onClick={() => compact && onViewChart && onViewChart(symbol)}
            className={`
                relative overflow-hidden group transition-all duration-300
                ${compact
                    ? `p-4 mb-3 cursor-pointer bg-[#0a0a0c] border ${borderColor} rounded-2xl hover:bg-white/[0.02] active:scale-[0.98]`
                    : 'p-0 backdrop-blur-xl bg-[#0a0a0c]/80 border border-white/5 rounded-3xl hover:border-white/10 shadow-2xl'}
                bg-gradient-to-br from-white/[0.02] to-transparent
            `}
        >
            {/* === HOVER OVERLAY: AI ACTION (Hidden by default, visible on hover) === */}
            {onConsultAI && (
                <div className="absolute inset-0 z-20 bg-black/60 backdrop-blur-[2px] opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col items-center justify-center gap-3 pointer-events-none group-hover:pointer-events-auto">
                    <button
                        onClick={(e) => { e.stopPropagation(); onConsultAI({ symbol, price, confidence, signal_type, rsi, stop_loss, take_profit }); }}
                        className="px-6 py-2 rounded-xl bg-[#7c3aed] text-white font-bold tracking-wider shadow-[0_0_20px_rgba(124,58,237,0.5)] hover:scale-105 transition-transform flex items-center gap-2"
                    >
                        <Brain size={18} />
                        CONSULT AI
                    </button>
                    {!compact && (
                        <button
                            onClick={(e) => { e.stopPropagation(); onViewChart && onViewChart(symbol); }}
                            className="px-6 py-2 rounded-xl bg-white/10 text-white font-bold tracking-wider hover:bg-white/20 transition-colors"
                        >
                            VIEW CHART
                        </button>
                    )}
                </div>
            )}

            {/* === 1. HEADER ROW === */}
            <div className={`${compact ? 'flex justify-between items-start mb-3' : 'p-6 pb-2 flex justify-between items-start'}`}>

                {/* Left: Icon & Info */}
                <div className="flex items-center gap-4">
                    {/* Icon */}
                    <div className={`relative ${compact ? 'w-10 h-10' : 'w-12 h-12'} rounded-full bg-white/5 flex items-center justify-center p-1 overflow-hidden border border-white/10`}>
                        <img src={logoUrl} alt={coin} className="w-full h-full object-contain"
                            onError={(e) => { (e.target as HTMLElement).style.display = 'none'; }}
                        />
                        {/* Status Dot */}
                        <div className={`absolute top-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-[#0a0a0c] ${isBuy ? 'bg-[#00ffa3]' : 'bg-[#ff4d4d]'}`}></div>
                    </div>

                    {/* Text */}
                    <div>
                        <div className="flex items-center gap-2">
                            <h3 className={`${compact ? 'text-sm' : 'text-lg'} font-bold font-sans text-white leading-none`}>{symbol}</h3>
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                            <span className={`text-[10px] font-black uppercase tracking-wider ${textColor}`}>{actionText}</span>
                            <span className="text-[10px] text-gray-500 font-mono flex items-center gap-1">
                                {confidence}% Conf.
                            </span>
                        </div>
                    </div>
                </div>

                {/* Right: Price */}
                <div className="text-right">
                    <p className={`${compact ? 'text-lg' : 'text-xl'} font-mono font-bold text-white tracking-tighter`}>{formatPrice(price)}</p>
                    <div className="flex items-center justify-end gap-1">
                        {/* RSI Small */}
                        <span className="text-[9px] text-gray-500 font-mono">RSI: <span className={rsi > 70 || rsi < 30 ? 'text-white font-bold' : ''}>{rsi.toFixed(1)}</span></span>
                    </div>
                </div>
            </div>

            {/* === 2. METRICS ROW (Exact Labels) === */}
            <div className={`${compact ? 'px-0 py-2' : 'px-6 py-4'}`}>
                <div className="bg-white/[0.02] border border-white/5 rounded-xl p-3 flex items-center justify-between">
                    <div className="space-y-0.5">
                        <p className="text-[8px] text-gray-500 uppercase font-bold tracking-widest">VOL PRESSURE</p>
                        <p className="text-[10px] font-medium text-gray-300">{(volume_ratio || 0).toFixed(2)}x</p>
                    </div>
                    <div className="h-5 w-px bg-white/5"></div>
                    <div className="space-y-0.5">
                        <p className="text-[8px] text-gray-500 uppercase font-bold tracking-widest">ATR RISK</p>
                        <p className="text-[10px] font-medium text-gray-300">{(atr_value || 0).toFixed(2)}</p>
                    </div>
                    <div className="h-5 w-px bg-white/5"></div>
                    <div className="space-y-0.5 text-right">
                        <p className="text-[8px] text-gray-500 uppercase font-bold tracking-widest">TREND STATUS</p>
                        <div className="flex items-center justify-end gap-1">
                            <div className={`w-2 h-2 rounded-full ${confidence > 75 ? 'bg-[#00ffa3] shadow-[0_0_5px_#00ffa3]' : 'bg-gray-600'}`}></div>
                            <span className="text-[10px] font-bold text-white">{confidence > 75 ? 'STRONG' : 'WEAK'}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* === 3. TARGETS ROW (Exact Labels) === */}
            <div className={`${compact ? 'pt-1 pb-1 grid grid-cols-2 gap-4' : 'px-6 pb-6 grid grid-cols-2 gap-8'}`}>
                <div>
                    <p className="text-[8px] uppercase tracking-widest text-gray-500 font-bold mb-1">TARGET STOP</p>
                    <p className={`${compact ? 'text-sm' : 'text-base'} font-mono text-gray-400 font-bold`}>{formatPrice(stop_loss)}</p>
                </div>
                <div className="text-right">
                    <p className="text-[8px] uppercase tracking-widest text-[#00ffa3] font-bold mb-1">TARGET PROFIT</p>
                    <p className={`${compact ? 'text-sm' : 'text-base'} font-mono text-white font-bold`}>{formatPrice(take_profit)}</p>
                </div>
            </div>

            {/* No VISIBLE Footer in Default State - Matches Screenshot */}
        </div>
    );
};

export default SignalCard;
