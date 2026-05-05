from click.utils import KeepOpenFile


def test_keepopenfile_iter(tmpdir):
    expected = list(map(str, range(10)))
    p = tmpdir.mkdir("testdir").join("testfile")
    p.write("\n".join(expected))
    with p.open() as f:
        for e_line, a_line in zip(expected, KeepOpenFile(f), strict=False):
            assert e_line == a_line.strip()
