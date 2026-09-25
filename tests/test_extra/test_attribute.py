"""Test attribute selectors."""
from .. import util
import os
import subprocess
import sys
import textwrap
import soupsieve as sv


class TestAttribute(util.TestCase):
    """Test attribute selectors."""

    MARKUP = """
    <div id="div">
    <p id="0">Some text <span id="1"> in a paragraph</span>.</p>
    <a id="2" href="http://google.com">Link</a>
    <span id="3">Direct child</span>
    <pre id="pre">
    <span id="4">Child 1</span>
    <span id="5">Child 2</span>
    <span id="6">Child 3</span>
    </pre>
    </div>
    """

    def test_attribute_not_equal_no_quotes(self):
        """Test attribute with value that does not equal specified value (no quotes)."""

        # No quotes
        self.assert_selector(
            self.MARKUP,
            'body [id!=\\35]',
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    def test_attribute_not_equal_quotes(self):
        """Test attribute with value that does not equal specified value (quotes)."""

        # Quotes
        self.assert_selector(
            self.MARKUP,
            "body [id!='5']",
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    def test_attribute_not_equal_double_quotes(self):
        """Test attribute with value that does not equal specified value (double quotes)."""

        # Double quotes
        self.assert_selector(
            self.MARKUP,
            'body [id!="5"]',
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    def assert_syntax_error_no_timeout(self, selectors):
        """Assert that the selectors fail with a syntax error and do not hang."""

        # Compile the selectors in a separate process so that catastrophic backtracking
        # can be aborted with a timeout on every platform (`signal.SIGALRM` is not
        # available on Windows).
        code = textwrap.dedent(
            """
            import soupsieve as sv

            for selector in {selectors!r}:
                try:
                    sv.compile(selector)
                except sv.SelectorSyntaxError:
                    pass
                else:
                    raise SystemExit('SelectorSyntaxError not raised for ' + repr(selector))
            """
        ).format(selectors=selectors)

        # Make sure the child process imports the same `soupsieve` as the one under test.
        cwd = os.path.dirname(os.path.dirname(os.path.abspath(sv.__file__)))

        passed = False
        try:
            result = subprocess.run(
                [sys.executable, '-c', code],
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )
            passed = True
        except subprocess.TimeoutExpired:
            pass
        self.assertTrue(passed, 'Compiling the selectors timed out')
        self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8', 'replace'))

        # Now that they are known not to hang, verify the error in process as well.
        for selector in selectors:
            with self.assertRaises(sv.SelectorSyntaxError):
                sv.compile(selector)

    def test_bad_attribute_unclused(self):
        """Test bad attribute fails for syntax error, not timeout error."""

        self.assert_syntax_error_no_timeout(
            [
                '[a="' + ('x' * 300),
                "[a='" + ('x' * 300)
            ]
        )

    def test_bad_value_unclosed_pseudo_class(self):
        """Test unclosed values in pseudo classes fail for syntax error, not timeout error."""

        # Pseudo classes that accept values share the same value pattern as attributes.
        self.assert_syntax_error_no_timeout(
            [
                ':-soup-contains("' + ('x' * 300),
                ":-soup-contains('" + ('x' * 300),
                ':lang("' + ('x' * 300),
                ":lang('" + ('x' * 300)
            ]
        )
