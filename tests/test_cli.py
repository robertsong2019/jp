"""
jp CLI 测试套件

契约（README + jq 语义）：
- 默认输出 = JSON 编码（字符串带引号）
- -r/--raw = 字符串裸输出
- -j/--json-output = 总是有效 JSON（缩进、多结果包成数组）
"""

import json
import pytest

from jp.cli import main, format_output


@pytest.fixture
def infile(tmp_path):
    """写一个 JSON 文件供 -i 使用"""
    p = tmp_path / "data.json"
    p.write_text('{"name": "Alice", "age": 30, "items": [1, 2, 3], "users": [{"name": "A"}, {"name": "B"}]}',
                 encoding="utf-8")
    return str(p)


def run_cli(capsys, infile, *args):
    """跑一次 main() 并返回 (exitcode, stdout)"""
    try:
        main(["-i", infile, *args])
        code = 0
    except SystemExit as e:
        code = e.code
    out = capsys.readouterr().out
    return code, out


class TestFormatOutput:
    """format_output 单元契约"""

    def test_string_default_is_json_quoted(self):
        assert format_output("Alice") == '"Alice"'

    def test_string_raw_is_bare(self):
        assert format_output("Alice", raw=True) == "Alice"

    def test_int_same_both_ways(self):
        assert format_output(30) == "30"
        assert format_output(30, raw=True) == "30"

    def test_container_json_encoded(self):
        assert format_output({"a": 1}, raw=True) == '{"a": 1}'


class TestCliOutput:
    def test_default_string_output_quoted(self, capsys, infile):
        """RED-first: 默认输出字符串带引号（jq 语义；修复前 -r 是 no-op）"""
        code, out = run_cli(capsys, infile, ".name")
        assert code == 0
        assert out.strip() == '"Alice"'

    def test_raw_string_output_bare(self, capsys, infile):
        code, out = run_cli(capsys, infile, ".name", "-r")
        assert code == 0
        assert out.strip() == "Alice"

    def test_raw_makes_difference(self, capsys, infile):
        """-r 与默认输出必须不同（修复前 flag 无效）"""
        _, out_default = run_cli(capsys, infile, ".name")
        _, out_raw = run_cli(capsys, infile, ".name", "-r")
        assert out_default != out_raw

    def test_json_output_pretty(self, capsys, infile):
        code, out = run_cli(capsys, infile, ".items", "-j")
        assert code == 0
        assert json.loads(out) == [1, 2, 3]

    def test_multi_results_default_one_per_line(self, capsys, infile):
        code, out = run_cli(capsys, infile, ".users[*].name")
        assert code == 0
        assert out.splitlines() == ['"A"', '"B"']

    def test_multi_results_raw_bare(self, capsys, infile):
        code, out = run_cli(capsys, infile, ".users[*].name", "-r")
        assert out.splitlines() == ["A", "B"]

    def test_multi_results_json_wraps_array(self, capsys, infile):
        code, out = run_cli(capsys, infile, ".users[*].name", "-j")
        assert json.loads(out) == ["A", "B"]

    def test_nonstring_raw_untouched(self, capsys, infile):
        code, out = run_cli(capsys, infile, ".age", "-r")
        assert out.strip() == "30"


class TestCliErrors:
    def test_invalid_json_exits_1(self, capsys, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{not json", encoding="utf-8")
        with pytest.raises(SystemExit) as e:
            main(["-i", str(p), ".name"])
        assert e.value.code == 1
        err = capsys.readouterr().err
        assert "Error" in err

    def test_missing_field_exits_1(self, capsys, infile):
        """查询错误（非扇出）→ exit 1 + stderr"""
        with pytest.raises(SystemExit) as e:
            main(["-i", infile, ".nonexistent"])
        assert e.value.code == 1

    def test_empty_wildcard_result_exits_0_silent(self, capsys, tmp_path):
        p = tmp_path / "empty.json"
        p.write_text('{"items": []}', encoding="utf-8")
        code, out = run_cli(capsys, str(p), ".items[*]")
        assert code == 0
        assert out == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
