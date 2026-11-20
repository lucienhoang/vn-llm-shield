import pytest
from pii import clear_session, detect_pii, mask, unmask


@pytest.mark.parametrize(
    "text, expected_type, expected_value",
    [
        ("Gọi cho tôi qua số 0912345678 nhé.", "PHONE", "0912345678"),
        ("SĐT liên hệ: +84 987 654 321", "PHONE", "+84 987 654 321"),
        ("Số điện thoại 038.456.7890", "PHONE", "038.456.7890"),
        ("CCCD của nhân viên là 046095001234.", "CCCD", "046095001234"),
        ("Chuyển tiền vào STK: 19034567890123", "BANK_ACCOUNT", "19034567890123"),
        ("Số tài khoản nhận: 0011001234567", "BANK_ACCOUNT", "0011001234567"),
    ],
)
def test_detect_pii_positive(
    text: str, expected_type: str, expected_value: str
) -> None:
    results = detect_pii(text)
    assert len(results) == 1
    assert results[0]["type"] == expected_type
    assert results[0]["value"] == expected_value


@pytest.mark.parametrize(
    "text",
    [
        "Mã đơn hàng #1234567890123456 đã giao thành công.",
        "Tổng hóa đơn thanh toán là 15000000 đồng.",
        "Số hotline cũ 02438251234 không còn sử dụng.",
        "Năm 2026 dự kiến tăng trưởng 12%.",
    ],
)
def test_detect_pii_false_positives(text: str) -> None:
    assert detect_pii(text) == []


def test_mask_and_unmask_roundtrip() -> None:
    session_id = "sess_test_001"
    clear_session(session_id)

    raw = (
        "Khách hàng Nguyễn Văn A, CCCD 079090005678, "
        "SĐT 0909.123.456, STK 9988776655."
    )
    result = mask(raw, session_id=session_id)

    assert result.masked_text == (
        "Khách hàng Nguyễn Văn A, CCCD [CCCD_1], "
        "SĐT [PHONE_1], STK [BANK_ACCOUNT_1]."
    )
    assert len(result.entities) == 3

    llm_reply = "Đã xác nhận thông tin cho số [PHONE_1] và chuyển khoản về [BANK_ACCOUNT_1]."
    restored = unmask(llm_reply, session_id=session_id)
    assert restored == (
        "Đã xác nhận thông tin cho số 0909.123.456 và chuyển khoản về 9988776655."
    )

    clear_session(session_id)


def test_session_isolation() -> None:
    mask("Gọi số 0911111111", session_id="sess_A")
    mask("Gọi số 0922222222", session_id="sess_B")

    assert unmask("Số của bạn là [PHONE_1]", session_id="sess_A") == "Số của bạn là 0911111111"
    assert unmask("Số của bạn là [PHONE_1]", session_id="sess_B") == "Số của bạn là 0922222222"
    assert unmask("Số của bạn là [PHONE_1]", session_id="sess_unknown") == "Số của bạn là [PHONE_1]"

    clear_session("sess_A")
    clear_session("sess_B")