import pytest
import asyncio
from langsmith import Client, evaluate
from langsmith.schemas import Example, Run
from src.tools.search.tool import SearchTool
from src.core.config import get_settings

# Initialize LangSmith client
client = Client()


# Define evaluators
def correctness_evaluator(run: Run, example: Example) -> dict:
    """
    Simple evaluator to check if the output contains expected keywords.
    In a real scenario, this would use an LLM-as-a-judge.
    """
    student_answer = run.outputs.get("output", "")
    expected_answer = example.outputs.get("answer", "")

    # Simple keyword match for this demo
    score = 1.0 if expected_answer.lower() in student_answer.lower() else 0.0

    return {"key": "correctness", "score": score}


@pytest.mark.asyncio
async def test_search_tool_evaluation():
    """
    Run an evaluation on the SearchTool using LangSmith.
    """
    settings = get_settings()
    if not settings.telemetry.langsmith_tracing_enabled:
        pytest.skip("LangSmith tracing not enabled")

    # 1. Create a dataset (if not exists)
    dataset_name = "Company Research Search Test"
    if not client.has_dataset(dataset_name=dataset_name):
        dataset = client.create_dataset(dataset_name=dataset_name)
        client.create_examples(
            inputs=[
                {"query": "Who is the CEO of Microsoft?"},
                {"query": "What is the capital of France?"},
            ],
            outputs=[
                {"answer": "Satya Nadella"},
                {"answer": "Paris"},
            ],
            dataset_id=dataset.id,
        )

    # 2. Define the target function (the "student")
    async def target(inputs: dict) -> dict:
        tool = SearchTool()
        # Use the LangChain wrapper we just added
        lc_tool = tool.to_langchain_tool()
        result = await lc_tool.ainvoke(inputs["query"])
        return {"output": result}

    # 3. Run evaluation
    # Note: 'evaluate' is the new API replacing 'run_on_dataset'
    results = await evaluate(
        target,
        data=dataset_name,
        evaluators=[correctness_evaluator],
        experiment_prefix="search-tool-eval",
    )

    # 4. Assertions
    # We just check that the evaluation ran successfully
    assert results is not None
    print(f"Evaluation complete. View results at: {results.run_url}")
