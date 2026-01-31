
'use client';

import { useState, useEffect, useRef } from 'react';
import { Send, X, Bot, Sparkles, User, Loader2 } from 'lucide-react';

interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
}

interface AIChatModalProps {
    signal: any;
    isOpen: boolean;
    onClose: () => void;
}

export default function AIChatModal({ signal, isOpen, onClose }: AIChatModalProps) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Initial Greeting
    useEffect(() => {
        if (isOpen && messages.length === 0) {
            setMessages([
                {
                    role: 'assistant',
                    content: `Hello! I'm your Nexus Trading Advisor. I've analyzed **${signal.symbol}**. Ask me about the risk, targets, or why this signal was generated.`
                }
            ]);
        }
    }, [isOpen, signal]);

    // Auto-scroll
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim() || loading) return;

        const userMsg = input;
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setLoading(true);

        try {
            const res = await fetch('/api/chat/advisor', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: userMsg,
                    signalContext: signal
                })
            });
            const data = await res.json();

            setMessages(prev => [...prev, { role: 'assistant', content: data.reply || "Connection error." }]);
        } catch (e) {
            setMessages(prev => [...prev, { role: 'assistant', content: "Error connecting to Neural Net." }]);
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
            <div className="w-full max-w-md bg-[#0a0a0c] border border-white/10 rounded-3xl shadow-2xl flex flex-col overflow-hidden max-h-[600px] animate-slide-up">

                {/* Header */}
                <div className="p-4 border-b border-white/10 bg-white/[0.02] flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-purple-500/20 rounded-xl border border-purple-500/30">
                            <Bot size={20} className="text-purple-400" />
                        </div>
                        <div>
                            <h3 className="text-sm font-bold text-white">Nexus Advisor</h3>
                            <p className="text-[10px] text-gray-400 font-mono">Analyzing {signal.symbol}</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-full transition-colors text-gray-400 hover:text-white">
                        <X size={18} />
                    </button>
                </div>

                {/* Chat Area */}
                <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar bg-[url('/grid-pattern.svg')]">
                    {messages.map((m, idx) => (
                        <div key={idx} className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            {m.role === 'assistant' && (
                                <div className="w-6 h-6 rounded-full bg-purple-500/20 flex items-center justify-center border border-purple-500/30 mt-1">
                                    <Sparkles size={12} className="text-purple-400" />
                                </div>
                            )}
                            <div className={`max-w-[80%] p-3 rounded-2xl text-xs leading-relaxed ${m.role === 'user'
                                    ? 'bg-blue-600 text-white rounded-tr-sm'
                                    : 'bg-white/5 text-gray-200 border border-white/10 rounded-tl-sm prose prose-invert prose-sm' // prose for potential markdown
                                }`}>
                                <div dangerouslySetInnerHTML={{ __html: m.content.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>').replace(/\n/g, '<br/>') }} />
                            </div>
                            {m.role === 'user' && (
                                <div className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center border border-blue-500/30 mt-1">
                                    <User size={12} className="text-blue-400" />
                                </div>
                            )}
                        </div>
                    ))}
                    {loading && (
                        <div className="flex gap-3 justify-start">
                            <div className="w-6 h-6 rounded-full bg-purple-500/20 flex items-center justify-center mt-1">
                                <Loader2 size={12} className="text-purple-400 animate-spin" />
                            </div>
                            <div className="bg-white/5 px-4 py-2 rounded-2xl">
                                <span className="text-[10px] text-gray-500 animate-pulse">Computing...</span>
                            </div>
                        </div>
                    )}
                </div>

                {/* Input Area */}
                <div className="p-4 border-t border-white/10 bg-white/[0.02]">
                    <div className="flex gap-2">
                        <input
                            type="text"
                            className="flex-1 bg-black/20 border border-white/10 rounded-xl px-4 py-2 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-purple-500/50 transition-colors"
                            placeholder="Ask about this trade..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                        />
                        <button
                            onClick={handleSend}
                            disabled={loading || !input.trim()}
                            className="bg-purple-600 hover:bg-purple-500 text-white p-2 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <Send size={16} />
                        </button>
                    </div>
                </div>

            </div>
        </div>
    );
}
