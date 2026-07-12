import os
import argparse
import httpx

def ingest_file(file_path: str, base_dir: str, project_id: str, version: str, endpoint: str):
    rel_path = os.path.relpath(file_path, base_dir)
    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()
    
    # 파일 내용 읽기
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        
    if not content.strip():
        return
        
    # 요청 페이로드 작성
    payload = {
        "source": {
            "type": "file",
            "uri": rel_path,
            "title": filename,
            "version": version
        },
        "content": content,
        "metadata": {
            "file_path": rel_path,
            "extension": ext,
        }
    }
    
    url = f"{endpoint}/internal/projects/{project_id}/documents"
    try:
        response = httpx.post(url, json=payload, timeout=30.0)
        if response.status_code == 200:
            res_data = response.json()
            print(f"[SUCCESS] Ingested {rel_path} -> Chunks: {res_data['chunk_count']}")
        else:
            print(f"[FAILED] Status {response.status_code} for {rel_path}: {response.text}")
    except Exception as e:
        print(f"[ERROR] Failed to connect to memory service at {url}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Aegis RAG Ingestion Pipeline CLI")
    parser.add_argument("--project-id", default="aegis-system-docs", help="Target RAG namespace project_id")
    parser.add_argument("--dir", required=True, help="Base directory containing documentation files")
    parser.add_argument("--doc-version", default="1.0.0", help="Document version for tagging data")
    parser.add_argument("--endpoint", default="http://localhost:8095", help="aegis-memory service base endpoint")
    args = parser.parse_args()
    
    if not os.path.exists(args.dir):
        print(f"[ERROR] Directory '{args.dir}' does not exist.")
        return
        
    allowed_extensions = {".md", ".yaml", ".yml", ".json"}
    
    print(f"[*] Starting ingestion for project '{args.project_id}' (version: {args.doc_version}) from dir '{args.dir}'...")
    
    count = 0
    for root, dirs, files in os.walk(args.dir):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d.lower() not in ('node_modules', 'venv', '.venv', 'dist', 'build', 'htmlcov', 'nas', 'nas_mock') and 'nas' not in d.lower()]
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in allowed_extensions:
                file_path = os.path.join(root, file)
                ingest_file(file_path, args.dir, args.project_id, args.doc_version, args.endpoint)
                count += 1
                
    print(f"[*] Completed. Processed {count} file(s).")

if __name__ == "__main__":
    main()
