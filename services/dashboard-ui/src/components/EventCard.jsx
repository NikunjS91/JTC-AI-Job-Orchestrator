import React from 'react';
import { cn } from '../lib/utils';
import { Briefcase, Building, CheckCircle, XCircle, AlertCircle, ChevronRight } from 'lucide-react';

const EventCard = ({ event }) => {
    const getStatusColor = (type) => {
        switch (type) {
            case 'INTERVIEW': return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
            case 'OFFER': return 'bg-green-500/10 text-green-500 border-green-500/20';
            case 'REJECTION': return 'bg-red-500/10 text-red-500 border-red-500/20';
            default: return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
        }
    };

    const getIcon = (type) => {
        switch (type) {
            case 'INTERVIEW': return <Briefcase className="w-5 h-5" />;
            case 'OFFER': return <CheckCircle className="w-5 h-5" />;
            case 'REJECTION': return <XCircle className="w-5 h-5" />;
            default: return <AlertCircle className="w-5 h-5" />;
        }
    };

    return (
        <div className="group relative bg-slate-800 hover:bg-slate-700/50 border border-slate-700 rounded-xl p-5 transition-all duration-200 hover:shadow-lg">
            <div className="flex items-start justify-between">
                <div className="flex gap-4">
                    <div className={cn("p-3 rounded-lg border", getStatusColor(event.event_type))}>
                        {getIcon(event.event_type)}
                    </div>
                    <div>
                        <h3 className="font-semibold text-lg text-white">{event.company || "Unknown Company"}</h3>
                        <p className="text-sm text-slate-400 font-medium">{event.event_type}</p>
                        <p className="text-sm text-slate-400 mt-1 line-clamp-2">{event.summary}</p>
                    </div>
                </div>
                <div className="text-xs text-slate-500 whitespace-nowrap">
                    {new Date(event.created_at).toLocaleDateString()}
                </div>
            </div>

            {event.research_briefing && (
                <div className="mt-4 pt-4 border-t border-slate-700/50">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">Research Briefing</h4>
                    <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">
                        {event.research_briefing}
                    </p>
                </div>
            )}
        </div>
    );
};

export default EventCard;
