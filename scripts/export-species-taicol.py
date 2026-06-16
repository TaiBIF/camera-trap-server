"""
Export taicat_species (id, name) with a TaiCOL taxon mapping.

For each species name, look up the TaiCOL taxon id via the v2 taxon API:
  https://api.taicol.tw/v2/taxon?common_name={name}
  (docs: https://taicol.tw/zh-hant/api)

Output columns:
  id                 — taicat_species.id
  name               — taicat_species.name (kept verbatim, even if junk)
  taicol_taxon_id    — matched TaiCOL taxon_id, '' if none
  is_valid           — T if an *accepted* taxon was matched, else F
  scientific_name    — matched simple_name (for verification)
  taxon_status       — matched taxon_status (accepted / not-accepted / ...)
  note               — ignored | no-match | ok

Names that are obviously not a species — pure number / alphabet / symbol / path
(no CJK char), or anything containing 人 (人, 獵人, 研究人員, ...) — are NOT
queried: they are kept in the table with is_valid=F and note=ignored.

Matching rule (to avoid wrong fuzzy mappings, the returned record must really
carry our name):
  1. exact match on the primary common_name_c (accepted preferred); else
  2. exact match on a comma-separated element of alternative_name_c, but ONLY
     when unambiguous — exactly one taxon carries that name. Generic colloquial
     names (e.g. 老鼠 is an alternative name of 39 unrelated dragonet fish) are
     therefore left unmatched instead of mapped to an arbitrary taxon.

Usage:
  python scripts/export-species-taicol.py                 # -> stdout
  python scripts/export-species-taicol.py -o species-taicol.csv
"""

import argparse
import csv
import os
import re
import sys
import time

import django
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')
django.setup()

from taicat.models import Species

API_URL = 'https://api.taicol.tw/v2/taxon'
CJK_RE = re.compile(r'[一-鿿]')

OUTPUT_COLUMNS = [
    'id', 'name', 'taicol_taxon_id', 'is_valid',
    'scientific_name', 'taxon_status', 'note',
]


def is_ignored(name):
    """True for names that are obviously not a species: number / alphabet /
    symbol / path (no CJK), or human labels containing 人."""
    s = (name or '').strip()
    if not s:
        return True
    if '人' in s:
        return True
    if not CJK_RE.search(s):
        return True
    return False


def match_taxon(name, data):
    """Pick the taxon record that actually carries `name`, preferring accepted
    ones. Returns the record dict, or None when there is no match or the
    alternative-name match is ambiguous (carried by more than one taxon)."""
    name = (name or '').strip()

    # 1) exact match on the primary Chinese common name (accepted preferred)
    primary = [t for t in data if (t.get('common_name_c') or '').strip() == name]
    primary_accepted = [t for t in primary if t.get('taxon_status') == 'accepted']
    if primary_accepted:
        return primary_accepted[0]
    if primary:
        return primary[0]

    # 2) exact match on an alternative name — only if unambiguous
    def carries(t):
        return name in [a.strip() for a in (t.get('alternative_name_c') or '').split(',')]
    carriers = [t for t in data if carries(t)]
    carriers_accepted = [t for t in carriers if t.get('taxon_status') == 'accepted']
    if len(carriers_accepted) == 1:
        return carriers_accepted[0]
    if not carriers_accepted and len(carriers) == 1:
        return carriers[0]
    return None


def lookup(name, session):
    """Query the TaiCOL API for one common name. Returns the matched record or
    None. Raises on transport errors so the caller can retry."""
    resp = session.get(API_URL, params={'common_name': name}, timeout=20)
    resp.raise_for_status()
    payload = resp.json()
    return match_taxon(name, payload.get('data') or [])


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-o', '--output', help='Output CSV path (default: stdout)')
    parser.add_argument('--delay', type=float, default=0.2,
                        help='Seconds to sleep between API calls (default 0.2)')
    args = parser.parse_args()

    rows = list(Species.objects.values('id', 'name').order_by('id'))

    session = requests.Session()
    cache = {}   # name -> matched record or None (dedupe repeated names)

    out_fh = open(args.output, 'w', newline='', encoding='utf-8') if args.output else sys.stdout
    writer = csv.DictWriter(out_fh, fieldnames=OUTPUT_COLUMNS)
    writer.writeheader()

    n_ok = n_ignored = n_nomatch = 0
    for r in rows:
        name = r['name']
        if is_ignored(name):
            writer.writerow({'id': r['id'], 'name': name, 'taicol_taxon_id': '',
                             'is_valid': 'F', 'scientific_name': '',
                             'taxon_status': '', 'note': 'ignored'})
            n_ignored += 1
            continue

        if name not in cache:
            for attempt in range(3):
                try:
                    cache[name] = lookup(name, session)
                    break
                except Exception as exc:  # transient network/HTTP error
                    if attempt == 2:
                        print(f'  ! lookup failed for {name!r}: {exc}', file=sys.stderr)
                        cache[name] = None
                    else:
                        time.sleep(1.0)
            time.sleep(args.delay)

        rec = cache[name]
        if rec is None:
            writer.writerow({'id': r['id'], 'name': name, 'taicol_taxon_id': '',
                             'is_valid': 'F', 'scientific_name': '',
                             'taxon_status': '', 'note': 'no-match'})
            n_nomatch += 1
        else:
            valid = 'T' if rec.get('taxon_status') == 'accepted' else 'F'
            writer.writerow({
                'id': r['id'], 'name': name,
                'taicol_taxon_id': rec.get('taxon_id') or '',
                'is_valid': valid,
                'scientific_name': rec.get('simple_name') or '',
                'taxon_status': rec.get('taxon_status') or '',
                'note': 'ok',
            })
            n_ok += 1

    if args.output:
        out_fh.close()
    print(f'rows: {len(rows)}  matched: {n_ok}  ignored: {n_ignored}  no-match: {n_nomatch}',
          file=sys.stderr)


if __name__ == '__main__':
    main()
