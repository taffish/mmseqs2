#!/usr/bin/python3
"""Small, offline, synthetic packaging checks. No production reference data."""
import argparse
import bz2
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

COMMIT = 'ae60ef6964f3de689139bcfe290d9fad18f70b06'
SEQ = 'MKTAYIAKQRQISFVKSHFSRQDILDLWIYHTQGYFPQWDAARVGHVTKAVNQLRDRSLSAEVKAAALEHHHHHH'
EXE = os.environ.get('MMSEQS_BINARY', 'mmseqs')
counter = 0

def run(*args, expected=0):
    global counter
    argv = [EXE, *args]
    result = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=120)
    Path(f'command-{counter:03}.log').write_text('ARGV: ' + repr(argv) + '\n' + result.stdout)
    counter += 1
    assert result.returncode == expected, (argv, result.returncode, result.stdout[-5000:])
    return result.stdout

def input_files():
    Path('query.fa').write_text('>query\n' + SEQ + '\n')
    Path('target.fa').write_text('>target\n' + SEQ + '\n>duplicate\n' + SEQ + '\n')

def meta():
    assert run('version').strip() == COMMIT
    for command in ('easy-search', 'createdb', 'databases', 'easy-taxonomy', 'fwbw', 'pairaln', 'taxonomyreport', 'createdmptaxonomy', 'easy-proteomecluster', 'easy-proteomesearch', 'convertblastdb'):
        result = subprocess.run([EXE, command, '-h'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        assert 'usage: mmseqs ' + command in result.stdout, (command, result.returncode)
    for exe in Path('/opt/mmseqs2/bin').glob('mmseqs_*'):
        assert exe.is_file() and os.access(exe, os.X_OK)
    assert Path('/opt/mmseqs2/userguide.pdf').is_file()

def database():
    input_files()
    for suffix, compressor in (('gz', gzip.compress), ('bz2', bz2.compress)):
        Path('target.fa.' + suffix).write_bytes(compressor(Path('target.fa').read_bytes()))
        run('createdb', 'target.fa.' + suffix, 'db-' + suffix, '--threads', '1', '--shuffle', '0')
        run('convert2fasta', 'db-' + suffix, 'back-' + suffix + '.fa')
        assert Path('back-' + suffix + '.fa').read_text() == Path('target.fa').read_text()

def search():
    input_files()
    run('easy-search', 'query.fa', 'target.fa', 'hits.tsv', 'tmp-easy', '--threads', '1', '--prefilter-mode', '1')
    rows = [s.split('\t') for s in Path('hits.tsv').read_text().splitlines()]
    assert {r[1] for r in rows} == {'target', 'duplicate'} and all(r[0] == 'query' and int(r[3]) == len(SEQ) for r in rows)
    run('createdb', 'query.fa', 'qdb', '--shuffle', '0')
    run('createdb', 'target.fa', 'tdb', '--shuffle', '0')
    run('search', 'qdb', 'tdb', 'resultdb', 'tmp-search', '--threads', '1', '--prefilter-mode', '1', '-a')
    run('convertalis', 'qdb', 'tdb', 'resultdb', 'db-hits.tsv')
    assert Path('db-hits.tsv').read_bytes() == Path('hits.tsv').read_bytes()
    run('createtsv', 'qdb', 'tdb', 'resultdb', 'db.tsv')
    assert Path('db.tsv').stat().st_size > 0
    run('easy-rbh', 'query.fa', 'target.fa', 'rbh.tsv', 'tmp-rbh', '--threads', '1', '--prefilter-mode', '1')
    assert Path('rbh.tsv').stat().st_size > 0

def paired_msa():
    # Synthetic alignment rows isolate the missing-partner contract; the real
    # pairaln command must create the dummy before result2msa exports it.
    Path('query.fa').write_text(''.join(f'>chain{i}\n{SEQ}\n' for i in range(3)))
    Path('target.fa').write_text(''.join(f'>target{i}\n{SEQ}\n' for i in range(3)))
    for source, db in [('query.fa', 'qdb'), ('target.fa', 'tdb')]:
        run('createdb', source, db, '--dbtype', '1', '--shuffle', '0')
    Path('tax').mkdir()
    Path('tax/nodes.dmp').write_text('1\t|\t1\t|\tno rank\t|\n3\t|\t1\t|\tspecies\t|\n4\t|\t1\t|\tspecies\t|\n')
    Path('tax/names.dmp').write_text('1\t|\troot\t|\t\t|\tscientific name\t|\n3\t|\tFixture A\t|\t\t|\tscientific name\t|\n4\t|\tFixture B\t|\t\t|\tscientific name\t|\n')
    for name in ('merged.dmp', 'delnodes.dmp'):
        Path('tax/' + name).write_text('')
    Path('mapping.tsv').write_text('target0\t3\ntarget1\t3\ntarget2\t4\n')
    run('createtaxdb', 'tdb', 'tmp-tax', '--ncbi-tax-dump', 'tax', '--tax-mapping-file', 'mapping.tsv', '--threads', '1')
    length = len(SEQ)
    Path('alignments.tsv').write_text(''.join(
        f'{i}\t{i}\t100\t1.000\t0.0\t0\t{length-1}\t{length}\t0\t{length-1}\t{length}\t{length}M\n'
        for i in range(3)))
    run('tsv2db', 'alignments.tsv', 'alignments', '--output-dbtype', '5')
    run('pairaln', 'qdb', 'tdb', 'alignments', 'paired', '--pairing-mode', '0', '--pairing-dummy-mode', '1', '--threads', '1')
    assert b'\t-1\t0\t0\t-1\t0\t0\t1M\n' in Path('paired').read_bytes()
    run('result2msa', 'qdb', 'tdb', 'paired', 'paired.a3m', '--msa-format-mode', '5', '--filter-msa', '0', '--threads', '1')
    records = Path('paired.a3m').read_bytes().replace(b'\x00', b'').decode()
    assert records.count('>DUMMY\n' + '-' * length + '\n') == 1, records
    assert '>target0\n' + SEQ in records and '>target1\n' + SEQ in records
    assert '>target2\n' not in records

def clustering():
    input_files()
    for name, args in [('lin2', []), ('lin1', ['--linclust-version', '1'])]:
        run('easy-linclust', 'target.fa', name, 'tmp-' + name, '--threads', '1', *args)
        rows = [s.split('\t') for s in Path(name + '_cluster.tsv').read_text().splitlines()]
        assert {r[1] for r in rows} == {'target', 'duplicate'} and len({r[0] for r in rows}) == 1
    run('easy-cluster', 'target.fa', 'cluster', 'tmp-cluster', '--threads', '1', '--min-seq-id', '0.9', '-s', '1')
    assert Path('cluster_cluster.tsv').stat().st_size > 0
    run('createdb', 'target.fa', 'targetdb')
    run('cluster', 'targetdb', 'cluster2db', 'tmp-cluster2', '--cluster-version', '2', '--threads', '1', '--min-seq-id', '0.9', '-s', '1')
    run('createtsv', 'targetdb', 'targetdb', 'cluster2db', 'cluster2.tsv')
    assert Path('cluster2.tsv').stat().st_size > 0

def html():
    label = 'name"\\</script><script>window.TAF_PROBE=1</script>&中文'
    Path('query.fa').write_text('>' + label + '\n' + SEQ + '\n')
    Path('target.fa').write_text('>target' + label + '\n' + SEQ + '\n')
    run('easy-search', 'query.fa', 'target.fa', 'literal labels.html', 'tmp-html', '--threads', '1', '--prefilter-mode', '1', '--format-mode', '3')
    report = Path('literal labels.html').read_text()
    payload = report.split('<script>render(', 1)[1].rsplit(');</script>', 1)[0]
    assert '<' not in payload and '\\u003c/script\\u003e' in payload
    records = json.loads(re.sub(r',\s*([\]}])', r'\1', payload))
    assert records[0]['query']['accession'] == label
    assert records[0]['alignments'][0]['target'] == 'target' + label
    assert records[0]['alignments'][0]['alnLen'] == len(SEQ)
    input_files()
    run('easy-search', 'query.fa', 'target.fa', 'report.html', 'tmp-normal', '--threads', '1', '--prefilter-mode', '1', '--format-mode', '3')
    assert '<script>render(' in Path('report.html').read_text()

def proteomes():
    input_files()
    run('easy-proteomecluster', 'query.fa', 'target.fa', 'proteomes', 'tmp-proteomes', '--threads', '1', '--cluster-module', '0')
    assert Path('proteomes_protein_cluster.tsv').stat().st_size > 0
    assert Path('proteomes_cluster_count.tsv').stat().st_size > 0
    run('easy-proteomesearch', 'query.fa', 'target.fa', 'proteome-search', 'tmp-proteome-search', '--threads', '1', '--prefilter-mode', '1')
    assert Path('proteome-search_search.m8').stat().st_size > 0
    assert Path('proteome-search_score.tsv').stat().st_size > 0

def taxonomy():
    input_files()
    run('createdb', 'target.fa', 'tdb', '--shuffle', '0')
    Path('tax').mkdir()
    Path('tax/nodes.dmp').write_text('1\t|\t1\t|\tno rank\t|\n2\t|\t1\t|\tsuperkingdom\t|\n3\t|\t2\t|\tspecies\t|\n')
    Path('tax/names.dmp').write_text('1\t|\troot\t|\t\t|\tscientific name\t|\n2\t|\tBacteria\t|\t\t|\tscientific name\t|\n3\t|\tSynthetic species\t|\t\t|\tscientific name\t|\n')
    for name in ('merged.dmp', 'delnodes.dmp'):
        Path('tax/' + name).write_text('')
    Path('mapping.tsv').write_text('target\t3\nduplicate\t3\n')
    run('createtaxdb', 'tdb', 'tmp-tax', '--ncbi-tax-dump', 'tax', '--tax-mapping-file', 'mapping.tsv', '--threads', '1')
    run('easy-taxonomy', 'query.fa', 'tdb', 'tax-result', 'tmp-tax-result', '--threads', '1', '--prefilter-mode', '1', '--report-mode', '1')
    assert 'Synthetic species' in Path('tax-result_lca.tsv').read_text()
    report = Path('tax-result_report').read_bytes()
    assert b'<krona' in report
    Path('tax-result_report.html').write_bytes(report)

def resources():
    Path('source').mkdir(); Path('db').mkdir(mode=0o755)
    Path('source/seq.fa').write_text('>synthetic\n' + SEQ + '\n')
    value = Path('source/seq.fa').read_bytes()
    recipe = dict(schema='taffish.mmseqs2.recipe.v1', id='synthetic', version='1', source='Synthetic packaging fixture; not research data',
                  license='CC0 synthetic test fixture', files=[dict(name='seq.fa', url='https://example.invalid/seq.fa', size=len(value), sha256=hashlib.sha256(value).hexdigest())], createdb=dict(input='seq.fa', dbtype=1))
    Path('recipe.json').write_text(json.dumps(recipe))
    cmd = ['mmseqs2-db', 'install', '--recipe', 'recipe.json', '--db-root', str(Path('db').resolve()), '--source-dir', 'source', '--reserve-gb', '0', '--rights-reviewed']
    for _ in range(2):
        subprocess.run(cmd, check=True)
    subprocess.run(['mmseqs2-db', 'list', '--db-root', str(Path('db').resolve())], check=True)
    assert Path('db/synthetic--1/reference').stat().st_size > 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('case', choices=['meta', 'database', 'search', 'paired_msa', 'clustering', 'proteomes', 'html', 'taxonomy', 'resources'])
    parser.add_argument('--work', type=Path)
    args = parser.parse_args()
    work = args.work.resolve() if args.work else Path(tempfile.mkdtemp(prefix='mmseqs-check-', dir='/tmp'))
    work.mkdir(parents=True, exist_ok=True)
    os.chdir(work)
    print('WORK', work, flush=True)
    globals()[args.case]()
    print('PASS', args.case, flush=True)
