(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const state = {
    worldId: localStorage.getItem("rpg.worldId") || null,
    chatId: localStorage.getItem("rpg.chatId") || null,
    worlds: [],
    chats: [],
    generating: false,
    controller: null,
    speed: 0,
  };

  const el = {
    form: $("chat-form"), input: $("message"), chat: $("chat"), messages: $("messages"),
    send: $("send-button"), sidebar: $("sidebar"), toggle: $("sidebar-toggle"), closeSidebar: $("sidebar-close"),
    newChat: $("new-chat"), worldsButton: $("worlds-button"), worldPanel: $("world-panel"), closeWorld: $("close-world-panel"),
    createWorld: $("create-world-button"), realWorlds: $("real-worlds"), fantasyWorlds: $("fantasia-worlds"),
    currentWorldButton: $("current-world-button"), currentWorldName: $("current-world-name"), currentChatName: $("current-chat-name"),
    chatTree: $("chat-tree"), memoryButton: $("memory-button"), memoryPanel: $("memory-panel"), closeMemory: $("close-memory-panel"),
    currentWorldPanel: $("current-world-panel"), closeCurrentWorld: $("close-current-world-panel"), currentWorldInfo: $("current-world-info"),
    currentWorldTitle: $("current-world-panel-title"), currentWorldType: $("current-world-panel-type"),
    settingsButton: $("settings-button"), settingsPanel: $("settings-panel"), closeSettings: $("close-settings-panel"), settingsContent: $("settings-content"),
    memoryTree: $("memory-tree"), status: $("connection-status"), toast: $("toast"), worldPill: $("world-pill"), worldPillName: $("world-pill-name"),
    context: $("input-context"), welcome: $("welcome"), modelSelector: $("model-selector"), attach: $("attach-button"), share: $("share-button"),
  };

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[char]));
  }

  function markdown(text) {
    let html = escapeHtml(text);
    html = html.replace(/```([\s\S]*?)```/g, (_, code) => `<pre><code>${code.trim()}</code></pre>`);
    html = html.replace(/`([^`\n]+)`/g, "<code>$1</code>");
    html = html.replace(/^### (.*)$/gm, "<h3>$1</h3>");
    html = html.replace(/^## (.*)$/gm, "<h2>$1</h2>");
    html = html.replace(/^# (.*)$/gm, "<h1>$1</h1>");
    html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, "<em>$1</em>");
    html = html.replace(/^&gt; (.*)$/gm, "<blockquote>$1</blockquote>");
    html = html.replace(/^(?:[-*]) (.*)$/gm, "<li>$1</li>");
    html = html.replace(/(<li>.*?<\/li>)(?:\n|<br>)(?=<li>)/gs, "$1");
    html = html.replace(/\n/g, "<br>");
    return html;
  }

  function toast(message, duration = 3000) {
    el.toast.textContent = message;
    el.toast.classList.add("visible");
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => el.toast.classList.remove("visible"), duration);
  }

  async function api(url, options = {}) {
    const response = await fetch(url, options);
    const type = response.headers.get("content-type") || "";
    if (!response.ok) {
      const body = await response.text();
      throw new Error(body || `Erro HTTP ${response.status}`);
    }
    if (!type.includes("application/json")) throw new Error("O servidor retornou uma página em vez de JSON.");
    return response.json();
  }

  function saveSelection() {
    if (state.worldId) localStorage.setItem("rpg.worldId", state.worldId); else localStorage.removeItem("rpg.worldId");
    if (state.chatId) localStorage.setItem("rpg.chatId", state.chatId); else localStorage.removeItem("rpg.chatId");
  }

  function selectedWorld() { return state.worlds.find((world) => world.id === state.worldId) || null; }

  function worldLabel(world) {
    return world?.nome || `Mundo ${world?.numero || world?.id || ""}`;
  }

  function setGenerating(value) {
    state.generating = value;
    el.send.textContent = value ? "■" : "↑";
    el.send.classList.toggle("stop", value);
    el.send.disabled = !value && !el.input.value.trim();
    el.input.setAttribute("aria-busy", String(value));
  }

  function scrollBottom() { el.chat.scrollTop = el.chat.scrollHeight; }

  function clearMessages() {
    el.messages.innerHTML = "";
  }

  function addMessage(role, text = "", streaming = false) {
    const row = document.createElement("article");
    row.className = `message ${role}`;
    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = role === "user" ? "R" : "✦";
    const body = document.createElement("div");
    body.className = "message-body";
    const content = document.createElement("div");
    content.className = "message-content";
    if (role === "assistant") content.innerHTML = markdown(text);
    else content.textContent = text;
    body.appendChild(content);
    row.append(avatar, body);
    el.messages.appendChild(row);
    scrollBottom();
    return content;
  }

  function showWelcome() {
    clearMessages();
    const box = document.createElement("div");
    box.className = "welcome";
    box.innerHTML = `<div class="welcome-mark">✦</div><h1>Simule o seu mundo.</h1><p>${state.worldId ? `Você está em <strong>${escapeHtml(worldLabel(selectedWorld()))}</strong>. Escolha uma ação para continuar.` : "Escolha um mundo para começar uma simulação persistente."}</p><div class="quick-actions"><button type="button" data-quick="Mundos">◇ Escolher mundo</button><button type="button" data-quick="Memória">▤ Ver memória</button></div>`;
    el.messages.appendChild(box);
  }

  function renderChat(chat) {
    clearMessages();
    if (!chat || !chat.mensagens?.length) { showWelcome(); return; }
    chat.mensagens.forEach((message) => addMessage(message.role === "user" ? "user" : "assistant", message.content));
    scrollBottom();
  }

  function renderWorlds() {
    const render = (container, kind) => {
      container.innerHTML = "";
      const worlds = state.worlds.filter((world) => world.tipo === kind);
      if (!worlds.length) {
        container.innerHTML = `<div class="empty-state">Nenhum mundo ainda.</div>`;
        return;
      }
      worlds.forEach((world) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = `world-item ${world.id === state.worldId ? "selected" : ""}`;
        button.dataset.worldId = world.id;
        button.innerHTML = `<span class="world-icon">${kind === "fantasia" ? "✦" : "🌎"}</span><span class="world-item-main"><strong>${escapeHtml(worldLabel(world))}</strong><small>ID ${escapeHtml(world.id)}</small></span><span class="world-arrow">›</span>`;
        button.addEventListener("click", () => selectWorld(world.id));
        container.appendChild(button);
      });
    };
    render(el.realWorlds, "real");
    render(el.fantasyWorlds, "fantasia");
  }

  function renderChatTree() {
    el.chatTree.innerHTML = "";
    if (!state.worldId) return;
    const world = selectedWorld();
    const header = document.createElement("div");
    header.className = "tree-world-label";
    header.innerHTML = `<span>▾</span><span>${escapeHtml(worldLabel(world))}</span>`;
    el.chatTree.appendChild(header);
    state.chats.forEach((chat) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `tree-chat ${chat.id === state.chatId ? "selected" : ""}`;
      button.innerHTML = `<span class="tree-line">└</span><span class="tree-chat-icon">◌</span><span class="tree-chat-name">${escapeHtml(chat.nome)}</span><span class="tree-chat-id">${chat.id}</span>`;
      button.addEventListener("click", () => selectChat(chat.id));
      el.chatTree.appendChild(button);
    });
  }

  function updateHeader() {
    const world = selectedWorld();
    const chat = state.chats.find((item) => item.id === state.chatId);
    el.currentWorldName.textContent = world ? worldLabel(world) : "Nenhum mundo";
    el.currentChatName.textContent = chat?.nome || (world ? worldLabel(world) : "RPG Simulator");
    el.context.textContent = world ? `ID ${world.id} · ${state.chats.length} conversa${state.chats.length === 1 ? "" : "s"}` : "Nenhum mundo selecionado";
    el.worldPill.classList.toggle("hidden", !world);
    if (world) el.worldPillName.textContent = world.id;
  }

  async function loadWorlds() {
    const data = await api("/api/worlds");
    state.worlds = data.mundos || [];
    renderWorlds();
    if (!state.worldId && state.worlds.length) {
      await selectWorld(state.worlds[0].id, true);
    } else if (state.worldId && !state.worlds.some((w) => w.id === state.worldId)) {
      state.worldId = state.chatId = null;
      saveSelection();
      updateHeader();
      showWelcome();
    }
  }

  async function loadChats() {
    if (!state.worldId) { state.chats = []; renderChatTree(); updateHeader(); return; }
    const data = await api(`/api/worlds/${encodeURIComponent(state.worldId)}/chats`);
    state.chats = data.chats || [];
    renderChatTree();
    if (!state.chatId || !state.chats.some((chat) => chat.id === state.chatId)) state.chatId = state.chats[0]?.id || null;
    saveSelection();
    updateHeader();
    if (state.chatId) await loadChat(state.chatId); else showWelcome();
  }

  async function loadChat(chatId) {
    const data = await api(`/api/worlds/${encodeURIComponent(state.worldId)}/chats/${encodeURIComponent(chatId)}`);
    state.chatId = chatId;
    saveSelection();
    renderChat(data);
    renderChatTree();
    updateHeader();
  }

  async function selectWorld(worldId, silent = false) {
    if (state.generating) return;
    state.worldId = worldId;
    state.chatId = null;
    saveSelection();
    await loadChats();
    renderWorlds();
    if (!silent) closeOverlay(el.worldPanel);
    if (window.innerWidth < 700) el.sidebar.classList.remove("open");
  }

  async function selectChat(chatId) {
    if (!state.worldId || state.generating) return;
    await loadChat(chatId);
    if (window.innerWidth < 700) el.sidebar.classList.remove("open");
  }

  async function createChat() {
    if (!state.worldId || state.generating) { openOverlay(el.worldPanel); return; }
    const data = await api(`/api/worlds/${encodeURIComponent(state.worldId)}/chats`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ nome: "Nova conversa" }) });
    state.chats.push(data.chat);
    state.chatId = data.chat.id;
    saveSelection();
    renderChatTree(); updateHeader(); renderChat(data.chat);
    toast("Nova conversa criada.");
  }

  async function createWorld() {
    const kind = prompt("Tipo do mundo:\n1 = Real\n2 = Fantasia", "1");
    if (kind === null) return;
    const type = kind.trim() === "2" ? "fantasia" : "real";
    const name = prompt("Nome opcional do mundo:", "");
    try {
      const data = await api("/api/worlds", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ tipo: type, nome: name || undefined }) });
      await loadWorlds();
      await selectWorld(data.world.id);
      toast(`${worldLabel(data.world)} criado.`);
    } catch (error) { toast(error.message); }
  }

  async function sendMessage() {
    if (state.generating) { state.controller?.abort(); return; }
    const text = el.input.value.trim();
    if (!text || !state.worldId || !state.chatId) {
      if (!state.worldId) toast("Escolha um mundo primeiro.");
      return;
    }
    el.input.value = "";
    resizeInput();
    if (el.welcome) el.welcome.remove();
    addMessage("user", text);
    const assistant = addMessage("assistant", "");
    assistant.innerHTML = `<span class="typing">▍</span>`;
    state.generating = true;
    state.controller = new AbortController();
    setGenerating(true);
    let full = "";
    try {
      const response = await fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ world_id: state.worldId, chat_id: state.chatId, message: text }), signal: state.controller.signal });
      if (!response.ok) throw new Error(await response.text() || `Erro HTTP ${response.status}`);
      if (!response.body) throw new Error("Streaming não suportado pelo navegador.");
      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        full += chunk;
        const marker = full.indexOf("[[STREAM_ERROR]]");
        if (marker >= 0) throw new Error(full.slice(marker + "[[STREAM_ERROR]]".length).trim());
        assistant.innerHTML = markdown(full) + `<span class="typing">▍</span>`;
        scrollBottom();
        if (state.speed) await sleep(state.speed);
      }
      assistant.innerHTML = markdown(full);
      await refreshChatsOnly();
    } catch (error) {
      if (error.name === "AbortError") {
        assistant.innerHTML = full ? markdown(full) : `<span class="interrupted">Geração interrompida.</span>`;
      } else {
        assistant.innerHTML = `<span class="error-text">Erro: ${escapeHtml(error.message)}</span>`;
        toast(error.message);
      }
    } finally {
      state.generating = false;
      state.controller = null;
      setGenerating(false);
      el.input.focus();
    }
  }

  async function refreshChatsOnly() {
    if (!state.worldId) return;
    try {
      const data = await api(`/api/worlds/${encodeURIComponent(state.worldId)}/chats`);
      state.chats = data.chats || [];
      renderChatTree(); updateHeader();
    } catch (_) {}
  }

  async function openMemory() {
    if (!state.worldId) { toast("Escolha um mundo primeiro."); return; }
    try {
      const [memory, files] = await Promise.all([
        api(`/api/worlds/${encodeURIComponent(state.worldId)}/memory`),
        api(`/api/worlds/${encodeURIComponent(state.worldId)}/files`),
      ]);
      renderMemory(memory.memory || {}, files.tree || []);
      openOverlay(el.memoryPanel);
    } catch (error) { toast(error.message); }
  }

  function renderMemory(memory, tree) {
    el.memoryTree.innerHTML = "";
    tree.forEach((folder) => {
      const section = document.createElement("details");
      section.className = "memory-folder";
      section.open = folder.name !== "chat";
      const summary = document.createElement("summary");
      summary.innerHTML = `<span>📁</span><strong>${escapeHtml(folder.name)}</strong><small>${folder.files.length}</small>`;
      section.appendChild(summary);
      if (folder.files.length) {
        const list = document.createElement("div"); list.className = "memory-files";
        folder.files.forEach((file) => { const item = document.createElement("div"); item.className = "memory-file"; item.innerHTML = `<span>◌</span>${escapeHtml(file.replace(`${folder.name}/`, ""))}`; list.appendChild(item); });
        section.appendChild(list);
      } else {
        const empty = document.createElement("div"); empty.className = "memory-empty"; empty.textContent = "Vazio"; section.appendChild(empty);
      }
      el.memoryTree.appendChild(section);
    });
    const stats = document.createElement("div"); stats.className = "memory-summary"; stats.textContent = `${Object.keys(memory).length} categorias carregadas · memória gerenciada pela Carmilla`; el.memoryTree.appendChild(stats);
  }

  async function openCurrentWorld() {
    if (!state.worldId) { toast("Nenhum mundo selecionado."); return; }
    try {
      const data = await api(`/api/worlds/${encodeURIComponent(state.worldId)}`);
      el.currentWorldTitle.textContent = worldLabel(data);
      el.currentWorldType.textContent = `${data.tipo === "fantasia" ? "Mundo Fantasia" : "Mundo Real"} · ID ${data.id}`;
      el.currentWorldInfo.innerHTML = Object.entries(data).map(([key, value]) => `<div class="info-card"><span>${escapeHtml(key)}</span><strong>${escapeHtml(typeof value === "object" ? JSON.stringify(value) : value)}</strong></div>`).join("");
      openOverlay(el.currentWorldPanel);
    } catch (error) { toast(error.message); }
  }

  async function openSettings() {
    try {
      const health = await api("/api/health");
      el.settingsContent.innerHTML = `<div class="setting-row"><span>Modelo</span><strong>${escapeHtml(health.model)}</strong></div><div class="setting-row"><span>Ollama</span><strong class="${health.ollama ? "ok" : "bad"}">${health.ollama ? "Conectado" : "Offline"}</strong></div><div class="setting-row"><span>Carmilla</span><strong>${escapeHtml(health.carmilla.name)} ${escapeHtml(health.carmilla.version)}</strong></div><div class="setting-row"><span>Mundos</span><strong>${state.worlds.length}</strong></div>`;
      openOverlay(el.settingsPanel);
    } catch (error) { toast(error.message); }
  }

  function openOverlay(overlay) { overlay.classList.remove("hidden"); overlay.setAttribute("aria-hidden", "false"); }
  function closeOverlay(overlay) { overlay.classList.add("hidden"); overlay.setAttribute("aria-hidden", "true"); }

  function resizeInput() {
    el.input.style.height = "auto";
    el.input.style.height = `${Math.min(el.input.scrollHeight, 180)}px`;
    if (!state.generating) el.send.disabled = !el.input.value.trim();
  }

  async function checkHealth() {
    try {
      const health = await api("/api/health");
      el.status.classList.toggle("offline", !health.ollama);
      el.status.innerHTML = `<span class="status-dot"></span><span>${health.ollama ? `${escapeHtml(health.model)} conectado` : "Ollama offline"}</span>`;
    } catch (_) {
      el.status.classList.add("offline"); el.status.innerHTML = `<span class="status-dot"></span><span>Servidor indisponível</span>`;
    }
  }

  el.form.addEventListener("submit", (event) => { event.preventDefault(); sendMessage(); });
  el.input.addEventListener("input", resizeInput);
  el.input.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    if (event.shiftKey || event.ctrlKey) return;
    event.preventDefault(); if (!state.generating) sendMessage();
  });
  el.send.addEventListener("click", (event) => { if (state.generating) { event.preventDefault(); state.controller?.abort(); } });
  el.newChat.addEventListener("click", createChat);
  el.worldsButton.addEventListener("click", () => openOverlay(el.worldPanel));
  el.currentWorldButton.addEventListener("click", openCurrentWorld);
  el.memoryButton.addEventListener("click", openMemory);
  el.settingsButton.addEventListener("click", openSettings);
  el.createWorld.addEventListener("click", createWorld);
  el.closeWorld.addEventListener("click", () => closeOverlay(el.worldPanel));
  el.closeMemory.addEventListener("click", () => closeOverlay(el.memoryPanel));
  el.closeCurrentWorld.addEventListener("click", () => closeOverlay(el.currentWorldPanel));
  el.closeSettings.addEventListener("click", () => closeOverlay(el.settingsPanel));
  [el.worldPanel, el.memoryPanel, el.currentWorldPanel, el.settingsPanel].forEach((overlay) => overlay.addEventListener("click", (event) => { if (event.target === overlay) closeOverlay(overlay); }));
  el.toggle.addEventListener("click", () => el.sidebar.classList.add("open"));
  el.closeSidebar.addEventListener("click", () => el.sidebar.classList.remove("open"));
  el.attach.addEventListener("click", () => state.worldId ? openMemory() : toast("Escolha um mundo primeiro."));
  el.share.addEventListener("click", async () => { try { await navigator.clipboard.writeText(location.href); toast("Endereço copiado."); } catch (_) { toast("Não foi possível copiar."); } });
  document.addEventListener("click", (event) => { const quick = event.target.closest("[data-quick]"); if (!quick) return; if (quick.dataset.quick === "Mundos") openOverlay(el.worldPanel); else openMemory(); });
  document.querySelectorAll(".group-header").forEach((button) => button.addEventListener("click", () => button.parentElement.classList.toggle("collapsed")));
  el.modelSelector.addEventListener("click", openCurrentWorld);

  (async function init() {
    resizeInput();
    showWelcome();
    try { await loadWorlds(); } catch (error) { toast(error.message, 5000); }
    updateHeader();
    await checkHealth();
    el.input.focus();
  })();
})();
