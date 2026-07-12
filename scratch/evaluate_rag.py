import os
import argparse
import re
import httpx
import openai

EVAL_QUESTIONS = [
    "Aegis Memory의 API 포트는 기본적으로 몇 번인가요?",
    "Aegis Gateway에서 타임아웃 기본값은 몇 초인가요?",
    "Aegis의 공통 계약 스키마 정의에서 데이터 필드 명명 규칙은 무엇인가요?",
    "Aegis Memory에서 PostgreSQL DB를 쓸 때 vector 데이터타입을 사용하는 테이블은 무엇인가요?",
    "오픈소스 프로젝트인 Aegis에서 사내 전용 인프라 IP를 노출하지 않으려면 가이드를 어디에 보관해야 하나요?"
]

def query_rag(query: str, project_id: str, endpoint: str, version: str | None = None) -> dict:
    url = f"{endpoint}/internal/projects/{project_id}/search"
    payload = {"query": query, "limit": 3}
    if version:
        payload["version"] = version
    try:
        response = httpx.post(url, json=payload, timeout=15.0)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"[RAG Error] {e}")
    return {}

def call_llm_generator(query: str, contexts: list[str], llm_client: openai.OpenAI, model: str, mock: bool = False) -> str:
    if mock:
        # Mock answers based on query keywords
        if "포트" in query:
            return "Aegis Memory의 기본 API 포트는 8095번입니다. 이는 내부 네트워크에서만 접근 가능하도록 설계되었습니다."
        elif "타임아웃" in query:
            return "Aegis Gateway의 HTTP 클라이언트 및 API 호출 기본 타임아웃은 AEGIS_HTTP_TIMEOUT 환경변수에 의해 90.0초로 지정됩니다."
        elif "명명 규칙" in query:
            return "Aegis의 공통 계약 스키마(contracts) 정의에서 데이터 필드는 기본적으로 snake_case를 사용합니다."
        elif "PostgreSQL" in query:
            return "Aegis Memory에서 pgvector를 사용하는 테이블은 memory_chunks 테이블의 embedding 컬럼입니다."
        elif "IP" in query:
            return "사내 전용 환경 및 인프라 사설 IP 등 비공개 가이드는 .gitignore에 등록되는 docs/internal/ 디렉토리에 보관해야 합니다."
        return "주어진 컨텍스트에 기반한 목업 답변입니다."

    context_str = "\n\n".join(contexts)
    prompt = f"""당신은 Aegis 시스템 개발 지원 에이전트입니다. 주어진 Context를 기반으로 사용자의 Question에 정확하게 답변하세요.
Context에 없는 내용은 억지로 지어내지 말고 모른다고 답하세요.

[Context]
{context_str}

[Question]
{query}

[Answer]"""
    try:
        response = llm_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating answer: {e}"

def evaluate_faithfulness(answer: str, contexts: list[str], llm_client: openai.OpenAI, model: str, mock: bool = False) -> float:
    if mock:
        import random
        return round(random.uniform(0.85, 1.0), 2)

    context_str = "\n\n".join(contexts)
    prompt = f"""주어진 Context와 Answer를 평가하여 Answer의 충실도(Faithfulness) 점수를 소수점 형식(0.0에서 1.0 사이)으로만 출력하세요.
- Answer에 적힌 주장/사실들이 Context에 명시된 사실과 일치하고 추론 가능하다면 1.0에 가까운 점수를 부여하세요.
- Context에 없는 독자적인 내용이나 할루시네이션(거짓 정보)이 포함되어 있다면 감점하십시오.
- 오직 숫자(예: 0.85)만 출력하세요. 다른 텍스트나 설명은 절대 금지합니다.

[Context]
{context_str}

[Answer]
{answer}

[Score (0.0 ~ 1.0)]:"""
    score_text = "0.0"
    try:
        response = llm_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=10
        )
        score_text = response.choices[0].message.content.strip()
        return float(score_text)
    except Exception:
        match = re.search(r"0\.\d+|1\.0|0", score_text)
        if match:
            return float(match.group(0))
        return 0.0

def evaluate_relevance(query: str, answer: str, llm_client: openai.OpenAI, model: str, mock: bool = False) -> float:
    if mock:
        import random
        return round(random.uniform(0.80, 0.98), 2)

    prompt = f"""주어진 Question과 Answer를 평가하여 Answer가 Question에 얼마나 직접적으로 대응하는 관련 있는 답변인지 점수(0.0에서 1.0 사이)로만 출력하세요.
- 질문에 대한 답변으로 적절하며 엉뚱한 소리를 하지 않는다면 1.0에 가까운 점수를 부여하세요.
- 질문의 핵심을 벗어나 있거나 딴소리를 한다면 감점하십시오.
- 오직 숫자(예: 0.9)만 출력하세요. 다른 텍스트나 설명은 절대 금지합니다.

[Question]
{query}

[Answer]
{answer}

[Score (0.0 ~ 1.0)]:"""
    score_text = "0.0"
    try:
        response = llm_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=10
        )
        score_text = response.choices[0].message.content.strip()
        return float(score_text)
    except Exception:
        match = re.search(r"0\.\d+|1\.0|0", score_text)
        if match:
            return float(match.group(0))
        return 0.0

def main():
    parser = argparse.ArgumentParser(description="Aegis RAG Evaluation Pipeline")
    parser.add_argument("--project-id", default="aegis-system-docs", help="Target RAG namespace project_id")
    parser.add_argument("--endpoint", default="http://localhost:8095", help="aegis-memory service endpoint")
    parser.add_argument("--llm-model", default="text-davinci-003", help="Model name for generation & evaluation")
    parser.add_argument("--openai-api-key", default="dummy", help="OpenAI API Key (or vLLM API Key)")
    parser.add_argument("--openai-base-url", default="", help="OpenAI Base URL (or vLLM Base URL)")
    parser.add_argument("--doc-version", default=None, help="Specific RAG data version to query")
    parser.add_argument("--mock", action="store_true", help="Enable mock evaluation for offline demo")
    args = parser.parse_args()
    
    api_key = args.openai_api_key
    base_url = args.openai_base_url or None
    llm_client = openai.OpenAI(api_key=api_key, base_url=base_url)
    
    print(f"[*] Starting RAG evaluation for project: {args.project_id}")
    print(f"[*] Endpoint: {args.endpoint}")
    if args.doc_version:
        print(f"[*] Querying Version: {args.doc_version}")
    if args.mock:
        print("[*] MODE: Offline Mock Demonstration Enabled")
    else:
        print(f"[*] LLM Model: {args.llm_model}")
    
    results = []
    total_faithfulness = 0.0
    total_relevance = 0.0
    valid_count = 0
    
    for q in EVAL_QUESTIONS:
        print(f"\n[Q] Question: {q}")
        
        # 1. RAG Search
        rag_data = query_rag(q, args.project_id, args.endpoint, version=args.doc_version)
        if not rag_data or not rag_data.get("chunks"):
            print("[-] No chunks retrieved from RAG.")
            results.append({
                "question": q,
                "rag_hit": False,
                "answer": "N/A",
                "faithfulness": 0.0,
                "relevance": 0.0
            })
            continue
            
        contexts = [chunk["text"] for chunk in rag_data["chunks"]]
        print(f"[+] Retrieved {len(contexts)} chunk(s).")
        
        # 2. Generate Answer
        answer = call_llm_generator(q, contexts, llm_client, args.llm_model, mock=args.mock)
        print(f"[A] Generated Answer:\n{answer}")
        
        # 3. Evaluate
        faith = evaluate_faithfulness(answer, contexts, llm_client, args.llm_model, mock=args.mock)
        rel = evaluate_relevance(q, answer, llm_client, args.llm_model, mock=args.mock)
        
        print(f"[E] Faithfulness: {faith:.2f} | Answer Relevance: {rel:.2f}")
        
        results.append({
            "question": q,
            "rag_hit": True,
            "answer": answer,
            "faithfulness": faith,
            "relevance": rel
        })
        
        total_faithfulness += faith
        total_relevance += rel
        valid_count += 1
        
    if valid_count > 0:
        avg_faith = total_faithfulness / valid_count
        avg_rel = total_relevance / valid_count
        print("\n================ EVALUATION SUMMARY ================")
        print(f"Average Faithfulness (충실도): {avg_faith:.4f}")
        print(f"Average Answer Relevance (답변 관련성): {avg_rel:.4f}")
        print("====================================================")
    else:
        print("\n[!] No evaluation could be performed.")

if __name__ == "__main__":
    main()
