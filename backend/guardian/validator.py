import re


class Validator:

    ALLOWED_FILES = {

        "mundo.json",

        "personagem/estado.json",
        "personagem/atributos.json",
        "personagem/habilidades.json",
        "personagem/inventario.json",
        "personagem/relacionamentos.json",

        "npcs/registro.json",
        "npcs/relacionamentos.json",

        "politica/governos.json",
        "politica/relacoes.json",

        "economia/dinheiro.json",
        "economia/precos.json",
        "economia/mercado.json",

        "diario/diario.json",

        "eventos/ativos.json",
        "eventos/historico.json"
    }

    def valid_world_id(self, world_id):

        if not isinstance(
            world_id,
            str
        ):
            return False

        return bool(
            re.fullmatch(
                r"\d{3}",
                world_id
            )
        )

    def valid_memory_file(self, file):

        if not isinstance(
            file,
            str
        ):
            return False

        return file in self.ALLOWED_FILES

    def validate_update(self, update):

        if not isinstance(
            update,
            dict
        ):
            return False, "Formato inválido."

        file = update.get("file")
        changes = update.get("changes")

        if not self.valid_memory_file(
            file
        ):

            return (
                False,
                "Arquivo não permitido."
            )

        if not isinstance(
            changes,
            dict
        ):

            return (
                False,
                "changes deve ser um objeto."
            )

        return True, None

    def validate_updates(
        self,
        updates
    ):

        valid = []
        rejected = []

        if not isinstance(
            updates,
            list
        ):

            return valid, [
                {
                    "reason":
                    "updates não é uma lista."
                }
            ]

        for update in updates:

            ok, reason = self.validate_update(
                update
            )

            if ok:

                valid.append(update)

            else:

                rejected.append({
                    "update": update,
                    "reason": reason
                })

        return valid, rejected