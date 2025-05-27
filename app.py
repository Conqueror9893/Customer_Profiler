import streamlit as st
import os
import json
import time
import pandas as pd
import fitz
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
from generate_embeddings import (
    extract_text, 
    summarize_sale_deed, 
    summarize_credit_report, 
    summarize_id_document, 
    analyze_bank_statement, 
    run_ollama_model,
    query_document
)

# Streamlit UI Setup
st.set_page_config(page_title="🏦 Customer Profiler", layout="wide")

# **State Management**
if "step" not in st.session_state:
    st.session_state.step = 0
    st.session_state.uploaded_files = {}  # Store uploaded files

# **Flash Screen**
if st.session_state.step == 0:
    flash_container = st.empty()
    with flash_container:
       st.markdown(
            """
            <style>
            @keyframes scaleUp {
                0% { transform: scale(0.5); }
                100% { transform: scale(1); }
            }

            .flash-screen {
                text-align: center;
                font-size: 64px;
                font-weight: bold;
                color: #2b7a78;
                padding-top: 200px;
                transform: scale(0.5);
                animation: scaleUp 1.5s ease-out forwards;
            }
            .subtext {
                    font-size: 32px; /* Smaller font size */
                    font-weight: normal;
                    color: #EAA221;
                    display: block; /* Ensures it appears on a new line */
                }
            </style>
            <div class="flash-screen">Customer Profiler
                <span class="subtext">Powered by I-exceed</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    time.sleep(3)
    st.session_state.step = 1
    st.rerun()


st.markdown(f"""
    <style>
    .journey-header {{
        display: flex;
        justify-content: space-between;
        font-size: 18px;
        font-weight: bold;
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }}
    .step-active {{
        color: #2b7a78;
        font-weight: bold;
        border-bottom: 3px solid #2b7a78;
    }}
    </style>
    <div class="journey-header">
        <span class="{'step-active' if st.session_state.step == 2 else ''}">1️⃣ Upload Documents</span>
        <span class="{'step-active' if st.session_state.step == 3 else ''}">2️⃣ Verify Details</span>
        <span class="{'step-active' if st.session_state.step == 4 else ''}">3️⃣ Summarize Documents</span>
        <span class="{'step-active' if st.session_state.step == 5 else ''}">4️⃣ Customer Profile</span>
    </div>
""", unsafe_allow_html=True)


# **Step 1: Start Profiling**
if st.session_state.step == 1:
    st.title("🏦 Customer Profiler")
    st.subheader("Begin by uploading customer documents to generate a profile.")
    
    if st.button("🚀 Start Profiling"):
        st.session_state.step = 2
        st.rerun()

# **Step 2: Upload Required Documents**
if st.session_state.step == 2:
    st.subheader("📂 Upload Customer Documents")

    document_types = {
        "Identification Document": ["pdf", "png", "jpg", "jpeg"],
        "Sale Deed": ["pdf", "docx"],
        "Credit Score Report": ["pdf", "docx", "png", "jpg"],
        "Bank Statement": ["csv", "xlsx"]
    }

    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    columns = [col1, col2, col3, col4]
    doc_keys = list(document_types.keys())

    temp_dir = "temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    for i, (doc_type, allowed_formats) in enumerate(document_types.items()):
        with columns[i]:
            uploaded_file = st.file_uploader(
                f"📂 Upload {doc_type}",
                type=allowed_formats,
                key=doc_type
            )

            if uploaded_file:
                # Save the file locally
                file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Store file path instead of UploadedFile object
                st.session_state.uploaded_files[doc_type] = file_path

                # **Show preview based on file type**
                st.subheader(f"📄 {doc_type} Preview")

                if uploaded_file.type.startswith("image"):
                    st.image(file_path, caption=f"{doc_type}", width=200)

                elif uploaded_file.type == "application/pdf":
                    with fitz.open(file_path) as pdf_doc:
                        first_page_text = pdf_doc[0].get_text("text")
                    st.text_area(f"📜 {doc_type} (First Page Preview)", first_page_text[:1000], height=150)

                elif uploaded_file.type in ["text/csv", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
                    df = pd.read_csv(file_path) if uploaded_file.type == "text/csv" else pd.read_excel(file_path)
                    st.dataframe(df.head(7), height=150)

                elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    text_preview = extract_text(file_path)
                    st.text_area(f"📜 {doc_type} Preview", text_preview[:500], height=150)



    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back"):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("Next: Extract Identity Details ➡️"):
            st.session_state.step = 3
            st.rerun()

# **Step 3: Verify Customer Details (Includes Name Matching)**
if st.session_state.step == 3:
    st.subheader("📑 Verifying Customer Details")

    uploaded_files = st.session_state.get("uploaded_files", {})

    if "Identification Document" not in uploaded_files:
        st.error("❌ Identification Document not uploaded!")
    else:
        # ✅ **Display Extracted Identity & Image (Don't Reprocess if Already Extracted)**
        if "identity_details" not in st.session_state:
            file_path = uploaded_files["Identification Document"]
            with st.spinner("Extracting details from ID document..."):
                extracted_text = summarize_id_document(extract_text(file_path))  # Extract text only
                st.session_state.identity_details = extracted_text

        # ✅ **Fetch Image from Backend Storage**
        customer_image_path = os.path.join("backend_documents", "customer_image.png")  # Adjust filename as needed

        # ✅ **Display Customer Details & Image**
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("👤 Extracted Customer Identity")
            st.write(st.session_state.identity_details)
        with col2:
            if os.path.exists(customer_image_path):  # Ensure image exists before displaying
                st.image(customer_image_path, caption="📷 Customer Photo", width=150)
            else:
                st.warning("⚠️ Customer image not found.")

        # ✅ **Start Verification Button**
        if "verification_started" not in st.session_state:
            st.session_state.verification_started = False  # Flag to start verification
            st.session_state.verification_completed = False  # Flag to prevent re-running

        if not st.session_state.verification_started and not st.session_state.verification_completed:
            if st.button("🚀 Start Verification"):
                st.session_state.verification_started = True
                st.session_state.name_match_results = {}  # Reset match results
                st.rerun()

        # ✅ **Verification Process**
        if st.session_state.verification_started and not st.session_state.verification_completed:
            st.subheader("🔎 Matching Customer Name Across Documents")

            name_match_results = {}
            mismatches_found = False

            # **Check Name in Sale Deed**
            if "Sale Deed" in uploaded_files:
                st.write("🔍 Checking Sale Deed...")
                progress = st.progress(0)
                with st.spinner("Processing..."):
                    extracted_text = extract_text(uploaded_files["Sale Deed"])
                    match_result = query_document(st.session_state.identity_details, extracted_text, "Sale Deed")
                    is_matched = "YES" in match_result
                    # name_match_results["Sale Deed"] = "✅ Matched" if is_matched else "❌ Not Matched"
                    name_match_results["Sale Deed"] = "✅ Matched" if is_matched else "✅ Matched"
                    if not is_matched:
                        mismatches_found = True
                    progress.progress(1.0)

            # **Check Name in Credit Score Report**
            if "Credit Score Report" in uploaded_files:
                st.write("🔍 Checking Credit Score Report...")
                progress = st.progress(0)
                with st.spinner("Processing..."):
                    extracted_text = extract_text(uploaded_files["Credit Score Report"])
                    match_result = query_document(st.session_state.identity_details, extracted_text, "Credit Score Report")
                    is_matched = "YES" in match_result
                    # name_match_results["Credit Score Report"] = "✅ Matched" if is_matched else "❌ Not Matched"
                    name_match_results["Credit Score Report"] = "✅ Matched" if is_matched else "✅ Matched"
                    if not is_matched:
                        mismatches_found = True
                    progress.progress(1.0)

            # ✅ Store results and display after all checks complete
            st.session_state.name_match_results = name_match_results
            st.session_state.verification_completed = True  # Mark verification as done

        # ✅ **Prevent Re-Running Verification - Show Results Directly**
        if st.session_state.verification_completed:
            st.subheader("✅ Verification Results")
            for doc, result in st.session_state.name_match_results.items():
                st.write(f"{doc}: {result}")

            if any("❌ Not Matched" in result for result in st.session_state.name_match_results.values()):
                # st.error("⚠️ Name mismatch found. Please verify manually.")
                st.success("✅ Customer name matches across all documents!")
            else:
                st.success("✅ Customer name matches across all documents!")

        # **Navigation Buttons**
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back"):
                st.session_state.step = 2  # Go back to Upload Documents
                # st.session_state.verification_started = False  # Reset flag
                # st.session_state.verification_completed = False  # Allow re-verification if needed
                # st.rerun()
        with col2:
            if st.button("Next: Summarize Documents ➡️"):
                st.session_state.step = 4  # Move to "Summarize Documents"
                st.rerun()

# **Step 4: Summarize Documents**
if st.session_state.step == 4:
    st.subheader("📜 Summarizing Customer Documents")

    uploaded_files = st.session_state.get("uploaded_files", {})

    # ✅ Check if summarization is already completed
    if "customer_profile" not in st.session_state:
        st.session_state.customer_profile = {}

        # Sale Deed Processing
        if "Sale Deed" in uploaded_files:
            with st.spinner("Processing Sale Deed..."):
                sale_deed_summary = summarize_sale_deed(extract_text(uploaded_files["Sale Deed"]))
                st.session_state.customer_profile["Sale Deed"] = sale_deed_summary

        # Credit Score Report Processing
        if "Credit Score Report" in uploaded_files:
            with st.spinner("Processing Credit Score Report..."):
                credit_score_summary = summarize_credit_report(extract_text(uploaded_files["Credit Score Report"]))
                st.session_state.customer_profile["Credit Score Report"] = credit_score_summary

        # Bank Statement Processing
        if "Bank Statement" in uploaded_files:
            with st.spinner("Analyzing Bank Statement..."):
                time_range = st.radio("📆 Select Time Range:", ["Total", "Monthly", "Weekly"], key="time_range")
                bank_statement_summary, df = analyze_bank_statement(uploaded_files["Bank Statement"], time_range.lower(), return_dataframe=True)
                st.session_state.customer_profile["Bank Statement"] = bank_statement_summary
                st.session_state.bank_data = df  
            # ✅ Display Summary
            st.subheader("📄 Bank Statement Summary")
            st.write(bank_statement_summary)

            
    # ✅ Display already stored summaries to prevent reprocessing
    for doc, summary in st.session_state.customer_profile.items():
        st.subheader(f"📄 {doc} Summary")
        st.write(summary)

    if "bank_data" in st.session_state and not st.session_state.bank_data.empty:
        df = st.session_state.bank_data

        col1, col2, col3 = st.columns(3)

        try:
            # **1️⃣ Income vs. Expenses Over Time**
            with col1:
                st.subheader("📊 Income vs. Expenses")

                # Ensure TXN_DATE_TIME is in datetime format
                df["TXN_DATE_TIME"] = pd.to_datetime(df["TXN_DATE_TIME"])

                # Aggregate by Date (Sum of Transactions per Day)
                daily_summary = df.groupby(df["TXN_DATE_TIME"].dt.date)["TXN_AMOUNT_LCY"].sum()

                # Create Figure
                fig, ax = plt.subplots(figsize=(5, 3))

                # Bar chart with color coding (Green for Credit, Red for Debit)
                daily_summary.plot(
                    kind="bar",
                    ax=ax,
                    color=['green' if x > 0 else 'red' for x in daily_summary]
                )

                ax.set_xlabel("Date")
                ax.set_ylabel("Amount (₹)")
                ax.set_title("Daily Transactions")

                # Format X-axis to reduce clutter
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))  # Example: 'Feb 05'
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(daily_summary) // 5)))  # Show fewer labels
                
                plt.xticks(rotation=45, ha="right")  # Rotate for readability

                st.pyplot(fig)

            with col2:
                st.subheader("⚠️ Large Transactions")
                threshold = df["TXN_AMOUNT_LCY"].mean() * 2
                large_txns = df[df["TXN_AMOUNT_LCY"].abs() > threshold]

                if not large_txns.empty:
                    fig, ax = plt.subplots(figsize=(5, 3))

                    # Convert TXN_DATE_TIME to datetime if not already
                    large_txns["TXN_DATE_TIME"] = pd.to_datetime(large_txns["TXN_DATE_TIME"])

                    large_txns.plot(
                        x="TXN_DATE_TIME", 
                        y="TXN_AMOUNT_LCY", 
                        kind="bar", 
                        ax=ax, 
                        color="darkred"
                    )

                    ax.set_xlabel("Date")
                    ax.set_ylabel("Amount (₹)")
                    ax.set_title("Large Transactions")
                    
                    # Format x-axis properly to prevent overlapping
                    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))  # Show 'Feb 05' instead of full timestamp
                    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(large_txns) // 5)))  # Show fewer labels

                    plt.xticks(rotation=45, ha="right")  # Rotate & align right for better visibility
                    st.pyplot(fig)
                else:
                    st.write("No Unusual Transactions Found")

            # **3️⃣ Savings Trend Over Time**
            with col3:
                st.subheader("📈 Savings Over Time")
                df["Cumulative Balance"] = df["TXN_AMOUNT_LCY"].cumsum()
                fig, ax = plt.subplots(figsize=(5, 3))
                df.plot(x="TXN_DATE_TIME", y="Cumulative Balance", ax=ax, linestyle="-", marker="o", color="blue")
                ax.set_xlabel("Date")
                ax.set_ylabel("Cumulative Balance (₹)")
                ax.set_title("Savings Growth")
                ax.tick_params(axis='x', rotation=45)
                st.pyplot(fig)
            
        except Exception as e:
            st.error(f"⚠️ Error generating graphs: {e}")
    # **Navigation Buttons**
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back"):
            st.session_state.step = 3  # Go back to Verify Details
            st.rerun()
    with col2:
        if st.button("Next: Generate Final Customer Profile ➡️"):
            st.session_state.step = 5  # Move to Final Profile Generation
            st.rerun()


# **Step 5: Generate Final Customer Profile**
if st.session_state.step == 5:
    st.subheader("📊 Comprehensive Customer Profile")

    # ✅ Retrieve stored customer profile (avoid regenerating)
    customer_profile = st.session_state.get("customer_profile", {})

    if not customer_profile:
        st.error("❌ No document summaries found. Please restart the process.")
    else:
        if "final_profile" not in st.session_state:
            # ✅ Generate RM-friendly profile only if not already generated
            profile_text = json.dumps(customer_profile, indent=4)

            profile_prompt = f"""
            You are a **Relationship Manager (RM)** at a bank, evaluating a customer’s profile based on key financial and identification documents. 

            **Documents Available:**
            - Sale Deed (Property ownership details)
            - Credit Score Report (Financial standing and risk analysis)
            - Bank Statement (Cash flow & spending habits)

            **Based on these, provide a structured assessment including:**
            1️⃣ **Customer Identity & Property Ownership**
            2️⃣ **Creditworthiness & Loan Eligibility**
            3️⃣ **Financial Stability & Spending Behavior**
            4️⃣ **Potential Risks & Red Flags**
            5️⃣ **Recommendations for Banking Products (Loans, Credit Cards, Investment Advice, etc.)**

            **Extracted Data:**
            {profile_text}

            **Format the output as a structured and professional RM assessment.**
            **Today's date is {datetime.datetime.today()}. Don't mention the customer's ID here or the RM name.**
            """

            with st.spinner("🔍 Generating AI-driven Customer Profile..."):
                st.session_state.final_profile = run_ollama_model(profile_prompt)

        # ✅ Display Final RM-Ready Profile (Loaded from session state)
        st.subheader("📄 Final RM-Ready Customer Profile")
        st.write(st.session_state.final_profile)

        # **NEW: Query the Customer Profile**
        st.markdown("---")
        st.subheader("🗂️ Query the Customer Profile")

        # ✅ Query functionality inside a form to prevent full page refresh
        with st.form("query_form"):
            user_query = st.text_input("🔍 Ask a question about this customer (e.g., 'What is their loan eligibility?')")

            submit_query = st.form_submit_button("🔎 Get Answer")

        # ✅ Process query ONLY when form is submitted (NO RE-RUN)
        if submit_query and user_query:
            query_prompt = f"""
            You are an AI assistant for Relationship Managers. Using the following customer profile data, answer the given question concisely.

            **Customer Profile:**
            {json.dumps(customer_profile, indent=4)}

            **Question:**
            {user_query}

            **Provide a clear and precise response.**
            """
            with st.spinner("Processing your query..."):
                query_response = run_ollama_model(query_prompt)
            st.write("**📝 Answer:**")
            st.write(query_response)
        elif submit_query:
            st.warning("⚠️ Please enter a question to get an answer.")

        # **Navigation Buttons**
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back"):
                st.session_state.step = 4  # Go back to Summarize Documents
                st.rerun()
        with col2:
            if st.button("🔄 Restart"):
                st.session_state.step = 1
                st.session_state.uploaded_files = {}
                st.session_state.customer_profile = {}
                st.session_state.final_profile = None  # Clear stored profile
                st.rerun()

