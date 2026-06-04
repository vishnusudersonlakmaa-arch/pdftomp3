/* class VoiceAssistant {
    constructor() {
        // Initialize speech recognition
        this.speechRecognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        this.speechRecognition.continuous = false;
        this.speechRecognition.interimResults = false;
        this.speechRecognition.lang = 'en-US';
        this.speechRecognition.onresult = (event) => this.handleResult(event);

        // Initialize speech synthesis
        this.synth = window.speechSynthesis;

        // Command synonyms for natural language understanding
        this.commandSynonyms = {
            play: ['play', 'start', 'listen to', 'open'],
            preview: ['preview', 'view', 'open', 'show'],
            delete: ['delete', 'remove', 'trash'],
            convert: ['convert', 'change', 'transform'],
            next: ['next', 'forward', 'go next'],
            previous: ['previous', 'backwards', 'go previous'],
            back: ['back', 'go back', 'return'],
            goTo: ['go to', 'navigate to', 'open', 'show', 'take me to'],
            list: ['list', 'show', 'what are', 'display'],
            help: ['help', 'commands', 'what can I do']
        };

        // Page mappings for navigation
        this.urlMappings = {
            'Dashboard': ['dashboard', 'home', 'main'],
            'upload': ['upload', 'upload page'],
            'mp3files': ['mp3 files', 'audio', 'music'],
            'pdffiles': ['pdf files', 'pdfs', 'documents'],
            'files': ['files', 'all files'],
            'profile': ['profile', 'my profile'],
            'settings': ['settings', 'options', 'preferences']
        };

        // Bind keypress events to start/stop listening
        this.bindKeyPressEvents();
    }

    bindKeyPressEvents() {
        document.addEventListener('keydown', (event) => {
            if (event.key.toLowerCase() === 'j') this.startListening();
            if (event.key.toLowerCase() === 'f') this.stopListening();
        });
    }

    startListening() {
        console.log("Voice assistant started...");
        this.speak("Listening...");
        this.speechRecognition.start();
    }

    stopListening() {
        console.log("Voice assistant stopped.");
        this.speak("Stopped.");
        this.speechRecognition.stop();
    }

    handleResult(event) {
        const transcript = event.results[0][0].transcript.toLowerCase().trim();
        console.log("Heard:", transcript);
        const response = this.processCommand(transcript);
        this.speak(response);
    }

    speak(text) {
        if (this.synth.speaking) return;
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = "en-US";
        this.synth.speak(utterance);
    }

    processCommand(text) {
        // Help command
        if (this.matchesCommand(text, this.commandSynonyms.help)) {
            return this.getHelpMessage();
        }

        // Navigation to pages
        for (const [page, aliases] of Object.entries(this.urlMappings)) {
            const goToPatterns = aliases.flatMap(alias =>
                this.commandSynonyms.goTo.map(cmd => `${cmd} ${alias}`)
            );
            if (this.matchesCommand(text, goToPatterns)) {
                window.location.href = `/${page}`;
                return `Going to ${page}.`;
            }
        }

        // List files (audio or PDF)
        if (this.matchesCommand(text, [...this.commandSynonyms.list, 'audio files', 'mp3 files'])) {
            return this.listFiles('audio');
        }
        if (this.matchesCommand(text, [...this.commandSynonyms.list, 'pdf files', 'documents'])) {
            return this.listFiles('pdf');
        }

        const openMatch = text.match(/open (one|two|three|four|five|six|seven|eight)/);
        if (openMatch) {
            const numbers = {
                "one": 1, "two": 2, "three": 3, "four": 4,
                "five": 5, "six": 6, "seven": 7, "eight": 8
            };
            const count = numbers[openMatch[1]];
            return this.openMultipleFiles(count);
        }

        // File operations (play, preview, delete, convert)
        const fileName = this.extractFileName(text);
        if (fileName) {
            if (this.matchesCommand(text, this.commandSynonyms.play)) {
                return this.handleFileAction(fileName, 'play');
            }
            if (this.matchesCommand(text, this.commandSynonyms.preview)) {
                return this.handleFileAction(fileName, 'preview');
            }
            if (this.matchesCommand(text, this.commandSynonyms.delete)) {
                return this.handleFileAction(fileName, 'delete');
            }
            if (this.matchesCommand(text, this.commandSynonyms.convert)) {
                return this.handleConvert(fileName);
            }
        }

        // Navigation commands (next, previous, back)
        if (this.matchesCommand(text, this.commandSynonyms.next)) {
            return this.navigate('next');
        }
        if (this.matchesCommand(text, this.commandSynonyms.previous)) {
            return this.navigate('previous');
        }
        if (this.matchesCommand(text, this.commandSynonyms.back)) {
            return this.navigate('back');
        }

        // Utility commands
        if (this.matchesCommand(text, ['toggle dark mode', 'dark mode'])) {
           document.documentElement.setAttribute(
            "data-theme",
            document.documentElement.getAttribute("data-theme") === "light" ? "dark" : "light"
        );
            return "Dark mode toggled.";
        }

        return "Sorry, I didn’t understand. Try 'list audio files', 'play song.mp3', 'go to profile', or say 'help' for more options.";
    }

    matchesCommand(text, commands) {
        return commands.some(cmd => new RegExp(`\\b${cmd}\\b`, 'i').test(text));
    }

    extractFileName(text) {
        const match = text.match(/(\w+\.(mp3|pdf))/i);
        return match ? match[0].toLowerCase() : null;
    }

    listFiles(type) {
        const sectionId = type === 'audio' ? 'audioFiles' : 'PdfFiles';
        const pageName = type === 'audio' ? 'mp3 files' : 'pdf files';
        const section = document.getElementById(sectionId);
        console.log(sectionId, pageName,section);
         if (!section) {
            return `Please go to the ${pageName} page first. Say 'go to ${pageName}'.`;
        } 

        const files = Array.from(section.querySelectorAll('.card h6')).map(el => el.innerText);
        if (files.length === 0) {
            return `No ${type} files found.`;
        }
        return `You have the following ${type} files: ${files.join(", ")}`;
    }

    handleFileAction(fileName, action) {
        const isAudio = fileName.endsWith('.mp3');
        const sectionId = isAudio ? 'audioFiles' : 'PdfFiles';
        const section = document.getElementById(sectionId);

         if (!section) {
            const pageName = isAudio ? 'mp3 files' : 'pdf files';
            return `Please go to the ${pageName} page first. Say 'go to ${pageName}'.`;
        }

        const files = Array.from(section.querySelectorAll('.card h6'));
        const target = files.find(el => el.innerText.toLowerCase().includes(fileName));

        if (!target) {
            return `File "${fileName}" not found on this page.`;
        }

        const card = target.closest('.card');
        if (action === 'play' && isAudio) {
            const link = card.querySelector('a');
            if (link) {
                link.click();
                return `Playing ${fileName}.`;
            }
        } else if (action === 'preview' && !isAudio) {
            const link = card.querySelector('a');
            if (link) {
                link.click();
                return `Previewing ${fileName}.`;
            }
        } else if (action === 'delete') {
            const deleteBtn = card.querySelector('.delete-btn');
            if (deleteBtn) {
                deleteBtn.click();
                return `Deleted ${fileName}.`;
            }
        }

        return `Cannot ${action} ${fileName}.`;
    }

    handleConvert(fileName) {
        // Placeholder for conversion logic
        console.log(`Converting ${fileName}...`);
        return `Converting ${fileName}. This feature is under development.`;
    }

    navigate(direction) {
        const buttons = {
            next: document.querySelector('[id*="next"], [class*="next"]'),
            previous: document.querySelector('[id*="prev"], [class*="prev"]'),
            back: document.querySelector('[id*="back"], [class*="back"]')
        };

        if (buttons[direction] && buttons[direction].tagName === 'BUTTON') {
            buttons[direction].click();
            return `${direction.charAt(0).toUpperCase() + direction.slice(1)} clicked.`;
        }

        if (direction === 'back') {
            window.history.back();
            return "Going back.";
        }

        return `No ${direction} button found on this page.`;
    }

    getHelpMessage() {
        return "Here are some commands you can use: " +
            "'list audio files', 'list pdf files', 'play song.mp3', 'preview document.pdf', " +
            "'delete file.mp3', 'convert file.pdf', 'go to profile', 'go to settings', " +
            "'next', 'previous', 'back', 'toggle dark mode'. You can also say 'help' for assistance.";
    }

openMultipleFiles(count) {
    let section = document.getElementById("audioFiles") || document.getElementById("PdfFiles");
    if (!section) return "Please go to the Audio or PDF files page first.";

    const links = Array.from(section.querySelectorAll(".card a")).slice(0, count);
    if (links.length === 0) return "No files found to open.";

    links.forEach(link => window.open(link.href)); // Opens files in new tabs
    return `Opening ${links.length} file(s).`;
}

}

/**
 * AI-Powered Voice Assistant
 * ──────────────────────────
 * Wake : Shift + Ctrl + J
 * Stop : Shift + Ctrl + X
 *
 * Supports three free AI providers — pick one below:
 *   "groq"   → Groq Cloud  (free, very fast, Llama 3)       aistudio.google.com
 *   "gemini" → Google AI   (free, 15 req/min, Gemini Flash)  console.groq.com
 *   "ollama" → Local LLM   (100% free, no key, offline)      ollama.com
 *
 * ⚠️  API keys here are visible in browser DevTools.
 *     Fine for localhost dev — use the Django proxy for production.
 */

// ════════════════════════════════════════════════════════════
//  CONFIGURATION — edit this block only
// ════════════════════════════════════════════════════════════
const VA_PROVIDER = "gemini";          // "groq" | "gemini" | "ollama"

const VA_CONFIG = {
  groq: {
    apiKey : "YOUR_GROQ_API_KEY",    // console.groq.com → free, no card needed
    model  : "llama3-8b-8192",       // free & fast; or "mixtral-8x7b-32768"
  },
  gemini: {
    apiKey : "AIzaSyBovs2qgIzQJTRiiq3Cq09Fwzm2H0imBfk",  // aistudio.google.com → free tier
    model  : "gemini-3.5-flash",     // free: 15 req/min, 1M tokens/day
  },
  ollama: {
    apiKey : "",                     // no key — runs on your machine
    model  : "llama3",               // run once: ollama pull llama3
    url    : "http://localhost:11434",
  },
};

// System prompt — tells the AI to return structured JSON commands
const VA_SYSTEM_PROMPT = `
You are a voice command parser for a file-management web app.
Interpret the user's spoken command and respond ONLY with a single valid JSON
object — no markdown, no explanation, no extra text.

Actions and their exact JSON shape:
  navigate       → { "action": "navigate",      "page": "Dashboard|upload|mp3files|pdffiles|files|profile|settings" }
  listFiles      → { "action": "listFiles",      "type": "audio|pdf" }
  fileAction     → { "action": "fileAction",     "fileName": "<name.mp3|name.pdf>", "operation": "play|preview|delete|convert" }
  openMultiple   → { "action": "openMultiple",   "count": <integer 1-8> }
  navDirection   → { "action": "navDirection",   "direction": "next|previous|back" }
  toggleDarkMode → { "action": "toggleDarkMode" }
  help           → { "action": "help" }
  unknown        → { "action": "unknown",        "suggestion": "<one friendly sentence>" }

Rules:
- Infer intent flexibly; users will not always use exact keywords.
- If a file name is said without an extension, infer .mp3 for audio verbs and .pdf for document verbs.
- Respond ONLY with JSON. Nothing else.
`.trim();
// ════════════════════════════════════════════════════════════

class VoiceAssistant {
  // ─────────────────────────────── bootstrap ─────────────────────────────── //

  constructor() {
    /* ── Speech recognition ── */
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      console.error("Web Speech API not supported in this browser.");
      return;
    }
    this.recognition = new SR();
    this.recognition.continuous  = false;
    this.recognition.interimResults = false;
    this.recognition.lang = "en-US";
    this.recognition.onresult = (e) => this._onResult(e);
    this.recognition.onerror  = (e) => this._onError(e);
    this.recognition.onend    = ()  => { this.isListening = false; this._updateHUD(); };

    /* ── Speech synthesis ── */
    this.synth = window.speechSynthesis;

    /* ── State ── */
    this.isListening = false;
    this.isBusy      = false;   // true while waiting for AI response

    /* ── UI ── */
    this._injectStyles();
    this._createHUD();
    this._bindKeys();

    console.log(
      "%c🎙 AI Voice Assistant ready\n" +
      "%cShift+Ctrl+J → Start listening\n" +
      "Shift+Ctrl+X → Stop listening",
      "color:#6ee7b7;font-weight:bold;font-size:14px",
      "color:#94a3b8;font-size:12px"
    );
  }

  // ───────────────────────────── key bindings ─────────────────────────────── //

  _bindKeys() {
    document.addEventListener("keydown", (e) => {
      const shiftCtrl = e.shiftKey && e.ctrlKey;
      if (!shiftCtrl) return;

      if (e.key.toLowerCase() === "j") { e.preventDefault(); this.startListening(); }
      if (e.key.toLowerCase() === "x") { e.preventDefault(); this.stopListening();  }
    });
  }

  // ──────────────────────────── listen / stop ─────────────────────────────── //

  startListening() {
    if (this.isListening || this.isBusy) return;
    this.isListening = true;
    this._updateHUD("listening");
    this._speak("Listening…");
    this.recognition.start();
  }

  stopListening() {
    if (!this.isListening) return;
    this.isListening = false;
    this._updateHUD("idle");
    this._speak("Stopped.");
    this.recognition.stop();
  }

  // ──────────────────────────── speech events ─────────────────────────────── //

  async _onResult(event) {
    const transcript = event.results[0][0].transcript.trim();
    console.log(`🎤 Heard: "${transcript}"`);

    this.isListening = false;
    this.isBusy      = true;
    this._updateHUD("thinking");
    this._speak("Got it, processing…");

    let response;
    try {
      const action = await this._parseWithAI(transcript);
      response = this._executeAction(action, transcript);
    } catch (err) {
      console.warn("AI parse failed, using fallback →", err.message);
      response = this._fallback(transcript.toLowerCase());
    }

    this.isBusy = false;
    this._updateHUD("idle");
    this._speak(response);
  }

  _onError(event) {
    console.error("Speech recognition error:", event.error);
    this.isListening = false;
    this.isBusy      = false;
    this._updateHUD("idle");
    if (event.error !== "no-speech" && event.error !== "aborted") {
      this._speak("I had trouble hearing you — please try again.");
    }
  }

  // ─────────────────── AI command parser — routes to chosen provider ─────────── //

  async _parseWithAI(transcript) {
    switch (VA_PROVIDER) {
      case "groq":   return await this._callGroq(transcript);
      case "gemini": return await this._callGemini(transcript);
      case "ollama": return await this._callOllama(transcript);
      default: throw new Error(`Unknown provider: ${VA_PROVIDER}`);
    }
  }

  // ── Groq (Llama 3) ── free tier, fast, CORS-enabled ─────────────────────── //
  async _callGroq(transcript) {
    const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method:  "POST",
      headers: {
        "Content-Type":  "application/json",
        "Authorization": `Bearer ${VA_CONFIG.groq.apiKey}`,
      },
      body: JSON.stringify({
        model:      VA_CONFIG.groq.model,
        max_tokens: 256,
        messages: [
          { role: "system", content: VA_SYSTEM_PROMPT },
          { role: "user",   content: transcript },
        ],
      }),
    });

    if (!res.ok) throw new Error(`Groq ${res.status}: ${await res.text()}`);
    const data = await res.json();
    const raw  = data.choices[0].message.content.trim();
    return JSON.parse(raw.replace(/^```json\s*|```\s*$/g, "").trim());
  }

  // ── Google Gemini Flash ── free tier, 15 req/min, CORS-enabled ───────────── //
  async _callGemini(transcript) {
    const { apiKey, model } = VA_CONFIG.gemini;
    const url = `https://generativelanguage.googleapis.com/v1beta2/models/${model}:generateContent?key=${apiKey}`;

    const res = await fetch(url, {
      method:  "POST",
      headers: { "Content-Type": "application/json", 'X-goog-api-key': 'AQ.Ab8RN6IR7ynNfpPgeC1Zbyf5ykJGCMlw8VoJKWMF82RAjU4uYQ' },
      body: JSON.stringify({
        system_instruction: { parts: [{ text: VA_SYSTEM_PROMPT }] },
        contents: [{ role: "user", parts: [{ text: transcript }] }],
        generationConfig: { maxOutputTokens: 256, temperature: 0.1 },
      }),
    });

    if (!res.ok) throw new Error(`Gemini ${res.status}: ${await res.text()} , error: ${res.statusText}`);
    const data = await res.json();
    const raw  = data.candidates[0].content.parts[0].text.trim();
    return JSON.parse(raw.replace(/^```json\s*|```\s*$/g, "").trim());
  }

  // ── Ollama ── 100% free, runs locally, no API key ────────────────────────── //
  async _callOllama(transcript) {
    const { model, url } = VA_CONFIG.ollama;

    const res = await fetch(`${url}/api/chat`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model,
        stream: false,
        messages: [
          { role: "system", content: VA_SYSTEM_PROMPT },
          { role: "user",   content: transcript },
        ],
      }),
    });

    if (!res.ok) throw new Error(`Ollama ${res.status}: ${await res.text()}`);
    const data = await res.json();
    const raw  = data.message.content.trim();
    return JSON.parse(raw.replace(/^```json\s*|```\s*$/g, "").trim());
  }

  // ──────────────────────────── action router ─────────────────────────────── //

  _executeAction(action, original) {
    switch (action.action) {

      case "navigate":
        window.location.href = `/${action.page}`;
        return `Going to ${action.page}.`;

      case "listFiles":
        return this._listFiles(action.type);

      case "fileAction":
        return this._fileAction(action.fileName, action.operation);

      case "openMultiple":
        return this._openMultiple(action.count);

      case "navDirection":
        return this._navDirection(action.direction);

      case "toggleDarkMode": {
        const cur = document.documentElement.getAttribute("data-theme");
        document.documentElement.setAttribute("data-theme", cur === "dark" ? "light" : "dark");
        return "Dark mode toggled.";
      }

      case "help":
        return this._helpMessage();

      case "unknown":
        return action.suggestion || "I didn't understand — say 'help' for a list of commands.";

      default:
        return "I didn't understand that. Say 'help' for available commands.";
    }
  }

  // ──────────────────────────── DOM helpers ───────────────────────────────── //

  _listFiles(type) {
    const id  = type === "audio" ? "audioFiles" : "PdfFiles";
    const sec = document.getElementById(id);
    if (!sec) return `Please navigate to the ${type === "audio" ? "MP3 files" : "PDF files"} page first.`;

    const names = Array.from(sec.querySelectorAll(".card h6")).map((el) => el.innerText);
    return names.length
      ? `You have ${names.length} ${type} file${names.length > 1 ? "s" : ""}: ${names.join(", ")}.`
      : `No ${type} files found on this page.`;
  }

  _fileAction(fileName, operation) {
    if (!fileName) return "Please say the file name, for example 'play music.mp3'.";

    const isAudio = fileName.toLowerCase().endsWith(".mp3");
    const secId   = isAudio ? "audioFiles" : "PdfFiles";
    const sec     = document.getElementById(secId);
    if (!sec) return `Please go to the ${isAudio ? "MP3 files" : "PDF files"} page first.`;

    const card = Array
      .from(sec.querySelectorAll(".card h6"))
      .find((el) => el.innerText.toLowerCase().includes(fileName.toLowerCase()))
      ?.closest(".card");

    if (!card) return `"${fileName}" was not found on this page.`;

    if (operation === "play" && isAudio) {
      const a = card.querySelector("a");
      if (a) { a.click(); return `Playing ${fileName}.`; }
    }
    if (operation === "preview" && !isAudio) {
      const a = card.querySelector("a");
      if (a) { a.click(); return `Previewing ${fileName}.`; }
    }
    if (operation === "delete") {
      const btn = card.querySelector(".delete-btn");
      if (btn) { btn.click(); return `Deleted ${fileName}.`; }
    }
    if (operation === "convert") {
      return `Converting ${fileName} — this feature is under development.`;
    }

    return `Cannot ${operation} ${fileName}.`;
  }

  _openMultiple(count) {
    const sec = document.getElementById("audioFiles") || document.getElementById("PdfFiles");
    if (!sec) return "Please go to the Audio or PDF files page first.";
    const links = Array.from(sec.querySelectorAll(".card a")).slice(0, count);
    if (!links.length) return "No files found to open.";
    links.forEach((l) => window.open(l.href));
    return `Opening ${links.length} file${links.length > 1 ? "s" : ""}.`;
  }

  _navDirection(direction) {
    const selectors = {
      next:     '[id*="next"],[class*="next"]',
      previous: '[id*="prev"],[class*="prev"]',
      back:     '[id*="back"],[class*="back"]',
    };
    const el = document.querySelector(selectors[direction]);
    if (el?.tagName === "BUTTON") { el.click(); return `${direction} clicked.`; }
    if (direction === "back") { window.history.back(); return "Going back."; }
    return `No ${direction} button found on this page.`;
  }

  // ───────────────────────── rule-based fallback ──────────────────────────── //

  _fallback(text) {
    if (/help/.test(text))                      return this._helpMessage();
    if (/dark mode/.test(text)) {
      const cur = document.documentElement.getAttribute("data-theme");
      document.documentElement.setAttribute("data-theme", cur === "dark" ? "light" : "dark");
      return "Dark mode toggled.";
    }
    if (/audio|mp3/.test(text))                 return this._listFiles("audio");
    if (/pdf|document/.test(text))              return this._listFiles("pdf");
    if (/dashboard|home/.test(text))            { window.location.href = "/Dashboard"; return "Going to Dashboard."; }
    if (/settings|preference/.test(text))       { window.location.href = "/settings";  return "Going to Settings.";  }
    if (/profile/.test(text))                   { window.location.href = "/profile";   return "Going to Profile.";   }
    if (/upload/.test(text))                    { window.location.href = "/upload";    return "Going to Upload.";    }
    if (/back/.test(text))                      { window.history.back(); return "Going back."; }
    return "AI is unavailable right now. Say 'help' for commands.";
  }

  // ──────────────────────────── speech synthesis ──────────────────────────── //

  _speak(text) {
    if (!text) return;
    this.synth.cancel();
    const utt  = new SpeechSynthesisUtterance(text);
    utt.lang   = "en-US";
    utt.rate   = 1.05;
    utt.pitch  = 1;
    this.synth.speak(utt);
  }

  // ───────────────────────────────── HUD ─────────────────────────────────── //

  _injectStyles() {
    if (document.getElementById("va-style")) return;
    const style = document.createElement("style");
    style.id = "va-style";
    style.textContent = `
      /* ── HUD container ── */
      #va-hud {
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 99999;
        display: flex;
        align-items: center;
        gap: 10px;
        background: rgba(15, 23, 42, 0.88);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 40px;
        padding: 10px 18px 10px 12px;
        font-family: 'Segoe UI', system-ui, sans-serif;
        font-size: 13px;
        color: #cbd5e1;
        box-shadow: 0 8px 32px rgba(0,0,0,0.45);
        transition: opacity .25s, transform .25s;
        user-select: none;
        cursor: default;
      }
      #va-hud.va-hidden { opacity: 0; transform: translateY(8px); pointer-events: none; }

      /* ── Orb ── */
      #va-orb {
        width: 28px; height: 28px;
        border-radius: 50%;
        background: #334155;
        display: flex; align-items: center; justify-content: center;
        flex-shrink: 0;
        transition: background .3s;
        position: relative;
      }
      #va-orb svg { width: 14px; height: 14px; fill: #94a3b8; transition: fill .3s; }

      /* ── Listening ring ── */
      #va-orb::before {
        content: '';
        position: absolute;
        inset: -4px;
        border-radius: 50%;
        border: 2px solid transparent;
        transition: border-color .3s;
      }

      /* States */
      #va-hud.va-listening #va-orb              { background: #065f46; }
      #va-hud.va-listening #va-orb svg          { fill: #6ee7b7; }
      #va-hud.va-listening #va-orb::before      { border-color: #6ee7b7; animation: va-pulse 1.2s ease-in-out infinite; }

      #va-hud.va-thinking #va-orb               { background: #1e3a5f; }
      #va-hud.va-thinking #va-orb svg           { fill: #93c5fd; }
      #va-hud.va-thinking #va-orb::before       { border-color: #93c5fd; animation: va-spin 1s linear infinite; }

      @keyframes va-pulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50%       { transform: scale(1.35); opacity: .5; }
      }
      @keyframes va-spin {
        to { transform: rotate(360deg); }
      }

      /* ── Label ── */
      #va-label { font-weight: 500; letter-spacing: .01em; min-width: 120px; transition: color .2s; }
      #va-hud.va-listening #va-label { color: #6ee7b7; }
      #va-hud.va-thinking  #va-label { color: #93c5fd; }

      /* ── Shortcut badge ── */
      #va-shortcut {
        font-size: 10px;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 4px;
        padding: 2px 5px;
        color: #64748b;
        letter-spacing: .03em;
        white-space: nowrap;
      }
    `;
    document.head.appendChild(style);
  }

  _createHUD() {
    if (document.getElementById("va-hud")) return;
    this.hud = document.createElement("div");
    this.hud.id = "va-hud";
    this.hud.classList.add("va-hidden");
    this.hud.innerHTML = `
      <div id="va-orb">
        <!-- microphone icon -->
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 1a4 4 0 0 1 4 4v7a4 4 0 0 1-8 0V5a4 4 0 0 1 4-4zm6.5 10a.5.5 0 0 1 .5.5A7 7 0 0 1 12.5 19v2.5h2a.5.5 0 0 1 0 1h-5a.5.5 0 0 1 0-1h2V19A7 7 0 0 1 5 11.5a.5.5 0 0 1 1 0 6 6 0 0 0 12 0 .5.5 0 0 1 .5-.5z"/>
        </svg>
      </div>
      <span id="va-label">Voice Assistant</span>
      <span id="va-shortcut">⇧^J / ⇧^X</span>
    `;
    document.body.appendChild(this.hud);
    this.hudLabel = document.getElementById("va-label");

    // Reveal HUD after short delay so page can finish rendering
    setTimeout(() => this.hud.classList.remove("va-hidden"), 800);
  }

  _updateHUD(state = "idle") {
    if (!this.hud) return;
    this.hud.classList.remove("va-listening", "va-thinking");
    const labels = { idle: "Voice Assistant", listening: "Listening…", thinking: "Thinking…" };
    if (state !== "idle") this.hud.classList.add(`va-${state}`);
    this.hudLabel.textContent = labels[state] || "Voice Assistant";
  }

  // ─────────────────────────────── help ───────────────────────────────────── //

  _helpMessage() {
    return (
      "I understand natural speech — just talk to me! " +
      "Try: 'Show my audio files', 'Play music.mp3', 'Delete report.pdf', " +
      "'Take me to settings', 'Open the dashboard', 'Go to the next page', " +
      "or 'Switch to dark mode'. " +
      "Press Shift+Ctrl+J to start and Shift+Ctrl+X to stop."
    );
  }
}

/* ── Boot ── */
const assistant = new VoiceAssistant();