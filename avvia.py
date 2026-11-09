#!/usr/bin/env python3
"""
Unico file da lanciare per far funzionare l'app "Academy Soccer Ercolano 2019".

Fa tre cose in una:
1. Avvia un server web locale su http://localhost:8765
2. Serve l'app HTML/React (incorporata sotto)
3. Inoltra le richieste al sito csaincampania.it aggiungendo i header CORS,
   così il browser può leggere classifica e calendario senza errori.

Uso:
    python avvia.py
Poi apri il browser su: http://localhost:8765
"""

import os
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

TARGET = "https://www.csaincampania.it"
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 18765))


HTML = r"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Academy Soccer Ercolano 2019</title>

    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>

    <!-- React & ReactDOM -->
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>

    <!-- Babel (per compilare il codice React nel browser) -->
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>


    <style>
        body { margin: 0; padding: 0; background-color: #F8FAFC; }
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
    </style>
</head>
<body>
    <div id="root"></div>


    <script type="text/babel">
        const { useState, useEffect } = React;


        // ================= CONFIGURAZIONE =================
        const TARGET = 'https://www.csaincampania.it';
        const TOURNAMENT_ID = '47';
        /*
         * PROXY_URL punta al server locale avviato da avvia.py.
         * Tutto parte dallo stesso indirizzo (localhost), quindi non ci sono
         * problemi di CORS: il server inoltra le richieste al sito target.
         */
        const PROXY_URL = '/proxy';

        // Icone SVG
        const IconTrophy = ({ className }) => (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/></svg>
        );
        const IconCalendarDays = ({ className }) => (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/><path d="M8 14h.01"/><path d="M12 14h.01"/><path d="M16 14h.01"/><path d="M8 18h.01"/><path d="M12 18h.01"/><path d="M16 18h.01"/></svg>
        );
        const IconCalendar = ({ className }) => (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/></svg>
        );
        const IconRefresh = ({ className }) => (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
        );
        const IconAlert = ({ className }) => (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>
        );


        function App() {
            const [activeTab, setActiveTab] = useState('classifica');
            const [standings, setStandings] = useState([]);
            const [results, setResults] = useState([]);
            const [calendar, setCalendar] = useState([]);
            const [isLoading, setIsLoading] = useState(true);
            const [error, setError] = useState('');


            // Dati di emergenza (usati se il sito non è raggiungibile)
            const MOCK_STANDINGS = [
                { id: 1, rank: 1, name: 'Academy Soccer Ercolano', points: '0' },
                { id: 2, rank: 2, name: 'FALCONE', points: '0' },
                { id: 3, rank: 3, name: 'FC PARAISO', points: '0' },
                { id: 4, rank: 4, name: 'FOOTBALL ACADEMY NERA', points: '0' },
                { id: 5, rank: 5, name: 'FOOTBALL ACADEMY ROSSA', points: '0' },
                { id: 6, rank: 6, name: 'IN GRUPPO PER CRESCERE', points: '0' },
                { id: 7, rank: 7, name: 'MARIGLIANELLA', points: '0' },
                { id: 8, rank: 8, name: 'OASI SANT\'ANASTASIA', points: '0' },
                { id: 9, rank: 9, name: 'VESEVUS ACCADEMY', points: '0' },
                { id: 10, rank: 10, name: '2019 riposo', points: '0' }
            ];
            const MOCK_RESULTS = [];
            const MOCK_CALENDAR = [
                { id: 1, date: 'sab 07 novembre', home: 'Academy Soccer Ercolano', away: 'VESEVUS ACCADEMY', homeScore: '', awayScore: '' }
            ];


            const cleanName = (s) => String(s || '').replace(/\s+/g, ' ').trim().replace(/\b\w/g, (c) => c.toUpperCase());
            const isBye = (name) => /riposo/i.test(String(name || ''));


            // --- Proxy verso il sito target (stesso origine: nessun problema CORS) ---
            const proxyRequest = async (path, { method = 'GET', body } = {}) => {
                const res = await fetch(`${PROXY_URL}${path}`, {
                    method,
                    headers: body ? { 'Content-Type': 'application/x-www-form-urlencoded' } : {},
                    body,
                });
                if (!res.ok) throw new Error(`Proxy rispose HTTP ${res.status}`);
                return await res.text();
            };


            // --- PARSING CLASSIFICA ---
            // league.php risponde con JSON { html }: tabella a due blocchi
            // (sinistra: posizione + nome squadra; destra: Pt, G, V, N, P, F, S, +/-, FP)
            const parseStandings = (htmlText) => {
                const doc = new DOMParser().parseFromString(htmlText, 'text/html');
                const rows = Array.from(doc.querySelectorAll('.tables-body'));
                let teams = [];
                let stats = [];
                rows.forEach((row) => {
                    const pos = row.querySelector('.col-pos');
                    const nameEl = row.querySelector('.participant-name');
                    if (pos && nameEl) {
                        teams.push({
                            rank: pos.textContent.replace(/\D/g, ''),
                            name: cleanName(nameEl.textContent),
                        });
                    } else if (row.querySelector('.col-data')) {
                        stats.push(Array.from(row.querySelectorAll('.col-data')).map((c) => c.textContent.trim()));
                    }
                });
                return teams.map((t, i) => ({
                    id: i,
                    rank: t.rank || String(i + 1),
                    name: t.name,
                    points: (stats[i] && stats[i][0]) ? stats[i][0] : '0',
                })).filter((t) => !isBye(t.name));
            };

            // --- PARSING CALENDARIO / RISULTATI ---
            // dalla pagina di stampa t-printable.php?t=47&sk=calendar
            const parseCalendarPage = (htmlText) => {
                const doc = new DOMParser().parseFromString(htmlText, 'text/html');
                const blocks = Array.from(doc.querySelectorAll('.tcalendar-match-container'));
                const results = [];
                const calendar = [];
                blocks.forEach((block, idx) => {
                    const giornata = (block.querySelector('.tmatch-top')?.textContent || '').trim();
                    const names = Array.from(block.querySelectorAll('.tmatch-left .team-name')).map((el) => cleanName(el.textContent));
                    const date = (block.querySelector('.tmatch-bottom .center')?.textContent || '').trim();
                    const scoreDivs = block.querySelectorAll('.tmatch-right > div');
                    const homeScore = (scoreDivs[0]?.textContent || '').trim();
                    const awayScore = (scoreDivs[1]?.textContent || '').trim();
                    const hasScore = /\d/.test(homeScore) && /\d/.test(awayScore);
                    if (names.length < 2 || isBye(names[0]) || isBye(names[1])) return;
                    // Mostra solo partite che coinvolgono Academy Soccer Ercolano
                    if (!isErcolano(names[0]) && !isErcolano(names[1])) return;
                    const match = {
                        id: idx,
                        home: names[0],
                        away: names[1],
                        date: date || giornata,
                        homeScore,
                        awayScore,
                    };
                    if (hasScore) results.push(match);
                    else calendar.push(match);
                });
                return { results, calendar };
            };

            // --- FALLBACK: calendario tramite r.jina.ai (restituisce markdown) ---
            const parseCalendarMarkdown = (md) => {
                const results = [];
                const calendar = [];
                const parts = md.split(/GIORNATA\s+\d+/gi);
                parts.shift(); // elimina l'intestazione prima della prima giornata
                parts.forEach((body) => {
                    const lines = body.split(/\n/).map((l) => l.trim()).filter(Boolean);
                    let home = '';
                    let away = '';
                    let date = '';
                    let extra = '';
                    let i = 0;
                    while (i < lines.length) {
                        const line = lines[i];
                        if (line.startsWith('![')) {
                            // ![Image N](url) -> la riga successiva è il nome della squadra
                            if (!home) home = lines[i + 1] || '';
                            else if (!away) away = lines[i + 1] || '';
                            i += 2;
                            continue;
                        }
                        if (line.startsWith('**') && line.endsWith('**')) { i++; continue; }
                        if (/^(sab|dom|lun|mar|mer|gio|ven)\s/i.test(line)) { date = line; i++; continue; }
                        extra = line;
                        i++;
                    }
                    home = cleanName(home);
                    away = cleanName(away);
                    if (!home || !away || isBye(home) || isBye(away)) return;
                    const mScore = extra.match(/(\d+)\s*-\s*(\d+)/);
                    const match = {
                        id: results.length + calendar.length,
                        home,
                        away,
                        date,
                        homeScore: mScore ? mScore[1] : '',
                        awayScore: mScore ? mScore[2] : '',
                    };
                    if (mScore) results.push(match);
                    else calendar.push(match);
                });
                return { results, calendar };
            };

            const calURL = `${TARGET}/t-printable.php?t=${TOURNAMENT_ID}&sk=calendar`;

            const fetchStandings = async () => {
                try {
                    const text = await proxyRequest(`/system/include/ajax/public/league.php?op=20&tid=${TOURNAMENT_ID}`, {
                        method: 'POST',
                        body: `op=20&tid=${TOURNAMENT_ID}`,
                    });
                    const data = JSON.parse(text);
                    const parsed = parseStandings(data.html || '');
                    if (parsed.length > 0) return parsed;
                    throw new Error('classifica vuota');
                } catch (err) {
                    setError((error || '') + 'Classifica live non disponibile (' + err.message + '). ');
                }
                return MOCK_STANDINGS;
            };

            const fetchCalendar = async () => {
                let lastErr = '';
                // 1) proxy locale (HTML -> parsing diretto)
                try {
                    const html = await proxyRequest(`/t-printable.php?t=${TOURNAMENT_ID}&sk=calendar`);
                    const parsed = parseCalendarPage(html);
                    if (parsed.results.length > 0 || parsed.calendar.length > 0) return parsed;
                    throw new Error('calendario vuoto');
                } catch (err) {
                    lastErr = err.message;
                }
                // 2) r.jina.ai (markdown, cross-origin diretto dal browser)
                try {
                    const res = await fetch(`https://r.jina.ai/${calURL}`);
                    if (!res.ok) throw new Error(`r.jina.ai HTTP ${res.status}`);
                    const md = await res.text();
                    const parsed = parseCalendarMarkdown(md);
                    if (parsed.results.length > 0 || parsed.calendar.length > 0) return parsed;
                    throw new Error('markdown vuoto');
                } catch (err) {
                    lastErr = lastErr ? lastErr + '; ' : '' + 'r.jina.ai: ' + err.message;
                }
                // 3) proxy pubblici (GET) sulla pagina di stampa
                const publicProxies = [
                    `https://api.allorigins.win/get?url=${encodeURIComponent(calURL)}`,
                    `https://api.codetabs.com/v1/proxy?quest=${calURL}`,
                    `https://corsproxy.io/?${encodeURIComponent(calURL)}`,
                ];
                for (const proxy of publicProxies) {
                    try {
                        let html = '';
                        if (proxy.includes('allorigins')) {
                            const res = await fetch(proxy);
                            if (!res.ok) throw new Error(`HTTP ${res.status}`);
                            const data = await res.json();
                            if (!data.contents) throw new Error('nessun contenuto');
                            html = data.contents;
                        } else {
                            const res = await fetch(proxy);
                            if (!res.ok) throw new Error(`HTTP ${res.status}`);
                            html = await res.text();
                        }
                        const parsed = parseCalendarPage(html);
                        if (parsed.results.length > 0 || parsed.calendar.length > 0) return parsed;
                        throw new Error('vuoto');
                    } catch (err) {
                        lastErr = lastErr ? lastErr + '; ' : '' + `proxy: ${err.message}`;
                    }
                }
                setError((error || '') + 'Calendario non recuperabile (' + lastErr + '). ');
                return { results: [], calendar: [] };
            };

            const fetchData = async () => {
                setIsLoading(true);
                setError('');

                try {
                    const [standingsData, calendarData] = await Promise.all([
                        fetchStandings(),
                        fetchCalendar(),
                    ]);

                    setStandings(standingsData.length > 0 ? standingsData : MOCK_STANDINGS);
                    setResults(calendarData.results.length > 0 ? calendarData.results : MOCK_RESULTS);
                    setCalendar(calendarData.calendar.length > 0 ? calendarData.calendar : MOCK_CALENDAR);

                    if ((!standingsData || standingsData.length === 0) &&
                        calendarData.results.length === 0 && calendarData.calendar.length === 0 &&
                        !error) {
                        setError('Sito modificato dai proprietari. Dati di esempio attivi.');
                    }
                } catch (err) {
                    setError('Nessuna connessione al sito del campionato. Mostro dati offline.');
                    setStandings(MOCK_STANDINGS);
                    setResults(MOCK_RESULTS);
                    setCalendar(MOCK_CALENDAR);
                } finally {
                    setIsLoading(false);
                }
            };


            useEffect(() => {
                fetchData();
            }, []);


            const isErcolano = (teamName) => teamName.toLowerCase().includes('ercolano');


            const renderContent = () => {
                if (isLoading) {
                    return (
                        <div className="flex flex-col items-center justify-center h-64 space-y-4">
                            <IconRefresh className="w-10 h-10 text-[#800000] animate-spin" />
                            <p className="text-[#003366] font-bold animate-pulse">Sincronizzazione dati...</p>
                        </div>
                    );
                }


                switch (activeTab) {
                    case 'classifica':
                        return (
                        <div className="p-6 pb-32 animate-in fade-in duration-500">
                            <h2 className="text-2xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-[#800000] to-[#003366] tracking-tight mb-6">Classifica</h2>

                            {error && (
                            <div className="mb-6 bg-red-50/80 p-4 rounded-2xl border border-red-100 flex items-start space-x-3 text-red-700 text-sm font-medium">
                                <IconAlert className="w-5 h-5 flex-shrink-0 mt-0.5" />
                                <p>{error}</p>
                            </div>
                            )}


                            <div className="bg-white/80 backdrop-blur-md rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-white/60 overflow-hidden">
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm text-left">
                                <thead className="bg-slate-50/50 text-slate-400 uppercase text-[10px] tracking-widest font-bold">
                                    <tr>
                                    <th className="px-4 py-4 text-center w-8">Pos</th>
                                    <th className="px-4 py-4">Squadra</th>
                                    <th className="px-4 py-4 text-center text-[#800000]">Pt</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100/50">
                                    {standings.map((team) => {
                                    const highlighted = isErcolano(team.name);
                                    return (
                                        <tr key={team.id} className={`transition-colors ${highlighted ? 'bg-gradient-to-r from-[#800000]/10 to-[#003366]/10' : 'hover:bg-slate-50/50'}`}>
                                        <td className="px-4 py-4 text-center text-slate-400 font-bold">{team.rank}</td>
                                        <td className={`px-4 py-4 ${highlighted ? 'font-black text-[#800000]' : 'font-bold text-slate-700'}`}>
                                            {team.name}
                                        </td>
                                        <td className={`px-4 py-4 text-center font-black ${highlighted ? 'text-[#003366]' : 'text-slate-900'}`}>
                                            {team.points}
                                        </td>
                                        </tr>
                                    );
                                    })}
                                </tbody>
                                </table>
                            </div>
                            </div>
                        </div>
                        );


                    case 'risultati':
                        return (
                        <div className="p-6 space-y-5 pb-32 animate-in fade-in duration-500">
                            <h2 className="text-2xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-[#800000] to-[#003366] tracking-tight mb-2">Risultati</h2>

                            {results.length === 0 && !isLoading && (
                            <p className="text-slate-500 text-center py-10 font-medium">Nessun risultato giocato trovato.</p>
                            )}


                            {results.map((match) => (
                            <div key={match.id} className="bg-white/80 backdrop-blur-md rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-white/60 overflow-hidden transition-all duration-300 hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)]">
                                <div className="bg-slate-50/50 text-[10px] text-slate-500 text-center py-2 font-bold uppercase tracking-widest border-b border-slate-100/50">
                                {match.date}
                                </div>
                                <div className="flex items-center justify-between p-5">
                                <div className={`flex-1 text-center font-bold text-sm sm:text-base leading-tight ${isErcolano(match.home) ? 'text-[#800000] font-black' : 'text-slate-700'}`}>
                                    {match.home}
                                </div>
                                <div className="px-4 flex items-center justify-center space-x-2">
                                    <span className="bg-gradient-to-br from-[#800000] to-[#5c0000] shadow-inner text-white font-black text-xl w-10 h-10 flex items-center justify-center rounded-2xl">{match.homeScore}</span>
                                    <span className="text-slate-300 font-bold">-</span>
                                    <span className="bg-gradient-to-br from-[#003366] to-[#001f3f] shadow-inner text-white font-black text-xl w-10 h-10 flex items-center justify-center rounded-2xl">{match.awayScore}</span>
                                </div>
                                <div className={`flex-1 text-center font-bold text-sm sm:text-base leading-tight ${isErcolano(match.away) ? 'text-[#003366] font-black' : 'text-slate-700'}`}>
                                    {match.away}
                                </div>
                                </div>
                            </div>
                            ))}
                        </div>
                        );


                    case 'calendario':
                        return (
                        <div className="p-6 space-y-5 pb-32 animate-in fade-in duration-500">
                            <h2 className="text-2xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-[#800000] to-[#003366] tracking-tight mb-2">Prossime Partite</h2>

                            {calendar.length === 0 && !isLoading && (
                            <p className="text-slate-500 text-center py-10 font-medium">Nessuna partita in programma trovata.</p>
                            )}


                            {calendar.map((match) => (
                            <div key={match.id} className="bg-white/80 backdrop-blur-md rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-white/60 overflow-hidden transition-all duration-300 hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)]">
                                <div className="bg-[#800000]/5 text-[10px] text-[#800000] text-center py-2 font-bold uppercase tracking-widest border-b border-[#800000]/10">
                                {match.date}
                                </div>
                                <div className="flex items-center justify-between p-5">
                                <div className={`flex-1 text-center font-bold text-sm sm:text-base leading-tight ${isErcolano(match.home) ? 'text-[#800000] font-black' : 'text-slate-700'}`}>
                                    {match.home}
                                </div>
                                <div className="px-5 flex items-center justify-center">
                                    <span className="bg-slate-100/80 border border-slate-200 text-slate-400 font-black text-xs px-3 py-1.5 rounded-xl">VS</span>
                                </div>
                                <div className={`flex-1 text-center font-bold text-sm sm:text-base leading-tight ${isErcolano(match.away) ? 'text-[#003366] font-black' : 'text-slate-700'}`}>
                                    {match.away}
                                </div>
                                </div>
                            </div>
                            ))}
                        </div>
                        );
                    default:
                        return null;
                }
            };


            return (
                <div className="min-h-screen bg-[#F8FAFC] bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-blue-50/60 via-slate-50 to-rose-50/40 flex justify-center font-sans selection:bg-[#800000] selection:text-white">
                <div className="w-full max-w-md relative flex flex-col min-h-screen shadow-2xl bg-white/40 overflow-hidden">

                    <header className="bg-gradient-to-r from-[#800000] via-[#5c0000] to-[#003366] text-white pt-12 pb-5 px-5 shadow-[0_10px_40px_-10px_rgba(0,51,102,0.5)] rounded-b-[2.5rem] sticky top-0 z-20 relative overflow-hidden flex flex-col justify-center">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full blur-3xl transform translate-x-1/3 -translate-y-1/3"></div>

                    <div className="flex items-center justify-between relative z-10 w-full">
                        <div className="flex items-center space-x-3 w-[85%]">
                            <div className="w-10 h-10 bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl flex items-center justify-center shadow-inner shrink-0">
                                <IconTrophy className="w-5 h-5 text-white" />
                            </div>
                            <h1 className="font-extrabold text-[15px] sm:text-base tracking-tight truncate w-full uppercase">Academy Soccer Ercolano 2019</h1>
                        </div>

                        <button onClick={fetchData} disabled={isLoading} className="p-2 bg-white/10 hover:bg-white/20 rounded-full transition-colors shrink-0">
                        <IconRefresh className={`w-5 h-5 text-white ${isLoading ? 'animate-spin' : ''}`} />
                        </button>
                    </div>
                    </header>


                    <main className="flex-1 overflow-y-auto custom-scrollbar">
                    {renderContent()}
                    </main>


                    <div className="fixed bottom-6 left-0 right-0 z-30 flex justify-center px-4 pointer-events-none">
                    <nav className="w-full max-w-md bg-white/95 backdrop-blur-xl border border-white shadow-[0_8px_30px_rgb(0,0,0,0.12)] rounded-3xl pointer-events-auto">
                        <div className="flex justify-around items-center h-[72px] px-2">
                        {[
                            { id: 'classifica', icon: IconTrophy, label: 'Classifica' },
                            { id: 'risultati', icon: IconCalendarDays, label: 'Risultati' },
                            { id: 'calendario', icon: IconCalendar, label: 'Calendario' },
                        ].map((tab) => {
                            const Icon = tab.icon;
                            const isActive = activeTab === tab.id;
                            return (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className="relative flex flex-col items-center justify-center w-full h-full space-y-1.5 transition-all duration-300"
                            >
                                <div className={`p-1.5 rounded-xl transition-all duration-300 ${isActive ? 'bg-[#800000]/10' : 'bg-transparent'}`}>
                                <Icon className={`w-[22px] h-[22px] transition-colors duration-300 ${isActive ? 'text-[#800000] stroke-[2.5px]' : 'text-slate-400 stroke-[1.5px]'}`} />
                                </div>
                                <span className={`text-[10px] font-bold uppercase tracking-wider transition-colors duration-300 ${isActive ? 'text-[#003366]' : 'text-slate-400'}`}>
                                {tab.label}
                                </span>
                            </button>
                            );
                        })}
                        </div>
                    </nav>
                    </div>
                </div>
                </div>
            );
        }


        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<App />);
    </script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ct="text/html; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ct)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(204, b"")

    def do_GET(self):
        # Debug: stampa il path ricevuto
        print(f"[GET] {self.path}", flush=True)
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html", "/app"):
            self._send(200, HTML)
        elif path.startswith("/proxy"):
            # Inoltra GET al sito target (es. /proxy/t-printable.php?t=47&sk=calendar)
            rest = self.path[len("/proxy"):]
            url = TARGET + rest
            print(f"[GET proxy] -> {url}", flush=True)
            self._forward("GET", url)
        else:
            self._send(404, "Not found")

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        print(f"[POST] {self.path}", flush=True)
        if path.startswith("/proxy"):
            rest = self.path[len("/proxy"):]
            url = TARGET + rest
            print(f"[POST proxy] -> {url}", flush=True)
            length = int(self.headers.get("Content-Length", 0) or 0)
            body = self.rfile.read(length)
            self._forward("POST", url, body)
        else:
            self._send(404, "Not found")

    def _forward(self, method, url, body=None):
        print(f"[FORWARD] {method} {url}", flush=True)
        req = Request(
            url,
            data=body,
            method=method,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; calcetto-avvia/1.0)",
                "Content-Type": self.headers.get("Content-Type", "application/x-www-form-urlencoded"),
                "Referer": TARGET + "/",
                "Origin": TARGET,
            },
        )
        try:
            with urlopen(req, timeout=30) as r:
                data = r.read()
                ct = r.headers.get("Content-Type", "text/html; charset=utf-8")
                print(f"[FORWARD OK] {method} {url} -> {r.status}", flush=True)
                self._send(r.status, data, ct)
        except HTTPError as e:
            data = e.read() if hasattr(e, "read") else str(e).encode()
            print(f"[FORWARD ERR] {method} {url} -> HTTP {e.code}", flush=True)
            self._send(e.code, data, e.headers.get("Content-Type", "text/plain"))
        except URLError as e:
            print(f"[FORWARD ERR] {method} {url} -> {e}", flush=True)
            self._send(502, str(e).encode(), "text/plain")

    def log_message(self, format, *args):
        # Tieni il terminale pulito
        return


def get_local_ip():
    """Restituisce l'indirizzo IP locale del PC (es. 192.168.1.45)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


if __name__ == "__main__":
    local_ip = get_local_ip()
    print(f"Server in ascolto su http://0.0.0.0:{PORT}")
    print(f"Da questo PC:      http://127.0.0.1:{PORT}/")
    print(f"Dal telefono:      http://{local_ip}:{PORT}/")
    print("(PC e telefono devono essere sullo stesso Wi-Fi)")
    print("Premi Ctrl+C per fermare.")
    import sys
    sys.stdout.flush()
    HTTPServer((HOST, PORT), Handler).serve_forever()
