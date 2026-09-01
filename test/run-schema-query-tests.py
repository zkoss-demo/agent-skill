#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["lxml"]
# ///
"""
Contract checks for the pre-write schema lookup and the two source-only checks
added to skills/zul-writer/scripts/validate-zul.py.

Three things are being pinned, and each of them can fail silently:

  --describe   Answers a question BEFORE the markup is written. The failure that
               matters is not "it printed nothing" but "it printed a confident
               wrong answer" -- a component absent from the bundled 10.x schema
               is removed-in-10 for one target and perfectly valid for another,
               and saying "not a ZUL component" for the second would teach the
               agent to avoid something legal.

  Layer 6      A literal selectedIndex pointing past the items that exist. Every
               check here comes in pairs: the defect must fire AND the legal
               neighbour must stay quiet, because a rule that reports both is
               reading markup while claiming to measure.

  Layer 7      @Wire cross-check. Same pairing, plus the families it declines to
               judge -- a false accusation costs more than a missed defect.

Also pinned: the default output shape. Layer 7 must not appear unless
--controller is passed, and a bare invocation must still be a usage error.

No browser, no network, no build. Run with:
    uv run test/run-schema-query-tests.py
"""

import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = REPO_ROOT / "skills" / "zul-writer" / "scripts" / "validate-zul.py"


def describe(*args):
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--describe", *args],
        capture_output=True, text=True, timeout=120,
        env={**__import__("os").environ, "DO_NOT_TRACK": "1"})
    return result.stdout + result.stderr, result.returncode


def validate(zul_text, extra_args=(), controller_text=None):
    """Validate `zul_text` in a temp dir, optionally with a controller."""
    import os
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        page = root / "page.zul"
        page.write_text(zul_text, encoding="utf-8")
        args = [sys.executable, str(VALIDATOR), str(page), *extra_args]
        if controller_text is not None:
            controller = root / "Ctrl.java"
            controller.write_text(controller_text, encoding="utf-8")
            args += ["--controller", str(controller)]
        result = subprocess.run(args, capture_output=True, text=True, timeout=120,
                                env={**os.environ, "DO_NOT_TRACK": "1"})
    return result.stdout + result.stderr, result.returncode


# --- --describe -----------------------------------------------------------

def check_the_charts_sclass_case():
    """The exact question that cost a round: <charts> takes className/zclass and
    not sclass. The answer has to name the alternatives, or it only says 'no'."""
    out, code = describe("charts", "--attr", "sclass")
    assert "available" in out, out
    assert "sclass: NOT accepted" in out, out
    assert "zclass" in out or "className" in out, out
    assert code == 1, code


def check_a_component_that_does_not_exist():
    out, code = describe("togglebutton")
    assert "NOT FOUND" in out, out
    assert "toolbarbutton" in out, out          # the near-miss is the useful half
    assert code == 1, code


def check_absence_is_not_reported_as_removal():
    """<fragment> is missing from the bundled 10.x schema for two opposite
    reasons depending on the target. Conflating them is the one wrong answer
    this mode must never give."""
    out9, code9 = describe("fragment", "--zk-version", "9")
    assert "removed in ZK 10" in out9, out9
    assert "NOT FOUND" not in out9, out9
    assert code9 == 0, code9

    out10, code10 = describe("fragment", "--zk-version", "10")
    assert "REMOVED" in out10, out10
    assert code10 == 1, code10


def check_an_accepted_attribute_answers_yes():
    out, code = describe("combobox", "--attr", "model", "--attr", "selectedItem")
    assert "model: accepted" in out, out
    assert "selectedItem: accepted" in out, out
    assert code == 0, code


def check_a_bare_component_lists_its_attributes():
    out, code = describe("label")
    assert "Accepts" in out and "attributes" in out, out
    assert "value" in out, out
    assert code == 0, code


def check_no_arguments_is_still_a_usage_error():
    """--describe made the file argument optional; 'no arguments at all' must
    keep failing the way it always has."""
    import os
    result = subprocess.run([sys.executable, str(VALIDATOR)],
                            capture_output=True, text=True, timeout=60,
                            env={**os.environ, "DO_NOT_TRACK": "1"})
    assert result.returncode == 2, result.returncode
    assert "required" in (result.stdout + result.stderr).lower(), result.stderr


# --- Layer 6: runtime semantics -------------------------------------------

EMPTY_COMBOBOX = '<zk>\n  <combobox selectedIndex="0"/>\n</zk>\n'
COMBOBOX_WITH_ITEM = ('<zk>\n  <combobox selectedIndex="0">\n'
                      '    <comboitem label="One"/>\n  </combobox>\n</zk>\n')
COMBOBOX_WITH_MODEL = '<zk>\n  <combobox selectedIndex="0" model="@load(vm.items)"/>\n</zk>\n'
COMBOBOX_BOUND_INDEX = '<zk>\n  <combobox selectedIndex="@load(vm.idx)"/>\n</zk>\n'
COMBOBOX_NO_SELECTION = '<zk>\n  <combobox selectedIndex="-1"/>\n</zk>\n'
LISTBOX_INDEX_PAST_END = ('<zk>\n  <listbox selectedIndex="3">\n'
                          '    <listitem label="a"/>\n    <listitem label="b"/>\n'
                          '  </listbox>\n</zk>\n')
SELECTBOX_NO_MODEL = '<zk>\n  <selectbox selectedIndex="0"/>\n</zk>\n'


def check_the_out_of_bound_case_fires():
    out, code = validate(EMPTY_COMBOBOX)
    assert "Layer 6: Runtime Semantics... ✗ FAIL" in out, out
    assert "will throw at render time" in out, out
    assert code == 1, code


def check_one_literal_item_makes_index_zero_legal():
    out, code = validate(COMBOBOX_WITH_ITEM)
    assert "Layer 6: Runtime Semantics... ✓ PASS" in out, out
    assert code == 0, code


def check_a_model_silences_the_rule():
    """The model's size is not knowable from markup. Under-reporting is the safe
    direction for a list the agent is told to trust."""
    out, code = validate(COMBOBOX_WITH_MODEL)
    assert "Layer 6: Runtime Semantics... ✓ PASS" in out, out


def check_a_bound_index_is_not_judged():
    out, _ = validate(COMBOBOX_BOUND_INDEX)
    assert "Layer 6: Runtime Semantics... ✓ PASS" in out, out


def check_minus_one_is_always_legal():
    out, _ = validate(COMBOBOX_NO_SELECTION)
    assert "Layer 6: Runtime Semantics... ✓ PASS" in out, out


def check_an_index_past_the_last_item_fires():
    out, code = validate(LISTBOX_INDEX_PAST_END)
    assert "Layer 6: Runtime Semantics... ✗ FAIL" in out, out
    assert "valid: 0-1" in out, out
    assert code == 1, code


def check_a_model_only_component_says_so():
    """<selectbox> has no literal item form at all, so the advice is 'add a
    model', not 'add items'."""
    out, code = validate(SELECTBOX_NO_MODEL)
    assert "Layer 6: Runtime Semantics... ✗ FAIL" in out, out
    assert "needs a model" in out, out


# --- Layer 7: controller cross-check --------------------------------------

WIRED_PAGE = '<zk>\n  <window apply="Ctrl">\n    <a id="detail" label="Detail"/>\n  </window>\n</zk>\n'
WIRED_LISTBOX = ('<zk>\n  <window apply="Ctrl">\n    <hbox id="row"/>\n'
                 '    <textbox id="query"/>\n  </window>\n</zk>\n')
INCLUDING_PAGE = ('<zk>\n  <window apply="Ctrl">\n    <include src="/part.zul"/>\n'
                  '  </window>\n</zk>\n')


def ctrl(body):
    return "package demo;\nimport org.zkoss.zk.ui.select.annotation.Wire;\n" \
           "public class Ctrl {\n" + body + "\n}\n"


def check_layer_7_is_absent_without_the_flag():
    """The default output shape is a contract. Layer 7 must be invisible unless
    a controller is named."""
    out, code = validate(WIRED_PAGE)
    assert "Layer 7" not in out, out
    assert "Layer 6" in out, out
    assert code == 0, code


def check_a_wrong_field_type_is_flagged():
    """The observed defect: @Wire Label on an <a>. Compiles, validates, renders,
    then throws ClassCastException at first use."""
    out, code = validate(WIRED_PAGE, controller_text=ctrl("  @Wire\n  Label detail;"))
    assert "Layer 7: Controller Cross-Check... ✗ FAIL" in out, out
    assert "ClassCastException" in out, out
    assert "Change the field type to A." in out, out
    assert code == 1, code


def check_the_right_field_type_passes():
    out, code = validate(WIRED_PAGE, controller_text=ctrl("  @Wire\n  A detail;"))
    assert "Layer 7: Controller Cross-Check... ✓ PASS" in out, out
    assert code == 0, code


def check_a_base_class_field_is_not_flagged():
    """@Wire Component is legal for any component, and Component is not an
    element name, so the rule must never reach it."""
    out, code = validate(WIRED_PAGE, controller_text=ctrl("  @Wire\n  Component detail;"))
    assert "Layer 7: Controller Cross-Check... ✓ PASS" in out, out


def check_an_ambiguous_family_is_declined():
    """Hbox extends Box and Combobox extends Textbox. Without a real class
    hierarchy the rule cannot tell a legal ancestor from a wrong type, so it
    declines to judge these families at all."""
    out, code = validate(WIRED_LISTBOX,
                         controller_text=ctrl("  @Wire\n  Box row;\n  @Wire\n  Textbox query;"))
    assert "Layer 7: Controller Cross-Check... ✓ PASS" in out, out


def check_a_wired_id_that_does_not_exist_is_flagged():
    out, code = validate(WIRED_PAGE, controller_text=ctrl("  @Wire\n  A missing;"))
    assert "Layer 7: Controller Cross-Check... ✗ FAIL" in out, out
    assert "NullPointerException" in out, out
    assert code == 1, code


def check_an_include_silences_the_missing_id_rule():
    """An <include> can contribute ids this file never shows, so absence proves
    nothing."""
    out, code = validate(INCLUDING_PAGE, controller_text=ctrl("  @Wire\n  A elsewhere;"))
    assert "Layer 7: Controller Cross-Check... ✓ PASS" in out, out


def check_a_commented_out_wire_is_not_read_as_real():
    out, code = validate(WIRED_PAGE,
                         controller_text=ctrl("  // @Wire\n  // Label detail;\n  @Wire\n  A detail;"))
    assert "Layer 7: Controller Cross-Check... ✓ PASS" in out, out


def check_the_reported_line_is_the_real_line():
    """Comments are blanked, not deleted. Deleting them shifted every line number
    after the first comment, and a wrong location is worse than no location."""
    body = ("  /* a license header\n     spanning several lines\n     of prose */\n"
            "  // and a trailing note\n"
            "  @Wire\n  Label detail;")
    out, _ = validate(WIRED_PAGE, controller_text=ctrl(body))
    # ctrl() puts 3 lines before the body, so the field lands on line 9.
    assert "Line 9:" in out, out


def check_a_collection_field_is_skipped():
    out, code = validate(WIRED_PAGE,
                         controller_text=ctrl("  @Wire\n  List<Label> detail;\n  @Wire\n  A detail2;"))
    # detail2 has no id in the page, but the page has no <include>, so it is flagged;
    # what matters here is that the generic field produced no type complaint.
    assert "List" not in out, out


def check_an_id_selector_is_honoured():
    out, code = validate(WIRED_PAGE,
                         controller_text=ctrl('  @Wire("#detail")\n  Label renamed;'))
    assert "Layer 7: Controller Cross-Check... ✗ FAIL" in out, out
    assert "ClassCastException" in out, out


def check_a_class_selector_is_declined():
    out, code = validate(WIRED_PAGE,
                         controller_text=ctrl('  @Wire(".some-class")\n  Label many;'))
    assert "Layer 7: Controller Cross-Check... ✓ PASS" in out, out


CHECKS = [
    ("describe: charts/sclass    ", check_the_charts_sclass_case),
    ("describe: unknown component", check_a_component_that_does_not_exist),
    ("describe: absent != removed", check_absence_is_not_reported_as_removal),
    ("describe: accepted attrs   ", check_an_accepted_attribute_answers_yes),
    ("describe: attribute listing", check_a_bare_component_lists_its_attributes),
    ("describe: no args = usage  ", check_no_arguments_is_still_a_usage_error),
    ("L6: out-of-bound fires     ", check_the_out_of_bound_case_fires),
    ("L6: one item is legal      ", check_one_literal_item_makes_index_zero_legal),
    ("L6: a model silences it    ", check_a_model_silences_the_rule),
    ("L6: bound index skipped    ", check_a_bound_index_is_not_judged),
    ("L6: -1 always legal        ", check_minus_one_is_always_legal),
    ("L6: past the last item     ", check_an_index_past_the_last_item_fires),
    ("L6: model-only component   ", check_a_model_only_component_says_so),
    ("L7: absent without flag    ", check_layer_7_is_absent_without_the_flag),
    ("L7: wrong type flagged     ", check_a_wrong_field_type_is_flagged),
    ("L7: right type passes      ", check_the_right_field_type_passes),
    ("L7: base class declined    ", check_a_base_class_field_is_not_flagged),
    ("L7: ambiguous family       ", check_an_ambiguous_family_is_declined),
    ("L7: missing id flagged     ", check_a_wired_id_that_does_not_exist_is_flagged),
    ("L7: include silences it    ", check_an_include_silences_the_missing_id_rule),
    ("L7: commented-out @Wire    ", check_a_commented_out_wire_is_not_read_as_real),
    ("L7: line number is real    ", check_the_reported_line_is_the_real_line),
    ("L7: collection field       ", check_a_collection_field_is_skipped),
    ("L7: #id selector honoured  ", check_an_id_selector_is_honoured),
    ("L7: .class selector declined", check_a_class_selector_is_declined),
]


def main():
    failed = 0
    for label, check in CHECKS:
        try:
            check()
            print(f"  ✓ {label}")
        except AssertionError as failure:
            failed += 1
            print(f"  ✗ {label} — {failure}")
    print(f"\n{len(CHECKS)} checks | {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
