from langchain_core.messages import AIMessage

from app.ai.direct_prompt import DirectPromptSummarizer, build_summary_prompt


class FakeModel:
    def __init__(self, content: str) -> None:
        self.content = content
        self.calls = 0

    def invoke(self, _messages):
        self.calls += 1
        return AIMessage(content=self.content)


def test_build_summary_prompt_includes_required_constraints() -> None:
    prompt = build_summary_prompt("A fantasy quest with dragons.")

    assert "Task:" in prompt
    assert "Audience:" in prompt
    assert "Length: Exactly two concise sentences." in prompt
    assert "Grounding constraint:" in prompt
    assert "A fantasy quest with dragons." in prompt


def test_direct_prompt_summarizer_invokes_model_once_and_limits_output() -> None:
    model = FakeModel("Sentence one. Sentence two. Sentence three.")
    summarizer = DirectPromptSummarizer(model)

    summary = summarizer.summarize("A long description")

    assert model.calls == 1
    assert summary == "Sentence one. Sentence two."
