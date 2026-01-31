"use client";

import { Activity, Globe, TrendingUp, TrendingDown } from "lucide-react";

interface MacroProps {
    sentiment: "RISK_ON" | "RISK_OFF" | "NEUTRAL";
    dxyChange: number;
    spxChange: number;
}

export default function MacroMonitor({ sentiment, dxyChange, spxChange }: MacroProps) {
    const isRiskOn = sentiment === "RISK_ON";
    const isRiskOff = sentiment === "RISK_OFF";

    return (
        <div className="bg-[#0a0a0a] border border-white/10 rounded-xl p-4 flex flex-col gap-3 relative overflow-hidden group">
            {/* Background Glow */}
            <div className={`absolute -right-10 -top-10 w-32 h-32 blur-[60px] rounded-full opacity-20
                ${isRiskOn ? "bg-green-500" : isRiskOff ? "bg-red-500" : "bg-blue-500"}`}
            />

            <div className="flex items-center justifyContent-between">
                <h3 className="text-xs font-bold text-gray-500 tracking-widest uppercase flex items-center gap-2">
                    <Globe size={14} className="text-[#00ffa3]" />
                    Macro Correlation
                </h3>
                <span className={`text-[10px] font-black px-2 py-0.5 rounded border 
                    ${isRiskOn ? "bg-green-500/20 border-green-500 text-green-400" :
                        isRiskOff ? "bg-red-500/20 border-red-500 text-red-400" :
                            "bg-blue-500/20 border-blue-500 text-blue-400"}`}>
                    {sentiment.replace("_", " ")}
                </span>
            </div>

            <div className="grid grid-cols-2 gap-2 mt-2">
                {/* DXY */}
                <div>
                    <span className="text-gray-400 text-[10px] font-bold">DXY (USD)</span>
                    <div className="flex items-center gap-2 mt-1">
                        {dxyChange > 0 ? <TrendingUp size={16} className="text-red-400" /> : <TrendingDown size={16} className="text-green-400" />}
                        <span className={`text-xl font-mono font-bold ${dxyChange > 0 ? "text-red-400" : "text-green-400"}`}>
                            {dxyChange > 0 ? "+" : ""}{dxyChange.toFixed(2)}%
                        </span>
                    </div>
                </div>

                {/* SPX */}
                <div>
                    <span className="text-gray-400 text-[10px] font-bold">SPX (S&P500)</span>
                    <div className="flex items-center gap-2 mt-1">
                        {spxChange > 0 ? <TrendingUp size={16} className="text-green-400" /> : <TrendingDown size={16} className="text-red-400" />}
                        <span className={`text-xl font-mono font-bold ${spxChange > 0 ? "text-green-400" : "text-red-400"}`}>
                            {spxChange > 0 ? "+" : ""}{spxChange.toFixed(2)}%
                        </span>
                    </div>
                </div>
            </div>

            <p className="text-[9px] text-gray-600 font-mono mt-1">
                algo_logic: {isRiskOn ? "Weak Dollar detected. Crypto confidence boosted." : isRiskOff ? "Strong Dollar detected. Defensive mode active." : "Markets stable."}
            </p>
        </div>
    );
}
