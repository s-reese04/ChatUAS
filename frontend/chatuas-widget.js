/*
 * ChatUAS Widget
 * Einbinden:  <script src="chatuas-widget.js" defer></script>
 * Optional davor konfigurieren:
 *   <script>window.CHATUAS_CONFIG = { apiUrl: "https://bot.example.de/chat/stream" };</script>
 */
(() => {
    "use strict";

    const CONFIG = Object.assign(
        {
            apiUrl: "http://127.0.0.1:8001/chat/stream",
            title: "Fragen zur Hochschule",
            subtitle: "Antworten aus den Webseiten der Frankfurt UAS",
            welcome:
            "Hallo! Stell mir eine Frage zu Studium, Bewerbung oder Organisation. Ich suche die Antwort auf den Webseiten der Hochschule.",
            accent: "#0d5c75",
            maxLength: 500,
            timeoutMs: 180000,
            // true: sendet zusätzlich "history" (letzte Nachrichten) mit. Das Backend ignoriert das Feld,
            // bis rag() es auswertet.
            sendHistory: false,
        },
        window.CHATUAS_CONFIG || {}
    );

    if (document.getElementById("chatuas-widget")) return;

    const CSS = `
    :host { all: initial; }
    *, *::before, *::after { box-sizing: border-box; }
    .wrap {
        --ink: #1c2430; --muted: #5a6676; --paper: #ffffff; --mist: #eef1f5; --line: #d9dee6;
        --accent: ${CONFIG.accent};
        font: 15px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
        color: var(--ink);
    }
    button, input { font: inherit; color: inherit; }
    :focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

    .launcher {
        position: fixed; right: 20px; bottom: max(20px, env(safe-area-inset-bottom));
        width: 56px; height: 56px; border: 0; border-radius: 50%;
        background: var(--accent); color: #fff; cursor: pointer;
        display: grid; place-items: center;
        box-shadow: 0 4px 16px rgba(20, 30, 45, .28);
        z-index: 2147483000;
    }
    .launcher svg { width: 26px; height: 26px; }

    .panel {
        position: fixed; right: 20px; bottom: calc(max(20px, env(safe-area-inset-bottom)) + 68px);
        width: min(400px, calc(100vw - 24px));
        height: min(600px, calc(100dvh - 110px));
        display: flex; flex-direction: column;
        background: var(--paper); border: 1px solid var(--line); border-radius: 12px;
        box-shadow: 0 12px 40px rgba(20, 30, 45, .22);
        overflow: hidden; z-index: 2147483000;
        opacity: 0; transform: translateY(8px); visibility: hidden;
        transition: opacity .16s, transform .16s, visibility 0s .16s;
    }
    .panel.open { opacity: 1; transform: none; visibility: visible; transition-delay: 0s; }

    header {
        display: flex; align-items: center; justify-content: space-between; gap: 12px;
        padding: 12px 14px; background: var(--accent); color: #fff;
    }
    .title { font-weight: 600; }
    .subtitle { font-size: 13px; opacity: .85; }
    .close {
        flex: none; width: 32px; height: 32px; border: 0; border-radius: 8px;
        background: transparent; color: #fff; cursor: pointer; display: grid; place-items: center;
    }
    .close:hover { background: rgba(255, 255, 255, .16); }
    .close:focus-visible { outline-color: #fff; }
    .close svg { width: 18px; height: 18px; }

    .messages {
        flex: 1; overflow-y: auto; padding: 14px; background: var(--mist);
        display: flex; flex-direction: column; gap: 10px;
    }
    .msg {
        max-width: 88%; padding: 9px 12px; border-radius: 10px;
        overflow-wrap: anywhere;
    }
    .msg .text { white-space: pre-wrap; }
    .msg.user {
        align-self: flex-end; background: var(--accent); color: #fff;
        border-bottom-right-radius: 3px; white-space: pre-wrap;
    }
    .msg.bot {
        align-self: flex-start; background: var(--paper); border: 1px solid var(--line);
        border-bottom-left-radius: 3px;
    }
    .msg.error { background: #fdf3f2; border-color: #d9847a; color: #8f1f14; }

    .sources { margin-top: 8px; font-size: 13px; }
    .sources-toggle {
        padding: 0; border: 0; background: none; cursor: pointer;
        color: var(--accent); font-weight: 600;
    }
    .sources-toggle:hover { text-decoration: underline; }
    .sources-list { list-style: none; margin: 6px 0 0; padding: 6px 0 0; border-top: 1px solid var(--line); }
    .sources-list[hidden] { display: none; }
    .sources-list a {
        display: block; padding: 2px 0; color: var(--accent);
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    .sources-list a:hover { text-decoration: underline; }

    .dots { display: inline-flex; gap: 4px; padding: 5px 0; }
    .dots i {
        width: 6px; height: 6px; border-radius: 50%; background: #8893a3;
        animation: pulse 1s infinite ease-in-out;
    }
    .dots i:nth-child(2) { animation-delay: .15s; }
    .dots i:nth-child(3) { animation-delay: .3s; }
    @keyframes pulse { 0%, 80%, 100% { opacity: .3; } 40% { opacity: 1; } }

    .composer { display: flex; gap: 8px; padding: 10px; border-top: 1px solid var(--line); background: var(--paper); }
    .composer input {
        flex: 1; min-width: 0; padding: 9px 12px;
        border: 1px solid var(--line); border-radius: 8px; background: var(--paper);
    }
    .composer button {
        flex: none; padding: 9px 14px; border: 0; border-radius: 8px;
        background: var(--accent); color: #fff; font-weight: 600; cursor: pointer;
    }
    .composer button:disabled, .composer input:disabled { opacity: .55; cursor: not-allowed; }
    .note { margin: 0; padding: 0 12px 10px; font-size: 12px; color: var(--muted); background: var(--paper); }

    @media (max-width: 480px) {
        .panel { left: 8px; right: 8px; width: auto; height: calc(100dvh - 100px); }
    }
    @media (prefers-reduced-motion: reduce) {
        .panel { transition: none; }
        .dots i { animation: none; opacity: .6; }
    }
    `;

    const HTML = `
    <div class="wrap">
    <section class="panel" id="panel" role="dialog" aria-label="Chat mit dem Hochschul-Assistenten">
    <header>
    <div><div class="title"></div><div class="subtitle"></div></div>
    <button class="close" type="button" aria-label="Chat schließen">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>
    </button>
    </header>
    <div class="messages" role="log" aria-live="polite"></div>
    <form class="composer" autocomplete="off">
    <input type="text" name="q" aria-label="Deine Frage" placeholder="Frage eingeben" />
    <button type="submit">Senden</button>
    </form>
    <p class="note">KI-Assistent. Antworten ohne Gewähr, bitte Quellen prüfen.</p>
    </section>
    <button class="launcher" type="button" aria-label="Chat öffnen" aria-expanded="false" aria-controls="panel">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="M4 5h16v11H9l-5 4z"/></svg>
    </button>
    </div>
    `;

    const host = document.createElement("div");
    host.id = "chatuas-widget";
    const root = host.attachShadow({ mode: "open" });
    root.innerHTML = `<style>${CSS}</style>${HTML}`;

    const $ = (sel) => root.querySelector(sel);
    const panel = $(".panel");
    const launcher = $(".launcher");
    const closeBtn = $(".close");
    const list = $(".messages");
    const form = $(".composer");
    const input = form.querySelector("input");
    const sendBtn = form.querySelector("button");

    $(".title").textContent = CONFIG.title;
    $(".subtitle").textContent = CONFIG.subtitle;
    input.maxLength = CONFIG.maxLength;

    const history = []; // { role: "user" | "assistant", content }
    let busy = false;

    // ---------- Hilfsfunktionen ----------

    function setOpen(open, moveFocus) {
        panel.classList.toggle("open", open);
        launcher.setAttribute("aria-expanded", String(open));
        launcher.setAttribute("aria-label", open ? "Chat schließen" : "Chat öffnen");
        if (moveFocus) (open ? input : launcher).focus();
    }

    function addMessage(role, text) {
        const el = document.createElement("div");
        el.className = `msg ${role}`;
        if (text) el.textContent = text;
        list.appendChild(el);
        list.scrollTop = list.scrollHeight;
        return el;
    }

    function showText(el, text) {
        const stick = list.scrollHeight - list.scrollTop - list.clientHeight < 60;
        el.textContent = text;
        if (stick) list.scrollTop = list.scrollHeight;
    }

    // Das Backend hängt die Quellen als Text an: "<Antwort>\n\nQuellen:\n<url>\n<url>".
    // Erkannt wird die letzte Zeile "Quellen:". Alle URLs dahinter werden eingesammelt,
    // egal in welchem Zeilenformat und ob mit \n oder \r\n.
    const SOURCES_RE = /\n[ \t]*Quellen:[ \t]*\r?\n/g;
    const PARTIAL_RE = /\n[ \t]*Q(?:u(?:e(?:l(?:l(?:e(?:n(?::[ \t]*)?)?)?)?)?)?)?\r?$/;
    const URL_RE = /https?:\/\/[^\s<>"')\]]+/g;

    function splitAnswer(full) {
        let m;
        let last = null;
        SOURCES_RE.lastIndex = 0;
        while ((m = SOURCES_RE.exec(full))) last = m;
        // Noch kein vollständiger Marker: angefangenes "Quellen:" am Ende nicht anzeigen
        if (!last) return { text: full.replace(PARTIAL_RE, "").trim(), urls: [] };
        const found = full.slice(last.index + last[0].length).match(URL_RE) || [];
        const urls = [...new Set(found.map((u) => u.replace(/[.,;:!?]+$/, "")))];
        return { text: full.slice(0, last.index).trim(), urls };
    }

    function linkLabel(url) {
        try {
            const u = new URL(url);
            const path = u.pathname === "/" ? "" : u.pathname.replace(/\/$/, "");
            return u.hostname.replace(/^www\./, "") + path;
        } catch {
            return url;
        }
    }

    function renderAnswer(el, full) {
        const { text, urls } = splitAnswer(full);
        el.textContent = "";
        const body = document.createElement("div");
        body.className = "text";
        body.textContent = text;
        el.appendChild(body);

        if (urls.length) {
            const box = document.createElement("div");
            box.className = "sources";

            const toggle = document.createElement("button");
            toggle.type = "button";
            toggle.className = "sources-toggle";
            toggle.textContent = `Quellen anzeigen (${urls.length})`;
            toggle.setAttribute("aria-expanded", "false");

            const ul = document.createElement("ul");
            ul.className = "sources-list";
            ul.hidden = true;
            for (const url of urls) {
                const li = document.createElement("li");
                const a = document.createElement("a");
                a.href = url;
                a.target = "_blank";
                a.rel = "noopener noreferrer";
                a.textContent = linkLabel(url);
                a.title = url;
                li.appendChild(a);
                ul.appendChild(li);
            }

            toggle.addEventListener("click", () => {
                const open = ul.hidden; // war zu, wird jetzt geöffnet
                ul.hidden = !open;
                toggle.setAttribute("aria-expanded", String(open));
                toggle.textContent = open ? "Quellen ausblenden" : `Quellen anzeigen (${urls.length})`;
                if (open) ul.scrollIntoView?.({ block: "nearest" });
            });

            box.append(toggle, ul);
            el.appendChild(box);
        }
        list.scrollTop = list.scrollHeight;
        return text;
    }

    function errorText(err) {
        if (err.name === "AbortError") return "Die Anfrage hat zu lange gedauert. Bitte stelle die Frage noch einmal.";
        if (err instanceof TypeError) return "Der Assistent ist nicht erreichbar. Bitte versuche es später erneut.";
        return err.message || "Etwas ist schiefgelaufen. Bitte stelle die Frage noch einmal.";
    }

    function setBusy(value) {
        busy = value;
        input.disabled = value;
        sendBtn.disabled = value;
        list.setAttribute("aria-busy", String(value));
    }

    // ---------- Senden und Streamen ----------

    async function send(question) {
        setBusy(true);
        addMessage("user", question);
        history.push({ role: "user", content: question });

        const botEl = addMessage("bot");
        botEl.innerHTML = '<span class="dots" aria-label="Der Assistent antwortet"><i></i><i></i><i></i></span>';

        const payload = { question };
        if (CONFIG.sendHistory) payload.history = history.slice(-7, -1);

        const ctrl = new AbortController();
        const timer = setTimeout(() => ctrl.abort(), CONFIG.timeoutMs);

        try {
            const res = await fetch(CONFIG.apiUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
                                    signal: ctrl.signal,
            });

            if (!res.ok) {
                if (res.status === 422)
                    throw new Error(`Die Frage ist leer oder zu lang. Bitte kürze sie auf höchstens ${CONFIG.maxLength} Zeichen.`);
                if (res.status === 429) throw new Error("Zu viele Anfragen. Bitte warte einen Moment.");
                throw new Error(`Der Server hat mit Fehler ${res.status} geantwortet.`);
            }

            const reader = res.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let answer = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                answer += decoder.decode(value, { stream: true });
                showText(botEl, splitAnswer(answer).text); // Quellen erst am Ende anzeigen
            }
            answer += decoder.decode();

            if (!answer.trim()) throw new Error("Es kam keine Antwort an. Bitte stelle die Frage noch einmal.");

            const text = renderAnswer(botEl, answer);
            history.push({ role: "assistant", content: text });
        } catch (err) {
            botEl.className = "msg bot error";
            botEl.textContent = errorText(err);
        } finally {
            clearTimeout(timer);
            setBusy(false);
            input.focus();
        }
    }

    // ---------- Events ----------

    launcher.addEventListener("click", () => setOpen(!panel.classList.contains("open"), true));
    closeBtn.addEventListener("click", () => setOpen(false, true));
    root.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && panel.classList.contains("open")) setOpen(false, true);
    });
        form.addEventListener("submit", (e) => {
            e.preventDefault();
            const question = input.value.trim();
            if (!question || busy) return;
                              input.value = "";
            send(question);
        });

        addMessage("bot", CONFIG.welcome);

        const mount = () => document.body.appendChild(host);
        if (document.body) mount();
        else document.addEventListener("DOMContentLoaded", mount);
})();
