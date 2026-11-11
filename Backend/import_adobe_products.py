import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
DOCUMENT_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
PRODUCT_HEADER_ROW = 4


def node_text(node):
    return "".join(part.text or "" for part in node.iter(f"{{{MAIN_NS}}}t"))


def column_index(reference):
    letters = re.match(r"[A-Z]+", reference).group(0)
    result = 0
    for letter in letters:
        result = result * 26 + ord(letter) - 64
    return result - 1


def cell_value(cell, shared_strings):
    cell_type = cell.attrib.get("t")
    value_node = cell.find(f"{{{MAIN_NS}}}v")
    if cell_type == "s" and value_node is not None:
        return shared_strings[int(value_node.text)]
    if cell_type == "inlineStr":
        return node_text(cell)
    if cell_type == "b" and value_node is not None:
        return value_node.text == "1"
    if cell_type in {"str", "e"} and value_node is not None:
        return value_node.text
    if value_node is None:
        return None

    raw_value = value_node.text
    try:
        number = float(raw_value)
        return int(number) if number.is_integer() else number
    except (TypeError, ValueError):
        return raw_value


def workbook_rows(path):
    with zipfile.ZipFile(path) as archive:
        archive_names = set(archive.namelist())
        shared_strings = []
        if "xl/sharedStrings.xml" in archive_names:
            shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared_strings = [node_text(item) for item in shared_root.findall(f"{{{MAIN_NS}}}si")]

        relationships_root = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {
            relationship.attrib["Id"]: relationship.attrib["Target"]
            for relationship in relationships_root.findall(f"{{{PACKAGE_REL_NS}}}Relationship")
        }
        workbook_root = ET.fromstring(archive.read("xl/workbook.xml"))

        for sheet in workbook_root.find(f"{{{MAIN_NS}}}sheets"):
            sheet_name = sheet.attrib["name"]
            if "terms" in sheet_name.lower():
                continue

            target = targets[sheet.attrib[f"{{{DOCUMENT_REL_NS}}}id"]].replace("\\", "/")
            sheet_path = target.lstrip("/") if target.startswith("/xl/") else "xl/" + target.lstrip("/")
            sheet_root = ET.fromstring(archive.read(sheet_path))
            rows = {}
            for row in sheet_root.iter(f"{{{MAIN_NS}}}row"):
                row_number = int(row.attrib.get("r", len(rows) + 1))
                values = {}
                for cell in row.findall(f"{{{MAIN_NS}}}c"):
                    value = cell_value(cell, shared_strings)
                    if value not in (None, ""):
                        values[column_index(cell.attrib.get("r", "A1"))] = value
                if values:
                    rows[row_number] = values

            header_values = rows.get(PRODUCT_HEADER_ROW, {})
            headers = {index: str(value).strip() for index, value in header_values.items()}
            for row_number in sorted(number for number in rows if number > PRODUCT_HEADER_ROW):
                record = {
                    headers[index]: value
                    for index, value in rows[row_number].items()
                    if index in headers
                }
                if record.get("Part Number") and record.get("Product Family"):
                    yield sheet_name, row_number, record


def clean_text(value, fallback="Not specified"):
    if value in (None, ""):
        return fallback
    return str(value).strip()


def stable_product_id(variant_key):
    digest = hashlib.sha256(variant_key.encode("utf-8")).digest()
    return 1_000_000_000 + int.from_bytes(digest[:5], "big")


def slugify(value):
    return re.sub(r"(^-|-$)", "", re.sub(r"[^a-z0-9]+", "-", value.lower()))


def source_vendor(source_name):
    return "NCA" if source_name.lower().startswith("nca") else "TechData"


def variant_key(record, sheet_name):
    values = [
        clean_text(record.get("Part Number"), ""),
        segment_for(sheet_name, ""),
        clean_text(record.get("Additional Detail"), ""),
        clean_text(record.get("Users"), ""),
        clean_text(record.get("Level Detail"), ""),
        clean_text(record.get("Duration"), ""),
        clean_text(record.get("Metric"), ""),
        clean_text(record.get("Points"), ""),
    ]
    return "|".join(values)


def segment_for(sheet_name, source_name):
    label = f"{source_name} {sheet_name}".lower()
    if "education" in label or "edu" in label:
        return "Education"
    if "3yc" in label:
        return "Commercial - 3 Year Commit"
    if "nca" in label:
        return "Named User Licensing"
    return "Commercial"


def build_product(record, sheet_name, source_name):
    part_number = clean_text(record["Part Number"])
    family = clean_text(record["Product Family"])
    product_type = clean_text(record.get("Product Type"), "Adobe Software Subscription")
    product_type_detail = clean_text(record.get("Product Type Detail"), "Subscription")
    users = clean_text(record.get("Users"), "Per user")
    duration = clean_text(record.get("Duration"), "Subscription term")
    operating_system = clean_text(record.get("Operating System"), "Platform dependent")
    language = clean_text(record.get("Language"), "Multiple languages")
    additional_detail = clean_text(record.get("Additional Detail"), "Standard offering")
    level_detail = clean_text(record.get("Level Detail"), "Standard pricing level")
    segment = segment_for(sheet_name, source_name)
    identity = variant_key(record, sheet_name)
    identity_hash = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:10]
    variant_name_parts = [family]
    if additional_detail != "Standard offering":
        variant_name_parts.append(additional_detail)
    variant_name_parts.extend([level_detail, part_number])
    product_name = " - ".join(variant_name_parts)

    features = [
        f"{product_type_detail} Adobe licensing",
        f"Licensed for {users}",
        f"{duration} subscription term",
        f"Supports {operating_system} in {language}",
    ]
    short_description = (
        f"{family} Adobe licensing for {users}, supplied as a {duration.lower()} offering."
    )
    description = (
        f"{family} is an Adobe {product_type_detail.lower()} offering for {users}. "
        f"This {duration.lower()} SKU is provided under the {segment.lower()} program and supports "
        f"{operating_system} with {language}. Review the licensing level and additional details "
        "below to confirm that this edition matches your organization’s requirements."
    )

    additional_info = {
        "Product Edition": family,
        "Publisher / Brand": "Adobe",
        "Part Number": part_number,
        "Product ID": part_number,
        "Software Type": product_type,
        "Product Type": product_type_detail,
        "Family": family,
        "Agreement": sheet_name,
        "Segment": segment,
        "Version": clean_text(record.get("Version")),
        "Operating System": operating_system,
        "Language": language,
        "Term": duration,
        "Purchase Unit": users,
        "Additional Detail": additional_detail,
        "Level Detail": level_detail,
        "Metric": clean_text(record.get("Metric")),
        "Pool": clean_text(record.get("Pool")),
        "UPC / EAN Code": clean_text(record.get("UPC/EAN Code")),
        "Distributor": source_vendor(source_name),
        "License Type": f"Digital License ({sheet_name})",
        "Delivery": "Digital delivery via email",
        "Support & Updates": "Official Adobe support and updates according to the subscription plan",
    }

    return {
        "id": stable_product_id(identity),
        "name": product_name,
        "slug": f"{slugify(family)}-{slugify(part_number)}-{identity_hash}",
        "productId": part_number,
        "partNumber": part_number,
        "category": "Adobe Software",
        "softwareType": product_type,
        "family": family,
        "term": duration,
        "brand": "Adobe",
        "brandCode": "AD",
        "image": "/products/adobe-software.png",
        "price": None,
        "enquiryOnly": True,
        "badge": "Adobe Subscription",
        "moq": users,
        "stockAvailability": "Available",
        "features": features,
        "shortDescription": short_description,
        "description": description,
        "additionalInfo": additional_info,
        "warranty": "Adobe license supplied under the applicable subscription and program terms.",
    }


def main():
    parser = argparse.ArgumentParser(description="Import Adobe distributor XLSX price lists.")
    parser.add_argument("workbooks", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("adobe_products.json"))
    args = parser.parse_args()

    products_by_variant = {}
    equivalent_offer_count = 0
    for workbook_path in args.workbooks:
        for sheet_name, _row_number, record in workbook_rows(workbook_path):
            product = build_product(record, sheet_name, workbook_path.name)
            identity = variant_key(record, sheet_name)
            existing = products_by_variant.get(identity)
            if existing:
                equivalent_offer_count += 1
                continue
            products_by_variant[identity] = product

    products = sorted(
        products_by_variant.values(),
        key=lambda item: (item["family"], item["partNumber"], item["slug"]),
    )
    ids = [product["id"] for product in products]
    if len(ids) != len(set(ids)):
        raise ValueError("Stable Adobe product ID collision detected")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(products, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(
        f"Generated {len(products)} Adobe products in {args.output} "
        f"({equivalent_offer_count} equivalent distributor offers consolidated)."
    )


if __name__ == "__main__":
    main()