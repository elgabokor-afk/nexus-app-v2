import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabaseClient';
import { Shield, Key, CheckCircle, AlertTriangle, Loader2, Save, Trash2 } from 'lucide-react';

export default function ExchangeSettings() {
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [exchange, setExchange] = useState('binance');
    const [apiKey, setApiKey] = useState('');
    const [apiSecret, setApiSecret] = useState('');
    const [hasKeys, setHasKeys] = useState(false);
    const [status, setStatus] = useState<string | null>(null);

    useEffect(() => {
        fetchStatus();
    }, []);

    const fetchStatus = async () => {
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) return;

        const { data } = await supabase
            .from('user_exchanges')
            .select('id')
            .eq('user_id', user.id)
            .eq('is_active', true)
            .maybeSingle();

        if (data) setHasKeys(true);
        setLoading(false);
    };

    const saveKeys = async () => {
        setSaving(true);
        setStatus(null);

        try {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) throw new Error("Auth required");

            // VALIDATION: No empty keys
            if (!apiKey || !apiSecret) throw new Error("Please fill both API Key and Secret");

            // V5005: CALL BACKEND TO ENCRYPT AND SAVE
            // V5005: CALL BACKEND TO ENCRYPT AND SAVE
            const API_URL = "/api/py";

            const res = await fetch(`${API_URL}/save-keys`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: user.id,
                    exchange: exchange,
                    api_key: apiKey,
                    secret_key: apiSecret
                })
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || data.error || "Failed to save keys");

            setHasKeys(true);
            setApiKey('');
            setApiSecret('');
            setStatus('success');

        } catch (e: any) {
            console.error(e);
            setStatus(e.message);
        } finally {
            setSaving(false);
        }
    };

    const disconnect = async () => {
        if (!confirm("Are you sure you want to disconnect your exchange?")) return;
        const { data: { user } } = await supabase.auth.getUser();
        await supabase.from('user_exchanges').delete().eq('user_id', user?.id);
        setHasKeys(false);
    };

    if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-[#00ffa3]" /></div>;

    return (
        <div className="bg-[#0a0a0c] border border-white/5 rounded-3xl p-8 max-w-2xl mx-auto shadow-2xl">
            <div className="flex items-center gap-4 mb-8">
                <div className="w-12 h-12 bg-[#00ffa3]/10 rounded-2xl flex items-center justify-center border border-[#00ffa3]/20">
                    <Shield className="text-[#00ffa3]" size={24} />
                </div>
                <div>
                    <h2 className="text-2xl font-black text-white italic tracking-tighter">EXCHANGE TERMINAL</h2>
                    <p className="text-xs text-zinc-500 font-mono uppercase tracking-widest">Secure Production Connection</p>
                </div>
            </div>

            {hasKeys ? (
                <div className="space-y-6 animate-in fade-in zoom-in duration-300">
                    <div className="bg-[#00ffa3]/10 border border-[#00ffa3]/20 rounded-2xl p-6 flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <CheckCircle className="text-[#00ffa3]" size={32} />
                            <div>
                                <h3 className="text-white font-bold">BINANCE CONNECTED</h3>
                                <p className="text-[10px] text-[#00ffa3] font-mono">READY FOR ONE-CLICK EXECUTION</p>
                            </div>
                        </div>
                        <button
                            onClick={disconnect}
                            className="p-3 bg-red-500/10 hover:bg-red-500/20 text-red-500 rounded-xl transition"
                        >
                            <Trash2 size={18} />
                        </button>
                    </div>
                </div>
            ) : (
                <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest ml-1">Exchange</label>
                            <select
                                value={exchange}
                                onChange={(e) => setExchange(e.target.value)}
                                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white focus:border-[#00ffa3] outline-none appearance-none cursor-pointer"
                            >
                                <option value="binance">Binance Futures</option>
                                <option value="bybit">ByBit (Coming Soon)</option>
                            </select>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <div className="space-y-2">
                            <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest ml-1 flex items-center gap-1">
                                <Key size={10} /> API Key
                            </label>
                            <input
                                type="text"
                                value={apiKey}
                                onChange={(e) => setApiKey(e.target.value)}
                                placeholder="Enter your Binance API Key"
                                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white font-mono text-sm focus:border-[#00ffa3] outline-none transition"
                            />
                        </div>

                        <div className="space-y-2">
                            <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest ml-1 flex items-center gap-1">
                                <Shield size={10} /> API Secret
                            </label>
                            <input
                                type="password"
                                value={apiSecret}
                                onChange={(e) => setApiSecret(e.target.value)}
                                placeholder="Enter your API Secret"
                                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white font-mono text-sm focus:border-[#00ffa3] outline-none transition"
                            />
                        </div>
                    </div>

                    <div className="bg-zinc-900/50 rounded-2xl p-4 border border-white/5 space-y-3">
                        <h4 className="text-[10px] font-black text-zinc-400 uppercase tracking-wider flex items-center gap-2">
                            <AlertTriangle size={12} className="text-yellow-500" /> Security Protocol
                        </h4>
                        <ul className="text-[10px] text-zinc-500 space-y-1 ml-4 list-disc italic">
                            <li>Ensure "Enable Withdrawals" is <strong className="text-red-500">DISABLED</strong>.</li>
                            <li>The bot only requires "Futures" and "Spot" trading permissions.</li>
                            <li>Your keys are encrypted via AES-256 before storage.</li>
                        </ul>
                    </div>

                    <button
                        onClick={saveKeys}
                        disabled={saving}
                        className="w-full py-4 bg-[#00ffa3] text-black rounded-xl font-black uppercase tracking-widest flex items-center justify-center gap-2 hover:scale-[1.01] transition-all disabled:opacity-50"
                    >
                        {saving ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
                        Save & Encrypt Connection
                    </button>

                    {status === 'success' && (
                        <p className="text-center text-[10px] font-bold text-[#00ffa3] animate-bounce">
                            CONNECTION SECURED! READY TO TRADE.
                        </p>
                    )}
                    {status && status !== 'success' && (
                        <p className="text-center text-[10px] font-bold text-red-500">
                            {status}
                        </p>
                    )}
                </div>
            )}
        </div>
    );
}
