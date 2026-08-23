from .filesystem import FileSystemManager
from .memory import MemoryManager
from .validator import Validator
from .context import ContextManager


class Carmilla:

    NAME = "Carmilla"
    VERSION = "1.1.0"


    WORLD_STRUCTURE = {

        "mundo.json": {
            "versao": 1,
            "id": None,
            "nome": None,
            "data": None,
            "localizacoes": {},
            "condicoes": {}
        },

        "personagem/estado.json": {
            "versao": 1,
            "nome": None,
            "idade": None,
            "localizacao": None,
            "vida": None,
            "mana": None,
            "fadiga": 0,
            "fome": 0,
            "sede": 0,
            "sono": 0,
            "condicoes": []
        },

        "personagem/atributos.json": {
            "versao": 1,
            "fisicos": {},
            "mentais": {},
            "sociais": {},
            "conhecimento": {}
        },

        "personagem/habilidades.json": {
            "versao": 1,
            "habilidades": {}
        },

        "personagem/inventario.json": {
            "versao": 1,
            "itens": {},
            "dinheiro": {}
        },

        "personagem/relacionamentos.json": {
            "versao": 1,
            "relacoes": {}
        },

        "npcs/registro.json": {
            "versao": 1,
            "npcs": {}
        },

        "npcs/relacionamentos.json": {
            "versao": 1,
            "relacoes": {}
        },

        "politica/governos.json": {
            "versao": 1,
            "governos": {}
        },

        "politica/relacoes.json": {
            "versao": 1,
            "relacoes": {}
        },

        "economia/dinheiro.json": {
            "versao": 1,
            "moedas": {},
            "tesouros": {},
            "dividas": {}
        },

        "economia/precos.json": {
            "versao": 1,
            "precos": {}
        },

        "economia/mercado.json": {
            "versao": 1,
            "oferta": {},
            "demanda": {},
            "comercio": {}
        },

        "diario/diario.json": {
            "versao": 1,
            "entradas": []
        },

        "eventos/ativos.json": {
            "versao": 1,
            "eventos": {}
        },

        "eventos/historico.json": {
            "versao": 1,
            "eventos": []
        }
    }


    def __init__(
        self,
        worlds_dir="data/mundos"
    ):

        self.filesystem = FileSystemManager(
            worlds_dir
        )

        self.validator = Validator()

        self.memory = MemoryManager(
            self.filesystem
        )

        self.context = ContextManager(
            self.memory
        )


    def info(self):

        return {
            "name": self.NAME,
            "version": self.VERSION,
            "status": "online",
            "role":
                "Guardião da memória persistente"
        }


    def status(self):

        return {
            "name": self.NAME,
            "version": self.VERSION,
            "status": "online",

            "components": {
                "filesystem": "online",
                "memory": "online",
                "validator": "online",
                "context": "online"
            }
        }


    def _copy_data(self, data):

        if isinstance(
            data,
            dict
        ):

            return {
                key: self._copy_data(value)
                for key, value in data.items()
            }

        if isinstance(
            data,
            list
        ):

            return [
                self._copy_data(item)
                for item in data
            ]

        return data


    def initialize_world(
        self,
        world_id
    ):

        if not self.validator.valid_world_id(
            world_id
        ):

            raise ValueError(
                "ID de mundo inválido."
            )

        structure = {}

        for file, data in self.WORLD_STRUCTURE.items():

            structure[file] = self._copy_data(
                data
            )

        structure[
            "mundo.json"
        ][
            "id"
        ] = world_id

        self.filesystem.initialize_world(
            world_id,
            structure
        )


    def ensure_world(
        self,
        world_id
    ):

        self.initialize_world(
            world_id
        )


    def read_memory(
        self,
        world_id,
        file
    ):

        self.ensure_world(
            world_id
        )

        return self.memory.read(
            world_id,
            file
        )


    def build_context(
        self,
        world_id,
        message=""
    ):

        self.ensure_world(
            world_id
        )

        return self.context.build(
            world_id,
            message
        )


    def selected_files(
        self,
        world_id,
        message
    ):

        self.ensure_world(
            world_id
        )

        return self.context.describe_selection(
            world_id,
            message
        )


    def update_memory(
        self,
        world_id,
        update
    ):

        self.ensure_world(
            world_id
        )

        valid, reason = (
            self.validator.validate_update(
                update
            )
        )

        if not valid:

            raise ValueError(
                reason
            )

        return self.memory.apply_update(
            world_id,
            update
        )


    def apply_updates(
        self,
        world_id,
        updates
    ):

        self.ensure_world(
            world_id
        )

        valid, rejected = (
            self.validator.validate_updates(
                updates
            )
        )

        results = self.memory.apply_updates(
            world_id,
            valid
        )

        return {
            "applied": results,
            "rejected": rejected
        }


    def file_tree(
        self,
        world_id
    ):

        self.ensure_world(
            world_id
        )

        return self.filesystem.tree(
            world_id
        )