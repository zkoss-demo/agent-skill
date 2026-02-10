#!/usr/bin/env python3
"""
ZUL File Validator

Validates ZUL files for:
  Layer 1: XML well-formedness (no dependencies)
  Layer 2: XSD schema validation (requires lxml)
  Layer 3: ZK 10 compatibility checks (no dependencies)

Note: ZK's official XSD may have issues. This script defaults to using the
revised local schema in ../assets/zul.xsd. Use --xsd to override it.
"""

import sys
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path


# Default to the revised local schema file
DEFAULT_XSD_PATH = Path(__file__).parent.parent / "assets" / "zul.xsd"
ZK_XSD_URL = "http://www.zkoss.org/2005/zul/zul.xsd"


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


REMOVED_ATTRIBUTES = {
    "autostart": (["audio"], "Deprecated since 7.0.0, use \"autoplay\" attribute instead."),
    "widths": (["box", "hbox", "vbox"], "Deprecated since 5.0.0, put <cell width> inside instead."),
    "heights": (["box", "hbox", "vbox"], "Deprecated since 5.0.0, put <cell height> inside instead."),
    "timeZone": (["calendar"], "Deprecated since 5.0.5, please remove it."),
    "border": (["captcha"], "Deprecated since 5.0.4, use \"frame\" attribute instead."),
    "align": (["div", "grid", "iframe", "image"], "Deprecated since 5.0/6.0, use CSS instead e.g. align=\"left\" --> style=\"text-align:left\", align=\"right\" --> style=\"text-align:right\""),
    "compact": (["datebox"], "Deprecated since 5.0.0, please remove it."),
    "maxsize": (["fileupload"], "Deprecated since 5.0.0, specified it in \"upload\" attribute e.g. upload=\"maxsize=1024\""),
    "number": (["fileupload"], "Deprecated since 5.0.0, specified it in \"upload\" attribute"),
    "native": (["fileupload"], "Deprecated since 5.0.0, specified it in \"upload\" attribute e.g. upload=\"native\""),
    "fixedLayout": (["grid", "listbox", "tree"], "Since 5.0.0, use \"sizedByContent\" attribute instead."),
    "legend": (["groupbox"], "Deprecated since 6.0, please remove it."),
    "hspace": (["image"], "Deprecated since 6.0.0, use CSS instead, style=\"margin-left:10px; margin-right:10px;\""),
    "vspace": (["image"], "Deprecated since 6.0.0, use CSS instead, style=\"margin-top:10px; margin-bottom:10px;\""),
    "hyphen": (["label"], "Deprecated since 5.0.0, use CSS instead, style=\"overflow-wrap: break-word;\""),
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

REMOVED_COMPONENTS = {
    "fragment": "Removed since 10.2.0, use the new Client MVVM (client-bind.jar) library instead"
}


def validate_zk10_compatibility(file_path: Path) -> tuple[bool, list[str]]:
    """
    Layer 3: Check for ZK 10 compatibility issues that may not be caught by XSD.
    (e.g., deprecated or removed attributes allowed by XSD wildcards)

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
            # Get local name (without namespace)
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            tag_lower = tag.lower()
            
            line_str = f"Line {elem.sourceline}: " if use_lxml and hasattr(elem, 'sourceline') else ""
            
            # Check for removed components
            if tag_lower in REMOVED_COMPONENTS:
                errors.append(f"{line_str}ZK 10 Compatibility: Component <{tag}> is removed. {REMOVED_COMPONENTS[tag_lower]}")
            
            # Check for removed attributes
            for attr_name, attr_value in elem.attrib.items():
                attr_name_local = attr_name.split('}')[-1] if '}' in attr_name else attr_name
                
                if attr_name_local in REMOVED_ATTRIBUTES:
                    components, hint = REMOVED_ATTRIBUTES[attr_name_local]
                    if tag_lower in components:
                        errors.append(f"{line_str}ZK 10 Compatibility: Attribute '{attr_name_local}' on <{tag}> is removed. {hint}")

        return len(errors) == 0, errors

    except Exception as e:
        return False, [f"Compatibility check error: {e}"]


def validate_zul(file_path: Path, skip_xsd: bool = False, xsd_source: str = str(DEFAULT_XSD_PATH), zk_version: str = "10") -> bool:
    """
    Validate a ZUL file through all validation layers.

    Returns:
        True if all validations pass, False otherwise
    """
    print(f"Validating: {file_path}")
    print("-" * 50)

    all_valid = True

    # Layer 1: XML Well-formedness
    print("Layer 1: XML Well-formedness... ", end="")
    is_valid, error = validate_xml_wellformedness(file_path)
    if is_valid:
        print("✓ PASS")
    else:
        print("✗ FAIL")
        print(f"  {error}")
        all_valid = False
        # Skip Layer 2 if XML is malformed
        return False

    # Layer 2: XSD Schema Validation
    if not skip_xsd:
        print("Layer 2: XSD Schema Validation... ", end="")
        is_valid, errors = validate_xsd_schema(file_path, xsd_source)
        if is_valid:
            print("✓ PASS")
        else:
            print("✗ FAIL")
            for error in errors:
                print(f"  {error}")
            all_valid = False
    else:
        print("Layer 2: XSD Schema Validation... SKIPPED")

    # Layer 3: ZK 10 Compatibility
    if zk_version.startswith("10"):
        print("Layer 3: ZK 10 Compatibility... ", end="")
        is_valid, errors = validate_zk10_compatibility(file_path)
        if is_valid:
            print("✓ PASS")
        else:
            print("✗ FAIL")
            for error in errors:
                print(f"  {error}")
            all_valid = False
    else:
        print(f"Layer 3: ZK 10 Compatibility... SKIPPED (Version {zk_version} specified)")

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
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="ZUL file(s) to validate"
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
        help="ZK version to validate against (default: 10). Layer 3 checks only run for version 10.x."
    )

    args = parser.parse_args()

    all_passed = True
    for file_path in args.files:
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            all_passed = False
            continue

        if not validate_zul(file_path, skip_xsd=args.skip_xsd, xsd_source=args.xsd_source, zk_version=args.zk_version):
            all_passed = False

        print()  # Blank line between files

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
