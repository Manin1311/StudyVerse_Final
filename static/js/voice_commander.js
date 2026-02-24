/**
 * ============================================================
 * StudyVerse Voice Commander
 * ============================================================
 * Uses the Web Speech API (built into Chrome/Edge — no API key)
 * to allow full voice control of the StudyVerse application.
 *
 * SUPPORTED COMMANDS:
 * - Navigation : "go to dashboard / focus / friends / quiz ..."
 * - Timer      : "start timer / stop timer / reset timer"
 * - Tasks      : "mark [task] done / add task [name]"
 * - Friends    : "search [name] / send friend request"
 * - Topic      : "explain [topic] / resolve [topic]"
 * - General    : "help" — shows command list
 * ============================================================
 */

(function () {
    'use strict';

    // ── Browser support check ──────────────────────────────
    const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        console.warn('[Voice] Web Speech API not supported in this browser.');
        return; // Gracefully exit — no mic button shown
    }

    // ── State ──────────────────────────────────────────────
    let recognition = null;
    let isListening = false;
    let listenTimeout = null;

    // ── DOM References (created dynamically) ──────────────
    let micBtn, voiceOverlay, voiceText, voiceStatus, commandListModal;

    // ── Init on DOM ready ─────────────────────────────────
    document.addEventListener('DOMContentLoaded', () => {
        createMicButton();
        createVoiceOverlay();
        createCommandListModal();
        setupRecognition();
    });

    // ══════════════════════════════════════════════════════
    // UI CREATION
    // ══════════════════════════════════════════════════════

    function createMicButton() {
        micBtn = document.createElement('button');
        micBtn.id = 'voice-mic-btn';
        micBtn.title = 'Voice Commands (Click to speak)';
        micBtn.innerHTML = `<i class="fa-solid fa-microphone"></i><span>Voice</span>`;
        micBtn.style.cssText = `
            display: flex;
            align-items: center;
            gap: 8px;
            width: 100%;
            background: transparent;
            border: 1px solid rgba(167,139,250,0.25);
            border-radius: 12px;
            color: var(--text-secondary);
            padding: 10px 14px;
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            margin: 6px 0;
            transition: all 0.2s;
            font-family: inherit;
        `;

        micBtn.addEventListener('mouseenter', () => {
            if (!isListening) {
                micBtn.style.background = 'rgba(167,139,250,0.08)';
                micBtn.style.color = '#a78bfa';
                micBtn.style.borderColor = 'rgba(167,139,250,0.5)';
            }
        });
        micBtn.addEventListener('mouseleave', () => {
            if (!isListening) resetMicBtnStyle();
        });
        micBtn.addEventListener('click', toggleListening);

        // Insert before the theme toggle button in sidebar
        const themeBtn = document.getElementById('theme-toggle');
        if (themeBtn && themeBtn.parentElement) {
            themeBtn.parentElement.insertBefore(micBtn, themeBtn);
        } else {
            // Fallback: append to sidebar nav
            const nav = document.querySelector('.nav-menu');
            if (nav) nav.appendChild(micBtn);
        }
    }

    function createVoiceOverlay() {
        voiceOverlay = document.createElement('div');
        voiceOverlay.id = 'voice-overlay';
        voiceOverlay.innerHTML = `
            <div id="voice-overlay-inner">
                <div id="voice-ripple">
                    <div class="ripple-ring r1"></div>
                    <div class="ripple-ring r2"></div>
                    <div class="ripple-ring r3"></div>
                    <i class="fa-solid fa-microphone" id="voice-mic-icon"></i>
                </div>
                <div id="voice-status-text">Listening...</div>
                <div id="voice-heard-text"></div>
                <button id="voice-stop-btn" onclick="window._voiceStop()">
                    <i class="fa-solid fa-xmark"></i> Stop
                </button>
            </div>
        `;

        const style = document.createElement('style');
        style.textContent = `
            #voice-overlay {
                display: none;
                position: fixed;
                bottom: 100px;
                left: 50%;
                transform: translateX(-50%);
                z-index: 9000;
                animation: voiceSlideUp 0.3s ease;
            }
            @keyframes voiceSlideUp {
                from { opacity:0; transform: translateX(-50%) translateY(20px); }
                to   { opacity:1; transform: translateX(-50%) translateY(0); }
            }
            #voice-overlay-inner {
                background: var(--bg-card);
                border: 1px solid rgba(167,139,250,0.35);
                border-radius: 20px;
                padding: 20px 32px;
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 12px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.4), 0 0 40px rgba(167,139,250,0.15);
                min-width: 280px;
            }
            #voice-ripple {
                position: relative;
                width: 64px;
                height: 64px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .ripple-ring {
                position: absolute;
                border-radius: 50%;
                border: 2px solid rgba(167,139,250,0.5);
                animation: ripplePulse 1.8s infinite;
            }
            .r1 { width: 64px; height: 64px; animation-delay: 0s; }
            .r2 { width: 80px; height: 80px; animation-delay: 0.3s; }
            .r3 { width: 96px; height: 96px; animation-delay: 0.6s; }
            @keyframes ripplePulse {
                0%   { transform: scale(0.8); opacity: 1; }
                100% { transform: scale(1.2); opacity: 0; }
            }
            #voice-mic-icon {
                font-size: 22px;
                color: #a78bfa;
                z-index: 1;
                filter: drop-shadow(0 0 8px rgba(167,139,250,0.8));
            }
            #voice-status-text {
                font-size: 14px;
                font-weight: 700;
                color: #a78bfa;
                letter-spacing: 0.5px;
            }
            #voice-heard-text {
                font-size: 13px;
                color: var(--text-secondary);
                min-height: 18px;
                font-style: italic;
                text-align: center;
                max-width: 260px;
            }
            #voice-stop-btn {
                background: rgba(167,139,250,0.1);
                border: 1px solid rgba(167,139,250,0.25);
                color: var(--text-secondary);
                border-radius: 20px;
                padding: 6px 18px;
                font-size: 12px;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 6px;
                font-family: inherit;
                transition: all 0.2s;
            }
            #voice-stop-btn:hover {
                background: rgba(239,68,68,0.1);
                border-color: rgba(239,68,68,0.3);
                color: #f87171;
            }
            /* Listening state on mic button */
            #voice-mic-btn.listening {
                background: rgba(167,139,250,0.15) !important;
                border-color: #a78bfa !important;
                color: #a78bfa !important;
                animation: micPulse 1.5s infinite;
            }
            @keyframes micPulse {
                0%, 100% { box-shadow: 0 0 0 0 rgba(167,139,250,0.4); }
                50%       { box-shadow: 0 0 0 8px rgba(167,139,250,0); }
            }
            /* Voice toast feedback */
            .voice-toast {
                position: fixed;
                bottom: 80px;
                left: 50%;
                transform: translateX(-50%);
                background: var(--bg-card);
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 12px 24px;
                font-size: 13.5px;
                font-weight: 600;
                color: var(--text-primary);
                z-index: 9001;
                display: flex;
                align-items: center;
                gap: 10px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.3);
                animation: voiceSlideUp 0.3s ease;
                white-space: nowrap;
            }
            .voice-toast i { color: #a78bfa; }
            /* Command list modal */
            #voice-command-modal {
                display: none;
                position: fixed;
                inset: 0;
                background: rgba(0,0,0,0.7);
                z-index: 9500;
                place-items: center;
            }
            #voice-command-modal.open { display: grid; }
            #voice-cmd-list-inner {
                background: var(--bg-card);
                border: 1px solid var(--border);
                border-radius: 20px;
                padding: 28px;
                max-width: 480px;
                width: 90%;
                max-height: 80vh;
                overflow-y: auto;
            }
        `;
        document.head.appendChild(style);
        document.body.appendChild(voiceOverlay);
    }

    function createCommandListModal() {
        commandListModal = document.createElement('div');
        commandListModal.id = 'voice-command-modal';
        commandListModal.innerHTML = `
            <div id="voice-cmd-list-inner">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                    <h3 style="color:var(--text-primary); font-size:1.1rem; font-weight:800;">
                        🎙️ Voice Commands
                    </h3>
                    <button onclick="document.getElementById('voice-command-modal').classList.remove('open')"
                        style="background:transparent; border:none; color:var(--text-secondary); font-size:18px; cursor:pointer;">
                        <i class="fa-solid fa-xmark"></i>
                    </button>
                </div>
                ${renderCommandList()}
            </div>
        `;
        document.body.appendChild(commandListModal);
    }

    function renderCommandList() {
        const cmds = [
            { cat: '⏱️ Timer', items: ['"Start timer"', '"Stop timer"', '"Pause timer"', '"Reset timer"'] },
            { cat: '🧭 Navigation', items: ['"Go to dashboard"', '"Open focus mode"', '"Go to friends"', '"Open quiz"', '"Go to shop"', '"Open leaderboard"', '"Go to profile"', '"Go to live"', '"Open battle"'] },
            { cat: '✅ Tasks', items: ['"Add task [name]"', '"Mark [task name] done"'] },
            { cat: '👥 Friends', items: ['"Search [name]"', '"Find [name]"', '"Send friend request"'] },
            { cat: '🧠 AI', items: ['"Explain [topic]"', '"Resolve [topic]"', '"Ask AI [question]"'] },
            { cat: '❓ Help', items: ['"Help" or "Show commands"'] },
        ];
        return cmds.map(c => `
            <div style="margin-bottom:16px;">
                <div style="font-size:12px; font-weight:800; color:#a78bfa; text-transform:uppercase; letter-spacing:0.8px; margin-bottom:8px;">${c.cat}</div>
                ${c.items.map(i => `<div style="font-size:13px; color:var(--text-secondary); padding:5px 10px; background:var(--bg-hover); border-radius:8px; margin-bottom:4px; font-style:italic;">${i}</div>`).join('')}
            </div>
        `).join('');
    }

    // ══════════════════════════════════════════════════════
    // SPEECH RECOGNITION SETUP
    // ══════════════════════════════════════════════════════

    function setupRecognition() {
        recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.continuous = false;       // One command at a time — more accurate
        recognition.interimResults = true;    // Show partial transcript while speaking
        recognition.maxAlternatives = 1;

        recognition.onstart = () => {
            isListening = true;
            showOverlay();
            setHeard('');
            setStatus('Listening...');
        };

        recognition.onresult = (event) => {
            const result = event.results[event.results.length - 1];
            const transcript = result[0].transcript.trim().toLowerCase();

            // Show partial/interim result
            setHeard(`"${transcript}"`);

            // Only process when final
            if (result.isFinal) {
                processCommand(transcript);
            }
        };

        recognition.onerror = (event) => {
            if (event.error === 'no-speech') {
                setStatus('No speech detected');
                setTimeout(stopListening, 1500);
            } else if (event.error === 'not-allowed') {
                showToast('❌ Microphone access denied. Please allow mic in browser settings.', 4000);
                stopListening();
            } else {
                stopListening();
            }
        };

        recognition.onend = () => {
            // If still supposed to be listening (user didn't stop), restart
            if (isListening) {
                try { recognition.start(); } catch (e) { stopListening(); }
            }
        };
    }

    // ══════════════════════════════════════════════════════
    // LISTENING CONTROL
    // ══════════════════════════════════════════════════════

    function toggleListening() {
        if (isListening) stopListening();
        else startListening();
    }

    function startListening() {
        if (isListening) return;
        try {
            recognition.start();
            isListening = true; // Will be set true in onstart too
            micBtn.classList.add('listening');
            micBtn.querySelector('i').className = 'fa-solid fa-circle-dot';
        } catch (e) {
            console.warn('[Voice] Recognition start error:', e);
        }
    }

    function stopListening() {
        isListening = false;
        try { recognition.stop(); } catch (e) { }
        hideOverlay();
        resetMicBtnStyle();
        micBtn.classList.remove('listening');
        micBtn.querySelector('i').className = 'fa-solid fa-microphone';
        clearTimeout(listenTimeout);
    }

    // Expose stop for the overlay button
    window._voiceStop = stopListening;

    // ══════════════════════════════════════════════════════
    // COMMAND PROCESSING
    // ══════════════════════════════════════════════════════

    function processCommand(text) {
        console.log('[Voice] Heard:', text);
        setStatus('Processing...');

        let handled = false;

        // ── HELP ──────────────────────────────────────────
        if (match(text, ['help', 'show commands', 'what can you do', 'commands'])) {
            stopListening();
            document.getElementById('voice-command-modal').classList.add('open');
            return;
        }

        // ── NAVIGATION ────────────────────────────────────
        const navMap = {
            'dashboard': '/dashboard',
            'home': '/dashboard',
            'focus': '/pomodoro',
            'pomodoro': '/pomodoro',
            'focus mode': '/pomodoro',
            'timer': '/pomodoro',
            'tasks': '/todos',
            'todos': '/todos',
            'to do': '/todos',
            'quiz': '/quiz',
            'syllabus': '/syllabus',
            'topic': '/topic-resolver',
            'topic resolver': '/topic-resolver',
            'photo': '/photo-solver',
            'photo solver': '/photo-solver',
            'progress': '/progress',
            'friends': '/friends',
            'live': '/live',
            'live streams': '/live',
            'battle': '/battle',
            'byte battle': '/battle',
            'ai coach': '/chat',
            'chat': '/chat',
            'shop': '/shop',
            'item shop': '/shop',
            'leaderboard': '/leaderboard',
            'profile': '/profile',
            'settings': '/settings',
        };

        for (const [keyword, url] of Object.entries(navMap)) {
            if (text.includes(keyword) && (text.includes('go to') || text.includes('open') || text.includes('navigate') || text.includes('take me') || text.includes('show') || text === keyword)) {
                stopListening();
                showToast(`🧭 Navigating to ${keyword}...`);
                setTimeout(() => window.location.href = url, 800);
                handled = true;
                break;
            }
        }
        if (handled) return;

        // ── TIMER COMMANDS ────────────────────────────────
        if (match(text, ['start timer', 'start focus', 'begin timer', 'start the timer', 'start pomodoro', 'start session'])) {
            stopListening();
            const btn = document.getElementById('startBtn') || document.getElementById('start-btn');
            if (btn && btn.textContent.toLowerCase().includes('start')) {
                btn.click();
                showToast('⏱️ Focus timer started!');
            } else if (window.location.pathname !== '/pomodoro') {
                showToast('🧭 Taking you to Focus Mode...');
                setTimeout(() => window.location.href = '/pomodoro', 800);
            } else {
                showToast('⚠️ Timer already running.');
            }
            return;
        }

        if (match(text, ['stop timer', 'pause timer', 'pause', 'stop', 'halt timer', 'end session'])) {
            stopListening();
            const btn = document.getElementById('startBtn') || document.getElementById('start-btn');
            if (btn && btn.textContent.toLowerCase().includes('pause')) {
                btn.click();
                showToast('⏸️ Timer paused.');
            } else {
                showToast('ℹ️ No active timer found. Go to Focus Mode first.');
            }
            return;
        }

        if (match(text, ['reset timer', 'restart timer', 'clear timer'])) {
            stopListening();
            const btn = document.getElementById('resetBtn') || document.getElementById('reset-btn');
            if (btn) {
                btn.click();
                showToast('🔄 Timer reset!');
            } else {
                showToast('ℹ️ Go to Focus Mode first.');
            }
            return;
        }

        // ── ADD TASK ──────────────────────────────────────
        if (match(text, ['add task', 'new task', 'create task'])) {
            stopListening();
            const taskName = text
                .replace(/add task|new task|create task/gi, '')
                .trim();

            const input = document.getElementById('new-goal-input')
                || document.getElementById('todoInput')
                || document.querySelector('input[placeholder*="task"]');

            if (input && taskName) {
                input.value = taskName;
                input.focus();
                // Try to submit
                const addBtn = document.getElementById('addGoalBtn')
                    || document.getElementById('addTodoBtn')
                    || input.closest('form')?.querySelector('button[type=submit]');
                if (addBtn) { addBtn.click(); }
                showToast(`✅ Task "${taskName}" added!`);
            } else if (!taskName) {
                showToast('❓ Say: "Add task [task name]"');
            } else {
                showToast('ℹ️ Open Focus Mode or Tasks page first.');
            }
            return;
        }

        // ── MARK TASK DONE ────────────────────────────────
        if (match(text, ['mark', 'complete', 'done', 'finished', 'tick'])) {
            stopListening();
            const taskName = text
                .replace(/mark|complete|done|finished|tick|as done|as complete/gi, '')
                .trim();

            if (!taskName) {
                showToast('❓ Say: "Mark [task name] done"');
                return;
            }

            // Try to find in goals/todos
            const allItems = [
                ...document.querySelectorAll('.goal-title'),
                ...document.querySelectorAll('.todo-title'),
                ...document.querySelectorAll('[data-task-name]'),
            ];

            let found = null;
            for (const el of allItems) {
                if (el.textContent.toLowerCase().includes(taskName)) {
                    found = el;
                    break;
                }
            }

            if (found) {
                // Try to find and click the checkbox near it
                const parent = found.closest('.goal-item, .todo-item, li, .task-row');
                const cb = parent?.querySelector('input[type=checkbox], .check-btn, .goal-check');
                if (cb) {
                    cb.click();
                    showToast(`✅ "${taskName}" marked as done!`);
                } else {
                    showToast(`⚠️ Found "${taskName}" but couldn't check it — try manually.`);
                }
            } else {
                showToast(`❓ Task "${taskName}" not found on this page.`);
            }
            return;
        }

        // ── FRIEND SEARCH ─────────────────────────────────
        if (match(text, ['search', 'find', 'look for', 'look up'])) {
            stopListening();
            const name = text
                .replace(/search|find|look for|look up|in friends|friend list|friend/gi, '')
                .trim();

            if (!name) {
                showToast('❓ Say: "Search [name]"');
                return;
            }

            // Try friend search input
            const searchInput = document.getElementById('friendSearch')
                || document.getElementById('search-input')
                || document.querySelector('input[placeholder*="earch"]');

            if (searchInput) {
                searchInput.value = name;
                searchInput.dispatchEvent(new Event('input', { bubbles: true }));
                searchInput.dispatchEvent(new Event('keyup', { bubbles: true }));
                showToast(`🔍 Searching for "${name}"...`);
            } else if (window.location.pathname !== '/friends') {
                showToast(`🧭 Taking you to Friends to search "${name}"...`);
                setTimeout(() => window.location.href = `/friends?q=${encodeURIComponent(name)}`, 800);
            } else {
                showToast('ℹ️ Search box not found on this page.');
            }
            return;
        }

        // ── SEND FRIEND REQUEST ───────────────────────────
        if (match(text, ['send request', 'send friend request', 'add friend', 'add as friend'])) {
            stopListening();
            const addBtn = document.querySelector('.btn-add-friend, [data-action="add-friend"]');
            if (addBtn) {
                addBtn.click();
                showToast('👋 Friend request sent!');
            } else {
                showToast('ℹ️ Go to a friend\'s profile to send a request.');
            }
            return;
        }

        // ── AI TOPIC / RESOLVE ────────────────────────────
        if (match(text, ['explain', 'resolve', 'tell me about', 'what is', 'teach me'])) {
            stopListening();
            const topic = text
                .replace(/explain|resolve|tell me about|what is|teach me/gi, '')
                .trim();

            if (!topic) {
                showToast('❓ Say: "Explain [topic name]"');
                return;
            }

            showToast(`🧠 Resolving "${topic}"...`);
            setTimeout(() => {
                window.location.href = `/topic-resolver?q=${encodeURIComponent(topic)}`;
            }, 800);
            return;
        }

        // ── ASK AI ────────────────────────────────────────
        if (match(text, ['ask ai', 'ask the ai', 'ai coach', 'ask coach'])) {
            stopListening();
            const question = text.replace(/ask ai|ask the ai|ai coach|ask coach/gi, '').trim();
            if (question) {
                showToast(`💬 Asking AI: "${question}"...`);
                setTimeout(() => {
                    window.location.href = `/chat?q=${encodeURIComponent(question)}`;
                }, 800);
            } else {
                showToast('🧭 Opening AI Coach...');
                setTimeout(() => window.location.href = '/chat', 800);
            }
            return;
        }

        // ── NOT UNDERSTOOD ────────────────────────────────
        setStatus('Try again...');
        setHeard(`❓ Not understood: "${text}"`);
        setTimeout(() => {
            if (isListening) {
                setStatus('Listening...');
                setHeard('');
            }
        }, 2500);
    }

    // ══════════════════════════════════════════════════════
    // HELPERS
    // ══════════════════════════════════════════════════════

    function match(text, keywords) {
        return keywords.some(k => text.includes(k));
    }

    function showOverlay() {
        voiceOverlay.style.display = 'block';
    }

    function hideOverlay() {
        voiceOverlay.style.display = 'none';
    }

    function setStatus(msg) {
        const el = document.getElementById('voice-status-text');
        if (el) el.textContent = msg;
    }

    function setHeard(msg) {
        const el = document.getElementById('voice-heard-text');
        if (el) el.textContent = msg;
    }

    function resetMicBtnStyle() {
        micBtn.style.background = 'transparent';
        micBtn.style.color = 'var(--text-secondary)';
        micBtn.style.borderColor = 'rgba(167,139,250,0.25)';
    }

    function showToast(message, duration = 3000) {
        // Remove old toast if any
        const old = document.querySelector('.voice-toast');
        if (old) old.remove();

        const toast = document.createElement('div');
        toast.className = 'voice-toast';
        toast.innerHTML = `<i class="fa-solid fa-microphone-lines"></i> ${message}`;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.transition = 'opacity 0.3s';
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    console.log('[Voice] StudyVerse Voice Commander ready ✅');
})();
