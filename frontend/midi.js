class MIDIHandler {
    constructor(actionCallback) {
        this.actionCallback = actionCallback;
        this.access = null;
        // Default mappings (should match button_map.toml)
        this.mappings = {
            36: "toggle_recording",   // Pad 1
            37: "transcribe_copy",    // Pad 2
            38: "copy",               // Pad 3
            39: "append_session",     // Pad 4
            40: "refine:fix_grammar", // Pad 5
            41: "refine:summarize",   // Pad 6
            42: "refine:deep_research", // Pad 7
            43: "refine:expand"       // Pad 8
        };
    }

    async init() {
        if (!navigator.requestMIDIAccess) {
             console.warn("Web MIDI API not supported in this browser.");
             return false;
        }

        try {
            this.access = await navigator.requestMIDIAccess();
            this.access.onstatechange = (e) => this.handleStateChange(e);

            for (let input of this.access.inputs.values()) {
                input.onmidimessage = (e) => this.handleMessage(e);
            }
            return true;
        } catch (err) {
            console.warn("MIDI Access failed:", err);
            return false;
        }
    }

    handleStateChange(e) {
        console.log(`MIDI port ${e.port.name} ${e.port.state}`);
        if (e.port.type === "input" && e.port.state === "connected") {
             e.port.onmidimessage = (msg) => this.handleMessage(msg);
        }
    }

    handleMessage(message) {
        const [command, note, velocity] = message.data;
        // Note On is typically 144 (0x90) for channel 1
        // Some controllers might use different channels
        // 0x90 to 0x9F are Note On for channels 1-16
        if ((command & 0xF0) === 0x90 && velocity > 0) {
            const action = this.mappings[note];
            if (action) {
                this.actionCallback(action);
            }
        }
    }
}
