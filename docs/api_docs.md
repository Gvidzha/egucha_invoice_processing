# API Dokumentācija

## Invoice Processing API v1.0.0

Pavadzīmju apstrādes sistēmas REST API dokumentācija.

### Base URL
```
http://localhost:8000/api/v1
```

## Endpoints

### 1. Upload Endpoints

#### POST /upload
Augšupielādē pavadzīmes failu

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@invoice.jpg"
```

**Response:**
```json
{
  "success": true,
  "file_id": 123,
  "filename": "invoice.jpg",
  "file_size": 1048576,
  "status": "uploaded"
}
```

#### POST /upload/multiple
Augšupielādē vairākus failus vienlaicīgi

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/upload/multiple" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@invoice1.jpg" \
  -F "files=@invoice2.pdf"
```

### 2. Processing Endpoints

#### POST /process/{file_id}
Sāk pavadzīmes apstrādi ar OCR

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/process/123"
```

**Response:**
```json
{
  "file_id": 123,
  "status": "processing_started",
  "estimated_time": "30s"
}
```

#### GET /process/{file_id}/status
Pārbauda apstrādes statusu

**Response:**
```json
{
  "file_id": 123,
  "status": "processing", // uploaded, processing, completed, error
  "progress": 65,
  "error_message": null
}
```

### 3. Preview Endpoints

#### GET /preview/{file_id}
Iegūst apstrādātos datus priekšskatījumam

**Response:**
```json
{
  "id": 123,
  "filename": "invoice.jpg",
  "supplier_name": "SIA Piemērs",
  "supplier_confidence": 0.89,
  "invoice_date": "2024-01-15",
  "delivery_date": "2024-01-16",
  "total_amount": 125.50,
  "currency": "EUR",
  "products": [
    {
      "name": "Produkts 1",
      "quantity": 2,
      "unit_price": 50.25,
      "total_price": 100.50
    }
  ],
  "confidence_scores": {
    "supplier": 0.89,
    "date": 0.95,
    "total": 0.87,
    "overall": 0.90
  }
}
```

#### PUT /preview/{file_id}
Saglabā lietotāja labojumus

**Request:**
```json
{
  "supplier_name": "SIA Labotais Nosaukums",
  "invoice_date": "2024-01-15",
  "total_amount": 130.00,
  "products": [
    {
      "name": "Labotais produkts",
      "quantity": 2,
      "unit_price": 65.00,
      "total_price": 130.00
    }
  ],
  "correction_notes": "Laboju piegādātāja nosaukumu"
}
```

### 4. History Endpoints

#### GET /history
Iegūst pavadzīmju vēsturi

**Query Parameters:**
- `skip` (int): Pagination offset
- `limit` (int): Max results (default: 50)
- `status` (string): Filter by status
- `supplier` (string): Filter by supplier
- `date_from` (date): From date
- `date_to` (date): To date

**Response:**
```json
{
  "invoices": [
    {
      "id": 123,
      "filename": "invoice.jpg",
      "supplier_name": "SIA Piemērs",
      "total_amount": 125.50,
      "status": "completed",
      "processed_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "pages": 3
}
```

#### GET /stats
Iegūst apstrādes statistiku

**Response:**
```json
{
  "total_processed": 1250,
  "successful": 1180,
  "failed": 70,
  "manually_corrected": 320,
  "avg_confidence": 0.87,
  "processing_time_avg": 25.3,
  "top_suppliers": [
    {"name": "SIA A", "count": 45},
    {"name": "SIA B", "count": 32}
  ]
}
```

## Error Responses

Visi endpoints var atgriezt šādas kļūdas:

### 400 Bad Request
```json
{
  "error": "Invalid file format",
  "details": "Only JPG, PNG, PDF files are allowed"
}
```

### 404 Not Found
```json
{
  "error": "File not found",
  "file_id": 123
}
```

### 422 Validation Error
```json
{
  "error": "Validation failed",
  "details": [
    {
      "field": "file_size",
      "message": "File too large"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "error": "Processing failed",
  "message": "OCR service unavailable"
}
```

## Rate Limiting

- Upload endpoints: 10 requests/minute
- Processing endpoints: 5 requests/minute  
- Other endpoints: 60 requests/minute

## Authentication

MVP versijā autentifikācija nav implementēta. Production versijā būs JWT token based authentication.
