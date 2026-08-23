import os
import sys
import json
import re
from datetime import datetime, timezone

from flask import (
    Flask,
    request,
    jsonify,
    send_from_directory,
    Response,
    stream_with_context
)

import requests


# ============================================================
# CAMINHOS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


FRONTEND_DIR = os.path.join(
    BASE_DIR,
    "frontend"
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

WORLDS_DIR = os.path.join(
    DATA_DIR,
    "mundos"
)


# ============================================================
# CARMILLA
# ============================================================

from guardian import Carmilla


carmilla = Carmilla(
    worlds_dir=WORLDS_DIR
)


# ============================================================
# FLASK
# ============================================================

app = Flask(
    __name__,
    static_folder=FRONTEND_DIR
)


# ============================================================
# OLLAMA
# ============================================================

OLLAMA_URL = os.environ.get(
    "OLLAMA_URL",
    "http://127.0.0.1:11434"
)

OLLAMA_MODEL = os.environ.get(
    "OLLAMA_MODEL",
    "llama3.1"
)


DEFAULT_WORLD_ID = "001"


# ============================================================
# UTILIDADES
# ============================================================

def agora():

    return datetime.now(
        timezone.utc
    ).isoformat()


def normalizar_world_id(
    world_id
):

    world_id = str(
        world_id
    )

    if world_id.isdigit():

        world_id = world_id.zfill(3)

    if not re.fullmatch(
        r"\d{3}",
        world_id
    ):

        raise ValueError(
            "ID de mundo inválido."
        )

    return world_id


def normalizar_chat_id(
    chat_id
):

    chat_id = str(
        chat_id
    )

    if chat_id.isdigit():

        chat_id = chat_id.zfill(3)

    if not re.fullmatch(
        r"\d{3}",
        chat_id
    ):

        raise ValueError(
            "ID de chat inválido."
        )

    return chat_id


def world_path(
    world_id
):

    return os.path.join(
        WORLDS_DIR,
        normalizar_world_id(
            world_id
        )
    )


def chat_dir(
    world_id
):

    return os.path.join(
        world_path(world_id),
        "chat"
    )


def chat_path(
    world_id,
    chat_id
):

    return os.path.join(
        chat_dir(world_id),
        f"{normalizar_chat_id(chat_id)}.json"
    )


# ============================================================
# JSON
# ============================================================

def ler_json(
    path,
    default=None
):

    if not os.path.exists(path):

        return default

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as arquivo:

            return json.load(
                arquivo
            )

    except (
        json.JSONDecodeError,
        OSError
    ):

        return default


def salvar_json(
    path,
    data
):

    os.makedirs(
        os.path.dirname(path),
        exist_ok=True
    )

    temp_path = (
        path +
        ".tmp"
    )

    with open(
        temp_path,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            data,
            arquivo,
            ensure_ascii=False,
            indent=2
        )

    os.replace(
        temp_path,
        path
    )


# ============================================================
# MUNDO
# ============================================================

def garantir_mundo(
    world_id
):

    world_id = normalizar_world_id(
        world_id
    )

    os.makedirs(
        world_path(world_id),
        exist_ok=True
    )

    os.makedirs(
        chat_dir(world_id),
        exist_ok=True
    )

    try:

        carmilla.ensure_world(
            world_id
        )

    except Exception as error:

        print(
            "Aviso ao garantir mundo:",
            repr(error)
        )

    return world_id


# ============================================================
# CHATS
# ============================================================

def listar_chats(
    world_id
):

    world_id = garantir_mundo(
        world_id
    )

    pasta = chat_dir(
        world_id
    )

    resultado = []

    for filename in sorted(
        os.listdir(pasta)
    ):

        if not filename.endswith(
            ".json"
        ):

            continue

        match = re.fullmatch(
            r"(\d{3})\.json",
            filename
        )

        if not match:

            continue

        chat_id = match.group(1)

        data = ler_json(
            os.path.join(
                pasta,
                filename
            ),
            {}
        )

        resultado.append({

            "id":
                chat_id,

            "nome":
                data.get(
                    "nome",
                    f"Chat {chat_id}"
                ),

            "criado_em":
                data.get(
                    "criado_em"
                ),

            "atualizado_em":
                data.get(
                    "atualizado_em"
                ),

            "mensagens":
                len(
                    data.get(
                        "mensagens",
                        []
                    )
                )

        })

    return resultado


def proximo_chat_id(
    world_id
):

    chats = listar_chats(
        world_id
    )

    ids = []

    for chat in chats:

        try:

            ids.append(
                int(chat["id"])
            )

        except Exception:
            pass

    if not ids:

        return "001"

    return str(
        max(ids) + 1
    ).zfill(3)


def criar_chat(
    world_id,
    nome=None
):

    world_id = garantir_mundo(
        world_id
    )

    chat_id = proximo_chat_id(
        world_id
    )

    if not nome:

        nome = "Nova conversa"

    data = {

        "id":
            chat_id,

        "world_id":
            world_id,

        "nome":
            nome,

        "criado_em":
            agora(),

        "atualizado_em":
            agora(),

        "mensagens":
            []

    }

    salvar_json(
        chat_path(
            world_id,
            chat_id
        ),
        data
    )

    return data


def carregar_chat(
    world_id,
    chat_id
):

    world_id = garantir_mundo(
        world_id
    )

    chat_id = normalizar_chat_id(
        chat_id
    )

    path = chat_path(
        world_id,
        chat_id
    )

    data = ler_json(
        path,
        None
    )

    if data is None:

        raise FileNotFoundError(
            "Chat não encontrado."
        )

    return data


def salvar_chat(
    world_id,
    chat_id,
    data
):

    data["atualizado_em"] = agora()

    salvar_json(
        chat_path(
            world_id,
            chat_id
        ),
        data
    )


def adicionar_mensagem(
    world_id,
    chat_id,
    role,
    content
):

    chat = carregar_chat(
        world_id,
        chat_id
    )

    chat.setdefault(
        "mensagens",
        []
    )

    chat["mensagens"].append({

        "role":
            role,

        "content":
            content,

        "timestamp":
            agora()

    })

    salvar_chat(
        world_id,
        chat_id,
        chat
    )

    return chat


# ============================================================
# OLLAMA
# ============================================================

def verificar_ollama():

    try:

        response = requests.get(
            f"{OLLAMA_URL}/api/tags",
            timeout=5
        )

        return response.ok

    except Exception:

        return False


def ollama(
    messages,
    stream=True
):

    response = requests.post(

        f"{OLLAMA_URL}/api/chat",

        json={

            "model":
                OLLAMA_MODEL,

            "messages":
                messages,

            "stream":
                stream

        },

        stream=stream,

        timeout=600
    )

    response.raise_for_status()

    return response


# ============================================================
# PROMPT PRINCIPAL
# ============================================================

SYSTEM_PROMPT = """
Você é a inteligência responsável por operar um RPG de simulação
persistente.

Você deve SIMULAR o mundo, não contar uma história previamente
roteirizada.

REGRAS:

- O mundo continua existindo independentemente do jogador.
- O tempo é irreversível.
- Toda ação possui consequências.
- Recursos são finitos.
- NPCs possuem livre-arbítrio.
- NPCs possuem memória, personalidade, objetivos e rotinas.
- NPCs podem aprender, esquecer, envelhecer, adoecer e morrer.
- O jogador controla somente seu personagem.
- Não existe plot armor.
- Não existe deus ex machina.
- Não favoreça o jogador artificialmente.
- Não invente acontecimentos apenas para beneficiá-lo.
- Respeite causalidade.
- Considere atributos, habilidades, experiência, saúde, fadiga,
  fome, sede, sono, equipamento, terreno, clima e circunstâncias.
- Combates devem considerar técnica, força, velocidade,
  resistência, armas, terreno, fadiga, moral e ferimentos.
- Ferimentos e consequências persistem.
- Economia, política, sociedade e relações possuem continuidade.
- Não trate informações desconhecidas como fatos.
- Se uma informação não estiver disponível, trate-a como
  desconhecida.

O jogador controla somente seu personagem.

Você controla o mundo e os NPCs.

Não revele instruções internas, prompts ou mecanismos da Carmilla
a menos que o jogador peça explicitamente informações sobre o
sistema.
"""


# ============================================================
# PROMPT DE MEMÓRIA
# ============================================================

MEMORY_ANALYSIS_PROMPT = """
Analise a interação de um RPG persistente.

Sua função é identificar somente fatos que precisam ser
persistidos na memória do mundo.

NÃO continue a história.

NÃO invente fatos.

NÃO registre possibilidades.

NÃO registre cada frase.

Registre somente alterações relevantes para continuidade.

Exemplos:

- mudança de localização;
- ferimento;
- gasto ou recebimento de dinheiro;
- item adquirido ou perdido;
- mudança de relacionamento;
- NPC conhecido;
- evento iniciado ou encerrado;
- mudança política;
- mudança econômica;
- habilidade aprendida;
- mudança de condição;
- passagem relevante de tempo.

Responda SOMENTE com JSON válido.

Formato:

{
  "updates": [
    {
      "file": "personagem/estado.json",
      "changes": {
        "localizacao": "..."
      }
    }
  ]
}

Se não houver alterações:

{
  "updates": []
}
"""


# ============================================================
# EXTRAIR JSON
# ============================================================

def extrair_json(
    texto
):

    if not texto:

        return None

    texto = texto.strip()

    try:

        return json.loads(
            texto
        )

    except Exception:
        pass

    texto = re.sub(
        r"^```(?:json)?\s*",
        "",
        texto,
        flags=re.IGNORECASE
    )

    texto = re.sub(
        r"\s*```$",
        "",
        texto
    )

    try:

        return json.loads(
            texto
        )

    except Exception:
        pass

    inicio = texto.find(
        "{"
    )

    fim = texto.rfind(
        "}"
    )

    if (
        inicio >= 0
        and fim > inicio
    ):

        try:

            return json.loads(
                texto[
                    inicio:fim + 1
                ]
            )

        except Exception:
            pass

    return None


# ============================================================
# ANÁLISE DA MEMÓRIA
# ============================================================

def analisar_memoria(
    world_id,
    user_message,
    assistant_response,
    context
):

    prompt = f"""
{MEMORY_ANALYSIS_PROMPT}

MUNDO:

{world_id}


MENSAGEM DO JOGADOR:

{user_message}


RESPOSTA DO RPG:

{assistant_response}


MEMÓRIA DISPONÍVEL:

{context}
"""

    messages = [

        {
            "role":
                "system",

            "content":
                "Você é o analisador de memória. "
                "Retorne exclusivamente JSON válido."
        },

        {
            "role":
                "user",

            "content":
                prompt
        }

    ]

    try:

        response = ollama(
            messages,
            stream=False
        )

        data = response.json()

        content = (
            data
            .get(
                "message",
                {}
            )
            .get(
                "content",
                ""
            )
        )

        resultado = extrair_json(
            content
        )

        if not isinstance(
            resultado,
            dict
        ):

            return {
                "updates_applied": [],
                "error":
                    "JSON inválido."
            }

        updates = resultado.get(
            "updates",
            []
        )

        if not isinstance(
            updates,
            list
        ):

            updates = []

        valid, rejected = (
            carmilla.validator
            .validate_updates(
                updates
            )
        )

        applied = (
            carmilla.memory
            .apply_updates(
                world_id,
                valid
            )
        )

        return {

            "detected":
                updates,

            "applied":
                applied,

            "rejected":
                rejected

        }

    except Exception as error:

        print(
            "ERRO NA MEMÓRIA:",
            repr(error)
        )

        return {

            "applied": [],

            "error":
                str(error)

        }


# ============================================================
# FRONTEND
# ============================================================

@app.route("/")
def index():

    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )


@app.route("/<path:path>")
def frontend_files(path):

    return send_from_directory(
        FRONTEND_DIR,
        path
    )


# ============================================================
# API — MUNDOS
# ============================================================

@app.get("/api/worlds")
def api_worlds():

    os.makedirs(
        WORLDS_DIR,
        exist_ok=True
    )

    mundos = []

    for folder in sorted(
        os.listdir(WORLDS_DIR)
    ):

        path = os.path.join(
            WORLDS_DIR,
            folder
        )

        if not os.path.isdir(path):
            continue

        if not re.fullmatch(
            r"\d{3}",
            folder
        ):
            continue

        nome = f"Mundo {folder}"

        mundo_file = os.path.join(
            path,
            "mundo.json"
        )

        if os.path.exists(
            mundo_file
        ):

            mundo = ler_json(
                mundo_file,
                {}
            )

            nome = mundo.get(
                "nome",
                nome
            )

        mundos.append({

            "id":
                folder,

            "nome":
                nome,

            "chats":
                listar_chats(
                    folder
                )

        })

    return jsonify({

        "mundos":
            mundos

    })


# ============================================================
# CRIAR MUNDO
# ============================================================

@app.post("/api/worlds")
def api_create_world():

    try:

        os.makedirs(
            WORLDS_DIR,
            exist_ok=True
        )

        ids = []

        for folder in os.listdir(
            WORLDS_DIR
        ):

            if re.fullmatch(
                r"\d{3}",
                folder
            ):

                ids.append(
                    int(folder)
                )

        if ids:

            number = max(ids) + 1

        else:

            number = 1

        world_id = str(
            number
        ).zfill(3)

        carmilla.initialize_world(
            world_id
        )

        # Primeiro chat do mundo

        criar_chat(
            world_id
        )

        return jsonify({

            "success":
                True,

            "id":
                world_id,

            "nome":
                f"Mundo {world_id}"

        })

    except Exception as error:

        print(
            "ERRO CRIANDO MUNDO:",
            repr(error)
        )

        return jsonify({

            "success":
                False,

            "error":
                str(error)

        }), 500


# ============================================================
# API — CHATS
# ============================================================

@app.get(
    "/api/worlds/<world_id>/chats"
)
def api_chats(world_id):

    try:

        world_id = garantir_mundo(
            world_id
        )

        return jsonify({

            "world_id":
                world_id,

            "chats":
                listar_chats(
                    world_id
                )

        })

    except Exception as error:

        return jsonify({

            "error":
                str(error)

        }), 400


# ============================================================
# CRIAR CHAT
# ============================================================

@app.post(
    "/api/worlds/<world_id>/chats"
)
def api_create_chat(
    world_id
):

    try:

        data = (
            request.get_json(
                silent=True
            )
            or {}
        )

        nome = data.get(
            "nome",
            "Nova conversa"
        )

        chat = criar_chat(
            world_id,
            nome
        )

        return jsonify(
            chat
        )

    except Exception as error:

        return jsonify({

            "error":
                str(error)

        }), 400


# ============================================================
# OBTER CHAT
# ============================================================

@app.get(
    "/api/worlds/<world_id>/chats/<chat_id>"
)
def api_get_chat(
    world_id,
    chat_id
):

    try:

        chat = carregar_chat(
            world_id,
            chat_id
        )

        return jsonify(
            chat
        )

    except Exception as error:

        return jsonify({

            "error":
                str(error)

        }), 404


# ============================================================
# RENOMEAR CHAT
# ============================================================

@app.patch(
    "/api/worlds/<world_id>/chats/<chat_id>"
)
def api_rename_chat(
    world_id,
    chat_id
):

    try:

        data = (
            request.get_json(
                silent=True
            )
            or {}
        )

        nome = data.get(
            "nome"
        )

        if not nome:

            return jsonify({

                "error":
                    "Nome não informado."

            }), 400

        chat = carregar_chat(
            world_id,
            chat_id
        )

        chat["nome"] = nome

        salvar_chat(
            world_id,
            chat_id,
            chat
        )

        return jsonify(
            chat
        )

    except Exception as error:

        return jsonify({

            "error":
                str(error)

        }), 404


# ============================================================
# DELETAR CHAT
# ============================================================

@app.delete(
    "/api/worlds/<world_id>/chats/<chat_id>"
)
def api_delete_chat(
    world_id,
    chat_id
):

    try:

        path = chat_path(
            world_id,
            chat_id
        )

        if not os.path.exists(
            path
        ):

            return jsonify({

                "error":
                    "Chat não encontrado."

            }), 404

        os.remove(
            path
        )

        return jsonify({

            "success":
                True

        })

    except Exception as error:

        return jsonify({

            "error":
                str(error)

        }), 500


# ============================================================
# CHAT PRINCIPAL
# ============================================================

@app.post("/api/chat")
def api_chat():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    message = data.get(
        "message",
        ""
    ).strip()

    if not message:

        return jsonify({

            "error":
                "Mensagem vazia."

        }), 400


    world_id = normalizar_world_id(
        data.get(
            "world_id",
            DEFAULT_WORLD_ID
        )
    )


    chat_id = data.get(
        "chat_id"
    )


    # --------------------------------------------------------
    # Se não existe chat, cria
    # --------------------------------------------------------

    if not chat_id:

        chat = criar_chat(
            world_id
        )

        chat_id = chat["id"]

    else:

        chat_id = normalizar_chat_id(
            chat_id
        )

        # Garante que existe

        try:

            carregar_chat(
                world_id,
                chat_id
            )

        except FileNotFoundError:

            criar_chat(
                world_id,
                f"Chat {chat_id}"
            )


    garantir_mundo(
        world_id
    )


    # ========================================================
    # HISTÓRICO
    # ========================================================

    chat_data = carregar_chat(
        world_id,
        chat_id
    )

    historico = chat_data.get(
        "mensagens",
        []
    )


    # ========================================================
    # MEMÓRIA
    # ========================================================

    try:

        contexto = (
            carmilla.build_context(
                world_id,
                message
            )
        )

    except Exception as error:

        return jsonify({

            "error":
                f"Erro da Carmilla: {error}"

        }), 500


    # ========================================================
    # MENSAGEM DO USUÁRIO
    # ========================================================

    adicionar_mensagem(
        world_id,
        chat_id,
        "user",
        message
    )


    # ========================================================
    # HISTÓRICO PARA O MODELO
    # ========================================================

    mensagens_modelo = [

        {
            "role":
                "system",

            "content":
                SYSTEM_PROMPT
        }

    ]


    # Mantém o histórico completo do chat

    for item in historico:

        role = item.get(
            "role"
        )

        content = item.get(
            "content",
            ""
        )

        if role in (
            "user",
            "assistant"
        ):

            mensagens_modelo.append({

                "role":
                    role,

                "content":
                    content

            })


    # Adiciona a mensagem atual

    mensagens_modelo.append({

        "role":
            "user",

        "content":
            f"""
MEMÓRIA PERSISTENTE RELEVANTE:

{contexto}


AÇÃO ATUAL DO JOGADOR:

{message}


Simule o resultado dessa ação.
"""

    })


    # ========================================================
    # STREAM
    # ========================================================

    @stream_with_context
    def generate():

        resposta = ""


        try:

            print()
            print(
                "======================================"
            )

            print(
                "MUNDO:",
                world_id
            )

            print(
                "CHAT:",
                chat_id
            )

            print(
                "======================================"
            )


            response = ollama(
                mensagens_modelo,
                stream=True
            )


            for line in response.iter_lines():

                if not line:

                    continue

                try:

                    data = json.loads(
                        line.decode(
                            "utf-8"
                        )
                    )

                except Exception:

                    continue


                if data.get(
                    "done",
                    False
                ):

                    break


                texto = (
                    data
                    .get(
                        "message",
                        {}
                    )
                    .get(
                        "content",
                        ""
                    )
                )


                if not texto:

                    continue


                resposta += texto

                yield texto


            # =================================================
            # SALVAR RESPOSTA NO CHAT
            # =================================================

            adicionar_mensagem(
                world_id,
                chat_id,
                "assistant",
                resposta
            )


            # =================================================
            # MEMÓRIA — CARMILLA
            # =================================================

            print(
                "Analisando alterações..."
            )


            resultado_memoria = (
                analisar_memoria(

                    world_id,

                    message,

                    resposta,

                    contexto

                )
            )


            print(
                json.dumps(
                    resultado_memoria,
                    ensure_ascii=False,
                    indent=2
                )
            )


            print(
                "Chat salvo:",
                chat_id
            )


        except requests.exceptions.ConnectionError:

            yield (
                "\n\n"
                "[[STREAM_ERROR]]"
                "Não foi possível conectar ao Ollama."
            )


        except requests.exceptions.Timeout:

            yield (
                "\n\n"
                "[[STREAM_ERROR]]"
                "O Ollama demorou demais para responder."
            )


        except Exception as error:

            print(
                "ERRO:",
                repr(error)
            )

            yield (
                "\n\n"
                "[[STREAM_ERROR]]"
                + str(error)
            )


    return Response(

        generate(),

        mimetype="text/plain",

        headers={

            "Cache-Control":
                "no-cache",

            "X-Accel-Buffering":
                "no",

            "Connection":
                "keep-alive"

        }

    )


# ============================================================
# HISTÓRICO — COMPATIBILIDADE
# ============================================================

@app.get("/api/history")
def api_history():

    world_id = request.args.get(
        "world_id",
        DEFAULT_WORLD_ID
    )

    chat_id = request.args.get(
        "chat_id"
    )

    if not chat_id:

        return jsonify({

            "history":
                []

        })

    try:

        chat = carregar_chat(
            world_id,
            chat_id
        )

        return jsonify({

            "history":
                chat.get(
                    "mensagens",
                    []
                )

        })

    except Exception:

        return jsonify({

            "history":
                []

        })


# ============================================================
# CARMILLA
# ============================================================

@app.get("/api/carmilla")
def api_carmilla():

    return jsonify(
        carmilla.info()
    )


@app.get("/api/carmilla/status")
def api_carmilla_status():

    return jsonify(
        carmilla.status()
    )


# ============================================================
# OLLAMA
# ============================================================

@app.get("/api/ollama")
def api_ollama():

    return jsonify({

        "online":
            verificar_ollama(),

        "url":
            OLLAMA_URL,

        "model":
            OLLAMA_MODEL

    })


# ============================================================
# MEMÓRIA / FILE TREE
# ============================================================

@app.get(
    "/api/worlds/<world_id>/files"
)
def api_files(world_id):

    try:

        world_id = garantir_mundo(
            world_id
        )

        return jsonify({

            "world_id":
                world_id,

            "tree":
                carmilla.file_tree(
                    world_id
                )

        })

    except Exception as error:

        return jsonify({

            "error":
                str(error)

        }), 500


# ============================================================
# CONTEXTO
# ============================================================

@app.post(
    "/api/worlds/<world_id>/context"
)
def api_context(world_id):

    try:

        data = (
            request.get_json(
                silent=True
            )
            or {}
        )

        message = data.get(
            "message",
            ""
        )

        world_id = garantir_mundo(
            world_id
        )

        arquivos = (
            carmilla.selected_files(
                world_id,
                message
            )
        )

        contexto = (
            carmilla.build_context(
                world_id,
                message
            )
        )

        return jsonify({

            "world_id":
                world_id,

            "selected_files":
                arquivos,

            "context":
                contexto

        })

    except Exception as error:

        return jsonify({

            "error":
                str(error)

        }), 500


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    os.makedirs(
        DATA_DIR,
        exist_ok=True
    )

    os.makedirs(
        WORLDS_DIR,
        exist_ok=True
    )


    print()
    print(
        "======================================"
    )

    print(
        "       RPG SIMULATOR"
    )

    print(
        "======================================"
    )

    print(
        "Carmilla:",
        carmilla.VERSION
    )

    print(
        "Ollama:",
        OLLAMA_URL
    )

    print(
        "Modelo:",
        OLLAMA_MODEL
    )

    print(
        "Mundos:",
        WORLDS_DIR
    )

    print(
        "======================================"
    )


    if verificar_ollama():

        print(
            "Ollama: ONLINE"
        )

    else:

        print(
            "Ollama: OFFLINE"
        )


    print()


    app.run(

        host="0.0.0.0",

        port=8000,

        debug=True,

        threaded=True

    )