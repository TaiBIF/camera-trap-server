"""SQL safety guards for LLM-generated queries."""
import re

FORBIDDEN = re.compile(
    r'\b(INSERT|UPDATE|DELETE|DROP|ATTACH|DETACH|COPY|PRAGMA|CREATE|ALTER|'
    r'REPLACE|LOAD|INSTALL|EXPORT|IMPORT|VACUUM|CHECKPOINT|SET|CALL|EXECUTE|'
    r'USE|TRUNCATE|GRANT|REVOKE)\b',
    re.IGNORECASE,
)


class UnsafeSQLError(Exception):
    pass


def sanitize(sql: str) -> str:
    """Return a cleaned SQL string or raise UnsafeSQLError."""
    sql = sql.strip()
    # Strip markdown code fences if the LLM added them.
    if sql.startswith('```'):
        sql = re.sub(r'^```(?:sql)?\s*', '', sql)
        sql = re.sub(r'\s*```$', '', sql)
    sql = sql.strip().rstrip(';').strip()

    if not sql:
        raise UnsafeSQLError('空白查詢')
    if not re.match(r'^(SELECT|WITH)\b', sql, re.IGNORECASE):
        raise UnsafeSQLError('只允許 SELECT 或 WITH 開頭的查詢')
    if ';' in sql:
        raise UnsafeSQLError('只允許單一查詢')
    if FORBIDDEN.search(sql):
        raise UnsafeSQLError('查詢包含禁止的關鍵字')

    return sql
