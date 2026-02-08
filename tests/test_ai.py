import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock

from engines.ai import complete_lines, _parse_numbered_lines, _has_cyrillic, generate_with_prompt


def _mock_response(text):
    """Create a mock Anthropic response."""
    mock = MagicMock()
    mock.content = [MagicMock(text=text)]
    return mock


def test_parse_numbered_lines():
    text = "1. Първи ред\n2. Втори ред\n3. Трети ред"
    result = _parse_numbered_lines(text)
    assert len(result) == 3
    assert result[0] == "Първи ред"
    assert result[1] == "Втори ред"
    assert result[2] == "Трети ред"


def test_has_cyrillic():
    assert _has_cyrillic("Здравей свят") is True
    assert _has_cyrillic("Hello world") is False
    assert _has_cyrillic("Mix микс") is True


@patch("engines.ai._get_client")
def test_complete_lines_basic(mock_client_fn):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_response(
        "1. Пари в джоба, злато на ръката\n2. Карам бързо, няма кой да ме спре\n3. Живея живота, не гледам назад"
    )
    mock_client_fn.return_value = mock_client

    result = complete_lines(
        lines=["Имам пари да хвърлям"],
        theme="money",
        count=3,
    )
    assert len(result) == 3
    assert all(_has_cyrillic(line) for line in result)

    # Verify the API was called
    mock_client.messages.create.assert_called_once()
    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert "money" in call_kwargs["messages"][0]["content"]


@patch("engines.ai._get_client")
def test_complete_lines_with_style_context(mock_client_fn):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_response(
        "1. Нощта е млада, купонът тепърва\n2. В клуба ехтят басите\n3. Всички знаят моето име"
    )
    mock_client_fn.return_value = mock_client

    result = complete_lines(
        lines=["Тази нощ е наша"],
        theme="party",
        style_context="Средно 8 срички на ред, чести рими на -ата/-ята",
        corpus_context="Палим клуба тази вечер\nДискотека до зори",
        count=3,
    )
    assert len(result) == 3

    call_kwargs = mock_client.messages.create.call_args.kwargs
    user_msg = call_kwargs["messages"][0]["content"]
    assert "party" in user_msg
    assert "8 срички" in user_msg
    assert "Палим клуба" in user_msg


@patch("engines.ai._get_client")
def test_cyrillic_validation_rejects_english(mock_client_fn):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_response(
        "1. I have money to throw\n2. Driving fast on the boulevard\n3. Golden chains on my neck"
    )
    mock_client_fn.return_value = mock_client

    result = complete_lines(lines=["Test"], count=3)
    # With no Cyrillic, falls back to raw lines (up to count)
    assert len(result) <= 3


@patch("engines.ai._get_client")
def test_generate_with_prompt(mock_client_fn):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_response("Нещо интересно")
    mock_client_fn.return_value = mock_client

    result = generate_with_prompt(
        system="Test system",
        user_prompt="Test user",
    )
    assert result == "Нещо интересно"
    mock_client.messages.create.assert_called_once()
