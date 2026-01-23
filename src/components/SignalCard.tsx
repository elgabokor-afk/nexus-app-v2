import React from 'react';
import { ArrowUpRight, ArrowDownRight, Activity } from 'lucide-react';

interface SignalProps {
    symbol: string;
    price: number;
    rsi: number;
    signal_type: string;
    confidence: number;
    timestamp: string;
}

const SignalCard: React.FC<SignalProps> = ({ symbol, price, rsi, signal_type, confidence, timestamp }) => {
    const isBuy = signal_type.includes('BUY');
    const isSell = signal_type.includes('SELL');
    const isNeutral = !isBuy && !isSell;

    let borderColor = 'border-gray-800';
    let glowColor = '';
    let textColor = 'text-gray-400';

    if (isBuy) {
        borderColor = 'border-green-500';
        glowColor = 'shadow-[0_0_20px_rgba(0,255,163,0.1)]';
        textColor = 'text-[#00ffa3]';
    } else if (isSell) {
        borderColor = 'border-red-500';
        glowColor = 'shadow-[0_0_20px_rgba(255,77,77,0.1)]';
        textColor = 'text-red-500';
    }

    return (
        <div className={`bg-[#0e0e12] border ${borderColor} ${glowColor} rounded-xl p-5 mb-4 transition-all hover:scale-[1.02]`}>
            <div className="flex justify-between items-start mb-4">
                <div>
                    <h3 className="text-2xl font-bold font-mono text-white tracking-wider">{symbol}</h3>
                    <p className="text-xs text-gray-500">{new Date(timestamp).toLocaleTimeString()}</p>
                </div>
                <div className={`px-3 py-1 rounded-full text-xs font-bold border ${borderColor} ${textColor} bg-opacity-10`}>
                    {confidence}% CONFIDENCE
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                    <p className="text-xs text-gray-500 uppercase">Price</p>
                    <p className="text-lg font-mono text-white">${price.toLocaleString()}</p>
                </div>
                <div>
                    <p className="text-xs text-gray-500 uppercase">RSI (14)</p>
                    <div className="flex items-center gap-2">
                        <span className={`font-bold ${rsi < 30 ? 'text-green-400' : rsi > 70 ? 'text-red-400' : 'text-gray-300'}`}>
                            {rsi}
                        </span>
                        <Activity size={14} className="text-gray-600" />
                    </div>
                </div>
            </div>

            <div className={`flex items-center gap-2 text-sm font-bold ${textColor}`}>
                {isBuy && <ArrowUpRight size={20} />}
                {isSell && <ArrowDownRight size={20} />}
                {isNeutral && <span className="text-gray-600">WAITING FOR SETUP...</span>}
                <span>{signal_type.replace('STRONG ', '')}</span>
            </div>
        </div>
    );
};

export default SignalCard;
