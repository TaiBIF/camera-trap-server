"""Natural-language querying: question -> SQL -> DuckDB -> summary."""
import logging
import os
import threading
from pathlib import Path

import anthropic
import duckdb

from db import DUCKDB_PATH
from safety import UnsafeSQLError, sanitize

log = logging.getLogger('nl_query')

MODEL = os.environ.get('ANTHROPIC_MODEL', 'claude-sonnet-4-6')
MAX_ROWS = 500
QUERY_TIMEOUT_MS = 15_000

_schema_path = Path(__file__).parent / 'schema.md'
SCHEMA_DOC = _schema_path.read_text(encoding='utf-8')

SQLGEN_SYSTEM = (
    'You convert Chinese/English wildlife camera-trap analytics questions into '
    'a single read-only DuckDB SQL query. Output ONLY the SQL, no prose, no '
    'code fences, no explanation. Follow every rule in the schema document.'
)

SUMMARY_SYSTEM = (
    '你是台灣野生動物相機陷阱資料分析助手。根據 SQL 查詢結果以繁體中文簡潔回答使用者的問題。'
    '若結果為空，直接說「查無資料」。若有數字，保留合理精度。不要複述 SQL。'
    '回答長度控制在三段以內。'
)

_client: anthropic.Anthropic | None = None


def _anthropic() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
    return _client


def _generate_sql(question: str) -> str:
    resp = _anthropic().messages.create(
        model=MODEL,
        max_tokens=1024,
        system=[
            {'type': 'text', 'text': SQLGEN_SYSTEM},
            {
                'type': 'text',
                'text': SCHEMA_DOC,
                'cache_control': {'type': 'ephemeral'},
            },
        ],
        messages=[{'role': 'user', 'content': question}],
    )
    return ''.join(b.text for b in resp.content if b.type == 'text')


def _execute(sql: str) -> tuple[list[str], list[tuple]]:
    con = duckdb.connect(DUCKDB_PATH, read_only=True)
    timer = threading.Timer(QUERY_TIMEOUT_MS / 1000.0, con.interrupt)
    timer.start()
    try:
        cursor = con.execute(sql)
        rows = cursor.fetchmany(MAX_ROWS)
        columns = [d[0] for d in cursor.description] if cursor.description else []
        return columns, rows
    finally:
        timer.cancel()
        con.close()


def _summarize(question: str, sql: str, columns: list[str], rows: list[tuple]) -> str:
    sample = rows[:50]
    preview = {
        'columns': columns,
        'rows': [[str(v) for v in r] for r in sample],
        'truncated': len(rows) > len(sample),
        'total_rows_returned': len(rows),
    }
    prompt = (
        f'使用者問題：{question}\n\n'
        f'執行的 SQL：\n```sql\n{sql}\n```\n\n'
        f'查詢結果（JSON）：\n```json\n{preview}\n```\n\n'
        '請用繁體中文回答使用者的問題。'
    )
    resp = _anthropic().messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SUMMARY_SYSTEM,
        messages=[{'role': 'user', 'content': prompt}],
    )
    return ''.join(b.text for b in resp.content if b.type == 'text').strip()


def _format_table(columns: list[str], rows: list[tuple], cap: int = 10) -> str:
    if not rows:
        return ''
    shown = rows[:cap]
    widths = [len(c) for c in columns]
    for row in shown:
        for i, v in enumerate(row):
            widths[i] = max(widths[i], len(str(v)))
    header = '  '.join(c.ljust(widths[i]) for i, c in enumerate(columns))
    body = '\n'.join(
        '  '.join(str(v).ljust(widths[i]) for i, v in enumerate(row))
        for row in shown
    )
    more = f'\n…（共 {len(rows)} 列）' if len(rows) > cap else ''
    return f'```\n{header}\n{body}{more}\n```'


def ask(question: str) -> str:
    question = (question or '').strip()
    if not question:
        return '用法：`/ct-ask <問題>`，例如：`/ct-ask 2024 年哪個計畫拍到最多石虎？`'

    try:
        raw_sql = _generate_sql(question)
        log.info('raw_sql=%r', raw_sql)
        sql = sanitize(raw_sql)
    except UnsafeSQLError as exc:
        return f':warning: SQL 檢查失敗：{exc}'
    except anthropic.APIError as exc:
        log.exception('anthropic failed')
        return f':warning: LLM 呼叫失敗：`{exc}`'

    try:
        columns, rows = _execute(sql)
    except duckdb.Error as exc:
        return f':warning: 查詢失敗：`{exc}`\n產生的 SQL：\n```sql\n{sql}\n```'

    try:
        answer = _summarize(question, sql, columns, rows)
    except anthropic.APIError as exc:
        log.exception('summary failed')
        answer = f'(無法取得摘要：{exc})'

    parts = [answer, _format_table(columns, rows)]
    parts.append(f'_SQL:_ `{sql}`')
    return '\n\n'.join(p for p in parts if p)
