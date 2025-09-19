import chromadb

# 현재 메타데이터 파악하는 코드 입니다.
# ChromaDB 클라이언트 연결

client = chromadb.HttpClient(host='144.24.69.36', port=8001)

"""
# **컬렉션 명**
# 승인된 데이터: approved_templates
# 스팸 관련 정보통신망법 안내서 pdf: spam_prevention_documents
"""

collection_name = "approved_templates"
collection = client.get_collection(collection_name)

# 컬렉션에서 데이터 1개 조회
# metadatas
sample_data = collection.get(limit=1, include=["metadatas"])

# 메타데이터 구조 출력
print("ChromaDB에 저장된 메타데이터 샘플:")
print(sample_data['metadatas'][0])

# 'priority': 'high',
# 'id': '00',
# 'title': '회사소개서 발송',
# 'source': 'approved_data',
# 'category_1': '서비스이용',
# 'template_type': 'approved_template',
# 'category_2': '이용안내/공지',
# 'button': '소개서