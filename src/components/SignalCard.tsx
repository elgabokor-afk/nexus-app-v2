import React from 'react';
import { ArrowUpRight, ArrowDownRight, Activity } from 'lucide-react';

interface SignalProps {
    symbol: string;
    price: number;
    rsi: number;
    signal_type: string;
    confidence: number;
    timestamp: string;
    stop_loss?: number;
    take_profit?: number;
    onViewChart?: (symbol: string) => void;
}

const SignalCard: React.FC<SignalProps & { compact?: boolean }> = ({
    symbol, price, rsi, signal_type, confidence, timestamp, stop_loss, take_profit, onViewChart, compact = false
}) => {
    const isBuy = signal_type.includes('BUY');
    const isSell = signal_type.includes('SELL');
    const isNeutral = !isBuy && !isSell;

    let borderColor = 'border-gray-800';
    let textColor = 'text-gray-400';
    let badgeBg = 'bg-gray-800';
    let actionText = 'WAITING';

    if (isBuy) {
        borderColor = 'border-[#00ffa3]';
        textColor = 'text-[#00ffa3]';
        badgeBg = 'bg-[#00ffa3]/10';
        actionText = 'LONG';
    } else if (isSell) {
        borderColor = 'border-[#ff4d4d]';
        textColor = 'text-[#ff4d4d]';
        badgeBg = 'bg-[#ff4d4d]/10';
        actionText = 'SHORT';
    }

    const formatPrice = (p: number | undefined) =>
        p ? `$${Number(p).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '---';

    return (
        <div
            onClick={() => compact && onViewChart && onViewChart(symbol)}
            className={`
                relative overflow-hidden group transition-all duration-300
                ${compact ? 'p-3 cursor-pointer hover:bg-white/5 border border-white/5 rounded-xl' : 'p-0 backdrop-blur-xl bg-[#0a0a0c]/80 border border-white/5 rounded-2xl hover:border-white/10 hover:shadow-2xl hover:shadow-green-500/5'}
                ${isBuy && !compact ? 'shadow-[0_0_30px_-10px_rgba(0,255,163,0.1)]' : ''}
                ${isSell && !compact ? 'shadow-[0_0_30px_-10px_rgba(255,77,77,0.1)]' : ''}
            `}
        >
            {/* Top Gradient Line */}
            {!compact && (
                <div className={`absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-${isBuy ? 'green' : isSell ? 'red' : 'gray'}-500/50 to-transparent opacity-50`}></div>
            )}

            {/* Header / Main Info */}
            <div className={`${compact ? 'flex justify-between items-center' : 'p-5 flex justify-between items-start'}`}>
                <div className="flex items-center gap-3">
                    <div className={`
                        flex items-center justify-center rounded-full font-bold text-black
                        ${compact ? 'w-7 h-7 text-[10px]' : 'w-10 h-10 text-sm'}
                        ${isBuy ? 'bg-gradient-to-br from-[#00ffa3] to-[#00ce82]' : isSell ? 'bg-gradient-to-br from-[#ff4d4d] to-[#cc0000]' : 'bg-gray-700'}
                    `}>
                        {symbol.substring(0, 1)}
                    </div>

                    <div>
                        <div className="flex items-center gap-2">
                            <h3 className={`${compact ? 'text-xs' : 'text-lg'} font-bold font-sans text-white tracking-tight`}>{symbol}</h3>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className={`text-[9px] font-bold tracking-wider uppercase ${textColor}`}>
                                {compact ? actionText : signal_type.replace(/_/g, ' ')}
                            </span>
                        </div>
                    </div>
                </div>

                <div className="text-right">
                    <p className={`${compact ? 'text-xs' : 'text-xl'} font-mono font-medium text-white`}>
                        {formatPrice(price)}
                    </p>
                    {!compact && (
                        <div className="flex items-center justify-end gap-1.5 mt-1">
                            <Activity size={12} className={rsi < 30 || rsi > 70 ? textColor : 'text-gray-600'} />
                            <span className={`text-xs font-mono ${rsi < 30 || rsi > 70 ? 'text-white' : 'text-gray-500'}`}>RSI {rsi}</span>
                        </div>
                    )}
                </div>
            </div>

            {/* Metrics Row (Now adapted for both modes) */}
            {!isNeutral && (
                <div className={`
                    ${compact ? 'mt-2 pt-2 border-t border-white/5 grid grid-cols-2 gap-2' : 'px-5 py-4 grid grid-cols-2 gap-4 border-t border-white/5 bg-black/20'}
                `}>
                    <div className="space-y-0.5">
                        <p className={`${compact ? 'text-[8px]' : 'text-[10px]'} uppercase tracking-widest text-gray-500`}>Stop Loss</p>
                        <p className={`${compact ? 'text-[10px]' : 'text-sm'} font-mono text-gray-400`}>{formatPrice(stop_loss)}</p>
                    </div>
                    <div className="space-y-0.5 text-right">
                        <p className={`${compact ? 'text-[8px]' : 'text-[10px]'} uppercase tracking-widest text-[#00ffa3]`}>Take Profit</p>
                        <p className={`${compact ? 'text-[10px]' : 'text-sm'} font-mono text-white`}>{formatPrice(take_profit)}</p>
                    </div>
                </div>
            )}

            {/* Footer Action (Full Mode Only) */}
            {!compact && !isNeutral && (
                <div className="p-4">
                    <button
                        onClick={() => onViewChart && onViewChart(symbol)}
                        className={`
                            relative w-full py-3 rounded-lg font-bold text-xs tracking-[0.2em] uppercase overflow-hidden
                            transition-all duration-300
                            ${isBuy
                                ? 'bg-[#00ffa3] text-black hover:bg-[#00ffaa] shadow-[0_4px_20px_-5px_rgba(0,255,163,0.3)] hover:shadow-[0_6px_25px_-5px_rgba(0,255,163,0.5)]'
                                : 'bg-[#ff4d4d] text-white hover:bg-[#ff6666] shadow-[0_4px_20px_-5px_rgba(255,77,77,0.3)] hover:shadow-[0_6px_25px_-5px_rgba(255,77,77,0.5)]'}
                        `}
                    >
                        Analyze Signal
                    </button>
                </div>
            )}
        </div>
    );
};

export default SignalCard;
