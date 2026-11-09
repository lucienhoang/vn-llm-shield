"""RAG retrieval with role-based access control. STUB: fake docs, filter by role only.
Real version: issue #11."""

from app.types import Doc

_FAKE_DOCS = [
    Doc(
        "doc_001",
        "Chính sách nghỉ phép: nhân viên được 12 ngày phép mỗi năm.",
        ["employee", "manager", "admin"],
    ),
    Doc("doc_002", "Bảng lương khối quản lý (dữ liệu giả).", ["manager", "admin"]),
]


def retrieve(query: str, role: str, k: int = 3) -> list[Doc]:
    # Filter by role FIRST (the query is ignored in the stub).
    allowed = [d for d in _FAKE_DOCS if role in d.allowed_roles]
    return allowed[:k]
