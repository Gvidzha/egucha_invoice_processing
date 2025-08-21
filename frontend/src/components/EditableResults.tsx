import React, { useState } from 'react';
import { Save, Edit3, X, AlertCircle } from 'lucide-react';
import { ProductManager } from './ProductManager';
import { InvoiceAPI } from '../services/api';

interface EditableResultsProps {
  fileId: number;
  initialData: any;
  onDataUpdated: (data: any) => void;
  onError: (error: string) => void;
}

// PILNĪGS LAUKU KARTĒJUMS AR LATVIEŠU LABELS
const editableFields = [
  // === DOKUMENTA INFORMĀCIJA ===
  { key: 'document_type', label: 'Dokumenta veids', type: 'text', section: 'document' },
  { key: 'document_series', label: 'Dokumenta sērija', type: 'text', section: 'document' },
  { key: 'document_number', label: 'Dokumenta numurs', type: 'text', section: 'document', required: true },
  { key: 'invoice_date', label: 'Izrakstīšanas datums', type: 'date', section: 'document' },
  { key: 'delivery_date', label: 'Piegādes datums', type: 'date', section: 'document' },
  { key: 'service_delivery_date', label: 'Pakalpojuma sniegšanas datums', type: 'date', section: 'document' },
  { key: 'contract_number', label: 'Līguma numurs', type: 'text', section: 'document' },
  
  // === PIEGĀDĀTĀJA INFORMĀCIJA ===
  { key: 'supplier_name', label: 'Piegādātāja nosaukums', type: 'text', section: 'supplier', required: true },
  { key: 'supplier_registration_number', label: 'Piegādātāja reģ. numurs', type: 'text', section: 'supplier' },
  { key: 'supplier_vat_payer_number', label: 'Piegādātāja PVN maksātāja Nr.', type: 'text', section: 'supplier' },
  { key: 'supplier_vat_number', label: 'Piegādātāja PVN numurs', type: 'text', section: 'supplier' },
  { key: 'supplier_legal_address', label: 'Piegādātāja juridiskā adrese', type: 'text', section: 'supplier' },
  { key: 'issue_address', label: 'Izdošanas adrese', type: 'text', section: 'supplier' },
  
  // === PIEGĀDĀTĀJA BANKAS (GALVENĀ) ===
  { key: 'supplier_bank_name', label: 'Piegādātāja banka', type: 'text', section: 'supplier' },
  { key: 'supplier_account_number', label: 'Piegādātāja konts', type: 'text', section: 'supplier' },
  { key: 'supplier_swift_code', label: 'Piegādātāja SWIFT', type: 'text', section: 'supplier' },
  
  // === PIEGĀDĀTĀJA PAPILDU BANKAS ===
  { key: 'supplier_bank_name_1', label: 'Piegādātāja banka 2', type: 'text', section: 'supplier_banks' },
  { key: 'supplier_account_number_1', label: 'Piegādātāja konts 2', type: 'text', section: 'supplier_banks' },
  { key: 'supplier_swift_code_1', label: 'Piegādātāja SWIFT 2', type: 'text', section: 'supplier_banks' },
  { key: 'supplier_bank_name_2', label: 'Piegādātāja banka 3', type: 'text', section: 'supplier_banks' },
  { key: 'supplier_account_number_2', label: 'Piegādātāja konts 3', type: 'text', section: 'supplier_banks' },
  { key: 'supplier_swift_code_2', label: 'Piegādātāja SWIFT 3', type: 'text', section: 'supplier_banks' },
  { key: 'supplier_bank_name_3', label: 'Piegādātāja banka 4', type: 'text', section: 'supplier_banks' },
  { key: 'supplier_account_number_3', label: 'Piegādātāja konts 4', type: 'text', section: 'supplier_banks' },
  { key: 'supplier_swift_code_3', label: 'Piegādātāja SWIFT 4', type: 'text', section: 'supplier_banks' },
  { key: 'supplier_bank_name_4', label: 'Piegādātāja banka 5', type: 'text', section: 'supplier_banks' },
  { key: 'supplier_account_number_4', label: 'Piegādātāja konts 5', type: 'text', section: 'supplier_banks' },
  { key: 'supplier_swift_code_4', label: 'Piegādātāja SWIFT 5', type: 'text', section: 'supplier_banks' },
  
  // === SAŅĒMĒJA INFORMĀCIJA ===
  { key: 'recipient_name', label: 'Saņēmēja nosaukums', type: 'text', section: 'recipient' },
  { key: 'recipient_registration_number', label: 'Saņēmēja reģ. numurs', type: 'text', section: 'recipient' },
  { key: 'recipient_vat_number', label: 'Saņēmēja PVN numurs', type: 'text', section: 'recipient' },
  { key: 'recipient_legal_address', label: 'Saņēmēja juridiskā adrese', type: 'text', section: 'recipient' },
  { key: 'receiving_address', label: 'Saņemšanas adrese', type: 'text', section: 'recipient' },
  
  // === SAŅĒMĒJA BANKAS ===
  { key: 'recipient_bank_name', label: 'Saņēmēja bankas nosaukums', type: 'text', section: 'recipient' },
  { key: 'recipient_account_number', label: 'Saņēmēja konta numurs', type: 'text', section: 'recipient' },
  { key: 'recipient_swift_code', label: 'Saņēmēja SWIFT kods', type: 'text', section: 'recipient' },
  
  // === TRANSPORTA INFORMĀCIJA ===
  { key: 'carrier_name', label: 'Pārvadātāja nosaukums', type: 'text', section: 'transport' },
  { key: 'carrier_vat_number', label: 'Pārvadātāja PVN numurs', type: 'text', section: 'transport' },
  { key: 'vehicle_number', label: 'Transportlīdzekļa numurs', type: 'text', section: 'transport' },
  { key: 'driver_name', label: 'Vadītāja vārds', type: 'text', section: 'transport' },
  
  // === DARĪJUMA INFORMĀCIJA ===
  { key: 'transaction_type', label: 'Darījuma veids', type: 'text', section: 'transaction' },
  { key: 'service_period', label: 'Pakalpojuma periods', type: 'text', section: 'transaction' },
  { key: 'payment_method', label: 'Apmaksas veids', type: 'text', section: 'transaction' },
  { key: 'notes', label: 'Piezīmes', type: 'textarea', section: 'transaction' },
  
  // === FINANŠU INFORMĀCIJA ===
  { key: 'currency', label: 'Valūta', type: 'text', section: 'financial' },
  { key: 'discount', label: 'Atlaide', type: 'number', section: 'financial' },
  { key: 'total_with_discount', label: 'Kopā ar atlaidi', type: 'number', section: 'financial' },
  { key: 'amount_with_discount', label: 'Summa ar atlaidi', type: 'number', section: 'financial' },
  { key: 'amount_without_discount', label: 'Summa bez atlaides', type: 'number', section: 'financial' },
  { key: 'amount_without_vat', label: 'Summa bez PVN', type: 'number', section: 'financial' },
  { key: 'vat_amount', label: 'PVN summa', type: 'number', section: 'financial' },
  { key: 'total_amount', label: 'Kopējā summa', type: 'number', section: 'financial' },
  
  // === PAPILDU INFORMĀCIJA ===
  { key: 'issued_by_name', label: 'Izsniedza (vārds, uzvārds)', type: 'text', section: 'additional' },
  { key: 'payment_due_date', label: 'Apmaksāt līdz', type: 'date', section: 'additional' },
  { key: 'justification', label: 'Pamatojums', type: 'textarea', section: 'additional' },
  { key: 'total_issued', label: 'Kopā izsniegts', type: 'number', section: 'additional' },
  { key: 'weight_kg', label: 'Svars (kg)', type: 'number', section: 'additional' },
  { key: 'issued_by', label: 'Izsniedza', type: 'text', section: 'additional' },
  { key: 'total_quantity', label: 'Kopējais daudzums', type: 'number', section: 'additional' },
  { key: 'page_number', label: 'Lapas numurs', type: 'text', section: 'additional' },
];

// Sadaļu virsraksti
const sectionTitles: Record<string, string> = {
  document: '📄 Dokumenta informācija',
  supplier: '🏢 Piegādātāja informācija',
  supplier_banks: '🏦 Piegādātāja papildu bankas',
  recipient: '🎯 Saņēmēja informācija',
  transport: '🚛 Transporta informācija',
  transaction: '💼 Darījuma informācija',
  financial: '💰 Finanšu informācija',
  additional: '📋 Papildu informācija'
};

const EditableResults: React.FC<EditableResultsProps> = ({
  fileId,
  initialData,
  onDataUpdated,
  onError
}) => {
  const [editedData, setEditedData] = useState<any>(initialData);
  const [isEditing, setIsEditing] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Apstrādā lauka izmaiņu
  const handleFieldChange = (fieldKey: string, value: any) => {
    setEditedData((prev: any) => ({
      ...prev,
      [fieldKey]: value
    }));
    setHasChanges(true);
  };

  // Sāk labošanas režīmu
  const handleStartEdit = () => {
    setIsEditing(true);
    setHasChanges(false);
  };

  // Atceļ labošanu
  const handleCancelEdit = () => {
    setEditedData(initialData);
    setIsEditing(false);
    setHasChanges(false);
  };

  // Saglabā izmaiņas
  const handleSaveChanges = async () => {
    if (!hasChanges) {
      return;
    }

    setIsSaving(true);
    try {
      // Izmanto InvoiceAPI lai saglabātu labojumus
      const result = await InvoiceAPI.updateInvoiceWithCorrections(fileId, editedData);
      
      // Atjaunina datus ar servera atbildi
      onDataUpdated(result);
      setIsEditing(false);
      setHasChanges(false);
      
      // Parāda veiksmes paziņojumu
      const updatedCount = result.updated_fields?.length || 0;
      console.log('✅ Dati veiksmīgi saglabāti:', result);
      
      // Izveidot un parādīt veiksmes paziņojumu
      if (result.status === 'success') {
        alert(`🎉 Veiksmīgi saglabātas ${updatedCount} izmaiņas!\n\nAtjauninātie lauki: ${result.updated_fields?.join(', ') || 'nav'}`);
      }
      
    } catch (error: any) {
      console.error('Saglabāšanas kļūda:', error);
      onError(`Saglabāšanas kļūda: ${error.message || 'Nezināma kļūda'}`);
    } finally {
      setIsSaving(false);
    }
  };

  // Renderē lauka ievades elementi
  const renderField = (field: any) => {
    const value = editedData[field.key] || '';
    
    if (!isEditing) {
      return (
        <span className="text-gray-900">
          {value || <span className="text-gray-400">Nav norādīts</span>}
        </span>
      );
    }

    if (field.type === 'textarea') {
      return (
        <textarea
          value={value}
          onChange={(e) => handleFieldChange(field.key, e.target.value)}
          className={`w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            field.required && !value ? 'border-red-300' : 'border-gray-300'
          }`}
          placeholder={field.label}
          rows={3}
          required={field.required}
        />
      );
    }

    return (
      <input
        type={field.type}
        value={value}
        onChange={(e) => handleFieldChange(field.key, e.target.value)}
        className={`w-full px-3 py-1 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 ${
          field.required && !value ? 'border-red-300' : 'border-gray-300'
        }`}
        placeholder={field.label}
        required={field.required}
      />
    );
  };

  // Grupē laukus pēc sadaļām
  const fieldsBySection = editableFields.reduce((acc, field) => {
    if (!acc[field.section]) {
      acc[field.section] = [];
    }
    acc[field.section].push(field);
    return acc;
  }, {} as Record<string, any[]>);

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">
          Ekstraktētie dati (Pilnīga shēma)
        </h2>
        
        <div className="flex items-center space-x-2">
          {!isEditing ? (
            <button
              onClick={handleStartEdit}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Edit3 className="w-4 h-4" />
              <span>Labot</span>
            </button>
          ) : (
            <div className="flex items-center space-x-2">
              <button
                onClick={handleCancelEdit}
                className="flex items-center space-x-2 px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
              >
                <X className="w-4 h-4" />
                <span>Atcelt</span>
              </button>
              
              <button
                onClick={handleSaveChanges}
                disabled={!hasChanges || isSaving}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                  hasChanges && !isSaving
                    ? 'bg-green-600 text-white hover:bg-green-700'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                {isSaving ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Saglabā...</span>
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    <span>Saglabāt</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Editable Fields - Organized by Sections */}
      <div className="space-y-8">
        {Object.entries(fieldsBySection).map(([sectionKey, fields]) => (
          <div key={sectionKey} className={`rounded-lg p-4 ${
            sectionKey === 'document' ? 'bg-gray-50' :
            sectionKey === 'supplier' ? 'bg-blue-50' :
            sectionKey === 'supplier_banks' ? 'bg-indigo-50' :
            sectionKey === 'recipient' ? 'bg-green-50' :
            sectionKey === 'transport' ? 'bg-yellow-50' :
            sectionKey === 'transaction' ? 'bg-purple-50' :
            sectionKey === 'financial' ? 'bg-pink-50' :
            'bg-orange-50'
          }`}>
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              {sectionTitles[sectionKey]}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {fields.map((field) => (
                <div key={field.key} className="space-y-1">
                  <label className="text-sm font-medium text-gray-600">
                    {field.label}
                    {field.required && <span className="text-red-500 ml-1">*</span>}
                  </label>
                  <div className="min-h-[2rem] flex items-center">
                    {renderField(field)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* 🆕 PRODUKTU PĀRVALDĪBA */}
      <div className="mt-8">
        <ProductManager
          invoiceId={initialData?.id || fileId}
          documentType={initialData?.document_type || 'invoice'}
          readonly={!isEditing}
          onProductsChange={(products) => {
            // Atjaunina kopējos produktu datus
            console.log('Produkti atjaunināti:', products);
          }}
        />
      </div>

      {/* Instructions */}
      {isEditing && (
        <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start space-x-2">
            <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
            <div className="text-sm text-blue-800">
              <p className="font-medium mb-1">Labošanas instrukcijas:</p>
              <ul className="list-disc list-inside space-y-1">
                <li>Labojiet nepareizi atpazītos datus</li>
                <li>Sistēma automātiski mācīsies no jūsu labojumiem</li>
                <li>Obligātie lauki: Dokumenta numurs un Piegādātāja nosaukums</li>
                <li>Izmaiņas tiks saglabātas datubāzē un uzlabos AI modeli</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EditableResults;
