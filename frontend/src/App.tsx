import { useState } from 'react'
import FileUpload from './components/FileUpload'
import ProcessingStatus from './components/ProcessingStatus'
import EditableResults from './components/EditableResults'
import { Upload, FileX, CheckCircle, AlertCircle } from 'lucide-react'
import { UploadResponse, StatusResponse } from './types/invoice'
import { InvoiceAPI } from './services/api'
import './styles.css'

function App() {
  const [uploadedFile, setUploadedFile] = useState<UploadResponse | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [completedResults, setCompletedResults] = useState<StatusResponse | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const handleFileUploaded = async (response: UploadResponse) => {
    setUploadedFile(response)
    setError(null)
    setCompletedResults(null)
    
    try {
      // Palaižam OCR procesu
      await InvoiceAPI.processFile(response.file_id)
      setIsProcessing(true)
    } catch (error) {
      setError('Neizdevās palaist OCR procesu')
      setIsProcessing(false)
    }
  }

  const handleError = (errorMessage: string) => {
    setError(errorMessage)
    setIsProcessing(false)
  }

  const handleProcessingCompleted = (results: StatusResponse) => {
    setCompletedResults(results)
    setIsProcessing(false)
  }

  const handleDataUpdated = (updatedData: StatusResponse) => {
    setCompletedResults(updatedData)
    setError(null) // Dzēst iepriekšējās kļūdas
    
    // Parādīt paziņojumu par veiksmīgu atjaunināšanu (ja ir backend atbilde)
    if (updatedData && typeof updatedData === 'object' && 'status' in updatedData) {
      const result = updatedData as any;
      if (result.status === 'success' && result.updated_fields) {
        setSuccessMessage(`🎉 Veiksmīgi saglabātas ${result.updated_fields.length} izmaiņas: ${result.updated_fields.join(', ')}`);
        // Dzēst success ziņojumu pēc 5 sekundēm
        setTimeout(() => setSuccessMessage(null), 5000);
      }
    }
  }

  const resetApp = () => {
    setUploadedFile(null)
    setIsProcessing(false)
    setError(null)
    setCompletedResults(null)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-600 rounded-lg">
                <FileX className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Pavadzīmju OCR Apstrāde
                </h1>
                <p className="text-sm text-gray-600">
                  Pavadzīmju apstrāde ar OCR un mašīnmācīšanos
                </p>
              </div>
            </div>
            
            {(uploadedFile || error) && (
              <button
                onClick={resetApp}
                className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Jauns fails
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Status Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className={`p-2 rounded-full ${uploadedFile ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'}`}>
                <Upload className="h-5 w-5" />
              </div>
              <span className={`text-sm font-medium ${uploadedFile ? 'text-green-600' : 'text-gray-400'}`}>
                Fails augšupielādēts
              </span>
            </div>
            
            <div className="flex items-center space-x-2">
              <div className={`p-2 rounded-full ${isProcessing ? 'bg-blue-100 text-blue-600' : uploadedFile ? 'bg-gray-100 text-gray-400' : 'bg-gray-100 text-gray-400'}`}>
                <CheckCircle className="h-5 w-5" />
              </div>
              <span className={`text-sm font-medium ${isProcessing ? 'text-blue-600' : uploadedFile ? 'text-gray-400' : 'text-gray-400'}`}>
                Apstrādājas
              </span>
            </div>
            
            <div className="flex items-center space-x-2">
              <div className={`p-2 rounded-full ${completedResults ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'}`}>
                <AlertCircle className="h-5 w-5" />
              </div>
              <span className={`text-sm font-medium ${completedResults ? 'text-green-600' : 'text-gray-400'}`}>
                Pabeigts
              </span>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <p className="text-red-800 font-medium">Kļūda</p>
            </div>
            <p className="text-red-700 mt-2">{error}</p>
          </div>
        )}

        {/* Upload Section */}
        {!uploadedFile && !error && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Augšupielādēt pavadzīmi
            </h2>
            <FileUpload
              onFileUploaded={handleFileUploaded}
              onError={handleError}
            />
          </div>
        )}

        {/* Processing Section */}
        {uploadedFile && isProcessing && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Apstrāde notiek...
            </h2>
            <ProcessingStatus
              fileId={uploadedFile.file_id}
              filename={uploadedFile.filename}
              onCompleted={handleProcessingCompleted}
              onError={handleError}
            />
          </div>
        )}

        {/* Results Section */}
        {completedResults && (
          <EditableResults
            fileId={uploadedFile!.file_id}
            initialData={completedResults}
            onDataUpdated={handleDataUpdated}
            onError={handleError}
          />
        )}
        {/* Success Message */}
        {successMessage && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <p className="text-green-800 font-medium">Veiksme</p>
            </div>
            <p className="text-green-700 mt-2">{successMessage}</p>
          </div>
        )}
        {/* Info Section */}
        {!uploadedFile && !error && (
          <div className="mt-8 bg-blue-50 rounded-lg p-6">
            <h3 className="text-lg font-medium text-blue-900 mb-2">
              Kā tas darbojas?
            </h3>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Augšupielādējiet pavadzīmes attēlu (JPG, PNG) vai PDF</li>
              <li>• Sistēma izmanto OCR lai atpazītu tekstu</li>
              <li>• Hibridā AI sistēma (Regex + NER) ekstraktē strukturētus datus</li>
              <li>• Jūs varat labot rezultātus - sistēma mācīsies no labojumiem!</li>
              <li>• Katrs labojums uzlabo AI modeli nākamajām pavadzīmēm</li>
            </ul>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
