#!/usr/bin/python3
"""Explicit immutable resource recipes; never intercept MMSEQS2 analysis."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import tempfile

from mmseqs2_validation import (canonical, directory, recipe_load, regular, require, safe_name,
                                sha, verify, verify_root)
from mmseqs2_transaction import SIGNALS, interrupted, owned_lock, private_directory, run_owned


def install_path(root):
    directory(root, writable=True)
    # Fresh offline smoke uses a private /tmp. Persistent writes need a real host mount.
    if Path('/tmp') in root.parents:
        return
    with open('/proc/self/mountinfo') as stream:
        for line in stream:
            field = line.split(' - ', 1)[0].split()[4]
            mount = Path(re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), field))
            if mount not in (Path('/'), Path('/proc'), Path('/sys'), Path('/dev')) and (mount == root or mount in root.parents):
                return
    raise ValueError('persistent installs need an actual writable host bind: ' + str(root))


def command(stage, argv, cwd=None):
    # A disk-backed bounded diagnostic tail avoids storing large progress logs in RAM.
    with tempfile.TemporaryFile() as log:
        code = run_owned(argv, cwd=cwd, stdout=log, stderr=subprocess.STDOUT)
        if code:
            log.seek(max(0, log.tell() - 32768))
            print(f'mmseqs2-db: stage={stage} exit={code}', file=sys.stderr)
            print('\n'.join(log.read().decode(errors='replace').splitlines()[-100:]), file=sys.stderr)
            raise SystemExit(code)


def obtain(item, cache, source_dir):
    blob = cache / item['sha256']
    partial = cache / (item['sha256'] + '.part')
    for path in (blob, partial):
        if os.path.lexists(path):
            regular(path)
            require(path.stat().st_uid == os.geteuid() and path.stat().st_nlink == 1, 'unexpected cache ownership/link: ' + str(path))
    if blob.exists():
        require(blob.stat().st_size == item['size'] and sha(blob) == item['sha256'], 'corrupt cache; inspect exact file: ' + str(blob))
        return blob, False
    if source_dir is not None:
        source = source_dir / item['name']
        regular(source)
        require(source.stat().st_size == item['size'] and sha(source) == item['sha256'],
                'source checksum/size mismatch; existing cache preserved: ' + str(source))
        with source.open('rb') as inp:
            if partial.exists():
                require(partial.stat().st_size <= item['size'], 'oversize offline partial; inspect: ' + str(partial))
                with partial.open('rb') as prior:
                    for block in iter(lambda: prior.read(1024**2), b''):
                        require(inp.read(len(block)) == block, 'offline partial prefix mismatch; retained: ' + str(partial))
            with partial.open('ab' if partial.exists() else 'xb') as out:
                shutil.copyfileobj(inp, out, 1024**2)
    else:
        require(not partial.exists() or partial.stat().st_size <= item['size'], 'oversize partial cache')
        if not partial.exists() or partial.stat().st_size < item['size']:
            command('download', ['curl', '--fail', '--location', '--proto', '=https', '--proto-redir', '=https',
                                '--connect-timeout', '30', '--speed-limit', '1024', '--speed-time', '120',
                                '--retry', '3', '--retry-delay', '3', '--continue-at', '-',
                                '--max-filesize', str(item['size']), '--output', str(partial), item['url']])
    regular(partial)
    require(partial.stat().st_size == item['size'] and sha(partial) == item['sha256'],
            'download checksum/size mismatch; private partial retained: ' + str(partial))
    partial.chmod(0o600)
    partial.rename(blob)
    return blob, True


def install(root, recipe, source_dir, reserve, threads):
    install_path(root)
    unit = recipe['id'] + '--' + recipe['version']
    identity = hashlib.sha256(canonical(recipe)).hexdigest()
    destination = root / unit
    lock = root / '.install.lock'
    if os.path.lexists(lock):
        raise ValueError('install lock exists; do not remove an active lock: ' + str(lock))
    with owned_lock(lock):
        members = verify_root(root, allow_empty=True)
        if unit in members:
            require(members[unit]['recipe_sha256'] == identity, 'existing ID has a different recipe; use a new version')
            print('already complete: ' + str(destination))
            return
        cache = root / '.downloads'
        if not cache.exists():
            cache.mkdir(mode=0o700)
        directory(cache, writable=True)
        require(stat.S_IMODE(cache.stat().st_mode) == 0o700, 'cache must have mode 0700')
        pending = {}
        for item in recipe['files']:
            if not (cache / item['sha256']).exists():
                pending[item['sha256']] = item['size']
        # Conservative preflight; extraction is checked again per member. The
        # explicit extra reserve covers user-estimated createdb/taxonomy workspace.
        required = sum(pending.values()) + sum(item['size'] for item in recipe['files']) + reserve
        require(shutil.disk_usage(root).free >= required, f'insufficient space: need {required} free bytes')
        blobs = [(item, obtain(item, cache, source_dir)) for item in recipe['files']]
        with private_directory(prefix='.' + unit + '.stage-', dir=root) as stage:
            for item, (blob, _) in blobs:
                shutil.copyfile(blob, stage / item['name'])
                if item.get('extract'):
                    with tarfile.open(blob, 'r:*') as archive:
                        for name in item['extract']:
                            matches = [m for m in archive.getmembers() if m.name == name]
                            require(len(matches) == 1 and matches[0].isfile(), 'missing/duplicate/non-regular taxonomy member')
                            require(shutil.disk_usage(stage).free >= matches[0].size + reserve, 'insufficient extraction space')
                            with archive.extractfile(matches[0]) as inp, (stage / name).open('xb') as out:
                                shutil.copyfileobj(inp, out, 8 * 1024**2)
            if 'createdb' in recipe:
                build = recipe['createdb']
                command('createdb', ['mmseqs', 'createdb', build['input'], 'reference',
                    '--threads', str(threads), '--dbtype', str(build.get('dbtype', 0)),
                    '--shuffle', '0', '--createdb-mode', '0', '--compressed', '0'], stage)
                require((stage / 'reference').stat().st_size > 0, 'createdb produced no database')
            for path in stage.iterdir():
                regular(path)
            (stage / 'recipe.json').write_bytes(canonical(recipe) + b'\n')
            (stage / 'RESOURCE_LICENSE.txt').write_text(recipe['source'] + '\n\n' + recipe['license'] + '\n')
            inventory = [dict(name=p.name, size=p.stat().st_size, sha256=sha(p)) for p in sorted(stage.iterdir())]
            record = dict(schema='taffish.mmseqs2.db.v1', app_release='19-r1', resource=unit,
                          recipe_sha256=identity, files=inventory)
            (stage / 'manifest.json').write_bytes(canonical(record) + b'\n')
            (stage / 'READY').write_text(sha(stage / 'manifest.json') + '\n')
            for path in stage.iterdir():
                path.chmod(0o644)
            stage.chmod(0o755)
            verify(stage, unit, identity)
            command('promote', ['mv', '-T', '-n', '--', str(stage), str(destination)])
            require(not stage.exists(), 'destination appeared; refusing overwrite')
        # Retire only blobs promoted by this transaction, never an older verified cache.
        for blob in {path for _, (path, created) in blobs if created}:
            regular(blob)
            require(blob.stat().st_nlink == 1 and sha(blob) == blob.name, 'cache identity changed; retained')
            blob.unlink()
        print('installed: ' + str(destination))


def main():
    parser = argparse.ArgumentParser(description='Prepare one fixed sequence/taxonomy recipe. No implicit downloads.',
        epilog='Use an existing installer-owned private/site root. Members: 0755/0644. No --force; '
        'quarantine exact damaged members only after confirming no installer is running. '
        'Repeat network installation to resume. Always use actual writable/read-only backend binds.')
    parser.add_argument('--version', action='version', version='mmseqs2-db 19-r1')
    sub = parser.add_subparsers(dest='command', required=True)
    prepare = sub.add_parser('install')
    prepare.add_argument('--recipe', required=True, type=Path)
    prepare.add_argument('--db-root', required=True, type=Path)
    prepare.add_argument('--source-dir', type=Path, help='already acquired recipe members, no network')
    prepare.add_argument('--allow-download', action='store_true', help='explicitly enable the recipe HTTPS downloads')
    prepare.add_argument('--rights-reviewed', action='store_true', required=True,
                         help='confirm acquisition and intended sharing rights for every recipe member')
    prepare.add_argument('--dry-run', action='store_true')
    prepare.add_argument('--reserve-gb', type=float, default=10, help='extra extraction/build reserve, default 10 GiB')
    prepare.add_argument('--threads', type=int, default=1)
    check = sub.add_parser('verify')
    check.add_argument('--db-root', required=True, type=Path)
    check.add_argument('--id', required=True, help='exact prepared member ID: recipe-id--version')
    listing = sub.add_parser('list', help='Verify the entire prepared root and list its members')
    listing.add_argument('--db-root', required=True, type=Path)
    args = parser.parse_args()
    require(args.db_root.is_absolute(), '--db-root must be absolute')
    if args.command in ('verify', 'list'):
        records = verify_root(args.db_root)
        if args.command == 'list':
            print(json.dumps(sorted(records)))
        else:
            unit = safe_name(args.id)
            require(unit in records, 'missing resource member: ' + unit)
            print(json.dumps(records[unit], indent=2))
        return
    require(0 <= args.reserve_gb < 1000000 and args.threads > 0, 'invalid reserve/threads')
    recipe = recipe_load(args.recipe)
    require(not (args.source_dir and args.allow_download), 'choose --source-dir or --allow-download, not both')
    if args.dry_run:
        print(json.dumps(dict(resource=recipe['id'] + '--' + recipe['version'], recipe=recipe,
            recipe_sha256=hashlib.sha256(canonical(recipe)).hexdigest(),
            download_bytes=sum(f['size'] for f in recipe['files']), reserve_bytes=int(args.reserve_gb * 1024**3),
            destination=str(args.db_root / (recipe['id'] + '--' + recipe['version'])),
            network=args.allow_download, local_source=str(args.source_dir) if args.source_dir else None,
            network_requires_opt_in=True), indent=2))
        return
    require(args.source_dir is not None or args.allow_download, 'missing local source: pass --source-dir or explicitly --allow-download')
    install(args.db_root, recipe, args.source_dir, int(args.reserve_gb * 1024**3), args.threads)


if __name__ == '__main__':
    os.umask(0o077)
    for sig in SIGNALS:
        signal.signal(sig, interrupted)
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, tarfile.TarError) as error:
        print('mmseqs2-db: stage=prepare-or-verify exit=1: ' + str(error), file=sys.stderr)
        sys.exit(1)
