import React, { useState } from 'react';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import FileUpload from '../components/FileUpload';
import ProcessingStatus from '../components/ProcessingStatus';
import type { UploadResponse, StatusResponse } from '../types/invoice';
import { InvoiceAPI, handleApiError } from '../services/api';

type Step = 'upload' | 'processing' | 'results';

const UploadPage: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<Step>('upload');
  const [uploadResponse, setUploadResponse] = useState<UploadResponse | null>(null);
  const [processingResults, setProcessingResults] = useState<StatusResponse | null>(null);
  const [error, setError] = useState<string>('');
  const [isStartingProcess, setIsStartingProcess] = useState(false);

  const handleFileUploaded = async (response: UploadResponse) => {
    setUploadResponse(response);
    setError('');
    
    // Automātiski sākt apstrādi
    setIsStartingProcess(true);
    try {
      await InvoiceAPI.processFile(response.file_id);
      setCurrentStep('processing');
    } catch (error) {
      const errorMessage = handleApiError(error);
      setError(`Neizdevās sākt apstrādi: ${errorMessage}`);
    } finally {
      setIsStartingProcess(false);
    }
  };

  const handleProcessingCompleted = (results: StatusResponse) => {
    setProcessingResults(results);
    setCurrentStep('results');
  };

  const handleError = (errorMessage: string) => {
    setError(errorMessage);
  };

  const resetFlow = () => {
    setCurrentStep('upload');
    setUploadResponse(null);
    setProcessingResults(null);
    setError('');
  };

  const getStepNumber = (step: Step): number => {
    switch (step) {
      case 'upload': return 1;
      case 'processing': return 2;
      case 'results': return 3;
    }
  };

  const StepIndicator = ({ step, isActive, isCompleted }: { 
    step: Step; 
    isActive: boolean; 
    isCompleted: boolean; 
  }) => (
    <div className={`flex items-center ${isCompleted || isActive ? 'text-blue-600' : 'text-gray-400'}`}>
      <div className={`
        w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
        ${isCompleted ? 'bg-green-500 text-white' : 
          isActive ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-600'}
      `}>
        {getStepNumber(step)}
      </div>
      <span className="ml-2 font-medium">
        {step === 'upload' && 'Augšupielāde'}
        {step === 'processing' && 'Apstrāde'}
        {step === 'results' && 'Rezultāti'}
      </span>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Pavadzīmju Apstrādes Sistēma
          </h1>
          <p className="text-gray-600">
            Augšupielādējiet pavadzīmi un iegūstiet strukturētus datus ar OCR
          </p>
        </div>

        {/* Step Indicator */}
        <div className="flex justify-center items-center space-x-8 mb-8">
          <StepIndicator 
            step="upload" 
            isActive={currentStep === 'upload'} 
            isCompleted={currentStep !== 'upload'} 
          />
          <ArrowRight className="w-4 h-4 text-gray-400" />
          <StepIndicator 
            step="processing" 
            isActive={currentStep === 'processing'} 
            isCompleted={currentStep === 'results'} 
          />
          <ArrowRight className="w-4 h-4 text-gray-400" />
          <StepIndicator 
            step="results" 
            isActive={currentStep === 'results'} 
            isCompleted={false} 
          />
        </div>

        {/* Error Display */}
        {error && (
          <div className="max-w-lg mx-auto mb-6">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start space-x-2">
                <div className="text-sm text-red-700">
                  <strong>Kļūda:</strong> {error}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Content based on current step */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          {currentStep === 'upload' && (
            <div>
              <h2 className="text-xl font-semibold text-center mb-6">
                Augšupielādējiet pavadzīmi
              </h2>
              
              {isStartingProcess ? (
                <div className="text-center py-8">
                  <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                  <p className="text-gray-600">Sāk apstrādi...</p>
                </div>
              ) : (
                <FileUpload 
                  onFileUploaded={handleFileUploaded} 
                  onError={handleError} 
                />
              )}
            </div>
          )}

          {currentStep === 'processing' && uploadResponse && (
            <div>
              <h2 className="text-xl font-semibold text-center mb-6">
                Apstrādā pavadzīmi
              </h2>
              <ProcessingStatus
                fileId={uploadResponse.file_id}
                filename={uploadResponse.filename}
                onCompleted={handleProcessingCompleted}
                onError={handleError}
              />
            </div>
          )}

          {currentStep === 'results' && processingResults && (
            <div>
              <h2 className="text-xl font-semibold text-center mb-6">
                Apstrādes rezultāti
              </h2>
              
              <div className="max-w-2xl mx-auto">
                <div className="bg-gray-50 rounded-lg p-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {processingResults.invoice_number && (
                      <div className="bg-white p-4 rounded-lg">
                        <label className="text-sm font-medium text-gray-600">Pavadzīmes numurs</label>
                        <p className="text-lg font-semibold">{processingResults.invoice_number}</p>
                      </div>
                    )}
                    
                    {processingResults.supplier_name && (
                      <div className="bg-white p-4 rounded-lg">
                        <label className="text-sm font-medium text-gray-600">Piegādātājs</label>
                        <p className="text-lg font-semibold">{processingResults.supplier_name}</p>
                      </div>
                    )}
                    
                    {processingResults.invoice_date && (
                      <div className="bg-white p-4 rounded-lg">
                        <label className="text-sm font-medium text-gray-600">Datums</label>
                        <p className="text-lg font-semibold">
                          {new Date(processingResults.invoice_date).toLocaleDateString('lv-LV')}
                        </p>
                      </div>
                    )}
                    
                    {processingResults.total_amount && (
                      <div className="bg-white p-4 rounded-lg">
                        <label className="text-sm font-medium text-gray-600">Summa</label>
                        <p className="text-lg font-semibold">
                          {processingResults.total_amount} {processingResults.currency}
                        </p>
                      </div>
                    )}
                    
                    {processingResults.confidence_score && (
                      <div className="bg-white p-4 rounded-lg">
                        <label className="text-sm font-medium text-gray-600">Kvalitāte</label>
                        <p className="text-lg font-semibold">
                          {(processingResults.confidence_score * 100).toFixed(1)}%
                        </p>
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Action buttons */}
                <div className="flex justify-center space-x-4 mt-6">
                  <button
                    onClick={resetFlow}
                    className="flex items-center space-x-2 px-6 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                  >
                    <ArrowLeft className="w-4 h-4" />
                    <span>Jauna pavadzīme</span>
                  </button>
                  
                  <button
                    onClick={() => {
                      // TODO: Implementēt detalizētu rezultātu skatu
                      console.log('Detalizēti rezultāti');
                    }}
                    className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                  >
                    Detalizēti rezultāti
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UploadPage;
