"use client";

import { useEffect, useState, useMemo } from 'react';
import { supabase } from '@/lib/supabaseClient';
import { User as UserIcon, Camera, Save, Upload, BookOpen, LayoutGrid, Twitter, TrendingUp, Trophy, AlertTriangle } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export default function ProfilePage() {
    const [user, setUser] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'profile' | 'journal'>('profile');

    // Profile State
    const [profile, setProfile] = useState({
        full_name: '',
        bio: '',
        twitter_handle: '',
        trading_style: 'SCALPER',
        avatar_url: ''
    });

    // Journal State
    const [journalEntries, setJournalEntries] = useState<any[]>([]);
    const [newEntry, setNewEntry] = useState({
        symbol: '',
        pnl_percent: '',
        notes: '',
        image_url: '' // For now, simple URL input or Mock
    });

    // Derived Stats
    const stats = useMemo(() => {
        if (journalEntries.length === 0) return null;

        const totalTrades = journalEntries.length;
        const wins = journalEntries.filter(e => e.pnl_percent > 0).length;
        const winRate = (wins / totalTrades) * 100;
        const totalPnL = journalEntries.reduce((acc, curr) => acc + (curr.pnl_percent || 0), 0);
        const avgPnL = totalPnL / totalTrades;

        const sortedByPnL = [...journalEntries].sort((a, b) => b.pnl_percent - a.pnl_percent);
        const bestTrade = sortedByPnL[0];
        const worstTrade = sortedByPnL[sortedByPnL.length - 1];

        // Chart Data (Cumulative PnL)
        // Reverse array to be chronological (assuming API returns desc)
        let balance = 0;
        const chartData = [...journalEntries].reverse().map((e, i) => {
            balance += e.pnl_percent;
            return {
                id: i + 1,
                date: new Date(e.created_at).toLocaleDateString(),
                pnl: balance,
                raw: e.pnl_percent
            };
        });

        return { totalTrades, winRate, totalPnL, avgPnL, bestTrade, worstTrade, chartData };
    }, [journalEntries]);

    useEffect(() => {
        const fetchUser = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (user) {
                setUser(user);
                loadProfile(user.id);
                loadJournal(user.id);
            }
            setLoading(false);
        };
        fetchUser();
    }, []);

    const loadProfile = async (uid: string) => {
        const { data } = await supabase.from('profiles').select('*').eq('id', uid).single();
        if (data) setProfile(data);
    };

    const loadJournal = async (uid: string) => {
        const { data } = await supabase.from('trade_journal').select('*').eq('user_id', uid).order('created_at', { ascending: false });
        if (data) setJournalEntries(data);
    };

    const handleUpdateProfile = async () => {
        try {
            const { error } = await supabase.from('profiles').update(profile).eq('id', user.id);
            if (error) throw error;
            alert("Profile Updated Successfully!");
        } catch (e: any) {
            alert("Error: " + e.message);
        }
    };

    const handleAddJournal = async () => {
        try {
            if (!newEntry.symbol || !newEntry.pnl_percent) return alert("Fill Symbol and PnL");

            const { error } = await supabase.from('trade_journal').insert({
                user_id: user.id,
                symbol: newEntry.symbol.toUpperCase(),
                pnl_percent: parseFloat(newEntry.pnl_percent),
                notes: newEntry.notes,
                image_url: newEntry.image_url
            });

            if (error) throw error;

            setNewEntry({ symbol: '', pnl_percent: '', notes: '', image_url: '' }); // Reset
            loadJournal(user.id); // Reload
            alert("Trade Saved!");
        } catch (e: any) {
            alert("Error: " + e.message);
        }
    };

    if (loading) return <div className="p-8 text-white">Loading...</div>;

    return (
        <div className="flex flex-col h-full overflow-y-auto p-4 md:p-8 space-y-8 animate-fade-in custom-scrollbar">

            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-black text-white tracking-tighter">USER PROFILE</h1>
                    <p className="text-sm text-gray-500 font-mono">Manage your identity and trading records.</p>
                </div>

                {/* Tabs */}
                <div className="flex bg-[#0e0e10] p-1 rounded-lg border border-[#2f3336]">
                    <button
                        onClick={() => setActiveTab('profile')}
                        className={`px-4 py-2 rounded-md text-xs font-bold transition-all flex items-center gap-2
                        ${activeTab === 'profile' ? 'bg-[#2f3336] text-white shadow-lg' : 'text-gray-500 hover:text-white'}`}
                    >
                        <UserIcon size={16} /> PROFILE
                    </button>
                    <button
                        onClick={() => setActiveTab('journal')}
                        className={`px-4 py-2 rounded-md text-xs font-bold transition-all flex items-center gap-2
                         ${activeTab === 'journal' ? 'bg-[#2f3336] text-white shadow-lg' : 'text-gray-500 hover:text-white'}`}
                    >
                        <BookOpen size={16} /> TRADING JOURNAL
                    </button>
                </div>
            </div>

            {/* Content */}
            {activeTab === 'profile' ? (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {/* Left: Avatar Card */}
                    <div className="md:col-span-1 bg-[#0a0a0c] border border-[#2f3336] rounded-2xl p-6 flex flex-col items-center justify-center text-center">
                        <div className="w-32 h-32 rounded-full bg-gradient-to-br from-[#00ffa3] to-blue-600 p-1 mb-4 relative group cursor-pointer">
                            <div className="w-full h-full rounded-full bg-black flex items-center justify-center overflow-hidden">
                                {profile.avatar_url ? (
                                    <img src={profile.avatar_url} alt="Ava" className="w-full h-full object-cover" />
                                ) : (
                                    <UserIcon size={48} className="text-gray-500" />
                                )}
                            </div>
                            <div className="absolute inset-0 bg-black/60 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity rounded-full">
                                <Camera className="text-white" size={24} />
                            </div>
                        </div>
                        <h2 className="text-xl font-bold text-white">{profile.full_name || 'Anonymous Trader'}</h2>
                        <p className="text-xs text-gray-500 font-mono mt-1">{user.email}</p>
                        <span className="mt-4 px-3 py-1 bg-[#00ffa3]/10 text-[#00ffa3] text-[10px] font-bold rounded-full border border-[#00ffa3]/20">
                            {profile.trading_style}
                        </span>
                    </div>

                    {/* Right: Details Form */}
                    <div className="md:col-span-2 bg-[#0a0a0c] border border-[#2f3336] rounded-2xl p-8">
                        <div className="space-y-6">
                            <div className="grid grid-cols-2 gap-6">
                                <div>
                                    <label className="block text-[10px] font-bold text-gray-500 mb-2 uppercase">Full Name</label>
                                    <input
                                        type="text"
                                        value={profile.full_name || ''}
                                        onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
                                        className="w-full bg-[#0e0e10] border border-[#2f3336] rounded-lg p-3 text-white focus:border-[#00ffa3] transition-colors outline-none"
                                        placeholder="John Doe"
                                    />
                                </div>
                                <div>
                                    <label className="block text-[10px] font-bold text-gray-500 mb-2 uppercase">Trading Style</label>
                                    <select
                                        value={profile.trading_style || 'SCALPER'}
                                        onChange={(e) => setProfile({ ...profile, trading_style: e.target.value })}
                                        className="w-full bg-[#0e0e10] border border-[#2f3336] rounded-lg p-3 text-white focus:border-[#00ffa3] transition-colors outline-none"
                                    >
                                        <option value="SCALPER">High Freq Scalper</option>
                                        <option value="SWING">Swing Trader</option>
                                        <option value="HODL">Investor (HODL)</option>
                                    </select>
                                </div>
                            </div>

                            <div>
                                <label className="block text-[10px] font-bold text-gray-500 mb-2 uppercase">Bio / Mantra</label>
                                <textarea
                                    value={profile.bio || ''}
                                    onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
                                    rows={4}
                                    className="w-full bg-[#0e0e10] border border-[#2f3336] rounded-lg p-3 text-white focus:border-[#00ffa3] transition-colors outline-none"
                                    placeholder="I trade the trend..."
                                />
                            </div>

                            <div>
                                <label className="block text-[10px] font-bold text-gray-500 mb-2 uppercase flex items-center gap-2">
                                    <Twitter size={12} /> Twitter Handle
                                </label>
                                <div className="relative">
                                    <span className="absolute left-3 top-3 text-gray-500">@</span>
                                    <input
                                        type="text"
                                        value={profile.twitter_handle || ''}
                                        onChange={(e) => setProfile({ ...profile, twitter_handle: e.target.value })}
                                        className="w-full bg-[#0e0e10] border border-[#2f3336] rounded-lg p-3 pl-8 text-white focus:border-[#00ffa3] transition-colors outline-none"
                                        placeholder="trader_xyz"
                                    />
                                </div>
                            </div>

                            <div className="pt-4 border-t border-[#2f3336] flex justify-end">
                                <button
                                    onClick={handleUpdateProfile}
                                    className="px-6 py-2 bg-[#00ffa3] hover:bg-[#00ffa3]/90 text-black font-bold rounded-lg flex items-center gap-2 transition-all"
                                >
                                    <Save size={18} /> SAVE CHANGES
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="space-y-6">

                    {/* STATS ANALYTICS SECTION */}
                    {stats && (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-in fade-in slide-in-from-bottom-4">
                            <div className="bg-[#0a0a0c] border border-[#2f3336] rounded-xl p-4 flex flex-col justify-between group hover:border-[#00ffa3]/30 transition-colors">
                                <div className="flex justify-between items-start">
                                    <span className="text-[10px] font-bold text-gray-500 uppercase">Win Rate</span>
                                    <Trophy size={16} className="text-yellow-400" />
                                </div>
                                <span className={`text-3xl font-black ${stats.winRate >= 50 ? 'text-[#00ffa3]' : 'text-red-400'}`}>
                                    {stats.winRate.toFixed(1)}%
                                </span>
                            </div>
                            <div className="bg-[#0a0a0c] border border-[#2f3336] rounded-xl p-4 flex flex-col justify-between group hover:border-[#00ffa3]/30 transition-colors">
                                <div className="flex justify-between items-start">
                                    <span className="text-[10px] font-bold text-gray-500 uppercase">Total PnL %</span>
                                    <TrendingUp size={16} className="text-blue-400" />
                                </div>
                                <span className={`text-3xl font-black ${stats.totalPnL >= 0 ? 'text-[#00ffa3]' : 'text-red-400'}`}>
                                    {stats.totalPnL > 0 ? '+' : ''}{stats.totalPnL.toFixed(2)}%
                                </span>
                            </div>
                            <div className="bg-[#0a0a0c] border border-[#2f3336] rounded-xl p-4 flex flex-col justify-between group hover:border-[#00ffa3]/30 transition-colors">
                                <div className="flex justify-between items-start">
                                    <span className="text-[10px] font-bold text-gray-500 uppercase">Best Trade</span>
                                    <TrendingUp size={16} className="text-[#00ffa3]" />
                                </div>
                                <div className="flex flex-col">
                                    <span className="text-xl font-black text-white">{stats.bestTrade?.symbol}</span>
                                    <span className="text-sm font-bold text-[#00ffa3]">+{stats.bestTrade?.pnl_percent}%</span>
                                </div>
                            </div>
                            <div className="bg-[#0a0a0c] border border-[#2f3336] rounded-xl p-4 flex flex-col justify-between group hover:border-[#00ffa3]/30 transition-colors">
                                <div className="flex justify-between items-start">
                                    <span className="text-[10px] font-bold text-gray-500 uppercase">Journal Entries</span>
                                    <BookOpen size={16} className="text-purple-400" />
                                </div>
                                <span className="text-3xl font-black text-white">{stats.totalTrades}</span>
                            </div>
                        </div>
                    )}

                    {/* CHART SECTION */}
                    {stats && stats.chartData.length > 1 && (
                        <div className="w-full h-64 bg-[#0a0a0c] border border-[#2f3336] rounded-xl p-4 relative overflow-hidden">
                            <h3 className="text-xs font-bold text-gray-500 uppercase mb-4 flex items-center gap-2">
                                <TrendingUp size={14} /> Cumulative Performance
                            </h3>
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={stats.chartData}>
                                    <defs>
                                        <linearGradient id="colorPnL" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#00ffa3" stopOpacity={0.2} />
                                            <stop offset="95%" stopColor="#00ffa3" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#222" />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#111', borderColor: '#333' }}
                                        itemStyle={{ color: '#fff' }}
                                    />
                                    <Area type="monotone" dataKey="pnl" stroke="#00ffa3" strokeWidth={2} fillOpacity={1} fill="url(#colorPnL)" />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        {/* Left: Add New Entry */}
                        <div className="md:col-span-1 bg-[#0a0a0c] border border-[#2f3336] rounded-2xl p-6 h-fit sticky top-4">
                            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                <Upload size={18} className="text-[#00ffa3]" /> New Journal Entry
                            </h3>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-[10px] font-bold text-gray-500 mb-1 uppercase">Symbol</label>
                                    <input
                                        type="text"
                                        value={newEntry.symbol}
                                        onChange={(e) => setNewEntry({ ...newEntry, symbol: e.target.value })}
                                        className="w-full bg-[#0e0e10] border border-[#2f3336] rounded-lg p-2 text-white outline-none focus:border-[#00ffa3] transition-colors"
                                        placeholder="e.g. BTC/USDT"
                                    />
                                </div>
                                <div>
                                    <label className="block text-[10px] font-bold text-gray-500 mb-1 uppercase">PnL %</label>
                                    <input
                                        type="number"
                                        value={newEntry.pnl_percent}
                                        onChange={(e) => setNewEntry({ ...newEntry, pnl_percent: e.target.value })}
                                        className="w-full bg-[#0e0e10] border border-[#2f3336] rounded-lg p-2 text-white outline-none focus:border-[#00ffa3] transition-colors"
                                        placeholder="e.g. 15.5"
                                    />
                                </div>
                                <div>
                                    <label className="block text-[10px] font-bold text-gray-500 mb-1 uppercase">Screenshot URL</label>
                                    <input
                                        type="text"
                                        value={newEntry.image_url}
                                        onChange={(e) => setNewEntry({ ...newEntry, image_url: e.target.value })}
                                        className="w-full bg-[#0e0e10] border border-[#2f3336] rounded-lg p-2 text-white outline-none focus:border-[#00ffa3] transition-colors"
                                        placeholder="https://imgur.com/..."
                                    />
                                </div>
                                <div>
                                    <label className="block text-[10px] font-bold text-gray-500 mb-1 uppercase">Notes</label>
                                    <textarea
                                        value={newEntry.notes}
                                        onChange={(e) => setNewEntry({ ...newEntry, notes: e.target.value })}
                                        rows={3}
                                        className="w-full bg-[#0e0e10] border border-[#2f3336] rounded-lg p-2 text-white outline-none focus:border-[#00ffa3] transition-colors"
                                        placeholder="Entry reason..."
                                    />
                                </div>
                                <button
                                    onClick={handleAddJournal}
                                    className="w-full py-2 bg-white/10 hover:bg-white/20 text-white font-bold rounded-lg border border-white/10 transition-colors"
                                >
                                    + ADD ENTRY
                                </button>
                            </div>
                        </div>

                        {/* Right: Gallery */}
                        <div className="md:col-span-2">
                            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                <LayoutGrid size={18} className="text-[#00ffa3]" /> Past Entires
                            </h3>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-h-[600px] overflow-y-auto custom-scrollbar pr-2">
                                {journalEntries.map((entry) => (
                                    <div key={entry.id} className="group relative bg-[#0e0e10] border border-[#2f3336] rounded-xl overflow-hidden hover:border-[#00ffa3]/50 transition-colors">
                                        {entry.image_url ? (
                                            <div className="h-40 bg-gray-800 relative">
                                                <img src={entry.image_url} className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity" />
                                                <div className="absolute top-2 right-2 px-2 py-1 bg-black/70 rounded text-xs font-mono text-white">
                                                    {new Date(entry.trade_date || entry.created_at).toLocaleDateString()}
                                                </div>
                                            </div>
                                        ) : (
                                            <div className="h-40 bg-[#1a1c20] flex items-center justify-center relative">
                                                <Camera className="text-gray-700" />
                                                <div className="absolute top-2 right-2 px-2 py-1 bg-black/70 rounded text-xs font-mono text-white">
                                                    {new Date(entry.trade_date || entry.created_at).toLocaleDateString()}
                                                </div>
                                            </div>
                                        )}
                                        <div className="p-4">
                                            <div className="flex justify-between items-center mb-2">
                                                <span className="font-bold text-white text-base">{entry.symbol}</span>
                                                <span className={`font-mono text-sm font-bold ${entry.pnl_percent >= 0 ? 'text-[#00ffa3]' : 'text-red-500'}`}>
                                                    {entry.pnl_percent > 0 ? '+' : ''}{entry.pnl_percent}%
                                                </span>
                                            </div>
                                            <p className="text-xs text-gray-400 line-clamp-3">{entry.notes}</p>
                                        </div>
                                    </div>
                                ))}
                                {journalEntries.length === 0 && (
                                    <div className="col-span-2 text-center py-20 text-gray-600 border border-dashed border-[#2f3336] rounded-xl">
                                        <BookOpen size={48} className="mx-auto mb-4 opacity-50" />
                                        <p className="text-lg font-bold">Your Journal is Empty</p>
                                        <p className="text-sm">Record your first trade to unlock potential.</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}

        </div>
    );
}
