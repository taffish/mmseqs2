"""Read-only MMSEQS2 recipe and full-library checks; usable on the host and in the image."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from urllib.parse import urlsplit

SCHEMA = 'taffish.mmseqs2.recipe.v1'
RESERVED = {'manifest.json', 'READY', 'recipe.json', 'RESOURCE_LICENSE.txt'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024**2), b''):
            h.update(block)
    return h.hexdigest()


def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(',', ':')).encode()


def safe_name(value):
    require(isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,100}', value)
            and '..' not in value, 'unsafe resource ID, version or filename')
    return value


def regular(path):
    require(not path.is_symlink() and stat.S_ISREG(path.lstat().st_mode), 'not a regular non-symlink file: ' + str(path))


def directory(path, writable=False):
    require(path.is_absolute() and path.is_dir() and not path.is_symlink() and path.resolve() == path,
            'root must be an existing absolute physical directory: ' + str(path))
    require(not path.stat().st_mode & 0o022, 'root must not be group/world writable')
    if writable:
        require(path.stat().st_uid == os.geteuid() and os.access(path, os.W_OK),
                'installer must own and be able to write root')


def recipe_load(path):
    regular(path)
    require(path.stat().st_size <= 1024**2, 'recipe exceeds 1 MiB')
    recipe = json.loads(path.read_text())
    require(isinstance(recipe, dict), 'recipe must be a JSON object')
    require(recipe.get('schema') == SCHEMA, 'unsupported recipe schema')
    require(set(recipe).issubset({'schema', 'id', 'version', 'source', 'license', 'files', 'createdb'}), 'unknown recipe field')
    safe_name(recipe['id']); safe_name(recipe['version'])
    safe_name(recipe['id'] + '--' + recipe['version'])
    require(recipe['id'].lower() != 'all', 'select one fixed resource, not all')
    for field in ('source', 'license'):
        require(isinstance(recipe.get(field), str) and recipe[field].strip()
                and len(recipe[field]) <= 1024**2, 'source and license/permission notice required')
    require(isinstance(recipe.get('files'), list) and recipe['files'], 'explicit files required')
    outputs = set()
    for item in recipe['files']:
        require(isinstance(item, dict), 'recipe file must be a JSON object')
        require(set(item).issubset({'name', 'url', 'sha256', 'size', 'extract'}), 'unknown recipe file field')
        filename = safe_name(item['name'])
        require(filename not in outputs | RESERVED, 'duplicate/reserved output filename')
        require('createdb' not in recipe or not filename.startswith('reference'), 'reference prefix reserved for createdb')
        url = urlsplit(item['url'])
        require(url.scheme == 'https' and url.hostname and not url.username and not url.password and not url.fragment,
                'public HTTPS URL without credentials or fragments required')
        require(isinstance(item.get('sha256'), str) and re.fullmatch('[0-9a-f]{64}', item['sha256']), 'SHA256 required')
        require(type(item.get('size')) is int and item['size'] > 0, 'positive exact file size required')
        outputs.add(filename)
        require(isinstance(item.get('extract', []), list), 'extract must be a list')
        for member in item.get('extract', []):
            require(member in ('nodes.dmp', 'names.dmp', 'merged.dmp', 'delnodes.dmp') and member not in outputs, 'invalid/duplicate taxonomy member')
            outputs.add(member)
    if 'createdb' in recipe:
        build = recipe['createdb']
        require(isinstance(build, dict) and set(build).issubset({'input', 'dbtype'}), 'unknown createdb field')
        require(build.get('input') in outputs, 'createdb input missing')
        require(type(build.get('dbtype', 0)) is int and build.get('dbtype', 0) in (0, 1, 2), 'invalid createdb dbtype')
    return recipe


def verify(member, unit, recipe_hash=None):
    directory(member)
    require(stat.S_IMODE(member.stat().st_mode) == 0o755, 'member directory permission drift')
    for name in ('manifest.json', 'READY'):
        regular(member / name)
        require(stat.S_IMODE((member / name).stat().st_mode) == 0o644, 'manifest/READY permission drift')
    require((member / 'READY').read_text().strip() == sha(member / 'manifest.json'), 'READY/manifest mismatch')
    record = json.loads((member / 'manifest.json').read_text())
    require(isinstance(record, dict), 'manifest must be a JSON object')
    require(record.get('schema') == 'taffish.mmseqs2.db.v1' and record.get('resource') == unit, 'member schema/ID mismatch')
    require(recipe_hash is None or record.get('recipe_sha256') == recipe_hash, 'existing ID has a different recipe; use a new version')
    expected = {'manifest.json', 'READY'}
    inventory = {}
    require(isinstance(record.get('files'), list) and record['files'], 'empty inventory')
    for item in record['files']:
        require(isinstance(item, dict), 'inventory entry must be a JSON object')
        name = safe_name(item['name'])
        require(name not in expected, 'duplicate inventory entry')
        path = member / name
        regular(path)
        require(stat.S_IMODE(path.stat().st_mode) == 0o644, 'member file permission drift: ' + name)
        require(path.stat().st_size == item['size'] and sha(path) == item['sha256'], 'checksum/size mismatch: ' + name)
        expected.add(name)
        inventory[name] = item
    require({'recipe.json', 'RESOURCE_LICENSE.txt'}.issubset(expected), 'recipe/license inventory missing')
    require({p.name for p in member.iterdir()} == expected, 'unexpected/missing member files')
    recipe = recipe_load(member / 'recipe.json')
    require(hashlib.sha256(canonical(recipe)).hexdigest() == record['recipe_sha256'], 'recipe identity mismatch')
    require(recipe['id'] + '--' + recipe['version'] == unit, 'recipe/member ID mismatch')
    names = {'recipe.json', 'RESOURCE_LICENSE.txt'}
    for f in recipe['files']:
        names.add(f['name'])
        names.update(f.get('extract', ()))
        require(f['name'] in inventory and (inventory[f['name']]['size'], inventory[f['name']]['sha256']) ==
                (f['size'], f['sha256']), 'source file differs from recipe: ' + f['name'])
    if 'createdb' in recipe:
        generated = {n for n in inventory if re.fullmatch(r'reference(?:[._][A-Za-z0-9_.-]+)?', n)}
        required = {'reference', 'reference.index', 'reference.dbtype', 'reference_h', 'reference_h.index', 'reference_h.dbtype', 'reference.lookup', 'reference.source'}
        require(required.issubset(generated), 'generated database inventory incomplete')
        require(all(inventory[n]['size'] > 0 for n in required), 'generated database empty')
        require((member / 'reference.dbtype').read_bytes() in (b'\x00\x00\x00\x00', b'\x01\x00\x00\x00'), 'unsupported sequence database type')
        names.update(generated)
    require(names == set(inventory), 'recipe/payload inventory mismatch')
    require((member / 'RESOURCE_LICENSE.txt').read_text() == recipe['source'] + '\n\n' + recipe['license'] + '\n',
            'resource license notice differs from recipe')
    return record


def verify_root(root, *, allow_empty=False):
    directory(root)
    records = {p.name: verify(p, safe_name(p.name)) for p in sorted(root.iterdir()) if not p.name.startswith('.')}
    require(records or allow_empty, 'no complete visible resources in ' + str(root))
    return records


if __name__ == '__main__':
    try:
        require(len(sys.argv) == 2, 'expected one prepared resource root')
        verify_root(Path(sys.argv[1]))
    except (ValueError, KeyError, TypeError, OSError) as error:
        sys.exit('mmseqs2 resource verification failed: ' + str(error))
