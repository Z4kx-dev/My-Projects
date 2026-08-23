(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const form = $("chat-form");
  const input = $("message");
  const chat = $("chat");
  const messages = $("messages");
  const sendButton = $("send-button");
  const sidebar = $("sidebar");
  const sidebarToggle = $("sidebar-toggle");
  const sidebarOverlay = $("sidebar-overlay");
  const newChatButton = $("new-chat");
  const worldsButton = $("worlds-button");
  const worldPanel = $("world-panel");
  const closeWorldPanel = $("close-world-panel");
  const createWorldButton = $("create-world-button");
  const realWorlds = $("real-worlds");
  const fantasiaWorlds = $("fantasia-worlds");
  const currentWorldButton = $("current-world-button");
  const currentWorldName = $("current-world-name");
  const currentChatName = $("current-chat-name");
  const chatTree = $("chat-tree");
  const treeRefresh = $("tree-refresh");
  const memoryButton = $("memory-button");
  const memoryPanel = $("memory-panel");
  const closeMemoryPanel = $("close-memory-panel");
  const currentWorldPanel = $("current-world-panel");
  const closeCurrentWorldPanel = $("close-current-world-panel");
  const currentWorldInfo = $("current-world-info");
  const currentWorldPanelTitle = $("current-world-panel-title");
  const currentWorldPanelType = $("current-world-panel-type");
  const toastContainer = $("toast-container");
  const loading = $("loading");
  const welcome = $("welcome");
  const modelSelector = $("model-selector");

  const state = {
    worlds: [],
    worldId: localStorage.getItem("rpg.worldId") || null,
    chatId: localStorage.getItem("rpg.chatId") || null,
    generating: false,
    controller: null,
    categoryOpen: {
      real: localStorage.getItem("rpg.category.real") !== "0",
      fantasia: localStorage.getItem("rpg.category.fantasia") !== "0"
    }
  };

  function normalizeId(value) {
    const text = String(value ?? "").trim();
    return /^\d+$/.test(text) ? text.padStart(3, "0") : text;
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function markdown(text) {
    let source = escapeHtml(text);
    const blocks = [];
    source = source.replace(/```(?:[a-zA-Z0-9_-]+)?\n?([\s\S]*?)```/g, (_, code) => {
      const token = `@@CODE${blocks.length}@@`;
      blocks.push(`<pre><code>${code.trim()}</code></pre>`);
      return token;
    });
    source = source.replace(/`([^`\n]+)`/g, "<code>$1</code>");
    source = source.replace(/^### (.+)$/gm, "<h3>$1</h3>");
    source = source.replace(/^## (.+)$/gm, "<h2>$1</h2>");
    source = source.replace(/^# (.+)$/gm, "<h1>$1</h1>");
    source = source.replace(/^&gt; (.+)$/gm, "<blockquote>$1</blockquote>");
    source = source.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    source = source.replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, "<em>$1</em>");
    source = source.replace(/(?:^|\n)((?:[-*] .+(?:\n|$))+)/g, (_, list) => {
      const items = list.trim().split("\n").map(line => `<li>${line.replace(/^[-*] /, "")}</li>`).join("");
      return `\n<ul>${items}</ul>\n`;
    });
    source = source.replace(/\n{2,}/g, "</p><p>");
    source = source.replace(/\n/g, "<br>");
    source = `<p>${source}</p>`;
    source = source.replace(/<p>(\s*<(?:h[1-3]|ul|pre|blockquote))/g, "$1");
    source = source.replace(/(<\/(?:h[1-3]|ul|pre|blockquote)>)<\/p>/g, "$1");
    blocks.forEach((block, index) => {
      source = source.replace(`@@CODE${index}@@`, block);
    });
    return source;
  }

  function toast(message, type = "") {
    const node = document.createElement("div");
    node.className = `toast ${type}`;
    node.textContent = message;
    toastContainer.appendChild(node);
    setTimeout(() => node.remove(), 3600);
  }

  function setLoading(value) {
    loading.hidden = !value;
  }

  function saveSelection() {
    if (state.worldId) localStorage.setItem("rpg.worldId", state.worldId);
    else localStorage.removeItem("rpg.worldId");
    if (state.chatId) localStorage.setItem("rpg.chatId", state.chatId);
    else localStorage.removeItem("rpg.chatId");
  }

  function closeSidebar() {
    sidebar.classList.remove("open");
    sidebarOverlay.hidden = true;
  }

  function openSidebar() {
    sidebar.classList.add("open");
    sidebarOverlay.hidden = false;
  }

  function showModal(node) {
    if (!node) return;
    node.hidden = false;
    document.body.style.overflow = "hidden";
  }

  function hideModal(node) {
    if (!node) return;
    node.hidden = true;
    if ([worldPanel, currentWorldPanel, memoryPanel].every(panel => panel.hidden)) {
      document.body.style.overflow = "";
    }
  }

  async function api(url, options = {}) {
    const response = await fetch(url, {
      credentials: "same-origin",
      ...options,
      headers: {
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...(options.headers || {})
      }
    });
    const contentType = response.headers.get("content-type") || "";
    if (!response.ok) {
      const body = await response.text();
      let message = body;
      try { message = JSON.parse(body).error || body; } catch (_) {}
      throw new Error(message || `Erro HTTP ${response.status}`);
    }
    if (!contentType.includes("application/json")) {
      throw new Error("O servidor não retornou JSON.");
    }
    return response.json();
  }

  function worldCategory(world) {
    const raw = String(world.tipo || world.type || world.categoria || world.category || "").toLowerCase();
    if (["fantasia", "fantasy", "ficcao", "fiction"].includes(raw)) return "fantasia";
    return "real";
  }

  function worldById(id) {
    return state.worlds.find(world => normalizeId(world.id) === normalizeId(id)) || null;
  }

  function chatById(world, id) {
    return (world?.chats || []).find(chat => normalizeId(chat.id) === normalizeId(id)) || null;
  }

  function renderWorldCards() {
    renderWorldList(realWorlds, state.worlds.filter(w => worldCategory(w) === "real"));
    renderWorldList(fantasiaWorlds, state.worlds.filter(w => worldCategory(w) === "fantasia"));
  }

  function renderWorldList(container, worlds) {
    container.replaceChildren();
    if (!worlds.length) {
      const empty = document.createElement("div");
      empty.className = "world-empty";
      empty.textContent = "Nenhum mundo disponível.";
      container.appendChild(empty);
      return;
    }
    worlds.forEach(world => {
      const id = normalizeId(world.id);
      const card = document.createElement("button");
      card.type = "button";
      card.className = `world-card ${id === state.worldId ? "active" : ""}`;
      card.dataset.worldId = id;
      const count = Array.isArray(world.chats) ? world.chats.length : 0;
      card.innerHTML = `<span class="world-card-id">${escapeHtml(id)}</span><span class="world-card-main"><span class="world-card-name">${escapeHtml(world.nome || `Mundo ${id}`)}</span><span class="world-card-meta">${count} ${count === 1 ? "chat" : "chats"}</span></span><span class="world-card-arrow">›</span>`;
      card.addEventListener("click", () => selectWorld(id));
      container.appendChild(card);
    });
  }

  function renderTree() {
    chatTree.replaceChildren();
    const categories = [
      ["real", "🌎", "Mundo Real"],
      ["fantasia", "✨", "Mundo Fantasia"]
    ];
    categories.forEach(([category, icon, label]) => {
      const worlds = state.worlds.filter(world => worldCategory(world) === category);
      const section = document.createElement("div");
      section.className = `tree-category ${state.categoryOpen[category] ? "" : "collapsed"}`;
      const header = document.createElement("button");
      header.type = "button";
      header.className = "tree-category-header";
      header.innerHTML = `<span class="tree-arrow">▾</span><span>${icon}</span><span>${label}</span>`;
      header.addEventListener("click", () => {
        state.categoryOpen[category] = !state.categoryOpen[category];
        localStorage.setItem(`rpg.category.${category}`, state.categoryOpen[category] ? "1" : "0");
        renderTree();
      });
      section.appendChild(header);
      const items = document.createElement("div");
      items.className = "tree-items";
      worlds.forEach(world => {
        const id = normalizeId(world.id);
        const worldNode = document.createElement("div");
        worldNode.className = "tree-world";
        const worldHeader = document.createElement("button");
        worldHeader.type = "button";
        worldHeader.className = "tree-world-header";
        worldHeader.innerHTML = `<span class="tree-arrow">▾</span><span class="tree-world-id">${escapeHtml(id)}</span><span class="tree-world-name">${escapeHtml(world.nome || `Mundo ${id}`)}</span>`;
        worldHeader.addEventListener("click", () => selectWorld(id));
        worldNode.appendChild(worldHeader);
        const chats = document.createElement("div");
        chats.className = "tree-chat-list";
        (world.chats || []).forEach(chatData => {
          const chatId = normalizeId(chatData.id);
          const node = document.createElement("button");
          node.type = "button";
          node.className = `tree-chat ${id === state.worldId && chatId === state.chatId ? "active" : ""}`;
          node.innerHTML = `<span class="tree-chat-icon">•</span><span>${escapeHtml(chatData.nome || `Chat ${chatId}`)}</span>`;
          node.title = `Mundo ${id} · Chat ${chatId}`;
          node.addEventListener("click", () => selectChat(id, chatId));
          chats.appendChild(node);
        });
        if (!chats.children.length) {
          const empty = document.createElement("div");
          empty.className = "tree-empty";
          empty.textContent = "Sem chats";
          chats.appendChild(empty);
        }
        worldNode.appendChild(chats);
        items.appendChild(worldNode);
      });
      if (!worlds.length) {
        const empty = document.createElement("div");
        empty.className = "tree-empty";
        empty.textContent = "Nenhum mundo";
        items.appendChild(empty);
      }
      section.appendChild(items);
      chatTree.appendChild(section);
    });
  }

  function updateHeader() {
    const world = worldById(state.worldId);
    const chatData = chatById(world, state.chatId);
    currentWorldName.textContent = world ? `${world.nome || `Mundo ${state.worldId}`} · ${normalizeId(world.id)}` : "Nenhum mundo";
    currentChatName.textContent = chatData?.nome || (world ? `Mundo ${normalizeId(world.id)}` : "RPG Simulator");
    renderTree();
    renderWorldCards();
  }

  function clearMessages() {
    messages.replaceChildren();
  }

  function addMessage(role, text = "") {
    if (welcome?.isConnected) welcome.remove();
    const wrapper = document.createElement("article");
    wrapper.className = `message ${role}`;
    const content = document.createElement("div");
    content.className = "message-content";
    if (role === "assistant") content.innerHTML = markdown(text);
    else content.textContent = text;
    wrapper.appendChild(content);
    if (role === "assistant") {
      const actions = document.createElement("div");
      actions.className = "message-actions";
      const copy = document.createElement("button");
      copy.type = "button";
      copy.className = "message-action";
      copy.textContent = "⧉";
      copy.title = "Copiar";
      copy.addEventListener("click", async () => {
        await navigator.clipboard.writeText(text);
        toast("Mensagem copiada.", "success");
      });
      actions.appendChild(copy);
      wrapper.appendChild(actions);
    }
    messages.appendChild(wrapper);
    scrollToBottom();
    return content;
  }

  function scrollToBottom() {
    requestAnimationFrame(() => { chat.scrollTop = chat.scrollHeight; });
  }

  async function loadWorlds() {
    const data = await api("/api/worlds");
    state.worlds = Array.isArray(data.mundos) ? data.mundos : [];
    state.worlds.forEach(world => {
      world.id = normalizeId(world.id);
      world.chats = Array.isArray(world.chats) ? world.chats : [];
      world.chats.forEach(item => item.id = normalizeId(item.id));
    });
    renderTree();
    renderWorldCards();
    updateHeader();
  }

  async function selectWorld(id) {
    id = normalizeId(id);
    const world = worldById(id);
    if (!world) return toast("Mundo não encontrado.", "error");
    state.worldId = id;
    const availableChat = chatById(world, state.chatId);
    if (!availableChat) state.chatId = world.chats[0]?.id || null;
    saveSelection();
    updateHeader();
    hideModal(worldPanel);
    closeSidebar();
    if (state.chatId) await loadChat(id, state.chatId);
    else showEmptyChat();
  }

  async function selectChat(worldId, chatId) {
    worldId = normalizeId(worldId);
    chatId = normalizeId(chatId);
    if (!worldById(worldId) || !chatById(worldById(worldId), chatId)) {
      await loadWorlds();
    }
    if (!worldById(worldId) || !chatById(worldById(worldId), chatId)) return toast("Chat não encontrado.", "error");
    state.worldId = worldId;
    state.chatId = chatId;
    saveSelection();
    updateHeader();
    closeSidebar();
    await loadChat(worldId, chatId);
  }

  async function loadChat(worldId, chatId) {
    setLoading(true);
    try {
      const data = await api(`/api/worlds/${encodeURIComponent(worldId)}/chats/${encodeURIComponent(chatId)}`);
      clearMessages();
      const history = Array.isArray(data.mensagens) ? data.mensagens : [];
      if (!history.length) {
        showEmptyChat(false);
        return;
      }
      history.forEach(item => {
        if (item.role === "user" || item.role === "assistant") addMessage(item.role, item.content || "");
      });
      scrollToBottom();
    } catch (error) {
      toast(`Não foi possível carregar o chat: ${error.message}`, "error");
      showEmptyChat();
    } finally {
      setLoading(false);
    }
  }

  function showEmptyChat(showWelcome = true) {
    clearMessages();
    if (!showWelcome) return;
    const node = document.createElement("div");
    node.className = "welcome";
    node.innerHTML = `<div class="welcome-icon">✦</div><h1>${escapeHtml(currentChatName.textContent || "RPG Simulator")}</h1><p>Envie sua primeira ação para iniciar a simulação.</p>`;
    messages.appendChild(node);
  }

  async function createChat() {
    if (!state.worldId) {
      showModal(worldPanel);
      return;
    }
    try {
      const data = await api(`/api/worlds/${encodeURIComponent(state.worldId)}/chats`, {
        method: "POST",
        body: JSON.stringify({ nome: "Nova conversa" })
      });
      state.chatId = normalizeId(data.id);
      saveSelection();
      await loadWorlds();
      await loadChat(state.worldId, state.chatId);
      input.focus();
    } catch (error) {
      toast(`Não foi possível criar o chat: ${error.message}`, "error");
    }
  }

  async function createWorld() {
    try {
      setLoading(true);
      const data = await api("/api/worlds", { method: "POST", body: JSON.stringify({}) });
      if (!data.id) throw new Error("O servidor não retornou o ID do mundo.");
      state.worldId = normalizeId(data.id);
      state.chatId = "001";
      saveSelection();
      await loadWorlds();
      await selectWorld(state.worldId);
      toast(`Mundo ${state.worldId} criado.`, "success");
    } catch (error) {
      toast(`Não foi possível criar o mundo: ${error.message}`, "error");
    } finally {
      setLoading(false);
    }
  }

  function updateSendButton() {
    sendButton.disabled = state.generating || !input.value.trim() || !state.worldId;
  }

  function resizeInput() {
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 190)}px`;
  }

  async function sendMessage() {
    const text = input.value.trim();
    if (!text || state.generating) return;
    if (!state.worldId) {
      showModal(worldPanel);
      toast("Selecione um mundo primeiro.", "error");
      return;
    }
    if (!state.chatId) {
      await createChat();
      if (!state.chatId) return;
    }

    state.generating = true;
    state.controller = new AbortController();
    updateSendButton();
    input.value = "";
    resizeInput();
    addMessage("user", text);
    const assistantContent = addMessage("assistant", "");
    assistantContent.dataset.streaming = "true";

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ world_id: state.worldId, chat_id: state.chatId, message: text }),
        signal: state.controller.signal
      });
      if (!response.ok) {
        const body = await response.text();
        let errorText = body;
        try { errorText = JSON.parse(body).error || body; } catch (_) {}
        throw new Error(errorText || `Erro HTTP ${response.status}`);
      }
      if (!response.body) throw new Error("O servidor não forneceu um stream.");
      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let answer = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        answer += decoder.decode(value, { stream: true });
        if (answer.includes("[[STREAM_ERROR]]")) {
          const index = answer.indexOf("[[STREAM_ERROR]]");
          throw new Error(answer.slice(index + "[[STREAM_ERROR]]".length).trim() || "Erro no stream.");
        }
        assistantContent.innerHTML = markdown(answer);
        scrollToBottom();
      }
      answer += decoder.decode();
      if (answer.includes("[[STREAM_ERROR]]")) {
        const index = answer.indexOf("[[STREAM_ERROR]]");
        throw new Error(answer.slice(index + "[[STREAM_ERROR]]".length).trim() || "Erro no stream.");
      }
      if (!answer.trim()) assistantContent.textContent = "(A IA não retornou conteúdo.)";
      await loadWorldsSilently();
    } catch (error) {
      if (error.name === "AbortError") {
        assistantContent.textContent = "Geração interrompida.";
      } else {
        assistantContent.innerHTML = `<span class="message-error">Erro: ${escapeHtml(error.message)}</span>`;
        toast(`Falha ao gerar resposta: ${error.message}`, "error");
      }
    } finally {
      state.generating = false;
      state.controller = null;
      updateSendButton();
      input.focus();
    }
  }

  async function loadWorldsSilently() {
    try {
      const selectedWorld = state.worldId;
      const selectedChat = state.chatId;
      const data = await api("/api/worlds");
      state.worlds = Array.isArray(data.mundos) ? data.mundos : [];
      state.worlds.forEach(world => {
        world.id = normalizeId(world.id);
        world.chats = Array.isArray(world.chats) ? world.chats : [];
        world.chats.forEach(item => item.id = normalizeId(item.id));
      });
      state.worldId = selectedWorld;
      state.chatId = selectedChat;
      updateHeader();
    } catch (_) {}
  }

  function showCurrentWorld() {
    const world = worldById(state.worldId);
    if (!world) return toast("Nenhum mundo selecionado.", "error");
    const category = worldCategory(world) === "fantasia" ? "Mundo Fantasia" : "Mundo Real";
    currentWorldPanelTitle.textContent = world.nome || `Mundo ${world.id}`;
    currentWorldPanelType.textContent = `${category} · ID ${world.id}`;
    const chats = Array.isArray(world.chats) ? world.chats.length : 0;
    currentWorldInfo.innerHTML = `<div class="world-info-grid"><div class="info-card"><div class="info-label">ID</div><div class="info-value">${escapeHtml(world.id)}</div></div><div class="info-card"><div class="info-label">Categoria</div><div class="info-value">${escapeHtml(category)}</div></div><div class="info-card"><div class="info-label">Chats</div><div class="info-value">${chats}</div></div><div class="info-card"><div class="info-label">Chat atual</div><div class="info-value">${escapeHtml(state.chatId || "Nenhum")}</div></div></div>`;
    showModal(currentWorldPanel);
  }

  function toggleCategoryHeaders() {
    document.querySelectorAll(".world-category-header").forEach(header => {
      header.addEventListener("click", () => {
        const category = header.closest(".world-category");
        category.classList.toggle("collapsed");
      });
    });
  }

  function handleKeydown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  function bindEvents() {
    form.addEventListener("submit", event => { event.preventDefault(); sendMessage(); });
    input.addEventListener("input", () => { resizeInput(); updateSendButton(); });
    input.addEventListener("keydown", handleKeydown);
    sidebarToggle?.addEventListener("click", openSidebar);
    sidebarOverlay?.addEventListener("click", closeSidebar);
    newChatButton.addEventListener("click", createChat);
    worldsButton.addEventListener("click", () => { renderWorldCards(); showModal(worldPanel); });
    currentWorldButton.addEventListener("click", showCurrentWorld);
    closeWorldPanel.addEventListener("click", () => hideModal(worldPanel));
    closeCurrentWorldPanel.addEventListener("click", () => hideModal(currentWorldPanel));
    memoryButton.addEventListener("click", () => showModal(memoryPanel));
    closeMemoryPanel.addEventListener("click", () => hideModal(memoryPanel));
    createWorldButton.addEventListener("click", createWorld);
    treeRefresh.addEventListener("click", async () => {
      try { await loadWorlds(); toast("Mundos atualizados.", "success"); } catch (error) { toast(error.message, "error"); }
    });
    document.querySelectorAll(".modal-backdrop").forEach(backdrop => {
      backdrop.addEventListener("click", () => hideModal($(backdrop.dataset.close)));
    });
    document.querySelectorAll(".world-category-header").forEach(header => {
      header.addEventListener("click", () => header.closest(".world-category").classList.toggle("collapsed"));
    });
    modelSelector.addEventListener("click", () => {
      if (state.worldId) showCurrentWorld();
      else showModal(worldPanel);
    });
    $("share-button")?.addEventListener("click", async () => {
      const url = location.href;
      try { await navigator.clipboard.writeText(url); toast("Link copiado.", "success"); }
      catch (_) { toast("Não foi possível copiar o link.", "error"); }
    });
    $("attach-button")?.addEventListener("click", () => toast("Anexos ainda não estão habilitados.", ""));
    $("tools-button")?.addEventListener("click", () => toast("Ferramentas do simulador são executadas pelo backend/Guardian.", ""));
    document.addEventListener("keydown", event => {
      if (event.key === "Escape") {
        hideModal(worldPanel); hideModal(currentWorldPanel); hideModal(memoryPanel); closeSidebar();
        if (state.generating) state.controller?.abort();
      }
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault(); worldsButton.click();
      }
    });
  }

  async function init() {
    bindEvents();
    resizeInput();
    updateSendButton();
    setLoading(true);
    try {
      await loadWorlds();
      let world = worldById(state.worldId);
      if (!world) world = state.worlds[0] || null;
      if (world) {
        state.worldId = normalizeId(world.id);
        const chatData = chatById(world, state.chatId) || world.chats[0];
        state.chatId = chatData ? normalizeId(chatData.id) : null;
        saveSelection();
        updateHeader();
        if (state.chatId) await loadChat(state.worldId, state.chatId);
        else showEmptyChat();
      } else {
        showModal(worldPanel);
        showEmptyChat();
      }
    } catch (error) {
      console.error(error);
      toast(`Não foi possível conectar ao backend: ${error.message}`, "error");
      showEmptyChat();
    } finally {
      setLoading(false);
      input.focus();
    }
  }

  window.RPGSimulator = {
    reloadWorlds: loadWorlds,
    selectWorld,
    selectChat,
    createChat,
    createWorld,
    state
  };

  init();
})();
