const API_URL = "http://localhost:8765/api";
const STORAGE_KEY = "dictator.offline.transcript";

const state = {
    isRecording: false,
    isOffline: false,
    transcript: "",
    autosaveTimer: null
};

const recorder = new AudioRecorder();
const ui = {
    btnRecord: document.getElementById('btn-record'),
    btnStop: document.getElementById('btn-stop'),
    btnCopy: document.getElementById('btn-copy'),
    btnAppend: document.getElementById('btn-append'),
    btnClear: document.getElementById('btn-clear'),
    btnDownload: document.getElementById('btn-download'),

    // New Refs
    selectTemplate: document.getElementById('template-select'),
    btnRefine: document.getElementById('btn-refine'),

    transcript: document.getElementById('transcript'),
    offlineToggle: document.getElementById('offline-toggle'),
    autosaveStatus: document.getElementById('autosave-status'),
    wordCount: document.getElementById('word-count'),
    charCount: document.getElementById('char-count'),
    lastSaved: document.getElementById('last-saved'),
    status: document.getElementById('status'),
    apiStatus: document.getElementById('api-status'),
    midiStatus: document.getElementById('midi-status')
};

// --- Actions ---

async function toggleRecording() {
    if (state.isRecording) {
        await stopRecording();
    } else {
        await startRecording();
    }
}

async function startRecording() {
    try {
        await recorder.start();
        state.isRecording = true;
        updateUI();
    } catch (err) {
        console.error("Failed to start recording:", err);
        alert("Could not access microphone. Ensure you are using HTTPS or localhost.");
    }
}

async function stopRecording() {
    state.isRecording = false;
    updateUI();

    ui.status.textContent = "Processing...";

    try {
        const audioBlob = await recorder.stop();
        if (audioBlob) {
            await transcribe(audioBlob);
        }
    } catch (err) {
        console.error(err);
        ui.status.textContent = "Error stopping recording";
    }
}

async function transcribe(audioBlob) {
    const formData = new FormData();
    const extension = getAudioExtension(audioBlob.type);
    formData.append("file", audioBlob, `recording.${extension}`);

    try {
        ui.status.textContent = "Transcribing...";
        const res = await fetch(`${API_URL}/transcribe`, {
            method: "POST",
            body: formData
        });

        if (!res.ok) throw new Error(await res.text());

        const data = await res.json();
        state.transcript = data.text;
        ui.transcript.value = state.transcript;
        ui.status.textContent = "Transcribed";
    } catch (err) {
        console.error(err);
        ui.status.textContent = "Error during transcription";
    }
}

function getAudioExtension(mimeType) {
    if (!mimeType) return "wav";

    if (mimeType.includes("webm")) return "webm";
    if (mimeType.includes("ogg")) return "ogg";
    if (mimeType.includes("wav")) return "wav";

    return "wav";
}

async function appendSession() {
    const text = ui.transcript.value;
    if (!text) return;

    try {
        const res = await fetch(`${API_URL}/session/append`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
        });

        if (res.ok) {
            ui.status.textContent = "Appended to session";
            setTimeout(() => {
                if (!state.isRecording) ui.status.textContent = "Connected";
            }, 2000);
        }
    } catch (err) {
        console.error(err);
        ui.status.textContent = "Error appending";
    }
}

async function refineText(templateName) {
    const text = ui.transcript.value;
    if (!text) return;

    if (state.isOffline) {
        ui.status.textContent = "Refine unavailable in offline mode";
        return;
    }

    try {
        ui.status.textContent = `Refining with ${templateName}...`;
        const res = await fetch(`${API_URL}/refine`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                text: text,
                template: templateName
            })
        });

        if (!res.ok) throw new Error(await res.text());

        const data = await res.json();
        state.transcript = data.text;
        ui.transcript.value = state.transcript;
        updateStats(state.transcript);
        ui.status.textContent = "Refined";
        scheduleAutosave();
    } catch (err) {
        console.error(err);
        ui.status.textContent = "Error refining text";
    }
}

function copyToClipboard() {
    const text = ui.transcript.value;
    if (!text) return;

    navigator.clipboard.writeText(text).then(() => {
        const originalText = ui.btnCopy.textContent;
        ui.btnCopy.textContent = "Copied!";
        setTimeout(() => ui.btnCopy.textContent = originalText, 1500);
    }).catch(err => {
        console.error("Failed to copy:", err);
    });
}

function updateStats(text) {
    const trimmed = text.trim();
    const words = trimmed ? trimmed.split(/\s+/).length : 0;
    ui.wordCount.textContent = String(words);
    ui.charCount.textContent = String(text.length);
}

function setAutosaveStatus(message) {
    ui.autosaveStatus.textContent = message;
}

function saveTranscript() {
    const text = ui.transcript.value;
    localStorage.setItem(STORAGE_KEY, text);
    const timestamp = new Date();
    ui.lastSaved.textContent = timestamp.toLocaleTimeString();
    setAutosaveStatus("Saved");
}

function scheduleAutosave() {
    setAutosaveStatus("Saving...");
    if (state.autosaveTimer) {
        clearTimeout(state.autosaveTimer);
    }
    state.autosaveTimer = setTimeout(() => {
        saveTranscript();
        state.autosaveTimer = null;
    }, 500);
}

function downloadTranscript() {
    const text = ui.transcript.value.trim();
    if (!text) return;
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const timestamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");
    link.href = url;
    link.download = `dictator-transcript-${timestamp}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

function updateOfflineMode() {
    state.isOffline = ui.offlineToggle.checked;

    if (state.isOffline) {
        ui.btnAppend.disabled = false;
        ui.selectTemplate.disabled = true;
        ui.btnRefine.disabled = true;
        ui.apiStatus.textContent = "API: Local-only";
    } else {
        ui.btnAppend.disabled = false;
        ui.selectTemplate.disabled = false;
        if (!state.isRecording) {
            ui.btnRefine.disabled = false;
        }
        ui.apiStatus.textContent = "API: OK"; // Will be updated by checkAPI
    }
}

// --- UI Updates ---

function updateUI() {
    if (state.isRecording) {
        ui.btnRecord.classList.add('recording');
        ui.btnRecord.textContent = "Stop Recording (Pad 1)";
        ui.btnStop.disabled = false;
        ui.status.textContent = "Recording...";
        ui.btnRefine.disabled = true;
    } else {
        ui.btnRecord.classList.remove('recording');
        ui.btnRecord.textContent = "Record (Pad 1)";
        ui.btnStop.disabled = true;
        if (!state.isOffline) {
            ui.btnRefine.disabled = false;
        }
    }
}

// --- Initialization ---

async function checkAPI() {
    try {
        const res = await fetch(`${API_URL}/health`);
        if (res.ok) {
            if (ui.status.textContent === "Disconnected" || ui.status.textContent === "API Disconnected") {
                ui.status.textContent = "Connected";
            }
            ui.status.classList.remove('disconnected');
            ui.status.classList.add('connected');
            ui.apiStatus.textContent = state.isOffline ? "API: Local-only" : "API: OK";
        } else {
            throw new Error();
        }
    } catch {
        ui.status.classList.remove('connected');
        ui.status.classList.add('disconnected');
        ui.apiStatus.textContent = "API: Offline";
    }
}

// MIDI Callback
function handleAction(action) {
    console.log("MIDI Action:", action);
    ui.midiStatus.textContent = `MIDI Action: ${action}`;

    if (action.startsWith("refine:")) {
        const template = action.split(":")[1];
        refineText(template);
        return;
    }

    if (action.startsWith("open_browser:")) {
        ui.status.textContent = "External browser actions disabled";
        return;
    }

    switch(action) {
        case "toggle_recording": toggleRecording(); break;
        case "copy": copyToClipboard(); break;
        case "append_session": appendSession(); break;
        case "transcribe_copy":
            if (state.isRecording) {
                stopRecording().then(() => {
                    // Wait for transcription then copy
                    // A proper event system would be better here, but polling checks:
                    const checkInterval = setInterval(() => {
                        if (ui.status.textContent === "Transcribed") {
                            copyToClipboard();
                            clearInterval(checkInterval);
                        }
                    }, 500);
                });
            } else {
                // If not recording, just copy what's there
                copyToClipboard();
            }
            break;
    }
}

// Event Listeners
ui.btnRecord.onclick = toggleRecording;
ui.btnStop.onclick = stopRecording;
ui.btnCopy.onclick = copyToClipboard;
ui.btnAppend.onclick = appendSession;
ui.btnDownload.onclick = downloadTranscript;
ui.btnClear.onclick = () => {
    ui.transcript.value = "";
    state.transcript = "";
    updateStats("");
    saveTranscript();
    if (!state.isRecording) {
        ui.status.textContent = "Ready";
    }
};
ui.offlineToggle.onchange = updateOfflineMode;
ui.transcript.addEventListener("input", () => {
    const text = ui.transcript.value;
    state.transcript = text;
    updateStats(text);
    scheduleAutosave();
});

ui.btnRefine.onclick = () => {
    const template = ui.selectTemplate.value;
    refineText(template);
};

// Start
const midiHandler = new MIDIHandler(handleAction);
midiHandler.init().then(success => {
    ui.midiStatus.textContent = success ? "MIDI: Active" : "MIDI: Not Available";
});

const savedTranscript = localStorage.getItem(STORAGE_KEY);
if (savedTranscript) {
    ui.transcript.value = savedTranscript;
    state.transcript = savedTranscript;
    updateStats(savedTranscript);
    ui.status.textContent = "Session restored";
} else {
    updateStats("");
}
setAutosaveStatus("Idle");
updateOfflineMode();
checkAPI();
setInterval(checkAPI, 5000);
