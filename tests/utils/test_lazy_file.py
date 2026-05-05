from click.utils import LazyFile


def test_lazyfile_iter(tmpdir):
    expected = list(map(str, range(10)))
    p = tmpdir.mkdir("testdir").join("testfile")
    p.write("\n".join(expected))
    with p.open() as f:
        with LazyFile(f.name) as lf:
            for e_line, a_line in zip(expected, lf, strict=False):
                assert e_line == a_line.strip()
