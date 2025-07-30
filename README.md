
# Smart Receipt Manager

## Project Description

The Smart Receipt Manager is a web application built with Django and Django REST Framework that automates the process of managing scanned receipts. It allows users to upload PDF receipts, which are then automatically validated, processed using Google Gemini's native document understanding capabilities to extract key details, and stored efficiently in a SQLite database. The application provides a set of REST APIs for seamless interaction and retrieval of receipt data.

## Features

-   **PDF Upload:** Upload scanned receipts in PDF format.
    
-   **Automated Validation:** Ensures uploaded files are valid PDFs.
    
-   **AI-Powered Data Extraction:** Utilizes Google Gemini's multimodal capabilities to extract key details (merchant name, total amount, purchase date, etc.) directly from PDF documents.
    
-   **Structured Data Storage:** Stores extracted information and file metadata in a SQLite database.
    
-   **RESTful API:** Provides endpoints for uploading, listing, and retrieving receipt data.
    
-   **Categorized Storage:** Organizes uploaded PDF files into local directories based on the year of purchase.
    

## Technologies Used

-   **Backend:** Python 3.9+
    
-   **Web Framework:** Django
    
-   **API Framework:** Django REST Framework (DRF)
    
-   **AI/OCR:** Google Gemini API (`gemini-1.5-flash` for native PDF understanding)
    
-   **PDF Handling:** PyMuPDF (`fitz`) for basic PDF validation
    
-   **Image Processing (Dependency):** Pillow (used by PyMuPDF)
    
-   **Database:** SQLite3
    
-   **CORS Management:** `django-cors-headers`
    

## Setup and Installation

### Prerequisites

1.  **Python 3.9+**: Ensure Python is installed on your system.
    
2.  **Gemini API Key**:
    
    -   Go to **Google AI Studio** [ Api Key](https://aistudio.google.com/app/apikey/ "null").
    -	Click on **Create API Key** 
    -	Select or Create a Project, then generate an **API Key**. Keep this key secure.
    
        

### Installation Steps

1.  **Clone the repository:**
    
    ```
    git clone <git@github.com:Chinmay1903/smart_recept_manager.git>
    cd smart_recept_manager
    
    ```
    
2.  **Create a Python Virtual Environment (Recommended):**
    
    ```
    python -m venv venv
    
    ```
    
3.  **Activate the Virtual Environment:**
    
    -   **On macOS/Linux:**
        
        ```
        source venv/bin/activate
        
        ```
        
    -   **On Windows:**
        
        ```
        .\venv\Scripts\activate
        
        ```
        
4.  Install Python Dependencies:
    
    Change directory to backend
    ```
    cd backend
    ```
    
    Then install them:
    
    ```
    pip install -r requirements.txt
    
    ```
    
5.  Configure Django Settings:
    
    Open receipt_manager/settings.py and set your Google Gemini API key:
    
    ```
    # receipt_manager/settings.py
    
    # ... other settings ...
    
    # --- Google Gemini API Key ---
    GEMINI_API_KEY = "YOUR_GOOGLE_GEMINI_API_KEY_HERE" # <-- REPLACE THIS WITH YOUR ACTUAL API KEY
    # --- End Google Gemini API Key ---
    
    ```
    
6.  **Run Database Migrations:**(Optional as add demo data and db)
    
    ```
    python manage.py makemigrations receipts
    python manage.py migrate
    
    ```

## Running the Application

1.  **Start the Django Development Server:**
    
    ```
    python manage.py runserver
    
    ```
    
    The API will be accessible at `http://127.0.0.1:8000/api/`.
    
2.  **Running the Frontend page**
		Open new terminal on parent directory i.e. smart_recept_manager. Then go inside the frontent directory and run index.html in a browser.
		  

## API Usage

The application exposes the following REST API endpoints:

### 1. Upload & Process Receipt

-   **URL:** `/api/upload/`
    
-   **Method:** `POST`
    
-   **Description:** Uploads a PDF receipt file. The server automatically validates the PDF, extracts details using Google Gemini, and stores the metadata and extracted data in the database.
    
-   **Request Body:** `multipart/form-data` with a file field named `file`.
    
-   **Example Request (using `curl`):**
    
    ```
    curl -X POST -F "file=@/path/to/your/receipt.pdf" http://127.0.0.1:8000/api/upload/
    
    ```
    
-   **Example Success Response (Status: 201 Created):**
    
    ```
    {
        "message": "File uploaded, validated, and processed successfully!",
        "receipt_file": {
            "id": 1,
            "file_name": "your_receipt.pdf",
            "file_path": "receipts/2025/your_receipt_20250730174100123456.pdf",
            "is_valid": true,
            "invalid_reason": null,
            "is_processed": true,
            "created_at": "2025-07-30T17:41:00.123456Z",
            "updated_at": "2025-07-30T17:41:00.123456Z"
        },
        "extracted_receipt": {
            "id": 1,
            "receipt_file": 1,
            "purchased_at": "2025-07-29T00:00:00Z",
            "merchant_name": "ABC Store",
            "total_amount": "123.45",
            "parsed_text": "```json\n{\n  \"merchant_name\": \"ABC Store\",\n  \"purchase_date\": \"2025-07-29\",\n  \"total_amount\": 123.45,\n  \"items\": [\n    {\"description\": \"Item 1\", \"price\": 10.00},\n    {\"description\": \"Item 2\", \"price\": 5.50}\n  ]\n}\n```",
            "created_at": "2025-07-30T17:41:00.123456Z",
            "updated_at": "2025-07-30T17:41:00.123456Z"
        }
    }
    
    ```
    
-   **Example Error Response (Status: 400 Bad Request / 500 Internal Server Error):**
    
    ```
    {
        "message": "File uploaded but is invalid.",
        "receipt_file": {
            "id": 2,
            "file_name": "invalid.pdf",
            "file_path": "receipts/2025/invalid_20250730174200123456.pdf",
            "is_valid": false,
            "invalid_reason": "Invalid PDF file structure or format.",
            "is_processed": false,
            "created_at": "2025-07-30T17:42:00.123456Z",
            "updated_at": "2025-07-30T17:42:00.123456Z"
        }
    }
    
    ```
    
    or
    
    ```
    {
        "error": "An unexpected error occurred during receipt processing: Failed to parse Gemini's JSON response: Expecting value: line 1 column 1 (char 0). Raw response from Gemini: I could not extract the requested JSON from the document."
    }
    
    ```
    

### 2. List All Receipts

-   **URL:** `/api/receipts/`
    
-   **Method:** `GET`
    
-   **Description:** Retrieves a list of all extracted receipt details from the database.
    
-   **Example Request:**
    
    ```
    curl http://127.0.0.1:8000/api/receipts/
    
    ```
    
-   **Example Response (Status: 200 OK):**
    
    ```
    [
        {
            "id": 1,
            "receipt_file": 1,
            "purchased_at": "2025-07-29T00:00:00Z",
            "merchant_name": "ABC Store",
            "total_amount": "123.45",
            "parsed_text": "```json\n{\n  \"merchant_name\": \"ABC Store\",\n  \"purchase_date\": \"2025-07-29\",\n  \"total_amount\": 123.45,\n  \"items\": [\n    {\"description\": \"Item 1\", \"price\": 10.00},\n    {\"description\": \"Item 2\", \"price\": 5.50}\n  ]\n}\n```",
            "created_at": "2025-07-30T17:41:00.123456Z",
            "updated_at": "2025-07-30T17:41:00.123456Z",
            "receipt_file_details": {
                "id": 1,
                "file_name": "your_receipt.pdf",
                "file_path": "receipts/2025/your_receipt_20250730174100123456.pdf",
                "is_valid": true,
                "invalid_reason": null,
                "is_processed": true,
                "created_at": "2025-07-30T17:41:00.123456Z",
                "updated_at": "2025-07-30T17:41:00.123456Z"
            }
        }
    ]
    
    ```
    

### 3. Retrieve Specific Receipt

-   **URL:** `/api/receipts/{id}/`
    
-   **Method:** `GET`
    
-   **Description:** Retrieves detailed information for a specific receipt by its ID.
    
-   **Path Parameters:**
    
    -   `id` (integer): The ID of the `Receipt` object.
        
-   **Example Request:**
    
    ```
    curl http://127.0.0.1:8000/api/receipts/1/
    
    ```
    
-   Example Response (Status: 200 OK):
    
    (Same as a single object in the "List All Receipts" response above)
    
-   **Example Error Response (Status: 404 Not Found):**
    
    ```
    {
        "error": "Receipt not found"
    }
    
    ```
    

## Execution Instructions – Specific Setup Steps to Test Your Implementation

1.  **Follow all "Setup and Installation" steps meticulously.** The most critical parts are:
    
    -   **Correctly setting `GEMINI_API_KEY`** in `settings.py`.
        
    -   **Ensuring billing is enabled** on your Google Cloud project for Gemini API access.
        
    -   **Running `python manage.py migrate`** after any model changes.
        
2.  **Prepare Test PDF Receipts:**
    
    -   Start with simple, digitally generated PDFs (e.g., create a text file with "Merchant: Test Store\nTotal: 100.00\nDate: 2025-07-29" and "Print to PDF"). These are easiest for AI models to parse.
        
    -   Gradually test with scanned receipts of varying quality. Note that the accuracy of extraction heavily depends on the clarity and layout of the scanned document.
        
3.  **Use the Provided Frontend (`index.html`):**
    
    -   Open the `index.html` file (from the previous steps) in your web browser. This provides a simple interface to upload files and view results.
        
    -   Make sure `API_BASE_URL` in `index.html` matches your Django server's address (`http://127.0.0.1:8000/api`).
        
4.  **Monitor Server Console:**
    
    -   Keep the terminal where you run `python manage.py runserver` open. Any errors or debug messages (if you re-enable them) from the backend will appear here.
        
6.  **Review `media/receipts/` directory:**
    
    -   Verify that your uploaded PDF files are being saved correctly in year-based subdirectories within your `media` folder.
        

By following these instructions, you should be able to effectively test and verify the functionality of your Smart Receipt Manager.