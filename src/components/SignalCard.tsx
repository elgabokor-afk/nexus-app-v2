
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

    // V2100: UNIFIED LAYOUT
    // The user wants detailed cards (Header/Metrics/Targets) even in the sidebar "Signal Pulse".
    // We removed the "Strip" specific layout. "compact" now just means "tighter padding".

    const isBuy = signal_type.includes('BUY');
    const isSell = signal_type.includes('SELL');

    const coin = symbol.split('/')[0];
    const logoUrl = `https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/${coin.toLowerCase()}.png`;

    let borderColor = 'border-white/5';
    let textColor = 'text-gray-400';
    let actionText = 'WAITING';

    // Stronger colors for the border in compact mode to pop against sidebar
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
                    ? `p-3 mb-3 cursor-pointer bg-[#0a0a0c] border ${borderColor} rounded-xl hover:bg-white/[0.02] active:scale-[0.98]`
                    : 'p-0 backdrop-blur-xl bg-[#0a0a0c]/80 border border-white/5 rounded-3xl hover:border-white/10 shadow-2xl'}
                bg-gradient-to-br from-white/[0.02] to-transparent
            `}
        >
            {/* === 1. HEADER ROW (Symbol | Confidence | Price) === */}
            <div className={`${compact ? 'flex justify-between items-start mb-2' : 'p-6 pb-2 flex justify-between items-start'}`}>
                <div className="flex items-center gap-3">
                    {/* Icon */}
                    <div className={`relative ${compact ? 'w-8 h-8' : 'w-12 h-12'} rounded-lg bg-white/5 flex items-center justify-center p-1 overflow-hidden border border-white/10`}>
                        <img src={logoUrl} alt={coin} className="w-full h-full object-contain"
                            onError={(e) => { (e.target as HTMLElement).style.display = 'none'; }}
                        />
                    </div>
                    {/* Text Info */}
                    <div>
                        <div className="flex items-center gap-2">
                            <h3 className={`${compact ? 'text-xs' : 'text-lg'} font-bold font-sans text-white leading-none`}>{symbol}</h3>
                            {/* AI Brain Button (Discreet, next to symbol) */}
                            {onConsultAI && (
                                <button
                                    onClick={(e) => { e.stopPropagation(); onConsultAI({ symbol, price, confidence, signal_type, rsi, stop_loss, take_profit }); }}
                                    className="p-1 rounded hover:bg-white/10 text-purple-400 transition-colors"
                                    title="Consult AI"
                                >
                                    <Brain size={compact ? 12 : 14} />
                                </button>
                            )}
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                            <span className={`text-[9px] font-black uppercase tracking-wider ${textColor}`}>{actionText}</span>
                            <div className="w-12 h-1 bg-white/10 rounded-full overflow-hidden">
                                <div className={`h-full ${isBuy ? 'bg-[#00ffa3]' : 'bg-[#ff4d4d]'}`} style={{ width: `${confidence}%` }}></div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Price Block */}
                <div className="text-right">
                    <p className={`${compact ? 'text-sm' : 'text-xl'} font-mono font-bold text-white tracking-tighter`}>{formatPrice(price)}</p>
                    <div className="flex items-center justify-end gap-1">
                        <span className="text-[9px] text-gray-500 font-mono">RSI {rsi.toFixed(0)}</span>
                    </div>
                </div>
            </div>

            {/* === 2. METRICS ROW (Vol | ATR | Trend) === */}
            <div className={`${compact ? 'px-1 py-2' : 'px-6 py-4'}`}>
                <div className="bg-white/[0.02] border border-white/5 rounded-lg p-2 flex items-center justify-between">
                    <div className="text-center">
                        <p className="text-[8px] text-gray-600 uppercase font-bold">Vol</p>
                        <p className="text-[9px] font-medium text-gray-300">{(volume_ratio || 0).toFixed(1)}x</p>
                    </div>
                    <div className="h-4 w-px bg-white/5"></div>
                    <div className="text-center">
                        <p className="text-[8px] text-gray-600 uppercase font-bold">Risk</p>
                        <p className="text-[9px] font-medium text-gray-300">{(atr_value || 0).toFixed(2)}</p>
                    </div>
                    <div className="h-4 w-px bg-white/5"></div>
                    <div className="text-center">
                        <p className="text-[8px] text-gray-600 uppercase font-bold">Trend</p>
                        <p className={`text-[9px] font-bold ${textColor}`}>{confidence > 75 ? 'Good' : 'Weak'}</p>
                    </div>
                </div>
            </div>

            {/* === 3. TARGETS ROW (Stop | Profit) === */}
            <div className={`${compact ? 'px-2 pb-2 grid grid-cols-2 gap-4' : 'px-6 pb-6 grid grid-cols-2 gap-8'}`}>
                <div>
                    <p className="text-[8px] uppercase tracking-widest text-gray-600 font-bold mb-0.5">Stop</p>
                    <p className={`${compact ? 'text-xs' : 'text-base'} font-mono text-gray-400 font-medium`}>{formatPrice(stop_loss)}</p>
                </div>
                <div className="text-right">
                    <p className="text-[8px] uppercase tracking-widest text-[#00ffa3]/80 font-bold mb-0.5">Target</p>
                    <p className={`${compact ? 'text-xs' : 'text-base'} font-mono text-white font-bold`}>{formatPrice(take_profit)}</p>
                </div>
            </div>

            {/* Full Mode Only: Large Action Footer (Compact hides this to save vertical space, rely on small brain button) */}
            {!compact && (
                <div className="mt-2 p-4 border-t border-white/5 bg-black/40 flex gap-2">
                    <button
                        onClick={() => onViewChart && onViewChart(symbol)}
                        className={`
                            w-full py-3 rounded-xl font-black text-[10px] tracking-[0.2em] uppercase
                            transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]
                            ${isBuy ? 'bg-[#00ffa3] text-black hover:bg-white' : 'bg-[#ff4d4d] text-white hover:bg-white hover:text-black'}
                        `}
                    >
                        Chart Analysis
                    </button>
                </div>
            )}
        </div>
    );
};

export default SignalCard;
