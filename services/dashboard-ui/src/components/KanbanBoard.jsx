import React from 'react';

const KanbanColumn = ({ title, items, color }) => (
    <div className="flex-1 min-w-[300px] bg-slate-800 rounded-xl p-4 border border-slate-700">
        <div className={`flex items-center gap-2 mb-4 pb-3 border-b border-slate-700`}>
            <div className={`w-3 h-3 rounded-full ${color}`}></div>
            <h3 className="font-semibold text-slate-200">{title}</h3>
            <span className="ml-auto text-xs bg-slate-700 px-2 py-1 rounded-full text-slate-400">
                {items.length}
            </span>
        </div>
        <div className="space-y-3">
            {items.map((item) => (
                <div key={item.id} className="bg-slate-700 p-3 rounded-lg border border-slate-600 hover:border-slate-500 transition-colors cursor-pointer">
                    <h4 className="font-medium text-white">{item.company}</h4>
                    <p className="text-sm text-slate-400 mt-1">{item.role}</p>
                    <div className="flex items-center justify-between mt-3">
                        <span className="text-xs text-slate-500">
                            {new Date(item.created_at).toLocaleDateString()}
                        </span>
                        {item.confidence && (
                            <span className="text-xs bg-blue-500/10 text-blue-400 px-2 py-1 rounded">
                                {Math.round(item.confidence * 100)}% Match
                            </span>
                        )}
                    </div>
                </div>
            ))}
            {items.length === 0 && (
                <div className="text-center py-8 text-slate-500 text-sm italic">
                    No applications
                </div>
            )}
        </div>
    </div>
);

const KanbanBoard = ({ applications }) => {
    const columns = [
        { title: 'Applied / Detected', status: 'APPLIED', color: 'bg-blue-500' }, // Also includes UNKNOWN or others
        { title: 'Interviews', status: 'INTERVIEW', color: 'bg-purple-500' },
        { title: 'Offers', status: 'OFFER', color: 'bg-green-500' },
        { title: 'Rejections', status: 'REJECTION', color: 'bg-red-500' },
    ];

    const getItems = (status) => {
        if (status === 'APPLIED') {
            return applications.filter(a => !['INTERVIEW', 'OFFER', 'REJECTION'].includes(a.status));
        }
        return applications.filter(a => a.status === status);
    };

    return (
        <div className="flex gap-6 overflow-x-auto pb-6">
            {columns.map(col => (
                <KanbanColumn
                    key={col.status}
                    title={col.title}
                    color={col.color}
                    items={getItems(col.status)}
                />
            ))}
        </div>
    );
};

export default KanbanBoard;
