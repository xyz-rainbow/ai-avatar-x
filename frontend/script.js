const videoElement = document.getElementById('makima-avatar-video');
const subtitleBox = document.getElementById('subtitle-box');
const subtitleText = document.getElementById('subtitle-text');
const openControlPanelButton = document.getElementById('open-control-panel');
const openLogsPanelButton = document.getElementById('open-logs-panel');
const minimizeAvatarWindowButton = document.getElementById('minimize-avatar-window');
const closeAvatarWindowButton = document.getElementById('close-avatar-window');
const chatInput = document.getElementById('chat-input');

const API_URL = 'http://127.0.0.1:5000/api/state';
const CHAT_API_URL = 'http://127.0.0.1:5000/api/chat';

let isPlayingSequence = false;

// Map expressions to video filenames
const expressionVideos = {
    "neutral": "avatar/makima_neutral.mp4",
    "orgullosa": "avatar/makima_orgullosa.mp4",
    "angry": "avatar/makima_angry.mp4",
    "annoyed": "avatar/makima_annoyed.mp4",
    "idle1": "avatar/makima_idle1.mp4",
    "idle2": "avatar/makima_idle2.mp4",
    "idle3": "avatar/makima_idle3.mp4",
    "idle4": "avatar/makima_idle4.mp4",
    "nervous": "avatar/makima_nervous.mp4",
    "sad": "avatar/makima_sad.mp4",
    "sleepy": "avatar/makima_sleepy.mp4",
    "happy": "avatar/makima_happy.mp4", 
    "thinking": "avatar/makima_thinking.mp4", 
    "talking": "avatar/makima_talking.mp4", 
    "wink": "avatar/makima_wink.mp4", 
    "idea": "avatar/makima_idea.mp4", 
    "idea2": "avatar/makima_idea2.mp4",
    "curious": "avatar/makima_curious.mp4", 
    "excited": "avatar/makima_excited.mp4",
};

// Function to sleep for a given time
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Function to update the avatar's visual state (video and subtitle)
function updateVisuals(expression, subtitle) {
    // Update subtitle
    if (subtitle) {
        subtitleText.textContent = subtitle;
        subtitleBox.classList.add('show');
    } else {
        subtitleText.textContent = '';
        subtitleBox.classList.remove('show');
    }

    // Update video source
    const newVideoFilename = expressionVideos[expression] || expressionVideos["neutral"];
    const newVideoFullUrl = videoElement.baseURI + newVideoFilename;

    if (videoElement.currentSrc !== newVideoFullUrl) {
        videoElement.src = newVideoFilename;
        videoElement.load();
        videoElement.play();
        videoElement.loop = true;
    }
}

// Function to play a sequence of expressions and subtitles
async function playSequence(sequence) {
    isPlayingSequence = true;
    for (const item of sequence) {
        updateVisuals(item.expression, item.subtitle);
        const displayTime = Math.max(2000, item.subtitle.length * 80);
        await sleep(displayTime);
    }
    isPlayingSequence = false;
    // Revert to neutral state after sequence
    updateVisuals('neutral', '');
}

// Main state polling function
async function pollState() {
    if (isPlayingSequence) return; // Don't poll if a sequence is playing

    try {
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error('Network response was not ok');
        const state = await response.json();
        updateVisuals(state.expression, state.subtitle);
    } catch (error) {
        console.error('Failed to fetch avatar state:', error);
    }
}

// Event listener for chat input
if (chatInput) {
    chatInput.addEventListener('keypress', async (e) => {
        if (e.key === 'Enter' && chatInput.value.trim() !== '' && !isPlayingSequence) {
            const message = chatInput.value.trim();
            chatInput.value = '';
            chatInput.disabled = true;

            try {
                const response = await fetch(CHAT_API_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message }),
                });

                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                
                const sequence = await response.json();
                await playSequence(sequence);

            } catch (error) {
                console.error('Error during chat:', error);
                await playSequence([{
                    expression: 'sad',
                    subtitle: 'Sorry, I had a little trouble responding.'
                }]);
            } finally {
                chatInput.disabled = false;
                chatInput.focus();
            }
        }
    });
}

// --- Window & Control Listeners ---
if (openControlPanelButton) {
    openControlPanelButton.addEventListener('click', () => window.pywebview.api.open_control_window());
}
if (openLogsPanelButton) {
    openLogsPanelButton.addEventListener('click', () => {
        // This button is now repurposed. You might want to open the settings/logs window.
        // For now, it does nothing.
    });
}
if (minimizeAvatarWindowButton) {
    minimizeAvatarWindowButton.addEventListener('click', () => window.pywebview.api.minimize_avatar_window());
}
if (closeAvatarWindowButton) {
    closeAvatarWindowButton.addEventListener('click', () => window.pywebview.api.close_avatar_window());
}

// --- Initialization ---
setInterval( pollState, 2000); // Poll for state changes every 2 seconds
pollState(); // Initial state update