// ==================================================
// RPG SIMULATOR — APP.JS
// ==================================================


// ==================================================
// ELEMENTOS
// ==================================================

const form =
    document.getElementById("chat-form");

const input =
    document.getElementById("message");

const chat =
    document.getElementById("chat");

const messages =
    document.getElementById("messages");

const sendButton =
    document.getElementById("send-button");

const sidebar =
    document.getElementById("sidebar");

const sidebarToggle =
    document.getElementById("sidebar-toggle");

const newChat =
    document.getElementById("new-chat");

const worldsButton =
    document.getElementById("worlds-button");

const worldPanel =
    document.getElementById("world-panel");

const closeWorldPanel =
    document.getElementById("close-world-panel");

const createWorldButton =
    document.getElementById("create-world-button");

const realWorlds =
    document.getElementById("real-worlds");

const fantasiaWorlds =
    document.getElementById("fantasia-worlds");

const currentWorldButton =
    document.getElementById("current-world-button");

const currentWorldName =
    document.getElementById("current-world-name");

const currentChatName =
    document.getElementById("current-chat-name");

const chatTree =
    document.getElementById("chat-tree");

const memoryButton =
    document.getElementById("memory-button");

const memoryPanel =
    document.getElementById("memory-panel");

const closeMemoryPanel =
    document.getElementById("close-memory-panel");

const currentWorldPanel =
    document.getElementById("current-world-panel");

const closeCurrentWorldPanel =
    document.getElementById(
        "close-current-world-panel"
    );

const currentWorldInfo =
    document.getElementById(
        "current-world-info"
    );

const currentWorldPanelTitle =
    document.getElementById(
        "current-world-panel-title"
    );

const currentWorldPanelType =
    document.getElementById(
        "current-world-panel-type"
    );


// ==================================================
// ESTADO
// ==================================================

let gerando = false;

let controller = null;

let velocidadeDigitacao = 35;


// ID do mundo atualmente selecionado.
//
// IMPORTANTE:
// nunca usamos o nome do mundo como identidade.

let mundoAtualId = null;


// ID do chat atualmente selecionado.

let chatAtualId = null;


// Cache dos mundos carregados.

let mundos = [];


// Cache dos chats do mundo atual.

let chatsAtuais = [];


// ==================================================
// UTILIDADES
// ==================================================

function esperar(ms) {

    return new Promise(resolve => {

        setTimeout(resolve, ms);

    });

}


function escapeHtml(text) {

    return String(text)

        .replace(/&/g, "&amp;")

        .replace(/</g, "&lt;")

        .replace(/>/g, "&gt;")

        .replace(/"/g, "&quot;")

        .replace(/'/g, "&#039;");

}


// ==================================================
// MARKDOWN
// ==================================================

function markdownToHtml(text) {

    let html =
        escapeHtml(text);


    // Código em bloco

    html = html.replace(
        /```([\s\S]*?)```/g,
        (_, code) => {

            return `
                <pre>
                    <code>${code.trim()}</code>
                </pre>
            `;

        }
    );


    // Código inline

    html = html.replace(
        /`([^`\n]+)`/g,
        "<code>$1</code>"
    );


    // Títulos

    html = html.replace(
        /^### (.*)$/gm,
        "<h3>$1</h3>"
    );

    html = html.replace(
        /^## (.*)$/gm,
        "<h2>$1</h2>"
    );

    html = html.replace(
        /^# (.*)$/gm,
        "<h1>$1</h1>"
    );


    // Negrito

    html = html.replace(
        /\*\*(.*?)\*\*/g,
        "<strong>$1</strong>"
    );


    // Itálico

    html = html.replace(
        /(?<!\*)\*([^*\n]+)\*(?!\*)/g,
        "<em>$1</em>"
    );


    // Citações

    html = html.replace(
        /^&gt; (.*)$/gm,
        "<blockquote>$1</blockquote>"
    );


    // Listas simples

    html = html.replace(
        /(?:^|\n)([-*]) (.+)/g,
        "\n<li>$2</li>"
    );


    html = html.replace(
        /(<li>.*?<\/li>)(?:\s*<br>)?(?=<li>)/gs,
        "$1"
    );


    // Quebras de linha

    html = html.replace(
        /\n/g,
        "<br>"
    );


    return html;

}


// ==================================================
// ADICIONAR MENSAGEM
// ==================================================

function addMessage(
    type,
    text = "",
    renderMarkdown = true
) {

    const message =
        document.createElement("div");

    message.className =
        `message ${type}`;


    const content =
        document.createElement("div");

    content.className =
        "message-content";


    if (
        type === "assistant" &&
        renderMarkdown
    ) {

        content.innerHTML =
            markdownToHtml(text);

    } else {

        content.textContent =
            text;

    }


    message.appendChild(content);

    messages.appendChild(message);


    chat.scrollTop =
        chat.scrollHeight;


    return content;

}


// ==================================================
// API JSON
// ==================================================

async function apiJson(
    url,
    options = {}
) {

    const response =
        await fetch(
            url,
            options
        );


    const contentType =
        response.headers.get(
            "content-type"
        ) || "";


    if (!response.ok) {

        const texto =
            await response.text();

        throw new Error(
            texto ||
            `Erro HTTP ${response.status}`
        );

    }


    if (
        !contentType.includes(
            "application/json"
        )
    ) {

        const texto =
            await response.text();

        throw new Error(
            "O servidor não retornou JSON. " +
            texto.substring(0, 200)
        );

    }


    return response.json();

}


// ==================================================
// CARREGAR MUNDOS
// ==================================================

async function carregarMundos() {

    try {

        const data =
            await apiJson(
                "/api/worlds"
            );


        mundos =
            Array.isArray(data.mundos)
                ? data.mundos
                : [];


        renderizarMundos();


        // Se o mundo atual não existe mais,
        // limpa a seleção.

        if (
            mundoAtualId &&
            !mundos.some(
                mundo =>
                    mundo.id === mundoAtualId
            )
        ) {

            mundoAtualId = null;

            chatAtualId = null;

        }


        // Seleciona automaticamente o primeiro mundo
        // somente se nenhum estiver selecionado.

        if (
            !mundoAtualId &&
            mundos.length > 0
        ) {

            await selecionarMundo(
                mundos[0].id
            );

        } else {

            atualizarInterfaceAtual();

        }


    } catch (error) {

        console.error(
            "Erro ao carregar mundos:",
            error
        );

    }

}


// ==================================================
// RENDERIZAR MUNDOS
// ==================================================

function renderizarMundos() {

    if (realWorlds) {

        realWorlds.innerHTML = "";

    }


    if (fantasiaWorlds) {

        fantasiaWorlds.innerHTML = "";

    }


    for (
        const mundo of mundos
    ) {

        // O ID é obrigatório.

        if (!mundo.id) {

            continue;

        }


        const tipo =
            mundo.tipo ||
            (
                mundo.id.startsWith(
                    "fantasia:"
                )
                    ? "fantasia"
                    : "real"
            );


        const button =
            document.createElement("button");

        button.type =
            "button";

        button.className =
            "world-item";


        // IDENTIDADE REAL DO ELEMENTO

        button.dataset.worldId =
            mundo.id;


        const icon =
            tipo === "fantasia"
                ? "✨"
                : "🌎";


        button.innerHTML = `
            <span class="world-item-icon">
                ${icon}
            </span>

            <span class="world-item-name">
                ${escapeHtml(
                    mundo.nome ||
                    mundo.id
                )}
            </span>
        `;


        button.addEventListener(
            "click",
            async () => {

                await selecionarMundo(
                    mundo.id
                );

                fecharPainelMundos();

            }
        );


        if (
            mundo.id ===
            mundoAtualId
        ) {

            button.classList.add(
                "active"
            );

        }


        if (
            tipo === "fantasia"
        ) {

            fantasiaWorlds?.appendChild(
                button
            );

        } else {

            realWorlds?.appendChild(
                button
            );

        }

    }

}


// ==================================================
// SELECIONAR MUNDO
// ==================================================

async function selecionarMundo(
    worldId
) {

    // ID é a única referência aceita.

    if (!worldId) {

        return;

    }


    const mundo =
        mundos.find(
            item =>
                item.id === worldId
        );


    if (!mundo) {

        console.error(
            "Mundo não encontrado pelo ID:",
            worldId
        );

        return;

    }


    mundoAtualId =
        mundo.id;


    chatAtualId =
        null;


    atualizarInterfaceAtual();


    await carregarChats(
        mundo.id
    );


    renderizarMundos();


    atualizarInterfaceAtual();

}


// ==================================================
// CARREGAR CHATS
// ==================================================

async function carregarChats(
    worldId
) {

    try {

        const data =
            await apiJson(
                `/api/worlds/${encodeURIComponent(worldId)}/chats`
            );


        chatsAtuais =
            Array.isArray(data.chats)
                ? data.chats
                : [];


        renderizarChats();


        // Se houver chat, seleciona o primeiro.

        if (
            chatsAtuais.length > 0
        ) {

            await selecionarChat(
                chatsAtuais[0].id
            );

        } else {

            limparChat();

        }


    } catch (error) {

        console.error(
            "Erro ao carregar chats:",
            error
        );

        chatsAtuais = [];

        renderizarChats();

        limparChat();

    }

}


// ==================================================
// RENDERIZAR ÁRVORE DE CHATS
// ==================================================

function renderizarChats() {

    if (!chatTree) {

        return;

    }


    chatTree.innerHTML = "";


    if (!mundoAtualId) {

        return;

    }


    const mundo =
        mundos.find(
            item =>
                item.id === mundoAtualId
        );


    if (!mundo) {

        return;

    }


    // Cabeçalho do mundo atual.

    const worldHeader =
        document.createElement("div");

    worldHeader.className =
        "chat-tree-world";


    const worldIcon =
        mundo.tipo === "fantasia"
            ? "✨"
            : "🌎";


    worldHeader.innerHTML = `
        <span>${worldIcon}</span>
        <span>
            ${escapeHtml(
                mundo.nome ||
                mundo.id
            )}
        </span>
    `;


    chatTree.appendChild(
        worldHeader
    );


    // Lista de chats.

    for (
        const item of chatsAtuais
    ) {

        if (!item.id) {

            continue;

        }


        const button =
            document.createElement("button");

        button.type =
            "button";

        button.className =
            "chat-tree-item";


        // ID do chat.

        button.dataset.chatId =
            item.id;


        button.innerHTML = `
            <span class="chat-tree-icon">
                ◇
            </span>

            <span>
                ${escapeHtml(
                    item.nome ||
                    item.id
                )}
            </span>
        `;


        if (
            item.id ===
            chatAtualId
        ) {

            button.classList.add(
                "active"
            );

        }


        button.addEventListener(
            "click",
            async () => {

                await selecionarChat(
                    item.id
                );

            }
        );


        chatTree.appendChild(
            button
        );

    }

}


// ==================================================
// SELECIONAR CHAT
// ==================================================

async function selecionarChat(
    chatId
) {

    if (!chatId) {

        return;

    }


    const chatEncontrado =
        chatsAtuais.find(
            item =>
                item.id === chatId
        );


    if (!chatEncontrado) {

        console.error(
            "Chat não encontrado pelo ID:",
            chatId
        );

        return;

    }


    chatAtualId =
        chatEncontrado.id;


    atualizarInterfaceAtual();

    renderizarChats();


    await carregarHistorico(
        mundoAtualId,
        chatAtualId
    );

}


// ==================================================
// CARREGAR HISTÓRICO
// ==================================================

async function carregarHistorico(
    worldId,
    chatId
) {

    if (
        !worldId ||
        !chatId
    ) {

        limparChat();

        return;

    }


    try {

        const data =
            await apiJson(
                `/api/worlds/${encodeURIComponent(worldId)}/chats/${encodeURIComponent(chatId)}`
            );


        messages.innerHTML = "";


        const history =
            Array.isArray(
                data.mensagens
            )
                ? data.mensagens
                : (
                    Array.isArray(
                        data.history
                    )
                        ? data.history
                        : []
                );


        if (
            history.length === 0
        ) {

            mostrarWelcome();

            return;

        }


        for (
            const item of history
        ) {

            const type =
                item.role === "user"
                    ? "user"
                    : "assistant";


            addMessage(
                type,
                item.content || "",
                type === "assistant"
            );

        }


    } catch (error) {

        console.error(
            "Erro ao carregar histórico:",
            error
        );


        messages.innerHTML = "";


        addMessage(
            "assistant",
            "Não foi possível carregar este chat."
        );

    }

}


// ==================================================
// LIMPAR CHAT
// ==================================================

function limparChat() {

    messages.innerHTML = "";

    mostrarWelcome();

}


function mostrarWelcome() {

    const welcome =
        document.createElement("div");

    welcome.className =
        "welcome";


    welcome.innerHTML = `
        <div class="welcome-icon">
            ✦
        </div>

        <h1>
            Como posso ajudar?
        </h1>

        <p>
            Seu simulador de RPG está pronto.
        </p>
    `;


    messages.appendChild(
        welcome
    );

}


// ==================================================
// ATUALIZAR INTERFACE
// ==================================================

function atualizarInterfaceAtual() {

    const mundo =
        mundos.find(
            item =>
                item.id === mundoAtualId
        );


    if (mundo) {

        currentWorldName.textContent =
            mundo.nome ||
            mundo.id;

    } else {

        currentWorldName.textContent =
            "Nenhum mundo";

    }


    const chatEncontrado =
        chatsAtuais.find(
            item =>
                item.id === chatAtualId
        );


    if (chatEncontrado) {

        currentChatName.textContent =
            chatEncontrado.nome ||
            chatEncontrado.id;

    } else if (mundo) {

        currentChatName.textContent =
            mundo.nome ||
            mundo.id;

    } else {

        currentChatName.textContent =
            "RPG Simulator";

    }

}


// ==================================================
// NOVO CHAT
// ==================================================

async function criarChat() {

    if (!mundoAtualId) {

        alert(
            "Selecione um mundo primeiro."
        );

        return;

    }


    if (gerando) {

        return;

    }


    try {

        const data =
            await apiJson(
                `/api/worlds/${encodeURIComponent(mundoAtualId)}/chats`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    }
                }
            );


        if (
            data.chat &&
            data.chat.id
        ) {

            await carregarChats(
                mundoAtualId
            );


            await selecionarChat(
                data.chat.id
            );

        } else {

            await carregarChats(
                mundoAtualId
            );

        }


    } catch (error) {

        console.error(
            "Erro ao criar chat:",
            error
        );


        alert(
            "Não foi possível criar o chat."
        );

    }

}


// ==================================================
// NOVO MUNDO
// ==================================================

async function criarMundo() {

    const tipo =
        prompt(
            "Tipo do mundo:\n\n" +
            "1 = Mundo Real\n" +
            "2 = Mundo Fantasia"
        );


    if (
        tipo !== "1" &&
        tipo !== "2"
    ) {

        return;

    }


    const categoria =
        tipo === "1"
            ? "real"
            : "fantasia";


    try {

        const data =
            await apiJson(
                "/api/worlds",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        tipo: categoria
                    })
                }
            );


        await carregarMundos();


        if (data.id) {

            await selecionarMundo(
                data.id
            );

        }


    } catch (error) {

        console.error(
            "Erro ao criar mundo:",
            error
        );


        alert(
            "Não foi possível criar o mundo."
        );

    }

}


// ==================================================
// ENVIAR MENSAGEM
// ==================================================

async function enviarMensagem() {

    if (gerando) {

        return;

    }


    if (!mundoAtualId) {

        alert(
            "Selecione um mundo primeiro."
        );

        return;

    }


    if (!chatAtualId) {

        await criarChat();

        if (!chatAtualId) {

            return;

        }

    }


    const message =
        input.value.trim();


    if (!message) {

        return;

    }


    const welcome =
        document.querySelector(
            ".welcome"
        );


    if (welcome) {

        welcome.remove();

    }


    addMessage(
        "user",
        message,
        false
    );


    input.value = "";

    ajustarAltura();


    gerando = true;

    controller =
        new AbortController();


    input.focus();

    atualizarBotaoGeracao();


    const respostaElement =
        addMessage(
            "assistant",
            "",
            false
        );


    respostaElement.innerHTML =
        '<span class="typing-cursor">▍</span>';


    let respostaCompleta = "";


    try {

        const response =
            await fetch(
                "/api/chat",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        world_id:
                            mundoAtualId,

                        chat_id:
                            chatAtualId,

                        message:
                            message

                    }),

                    signal:
                        controller.signal

                }
            );


        if (!response.ok) {

            const errorText =
                await response.text();

            throw new Error(
                errorText ||
                `Erro HTTP ${response.status}`
            );

        }


        if (!response.body) {

            throw new Error(
                "O navegador não suporta streaming."
            );

        }


        const reader =
            response.body.getReader();


        const decoder =
            new TextDecoder(
                "utf-8"
            );


        while (true) {

            const {
                value,
                done
            } = await reader.read();


            if (done) {

                break;

            }


            const chunk =
                decoder.decode(
                    value,
                    {
                        stream: true
                    }
                );


            for (
                const caractere of chunk
            ) {

                respostaCompleta +=
                    caractere;


                if (
                    respostaCompleta.includes(
                        "[[STREAM_ERROR]]"
                    )
                ) {

                    const partes =
                        respostaCompleta.split(
                            "[[STREAM_ERROR]]"
                        );


                    throw new Error(
                        partes[1] ||
                        "Erro durante o streaming."
                    );

                }


                respostaElement.innerHTML =
                    markdownToHtml(
                        respostaCompleta
                    ) +
                    '<span class="typing-cursor">▍</span>';


                chat.scrollTop =
                    chat.scrollHeight;


                if (
                    velocidadeDigitacao > 0
                ) {

                    await esperar(
                        velocidadeDigitacao
                    );

                }

            }

        }


        respostaElement.innerHTML =
            markdownToHtml(
                respostaCompleta
            );


    } catch (error) {

        if (
            error.name ===
            "AbortError"
        ) {

            if (!respostaCompleta) {

                respostaElement.textContent =
                    "Geração interrompida.";

            } else {

                respostaElement.innerHTML =
                    markdownToHtml(
                        respostaCompleta
                    );

            }


        } else {

            console.error(
                "Erro:",
                error
            );


            respostaElement.textContent =
                "Erro: " +
                error.message;

        }


    } finally {

        gerando = false;

        controller = null;

        atualizarBotaoGeracao();

        input.focus();

    }

}


// ==================================================
// BOTÃO DE GERAÇÃO
// ==================================================

function atualizarBotaoGeracao() {

    if (gerando) {

        sendButton.textContent =
            "■";

        sendButton.title =
            "Parar geração";

        sendButton.disabled =
            false;

        sendButton.classList.add(
            "stop-button"
        );

    } else {

        sendButton.textContent =
            "↑";

        sendButton.title =
            "Enviar";

        sendButton.classList.remove(
            "stop-button"
        );


        sendButton.disabled =
            input.value.trim().length === 0;

    }

}


// ==================================================
// PARAR GERAÇÃO
// ==================================================

sendButton.addEventListener(
    "click",
    event => {

        if (!gerando) {

            return;

        }


        event.preventDefault();


        if (controller) {

            controller.abort();

        }

    }
);


// ==================================================
// FORMULÁRIO
// ==================================================

form.addEventListener(
    "submit",
    event => {

        event.preventDefault();


        if (gerando) {

            return;

        }


        enviarMensagem();

    }
);


// ==================================================
// ENTER
// ==================================================

input.addEventListener(
    "keydown",
    event => {

        if (
            event.key !== "Enter"
        ) {

            return;

        }


        // Ctrl + Enter = quebra de linha

        if (
            event.ctrlKey
        ) {

            event.preventDefault();


            const start =
                input.selectionStart;

            const end =
                input.selectionEnd;


            input.value =
                input.value.substring(
                    0,
                    start
                ) +
                "\n" +
                input.value.substring(
                    end
                );


            input.selectionStart =
                start + 1;

            input.selectionEnd =
                start + 1;


            ajustarAltura();

            return;

        }


        // Shift + Enter = quebra

        if (
            event.shiftKey
        ) {

            return;

        }


        // Enter = enviar

        event.preventDefault();


        if (!gerando) {

            enviarMensagem();

        }

    }
);


// ==================================================
// TEXTAREA
// ==================================================

function ajustarAltura() {

    input.style.height =
        "auto";


    input.style.height =
        Math.min(
            input.scrollHeight,
            180
        ) + "px";


    if (!gerando) {

        sendButton.disabled =
            input.value.trim().length === 0;

    }

}


input.addEventListener(
    "input",
    ajustarAltura
);


// ==================================================
// SIDEBAR
// ==================================================

if (sidebarToggle) {

    sidebarToggle.addEventListener(
        "click",
        () => {

            sidebar.classList.toggle(
                "open"
            );

        }
    );

}


// ==================================================
// PAINEL DE MUNDOS
// ==================================================

function abrirPainelMundos() {

    worldPanel?.classList.add(
        "open"
    );

}


function fecharPainelMundos() {

    worldPanel?.classList.remove(
        "open"
    );

}


worldsButton?.addEventListener(
    "click",
    abrirPainelMundos
);


closeWorldPanel?.addEventListener(
    "click",
    fecharPainelMundos
);


// ==================================================
// NOVO CHAT
// ==================================================

newChat?.addEventListener(
    "click",
    () => {

        if (gerando) {

            return;

        }


        criarChat();

    }
);


// ==================================================
// CRIAR MUNDO
// ==================================================

createWorldButton?.addEventListener(
    "click",
    criarMundo
);


// ==================================================
// MUNDO ATUAL
// ==================================================

currentWorldButton?.addEventListener(
    "click",
    () => {

        if (!mundoAtualId) {

            abrirPainelMundos();

            return;

        }


        const mundo =
            mundos.find(
                item =>
                    item.id ===
                    mundoAtualId
            );


        if (!mundo) {

            return;

        }


        currentWorldPanelTitle.textContent =
            mundo.nome ||
            mundo.id;


        currentWorldPanelType.textContent =
            mundo.tipo === "fantasia"
                ? "Mundo Fantasia"
                : "Mundo Real";


        currentWorldInfo.innerHTML = `

            <div class="world-info-row">

                <span>ID</span>

                <strong>
                    ${escapeHtml(
                        mundo.id
                    )}
                </strong>

            </div>


            <div class="world-info-row">

                <span>Nome</span>

                <strong>
                    ${escapeHtml(
                        mundo.nome ||
                        mundo.id
                    )}
                </strong>

            </div>


            <div class="world-info-row">

                <span>Tipo</span>

                <strong>
                    ${mundo.tipo === "fantasia"
                        ? "Fantasia"
                        : "Real"}
                </strong>

            </div>

        `;


        currentWorldPanel?.classList.add(
            "open"
        );

    }
);


// ==================================================
// FECHAR MUNDO ATUAL
// ==================================================

closeCurrentWorldPanel?.addEventListener(
    "click",
    () => {

        currentWorldPanel?.classList.remove(
            "open"
        );

    }
);


// ==================================================
// MEMÓRIA
// ==================================================

memoryButton?.addEventListener(
    "click",
    () => {

        if (!mundoAtualId) {

            alert(
                "Selecione um mundo primeiro."
            );

            return;

        }


        memoryPanel?.classList.add(
            "open"
        );

    }
);


closeMemoryPanel?.addEventListener(
    "click",
    () => {

        memoryPanel?.classList.remove(
            "open"
        );

    }
);


// ==================================================
// CATEGORIAS DE MUNDO
// ==================================================

document
    .querySelectorAll(
        ".world-category-header"
    )
    .forEach(button => {

        button.addEventListener(
            "click",
            () => {

                const category =
                    button.closest(
                        ".world-category"
                    );


                category?.classList.toggle(
                    "collapsed"
                );

            }
        );

    });


// ==================================================
// FECHAR PAINÉIS CLICANDO FORA
// ==================================================

worldPanel?.addEventListener(
    "click",
    event => {

        if (
            event.target ===
            worldPanel
        ) {

            fecharPainelMundos();

        }

    }
);


currentWorldPanel?.addEventListener(
    "click",
    event => {

        if (
            event.target ===
            currentWorldPanel
        ) {

            currentWorldPanel.classList.remove(
                "open"
            );

        }

    }
);


memoryPanel?.addEventListener(
    "click",
    event => {

        if (
            event.target ===
            memoryPanel
        ) {

            memoryPanel.classList.remove(
                "open"
            );

        }

    }
);


// ==================================================
// INICIALIZAÇÃO
// ==================================================

async function inicializar() {

    try {

        ajustarAltura();

        atualizarBotaoGeracao();

        await carregarMundos();

        input.focus();

    } catch (error) {

        console.error(
            "Erro na inicialização:",
            error
        );

    }

}


inicializar();