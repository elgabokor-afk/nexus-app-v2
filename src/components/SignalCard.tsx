
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

    // V2200: STRICT LAYOUT CONTROL
    // We are disregarding 'compact' mode's structure changes. 
    // Always render the Full detailed card.
    // Ensure AI button is FLEXbox aligned, never Absolute.

    const isBuy = signal_type.includes('BUY');
    const isSell = signal_type.includes('SELL');

    const coin = symbol.split('/')[0];
    const logoUrl = `https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/${coin.toLowerCase()}.png`;

    let borderColor = 'border-white/5';
    let textColor = 'text-gray-400';
    let actionText = 'WAITING';

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
            {/* === 1. HEADER ROW === */}
            {/* Flex Container: Left = Icon/Symbol/AI, Right = Price/RSI */}
            <div className={`${compact ? 'flex justify-between items-start mb-2' : 'p-6 pb-2 flex justify-between items-start'}`}>

                {/* Left Side Group */}
                <div className="flex items-center gap-3">
                    {/* Icon */}
                    <div className={`relative ${compact ? 'w-10 h-10' : 'w-12 h-12'} rounded-xl bg-white/5 flex items-center justify-center p-1 overflow-hidden border border-white/10`}>
                        <img src={logoUrl} alt={coin} className="w-full h-full object-contain"
                            onError={(e) => { (e.target as HTMLElement).style.display = 'none'; }}
                        />
                    </div>

                    {/* Symbol & Info */}
                    <div>
                        <div className="flex items-center gap-2">
                            {/* Symbol */}
                            <h3 className={`${compact ? 'text-sm' : 'text-lg'} font-bold font-sans text-white leading-none`}>{symbol}</h3>

                            {/* AI BUTTON (Discreet, Inline, No Overlap) */}
                            {onConsultAI && (
                                <button
                                    onClick={(e) => { e.stopPropagation(); onConsultAI({ symbol, price, confidence, signal_type, rsi, stop_loss, take_profit }); }}
                                    className="w-5 h-5 flex items-center justify-center rounded-md bg-purple-500/20 text-purple-400 hover:bg-purple-500 hover:text-white transition-colors ml-1"
                                    title="Consult AI"
                                >
                                    <Brain size={12} />
                                </button>
                            )}
                        </div>

                        {/* Status Line */}
                        <div className="flex items-center gap-2 mt-1">
                            <span className={`text-[9px] font-black uppercase tracking-wider ${textColor}`}>{actionText}</span>
                            <div className="w-12 h-1 bg-white/10 rounded-full overflow-hidden">
                                <div className={`h-full ${isBuy ? 'bg-[#00ffa3]' : 'bg-[#ff4d4d]'}`} style={{ width: `${confidence}%` }}></div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Side Group (Price) */}
                <div className="text-right pl-2">
                    <p className={`${compact ? 'text-sm' : 'text-xl'} font-mono font-bold text-white tracking-tighter`}>{formatPrice(price)}</p>
                    <div className="flex items-center justify-end gap-1">
                        <Activity size={10} className="text-gray-600" />
                        <span className="text-[9px] text-gray-500 font-mono">RSI {rsi.toFixed(0)}</span>
                    </div>
                </div>
            </div>

            {/* === 2. METRICS ROW === */}
            <div className={`${compact ? 'px-1 py-1' : 'px-6 py-4'}`}>
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

            {/* === 3. TARGETS ROW === */}
            <div className={`${compact ? 'px-2 pb-2 grid grid-cols-2 gap-4' : 'px-6 pb-6 grid grid-cols-2 gap-8'}`}>
                <div className="text-left">
                    <p className="text-[8px] uppercase tracking-widest text-gray-600 font-bold mb-0.5">Stop</p>
                    <p className={`${compact ? 'text-xs' : 'text-base'} font-mono text-gray-400 font-medium`}>{formatPrice(stop_loss)}</p>
                </div>
                <div className="text-right">
                    <p className="text-[8px] uppercase tracking-widest text-[#00ffa3]/80 font-bold mb-0.5">Target</p>
                    <p className={`${compact ? 'text-xs' : 'text-base'} font-mono text-white font-bold`}>{formatPrice(take_profit)}</p>
                </div>
            </div>

            {/* Full Mode Footer */}
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
