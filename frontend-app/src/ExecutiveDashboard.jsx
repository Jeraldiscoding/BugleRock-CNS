import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const mockAUMData = [
  { name: 'Jan', aum: 800 },
  { name: 'Feb', aum: 820 },
  { name: 'Mar', aum: 810 },
  { name: 'Apr', aum: 860 },
  { name: 'May', aum: 920 },
  { name: 'Jun', aum: 980 },
  { name: 'Jul', aum: 1100 },
  { name: 'Aug', aum: 1150 },
  { name: 'Sep', aum: 1200 },
];

const mockDepartments = [
  {
    id: 'client_uhnw',
    name: 'Client & UHNW',
    managers: 'Dheeraj Bharwani',
    personnel: ['Mike Lim', 'Parvathy Srikant', 'Duresh Kumar', 'Subiksha'],
    leads: '18 New Leads',
    processing: '12 In Processing',
    actionText: '5 Awaiting Action',
    actionLabel: 'Bottleneck Detected',
    isAlert: true,
    activeText: '142 Active • $1.2B',
  },
  {
    id: 'investments',
    name: 'Investments',
    managers: 'Nikhil Arora',
    personnel: ['William', 'Rishav Baid', 'Jeremy Sim'],
    leads: '4 New Leads',
    processing: '8 In Processing',
    actionText: '2 Awaiting Action',
    actionLabel: null,
    isAlert: false,
    activeText: '1,240 Active • $450M',
  },
  {
    id: 'operations_compliance',
    name: 'Ops & Compliance',
    managers: 'Aditi Gautam & Stefan Ho',
    personnel: ['Nidhi Khemka', 'Zeel'],
    leads: '0 New Leads',
    processing: '12 In Processing',
    actionText: '8 Awaiting Action',
    actionLabel: 'High Volume',
    isAlert: true,
    activeText: '18 Active • $840M',
  },
  {
    id: 'research_strategy',
    name: 'Research & Strategy',
    managers: 'Sarah Chen',
    personnel: ['David Kim', 'Emma Watson'],
    leads: '12 New Leads',
    processing: '5 In Processing',
    actionText: '1 Awaiting Action',
    actionLabel: null,
    isAlert: false,
    activeText: '4 Active • $120M',
  },
  {
    id: 'corporate_dev',
    name: 'Corporate Dev',
    managers: 'Michael Chang',
    personnel: ['Lisa Wong', 'James Smith'],
    leads: '3 New Leads',
    processing: '2 In Processing',
    actionText: '0 Awaiting Action',
    actionLabel: null,
    isAlert: false,
    activeText: '2 Active • $85M',
  }
];

const mockEscalations = [
  {
    id: 1,
    client: 'Apex Corp',
    dept: 'Compliance',
    riskLabel: 'Compliance Risk',
    riskText: 'Missing KYC for Apex Corp. Routed to Stefan Ho (Compliance).',
    baseColor: 'error',
    icon: 'priority_high'
  },
  {
    id: 2,
    client: 'LexCorp',
    dept: 'Investments',
    riskLabel: 'Action Required',
    riskText: 'Urgent Portfolio Rebalance requested. Routed to Jeremy Sim (Investments).',
    baseColor: 'tertiary',
    icon: 'bar_chart'
  }
];

export default function ExecutiveDashboard() {
  const [activeView, setActiveView] = useState('overview'); // 'overview', 'department_detail', 'client'
  const [selectionContext, setSelectionContext] = useState(null);
  const [liveData, setLiveData] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:8005/api/state');
        const data = await response.json();
        setLiveData(data);
      } catch (err) {
        console.error("API not reachable yet", err);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleViewDepartment = (dept) => {
    setSelectionContext(dept);
    setActiveView('department_detail');
  };

  const handleViewClient = (client) => {
    setSelectionContext(client);
    setActiveView('client');
  };

  const handleBackToOverview = () => {
    setSelectionContext(null);
    setActiveView('overview');
  };

  if (!liveData) {
    return <div className="min-h-screen flex items-center justify-center bg-surface text-on-surface">Loading live dashboard...</div>;
  }

  return (
    <div className="bg-surface text-on-surface selection:bg-primary-container selection:text-on-primary-container min-h-screen font-body">
      
      {/* SideNavBar */}
      <aside className="flex flex-col fixed left-0 top-0 z-40 h-screen w-64 border-r border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 font-headline tracking-tight">
        <div className="p-6 flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-primary flex items-center justify-center">
            <span className="material-symbols-outlined text-white text-sm" data-icon="shield">shield</span>
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tighter text-slate-900 dark:text-white">BugleRock CNS</h1>
            <p className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Executive Command</p>
          </div>
        </div>
        <nav className="flex-1 px-3 mt-4 space-y-1">
          <button onClick={() => { setActiveView('overview'); setSelectionContext(null); }} className={`w-full flex items-center gap-3 py-2 -ml-3 pl-5 pr-3 ${activeView === 'overview' ? 'text-primary font-semibold border-l-4 border-primary bg-primary/10 rounded-r-md' : 'text-slate-500 hover:text-primary/70 hover:bg-primary/5 rounded-md border-l-4 border-transparent'} cursor-pointer active:scale-95 transition-all duration-200`}>
            <span className="material-symbols-outlined text-[20px]" data-icon="dashboard">dashboard</span>
            <span className="text-sm">Executive Overview</span>
          </button>
          <button onClick={() => { setActiveView('aum_pipeline'); setSelectionContext(null); }} className={`w-full flex items-center gap-3 py-2 -ml-3 pl-5 pr-3 ${activeView === 'aum_pipeline' ? 'text-primary font-semibold border-l-4 border-primary bg-primary/10 rounded-r-md' : 'text-slate-500 hover:text-primary/70 hover:bg-primary/5 rounded-md border-l-4 border-transparent'} cursor-pointer active:scale-95 transition-all duration-200`}>
            <span className="material-symbols-outlined text-[20px]" data-icon="account_balance_wallet">account_balance_wallet</span>
            <span className="text-sm">AUM Pipeline</span>
          </button>
        </nav>
        <div className="p-4 border-t border-slate-200 dark:border-slate-800">
          <div className="bg-white dark:bg-slate-900 p-3 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
              <span className="text-xs font-medium text-slate-600 dark:text-slate-400">System Status: Optimal</span>
            </div>
            <div className="w-full bg-slate-100 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div className="bg-primary h-full w-[94%]"></div>
            </div>
          </div>
          <div className="mt-4 space-y-1">
            <a className="flex items-center gap-3 px-3 py-2 text-slate-500 text-sm hover:text-slate-900 transition-colors" href="#">
              <span className="material-symbols-outlined text-[20px]" data-icon="settings">settings</span>
              <span>Settings</span>
            </a>
            <a className="flex items-center gap-3 px-3 py-2 text-slate-500 text-sm hover:text-slate-900 transition-colors" href="#">
              <span className="material-symbols-outlined text-[20px]" data-icon="help_center">help_center</span>
              <span>Support</span>
            </a>
          </div>
        </div>
      </aside>

      {/* TopNavBar */}
      <header className="flex items-center justify-between px-8 w-[calc(100%-16rem)] ml-64 fixed top-0 z-30 docked full-width h-16 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-100 dark:border-slate-800 shadow-sm dark:shadow-none font-headline font-medium text-sm">
        <div className="flex flex-1 items-center h-full max-w-xl">
          <div className="relative group flex w-full">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-primary transition-colors" data-icon="search">search</span>
            <input className="pl-10 pr-4 py-2 bg-surface-container-low border-none rounded-md text-sm w-full focus:ring-1 focus:ring-slate-200 transition-all outline-none" placeholder="Search systems..." type="text" />
          </div>
        </div>
        <div className="flex items-center gap-6 h-full justify-end">
          <div className="flex items-center gap-4 h-full">
            <button className="text-slate-500 hover:text-slate-900 transition-colors relative flex items-center justify-center">
              <span className="material-symbols-outlined" data-icon="notifications">notifications</span>
              <span className="absolute top-0 right-0 w-2 h-2 bg-error rounded-full border-2 border-white translate-x-1 -translate-y-0.5"></span>
            </button>
            <button className="text-slate-500 hover:text-slate-900 transition-colors flex items-center justify-center">
              <span className="material-symbols-outlined" data-icon="calendar_today">calendar_today</span>
            </button>
            <div className="h-8 w-[1px] bg-slate-200 mx-2"></div>
            <div className="flex items-center gap-3">
              <div className="text-right flex flex-col justify-center">
                <p className="text-xs font-bold text-slate-900 leading-tight">Nikhil Arora</p>
                <p className="text-[10px] text-slate-500 leading-tight">Managing Partner</p>
              </div>
              <img alt="CEO/Managing Partner" className="w-9 h-9 rounded-full object-cover ring-2 ring-slate-100" src="https://lh3.googleusercontent.com/aida-public/AB6AXuA8JEyj05f_zfRgDYKxmOewmKAxIcolUan2lW4xSBhoktMLAc_oR1m7dFOCZ8zmn_UW2JEBCCJS-bVeIv4an0kS7VDomDWa3q6IRgsuGEYzm3lGY2brdECqNGWw21XYvXKcXh6a9wrCU9n2F9KkngmHdpX40h2QsWnmkL441X5dBs_RHToFp_ZnJQYnw0J9MPjRh4ijM30ouIffpNPFm6Ua11HKOW6QKn2bDPOCBRRVANz9x9TFJHE73qIDH2zPeEBWI5zO1ssNFpw" />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="ml-64 pt-16 min-h-screen relative z-10">
        <div className="p-8 max-w-[1600px] mx-auto space-y-14">
          
          {activeView === 'department_detail' && selectionContext && (
            <div className="animate-fade-in space-y-8">
              {/* Header */}
              <div>
                <button 
                  onClick={handleBackToOverview}
                  className="mb-4 flex items-center gap-2 text-sm font-semibold text-primary hover:opacity-80 transition-opacity"
                >
                  <span className="material-symbols-outlined text-sm">arrow_back</span>
                  Back to Overview
                </button>
                <div className="flex items-center justify-between">
                  <h2 className="font-headline text-4xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50">{selectionContext.name} Department</h2>
                </div>
              </div>

              {/* Department Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-surface-container-lowest p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col gap-2 relative overflow-hidden group">
                  <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                  <span className="text-sm font-bold text-slate-500 uppercase tracking-wide">Active AUM</span>
                  <div className="flex items-end gap-2">
                    <span className="text-3xl font-bold text-slate-900 dark:text-slate-50">{selectionContext.activeText.includes('$') ? selectionContext.activeText.split('•')[1].trim() : '$1.2B'}</span>
                    <span className="text-sm font-medium text-emerald-600 mb-1">+4.2%</span>
                  </div>
                </div>

                <div className="bg-surface-container-lowest p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col gap-2 relative overflow-hidden group">
                  <div className="absolute inset-0 bg-gradient-to-r from-secondary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                  <span className="text-sm font-bold text-slate-500 uppercase tracking-wide">AI Efficiency Score</span>
                  <div className="flex items-end gap-2">
                    <span className="text-3xl font-bold text-slate-900 dark:text-slate-50">92%</span>
                    <span className="text-sm font-medium text-emerald-600 mb-1">+2.1%</span>
                  </div>
                </div>

                <div className="bg-tertiary-container/30 border-tertiary/20 p-6 rounded-2xl border shadow-sm flex flex-col gap-2 relative overflow-hidden group">
                  <div className="absolute inset-0 bg-gradient-to-r from-tertiary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                  <div className="flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-[16px] text-tertiary">priority_high</span>
                    <span className="text-sm font-bold text-tertiary uppercase tracking-wide">Pending Actions</span>
                  </div>
                  <div className="flex items-end gap-2">
                    <span className="text-3xl font-bold text-tertiary">{selectionContext.actionText.split(' ')[0] || '3'}</span>
                    <span className="text-sm font-medium text-tertiary opacity-80 mb-1">items bottlenecked</span>
                  </div>
                </div>
              </div>

              {/* Team Personnel Grid */}
              <div className="bg-surface-container-lowest p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
                <h3 className="font-headline text-xl font-bold text-slate-900 dark:text-slate-50 mb-4">Team Personnel</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
                  {(() => {
                    const getInitials = (name) => name.split(' ').map(n => n[0]).join('').substring(0, 2);
                    const members = {
                      client_uhnw: [
                        { name: 'Dheeraj Bharwani', role: 'CIO/MD' },
                        { name: 'Mike Lim', role: 'Team' },
                        { name: 'Parvathy Srikant', role: 'Team' },
                        { name: 'Duresh Kumar', role: 'Team' },
                        { name: 'Subiksha', role: 'AVP' }
                      ],
                      investments: [
                        { name: 'Nikhil Arora', role: 'Head' },
                        { name: 'William', role: 'Team' },
                        { name: 'Rishav Baid', role: 'Team' },
                        { name: 'Jeremy Sim', role: 'Team' }
                      ],
                      operations_compliance: [
                        { name: 'Aditi Gautam', role: 'Head of Ops' },
                        { name: 'Stefan Ho', role: 'Head of Risk' },
                        { name: 'Zeel', role: 'Team' },
                        { name: 'Nidhi Khemka', role: 'Team' }
                      ]
                    };
                    const team = members[selectionContext.id] || [];
                    return team.map((m, i) => (
                      <div key={i} className="flex items-center gap-3 bg-slate-50 dark:bg-slate-900 p-3 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md transition-shadow">
                        <div className="w-10 h-10 shrink-0 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center font-bold text-sm">
                          {getInitials(m.name)}
                        </div>
                        <div className="truncate">
                          <div className="text-sm font-bold text-slate-900 dark:text-slate-50 truncate">{m.name}</div>
                          <div className="text-xs text-slate-500 truncate">{m.role}</div>
                        </div>
                      </div>
                    ));
                  })()}
                </div>
              </div>

              {/* The Pipeline (Kanban Style) */}
              <div className="bg-surface-container-lowest p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden flex flex-col">
                <h3 className="font-headline text-xl font-bold text-slate-900 dark:text-slate-50 mb-6 tracking-tight">Active Pipeline</h3>
                
                <div className="flex-1 overflow-x-auto pb-4">
                  <div className="flex gap-6 min-w-max h-full">
                    {/* Column 1: AI Triage */}
                    <div className="w-72 bg-slate-50/50 dark:bg-slate-900/50 rounded-xl p-4 border border-slate-100 dark:border-slate-800/50 flex flex-col gap-4">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="material-symbols-outlined text-secondary text-sm" data-icon="filter_alt">filter_alt</span>
                        <h4 className="font-bold text-sm text-slate-700 dark:text-slate-300">AI Triage</h4>
                        <span className="ml-auto bg-slate-200 dark:bg-slate-800 text-xs px-2 py-0.5 rounded-full text-slate-600">2</span>
                      </div>
                      
                      {/* Card */}
                      <div 
                        onClick={() => handleViewClient({ client: 'Bruce Wayne', dept: selectionContext.name })}
                        className={`p-4 rounded-lg shadow-sm cursor-pointer transition-all group ${
                          liveData.clients?.['Bruce Wayne']?.status === 'Compliance Hold'
                            ? 'bg-error/5 border-2 border-error/60 shadow-[0_0_15px_rgba(220,38,38,0.15)] animate-pulse hover:shadow-md'
                            : 'bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 hover:border-primary/50 hover:shadow-md'
                        }`}
                      >
                        <div className={`font-bold text-sm transition-colors ${
                           liveData.clients?.['Bruce Wayne']?.status === 'Compliance Hold' 
                             ? 'text-error group-hover:text-error/80' 
                             : 'text-slate-900 dark:text-slate-100 group-hover:text-primary'
                        }`}>
                          Bruce Wayne
                          {liveData.clients?.['Bruce Wayne']?.status === 'Compliance Hold' && " [ALERT]"}
                        </div>
                        <p className="text-xs text-slate-500 mt-2 line-clamp-2">{liveData.clients?.['Bruce Wayne']?.module_a_insight || "Module A: Evaluating intent from email..."}</p>
                      </div>

                      <div 
                        onClick={() => handleViewClient({ client: 'Stark Industries', dept: selectionContext.name })}
                        className="bg-white dark:bg-slate-950 p-4 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm hover:border-primary/50 hover:shadow-md cursor-pointer transition-all group"
                      >
                        <div className="font-bold text-sm text-slate-900 dark:text-slate-100 group-hover:text-primary transition-colors">Stark Industries</div>
                        <p className="text-xs text-slate-500 mt-2 line-clamp-2">Module A: Sorting attachments...</p>
                      </div>
                    </div>

                    {/* Column 2: AI Analysis */}
                    <div className="w-72 bg-slate-50/50 dark:bg-slate-900/50 rounded-xl p-4 border border-slate-100 dark:border-slate-800/50 flex flex-col gap-4">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="material-symbols-outlined text-primary text-sm" data-icon="memory">memory</span>
                        <h4 className="font-bold text-sm text-slate-700 dark:text-slate-300">AI Analysis</h4>
                        <span className="ml-auto bg-slate-200 dark:bg-slate-800 text-xs px-2 py-0.5 rounded-full text-slate-600">1</span>
                      </div>

                      <div 
                        onClick={() => handleViewClient({ client: 'Apex Corp', dept: selectionContext.name })}
                        className="bg-white dark:bg-slate-950 p-4 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm hover:border-primary/50 hover:shadow-md cursor-pointer transition-all group"
                      >
                        <div className="font-bold text-sm text-slate-900 dark:text-slate-100 group-hover:text-primary transition-colors">Apex Corp</div>
                        <p className="text-xs text-slate-500 mt-2 line-clamp-2">Module C: Extracting action items from transcripts...</p>
                        <div className="mt-3 bg-primary/10 rounded-full h-1 w-full overflow-hidden">
                          <div className="bg-primary h-full w-[60%]"></div>
                        </div>
                      </div>
                    </div>

                    {/* Column 3: Advisor Action */}
                    <div className="w-72 bg-tertiary/5 rounded-xl p-4 border border-tertiary/20 flex flex-col gap-4">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="material-symbols-outlined text-tertiary text-sm" data-icon="person_alert">person_alert</span>
                        <h4 className="font-bold text-sm text-tertiary">Advisor Action</h4>
                        <span className="ml-auto bg-tertiary/20 text-xs px-2 py-0.5 rounded-full text-tertiary">1</span>
                      </div>
                      
                      <div 
                        onClick={() => handleViewClient({ client: 'LexCorp', dept: selectionContext.name })}
                        className="bg-white dark:bg-slate-950 p-4 rounded-lg border border-tertiary/40 shadow-sm hover:border-tertiary hover:shadow-md cursor-pointer transition-all group ring-1 ring-tertiary/10"
                      >
                        <div className="flex items-start justify-between">
                          <div className="font-bold text-sm text-slate-900 dark:text-slate-100 group-hover:text-tertiary transition-colors">LexCorp</div>
                          <span className="flex h-2 w-2 relative">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-tertiary opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-tertiary"></span>
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 dark:text-slate-400 mt-2 font-medium">Draft ready. Awaiting Advisor Review (Subiksha).</p>
                        <div className="mt-4 flex gap-2">
                          <button className="flex-1 bg-tertiary text-on-tertiary text-[10px] uppercase font-bold py-1.5 rounded hover:bg-tertiary/90 transition-colors">Review</button>
                        </div>
                      </div>
                    </div>

                    {/* Column 4: Closed/Active */}
                    <div className="w-72 bg-slate-50/50 dark:bg-slate-900/50 rounded-xl p-4 border border-slate-100 dark:border-slate-800/50 flex flex-col gap-4">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="material-symbols-outlined text-emerald-600 text-sm" data-icon="check_circle">check_circle</span>
                        <h4 className="font-bold text-sm text-slate-700 dark:text-slate-300">Closed / Active</h4>
                        <span className="ml-auto bg-slate-200 dark:bg-slate-800 text-xs px-2 py-0.5 rounded-full text-slate-600">1</span>
                      </div>
                      
                      <div 
                        onClick={() => handleViewClient({ client: 'Wayne Enterprises', dept: selectionContext.name })}
                        className="bg-white dark:bg-slate-950 p-4 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm hover:border-emerald-600/50 hover:shadow-md cursor-pointer transition-all opacity-80 group"
                      >
                        <div className="font-bold text-sm text-slate-900 dark:text-slate-100 group-hover:text-emerald-600 transition-colors">Wayne Enterprises</div>
                        <p className="text-xs text-slate-500 mt-2">Completed successfully.</p>
                      </div>
                    </div>

                  </div>
                </div>
              </div>
            </div>
          )}

          {activeView === 'client' && selectionContext && (
            <div className="animate-fade-in space-y-6">
              {/* Header & Navigation */}
              <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-2">
                <div>
                  <div className="flex items-center gap-2 text-sm text-slate-500 mb-4">
                    <button onClick={handleBackToOverview} className="hover:text-primary transition-colors">Executive Overview</button>
                    <span className="material-symbols-outlined text-[14px]">chevron_right</span>
                    <button onClick={() => {
                        handleBackToOverview();
                    }} className="hover:text-primary transition-colors">{selectionContext.dept || 'Client Strategy'}</button>
                    <span className="material-symbols-outlined text-[14px]">chevron_right</span>
                    <span className="font-semibold text-slate-900 dark:text-slate-100">{selectionContext.client}</span>
                  </div>
                  <h2 className="font-headline text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50">{selectionContext.client}</h2>
                </div>
                <div className="flex flex-wrap gap-3">
                  <button className="px-4 py-2 text-sm font-semibold text-primary border border-primary/20 bg-primary/5 rounded-lg hover:bg-primary/10 transition-colors flex items-center gap-2">
                    <span className="material-symbols-outlined text-[18px]">auto_awesome</span>
                    Generate AI Report
                  </button>
                  <button className="px-4 py-2 text-sm font-semibold text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-800 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-900 transition-colors flex items-center gap-2">
                    <span className="material-symbols-outlined text-[18px]">open_in_new</span>
                    Open in Zoho CRM
                  </button>
                  <button className="px-4 py-2 text-sm font-semibold text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-800 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-900 transition-colors flex items-center gap-2">
                    <span className="material-symbols-outlined text-[18px]">forum</span>
                    View Slack Thread
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Column 1: Client Profile & Risk */}
                <div className="space-y-6">
                  {/* Client Profile Card */}
                  <div className="bg-surface-container-lowest p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col items-center text-center">
                    <div className="w-20 h-20 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center font-bold text-2xl mb-4 shadow-inner">
                      {selectionContext.client.split(' ').map(n => n[0]).join('').substring(0,2)}
                    </div>
                    <h3 className="font-headline text-xl font-bold text-slate-900 dark:text-slate-50">{selectionContext.client}</h3>
                    {liveData.clients?.[selectionContext.client]?.status === 'Compliance Hold' ? (
                      <div className="inline-flex mt-2 px-3 py-1 bg-error/10 text-error text-xs font-bold uppercase tracking-wider rounded-full border border-error/50 items-center justify-center gap-1 animate-pulse">
                        <span className="material-symbols-outlined text-[14px]">gavel</span>
                        <span>COMPLIANCE HOLD</span>
                      </div>
                    ) : (
                      <span className="inline-block mt-2 px-3 py-1 bg-tertiary/10 text-tertiary text-xs font-bold uppercase tracking-wider rounded-full">Awaiting Advisor Review</span>
                    )}
                    
                    <div className="w-full mt-6 space-y-4 text-left">
                      <div className="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-800/50">
                        <span className="text-sm text-slate-500">Net Worth / AUM</span>
                        <span className="text-sm font-bold text-slate-900 dark:text-slate-50">$25.4M</span>
                      </div>
                      <div className="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-800/50">
                        <span className="text-sm text-slate-500">Primary Advisor</span>
                        <span className="text-sm font-bold text-slate-900 dark:text-slate-50">Subiksha</span>
                      </div>
                      <div className="flex justify-between items-center py-2">
                        <span className="text-sm text-slate-500">Department</span>
                        <span className="text-sm font-bold text-slate-900 dark:text-slate-50">{selectionContext.dept || 'Client Strategy'}</span>
                      </div>
                    </div>
                  </div>

                  {/* Global Risk Status */}
                  <div className="bg-surface-container-lowest p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
                    <div className="flex items-center gap-2 mb-4">
                      <span className="material-symbols-outlined text-secondary">verified_user</span>
                      <h3 className="font-headline font-bold text-slate-900 dark:text-slate-50">Compliance & Risk</h3>
                    </div>
                    <p className="text-xs text-slate-500 mb-4 pb-4 border-b border-slate-100 dark:border-slate-800/50">
                      Assessment verified by <strong className="text-slate-700 dark:text-slate-300">Stefan Ho (Head of Risk)</strong>.
                    </p>
                    <ul className="space-y-3">
                      <li className="flex items-start gap-2">
                        <span className="material-symbols-outlined text-emerald-600 text-sm mt-0.5">check_circle</span>
                        <span className="text-sm text-slate-700 dark:text-slate-300">KYC up to date (Verified)</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="material-symbols-outlined text-tertiary text-sm mt-0.5">priority_high</span>
                        <span className="text-sm text-slate-700 dark:text-slate-300">Portfolio Drift: <strong className="text-tertiary">4.2%</strong></span>
                      </li>
                    </ul>
                  </div>
                </div>

                {/* Column 2 & 3: Intelligence Modules */}
                <div className="lg:col-span-2 space-y-6">
                  {/* Module A: Email Intelligence */}
                  <div className="bg-surface-container-lowest rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
                    <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800/50 flex items-center justify-between bg-slate-50/50 dark:bg-slate-900/50">
                      <div className="flex items-center gap-2">
                        <span className="material-symbols-outlined text-primary text-[20px]">mail</span>
                        <h3 className="font-headline font-bold text-slate-900 dark:text-slate-50">Recent Communications (Module A)</h3>
                      </div>
                      <span className="bg-error/10 text-error text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1">
                        <span className="material-symbols-outlined text-[14px]">priority_high</span>
                        AI Triage: High Urgency
                      </span>
                    </div>
                    <div className="p-6">
                      <div className="bg-white dark:bg-slate-950 p-4 rounded-xl border border-slate-200 dark:border-slate-800/80 shadow-inner relative">
                        <div className="absolute top-0 left-0 w-1 h-full bg-primary rounded-l-xl"></div>
                        <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Latest Email Summary</h4>
                        <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed italic">
                          "{selectionContext.client === 'Bruce Wayne' && liveData?.clients?.['Bruce Wayne']?.module_a_insight ? liveData.clients['Bruce Wayne'].module_a_insight : 'Client expressed interest in Q3 Rebalancing; urgent tone detected regarding tech sector volatility.'}"
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Module C: Meeting Intelligence */}
                  <div className="bg-surface-container-lowest rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
                    <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800/50 flex items-center justify-between bg-slate-50/50 dark:bg-slate-900/50">
                      <div className="flex items-center gap-2">
                        <span className="material-symbols-outlined text-secondary text-[20px]">graphic_eq</span>
                        <h3 className="font-headline font-bold text-slate-900 dark:text-slate-50">Meeting Insights (Module C)</h3>
                      </div>
                      <div className="flex items-center gap-2 text-sm bg-secondary/10 px-3 py-1 rounded-full">
                        <span className="text-secondary font-bold">Sentiment:</span>
                        <span className="text-slate-700 dark:text-slate-300 font-medium">Cautious Tracker</span>
                        <div className="w-16 h-2 bg-slate-200 rounded-full overflow-hidden ml-1">
                          <div className="w-2/3 h-full bg-secondary"></div>
                        </div>
                      </div>
                    </div>
                    <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-slate-50 mb-4">
                          <span className="material-symbols-outlined text-[18px] text-slate-400">notes</span>
                          Transcript Summary
                        </h4>
                        <ul className="space-y-3">
                          {selectionContext.client === 'Bruce Wayne' && liveData.clients?.['Bruce Wayne'] ? (
                            <li className="flex items-start gap-2">
                              <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 shrink-0"></div>
                              <span className="text-sm text-slate-600 dark:text-slate-400">{liveData.clients['Bruce Wayne'].module_c_insight}</span>
                            </li>
                          ) : (
                            <>
                              <li className="flex items-start gap-2">
                                <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 shrink-0"></div>
                                <span className="text-sm text-slate-600 dark:text-slate-400">Concerned about volatility in tech sector.</span>
                              </li>
                              <li className="flex items-start gap-2">
                                <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 shrink-0"></div>
                                <span className="text-sm text-slate-600 dark:text-slate-400">Requested overview of venture debt holdings.</span>
                              </li>
                              <li className="flex items-start gap-2">
                                <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 shrink-0"></div>
                                <span className="text-sm text-slate-600 dark:text-slate-400">Discussed family trust structures for next fiscal year.</span>
                              </li>
                            </>
                          )}
                        </ul>
                      </div>

                      <div className="bg-slate-50 dark:bg-slate-900/50 p-5 rounded-xl border border-slate-100 dark:border-slate-800/50">
                        <h4 className="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-slate-50 mb-4">
                          <span className="material-symbols-outlined text-[18px] text-tertiary">task_alt</span>
                          AI Identified Action Items
                        </h4>
                        <div className="space-y-3">
                          <label className="flex items-start gap-3 cursor-pointer group">
                            <input type="checkbox" className="mt-0.5 rounded border-slate-300 text-primary focus:ring-primary" />
                            <span className="text-sm text-slate-700 dark:text-slate-300 group-hover:text-primary transition-colors">Draft rebalancing proposal</span>
                          </label>
                          <label className="flex items-start gap-3 cursor-pointer group">
                            <input type="checkbox" className="mt-0.5 rounded border-slate-300 text-primary focus:ring-primary" />
                            <span className="text-sm text-slate-700 dark:text-slate-300 group-hover:text-primary transition-colors">Schedule follow-up with <strong className="text-slate-900 dark:text-slate-100">Stefan Ho</strong></span>
                          </label>
                          <label className="flex items-start gap-3 cursor-pointer group">
                            <input type="checkbox" className="mt-0.5 rounded border-slate-300 text-primary focus:ring-primary" defaultChecked />
                            <span className="text-sm text-slate-700 dark:text-slate-300 line-through opacity-60">Send Q2 tax documents to accountant</span>
                          </label>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeView === 'aum_pipeline' && (
            <div className="animate-fade-in space-y-8">
              <div className="flex justify-between items-end">
                <div>
                  <h2 className="font-headline text-3xl font-extrabold tracking-tight text-on-surface">Capital Allocation Pipeline</h2>
                  <p className="text-on-surface-variant font-medium mt-1">AUM Growth and Pipeline Overview</p>
                </div>
              </div>
              
              {/* Chart */}
              <div className="bg-surface-container-lowest p-6 rounded-2xl border border-outline-variant/10 shadow-sm flex flex-col h-80">
                <div className="mb-4">
                  <h3 className="font-headline text-xl font-bold text-on-surface">AUM Growth Chart</h3>
                </div>
                <div className="flex-1 w-full min-h-0">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={mockAUMData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorAum" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} dy={10} />
                      <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} tickFormatter={(val) => `$${val}M`} />
                      <Tooltip 
                        contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                        itemStyle={{ color: '#0f172a', fontWeight: 'bold' }}
                        formatter={(val) => [`$${val}M`, 'AUM']} 
                      />
                      <Area type="monotone" dataKey="aum" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorAum)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Departmental Pipeline Heatmap */}
              <section className="space-y-6">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary" data-icon="grid_view">grid_view</span>
                  <h3 className="font-headline text-2xl font-bold text-on-surface">Departmental Pipeline Heatmap</h3>
                </div>
                <div className="bg-surface-container-lowest rounded-xl overflow-hidden shadow-sm border border-outline-variant/5">
                  <table className="w-full text-left border-collapse text-lg">
                    <thead>
                      <tr className="bg-surface-container-low/50">
                        <th className="p-6 font-bold text-on-surface-variant uppercase tracking-wider border-b border-outline-variant/10">Department</th>
                        <th className="p-6 font-bold text-on-surface-variant uppercase tracking-wider border-b border-outline-variant/10">New Leads</th>
                        <th className="p-6 font-bold text-on-surface-variant uppercase tracking-wider border-b border-outline-variant/10">In Processing</th>
                        <th className="p-6 font-bold text-on-surface-variant uppercase tracking-wider border-b border-outline-variant/10">Awaiting Action</th>
                        <th className="p-6 font-bold text-on-surface-variant uppercase tracking-wider border-b border-outline-variant/10">Active AUM</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-outline-variant/10">
                      {mockDepartments.map((dept) => (
                        <tr key={dept.id} onClick={() => handleViewDepartment(dept)} className="cursor-pointer hover:bg-slate-50 hover:shadow-sm transition-all group">
                          <td className="p-6 font-bold text-on-surface flex items-center justify-between">
                            {dept.name}
                            <span className="material-symbols-outlined opacity-0 group-hover:opacity-100 text-primary transition-opacity ml-2">chevron_right</span>
                          </td>
                          <td className="p-6 text-center">
                            <span className="bg-blue-50 text-blue-700 px-3 py-1 rounded-md font-medium inline-block">{dept.leads}</span>
                          </td>
                          <td className="p-6 text-center">
                            <span className="bg-indigo-50 text-indigo-700 px-3 py-1 rounded-md font-medium inline-block">{dept.processing}</span>
                          </td>
                          <td className={`p-6 ${dept.isAlert ? 'bg-orange-50/50' : ''}`}>
                            <div className="flex items-center gap-2">
                              {dept.isAlert && <div className="w-2 h-2 rounded-full bg-orange-600"></div>}
                              <span className={`${dept.isAlert ? 'font-semibold text-orange-700' : 'text-slate-600 font-medium'}`}>{dept.actionText}</span>
                            </div>
                            {dept.actionLabel && (
                              <p className="text-xs text-orange-600/80 mt-1 uppercase font-bold tracking-tighter">{dept.actionLabel}</p>
                            )}
                          </td>
                          <td className="p-6 text-slate-900 font-extrabold text-base">{dept.activeText}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </div>
          )}

          {activeView === 'overview' && (
            <div className="animate-fade-in space-y-8">
              {/* Welcome Header */}
              <div className="flex justify-between items-end">
                <div>
                  <h2 className="font-headline text-3xl font-extrabold tracking-tight text-on-surface">Command Overview</h2>
                  <p className="text-on-surface-variant font-medium mt-1">Real-time operational status for Q3 FY24</p>
                </div>
                <div className="flex gap-3">
                  <button className="px-4 py-2 text-sm font-semibold text-primary border border-outline-variant/20 rounded-lg hover:bg-surface-container-low transition-colors">
                      Export Report
                  </button>
                  <button className="px-4 py-2 text-sm font-semibold text-on-primary bg-primary rounded-lg hover:opacity-90 transition-opacity flex items-center gap-2">
                    <span className="material-symbols-outlined text-sm" data-icon="add">add</span>
                    New Strategy
                  </button>
                </div>
              </div>

              {/* KPI Row */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-surface-container-lowest p-6 rounded-xl transition-all hover:shadow-sm border border-transparent">
                  <p className="text-xs font-medium text-on-surface-variant mb-4 flex items-center justify-between">
                    Total AUM in Pipeline
                    <span className="text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded text-[10px] font-bold">+12%</span>
                  </p>
                  <h3 className="font-headline text-3xl font-bold text-on-surface">$42.5M</h3>
                  <div className="mt-4 h-1 w-full bg-surface-container-low rounded-full overflow-hidden">
                    <div className="bg-primary h-full w-2/3"></div>
                  </div>
                </div>

                <div className="bg-surface-container-lowest p-6 rounded-xl transition-all hover:shadow-sm border border-transparent">
                  <p className="text-xs font-medium text-on-surface-variant mb-4 flex items-center justify-between">
                    AI Triage Volume
                    <span className="material-symbols-outlined text-slate-400 text-sm" data-icon="info">info</span>
                  </p>
                  <h3 className="font-headline text-3xl font-bold text-on-surface">{liveData.kpis.triage_volume} <span className="text-sm font-normal text-on-surface-variant">handled</span></h3>
                  <div className="mt-4 flex gap-1 items-end h-8">
                    <div className="bg-primary/20 w-full h-[40%] rounded-t-sm"></div>
                    <div className="bg-primary/20 w-full h-[60%] rounded-t-sm"></div>
                    <div className="bg-primary/20 w-full h-[55%] rounded-t-sm"></div>
                    <div className="bg-primary/20 w-full h-[80%] rounded-t-sm"></div>
                    <div className="bg-primary/20 w-full h-[70%] rounded-t-sm"></div>
                    <div className="bg-primary w-full h-[95%] rounded-t-sm"></div>
                  </div>
                </div>

                <div className="bg-surface-container-lowest p-6 rounded-xl transition-all hover:shadow-sm border border-transparent">
                  <p className="text-xs font-medium text-on-surface-variant mb-4">Manual Hours Saved</p>
                  <h3 className="font-headline text-3xl font-bold text-on-surface">124 hrs</h3>
                  <p className="text-[10px] text-on-surface-variant mt-2 font-medium tracking-wide uppercase">Performance Period: This Month</p>
                </div>

                <div className="bg-surface-container-lowest p-6 rounded-xl transition-all hover:shadow-sm border border-transparent ring-1 ring-error/10">
                  <p className="text-xs font-medium text-error mb-4 flex items-center gap-2">
                    <span className="material-symbols-outlined text-sm" data-icon="report">report</span>
                    Critical Risk Flags
                  </p>
                  <h3 className="font-headline text-3xl font-bold text-error">{liveData.kpis.risk_flags || 0}</h3>
                  <p className="text-[10px] text-error/60 mt-2 font-medium uppercase">Requires Immediate Review</p>
                </div>
              </div>

              {/* Heatmap Table Section */}
              <section className="space-y-6">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary" data-icon="grid_view">grid_view</span>
                  <h3 className="font-headline text-lg font-bold text-on-surface">Departmental Pipeline Heatmap</h3>
                </div>
                <div className="bg-surface-container-lowest rounded-xl overflow-hidden shadow-sm border border-outline-variant/5">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-surface-container-low/50">
                        <th className="p-5 text-xs font-bold text-on-surface-variant uppercase tracking-wider border-b border-outline-variant/10">Department</th>
                        <th className="p-5 text-xs font-bold text-on-surface-variant uppercase tracking-wider border-b border-outline-variant/10">New Leads (AI Triage)</th>
                        <th className="p-5 text-xs font-bold text-on-surface-variant uppercase tracking-wider border-b border-outline-variant/10">AI Processing</th>
                        <th className="p-5 text-xs font-bold text-on-surface-variant uppercase tracking-wider border-b border-outline-variant/10">Awaiting Advisor Action</th>
                        <th className="p-5 text-xs font-bold text-on-surface-variant uppercase tracking-wider border-b border-outline-variant/10">Closed/Active</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-outline-variant/10">
                      {mockDepartments.map((dept) => (
                        <tr key={dept.id} onClick={() => handleViewDepartment(dept)} className="cursor-pointer hover:bg-slate-50 hover:shadow-sm transition-all group">
                          <td className="p-5 font-bold text-on-surface flex items-center justify-between">
                            {dept.name}
                            <span className="material-symbols-outlined opacity-0 group-hover:opacity-100 text-primary transition-opacity text-sm ml-2">chevron_right</span>
                          </td>
                          <td className="p-5 text-center">
                            <span className="bg-blue-50 text-blue-700 px-2.5 py-1 rounded-md text-sm font-medium inline-block">{dept.leads}</span>
                          </td>
                          <td className="p-5 text-center">
                            <span className="bg-indigo-50 text-indigo-700 px-2.5 py-1 rounded-md text-sm font-medium inline-block">{dept.processing}</span>
                          </td>
                          <td className={`p-5 ${dept.isAlert ? 'bg-orange-50/50' : ''}`}>
                            <div className="flex items-center gap-2">
                              {dept.isAlert && <div className="w-1.5 h-1.5 rounded-full bg-orange-600"></div>}
                              <span className={`text-sm ${dept.isAlert ? 'font-semibold text-orange-700' : 'text-slate-600 font-medium'}`}>{dept.actionText}</span>
                            </div>
                            {dept.actionLabel && (
                              <p className="text-[10px] text-orange-600/80 mt-1 uppercase font-bold tracking-tighter">{dept.actionLabel}</p>
                            )}
                          </td>
                          <td className="p-5 text-base text-slate-900 font-extrabold">{dept.activeText}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>

              {/* AI Escalation Desk Section */}
              <section className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-error" data-icon="emergency">emergency</span>
                    <h3 className="font-headline text-lg font-bold text-on-surface">AI Escalation Desk</h3>
                  </div>
                  <span className="text-[10px] font-bold text-on-surface-variant bg-surface-container-low px-2 py-1 rounded">Last Update: Just now</span>
                </div>
                <div className="space-y-3">
                  {mockEscalations.map((esc) => (
                    <div key={esc.id} className={`flex items-center justify-between p-4 bg-surface-container-low rounded-lg border-l-4 border-${esc.baseColor} relative group transition-all hover:bg-surface-container-high/50`}>
                      <div className="flex items-center gap-8">
                        <div className="space-y-1">
                          <p className="text-[10px] uppercase tracking-widest text-on-surface-variant font-bold">Client Entity</p>
                          <p className="text-sm font-bold text-on-surface">{esc.client}</p>
                        </div>
                        <div className="space-y-1">
                          <p className="text-[10px] uppercase tracking-widest text-on-surface-variant font-bold">Department</p>
                          <p className="text-sm font-medium text-on-surface">{esc.dept}</p>
                        </div>
                        <div className="space-y-1 max-w-xl">
                          <div className="flex items-center gap-1">
                            {esc.icon && <span className={`material-symbols-outlined text-[14px] text-${esc.baseColor}`}>{esc.icon}</span>}
                            <p className={`text-[10px] uppercase tracking-widest text-${esc.baseColor} font-bold`}>{esc.riskLabel}</p>
                          </div>
                          <p className="text-sm text-on-surface-variant font-medium">{esc.riskText}</p>
                        </div>
                      </div>
                      <button onClick={() => handleViewClient(esc)} className="px-5 py-2 text-xs font-bold text-primary border border-primary/20 bg-white rounded-md hover:bg-primary hover:text-white transition-all">
                        View Details
                      </button>
                    </div>
                  ))}
                </div>
              </section>
            </div>
          )}
        </div>
      </main>

      {/* Visual Texture / Background Gradients */}
      <div className="fixed top-0 right-0 -z-10 w-1/2 h-1/2 bg-gradient-to-bl from-primary/5 to-transparent blur-3xl pointer-events-none"></div>
      <div className="fixed bottom-0 left-0 -z-10 w-1/3 h-1/3 bg-gradient-to-tr from-secondary/5 to-transparent blur-3xl pointer-events-none"></div>
    </div>
  );
}
