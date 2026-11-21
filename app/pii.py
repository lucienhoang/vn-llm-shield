"""PII masking and unmasking for Vietnamese text (SĐT, CCCD, số tài khoản)."""

import re
from typing import Any

from app.types import MaskResult

PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "CCCD": re.compile(r"(?<!\d)(?:0\d{2}[0-3]\d{2}\d{6}|\d{12})(?!\d)"),
    "PHONE": re.compile(r"(?<!\d)(?:\+84[\s.-]?|0)[35789](?:[\s.-]?\d){8}(?!\d)"),
    "BANK_ACCOUNT": re.compile(
        r"(?i)(?:stk|số\s*tài\s*khoản|tài\s*khoản|account|acc)"
        r"(?:[\s:.-]*|(?:\s+[^\W\d_]+){1,3}\s*:\s*)([0-9]{8,16})(?!\d)"
    ),
}

# Lưu ánh xạ placeholder -> giá trị gốc theo từng session_id để phục vụ unmask()
_SESSION_STORE: dict[str, dict[str, str]] = {}


def detect_pii(text: str) -> list[dict[str, Any]]:
    """Phát hiện các thực thể PII (CCCD, SĐT, số tài khoản) trong văn bản.

    Args:
        text: Chuỗi văn bản đầu vào cần kiểm tra.

    Returns:
        Danh sách dictionary chứa thông tin thực thể (type, value, start, end).
    """
    findings: list[dict[str, Any]] = []

    for pii_type, pattern in PII_PATTERNS.items():
        for match in pattern.finditer(text):
            if pii_type == "BANK_ACCOUNT":
                value = match.group(1)
                start, end = match.span(1)
            else:
                value = match.group(0)
                start, end = match.span(0)

            # Tránh trùng lặp nếu chuỗi 12 chữ số khớp chéo giữa CCCD và STK
            if any(f["start"] <= start and end <= f["end"] for f in findings):
                continue

            findings.append(
                {
                    "type": pii_type,
                    "value": value,
                    "start": start,
                    "end": end,
                }
            )

    findings.sort(key=lambda item: item["start"])
    return findings


def mask(text: str, session_id: str) -> MaskResult:
    """Che giấu PII trong văn bản bằng placeholder đánh số và lưu vào session.

    Args:
        text: Chuỗi văn bản gốc chứa dữ liệu nhạy cảm.
        session_id: Mã định danh phiên làm việc để khôi phục dữ liệu khi cần.

    Returns:
        Đối tượng MaskResult gồm văn bản đã che và danh sách thực thể phát hiện được.
    """
    findings = detect_pii(text)
    if not findings:
        return MaskResult(masked_text=text, entities=[])

    session_map = _SESSION_STORE.setdefault(session_id, {})
    type_counters: dict[str, int] = {}
    entities: list[dict[str, Any]] = []

    # Gán placeholder theo thứ tự xuất hiện từ trái sang phải (vd: [PHONE_1], [PHONE_2])
    for item in findings:
        pii_type = item["type"]
        value = item["value"]

        # Tái sử dụng placeholder nếu giá trị này đã xuất hiện trước đó trong cùng session
        existing_placeholder = next(
            (ph for ph, orig in session_map.items() if orig == value),
            None,
        )

        if existing_placeholder:
            placeholder = existing_placeholder
        else:
            existing_indices = [
                int(ph.rsplit("_", 1)[1][:-1])
                for ph in session_map
                if ph.startswith(f"[{pii_type}_")
            ]
            next_idx = max(existing_indices, default=0) + 1
            type_counters[pii_type] = next_idx
            placeholder = f"[{pii_type}_{next_idx}]"
            session_map[placeholder] = value

        entities.append(
            {
                "type": pii_type,
                "value": value,
                "placeholder": placeholder,
                "start": item["start"],
                "end": item["end"],
            }
        )

    # Thay thế từ cuối lên đầu để không làm lệch chỉ số start/end
    masked_text = text
    for ent in reversed(entities):
        start, end = ent["start"], ent["end"]
        masked_text = masked_text[:start] + ent["placeholder"] + masked_text[end:]

    return MaskResult(masked_text=masked_text, entities=entities)


def unmask(text: str, session_id: str) -> str:
    """Khôi phục các placeholder PII về giá trị gốc dựa trên session_id.

    Args:
        text: Văn bản phản hồi từ LLM chứa các thẻ placeholder.
        session_id: Mã định danh phiên làm việc tương ứng lúc gọi mask().

    Returns:
        Văn bản đã được điền lại giá trị PII gốc.
    """
    session_map = _SESSION_STORE.get(session_id)
    if not session_map:
        return text

    unmasked_text = text
    # Sắp xếp key giảm dần theo độ dài để tránh thay thế nhầm (vd: [PHONE_1] vs [PHONE_10])
    for placeholder in sorted(session_map.keys(), key=len, reverse=True):
        unmasked_text = unmasked_text.replace(placeholder, session_map[placeholder])

    return unmasked_text


def clear_session(session_id: str) -> None:
    """Xóa dữ liệu ánh xạ PII của một phiên khi kết thúc hội thoại.

    Args:
        session_id: Mã định danh phiên cần dọn dẹp.
    """
    _SESSION_STORE.pop(session_id, None)
