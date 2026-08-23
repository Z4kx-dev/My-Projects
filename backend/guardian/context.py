import json


class ContextManager:

    FILE_GROUPS = {

        "always": [
            "mundo.json",
            "personagem/estado.json",
            "personagem/atributos.json",
            "personagem/habilidades.json",
            "personagem/inventario.json",
            "personagem/relacionamentos.json"
        ],

        "npc": [
            "npcs/registro.json",
            "npcs/relacionamentos.json"
        ],

        "politica": [
            "politica/governos.json",
            "politica/relacoes.json"
        ],

        "economia": [
            "economia/dinheiro.json",
            "economia/precos.json",
            "economia/mercado.json"
        ],

        "eventos": [
            "eventos/ativos.json"
        ],

        "diario": [
            "diario/diario.json"
        ]
    }


    KEYWORDS = {

        "npc": [
            "npc",
            "pessoa",
            "homem",
            "mulher",
            "dono",
            "dona",
            "rei",
            "rainha",
            "prefeito",
            "soldado",
            "guarda",
            "mercador",
            "comerciante",
            "conversar",
            "falar",
            "conhecer"
        ],

        "politica": [
            "governo",
            "rei",
            "rainha",
            "política",
            "politica",
            "cidade",
            "reino",
            "império",
            "imperio",
            "guerra",
            "aliança",
            "alianca",
            "tratado",
            "exército",
            "exercito"
        ],

        "economia": [
            "dinheiro",
            "preço",
            "preco",
            "comprar",
            "vender",
            "ouro",
            "prata",
            "moeda",
            "mercado",
            "salário",
            "salario",
            "comércio",
            "comercio"
        ],

        "eventos": [
            "evento",
            "aconteceu",
            "acontecendo",
            "batalha",
            "ataque",
            "incêndio",
            "incendio",
            "desastre"
        ],

        "diario": [
            "diário",
            "diario",
            "lembrar",
            "lembro",
            "ontem",
            "antes"
        ]
    }


    def __init__(
        self,
        memory
    ):

        self.memory = memory


    def _load(
        self,
        world_id,
        file
    ):

        return self.memory.read(
            world_id,
            file
        )


    def select_files(
        self,
        message
    ):

        text = (
            message
            .lower()
            .strip()
        )

        selected = []

        # Sempre necessário
        selected.extend(
            self.FILE_GROUPS["always"]
        )

        for group, keywords in self.KEYWORDS.items():

            if any(
                keyword in text
                for keyword in keywords
            ):

                selected.extend(
                    self.FILE_GROUPS[group]
                )

        # Remove duplicados
        result = []

        for file in selected:

            if file not in result:

                result.append(file)

        return result


    def build(
        self,
        world_id,
        message=""
    ):

        files = self.select_files(
            message
        )

        sections = []

        for file in files:

            data = self._load(
                world_id,
                file
            )

            sections.append(
                f"=== MEMÓRIA: {file} ==="
            )

            sections.append(
                json.dumps(
                    data,
                    ensure_ascii=False,
                    indent=2
                )
            )

        return "\n\n".join(
            sections
        )


    def describe_selection(
        self,
        world_id,
        message
    ):

        return self.select_files(
            message
        )