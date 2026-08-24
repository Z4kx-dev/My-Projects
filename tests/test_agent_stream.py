from backend.ai.agent import RPGAgent


class FakeLLM:
    def __init__(self):
        self.calls = 0

    def chat(self, messages, stream=False, options=None, tools=None, cancel=None):
        self.calls += 1
        if stream:
            return iter(["Olá ", "mundo"])
        return {"message": {"role": "assistant", "content": "resposta final", "tool_calls": []}}


class FakeOrchestrator:
    def messages(self, world_id, chat_id, user_text):
        return [{"role": "system", "content": "teste"}, {"role": "user", "content": user_text}]


class FakeTools:
    def definitions(self):
        return []

    def call(self, name, arguments):
        raise AssertionError("nenhuma tool deveria ser chamada")


def test_agent_stream_yields_incremental_output():
    llm = FakeLLM()
    agent = RPGAgent(llm, FakeOrchestrator(), FakeTools(), max_iterations=2)
    assert list(agent.stream("001", "001", "oi")) == ["Olá ", "mundo"]
    assert llm.calls == 2
