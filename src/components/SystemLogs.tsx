'use client';

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabaseClient';
import { AlertCircle, Terminal, X, RefreshCw, AlertTriangle, ShieldCheck } from 'lucide-react';

interface Log {
    id: number;
    timestamp: string;
    service: string;
    error_level: string;
    message: string;
}

export default function SystemLogs({ onClose, embedded = false }: { onClose?: () => void, embedded?: boolean }) {
    const [logs, setLogs] = useState<Log[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchLogs = async () => {
        setLoading(true);
        const { data } = await supabase
            .from('error_logs')
            .select('*')
            .order('timestamp', { ascending: false })
            .limit(100);

        if (data) setLogs(data);
        setLoading(false);
    };

    useEffect(() => {
        fetchLogs();

        // REALTIME SUBSCRIPTION
        const channel = supabase.channel('system_logs_stream')
            .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'error_logs' }, (payload) => {
                const newLog = payload.new as Log;
                setLogs(prev => [newLog, ...prev].slice(0, 100));
            })
            .subscribe();

        return () => {
            supabase.removeChannel(channel);
        };
    }, []);

    const wrapperClasses = embedded
        ? "w-full h-full flex flex-col bg-transparent"
        : "fixed inset-0 z-[100] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4";

    const containerClasses = embedded
        ? "w-full h-full flex flex-col bg-transparent"
        : "w-full max-w-4xl bg-[#0a0a0c] border border-white/10 rounded-3xl shadow-2xl flex flex-col max-h-[80vh] overflow-hidden animate-in zoom-in-95 duration-200";

    return (
        <div className={wrapperClasses}>
            <div className={containerClasses}>
                {/* Header */}
                <div className="p-6 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
                    <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center border border-red-500/20">
                            <Terminal size={20} className="text-red-500" />
                        </div>
                        <div>
                            <h2 className="text-lg font-black text-white tracking-tight">SYSTEM LOGS</h2>
                            <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">Backend Diagnostics Stream</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={fetchLogs}
                            className="p-2 hover:bg-white/5 rounded-xl text-gray-500 hover:text-white transition-colors"
                        >
                            <RefreshCw size={18} className={loading ? "animate-spin" : ""} />
                        </button>
                        {!embedded && onClose && (
                            <button
                                onClick={onClose}
                                className="p-2 hover:bg-red-500/10 rounded-xl text-gray-500 hover:text-red-500 transition-colors"
                            >
                                <X size={18} />
                            </button>
                        )}
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-0 bg-black">
                    <table className="w-full text-left border-collapse">
                        <thead className="bg-white/[0.02] sticky top-0 backdrop-blur-md z-10">
                            <tr>
                                <th className="p-4 text-[9px] font-black text-gray-500 uppercase tracking-widest border-b border-white/5">Time</th>
                                <th className="p-4 text-[9px] font-black text-gray-500 uppercase tracking-widest border-b border-white/5">Level</th>
                                <th className="p-4 text-[9px] font-black text-gray-500 uppercase tracking-widest border-b border-white/5">Service</th>
                                <th className="p-4 text-[9px] font-black text-gray-500 uppercase tracking-widest border-b border-white/5 w-full">Message</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {logs.length === 0 ? (
                                <tr>
                                    <td colSpan={4} className="p-12 text-center">
                                        <div className="flex flex-col items-center gap-3 opacity-30">
                                            <ShieldCheck size={48} />
                                            <p className="font-mono text-sm">System Healthy. No Critical Errors.</p>
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                logs.map(log => (
                                    <tr key={log.id} className="hover:bg-white/[0.02] transition-colors font-mono text-xs group">
                                        <td className="p-4 text-gray-500 whitespace-nowrap">
                                            {new Date(log.timestamp).toLocaleTimeString()}
                                        </td>
                                        <td className="p-4">
                                            <span className={`
                                                px-2 py-1 rounded text-[9px] font-bold uppercase tracking-wider
                                                ${log.error_level === 'CRITICAL' ? 'bg-red-500/20 text-red-500 border border-red-500/20' : ''}
                                                ${log.error_level === 'ERROR' ? 'bg-orange-500/20 text-orange-500 border border-orange-500/20' : ''}
                                                ${log.error_level === 'WARNING' ? 'bg-yellow-500/20 text-yellow-500 border border-yellow-500/20' : ''}
                                            `}>
                                                {log.error_level}
                                            </span>
                                        </td>
                                        <td className="p-4 text-gray-400 font-bold uppercase">{log.service}</td>
                                        <td className="p-4 text-gray-300 break-all">{log.message}</td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Footer */}
                <div className="p-3 border-t border-white/5 bg-white/[0.02] flex items-center justify-between text-[10px] text-gray-600 font-mono">
                    <span>SERVER: KRAKEN-US-EAST-1</span>
                    <span>LOG_RETENTION: 7 DAYS</span>
                </div>
            </div>
        </div>
    );
}
