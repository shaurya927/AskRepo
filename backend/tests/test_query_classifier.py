"""Tests for query classifier."""

from app.services.rag.query_classifier import classify_query


class TestQueryClassifier:

    def test_code_question_function(self):
        assert classify_query("What does calculate_price() do?") == "code"

    def test_code_question_class(self):
        assert classify_query("Explain the UserService class") == "code"

    def test_code_question_method(self):
        assert classify_query("Show me the method getUser") == "code"

    def test_architecture_question(self):
        assert classify_query("How does authentication work?") == "architecture"

    def test_architecture_data_flow(self):
        assert classify_query("What is the data flow in this application?") == "architecture"

    def test_architecture_structure(self):
        assert classify_query("How is the code organized and structured?") == "architecture"

    def test_repository_overview(self):
        assert classify_query("What does this project do?") == "repository"

    def test_repository_technologies(self):
        assert classify_query("What technologies and frameworks are used?") == "repository"

    def test_historical_question(self):
        assert classify_query("Why was this function introduced?") == "historical"

    def test_historical_commit(self):
        assert classify_query("When did the authentication change?") == "historical"

    def test_general_fallback(self):
        assert classify_query("Tell me something interesting") == "general"

    def test_empty_query(self):
        assert classify_query("") == "general"
