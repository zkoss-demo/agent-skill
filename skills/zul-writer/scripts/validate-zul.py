#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["lxml"]
# ///
"""
ZUL File Validator

Validates ZUL files for:
  Layer 1: XML well-formedness (no dependencies)
  Layer 2: XSD schema validation (requires lxml)
  Layer 3: Attribute placement check (requires lxml) - catches misplaced
           attributes that XSD's anyAttribute wildcard allows through
  Layer 4: Version compatibility checks for the target ZK version
           (removed/deprecated API; ZK-10-only API on ZK 9 targets)
  Layer 5: Inline style advisory (never fails) - static style="..." attributes
           that belong in a <style> class attached with sclass
  Layer 6: Runtime semantics - markup that is legal by every static measure and
           still throws while the page is being built (a literal selectedIndex
           pointing past the items that exist)
  Layer 7: Controller cross-check (only with --controller) - @Wire fields against
           the ZUL's ids: a wrong id leaves the field null, a wrong field type
           throws ClassCastException at first use

Also provides --describe, which queries the bundled schema instead of validating
a file: does this component exist at this ZK version, and does it accept this
attribute. Asking before writing costs nothing; finding out afterwards costs a
render round.

Recommended invocation is `uv run validate-zul.py ...`: uv reads the PEP 723
inline metadata above and provides `lxml` in an ephemeral environment, so no
manual dependency setup is needed. When run with a plain interpreter,
ensure_lxml() self-installs lxml as a fallback.

Note: ZK's official XSD may have issues. This script defaults to using the
revised local schema in ../assets/zul.xsd. Use --xsd to override it.
"""

import sys
import os
import json
import threading
import urllib.request
import argparse
import difflib
import re
import subprocess
import tempfile
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path


# --- Anonymous, aggregate usage tracking ---------------------------------
# Privacy by design: sends NO identifier of any kind — no visitor ID, no
# cookie, no per-install file. Each run is an independent, unlinkable event
# carrying only the skill name and version.
#
# Fired on a background daemon thread so a slow/unreachable network never
# delays ZUL validation. Opt out entirely by setting DO_NOT_TRACK=1 or
# TRACK_URL="" in the env, or per-run with --dev (see track_usage_async).

TRACK_URL = os.environ.get("TRACK_URL", "https://www.zkoss.org/api/track")
SKILL_VERSION = "2.0.0"


def _tracking_opted_out() -> bool:
    return os.environ.get("DO_NOT_TRACK") == "1" or not TRACK_URL


def _send_usage_event():
    payload = {
        "events": [{
            "name": "zul_writer",  # GA4 event names allow only [a-zA-Z0-9_]
            "params": {
                "skill_version": SKILL_VERSION
            }
        }]
    }

    headers = {
        "Content-Type": "application/json",
        "User-Agent": f"zul-writer-skill/{SKILL_VERSION}"
    }

    req = urllib.request.Request(
        TRACK_URL,
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=3):
            pass
    except Exception:
        pass


def track_usage_async(dev: bool = False):
    """Fire the anonymous usage ping on a background thread; returns immediately.

    `dev` is set by --dev, for runs made while developing or testing the skill
    itself. Those runs are not usage of the skill, and counting them would
    overstate how many people the aggregate numbers represent.
    """
    if dev:
        print("[dev] usage tracking disabled for this run")
        return
    if _tracking_opted_out():
        return
    threading.Thread(target=_send_usage_event, daemon=True).start()


def ensure_lxml() -> bool:
    """
    Ensure lxml is available, installing it automatically if needed.
    Prefers `uv pip install` (fast, isolated); falls back to `pip install`.

    Returns True if lxml is available after the attempt, False otherwise.
    """
    try:
        import lxml  # noqa: F401
        return True
    except ImportError:
        pass

    print("  [dependency] lxml not found — attempting auto-install...")

    # Prefer uv (user's preferred Python env manager)
    try:
        result = subprocess.run(
            ["uv", "pip", "install", "lxml"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("  [dependency] lxml installed via uv ✓")
            return True
        print(f"  [dependency] uv install failed: {result.stderr.strip()}")
    except FileNotFoundError:
        pass  # uv not found, try pip

    # Fallback: pip
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "lxml"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("  [dependency] lxml installed via pip ✓")
            return True
        print(f"  [dependency] pip install failed: {result.stderr.strip()}")
    except Exception as e:
        print(f"  [dependency] Could not install lxml: {e}")

    return False


# Ensure lxml is available before any validation layers that need it
_LXML_AVAILABLE = ensure_lxml()


# Default to the revised local schema file
DEFAULT_XSD_PATH = Path(__file__).parent.parent / "assets" / "zul.xsd"
ZK_XSD_URL = "http://www.zkoss.org/2005/zul/zul.xsd"
ZK_NS = "http://www.zkoss.org/2005/zul"


def inject_default_namespace(file_path: Path) -> Path | None:
    """
    ZK's default namespace (http://www.zkoss.org/2005/zul) is implicit —
    ZUL files don't need to declare it. For XSD/attribute validation,
    inject it into a temp copy if missing.

    Returns temp file path if injection was needed, None if already present.
    """
    with open(file_path, 'r') as f:
        content = f.read()

    if f'xmlns="{ZK_NS}"' in content:
        return None

    # Find the first real element tag, skipping tag-like text inside comments
    # (<!-- ... -->) and processing instructions (<?...?>). A naive search
    # matches names such as <tabpanel inside a leading explanatory comment and
    # injects the namespace there, leaving the real root un-namespaced.
    skip_spans = [
        (m.start(), m.end())
        for m in re.finditer(r'<!--.*?-->|<\?.*?\?>', content, re.DOTALL)
    ]

    match = None
    for m in re.finditer(r'<([a-zA-Z][\w.-]*)', content):
        if not any(start <= m.start() < end for start, end in skip_spans):
            match = m
            break
    if not match:
        return None

    modified = content[:match.end()] + f' xmlns="{ZK_NS}"' + content[match.end():]

    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.zul', delete=False)
    tmp.write(modified)
    tmp.close()
    return Path(tmp.name)


def wrap_fragment_in_zk(file_path: Path) -> Path | None:
    """
    Wrap a ZUL fragment in a namespaced <zk>...</zk> root.

    Multi-root ZUL fragments (several top-level components, e.g. content loaded
    via createComponents/<include>) are legal ZUL but not well-formed as a
    standalone XML document, so Layer 1 rejects them. Wrapping the body in a
    single <zk> root makes such fragments validatable without altering their
    meaning (the <zk> content model accepts any components).

    The <zk> open tag is inserted immediately before the first real element
    (after any leading PIs/comments) with no newline, so body line numbers are
    preserved in downstream error messages. Returns a temp file path, or None
    if no element is found.
    """
    with open(file_path, 'r') as f:
        content = f.read()

    skip_spans = [
        (m.start(), m.end())
        for m in re.finditer(r'<!--.*?-->|<\?.*?\?>', content, re.DOTALL)
    ]

    first = None
    for m in re.finditer(r'<([a-zA-Z][\w.-]*)', content):
        if not any(start <= m.start() < end for start, end in skip_spans):
            first = m
            break
    if first is None:
        return None

    pos = first.start()
    wrapped = content[:pos] + f'<zk xmlns="{ZK_NS}">' + content[pos:] + '</zk>'

    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.zul', delete=False)
    tmp.write(wrapped)
    tmp.close()
    return Path(tmp.name)


def _double_dash_comment_line(text: str) -> int | None:
    """
    Find a comment whose body contains '--', which XML forbids. Java allows it,
    and the controller guidelines suggest '// --- section ---' separators, so the
    habit carries into ZUL and costs a validation round.

    Returns the 1-based line number of the offending comment, or None.
    """
    pos = 0
    while (start := text.find('<!--', pos)) != -1:
        end = text.find('-->', start + 4)
        body = text[start + 4:end if end != -1 else len(text)]
        if '--' in body:
            return text.count('\n', 0, start) + 1
        pos = (end + 3) if end != -1 else len(text)
    return None


def validate_xml_wellformedness(file_path: Path) -> tuple[bool, str | None]:
    """
    Layer 1: Check if the file is well-formed XML.
    Uses standard library - no external dependencies.

    Returns:
        (True, None) if valid
        (False, error_message) if invalid
    """
    try:
        ET.parse(file_path)
        return True, None
    except ET.ParseError as e:
        # Improve error message with context
        line_num, col_num = e.position
        error_msg = f"XML syntax error: {e.msg} at line {line_num}, column {col_num}"
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
                if 0 < line_num <= len(lines):
                    # Show the problematic line
                    context_line = lines[line_num - 1].rstrip()
                    error_msg += f"\n  Line {line_num}: {context_line}"
                    error_msg += f"\n  {' ' * (len(str(line_num)) + 2 + col_num)}^"
                    
                    # Heuristic for unclosed tags on previous lines
                    if line_num > 1:
                        prev_line = lines[line_num - 2].strip()
                        if '<' in prev_line and '>' not in prev_line:
                            error_msg += f"\n  Hint: Line {line_num-1} appears to have an unclosed tag: {prev_line}"

                    # Heuristic for '--' inside a comment: expat only reports an
                    # "invalid token", which does not point at the real rule.
                    bad = _double_dash_comment_line(''.join(lines))
                    if bad is not None:
                        error_msg += (
                            f"\n  Hint: Line {bad} has '--' inside an XML comment."
                            " XML forbids that anywhere between <!-- and -->."
                            " Use '=' for separators: <!-- ===== left column ===== -->"
                        )
        except Exception:
            pass # Fallback to original message if file reading fails
            
        return False, error_msg
    except Exception as e:
        return False, f"Error reading file: {e}"


def validate_xsd_schema(file_path: Path, xsd_source: str = str(DEFAULT_XSD_PATH)) -> tuple[bool, list[str]]:
    """
    Layer 2: Validate the ZUL file against an XSD schema.
    Requires lxml library.

    Args:
        file_path: Path to the ZUL file to validate
        xsd_source: URL or local file path to the XSD schema

    Returns:
        (True, []) if valid
        (False, [error_messages]) if invalid
    """
    try:
        from lxml import etree
    except ImportError:
        return False, ["lxml is required for XSD validation. Install with: pip install lxml"]

    import urllib.request
    import io

    errors = []

    try:
        # Determine if xsd_source is a URL or local file
        if xsd_source.startswith(('http://', 'https://')):
            # Fetch XSD schema via HTTP (handles redirects)
            with urllib.request.urlopen(xsd_source, timeout=30) as response:
                xsd_content = response.read()
            schema_doc = etree.parse(io.BytesIO(xsd_content))
        else:
            # Load from local file
            xsd_path = Path(xsd_source)
            if not xsd_path.exists():
                return False, [f"XSD file not found: {xsd_source}"]
            schema_doc = etree.parse(str(xsd_path))

        schema = etree.XMLSchema(schema_doc)

    except urllib.error.URLError as e:
        return False, [f"Failed to fetch XSD schema from {xsd_source}: {e}"]
    except etree.XMLSchemaParseError as e:
        # This often happens with ZK's official XSD due to duplicate definitions
        return False, [
            f"XSD schema has internal errors: {e}",
            "Note: ZK's official XSD may have issues. Consider:",
            "  1. Use --skip-xsd to skip schema validation",
            "  2. Use --xsd with a local corrected schema file"
        ]
    except Exception as e:
        return False, [f"Failed to load XSD schema: {e}"]

    try:
        # Parse and validate the ZUL file
        with open(file_path, 'rb') as f:
            doc = etree.parse(f)

        if schema.validate(doc):
            return True, []
        else:
            for error in schema.error_log:
                errors.append(f"Line {error.line}: {error.message}")
            return False, errors

    except etree.XMLSyntaxError as e:
        return False, [f"XML syntax error: {e}"]
    except Exception as e:
        return False, [f"Validation error: {e}"]


# Elements that forward any attribute they are given somewhere else -- to an
# included page or to a template -- so an undeclared name is the feature, not a
# mistake. The XSD has no way to express this, and a check that does not know it
# reports ZK's own documented examples as errors.
PASS_THROUGH_ATTRIBUTE_ELEMENTS = {"apply", "include"}


def build_attribute_map(
    xsd_path: Path,
) -> tuple[dict[str, set[str]], dict[str, list[str]], set[str]] | tuple[None, None, None]:
    """
    Parse the XSD to build per-element valid attribute maps.

    Returns:
        (element_attrs, attr_elements, wildcard_elements) where:
        - element_attrs: {element_name: {valid_attr_names}}
        - attr_elements: {attr_name: [element_names]} (reverse map for hints)
        - wildcard_elements: elements whose own type declares xs:anyAttribute, so
          any attribute name is legal on them and asking "is X accepted here" has
          no meaningful No answer
        Or (None, None, None) if lxml is unavailable.
    """
    try:
        from lxml import etree
    except ImportError:
        return None, None, None

    XS = "{http://www.w3.org/2001/XMLSchema}"

    tree = etree.parse(str(xsd_path))
    root = tree.getroot()

    # Step 1: Collect attributeGroup definitions
    raw_groups = {}  # name -> (direct_attrs, ref_groups)
    for ag in root.iterchildren(f'{XS}attributeGroup'):
        name = ag.get('name')
        if name is None:
            continue
        direct_attrs = set()
        ref_groups = []
        for child in ag:
            if child.tag == f'{XS}attribute':
                attr_name = child.get('name')
                if attr_name:
                    direct_attrs.add(attr_name)
            elif child.tag == f'{XS}attributeGroup':
                ref = child.get('ref')
                if ref:
                    ref_groups.append(ref)
        raw_groups[name] = (direct_attrs, ref_groups)

    # Resolve attributeGroups recursively
    resolved_groups = {}

    def resolve_group(name, visited=None):
        if visited is None:
            visited = set()
        if name in resolved_groups:
            return resolved_groups[name]
        if name in visited or name not in raw_groups:
            return set()
        visited.add(name)
        direct, refs = raw_groups[name]
        result = set(direct)
        for ref in refs:
            result |= resolve_group(ref, visited)
        resolved_groups[name] = result
        return result

    for name in raw_groups:
        resolve_group(name)

    # Step 2: Collect complexType definitions
    def collect_type_attrs(ct_elem):
        """Collect attributes from a complexType element (handles nested structures)."""
        attrs = set()
        for child in ct_elem:
            if child.tag == f'{XS}attribute':
                attr_name = child.get('name')
                if attr_name:
                    attrs.add(attr_name)
            elif child.tag == f'{XS}attributeGroup':
                ref = child.get('ref')
                if ref and ref in resolved_groups:
                    attrs |= resolved_groups[ref]
            elif child.tag in (f'{XS}complexContent', f'{XS}simpleContent'):
                # Handle type extension (e.g., toolbarbuttonType extends buttonType).
                # simpleContent is not an afterthought: every text-bearing element
                # keeps its attributes in there, so skipping it resolved <attribute>
                # and <zscript> to an empty set and made the tool answer "NOT
                # accepted" for <attribute name="...">, which is canonical ZUL.
                for ext in child:
                    if ext.tag == f'{XS}extension':
                        base = ext.get('base')
                        if base and base in type_attrs:
                            attrs |= type_attrs[base]
                        attrs |= collect_type_attrs(ext)
        return attrs

    def declares_wildcard(ct_elem) -> bool:
        """
        True when this type declares xs:anyAttribute itself.

        Deliberately not a search of the whole subtree: the shared zkAttrGroup
        carries an anyAttribute that every component inherits, so a recursive
        search would call every element a wildcard. Only a wildcard written into
        the element's own type means "this element really does take any name",
        which is how <custom-attributes> and <variables> are defined.
        """
        for child in ct_elem:
            if child.tag == f'{XS}anyAttribute':
                return True
            if child.tag in (f'{XS}complexContent', f'{XS}simpleContent'):
                for ext in child:
                    if ext.tag == f'{XS}extension' and declares_wildcard(ext):
                        return True
        return False

    type_attrs = {}  # type_name -> set of attr names
    # Two-pass: first collect all, then resolve extensions
    type_elems = {}
    for ct in root.iterchildren(f'{XS}complexType'):
        name = ct.get('name')
        if name is None:
            continue
        type_elems[name] = ct

    # Process types without extensions first, then with extensions
    for name, ct in type_elems.items():
        has_extension = ct.find(f'{XS}complexContent/{XS}extension') is not None
        if not has_extension:
            type_attrs[name] = collect_type_attrs(ct)
    for name, ct in type_elems.items():
        if name not in type_attrs:
            type_attrs[name] = collect_type_attrs(ct)

    wildcard_types = {name for name, ct in type_elems.items() if declares_wildcard(ct)}

    # Step 3: Map element names to valid attributes
    element_attrs = {}
    wildcard_elements = set()
    for elem in root.iterchildren(f'{XS}element'):
        name = elem.get('name')
        type_name = elem.get('type')
        if name and type_name and type_name in type_attrs:
            element_attrs[name] = type_attrs[type_name]
            if type_name in wildcard_types:
                wildcard_elements.add(name)

    # Elements whose arbitrary attributes are a documented feature rather than a
    # schema wildcard, so nothing in the XSD can be read to discover them:
    #   <include src="inner.zul" type="..."/>   passes type as a page argument
    #   <apply template="x" item="${each}"/>    passes item to the template
    # ZK's own reference documents both. Judging those names against a declared
    # list produces a confident No for the feature working as designed.
    wildcard_elements |= PASS_THROUGH_ATTRIBUTE_ELEMENTS & set(element_attrs)

    # Step 4: Build reverse map
    attr_elements = {}
    for elem_name, attrs in element_attrs.items():
        for attr in attrs:
            if attr not in attr_elements:
                attr_elements[attr] = []
            attr_elements[attr].append(elem_name)

    return element_attrs, attr_elements, wildcard_elements


def validate_attribute_placement(file_path: Path, xsd_path: Path) -> tuple[bool, list[str]]:
    """
    Layer 3: Check that attributes are used on components that support them.
    Catches misplaced attributes that XSD's anyAttribute wildcard allows through.

    The XSD uses xs:anyAttribute in zkAttrGroup which permits any unqualified
    attribute on any component. This check parses the XSD to determine which
    attributes each component actually declares, then flags mismatches.

    Returns:
        (True, []) if all attributes are correctly placed
        (False, [error_messages]) if misplaced attributes found
    """
    element_attrs, attr_elements, wildcard_elements = build_attribute_map(xsd_path)
    if element_attrs is None:
        return False, ["lxml is required for attribute placement check. Install with: pip install lxml"]

    try:
        from lxml import etree
    except ImportError:
        return False, ["lxml is required for attribute placement check."]

    errors = []
    ZUL_NS = "http://www.zkoss.org/2005/zul"
    all_known_attrs = set(attr_elements.keys())

    with open(file_path, 'rb') as f:
        doc = etree.parse(f)

    for elem in doc.iter():
        tag = elem.tag
        if not isinstance(tag, str) or '{' not in tag:
            continue
        ns, local = tag.split('}', 1)
        ns = ns[1:]

        if ns != ZUL_NS or local == 'zk':
            continue

        valid_attrs = element_attrs.get(local)
        if valid_attrs is None or local in wildcard_elements:
            continue

        for attr_name in elem.attrib:
            # Skip namespaced attributes (ca:, w:, client:, etc.)
            if '{' in attr_name:
                continue
            # Skip attributes not defined anywhere in XSD (truly custom)
            if attr_name not in all_known_attrs:
                continue
            if attr_name not in valid_attrs:
                line = elem.sourceline if hasattr(elem, 'sourceline') else '?'
                valid_on = sorted(attr_elements.get(attr_name, []))
                hint = f"Valid on: {', '.join(valid_on[:8])}"
                if len(valid_on) > 8:
                    hint += f" (+{len(valid_on) - 8} more)"
                errors.append(
                    f"Line {line}: Attribute '{attr_name}' is not supported on <{local}>. {hint}"
                )

    return len(errors) == 0, errors


REMOVED_ATTRIBUTES = {
    "autostart": (["audio"], "Deprecated since 7.0.0, use \"autoplay\" attribute instead."),
    "widths": (["box", "hbox", "vbox"], "Deprecated since 5.0.0, put <cell width> inside instead."),
    "heights": (["box", "hbox", "vbox"], "Deprecated since 5.0.0, put <cell height> inside instead."),
    "timeZone": (["calendar"], "Deprecated since 5.0.5, please remove it."),
    "border": (["captcha"], "Deprecated since 5.0.4, use \"frame\" attribute instead."),
    "align": (["div", "grid", "iframe", "image"], "Deprecated since 5.0/6.0. Use CSS instead: text-align: left|right, in a class attached with sclass"),
    "compact": (["datebox"], "Deprecated since 5.0.0, please remove it."),
    "maxsize": (["fileupload"], "Deprecated since 5.0.0, specified it in \"upload\" attribute e.g. upload=\"maxsize=1024\""),
    "number": (["fileupload"], "Deprecated since 5.0.0, specified it in \"upload\" attribute"),
    "native": (["fileupload"], "Deprecated since 5.0.0, specified it in \"upload\" attribute e.g. upload=\"native\""),
    "fixedLayout": (["grid", "listbox", "tree"], "Since 5.0.0, use \"sizedByContent\" attribute instead."),
    "legend": (["groupbox"], "Deprecated since 6.0, please remove it."),
    "hspace": (["image"], "Deprecated since 6.0.0. Use CSS instead: margin-left/margin-right, in a class attached with sclass"),
    "vspace": (["image"], "Deprecated since 6.0.0. Use CSS instead: margin-top/margin-bottom, in a class attached with sclass"),
    "hyphen": (["label"], "Deprecated since 5.0.0. Use CSS instead: overflow-wrap: break-word, in a class attached with sclass"),
    "flex": (["center", "east", "north", "south", "west"], "Deprecated since 6.0.2, use hflex or vflex on child components instead"),
    "preloadSize": (["grid", "listbox"], "Deprecated since 5.0.8, use <custom-attributes org.zkoss.zul.listbox.preloadSize=\"\"> or <custom-attributes org.zkoss.zul.grid.preloadSize=\"\" instead."),
    "checkable": (["listitem", "treeitem"], "Deprecated since 8.0.0, please use selectable"),
    "framable": (["panel"], "Deprecated since 5.0.6, use \"border\" attribute instead."),
    "spans": (["row", "group", "groupfoot"], "Deprecated since 5.0.0, use <cell colspan> instead."),
    "type": (["script"], "Deprecated since 5.0.0, text/javascript is always assumed, please remove it."),
    "dynamic": (["style"], "Deprecated since 5.0.0, it is decided by ZK automatically, please remove it."),
    "treeitemRenderer": (["tree"], "Deprecated since 5.0.6, replaced with \"itemRenderer\" attribute"),
    "defaultActionOnShow": (["window"], "Deprecated since 5.0.0, replaced with \"action\" attribute."),
    "src": (["a", "button", "caption", "checkbox", "comboitem", "fisheye", "footer", "listfooter", "treefooter", "auheader", "column", "listheader", "treecol", "listcell", "menu", "menuitem", "nav", "navitem", "orgnode", "tab", "treecell"], "Deprecated since 3.5.0, use \"image\" instead.")
}

# Components removed in a given ZK major version. The int is the earliest
# major version in which the component no longer exists; it is only flagged
# for targets at or above that version (e.g. <fragment> is valid in ZK 9).
REMOVED_COMPONENTS = {
    "fragment": (10, "Removed since 10.2.0, use the new Client MVVM (client-bind.jar) library instead")
}

# Attributes introduced in ZK 10.x that do NOT exist in ZK 9. Flagged only
# when validating against a pre-10 target so ZK 9 pages don't silently use
# ZK-10-only API against the bundled 10.x schema. Verified against the ZK
# component reference (supported-since markers); component-gated to avoid
# false positives on same-named attributes elsewhere.
NEW_IN_ZK10_ATTRIBUTES = {
    "accept": (["dropupload"], "Introduced in ZK 10.0.0; not available in ZK 9."),
    "responsive": (["grid"], "Introduced in ZK 10.4.0 (EE); not available in ZK 9."),
    "responsiveColumns": (["grid"], "Introduced in ZK 10.4.0 (EE); not available in ZK 9."),
    "responsiveVisible": (["column"], "Introduced in ZK 10.4.0 (EE); not available in ZK 9."),
}


def parse_major_version(zk_version: str) -> int:
    """Extract the leading major version integer (e.g. '10.3.0' -> 10,
    '9 or before' -> 9). Defaults to 10 when no digit is present."""
    m = re.match(r'\s*(\d+)', zk_version)
    return int(m.group(1)) if m else 10


def validate_version_compatibility(file_path: Path, major: int) -> tuple[bool, list[str]]:
    """
    Layer 4: Check for API incompatible with the target ZK major version.

    - Deprecated/removed attributes (all removed by ZK 8.x) are flagged for any
      supported target.
    - Components removed in ZK 10.x are flagged only for targets >= that version.
    - Attributes introduced in ZK 10.x are flagged for pre-10 targets, since
      they don't exist there.

    Returns:
        (True, []) if compatible
        (False, [error_messages]) if issues found
    """
    errors = []
    try:
        # Try to use lxml for line numbers if available
        try:
            from lxml import etree
            with open(file_path, 'rb') as f:
                root = etree.parse(f).getroot()
            use_lxml = True
        except ImportError:
            tree = ET.parse(file_path)
            root = tree.getroot()
            use_lxml = False
        
        # Check all elements
        for elem in root.iter():
            # Skip non-element nodes (comments, PIs) where tag is callable
            if not isinstance(elem.tag, str):
                continue
            # Get local name (without namespace)
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            tag_lower = tag.lower()
            
            line_str = f"Line {elem.sourceline}: " if use_lxml and hasattr(elem, 'sourceline') else ""

            # Check for removed components (only for targets at/above removal version)
            if tag_lower in REMOVED_COMPONENTS:
                removed_in, hint = REMOVED_COMPONENTS[tag_lower]
                if major >= removed_in:
                    errors.append(f"{line_str}Component <{tag}> is removed. {hint}")

            # Check attributes
            for attr_name, attr_value in elem.attrib.items():
                attr_name_local = attr_name.split('}')[-1] if '}' in attr_name else attr_name

                # Removed/deprecated attributes (relevant to all supported targets)
                if attr_name_local in REMOVED_ATTRIBUTES:
                    components, hint = REMOVED_ATTRIBUTES[attr_name_local]
                    if tag_lower in components:
                        errors.append(f"{line_str}Attribute '{attr_name_local}' on <{tag}> is removed. {hint}")

                # ZK-10-only attributes used against a pre-10 target
                if major < 10 and attr_name_local in NEW_IN_ZK10_ATTRIBUTES:
                    components, hint = NEW_IN_ZK10_ATTRIBUTES[attr_name_local]
                    if tag_lower in components:
                        errors.append(f"{line_str}Attribute '{attr_name_local}' on <{tag}> is not available in ZK {major}. {hint}")

        return len(errors) == 0, errors

    except Exception as e:
        return False, [f"Compatibility check error: {e}"]


# --- Layer 6: runtime semantics -------------------------------------------
# Markup that is legal by every static measure and still dies when the page is built.

# `selectedIndex` is applied while the component tree is built, which is BEFORE the
# component's own literal children are attached, BEFORE any Composer's doAfterCompose and
# BEFORE the MVVM binder loads a model. That timing is what makes this checkable from the
# markup alone -- and it is stronger than it looks.
#
# Measured by rendering each component with its literal items present (ZK 10.3.0.1):
#
#   component    literal items in markup   bound model      outcome
#   combobox     2 <comboitem>             @load(list)      throws BOTH ways
#   listbox      2 <listitem>              @load(list)      throws BOTH ways
#   radiogroup   2 <radio>                 (no model form)  throws
#   tabbox       2 <tab>                   (no model form)  throws
#   selectbox    (no literal form)         @load(list)      RENDERS
#   cardlayout   2 child <div>             (no model form)  RENDERS
#
# Exceptions raised: `Out of bound: 0 while size=0` (combobox, listbox),
# `0 out of 0..-1` (radiogroup), `No tab at all` (tabbox).
#
# So for the first four, NEITHER literal items NOR a model rescues the index: counting the
# children is the wrong model of the timing, and an earlier version of this layer stayed
# silent on `<combobox selectedIndex="0">` with three comboitems right there in the markup
# because it counted them. Those four are flagged unconditionally.
#
# For selectbox and cardlayout the setter tolerates an index, so they keep the counting
# rule: flag only when there is nothing at all for the index to point at.
ALWAYS_THROWS_ON_LITERAL_INDEX = {
    # component -> how to express the intended selection instead
    "combobox": 'set value="..." on a readonly combobox, or select from the controller '
                'once the model is in place',
    "listbox": 'mark the item with <listitem selected="true">, or select through the '
               'model (model.addToSelection(...)) after setModel',
    "radiogroup": 'mark the option with <radio selected="true">',
    "tabbox": 'mark the tab with <tab selected="true">',
}

# Components whose setter tolerates the index.
#   None  -> the index counts arbitrary child components (cardlayout's cards)
#   set() -> the component has no literal item form at all; it requires a model
TOLERANT_ITEM_TAGS = {
    "selectbox": set(),
    "cardlayout": None,
}


def validate_runtime_semantics(file_path: Path) -> tuple[bool, list[str]]:
    """
    Layer 6: legal markup that throws while the page is being built.

    Currently one rule: a literal selectedIndex on a component that cannot take one yet.
    An evaluation run shipped `<combobox selectedIndex="0">` with no items; it passed all
    five layers and the render died with `Out of bound: 0 while size=0`.

    For combobox, listbox, radiogroup and tabbox this fires unconditionally, because the
    index is applied before the children are attached and before any model is set -- see
    the measured table above. A `model` attribute is NOT an exemption for those four; a
    model-driven `<listbox model="@load(vm.items)" selectedIndex="0">` throws exactly the
    same way.

    Selectbox and cardlayout tolerate an index, so for those two the rule stays silent
    whenever a model is present or enough children exist: under-reporting is the safe
    direction for a list the agent is told to trust.
    """
    errors = []
    try:
        try:
            from lxml import etree
            with open(file_path, 'rb') as f:
                root = etree.parse(f).getroot()
            use_lxml = True
        except ImportError:
            root = ET.parse(file_path).getroot()
            use_lxml = False

        for elem in root.iter():
            if not isinstance(elem.tag, str):
                continue
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            tag_l = tag.lower()
            if tag_l not in ALWAYS_THROWS_ON_LITERAL_INDEX and tag_l not in TOLERANT_ITEM_TAGS:
                continue

            raw = None
            for name, value in elem.attrib.items():
                if (name.split('}')[-1] if '}' in name else name) == 'selectedIndex':
                    raw = value
                    break
            if raw is None:
                continue

            # A bound or computed index is resolved after construction; not ours to judge.
            if not re.fullmatch(r'\s*-?\d+\s*', raw):
                continue
            index = int(raw.strip())
            # -1 is the documented "nothing selected" value and is always legal.
            if index < 0:
                continue

            line_str = f"Line {elem.sourceline}: " if use_lxml and hasattr(elem, 'sourceline') else ""

            # These four throw whatever the markup says: neither the literal items nor a
            # bound model exists yet when the index is applied.
            if tag_l in ALWAYS_THROWS_ON_LITERAL_INDEX:
                errors.append(
                    f"{line_str}selectedIndex=\"{index}\" will throw at render time. "
                    f"<{tag}> applies the index before its items are attached and before any "
                    f"model is set, so neither literal items nor model=\"...\" makes it safe -- "
                    f"{ALWAYS_THROWS_ON_LITERAL_INDEX[tag_l]}."
                )
                continue

            if any((n.split('}')[-1] if '}' in n else n) == 'model' for n in elem.attrib):
                continue

            item_tags = TOLERANT_ITEM_TAGS[tag_l]
            if item_tags is None:
                available = sum(1 for c in elem if isinstance(c.tag, str))
                what = "child components"
            else:
                available = sum(
                    1 for d in elem.iter()
                    if isinstance(d.tag, str)
                    and (d.tag.split('}')[-1] if '}' in d.tag else d.tag).lower() in item_tags
                )
                what = " or ".join(f"<{t}>" for t in sorted(item_tags)) if item_tags else "items"

            if available > index:
                continue

            if item_tags == set():
                detail = (f"<{tag}> has no literal item form, so it needs a model. "
                          f"Set the model before selecting, or drop selectedIndex.")
            elif available == 0:
                detail = (f"<{tag}> declares no {what} and no model, so index {index} has nothing "
                          f"to point at. Add the items, bind a model, or drop selectedIndex.")
            else:
                detail = (f"<{tag}> declares {available} {what}, so index {index} is out of range "
                          f"(valid: 0-{available - 1}).")
            errors.append(
                f"{line_str}selectedIndex=\"{index}\" will throw at render time. {detail}"
            )

        return len(errors) == 0, errors

    except Exception as e:
        return False, [f"Runtime semantics check error: {e}"]


# --- Layer 7: controller cross-check --------------------------------------
# @Wire binds a Java field to a ZUL id. A wrong type compiles, validates, renders
# fine, and throws ClassCastException only when the field is first used; a wrong id
# leaves the field null. Neither the validator nor the render can see either one,
# which is what puts this in reach of a source check and nothing else.

# Families where one element-named class inherits from another, so a field typed as
# the ancestor is perfectly legal. The rule cannot tell those apart without a real
# class hierarchy, so it declines to judge any component in this set. Skipping a
# whole family is a deliberate trade: a missed defect costs a round, a false
# accusation costs the agent's trust in the whole list.
WIRE_AMBIGUOUS_FAMILIES = {
    # Textbox is the ancestor of combobox and bandbox, but not of the numeric boxes.
    "textbox", "combobox", "bandbox", "intbox", "longbox", "doublebox", "decimalbox",
    "spinner", "doublespinner", "datebox", "timebox",
    # Radio extends Checkbox.
    "checkbox", "radio",
    # Hbox and Vbox extend Box.
    "box", "hbox", "vbox",
    # Group and Groupfoot extend Row; Listgroup and Listgroupfoot extend Listitem.
    "row", "group", "groupfoot", "listitem", "listgroup", "listgroupfoot",
    # Combobutton extends Button.
    "button", "combobutton",
}

# An id may legitimately come from somewhere this file cannot see.
WIRE_OPAQUE_TAGS = {"include", "foreach", "apply", "if", "choose", "when", "otherwise"}

# @Wire, then optionally ("selector"), then a field declaration. Methods are excluded
# by requiring the declaration to end in a semicolon.
WIRE_FIELD = re.compile(
    r'@Wire\s*(?:\(\s*"([^"]*)"\s*\)\s*)?'
    r'(?:(?:private|protected|public|static|final|transient|volatile)\s+)*'
    r'([A-Za-z_][\w.]*)\s+([A-Za-z_]\w*)\s*(?:=[^;]*)?;'
)


def _top_level_body_span(source: str) -> tuple[int, int] | None:
    """
    The character range of the outermost type's body, exclusive of its braces.

    Why this is needed: a composer may declare a nested class that is itself a
    component -- `public class ArticleEditor extends Window` inside the composer,
    building its own UI. Its @Wire fields are wired against that component's own
    tree, so measuring them against this ZUL accuses correct code. Measured on ZK's
    own documentation: 2 false accusations out of 170 real fields, all of this shape.

    `source` must already have comments and string literals blanked in place, so a
    brace inside either cannot be counted and every offset is still true.
    """
    opener = re.search(r'\b(?:class|interface|enum|record)\b[^{;]*\{', source)
    if opener is None:
        return None
    start = opener.end()
    depth = 1
    for i in range(start, len(source)):
        ch = source[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return start, i
    return start, len(source)


def _blank_literals(source: str) -> str:
    """Replace string and char literal contents with spaces, preserving length so
    every offset computed against the result is still an offset into the original."""
    def blank(match):
        return match.group(0)[0] + ' ' * (len(match.group(0)) - 2) + match.group(0)[-1]
    source = re.sub(r'"(?:\\.|[^"\\\n])*"', blank, source)
    return re.sub(r"'(?:\\.|[^'\\\n])*'", blank, source)


def _tag_to_class(tag: str) -> str:
    """ZK's ZUL tags map to class names by capitalising the first letter, with no
    other transformation: a -> A, hlayout -> Hlayout, toolbarbutton -> Toolbarbutton."""
    return tag[:1].upper() + tag[1:]


def validate_controller_wiring(zul_path: Path, controller_path: Path,
                               element_names: set[str]) -> tuple[bool, list[str]]:
    """
    Layer 7: cross-check @Wire fields in a controller against the ZUL's ids.

    Reports two things it can establish from the two files alone:
      - a wired id that no component in the ZUL declares (the field stays null)
      - a field whose type is a different concrete component than the one it names

    Everything it cannot establish, it stays silent about: see WIRE_AMBIGUOUS_FAMILIES
    and WIRE_OPAQUE_TAGS.
    """
    errors = []
    try:
        try:
            from lxml import etree
            with open(zul_path, 'rb') as f:
                root = etree.parse(f).getroot()
        except ImportError:
            root = ET.parse(zul_path).getroot()

        id_to_tag = {}
        opaque = False
        for elem in root.iter():
            if not isinstance(elem.tag, str):
                continue
            tag = (elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag)
            if tag.lower() in WIRE_OPAQUE_TAGS:
                opaque = True
            for name, value in elem.attrib.items():
                if (name.split('}')[-1] if '}' in name else name) == 'id':
                    id_to_tag[value] = tag

        source = controller_path.read_text(encoding='utf-8', errors='replace')
        # Blank comments rather than removing them, so a commented-out @Wire is not
        # read as real AND every remaining match keeps its true offset. Deleting them
        # shifts every line number after the first comment, which sends the reader to
        # the wrong line -- a wrong location is worse than no location.
        blank = lambda m: re.sub(r'[^\n]', ' ', m.group(0))
        source = re.sub(r'/\*.*?\*/', blank, source, flags=re.S)
        source = re.sub(r'//[^\n]*', blank, source)

        # Braces are counted on a copy with literals blanked too, because a brace
        # inside "{0}" would shift the depth. Matching still uses `source`, where
        # the @Wire("#id") selector is intact -- blanking preserves length, so the
        # two strings share every offset.
        body = _top_level_body_span(_blank_literals(source))
        nesting = _blank_literals(source)

        for match in WIRE_FIELD.finditer(source):
            selector, field_type, field_name = match.groups()
            # Anchor on the type token, not on @Wire: the type is what has to change,
            # and the annotation is usually on the line above it.
            line = source.count('\n', 0, match.start(2)) + 1

            # Generics and arrays are collections of components, not one component.
            if '<' in field_type or '[' in field_type:
                continue

            # Only the outermost class is wired against this ZUL. A field inside a
            # nested class belongs to that class's own component tree, so neither
            # half of this check can say anything true about it.
            if body is not None:
                start, end = body
                pos = match.start(2)
                if not (start <= pos < end) or nesting.count('{', start, pos) != nesting.count('}', start, pos):
                    continue

            if selector is None:
                target_id = field_name
            elif re.fullmatch(r'#[A-Za-z_][\w-]*', selector.strip()):
                target_id = selector.strip()[1:]
            else:
                # A class or pseudo-class selector can match many components.
                continue

            simple_type = field_type.rsplit('.', 1)[-1]
            zul_tag = id_to_tag.get(target_id)

            if zul_tag is None:
                if opaque:
                    # An <include> or a shadow element can contribute ids this file
                    # never shows, so absence proves nothing here.
                    continue
                errors.append(
                    f"Line {line}: @Wire {simple_type} {field_name} names id '{target_id}', which "
                    f"no component in {zul_path.name} declares. The field stays null and the first "
                    f"use throws NullPointerException."
                )
                continue

            # Only compare when both sides are unambiguously concrete components.
            if simple_type.lower() not in element_names:
                continue
            if zul_tag.lower() in WIRE_AMBIGUOUS_FAMILIES or simple_type.lower() in WIRE_AMBIGUOUS_FAMILIES:
                continue

            expected = _tag_to_class(zul_tag)
            if simple_type != expected:
                article = "an" if expected[:1] in "AEIOU" else "a"
                errors.append(
                    f"Line {line}: @Wire {simple_type} {field_name} is wired to <{zul_tag} "
                    f"id=\"{target_id}\">, which is {article} {expected}. This compiles and renders, "
                    f"then throws ClassCastException the first time the field is used. Change the "
                    f"field type to {expected}."
                )

        return len(errors) == 0, errors

    except Exception as e:
        return False, [f"Controller cross-check error: {e}"]


def collect_element_names(xsd_path: Path) -> set[str] | None:
    """Every component name the schema declares, including those whose type it
    does not resolve. Used to answer "does <x> exist" independently of whether
    the attribute map could be built for it."""
    try:
        from lxml import etree
    except ImportError:
        return None
    XS = "{http://www.w3.org/2001/XMLSchema}"
    root = etree.parse(str(xsd_path)).getroot()
    return {e.get('name') for e in root.iterchildren(f'{XS}element') if e.get('name')}


def describe_component(component: str, attrs_asked: list[str], xsd_path: Path, major: int) -> bool:
    """
    Answer, from the bundled schema, what a component is and what it accepts --
    BEFORE the component gets written, rather than after.

    The skill has shipped this 183 KB schema all along and used it only as a
    checker. A checker answers once the markup is already wrong, at the cost of a
    render round; the same file asked first answers for free, exactly, locally,
    with no retrieval involved. Two of six evaluation runs invented this move on
    their own (one learned <charts> takes className/zclass and not sclass, the
    other that <togglebutton> does not exist in ZK 10) and both reported that the
    schema, not the documentation, is what saved them.

    Returns True when the component exists at this ZK version and every asked-for
    attribute is accepted, so the exit code is usable in a script.
    """
    names = collect_element_names(xsd_path)
    if names is None:
        print("lxml is required for --describe. Install with: pip install lxml")
        return False

    element_attrs, attr_elements, wildcard_elements = build_attribute_map(xsd_path)
    if element_attrs is None:
        print("lxml is required for --describe. Install with: pip install lxml")
        return False

    asked = component.lstrip('<').rstrip('>').strip()
    # The schema is case-sensitive, but an agent reaching for a component may not be.
    actual = asked if asked in names else next((n for n in names if n.lower() == asked.lower()), None)

    # Removal is checked BEFORE absence, because the two look identical in this file and
    # mean opposite things. The bundled schema is a single 10.x document, so a component
    # dropped in 10.x is simply missing from it -- and reporting that as "not a ZUL
    # component" would be flatly wrong for a ZK 9 target, where it is valid.
    removed_in, removed_hint = REMOVED_COMPONENTS.get(asked.lower(), (None, None))
    if removed_in is not None and major >= removed_in:
        print(f"Component <{asked}>: REMOVED as of ZK {removed_in}, so not available for your "
              f"ZK {major} target.")
        print(f"  {removed_hint}")
        return False
    if removed_in is not None and actual is None:
        print(f"Component <{asked}>: existed in ZK {major}, removed in ZK {removed_in}.")
        print(f"  {removed_hint}")
        print(f"  The bundled schema is 10.x and no longer declares it, so this tool cannot list "
              f"its attributes. Verify those against the ZK {major} component reference.")
        return True

    if actual is None:
        print(f"Component <{asked}>: NOT FOUND in the bundled schema.")
        close = difflib.get_close_matches(asked.lower(), sorted(names), n=5, cutoff=0.6)
        if close:
            print(f"  Closest names in the schema: {', '.join(close)}")
        print("  Nothing in the schema declares this component -- do not write it, and do not "
              "assume an add-on jar would supply it without checking.")
        if major < 10:
            print(f"  Caveat: the bundled schema is 10.x, so it cannot confirm a component that "
                  f"exists only in ZK {major}. Absence here is decisive for ZK 10+ and suggestive, "
                  f"not conclusive, for ZK {major}.")
        return False

    status = f"available in ZK {major}"
    if removed_in is not None:
        status += f" (but removed in ZK {removed_in} -- avoid if the project may upgrade)"
    print(f"Component <{actual}>: {status}")

    valid = element_attrs.get(actual)
    if valid is None:
        print("  The schema declares this component but does not resolve an attribute list for it.")
        print("  Treat the attribute set as unknown: verify against the ZK component reference.")
        return not attrs_asked

    if actual in wildcard_elements:
        # Answering No here would be a confident wrong answer about a feature: these
        # elements hand whatever name they are given to an included page, a template,
        # or the component's attribute map. There is no list to check against.
        why = ("passes any attribute it does not recognise on as an argument"
               if actual in PASS_THROUGH_ATTRIBUTE_ELEMENTS
               else "declares xs:anyAttribute, so the schema itself imposes no list")
        print(f"  <{actual}> accepts ARBITRARY attribute names -- it {why}.")
        for want in attrs_asked:
            print(f"  {want.strip()}: accepted (any name is)")
        print("  Nothing here can be checked for you: a typo in the name is legal markup "
              "and will simply be ignored at runtime, so check the spelling against "
              "whatever reads it.")
        return True

    ok = True
    if attrs_asked:
        # The question that actually costs a round is "does it take THIS attribute",
        # and a 40-name list is the wrong shape for proving an absence.
        for want in attrs_asked:
            want = want.strip()
            if want in valid:
                notes = []
                gone = REMOVED_ATTRIBUTES.get(want)
                if gone and actual.lower() in gone[0]:
                    notes.append(f"REMOVED: {gone[1]}")
                    ok = False
                new10 = NEW_IN_ZK10_ATTRIBUTES.get(want)
                if new10 and actual.lower() in new10[0] and major < 10:
                    notes.append(f"NOT IN ZK {major}: {new10[1]}")
                    ok = False
                suffix = (" -- " + "; ".join(notes)) if notes else ""
                print(f"  {want}: accepted{suffix}")
            else:
                ok = False
                near = difflib.get_close_matches(want, sorted(valid), n=4, cutoff=0.5)
                hint = f" Did you mean: {', '.join(near)}?" if near else ""
                print(f"  {want}: NOT accepted on <{actual}>.{hint}")
                elsewhere = sorted(attr_elements.get(want, []))
                if elsewhere:
                    shown = ', '.join(elsewhere[:8])
                    more = f" (+{len(elsewhere) - 8} more)" if len(elsewhere) > 8 else ""
                    print(f"    '{want}' is valid on: {shown}{more}")
        return ok

    listed = sorted(valid)
    print(f"  Accepts {len(listed)} attributes:")
    for line in textwrap.wrap(', '.join(listed), width=92):
        print(f"    {line}")

    deprecated = sorted(a for a in listed
                        if a in REMOVED_ATTRIBUTES and actual.lower() in REMOVED_ATTRIBUTES[a][0])
    if deprecated:
        print(f"  Declared but REMOVED -- do not use: {', '.join(deprecated)}")
    if major < 10:
        too_new = sorted(a for a in listed
                         if a in NEW_IN_ZK10_ATTRIBUTES and actual.lower() in NEW_IN_ZK10_ATTRIBUTES[a][0])
        if too_new:
            print(f"  Declared but NOT available in ZK {major}: {', '.join(too_new)}")

    print("  An attribute absent from that list is not accepted, however plausible it looks. "
          "Use --attr to ask about one directly.")
    return ok


# A style value that is computed while the page runs -- a colour or a width taken from a
# record -- cannot be expressed as a static class, so a binding or EL expression here is
# a legitimate inline style and not worth reporting.
DYNAMIC_STYLE_VALUE = re.compile(r'\$\{|@\s*(?:load|bind|init)\s*\(')


def find_inline_styles(file_path: Path) -> list[str]:
    """
    Layer 5 (advisory): report static style="..." attributes.

    A style attribute is rendered onto the widget's own element, so it outranks every
    rule any stylesheet can write: the page stops being themeable, later CSS silently
    loses to it, and no :hover/:focus/@media rule can reach it. The same declarations
    pasted onto several components then drift apart, where one class would be edited
    once. The fix is always the same -- move the declarations into the page's <style>
    block as a class and attach it with sclass.

    This is a convention rather than a correctness question, and a page may have a
    defensible one-off, so this layer reports and never fails the run.
    """
    notes = []
    try:
        try:
            from lxml import etree
            with open(file_path, 'rb') as f:
                root = etree.parse(f).getroot()
            use_lxml = True
        except ImportError:
            root = ET.parse(file_path).getroot()
            use_lxml = False

        for elem in root.iter():
            if not isinstance(elem.tag, str):
                continue
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            for attr_name, attr_value in elem.attrib.items():
                local = attr_name.split('}')[-1] if '}' in attr_name else attr_name
                if local != "style" or DYNAMIC_STYLE_VALUE.search(attr_value or ""):
                    continue
                line_str = f"Line {elem.sourceline}: " if use_lxml and hasattr(elem, 'sourceline') else ""
                value = " ".join((attr_value or "").split())
                if len(value) > 60:
                    value = value[:57] + "..."
                notes.append(f'{line_str}<{tag} style="{value}">')
        return notes

    except Exception:
        # Never let the advisory layer speak up about anything but inline styles: the
        # failing layers above have already reported whatever made parsing impossible.
        return []


def validate_zul(file_path: Path, skip_xsd: bool = False, xsd_source: str = str(DEFAULT_XSD_PATH),
                 zk_version: str = "10", controller: Path | None = None) -> bool:
    """
    Validate a ZUL file through all validation layers.

    Returns:
        True if all validations pass, False otherwise
    """
    print(f"Validating: {file_path}")
    print("-" * 50)

    all_valid = True

    # active_path is what downstream layers validate. It becomes a <zk>-wrapped
    # temp copy when the input is a legal-but-multi-root ZUL fragment.
    active_path = file_path
    wrapped_path = None

    # Layer 1: XML Well-formedness
    print("Layer 1: XML Well-formedness... ", end="")
    is_valid, error = validate_xml_wellformedness(file_path)
    if is_valid:
        print("✓ PASS")
    else:
        # A multi-root ZUL fragment isn't well-formed standalone but is legal
        # ZUL; retry after wrapping it in a single <zk> root.
        wrapped_path = wrap_fragment_in_zk(file_path)
        if wrapped_path and validate_xml_wellformedness(wrapped_path)[0]:
            print("✓ PASS (fragment wrapped in <zk> for validation)")
            active_path = wrapped_path
        else:
            print("✗ FAIL")
            print(f"  {error}")
            if wrapped_path:
                wrapped_path.unlink(missing_ok=True)
            # Skip remaining layers if XML is malformed
            return False

    # For Layer 2 & 3: inject default ZK namespace if not declared
    # (ZK treats http://www.zkoss.org/2005/zul as implicit default)
    ns_injected_path = inject_default_namespace(active_path) if not skip_xsd else None
    schema_file = ns_injected_path or active_path

    try:
        # Layer 2: XSD Schema Validation
        if not skip_xsd:
            print("Layer 2: XSD Schema Validation... ", end="")
            is_valid, errors = validate_xsd_schema(schema_file, xsd_source)
            if is_valid:
                print("✓ PASS")
            else:
                print("✗ FAIL")
                for error in errors:
                    print(f"  {error}")
                all_valid = False
        else:
            print("Layer 2: XSD Schema Validation... SKIPPED")

        # Layer 3: Attribute Placement Check
        if not skip_xsd:
            xsd_path = Path(xsd_source) if not xsd_source.startswith(('http://', 'https://')) else DEFAULT_XSD_PATH
            print("Layer 3: Attribute Placement... ", end="")
            is_valid, errors = validate_attribute_placement(schema_file, xsd_path)
            if is_valid:
                print("✓ PASS")
            else:
                print("✗ FAIL")
                for error in errors:
                    print(f"  {error}")
                all_valid = False
        else:
            print("Layer 3: Attribute Placement... SKIPPED")
    finally:
        if ns_injected_path:
            ns_injected_path.unlink(missing_ok=True)

    # Layer 4: Version Compatibility (runs for every target ZK version)
    major = parse_major_version(zk_version)
    # Echo the raw --zk-version beside the number it was reduced to, whenever the two differ.
    # Six independent runs of this skill passed six different spellings of the same version
    # ('10.3.0', '10.3.0.1-Eval', ...) and every one of them guessed at what the flag does with
    # the tail, because this line printed only the outcome. The input and its interpretation
    # side by side answer that where it is actually being asked; a sentence in the workflow
    # would only be read by whoever went looking for it.
    parsed_from = "" if zk_version.strip() == str(major) else f' (major version from "{zk_version}")'
    print(f"Layer 4: ZK {major} Compatibility{parsed_from}... ", end="")
    is_valid, errors = validate_version_compatibility(active_path, major)
    if is_valid:
        print("✓ PASS")
    else:
        print("✗ FAIL")
        for error in errors:
            print(f"  {error}")
        all_valid = False

    # Layer 5: Inline Styles (advisory -- reports, never fails; see find_inline_styles)
    print("Layer 5: Inline Styles... ", end="")
    inline_styles = find_inline_styles(active_path)
    if not inline_styles:
        print("✓ PASS")
    else:
        plural = "s" if len(inline_styles) > 1 else ""
        print(f"⚠ {len(inline_styles)} inline style attribute{plural} (advisory)")
        for note in inline_styles:
            print(f"  {note}")
        print("  Move these declarations into the page's <style> block as a class and "
              "attach it with sclass.")

    # Layer 6: Runtime Semantics
    print("Layer 6: Runtime Semantics... ", end="")
    is_valid, errors = validate_runtime_semantics(active_path)
    if is_valid:
        print("✓ PASS")
    else:
        print("✗ FAIL")
        for error in errors:
            print(f"  {error}")
        all_valid = False

    # Layer 7: Controller Cross-Check -- only when a controller is named, so the
    # default output shape stays exactly what it has always been.
    if controller is not None:
        print("Layer 7: Controller Cross-Check... ", end="")
        if not controller.exists():
            print("✗ FAIL")
            print(f"  Controller not found: {controller}")
            all_valid = False
        else:
            xsd_path = (Path(xsd_source) if not xsd_source.startswith(('http://', 'https://'))
                        else DEFAULT_XSD_PATH)
            element_names = collect_element_names(xsd_path)
            if element_names is None:
                print("SKIPPED (lxml unavailable)")
            else:
                is_valid, errors = validate_controller_wiring(active_path, controller, element_names)
                if is_valid:
                    print("✓ PASS")
                else:
                    print("✗ FAIL")
                    for error in errors:
                        print(f"  {error}")
                    all_valid = False

    if wrapped_path:
        wrapped_path.unlink(missing_ok=True)

    print("-" * 50)
    if all_valid:
        print("Result: ✓ All validations passed")
    else:
        print("Result: ✗ Validation failed")

    return all_valid


def main():
    parser = argparse.ArgumentParser(
        description="Validate ZUL files for XML well-formedness and XSD schema compliance",
        epilog=f"Default schema: {DEFAULT_XSD_PATH}"
    )
    # nargs="*" rather than "+" so --describe can run without a file. The
    # "no arguments at all" usage error is re-created by hand below, because
    # argparse can no longer enforce it.
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="ZUL file(s) to validate"
    )
    parser.add_argument(
        "--describe",
        metavar="COMPONENT",
        help="Ask the bundled schema about a component instead of validating a file: does it exist "
             "at this ZK version, and what attributes does it accept. Use this BEFORE writing a "
             "component you have not used before -- it costs nothing and replaces a guess."
    )
    parser.add_argument(
        "--attr",
        action="append",
        default=[],
        metavar="NAME",
        help="With --describe, ask whether this specific attribute is accepted (repeatable). "
             "Answering 'is this attribute allowed here' is what --describe is for; a full "
             "attribute list is the wrong shape for proving an absence."
    )
    parser.add_argument(
        "--skip-xsd",
        action="store_true",
        help="Skip XSD schema validation (Layer 2)"
    )
    parser.add_argument(
        "--xsd",
        dest="xsd_source",
        default=str(DEFAULT_XSD_PATH),
        help=f"XSD schema URL or local file path (default: {DEFAULT_XSD_PATH})"
    )
    parser.add_argument(
        "--zk-version",
        dest="zk_version",
        default="10",
        help="Target ZK version, e.g. 9, 10, or 10.3.0 (default: 10). Layer 4 tailors "
             "compatibility checks to this version: ZK-10-only API (e.g. dropped <fragment>) "
             "is flagged only for 10+, while attributes introduced in ZK 10 are flagged for 9."
    )

    parser.add_argument(
        "--controller",
        type=Path,
        metavar="PATH",
        help="Path to the Composer or ViewModel for this page. Enables Layer 7, which cross-checks "
             "@Wire fields against the ZUL's ids: a wrong id leaves the field null, and a wrong "
             "field type throws ClassCastException at first use. Neither is visible to the other "
             "layers or to a render."
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Development mode: suppress the anonymous usage ping for this run, so "
             "developing or testing the skill does not inflate its usage counts. "
             "Same effect as DO_NOT_TRACK=1, but per-invocation."
    )

    args = parser.parse_args()

    if not args.files and not args.describe:
        parser.error("the following arguments are required: files")
    if args.attr and not args.describe:
        parser.error("--attr only applies with --describe")

    if args.describe:
        # No usage ping for a schema lookup. It is not a run of the skill, and a
        # third emitter inside one run would break the usage trend line at the
        # version boundary in a way that reads as growth (the D19 reasoning).
        xsd_path = (Path(args.xsd_source)
                    if not args.xsd_source.startswith(('http://', 'https://'))
                    else DEFAULT_XSD_PATH)
        ok = describe_component(args.describe, args.attr, xsd_path,
                                parse_major_version(args.zk_version))
        sys.exit(0 if ok else 1)

    track_usage_async(dev=args.dev)

    all_passed = True
    for file_path in args.files:
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            all_passed = False
            continue

        if not validate_zul(file_path, skip_xsd=args.skip_xsd, xsd_source=args.xsd_source,
                            zk_version=args.zk_version, controller=args.controller):
            all_passed = False

        print()  # Blank line between files

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
