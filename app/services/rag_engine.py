import json
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

from app.utils.config import DB_PATH


def load_historical_cases() -> list[dict[str, object]]:
    """读取历史异常案例 JSON 数据。"""
    file_path = Path("data/historical_cases.json")

    with file_path.open("r", encoding="utf-8") as file:
        cases = json.load(file)

    return cases


def build_case_text(case: dict[str, object]) -> str:
    """将单条历史案例整理为适合向量化的文本。"""
    tags = case.get("tags", [])
    tags_text = ", ".join(tags) if isinstance(tags, list) else ""

    return (
        f"标题: {case.get('title', '')}\n"
        f"描述: {case.get('description', '')}\n"
        f"异常类型: {case.get('error_type', '')}\n"
        f"严重等级: {case.get('severity', '')}\n"
        f"根因: {case.get('root_cause', '')}\n"
        f"解决方案: {case.get('solution', '')}\n"
        f"标签: {tags_text}"
    )


def get_embedding_model() -> HuggingFaceEmbeddings:
    """创建本地文本向量模型。"""
    return HuggingFaceEmbeddings(
        model_name=r"D:\models\models\BAAI--bge-base-zh-v1.5\snapshots\master"
    )


def build_documents(
    cases: list[dict[str, object]],
) -> list[Document]:
    """将历史案例转换为 LangChain Document。"""
    documents = []

    for case in cases:
        document = Document(
            page_content=build_case_text(case),
            metadata={
                "id": str(case.get("id", "")),
                "title": str(case.get("title", "")),
                "error_type": str(case.get("error_type", "")),
                "severity": str(case.get("severity", "")),
            },
        )

        documents.append(document)

    return documents


def create_vector_store() -> Chroma:
    """创建并持久化历史案例 Chroma 向量数据库。"""
    cases = load_historical_cases()
    documents = build_documents(cases)

    embedding_model = get_embedding_model()

    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embedding_model,
        persist_directory=DB_PATH,
        collection_name="historical_cases",
    )

    return vector_store


def search_similar_cases(
    query: str,
    k: int = 3,
) -> list[Document]:
    """检索与当前异常最相似的历史案例。"""
    embedding_model = get_embedding_model()

    vector_store = Chroma(
        collection_name="historical_cases",
        embedding_function=embedding_model,
        persist_directory=DB_PATH,
    )

    results = vector_store.similarity_search(
        query=query,
        k=k,
    )

    return results


def format_search_results(
    documents: list[Document],
) -> list[dict[str, object]]:
    """将检索结果整理为可返回给 API 的结构化数据。"""
    results = []

    for document in documents:
        results.append(
            {
                "id": document.metadata.get("id", ""),
                "title": document.metadata.get("title", ""),
                "error_type": document.metadata.get("error_type", ""),
                "severity": document.metadata.get("severity", ""),
                "content": document.page_content,
            }
        )

    return results


def retrieve_similar_cases(
    query: str,
    k: int = 3,
) -> list[dict[str, object]]:
    """检索并返回结构化历史案例结果。"""
    documents = search_similar_cases(query=query, k=k)

    return format_search_results(documents)