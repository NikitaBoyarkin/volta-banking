"""
PDF Processing Module

Utilities for parsing and processing PDF files (bank statements, reports, etc.).
Based on Anthropic Skills patterns for PDF automation.

Dependencies:
    pip install pdfplumber pypdf pdf2image pytesseract

Usage:
    from utils.pdf_processor import extract_tables_from_pdf, merge_pdfs
"""

import os

import pandas as pd
import pdfplumber
from pypdf import PdfReader, PdfWriter


def extract_tables_from_pdf(
    pdf_path: str, output_excel: str = None, page_range: tuple = None
) -> list[pd.DataFrame]:
    """
    Extract all tables from a PDF file.

    Parameters
    ----------
    pdf_path : str
        Path to PDF file
    output_excel : str, optional
        If provided, save extracted tables to Excel
    page_range : tuple, optional
        (start, end) page range to process (1-indexed)

    Returns
    -------
    List[pd.DataFrame]
        List of DataFrames, one per table found

    Examples
    --------
    >>> tables = extract_tables_from_pdf("bank_statement.pdf")
    >>> tables = extract_tables_from_pdf("report.pdf", output_excel="tables.xlsx")
    >>> tables = extract_tables_from_pdf("doc.pdf", page_range=(1, 5))
    """

    all_tables = []

    with pdfplumber.open(pdf_path) as pdf:
        # Determine page range
        if page_range:
            start, end = page_range
            pages = pdf.pages[start - 1 : end]
        else:
            pages = pdf.pages

        for page_num, page in enumerate(pages, 1):
            tables = page.extract_tables()

            for _table_num, table in enumerate(tables):
                if table and len(table) > 1:  # Has data beyond header
                    # First row as header
                    headers = table[0]
                    data = table[1:]

                    # Clean headers
                    headers = [
                        str(h).strip() if h else f"Column_{i}" for i, h in enumerate(headers)
                    ]

                    df = pd.DataFrame(data, columns=headers)
                    df["source_page"] = page_num
                    df["source_table"] = len(all_tables) + 1
                    df["source_file"] = os.path.basename(pdf_path)

                    all_tables.append(df)

    # Save to Excel if requested
    if output_excel and all_tables:
        with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
            for i, table in enumerate(all_tables):
                table.to_excel(writer, sheet_name=f"Table_{i + 1}", index=False)
        print(f"✓ Extracted {len(all_tables)} tables to {output_excel}")

    return all_tables


def extract_text_from_pdf(pdf_path: str, output_txt: str = None, page_range: tuple = None) -> str:
    """
    Extract all text from a PDF file.

    Parameters
    ----------
    pdf_path : str
        Path to PDF file
    output_txt : str, optional
        If provided, save extracted text to file
    page_range : tuple, optional
        (start, end) page range to process

    Returns
    -------
    str
        Extracted text content
    """

    full_text = []

    with pdfplumber.open(pdf_path) as pdf:
        if page_range:
            start, end = page_range
            pages = pdf.pages[start - 1 : end]
        else:
            pages = pdf.pages

        for page_num, page in enumerate(pages, 1):
            text = page.extract_text()
            if text:
                full_text.append(f"--- Page {page_num} ---\n{text}")

    result = "\n\n".join(full_text)

    if output_txt:
        with open(output_txt, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"✓ Extracted text to {output_txt}")

    return result


def merge_pdfs(pdf_paths: list[str], output_path: str) -> str:
    """
    Merge multiple PDF files into one.

    Parameters
    ----------
    pdf_paths : List[str]
        List of paths to PDF files
    output_path : str
        Output merged PDF path

    Returns
    -------
    str
        Path to merged PDF

    Examples
    --------
    >>> merge_pdfs(["q1.pdf", "q2.pdf", "q3.pdf"], "annual_report.pdf")
    """

    writer = PdfWriter()

    for pdf_path in pdf_paths:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            writer.add_page(page)

    os.makedirs(
        os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True
    )

    with open(output_path, "wb") as output:
        writer.write(output)

    print(f"✓ Merged {len(pdf_paths)} files into {output_path}")
    return output_path


def split_pdf(pdf_path: str, output_dir: str = "output/split", prefix: str = "page") -> list[str]:
    """
    Split a PDF into individual pages.

    Parameters
    ----------
    pdf_path : str
        Path to PDF file
    output_dir : str
        Directory for output files
    prefix : str
        Prefix for output filenames

    Returns
    -------
    List[str]
        List of created file paths
    """

    reader = PdfReader(pdf_path)
    output_paths = []

    os.makedirs(output_dir, exist_ok=True)

    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)

        output_path = os.path.join(output_dir, f"{prefix}_{i + 1:03d}.pdf")
        with open(output_path, "wb") as output:
            writer.write(output)

        output_paths.append(output_path)

    print(f"✓ Split into {len(output_paths)} pages in {output_dir}")
    return output_paths


def parse_bank_statement(pdf_path: str, output_excel: str = None) -> dict[str, pd.DataFrame | str]:
    """
    Parse a bank statement PDF and extract structured data.

    Parameters
    ----------
    pdf_path : str
        Path to bank statement PDF
    output_excel : str, optional
        If provided, save extracted data to Excel

    Returns
    -------
    Dict
        Dictionary with extracted data:
        - transactions: DataFrame of transactions
        - summary: DataFrame with account summary
        - metadata: Dict with document metadata
    """

    result = {"transactions": pd.DataFrame(), "summary": pd.DataFrame(), "metadata": {}}

    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        all_tables = []

        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

            tables = page.extract_tables()
            if tables:
                all_tables.extend(tables)

        # Extract metadata from text
        result["metadata"]["raw_text"] = full_text
        result["metadata"]["page_count"] = len(pdf.pages)
        result["metadata"]["source_file"] = os.path.basename(pdf_path)

        # Process tables
        if all_tables:
            # Assume largest table is transactions
            largest_table = max(all_tables, key=len)

            if len(largest_table) > 1:
                headers = largest_table[0]
                data = largest_table[1:]

                # Clean headers
                headers = [
                    str(h).strip().replace("\n", " ") if h else f"Col_{i}"
                    for i, h in enumerate(headers)
                ]

                result["transactions"] = pd.DataFrame(data, columns=headers)

    # Save to Excel if requested
    if output_excel:
        with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
            if not result["transactions"].empty:
                result["transactions"].to_excel(writer, sheet_name="Transactions", index=False)

            # Add metadata sheet
            metadata_df = pd.DataFrame(
                [
                    ["Page Count", result["metadata"]["page_count"]],
                    ["Source File", result["metadata"]["source_file"]],
                ],
                columns=["Field", "Value"],
            )
            metadata_df.to_excel(writer, sheet_name="Metadata", index=False)

        print(f"✓ Parsed statement to {output_excel}")

    return result


def get_pdf_info(pdf_path: str) -> dict:
    """
    Get PDF metadata and basic info.

    Parameters
    ----------
    pdf_path : str
        Path to PDF file

    Returns
    -------
    Dict
        Dictionary with PDF metadata
    """

    reader = PdfReader(pdf_path)

    info = {
        "page_count": len(reader.pages),
        "metadata": reader.metadata,
        "file_size": os.path.getsize(pdf_path),
        "file_name": os.path.basename(pdf_path),
    }

    return info


if __name__ == "__main__":
    # Example usage
    print("PDF Processor Module")
    print("=" * 50)
    print("Available functions:")
    print("  - extract_tables_from_pdf(pdf_path)")
    print("  - extract_text_from_pdf(pdf_path)")
    print("  - merge_pdfs(pdf_paths, output_path)")
    print("  - split_pdf(pdf_path, output_dir)")
    print("  - parse_bank_statement(pdf_path)")
    print("  - get_pdf_info(pdf_path)")
