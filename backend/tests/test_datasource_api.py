from app.models import Datasource
from app.core.security import encrypt_password


def test_datasource_create(db_session):
    ds = Datasource(
        name="test", type="mysql", host="localhost", port=3306,
        username="root", password=encrypt_password("secret"),
        database="testdb",
    )
    db_session.add(ds)
    db_session.commit()

    saved = db_session.query(Datasource).first()
    assert saved.name == "test"
    assert saved.type == "mysql"
    assert saved.host == "localhost"
