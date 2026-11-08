from app.db.models import Posting


def test_term_id_index_declared():
    indexes = {
        index.name: [
            column.name for column in index.columns
        ]
        for index in Posting.__table__.indexes
    }

    assert indexes["ix_postings_term_id"] == ["term_id"]
