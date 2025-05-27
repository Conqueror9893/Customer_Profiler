// Backend API endpoint
const API_BASE_URL = "http://192.168.11.21:8080";  // Change this based on your backend setup

// Step 1: Verify Documents
function verifyDocuments() {
    fetch(`${API_BASE_URL}/verify-documents`)
        .then(response => response.json())
        .then(data => {
            let statusDiv = document.getElementById("verification-status");
            statusDiv.innerHTML = ""; // Clear previous results
            
            if (data.all_docs_uploaded) {
                statusDiv.innerHTML += "<p style='color:green;'>✅ All documents are uploaded!</p>";
                document.getElementById("customer-info").style.display = "block"; // Show next step
            } else {
                statusDiv.innerHTML += `<p style='color:red;'>⚠️ Missing Documents: ${data.missing_files.join(", ")}</p>`;
            }
        })
        .catch(error => {
            console.error("Error verifying documents:", error);
            document.getElementById("verification-status").innerHTML = "<p style='color:red;'>❌ Error verifying documents.</p>";
        });
}

// Step 2: Extract Customer ID Details
function matchCustomerDetails() {
    fetch(`${API_BASE_URL}/extract-id-details`)
        .then(response => response.json())
        .then(data => {
            let detailsDiv = document.getElementById("customer-details");
            detailsDiv.innerHTML = `
                <p><strong>Name:</strong> ${data.name}</p>
                <p><strong>Address:</strong> ${data.address}</p>
                <p><strong>Gender:</strong> ${data.gender}</p>
            `;
            document.getElementById("document-matching").style.display = "block"; // Show next step
        })
        .catch(error => {
            console.error("Error extracting ID details:", error);
            document.getElementById("customer-details").innerHTML = "<p style='color:red;'>❌ Error extracting details.</p>";
        });
}

// Step 3: Match Details Across Documents
function generateCustomerProfile() {
    fetch(`${API_BASE_URL}/generate-customer-profile`)
        .then(response => response.json())
        .then(data => {
            let profileDiv = document.getElementById("profile-summary");
            profileDiv.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
            document.getElementById("final-profile").style.display = "block"; // Show final profile
        })
        .catch(error => {
            console.error("Error generating profile:", error);
            document.getElementById("profile-summary").innerHTML = "<p style='color:red;'>❌ Error generating profile.</p>";
        });
}
