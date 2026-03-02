/**
 * VERSE — AI Voice Assistant for StudyVerse
 * ==========================================
 * Natural language voice interface for the entire app.
 * - Web Speech API for STT (Speech-to-Text)
 * - Web Speech Synthesis for TTS (Text-to-Speech)
 * - Gemini AI backend for intent understanding
 * - Fully natural — no rigid commands needed
 */

(function () {
    'use strict';

    /* ─── CONFIG ─────────────────────────────────────────── */
    const VERSE_ENDPOINT = '/api/voice-assistant';
    const VERSE_WELCOME_SHOWN_KEY = 'verse_welcome_shown_v1';

    /* ─── STATE ──────────────────────────────────────────── */
    let recognition = null;
    let isListening = false;
    let isSpeaking = false;
    let currentUtterance = null;
    let bubbleHideTimer = null;

    /* ─── DOM REFS (set after DOMContentLoaded) ──────────── */
    let micBtn, micLabel, bubble, bubbleHeader, bubbleDot,
        bubbleText, bubbleUser, welcomeOverlay;

    /* ─── SPEECH SYNTHESIS ────────────────────────────────── */
    function speak(text, onEnd) {
        if (!window.speechSynthesis) return onEnd && onEnd();
        window.speechSynthesis.cancel();

        const utter = new SpeechSynthesisUtterance(text);
        utter.lang = 'en-US';
        utter.rate = 1.05;
        utter.pitch = 1.0;
        utter.volume = 1.0;

        // Pick a nice female voice if available
        const voices = window.speechSynthesis.getVoices();
        const preferred = voices.find(v =>
            /google us english|samantha|karen|zira|microsoft zira/i.test(v.name)
        ) || voices.find(v => v.lang === 'en-US') || voices[0];
        if (preferred) utter.voice = preferred;

        utter.onend = () => { isSpeaking = false; onEnd && onEnd(); };
        utter.onerror = () => { isSpeaking = false; onEnd && onEnd(); };

        isSpeaking = true;
        currentUtterance = utter;
        window.speechSynthesis.speak(utter);
    }

    function stopSpeaking() {
        if (window.speechSynthesis) window.speechSynthesis.cancel();
        isSpeaking = false;
    }

    /* ─── SPEECH RECOGNITION ──────────────────────────────── */
    function initRecognition() {
        const SpeechRecognition =
            window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) return null;

        const r = new SpeechRecognition();
        r.lang = 'en-US';
        r.continuous = false;
        r.interimResults = true;
        r.maxAlternatives = 1;

        r.onstart = () => {
            isListening = true;
            micBtn.classList.add('verse-listening');
            micBtn.classList.remove('verse-thinking');
            micBtn.innerHTML = '<i class="fa-solid fa-stop"></i>';
            showBubble('listening');
        };

        r.onresult = (event) => {
            const interim = Array.from(event.results)
                .map(r => r[0].transcript).join('');
            updateBubbleTranscript(interim);
        };

        r.onend = () => {
            if (!isListening) return; // was manually stopped
            isListening = false;
            const lastResult = recognition._lastFinal;
            if (lastResult && lastResult.trim().length > 1) {
                processUserSpeech(lastResult.trim());
            } else {
                setBubbleIdle();
                resetMicBtn();
            }
        };

        r.onerror = (e) => {
            isListening = false;
            resetMicBtn();
            if (e.error !== 'aborted' && e.error !== 'no-speech') {
                showToast('⚠️ Mic error: ' + e.error);
            }
            setBubbleIdle();
        };

        // Capture final transcript
        r.addEventListener('result', (event) => {
            for (const res of event.results) {
                if (res.isFinal) {
                    recognition._lastFinal = res[0].transcript;
                }
            }
        });

        return r;
    }

    /* ─── START / STOP LISTENING ──────────────────────────── */
    function startListening() {
        if (isSpeaking) stopSpeaking();
        if (!recognition) {
            showToast('🚫 Voice recognition not supported in this browser. Try Chrome.');
            return;
        }
        recognition._lastFinal = '';
        try {
            recognition.start();
        } catch (e) {
            // Already started — stop then restart
            recognition.stop();
            setTimeout(startListening, 300);
        }
    }

    function stopListening() {
        if (!isListening) return;
        isListening = false;
        recognition && recognition.stop();
        resetMicBtn();
    }

    /* ─── PROCESS SPEECH → AI → ACTION ───────────────────── */
    async function processUserSpeech(transcript) {
        micBtn.classList.remove('verse-listening');
        micBtn.classList.add('verse-thinking');
        micBtn.innerHTML = '<i class="fa-solid fa-spinner"></i>';

        showBubble('thinking', transcript);

        try {
            const resp = await fetch(VERSE_ENDPOINT, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: transcript,
                    page: window.location.pathname
                })
            });

            if (!resp.ok) throw new Error('Server error ' + resp.status);
            const data = await resp.json();

            // Show Verse reply in bubble
            showBubble('reply', transcript, data.reply);

            // Speak the reply
            speak(data.reply, () => {
                // After speaking, optionally hide bubble
                scheduleBubbleHide(6000);
            });

            // Execute the action
            if (data.action) {
                await executeAction(data.action, data.params || {});
            }

        } catch (err) {
            console.error('[Verse]', err);
            const errMsg = "Sorry, I ran into a problem. Please try again.";
            showBubble('reply', transcript, errMsg);
            speak(errMsg);
        } finally {
            resetMicBtn();
        }
    }

    /* ─── ACTION EXECUTOR ─────────────────────────────────── */
    async function executeAction(action, params) {
        // Small delay so speech starts first
        await wait(300);

        const nav = (path) => {
            setTimeout(() => { window.location.href = path; }, 1400);
        };

        switch (action) {

            /* ── Navigation ── */
            case 'navigate_dashboard': nav('/dashboard'); break;
            case 'navigate_pomodoro': nav('/pomodoro'); break;
            case 'navigate_todos': nav('/todos'); break;
            case 'navigate_quiz': nav('/quiz'); break;
            case 'navigate_syllabus': nav('/syllabus'); break;
            case 'navigate_leaderboard': nav('/leaderboard'); break;
            case 'navigate_friends': nav('/friends'); break;
            case 'navigate_shop': nav('/shop'); break;
            case 'navigate_progress': nav('/progress'); break;
            case 'navigate_chat': nav('/chat'); break;
            case 'navigate_battle': nav('/battle'); break;
            case 'navigate_profile': nav('/profile'); break;
            case 'navigate_settings': nav('/settings'); break;
            case 'navigate_calendar': nav('/calendar'); break;
            case 'navigate_topic_resolver': nav('/topic-resolver'); break;
            case 'navigate_photo_solver': nav('/photo-solver'); break;

            /* ── Todo ── */
            case 'add_todo': {
                if (params.title) {
                    try {
                        await fetch('/todos/add', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                title: params.title,
                                priority: params.priority || 'medium',
                                category: params.category || 'general'
                            })
                        });
                        showToast('✅ Todo added: ' + params.title);
                    } catch (e) { showToast('⚠️ Could not add todo'); }
                }
                break;
            }

            /* ── Pomodoro ── */
            case 'start_pomodoro': {
                nav('/pomodoro');
                break;
            }

            /* ── Calendar Event ── */
            case 'add_event': {
                nav('/calendar');
                break;
            }

            /* ── Stats (read aloud — already spoken via reply) ── */
            case 'get_stats':
            case 'get_streak':
            case 'get_todos':
            case 'get_xp':
                // Stats are included in the reply text from backend
                break;

            /* ── Conversational (no action needed) ── */
            case 'conversation':
            case 'none':
            default:
                break;
        }
    }

    /* ─── WELCOME ANIMATION ───────────────────────────────── */
    function showWelcome(welcomeText) {
        if (!welcomeOverlay) return;

        // Show overlay
        welcomeOverlay.classList.add('verse-show');

        // Set the message text
        const subtitleEl = welcomeOverlay.querySelector('.verse-welcome-subtitle');
        if (subtitleEl) subtitleEl.textContent = welcomeText;

        // Speak after a short delay (let animation settle)
        setTimeout(() => speak(welcomeText), 800);

        // Dismiss on click or after 8s
        const dismiss = () => dismissWelcome();
        welcomeOverlay.addEventListener('click', dismiss, { once: true });
        setTimeout(dismiss, 9000);
    }

    function dismissWelcome() {
        if (!welcomeOverlay) return;
        welcomeOverlay.classList.remove('verse-show');
        welcomeOverlay.classList.add('verse-hide');
        setTimeout(() => welcomeOverlay.remove(), 700);
    }

    /* ─── BUBBLE UI ───────────────────────────────────────── */
    function showBubble(state, userText, verseText) {
        clearTimeout(bubbleHideTimer);
        if (!bubble) return;

        bubble.classList.add('verse-bubble-show');
        bubbleUser.style.display = 'none';

        if (state === 'listening') {
            bubbleHeader.innerHTML = '<span class="verse-bubble-dot"></span> Listening...';
            bubbleText.innerHTML = `
                <div class="verse-mini-wave">
                    <div class="verse-mini-bar"></div>
                    <div class="verse-mini-bar"></div>
                    <div class="verse-mini-bar"></div>
                    <div class="verse-mini-bar"></div>
                    <div class="verse-mini-bar"></div>
                </div>`;
        } else if (state === 'thinking') {
            bubbleHeader.innerHTML = '<span class="verse-bubble-dot"></span> Verse is thinking...';
            bubbleText.textContent = userText || '';
            if (userText) {
                bubbleUser.style.display = 'block';
                bubbleUser.textContent = ''; // cleared, will show below
                bubbleText.textContent = userText;
            }
        } else if (state === 'reply') {
            bubbleHeader.innerHTML = '🎙️ Verse';
            bubbleText.textContent = verseText || '';
            if (userText) {
                bubbleUser.style.display = 'block';
                bubbleUser.textContent = 'You: ' + userText;
            }
        }
    }

    function updateBubbleTranscript(text) {
        if (!bubble || !bubbleText) return;
        bubbleHeader.innerHTML = '<span class="verse-bubble-dot"></span> Listening...';
        bubbleText.textContent = text;
    }

    function setBubbleIdle() {
        scheduleBubbleHide(2000);
    }

    function scheduleBubbleHide(ms) {
        clearTimeout(bubbleHideTimer);
        bubbleHideTimer = setTimeout(() => {
            if (bubble) bubble.classList.remove('verse-bubble-show');
        }, ms);
    }

    /* ─── MIC BUTTON ──────────────────────────────────────── */
    function resetMicBtn() {
        if (!micBtn) return;
        micBtn.classList.remove('verse-listening', 'verse-thinking');
        micBtn.innerHTML = '<i class="fa-solid fa-microphone"></i>';
        isListening = false;
    }

    /* ─── TOAST ───────────────────────────────────────────── */
    function showToast(msg) {
        const t = document.createElement('div');
        t.className = 'verse-toast';
        t.textContent = msg;
        document.body.appendChild(t);
        requestAnimationFrame(() => {
            t.classList.add('verse-toast-show');
            setTimeout(() => {
                t.classList.remove('verse-toast-show');
                setTimeout(() => t.remove(), 400);
            }, 3500);
        });
    }

    /* ─── UTILS ───────────────────────────────────────────── */
    function wait(ms) { return new Promise(r => setTimeout(r, ms)); }

    /* ─── INIT ────────────────────────────────────────────── */
    function init() {
        micBtn = document.getElementById('verse-mic-btn');
        micLabel = document.getElementById('verse-mic-label');
        bubble = document.getElementById('verse-bubble');
        bubbleHeader = document.getElementById('verse-bubble-header');
        bubbleDot = document.getElementById('verse-bubble-dot');
        bubbleText = document.getElementById('verse-bubble-text');
        bubbleUser = document.getElementById('verse-bubble-user');
        welcomeOverlay = document.getElementById('verse-welcome-overlay');

        if (!micBtn) return; // No Verse on this page

        // Init speech recognition
        recognition = initRecognition();

        // Mic button click
        micBtn.addEventListener('click', () => {
            if (isListening) {
                stopListening();
            } else {
                startListening();
            }
        });

        // Keyboard shortcut: Alt+V
        document.addEventListener('keydown', (e) => {
            if (e.altKey && e.key.toLowerCase() === 'v') {
                e.preventDefault();
                isListening ? stopListening() : startListening();
            }
        });

        // Voices load async in some browsers
        if (window.speechSynthesis) {
            window.speechSynthesis.onvoiceschanged = () => { };
            window.speechSynthesis.getVoices(); // pre-load
        }
    }

    /* ─── PUBLIC API ──────────────────────────────────────── */
    window.Verse = {
        showWelcome,
        dismissWelcome,
        speak,
        showToast,
    };

    /* ─── BOOT ────────────────────────────────────────────── */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
