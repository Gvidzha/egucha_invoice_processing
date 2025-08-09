// Pavadzīmes datu tipi
export interface Invoice {
  id: number;
  filename: string;
  file_path: string;
  file_size: number;
  
  // OCR rezultāti
  extracted_text?: string;
  raw_text?: string;
  ocr_confidence?: number;
  ocr_strategy?: string;
  confidence_score?: number;
  
  // Ekstraktētie dati
  invoice_number?: string;
  supplier_name?: string;
  supplier_confidence?: number;
  reg_number?: string;
  address?: string;
  bank_account?: string;
  
  // Datumi
  invoice_date?: string;
  delivery_date?: string;
  
  // Finanšu dati
  total_amount?: number;
  vat_amount?: number;
  currency: string;
  
  // Statuss
  status: 'uploaded' | 'processing' | 'completed' | 'error';
  error_message?: string;
  
  // Laika zīmogi
  uploaded_at: string;
  started_at?: string;
  created_at: string;
  updated_at: string;
  processed_at?: string;
}

// API atbildes tipi
export interface UploadResponse {
  message: string;
  file_id: number;
  filename: string;
  file_size: number;
  status: string;
}

export interface ProcessResponse {
  message: string;
  file_id: number;
  filename: string;
  status: string;
}

export interface StatusResponse {
  file_id: number;
  filename: string;
  status: 'uploaded' | 'processing' | 'completed' | 'error';
  error_message?: string;
  
  // === TEMPLATE SYSTEM FIELDS (47 fields total) ===
  // Document Information
  document_type?: string;
  document_series?: string;
  invoice_number_number?: string;
  invoice_date?: string;
  delivery_date?: string;
  service_delivery_date?: string;
  contract_number?: string;
  
  // Supplier Information
  supplier_name?: string;
  supplier_reg_number?: string;
  supplier_vat_payer_number?: string;
  supplier_vat_number?: string;
  supplier_legal_address?: string;
  issue_address?: string;
  supplier_account_number?: string;
  supplier_banks?: string;
  
  // Recipient Information
  recipient_name?: string;
  recipient_reg_number?: string;
  recipient_vat_number?: string;
  recipient_legal_address?: string;
  receiving_address?: string;
  recipient_bank_name?: string;
  recipient_account_number?: string;
  recipient_swift_code?: string;
  
  // Transport Information
  carrier_name?: string;
  carrier_vat_number?: string;
  vehicle_number?: string;
  driver_name?: string;
  
  // Financial Information
  currency?: string;
  discount?: number;
  total_with_discount?: number;
  amount_with_discount?: number;
  amount_without_discount?: number;
  amount_without_vat?: number;
  vat_amount?: number;
  total_amount?: number;
  
  // Other Information
  transaction_type?: string;
  service_period?: string;
  payment_method?: string;
  payment_due_date?: string;
  notes?: string;
  issued_by_name?: string;
  justification?: string;
  total_issued?: number;
  weight_kg?: number;
  issued_by?: string;
  total_quantity?: number;
  page_number?: string;
  
  // Quality metrics
  confidence_score?: number;
  ocr_confidence?: number;
}

export interface ResultsResponse {
  invoice: Invoice;
  processing_time: string;
  ocr_text_preview: string;
}

// Komponenšu props tipi
export interface FileUploadProps {
  onFileUploaded: (response: UploadResponse) => void;
  onError: (error: string) => void;
}

export interface ProcessingStatusProps {
  fileId: number;
  onCompleted: (results: StatusResponse) => void;
  onError: (error: string) => void;
}
