import os
import json


class FileSystemManager:

    def __init__(
        self,
        worlds_dir
    ):

        self.worlds_dir = os.path.abspath(
            worlds_dir
        )

        os.makedirs(
            self.worlds_dir,
            exist_ok=True
        )


    # ========================================================
    # CAMINHOS
    # ========================================================

    def world_path(
        self,
        world_id
    ):

        return os.path.join(
            self.worlds_dir,
            str(world_id).zfill(3)
        )


    def file_path(
        self,
        world_id,
        file
    ):

        return os.path.join(
            self.world_path(
                world_id
            ),
            file
        )


    # ========================================================
    # LEITURA
    # ========================================================

    def read_json(
        self,
        world_id,
        file,
        default=None
    ):

        path = self.file_path(
            world_id,
            file
        )

        if not os.path.exists(
            path
        ):

            return (
                default
                if default is not None
                else {}
            )


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

            return (
                default
                if default is not None
                else {}
            )


    # ========================================================
    # ESCRITA
    # ========================================================

    def write_json(
        self,
        world_id,
        file,
        data
    ):

        path = self.file_path(
            world_id,
            file
        )

        os.makedirs(
            os.path.dirname(path),
            exist_ok=True
        )


        temp = (
            path +
            ".tmp"
        )


        with open(
            temp,
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
            temp,
            path
        )


    # ========================================================
    # INICIALIZAÇÃO
    # ========================================================

    def initialize_world(
        self,
        world_id,
        structure
    ):

        world = self.world_path(
            world_id
        )

        os.makedirs(
            world,
            exist_ok=True
        )


        for file, data in structure.items():

            path = os.path.join(
                world,
                file
            )

            # NÃO sobrescreve memória existente.

            if os.path.exists(
                path
            ):

                continue


            os.makedirs(
                os.path.dirname(path),
                exist_ok=True
            )


            self.write_json(
                world_id,
                file,
                data
            )


    # ========================================================
    # ÁRVORE
    # ========================================================

    def tree(
        self,
        world_id
    ):

        world = self.world_path(
            world_id
        )


        if not os.path.exists(
            world
        ):

            return {}


        result = {}


        for root, dirs, files in os.walk(
            world
        ):

            relative = os.path.relpath(
                root,
                world
            )


            if relative == ".":
                relative = ""


            current = result


            if relative:

                for part in relative.split(
                    os.sep
                ):

                    current = current.setdefault(
                        part,
                        {}
                    )


            for filename in files:

                current[filename] = {
                    "type": "file"
                }


        return result