/**
 * #xyz-rainbow #xyz-rainbowtechnology #rainbowtechnology.xyz #rainbow.xyz #rainbow@rainbowtechnology.xyz
 */

const videoBG = document.getElementById('video-bg');
const videoFG = document.getElementById('video-fg');
const thoughtBox = document.getElementById('thought-box');
const thoughtText = document.getElementById('thought-text');
const subtitleBox = document.getElementById('subtitle-box');
const subtitleText = document.getElementById('subtitle-text');
const chatInput = document.getElementById('chat-input');
const settingsModal = document.getElementById('settings-modal');

const API_URL = 'http://127.0.0.1:5000/api/state';
const CHAT_API_URL = 'http://127.0.0.1:5000/api/chat';
const CONFIG_API_URL = 'http://127.0.0.1:5000/api/config';
const I18N_API_URL = 'http://127.0.0.1:5000/api/i18n';

let isPlayingSequence = false;
let appConfig = { language: 'en', transition_style: 'crossout', transition_duration: 0.5, performance_mode: 'medium' };
let currentVideoElement = videoFG;
let allTranslations = {};

const expressionVideos = {
    "neutral": "avatar/makima_neutral.webm",
    "orgullosa": "avatar/makima_orgullosa.webm",
    "angry": "avatar/makima_angry.webm",
    "annoyed": "avatar/makima_annoyed.webm",
    "idle1": "avatar/makima_idle1.webm",
    "idle2": "avatar/makima_idle2.webm",
    "idle3": "avatar/makima_idle3.webm",
    "idle4": "avatar/makima_idle4.webm",
    "nervous": "avatar/makima_nervous.webm",
    "sad": "avatar/makima_sad.webm",
    "sleepy": "avatar/makima_sleepy.webm",
    "happy": "avatar/makima_happy.webm", 
    "thinking": "avatar/makima_thinking.webm", 
    "talking": "avatar/makima_talking.webm", 
    "wink": "avatar/makima_wink.webm", 
    "idea": "avatar/makima_idea.webm", 
    "idea2": "avatar/makima_idea2.webm",
    "curious": "avatar/makima_curious.webm", 
    "excited": "avatar/makima_excited.webm",
};

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// --- Performance & Styles ---
function applyPerformanceMode() {
    const mode = appConfig.performance_mode || 'medium';
    const main = document.getElementById('main-container');
    const thought = document.getElementById('thought-box');
    const scanline = document.querySelector('.scanline');
    const noise = document.querySelector('.noise');

    if (mode === 'low') {
        main.style.animation = 'none';
        main.style.boxShadow = 'none';
        thought.style.backdropFilter = 'none';
        thought.style.background = 'rgba(0, 20, 20, 0.95)';
        if (scanline) scanline.style.display = 'none';
        if (noise) noise.style.display = 'none';
    } else if (mode === 'medium') {
        main.style.animation = 'none';
        main.style.boxShadow = 'inset 0 0 50px rgba(0,0,0,0.8)';
        thought.style.backdropFilter = 'blur(8px)';
        thought.style.background = 'rgba(0, 20, 20, 0.7)';
        if (scanline) scanline.style.display = 'block';
        if (noise) {
            noise.style.display = 'block';
            noise.style.animation = 'noise-animation 1s infinite step-end';
        }
    } else {
        main.style.animation = 'vhs-jitter 0.15s infinite alternate';
        main.style.boxShadow = 'inset 0 0 80px rgba(0,0,0,1), inset 0 0 40px rgba(0,0,0,1)';
        thought.style.backdropFilter = 'blur(15px)';
        thought.style.background = 'rgba(0, 20, 20, 0.7)';
        if (scanline) scanline.style.display = 'block';
        if (noise) {
            noise.style.display = 'block';
            noise.style.animation = 'noise-animation 0.5s infinite step-end';
        }
    }
}

// --- i18n ---
async function fetchI18n() {
    try {
        const res = await fetch(I18N_API_URL);
        allTranslations = await res.json();
        applyI18n();
    } catch (e) { console.error("i18n error:", e); }
}

function applyI18n() {
    const lang = appConfig.language || 'en';
    const dict = allTranslations[lang]?.ui || {};
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (dict[key]) {
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') el.placeholder = dict[key];
            else el.innerText = dict[key];
        }
    });
    if (chatInput && dict.chat_placeholder) chatInput.placeholder = dict.chat_placeholder;
}

// --- Visuals ---
async function updateVisuals(expression, subtitle, thought = "") {
    if (thought && thought !== "") {
        thoughtText.textContent = thought;
        thoughtBox.classList.remove('hidden');
        thoughtBox.style.boxShadow = "0 0 30px rgba(0, 255, 255, 0.5)";
        setTimeout(() => thoughtBox.style.boxShadow = "0 8px 32px rgba(0, 255, 255, 0.15)", 500);
    } else {
        thoughtBox.classList.add('hidden');
    }

    if (subtitle) {
        subtitleText.textContent = subtitle;
        subtitleBox.classList.add('show');
    } else {
        subtitleBox.classList.remove('show');
    }

    const newSrc = expressionVideos[expression] || expressionVideos["neutral"];
    const nextVideoElement = (currentVideoElement === videoFG) ? videoBG : videoFG;

    if (!currentVideoElement.src.includes(newSrc)) {
        nextVideoElement.src = newSrc;
        nextVideoElement.load();
        const duration = appConfig.transition_duration || 0.5;
        nextVideoElement.style.transition = `opacity ${duration}s ease-in-out`;
        currentVideoElement.style.transition = `opacity ${duration}s ease-in-out`;
        nextVideoElement.style.opacity = 1;
        currentVideoElement.style.opacity = 0;
        await sleep(duration * 1000);
        currentVideoElement.classList.remove('active');
        nextVideoElement.classList.add('active');
        currentVideoElement = nextVideoElement;
    }
}

async function playSequence(sequence) {
    isPlayingSequence = true;
    for (const item of sequence) {
        await updateVisuals(item.expression, item.subtitle, item.thought);
        // Base time + variable time per char + 3 extra seconds for easy reading
        const displayTime = Math.max(5000, item.subtitle.length * 60 + (item.thought ? 3000 : 0) + 3000);
        await sleep(displayTime);
    }
    isPlayingSequence = false;
    await updateVisuals('neutral', '', '');
}

async function pollState() {
    if (isPlayingSequence || !settingsModal.classList.contains('hidden')) return;
    try {
        const response = await fetch(API_URL);
        const state = await response.json();
        updateVisuals(state.expression, state.subtitle, state.thought);
    } catch (e) {}
}

// --- Chat ---
if (chatInput) {
    chatInput.addEventListener('keypress', async (e) => {
        if (e.key === 'Enter' && chatInput.value.trim() !== '') {
            const message = chatInput.value.trim();
            chatInput.value = '';
            chatInput.disabled = true;
            try {
                const response = await fetch(CHAT_API_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message }),
                });
                const sequence = await response.json();
                await playSequence(sequence);
            } catch (e) {}
            chatInput.disabled = false;
            chatInput.focus();
        }
    });
}

// --- Settings ---
async function loadConfig() {
    try {
        const res = await fetch(CONFIG_API_URL);
        appConfig = await res.json();
        document.getElementById('app-language').value = appConfig.language || 'en';
        document.getElementById('ollama-url').value = appConfig.ollama_url || '';
        document.getElementById('transition-style').value = appConfig.transition_style || 'crossout';
        document.getElementById('transition-duration').value = appConfig.transition_duration || 0.5;
        document.getElementById('system-prompt').value = appConfig.system_prompt || '';
        document.getElementById('thought-mode').value = appConfig.thought_mode || 'short';
        document.getElementById('performance-mode').value = appConfig.performance_mode || 'medium';
        
        applyI18n();
        applyPerformanceMode();

        const mRes = await fetch('/api/models');
        const models = await mRes.json();
        const sel = document.getElementById('ollama-model-select');
        sel.innerHTML = '';
        models.forEach(m => {
            let opt = document.createElement('option');
            opt.value = opt.textContent = m;
            if (m === appConfig.ollama_model) opt.selected = true;
            sel.appendChild(opt);
        });
    } catch (e) {}
}

document.getElementById('open-settings-panel').addEventListener('click', () => {
    loadConfig();
    settingsModal.classList.remove('hidden');
});
document.getElementById('close-settings').addEventListener('click', () => settingsModal.classList.add('hidden'));
document.getElementById('save-settings').addEventListener('click', async () => {
    const cfg = {
        language: document.getElementById('app-language').value,
        ollama_url: document.getElementById('ollama-url').value,
        transition_style: document.getElementById('transition-style').value,
        transition_duration: parseFloat(document.getElementById('transition-duration').value),
        system_prompt: document.getElementById('system-prompt').value,
        thought_mode: document.getElementById('thought-mode').value,
        ollama_model: document.getElementById('ollama-model-select').value,
        performance_mode: document.getElementById('performance-mode').value
    };
    await fetch(CONFIG_API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cfg)
    });
    appConfig = {...appConfig, ...cfg};
    applyI18n();
    applyPerformanceMode();
    settingsModal.classList.add('hidden');
});

// Stepper
document.getElementById('trans-dec').addEventListener('click', () => {
    const i = document.getElementById('transition-duration');
    i.value = Math.max(0, (parseFloat(i.value) - 0.1).toFixed(1));
});
document.getElementById('trans-inc').addEventListener('click', () => {
    const i = document.getElementById('transition-duration');
    i.value = (parseFloat(i.value) + 0.1).toFixed(1);
});

// Tabs
document.querySelectorAll('.tab-btn').forEach(b => {
    b.addEventListener('click', (e) => {
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        e.target.classList.add('active');
        document.getElementById(e.target.dataset.tab).classList.add('active');
    });
});

document.getElementById('open-debug-tools').addEventListener('click', () => {
    if (window.pywebview && window.pywebview.api) window.pywebview.api.open_inspector();
});
document.getElementById('minimize-avatar-window').addEventListener('click', () => window.pywebview.api.minimize_avatar_window());
document.getElementById('close-avatar-window').addEventListener('click', () => window.pywebview.api.close_avatar_window());

// --- Start ---
fetchI18n().then(() => {
    loadConfig();
    setInterval(pollState, 2000);
});
