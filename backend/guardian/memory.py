import copy


class MemoryManager:

    def __init__(self, filesystem):
        self.filesystem = filesystem

    def read(self, world_id, file):
        return self.filesystem.read_json(
            world_id,
            file,
            default={}
        )

    def write(self, world_id, file, data):
        self.filesystem.write_json(
            world_id,
            file,
            data
        )

        return data

    def apply_update(self, world_id, update):
        """
        Aplica uma alteração controlada à memória.

        Formato esperado:

        {
            "file": "personagem/estado.json",
            "changes": {
                "localizacao": "Taverna"
            }
        }
        """

        if not isinstance(update, dict):
            raise ValueError(
                "Atualização de memória inválida."
            )

        file = update.get("file")
        changes = update.get("changes")

        if not file:
            raise ValueError(
                "Arquivo não especificado."
            )

        if not isinstance(changes, dict):
            raise ValueError(
                "changes deve ser um objeto."
            )

        current = self.read(
            world_id,
            file
        )

        if not isinstance(current, dict):
            current = {}

        updated = copy.deepcopy(current)

        self._deep_merge(
            updated,
            changes
        )

        self.write(
            world_id,
            file,
            updated
        )

        return updated

    def _deep_merge(self, target, changes):

        for key, value in changes.items():

            if (
                isinstance(value, dict)
                and isinstance(
                    target.get(key),
                    dict
                )
            ):

                self._deep_merge(
                    target[key],
                    value
                )

            else:

                target[key] = value

    def apply_updates(
        self,
        world_id,
        updates
    ):

        results = []

        if not isinstance(
            updates,
            list
        ):
            return results

        for update in updates:

            try:

                result = self.apply_update(
                    world_id,
                    update
                )

                results.append({
                    "success": True,
                    "file": update.get("file"),
                    "data": result
                })

            except Exception as error:

                results.append({
                    "success": False,
                    "file": update.get("file"),
                    "error": str(error)
                })

        return results