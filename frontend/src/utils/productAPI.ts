/**
 * Product API utilities - Frontend service for product management
 */

// Types
export interface ProductField {
  name: string;
  type: string;
  required: boolean;
  description: string;
  latvian: string;
}

export interface ProductItem {
  product_name: string;
  quantity: number;
  unit?: string;
  unit_price: number;
  total_price: number;
  discount?: number;
  vat_rate?: number;
  vat_amount?: number;
  description?: string;
  product_code?: string;
  [key: string]: any;
}

export interface ProductConfig {
  document_types: string[];
  base_fields: ProductField[];
  optional_fields: ProductField[];
  document_specific_fields: Record<string, ProductField[]>;
}

export interface ProductsResponse {
  success: boolean;
  message: string;
  products: ProductItem[];
  total_products: number;
  summary: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: Record<string, string[]>;
  normalized_products: ProductItem[];
  total_products: number;
  document_type: string;
}

// API service class
export class ProductAPIService {
  private baseURL = '/api/v1/products';

  /**
   * Get product configuration
   */
  async getConfig(): Promise<ProductConfig> {
    const response = await fetch(`${this.baseURL}/config`);
    if (!response.ok) {
      throw new Error(`Failed to get config: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Get fields for specific document type
   */
  async getFieldsForDocument(documentType: string): Promise<{
    document_type: string;
    fields: ProductField[];
    total_fields: number;
  }> {
    const response = await fetch(`${this.baseURL}/fields/${documentType}`);
    if (!response.ok) {
      throw new Error(`Failed to get fields: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Get JSON schema for document type
   */
  async getSchema(documentType: string): Promise<{
    document_type: string;
    schema: any;
  }> {
    const response = await fetch(`${this.baseURL}/schema/${documentType}`);
    if (!response.ok) {
      throw new Error(`Failed to get schema: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Get products for invoice
   */
  async getProducts(invoiceId: number): Promise<ProductsResponse> {
    const response = await fetch(`${this.baseURL}/${invoiceId}`);
    if (!response.ok) {
      throw new Error(`Failed to get products: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Update products for invoice
   */
  async updateProducts(
    invoiceId: number,
    products: ProductItem[],
    documentType: string = 'invoice'
  ): Promise<ProductsResponse> {
    const response = await fetch(`${this.baseURL}/update`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        invoice_id: invoiceId,
        products: products,
        document_type: documentType,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to update products: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Validate products without saving
   */
  async validateProducts(
    products: ProductItem[],
    documentType: string = 'invoice'
  ): Promise<ValidationResult> {
    const response = await fetch(`${this.baseURL}/validate?document_type=${documentType}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(products),
    });

    if (!response.ok) {
      throw new Error(`Failed to validate products: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Get Latvian mappings
   */
  async getLatvianMappings(): Promise<{
    mappings: Record<string, string>;
    total_mappings: number;
  }> {
    const response = await fetch(`${this.baseURL}/mappings/latvian`);
    if (!response.ok) {
      throw new Error(`Failed to get mappings: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Clear all products from invoice
   */
  async clearProducts(invoiceId: number): Promise<{
    success: boolean;
    message: string;
    invoice_id: number;
  }> {
    const response = await fetch(`${this.baseURL}/${invoiceId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`Failed to clear products: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Get raw product data (debug)
   */
  async getRawProductData(invoiceId: number): Promise<{
    invoice_id: number;
    product_items_raw: string | null;
    product_summary: string | null;
    product_schema_version: string | null;
  }> {
    const response = await fetch(`${this.baseURL}/debug/${invoiceId}/raw`);
    if (!response.ok) {
      throw new Error(`Failed to get raw data: ${response.statusText}`);
    }
    return response.json();
  }
}

// Utility functions
export const productAPI = new ProductAPIService();

/**
 * Calculate total price from quantity and unit price
 */
export function calculateTotalPrice(quantity: number, unitPrice: number, discount: number = 0): number {
  const subtotal = quantity * unitPrice;
  return subtotal - (subtotal * discount / 100);
}

/**
 * Calculate VAT amount
 */
export function calculateVATAmount(totalPrice: number, vatRate: number): number {
  return totalPrice * (vatRate / 100);
}

/**
 * Format product summary
 */
export function formatProductSummary(products: ProductItem[]): string {
  if (products.length === 0) return "Nav produktu";

  const totalItems = products.length;
  const totalAmount = products.reduce((sum, p) => sum + (p.total_price || 0), 0);
  
  const itemNames = products
    .slice(0, 3)
    .map(p => `${p.product_name} (${p.quantity} ${p.unit || 'gab.'})`);

  let summary = `Produkti: ${totalItems} | Kopsumma: ${totalAmount.toFixed(2)} | `;
  summary += `Saraksts: ${itemNames.join(', ')}`;

  if (products.length > 3) {
    summary += ` un vēl ${products.length - 3}`;
  }

  return summary;
}

/**
 * Validate single product
 */
export function validateProduct(product: ProductItem, requiredFields: string[]): string[] {
  const errors: string[] = [];

  // Check required fields
  for (const field of requiredFields) {
    if (!product[field] || product[field] === '') {
      errors.push(`Lauks "${field}" ir obligāts`);
    }
  }

  // Validate numbers
  if (product.quantity && product.quantity <= 0) {
    errors.push('Daudzumam jābūt lielākam par 0');
  }

  if (product.unit_price && product.unit_price <= 0) {
    errors.push('Vienības cenai jābūt lielākai par 0');
  }

  // Validate total price calculation
  if (product.quantity && product.unit_price && product.total_price) {
    const expectedTotal = product.quantity * product.unit_price;
    if (Math.abs(product.total_price - expectedTotal) > 0.01) {
      errors.push('Kopsumma neatbilst aprēķinātajai vērtībai');
    }
  }

  return errors;
}

/**
 * Create empty product with default values
 */
export function createEmptyProduct(): ProductItem {
  return {
    product_name: '',
    quantity: 0,
    unit: 'gab.',
    unit_price: 0,
    total_price: 0,
  };
}

/**
 * Normalize product data
 */
export function normalizeProduct(product: Partial<ProductItem>): ProductItem {
  const normalized: ProductItem = {
    product_name: product.product_name || '',
    quantity: Number(product.quantity) || 0,
    unit: product.unit || 'gab.',
    unit_price: Number(product.unit_price) || 0,
    total_price: Number(product.total_price) || 0,
  };

  // Copy optional fields
  const optionalFields = ['discount', 'vat_rate', 'vat_amount', 'description', 'product_code'];
  for (const field of optionalFields) {
    if (product[field] !== undefined) {
      normalized[field] = product[field];
    }
  }

  // Auto-calculate total if missing
  if (!normalized.total_price && normalized.quantity && normalized.unit_price) {
    normalized.total_price = normalized.quantity * normalized.unit_price;
  }

  return normalized;
}

/**
 * Convert Latvian field names to English
 */
export function convertLatvianToEnglish(
  data: Record<string, any>,
  mappings: Record<string, string>
): ProductItem {
  const converted: any = {};

  for (const [latvian, english] of Object.entries(mappings)) {
    if (data[latvian] !== undefined) {
      converted[english] = data[latvian];
    }
  }

  return normalizeProduct(converted);
}

// Export default API service instance
export default productAPI;
