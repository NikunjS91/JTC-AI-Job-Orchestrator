import React, { useState, useEffect } from 'react';
import axios from 'axios';
import EventCard from './EventCard';
import KanbanBoard from './KanbanBoard';
import ChatPanel from './ChatPanel';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const ORCHESTRATOR_URL = import.meta.env.VITE_ORCHESTRATOR_URL || 'http://localhost:8005';

const Dashboard = () => {
    const [stats, setStats] = useState({ total_events: 0, interviews: 0, offers: 0, rejections: 0 });
    const [applications, setApplications] = useState([]);
    const [loading, setLoading] = useState(true);
    const [connectionStatus, setConnectionStatus] = useState('connecting'); // connecting, connected, error

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [statsRes, appsRes] = await Promise.all([
                    axios.get(`${API_URL}/stats`),
                    axios.get(`${API_URL}/applications`)
                ]);
                setStats(statsRes.data);
                setApplications(appsRes.data);
            } catch (error) {
                console.error("Failed to fetch data:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    useEffect(() => {
        const eventSource = new EventSource(`${ORCHESTRATOR_URL}/events`);

        eventSource.onopen = () => {
            console.log("SSE Connected");
            setConnectionStatus('connected');
        };

        eventSource.onmessage = (event) => {
            try {
                const parsedData = JSON.parse(event.data);

                if (parsedData.type === 'heartbeat') {
                    // Optional: update last heartbeat timestamp
                } else if (parsedData.type === 'notification') {
                    const newEvent = parsedData.data;

                    // Update Stats
                    setStats(prev => {
                        const newStats = { ...prev, total_events: prev.total_events + 1 };
                        if (newEvent.event_type === 'INTERVIEW') newStats.interviews += 1;
                        else if (newEvent.event_type === 'OFFER') newStats.offers += 1;
                        else if (newEvent.event_type === 'REJECTION') newStats.rejections += 1;
                        return newStats;
                    });

                    // Update Applications List
                    setApplications(prev => {
                        // Check if exists (update status)
                        const exists = prev.find(a => a.id === newEvent.event_id);
                        if (exists) {
                            return prev.map(a => a.id === newEvent.event_id ? {
                                ...a,
                                ...newEvent,
                                status: newEvent.event_type
                            } : a);
                        }
                        // Add new
                        return [{
                            id: newEvent.event_id,
                            company: newEvent.company,
                            role: newEvent.role,
                            status: newEvent.event_type,
                            confidence: newEvent.confidence,
                            summary: newEvent.summary,
                            created_at: newEvent.classified_at || new Date().toISOString()
                        }, ...prev];
                    });
                }
            } catch (e) {
                console.error("Error parsing SSE event:", e);
            }
        };

        eventSource.onerror = (err) => {
            console.error("SSE Error:", err);
            setConnectionStatus('error');
            eventSource.close();
        };

        return () => {
            eventSource.close();
        };
    }, []);

    if (loading) return <div className="text-white text-center mt-20">Loading Dashboard...</div>;

    return (
        <div className="p-8 max-w-7xl mx-auto">
            <header className="mb-8 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white">CareerOps Dashboard</h1>
                    <p className="text-slate-400">Real-time Application Tracking</p>
                </div>
                <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${connectionStatus === 'connected' ? 'bg-green-500 animate-pulse' :
                            connectionStatus === 'error' ? 'bg-red-500' : 'bg-yellow-500'
                        }`}></div>
                    <span className="text-sm text-slate-300">
                        {connectionStatus === 'connected' ? 'System Operational' :
                            connectionStatus === 'error' ? 'Connection Lost' : 'Connecting...'}
                    </span>
                </div>
            </header>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
                    <h3 className="text-slate-400 text-sm font-medium">Total Applications</h3>
                    <p className="text-3xl font-bold text-white mt-2">{stats.total_events}</p>
                </div>
                <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
                    <h3 className="text-slate-400 text-sm font-medium">Interviews</h3>
                    <p className="text-3xl font-bold text-purple-400 mt-2">{stats.interviews}</p>
                </div>
                <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
                    <h3 className="text-slate-400 text-sm font-medium">Offers</h3>
                    <p className="text-3xl font-bold text-green-400 mt-2">{stats.offers}</p>
                </div>
                <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
                    <h3 className="text-slate-400 text-sm font-medium">Rejections</h3>
                    <p className="text-3xl font-bold text-red-400 mt-2">{stats.rejections}</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Content: Kanban + Feed */}
                <div className="lg:col-span-2 space-y-8">
                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">Pipeline</h2>
                        <KanbanBoard applications={applications} />
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">Recent Activity</h2>
                        <div className="space-y-4">
                            {applications.slice(0, 5).map(app => (
                                <EventCard key={app.id} event={app} />
                            ))}
                            {applications.length === 0 && (
                                <p className="text-slate-500 italic">No activity yet.</p>
                            )}
                        </div>
                    </section>
                </div>

                {/* Sidebar: Chat */}
                <div className="lg:col-span-1">
                    <ChatPanel />
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
