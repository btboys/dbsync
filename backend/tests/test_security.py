from app.core.security import encrypt_password, decrypt_password


def test_password_encrypt_decrypt():
    original = "my_secret_password_123"
    encrypted = encrypt_password(original)
    assert encrypted != original
    decrypted = decrypt_password(encrypted)
    assert decrypted == original


def test_encryption_different_each_time():
    original = "same_password"
    e1 = encrypt_password(original)
    e2 = encrypt_password(original)
    assert e1 != e2


def test_encrypt_empty_string():
    encrypted = encrypt_password("")
    decrypted = decrypt_password(encrypted)
    assert decrypted == ""
