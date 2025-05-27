import docx2txt
import fitz
import subprocess
import os
from logger import logger
from paddleocr import PaddleOCR
import cv2
import pandas as pd
# Initialize PaddleOCR for OCR processing
ocr = PaddleOCR(use_angle_cls=True, lang="en", det=True, rec=True)

# Backend storage folder for documents
backend_folder = "backend_documents"

# Required document types and formats
required_docs = {
    "Identification Document": ["pdf", "docx", "png", "jpg", "jpeg"],
    "Sale Deed": ["pdf", "docx", "png", "jpg", "jpeg"],
    "Credit Score Report": ["pdf", "docx", "png", "jpg", "jpeg"],
    "Bank Statement": ["csv", "xlsx"]
}

expected_files = {
    "Identification Document": "Identification_Document.png",
    "Bank Statement": "Bank_Statement.csv",
    "Credit Score Report": "Credit_Score_Report.jpg",
    "Sale Deed": "Sale_Deed.pdf"
}

def verify_documents():
    """Check if specific required documents are present in the backend folder."""
    available_files = {}
    missing_files = []

    for doc_type, filename in expected_files.items():
        file_path = os.path.join(backend_folder, filename)
        if os.path.exists(file_path):
            available_files[doc_type] = file_path
        else:
            available_files[doc_type] = None
            missing_files.append(doc_type)

    all_docs_uploaded = len(missing_files) == 0

    return available_files, all_docs_uploaded, missing_files


ocr = PaddleOCR(use_angle_cls=True, lang="en", det=True, rec=True)

def extract_text_paddle(file_path):
    """Extract structured text while maintaining document layout (headings, tables, paragraphs)."""
    try:
        img = cv2.imread(file_path)  # Load image
        result = ocr.ocr(img, cls=True)  # Perform OCR with layout detection

        structured_text = []
        for line in result[0]:
            text = line[1][0]  # Extract text
            structured_text.append(text)

        return "\n".join(structured_text)  # Join text while preserving order

    except Exception as e:
        print(f"Error extracting structured text: {e}")
        return ""
    
### **Step 2: Extract Identity from ID Document**
def extract_text(file_path):
    """Extract text from documents (Sale Deed, Credit Report, ID, Bank Statement)."""
    text = ""
    try:
        if file_path.endswith('.pdf'):
            document = fitz.open(file_path)
            text = "\n".join([page.get_text("text") for page in document])

        elif file_path.endswith('.docx'):
            text = docx2txt.process(file_path)

        elif file_path.endswith(('.png', '.jpg', '.jpeg')):
            logger.info(f"Extracting text from Image using PaddleOCR: {file_path}")
            text = extract_text_paddle(file_path)

        elif file_path.endswith(('.csv', '.xlsx')):
            return None  # Skip text extraction for CSV files

        else:
            raise ValueError("Unsupported file format")

        return text.encode('utf-8', 'ignore').decode('utf-8')

    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {e}")
        return ""


def extract_identity(text):
    """Extracts Name, Address, Gender, and Profile Picture from ID document."""
    try:
        prompt = f"""
        Extract the following details from this identification document:
        - **Customer Name**
        - **Address**
        - **Gender**
        - **ID Number**
        - **Profile Picture (if available)**

        **Extracted Text:**
        {text}

        Provide a structured **human-readable summary**.
        """
        return run_ollama_model(prompt)

    except Exception as e:
        logger.error(f"Error extracting identity: {e}")
        return "Error extracting identity details."


### **Step 3: Cross-Check Name Across Documents**
def verify_name_match(identity_details, doc_text, document_name):
    """Matches the extracted customer name across documents (Sale Deed, Credit Report)."""
    try:
        prompt = f"""
        Verify if the customer name in this {document_name} matches the name extracted from the Identification Document.

        **Extracted {document_name} Text:**
        {doc_text}

        **Customer Identity Details:**
        {identity_details}

        Return **YES or NO**, and provide a short reason.
        """
        return run_ollama_model(prompt)

    except Exception as e:
        logger.error(f"Error verifying name in {document_name}: {e}")
        return "Error verifying name."


### **Step 4: Generate Final Customer Profile**
def generate_customer_profile(identity_details, sale_deed_summary, credit_score_summary, bank_summary):
    """Generates a comprehensive customer profile using the LLM."""
    try:
        prompt = f"""
        Based on the following customer details, generate a structured **Customer Profile** for the Relationship Manager.

        **Identification Details:**
        {identity_details}

        **Sale Deed Summary:**
        {sale_deed_summary}

        **Credit Score Report Summary:**
        {credit_score_summary}

        **Bank Statement Analysis:**
        {bank_summary}

        Provide a **well-structured, human-readable summary** that gives an overview of:
        - **Customer Identity**
        - **Financial Standing**
        - **Creditworthiness**
        - **Any risks or important observations**
        """
        return run_ollama_model(prompt)

    except Exception as e:
        logger.error(f"Error generating customer profile: {e}")
        return "Error generating customer profile."


### **Helper Function: Run LLM Model**
def run_ollama_model(prompt):
    """Calls the Ollama model via CLI and returns structured response."""
    try:
        result = subprocess.run(
            ["ollama", "run", "gemma2:2b"],
            input=prompt.encode("utf-8", "ignore").decode("utf-8"),
            text=True,
            capture_output=True,
            encoding="utf-8"
        )

        if result.returncode != 0:
            raise Exception(f"Ollama CLI Error: {result.stderr.strip()}")

        return result.stdout.strip()

    except Exception as e:
        logger.error(f"Error running Ollama model: {e}")
        return "Unable to generate a response."


def summarize_sale_deed(text):
    """Generates a plain-text summary of the Sale Deed."""
    try:
        prompt = f"""
        You are analyzing a **Sale Deed** document.

        Extract and summarize in great detail:
        - **Seller Name**
        - **Buyer Name**
        - **Property Address**
        - **Exact Sale Amount and Payment Terms** (e.g., lump sum or installments).
        - **Date of Sale**
        - **Additional Conditions**, such as ownership transfer clauses or maintenance responsibilities.


        **Extracted Sale Deed:**
        {text}

        Provide a **human-readable summary**.
        """

        summary = run_ollama_model(prompt)
        logger.debug(f"Sale Deed Summary: {summary}")

        return summary  

    except Exception as e:
        logger.error(f"Error summarizing Sale Deed: {e}")
        return "Error processing Sale Deed summary."


def summarize_credit_report(text):
    """Generates a plain-text summary of the Credit Score Report."""
    try:
        prompt = f"""
        You are analyzing a **Credit Score Report**.

        Extract and summarize:
        - **Credit Score Breakdown**: Explain how the score was calculated and what it indicates.
        - **Credit Utilization**: Describe the current balance-to-limit ratio and its impact.
        - **Loan Repayment History**: Highlight past loans, late payments, and their effect.
        - **Outstanding Loans & Debt Status**: Mention amounts due, interest rates, and terms.
        - **Risk Level Assessment**: Based on the report, classify the customer as Low, Medium, or High risk.

        **Extracted Credit Report:**
        {text}

        Provide a **human-readable summary**.
        """

        summary = run_ollama_model(prompt)
        logger.debug(f"Credit Score Summary: {summary}")

        return summary  

    except Exception as e:
        logger.error(f"Error summarizing Credit Score Report: {e}")
        return "Error processing Credit Score Report summary."


def summarize_id_document(text):
    """Summarizes Identification Documents (Aadhar, Passport, National ID)."""
    try:
        prompt = f"""
        You are analyzing an **Identification Document**.

        Extract and summarize:
        - **Full Name**
        - **Date of Birth**
        - **ID Number (Passport, National ID)**
        - **Address**
        - **Issuing Authority**

        **Extracted ID Document:**
        {text}

        Provide a **human-readable summary** with the title name **Summary**.
        """
        
        summary = run_ollama_model(prompt)
        logger.debug(f"ID Document Summary: {summary}")

        return summary  

    except Exception as e:
        logger.error(f"Error summarizing Identification Document: {e}")
        return "Error processing Identification Document summary."


def analyze_bank_statement(csv_file_path, time_range="total",  return_dataframe=False):
    try:
        df = pd.read_csv(csv_file_path)

        # Ensure correct column names
        required_columns = {"CR_DR_INDICATOR", "TXN_AMOUNT_LCY", "TXN_DATE_TIME", "TXN_DESC"}
        if not required_columns.issubset(df.columns):
            raise ValueError(f"Missing required columns: {required_columns - set(df.columns)}")

        # Convert date column to datetime
        df["TXN_DATE_TIME"] = pd.to_datetime(df["TXN_DATE_TIME"])

        # Determine the first transaction date as the reference date
        start_date = df["TXN_DATE_TIME"].min()
        end_date = df["TXN_DATE_TIME"].max()

        if time_range == "weekly":
            end_date = start_date + pd.Timedelta(days=7)
        elif time_range == "monthly":
            end_date = start_date + pd.DateOffset(months=1)

        # Convert start_date and end_date to `pd.Timestamp` before filtering
        df_filtered = df[(df["TXN_DATE_TIME"] >= pd.Timestamp(start_date)) & (df["TXN_DATE_TIME"] <= pd.Timestamp(end_date))]

        # Identify salary credits (assuming transactions contain "SALARY" or "PAYROLL")
        total_salary = df_filtered[(df_filtered["CR_DR_INDICATOR"] == "C") & df_filtered["TXN_DESC"].str.contains("SALARY|PAYROLL", case=False, na=False)]["TXN_AMOUNT_LCY"].sum()

        total_expenditure = df_filtered[df_filtered["CR_DR_INDICATOR"] == "D"]["TXN_AMOUNT_LCY"].sum()

        # Estimated Savings: Salary - Expenditure
        estimated_savings = total_salary - total_expenditure

        # Identify potential investments (keywords: MF, STOCK, BOND, FD, etc.)
        investment_df = df_filtered[df_filtered["TXN_DESC"].str.contains("MF|STOCK|BOND|FD|ETF|MUTUAL FUND", case=False, na=False)]
        total_investments = investment_df["TXN_AMOUNT_LCY"].sum()

        # Generate summary output
        summary = f"""
        **Bank Statement Analysis ({time_range.capitalize()} View - Based on First Transaction Date):**
        - **Total Salary Credited:** Rs {total_salary:.2f}
        - **Total Expenditure:** Rs {total_expenditure:.2f}
        - **Estimated Savings:** Rs {estimated_savings:.2f}
        - **Total Investments Identified:** Rs {total_investments:.2f}
        """
        if return_dataframe:
            return summary, df_filtered
        return summary

    except Exception as e:
        print(f"Error analyzing bank statement: {e}")
        return "Error processing the bank statement."



def query_document(text, query, document_type):
    """Generates a response to user queries about Sale Deed or Credit Score Report."""
    try:
        prompt = f"""
        You are analyzing a **{document_type}** document. Based on the document, answer the following:

        **Extracted Document:**
        {text}

        **User Query:** {query}

        Provide a **clear and concise** answer.
        """

        return run_ollama_model(prompt)

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return "Unable to answer the query."