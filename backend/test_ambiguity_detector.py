"""
Test script for ambiguity detector
"""
import sys
sys.path.insert(0, '.')

from app.models.schema import TableSchema, ColumnSchema, ForeignKeyConstraint
from app.core.ambiguity_detector import detect_all_ambiguities


def test_film_table():
    """Test ambiguity detection on the film table"""
    
    # Create a simplified film table schema for testing
    film_table = TableSchema(
        table_name="film",
        schema_name="public",
        columns=[
            ColumnSchema(
                name="film_id",
                data_type="INTEGER",
                nullable=False,
                primary_key=True,
                default_value="nextval('film_film_id_seq'::regclass)"
            ),
            ColumnSchema(
                name="title",
                data_type="TEXT",
                nullable=False
            ),
            ColumnSchema(
                name="description",
                data_type="TEXT",
                nullable=True
            ),
            ColumnSchema(
                name="release_year",
                data_type="INTEGER",
                nullable=True
            ),
            ColumnSchema(
                name="language_id",
                data_type="SMALLINT",
                nullable=False,
                foreign_key="language.language_id"
            ),
            ColumnSchema(
                name="rental_duration",
                data_type="SMALLINT",
                nullable=False,
                default_value="3"
            ),
            ColumnSchema(
                name="rental_rate",
                data_type="NUMERIC(4,2)",
                nullable=False,
                default_value="4.99"
            ),
            ColumnSchema(
                name="rating",
                data_type="VARCHAR(5)",
                nullable=True,
                default_value="'G'::mpaa_rating"
            ),
            ColumnSchema(
                name="special_features",
                data_type="ARRAY",
                nullable=True
            ),
        ],
        primary_keys=["film_id"],
        foreign_keys=[
            ForeignKeyConstraint(
                column_name="language_id",
                referenced_table="language",
                referenced_column="language_id",
                on_delete=None,
                on_update=None
            )
        ],
        row_count=1000
    )
    
    # Detect ambiguities
    questions = detect_all_ambiguities(film_table)
    
    print(f"\n{'='*80}")
    print(f"AMBIGUITY DETECTION TEST: {film_table.table_name} table")
    print(f"{'='*80}\n")
    print(f"Total questions generated: {len(questions)}\n")
    
    for i, question in enumerate(questions, 1):
        print(f"Question {i}:")
        print(f"  ID: {question.question_id}")
        print(f"  Question: {question.question}")
        print(f"  Context: {question.context[:100]}...")
        print(f"  Suggested answers: {len(question.suggested_answers)}")
        print()
    
    return questions


if __name__ == "__main__":
    questions = test_film_table()
    print(f"[SUCCESS] Test completed successfully! Generated {len(questions)} questions.")

# Made with Bob
