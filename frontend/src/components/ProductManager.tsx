import React, { useState, useEffect } from 'react';
import { Trash2, Plus, Save, AlertCircle, CheckCircle } from 'lucide-react';

// TypeScript interfaces
interface ProductField {
  name: string;
  type: string;
  required: boolean;
  description: string;
  latvian: string;
}

interface ProductItem {
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
  [key: string]: any; // Allow dynamic fields
}

interface ProductConfig {
  document_types: string[];
  base_fields: ProductField[];
  optional_fields: ProductField[];
  document_specific_fields: Record<string, ProductField[]>;
}

interface ProductManagerProps {
  invoiceId: number;
  documentType?: string;
  onProductsChange?: (products: ProductItem[]) => void;
  readonly?: boolean;
}

export const ProductManager: React.FC<ProductManagerProps> = ({
  invoiceId,
  documentType = "invoice",
  onProductsChange,
  readonly = false
}) => {
  const [products, setProducts] = useState<ProductItem[]>([]);
  const [config, setConfig] = useState<ProductConfig | null>(null);
  const [availableFields, setAvailableFields] = useState<ProductField[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string[]>>({});
  const [summary, setSummary] = useState<string>("");

  // Load product configuration on mount
  useEffect(() => {
    loadProductConfig();
  }, []);

  // Load products when invoice ID changes
  useEffect(() => {
    if (invoiceId) {
      loadProducts();
    }
  }, [invoiceId]);

  // Update available fields when document type changes
  useEffect(() => {
    if (config) {
      updateAvailableFields();
    }
  }, [documentType, config]);

  const loadProductConfig = async () => {
    try {
      const response = await fetch('/api/v1/products/config');
      if (!response.ok) throw new Error('Failed to load config');
      const configData = await response.json();
      setConfig(configData);
    } catch (error) {
      console.error('Failed to load product config:', error);
    }
  };

  const updateAvailableFields = () => {
    if (!config) return;

    const fields = [
      ...config.base_fields,
      ...config.optional_fields,
      ...(config.document_specific_fields[documentType] || [])
    ];
    setAvailableFields(fields);
  };

  const loadProducts = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/products/${invoiceId}`);
      if (!response.ok) throw new Error('Failed to load products');
      const data = await response.json();
      
      setProducts(data.products || []);
      setSummary(data.summary || "Nav produktu");
      setErrors({});
    } catch (error) {
      console.error('Failed to load products:', error);
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  const saveProducts = async () => {
    setSaving(true);
    try {
      const response = await fetch('/api/v1/products/update', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          invoice_id: invoiceId,
          products: products,
          document_type: documentType
        }),
      });

      if (!response.ok) throw new Error('Failed to save products');
      const data = await response.json();

      if (data.success) {
        setProducts(data.products);
        setSummary(data.summary);
        setErrors({});
        onProductsChange?.(data.products);
      } else {
        setErrors(data.errors || {});
      }
    } catch (error) {
      console.error('Failed to save products:', error);
    } finally {
      setSaving(false);
    }
  };

  const addProduct = () => {
    const newProduct: ProductItem = {
      product_name: "",
      quantity: 0,
      unit_price: 0,
      total_price: 0
    };
    setProducts([...products, newProduct]);
  };

  const removeProduct = (index: number) => {
    const newProducts = products.filter((_, i) => i !== index);
    setProducts(newProducts);
  };

  const updateProduct = (index: number, field: string, value: any) => {
    const newProducts = [...products];
    newProducts[index] = { ...newProducts[index], [field]: value };
    
    // Auto-calculate total price
    if (field === 'quantity' || field === 'unit_price') {
      const quantity = field === 'quantity' ? value : newProducts[index].quantity;
      const unitPrice = field === 'unit_price' ? value : newProducts[index].unit_price;
      newProducts[index].total_price = quantity * unitPrice;
    }
    
    setProducts(newProducts);
  };

  const renderFieldInput = (product: ProductItem, field: ProductField, index: number) => {
    const value = product[field.name] || '';
    const fieldId = `${field.name}-${index}`;

    if (field.type === 'number') {
      return (
        <input
          id={fieldId}
          type="number"
          step="0.01"
          value={value}
          onChange={(e) => updateProduct(index, field.name, parseFloat(e.target.value) || 0)}
          disabled={readonly}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      );
    }

    if (field.name === 'unit') {
      return (
        <select
          value={value}
          onChange={(e) => updateProduct(index, field.name, e.target.value)}
          disabled={readonly}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Izvēlieties...</option>
          <option value="gab.">gab.</option>
          <option value="kg">kg</option>
          <option value="m">m</option>
          <option value="m²">m²</option>
          <option value="m³">m³</option>
          <option value="st.">st.</option>
          <option value="pak.">pak.</option>
        </select>
      );
    }

    return (
      <input
        id={fieldId}
        type="text"
        value={value}
        onChange={(e) => updateProduct(index, field.name, e.target.value)}
        disabled={readonly}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
    );
  };


  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
        <div className="p-6">
          <div className="text-center">Ielādē produktus...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-lg font-semibold">Produktu pārvaldība</h3>
              <p className="text-sm text-gray-600">
                Dokumenta tips: <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 border">{documentType}</span>
              </p>
            </div>
            {!readonly && (
              <div className="flex gap-2">
                <button
                  onClick={addProduct}
                  className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <Plus className="w-4 h-4 mr-1" />
                  Pievienot
                </button>
                <button
                  onClick={saveProducts}
                  disabled={saving}
                  className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
                >
                  <Save className="w-4 h-4 mr-1" />
                  {saving ? 'Saglabā...' : 'Saglabāt'}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Summary */}
      {summary && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-start">
            <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 mr-3" />
            <div className="text-sm text-green-800">{summary}</div>
          </div>
        </div>
      )}

      {/* Validation Errors */}
      {Object.keys(errors).length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 mr-3" />
            <div className="text-sm text-red-800">
              <div className="space-y-1">
                {Object.entries(errors).map(([type, messages]) => (
                  <div key={type}>
                    <strong>{type}:</strong> {messages.join(', ')}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Products List */}
      <div className="space-y-4">
        {products.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
            <div className="p-6 text-center text-gray-500">
              Nav pievienotu produktu
            </div>
          </div>
        ) : (
          products.map((product, index) => (
            <div key={index} className="bg-white border border-gray-200 rounded-lg shadow-sm">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex justify-between items-center">
                  <h4 className="font-medium">Produkts #{index + 1}</h4>
                  {!readonly && (
                    <button
                      onClick={() => removeProduct(index)}
                      className="inline-flex items-center px-2 py-1 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
              <div className="p-6 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {availableFields.map((field) => (
                    <div key={field.name} className="space-y-1">
                      <label htmlFor={`${field.name}-${index}`} className="block text-sm font-medium text-gray-700">
                        {field.latvian}
                        {field.required && <span className="text-red-500 ml-1">*</span>}
                      </label>
                      {renderFieldInput(product, field, index)}
                      <p className="text-xs text-gray-500">{field.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
