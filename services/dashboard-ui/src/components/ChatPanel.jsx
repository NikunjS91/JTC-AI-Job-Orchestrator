import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const ChatPanel = () => {
    const [messages, setMessages] = useState([
        { role: 'system', content: 'Hello! I am your CareerOps Agent. You can ask me for stats or to research a company.' }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(scrollToBottom, [messages]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMsg = input;
        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setInput('');
        setLoading(true);

        // Simple intent mapping (in a real app, backend would do this with LLM)
        let intent = 'unknown';
        let params = {};

        if (userMsg.toLowerCase().includes('stats') || userMsg.toLowerCase().includes('status')) {
            intent = 'stats_today';
        } else if (userMsg.toLowerCase().includes('research')) {
            intent = 'research_company';
            const company = userMsg.split('research')[1]?.trim();
            if (company) params = { company };
        } else if (userMsg.toLowerCase().includes('summary')) {
            intent = 'summarize_last';
        } else {
            // Fallback to backend Semantic Router
            intent = 'natural_language';
            params = { message: userMsg };
        }

        try {
            const res = await axios.post('http://localhost:8004/intent', {
                intent,
                parameters: params
            });

            setMessages(prev => [...prev, { role: 'system', content: res.data.response }]);
        } catch (error) {
            setMessages(prev => [...prev, { role: 'system', content: 'Sorry, I encountered an error processing your request.' }]);
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-slate-800 rounded-xl border border-slate-700 flex flex-col h-[600px]">
            <div className="p-4 border-b border-slate-700">
                <h3 className="font-semibold text-slate-200">Agent Chat</h3>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] rounded-lg p-3 ${msg.role === 'user'
                                ? 'bg-blue-600 text-white'
                                : 'bg-slate-700 text-slate-200'
                            }`}>
                            <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-slate-700 rounded-lg p-3">
                            <div className="flex gap-1">
                                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce delay-75"></div>
                                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce delay-150"></div>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <form onSubmit={handleSend} className="p-4 border-t border-slate-700">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Type a command..."
                        className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                    />
                    <button
                        type="submit"
                        disabled={loading}
                        className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg disabled:opacity-50 transition-colors"
                    >
                        Send
                    </button>
                </div>
            </form>
        </div>
    );
};

export default ChatPanel;
