"""Slash command handlers."""
import json

from db import query, snapshot_info
from nl_query import ask


def cmd_help(text: str) -> str:
    return (
        '*Camera Trap 分析機器人*\n'
        '`/ct-help`  顯示本說明\n'
        '`/ct-projects [keyword]`  列出計畫（可用關鍵字過濾）\n'
        '`/ct-stats <project_id|name>`  某計畫的統計摘要\n'
        '`/ct-snapshot`  顯示目前資料快照時間\n'
        '`/ct-ask <問題>`  用自然語言提問（LLM 生成 SQL）\n'
    )


def cmd_projects(text: str) -> str:
    keyword = (text or '').strip()
    if keyword:
        rows = query(
            'SELECT project_id, project_name, n_deployments, n_images, n_species '
            'FROM v_project_summary '
            'WHERE project_name ILIKE ? OR COALESCE(short_title, \'\') ILIKE ? '
            'ORDER BY n_images DESC LIMIT 25;',
            (f'%{keyword}%', f'%{keyword}%'),
        )
    else:
        rows = query(
            'SELECT project_id, project_name, n_deployments, n_images, n_species '
            'FROM v_project_summary '
            'ORDER BY n_images DESC LIMIT 25;'
        )

    if not rows:
        return f'找不到符合「{keyword}」的計畫。'

    header = f'*計畫列表{f"（關鍵字：{keyword}）" if keyword else ""}* — 共 {len(rows)} 筆'
    lines = [header, '```', f'{"id":>5}  {"相機數":>6}  {"影像數":>10}  {"物種數":>6}  計畫名稱']
    for pid, name, ndep, nimg, nsp in rows:
        lines.append(
            f'{pid:>5}  {(ndep or 0):>6}  {(nimg or 0):>10,}  {(nsp or 0):>6}  {name}'
        )
    lines.append('```')
    return '\n'.join(lines)


def cmd_stats(text: str) -> str:
    target = (text or '').strip()
    if not target:
        return '用法：`/ct-stats <project_id|計畫名稱關鍵字>`'

    if target.isdigit():
        rows = query(
            'SELECT project_id, project_name, short_title, funding_agency, '
            '       start_date, end_date, mode, is_public, '
            '       n_deployments, n_studyareas, n_images, n_species, '
            '       first_image_at, last_image_at '
            'FROM v_project_summary WHERE project_id = ? LIMIT 1;',
            (int(target),),
        )
    else:
        rows = query(
            'SELECT project_id, project_name, short_title, funding_agency, '
            '       start_date, end_date, mode, is_public, '
            '       n_deployments, n_studyareas, n_images, n_species, '
            '       first_image_at, last_image_at '
            'FROM v_project_summary '
            'WHERE project_name ILIKE ? OR COALESCE(short_title, \'\') ILIKE ? '
            'ORDER BY n_images DESC LIMIT 1;',
            (f'%{target}%', f'%{target}%'),
        )

    if not rows:
        return f'找不到計畫「{target}」。'

    (pid, name, short, funder, sd, ed, mode, is_public,
     ndep, nsa, nimg, nsp, first_dt, last_dt) = rows[0]

    top_species = query(
        'SELECT species, COUNT(*) AS n '
        'FROM image WHERE project_id = ? AND species IS NOT NULL AND species <> \'\' '
        'GROUP BY species ORDER BY n DESC LIMIT 10;',
        (pid,),
    )

    parts = [
        f'*{name}* (id: `{pid}`)',
        f'簡稱：{short or "—"}｜委辦單位：{funder or "—"}｜模式：{mode or "—"}｜公開：{"是" if is_public else "否"}',
        f'計畫期間：{sd or "—"} ~ {ed or "—"}',
        '',
        f'相機位置：{ndep or 0}　樣區：{nsa or 0}　影像總數：{(nimg or 0):,}　物種數：{nsp or 0}',
        f'最早影像：{first_dt or "—"}　最晚影像：{last_dt or "—"}',
    ]
    if top_species:
        parts.append('')
        parts.append('*Top 10 物種*')
        parts.append('```')
        for sp, n in top_species:
            parts.append(f'{n:>10,}  {sp}')
        parts.append('```')
    return '\n'.join(parts)


def cmd_snapshot(text: str) -> str:
    info = snapshot_info()
    if not info:
        return '找不到資料快照。請先執行每週 ETL。'
    counts = json.loads(info['row_counts_json'] or '{}')
    top = sorted(counts.items(), key=lambda kv: kv[1] or 0, reverse=True)[:6]
    lines = [
        f'*快照時間*: {info["run_at"]} UTC',
        f'ETL 耗時: {info["duration_sec"]:.1f}s',
        '*主要資料表列數*:',
        '```',
    ]
    for name, n in top:
        lines.append(f'{n or 0:>12,}  {name}')
    lines.append('```')
    return '\n'.join(lines)


HANDLERS = {
    '/ct-help': cmd_help,
    '/ct-projects': cmd_projects,
    '/ct-stats': cmd_stats,
    '/ct-snapshot': cmd_snapshot,
    '/ct-ask': ask,
}
