#!/usr/bin/env python3
"""
ZUL File Validator

Validates ZUL files for:
  Layer 1: XML well-formedness (no dependencies)
  Layer 2: XSD schema validation (requires lxml)

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


def validate_zul(file_path: Path, skip_xsd: bool = False, xsd_source: str = str(DEFAULT_XSD_PATH)) -> bool:
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

    args = parser.parse_args()

    all_passed = True
    for file_path in args.files:
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            all_passed = False
            continue

        if not validate_zul(file_path, skip_xsd=args.skip_xsd, xsd_source=args.xsd_source):
            all_passed = False

        print()  # Blank line between files

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
