import React, { useState, useEffect } from 'react';
import { Loader2, CheckCircle, AlertCircle, Clock, FileText } from 'lucide-react';
import { InvoiceAPI, handleApiError } from '../services/api';
import type { StatusResponse } from '../types/invoice';

interface ProcessingStatusProps {
  fileId: number;
  filename: string;
  onCompleted: (results: StatusResponse) => void;
  onError: (error: string) => void;
}

const ProcessingStatus: React.FC<ProcessingStatusProps> = ({ 
  fileId, 
  filename, 
  onCompleted, 
  onError 
}) => {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [startTime] = useState(Date.now());

  // Polling intervāls statusam
  useEffect(() => {
    let intervalId: NodeJS.Timeout;
    let timeIntervalId: NodeJS.Timeout;

    const checkStatus = async () => {
      try {
        const response = await InvoiceAPI.getStatus(fileId);
        setStatus(response);
        setIsLoading(false);

        if (response.status === 'completed') {
          onCompleted(response);
          clearInterval(intervalId);
          clearInterval(timeIntervalId);
        } else if (response.status === 'error') {
          onError(response.error_message || 'Apstrādes kļūda');
          clearInterval(intervalId);
          clearInterval(timeIntervalId);
        }
      } catch (error) {
        const errorMessage = handleApiError(error);
        onError(errorMessage);
        setIsLoading(false);
        clearInterval(intervalId);
        clearInterval(timeIntervalId);
      }
    };

    // Pārbaudīt statusu katras 2 sekundes
    intervalId = setInterval(checkStatus, 2000);
    
    // Atjaunināt elapsed time katru sekundi
    timeIntervalId = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);

    // Sākotnējā status pārbaude
    checkStatus();

    return () => {
      clearInterval(intervalId);
      clearInterval(timeIntervalId);
    };
  }, [fileId, onCompleted, onError, startTime]);

  const getStatusIcon = () => {
    if (isLoading || !status) {
      return <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />;
    }

    switch (status.status) {
      case 'processing':
        return <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-8 h-8 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-8 h-8 text-red-500" />;
      default:
        return <Clock className="w-8 h-8 text-gray-500" />;
    }
  };

  const getStatusText = () => {
    if (isLoading || !status) {
      return 'Ielādē...';
    }

    switch (status.status) {
      case 'uploaded':
        return 'Gatavs apstrādei';
      case 'processing':
        return 'Apstrādā ar OCR...';
      case 'completed':
        return 'Apstrāde pabeigta!';
      case 'error':
        return 'Apstrādes kļūda';
      default:
        return 'Nezināms statuss';
    }
  };

  const getProgressPercentage = () => {
    if (!status) { 
      return 0;
    }

    switch (status.status) {
      case 'uploaded':
        return 25;
      case 'processing':
        return 75;
      case 'completed':
        return 100;
      case 'error':
        return 0;
      default:
        return 0;
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="w-full max-w-lg mx-auto">
      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
        {/* Header */}
        <div className="flex items-center space-x-3 mb-4">
          <FileText className="w-5 h-5 text-gray-400" />
          <span className="text-sm font-medium text-gray-700 truncate">{filename}</span>
        </div>

        {/* Status Icon un teksts */}
        <div className="flex flex-col items-center space-y-4 mb-6">
          {getStatusIcon()}
          
          <div className="text-center">
            <p className="text-lg font-medium text-gray-800">
              {getStatusText()}
            </p>
            
            <div className="flex items-center justify-center space-x-2 mt-2 text-sm text-gray-500">
              <Clock className="w-4 h-4" />
              <span>Laiks: {formatTime(elapsedTime)}</span>
            </div>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progresa</span>
            <span>{getProgressPercentage()}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-500 ease-out ${
                status?.status === 'error' ? 'bg-red-500' : 
                status?.status === 'completed' ? 'bg-green-500' : 'bg-blue-500'
              }`}
              style={{ width: `${getProgressPercentage()}%` }}
            ></div>
          </div>
        </div>

        {/* Hasil awal jika status completed */}
        {status?.status === 'completed' && (
          <div className="bg-gray-50 rounded-lg p-4 text-sm">
            <h4 className="font-medium text-gray-800 mb-2">Sākotnējie rezultāti:</h4>
            <div className="space-y-1 text-gray-600">
              {status.document_number && (
                <div>📄 Pavadzīmes Nr: <span className="font-medium">{status.document_number}</span></div>
              )}
              {status.supplier_name && (
                <div>🏢 Piegādātājs: <span className="font-medium">{status.supplier_name}</span></div>
              )}
              {status.total_amount && (
                <div>💰 Summa: <span className="font-medium">{status.total_amount} {status.currency}</span></div>
              )}
              {status.confidence_score && (
                <div>📊 Kvalitāte: <span className="font-medium">{(status.confidence_score * 100).toFixed(1)}%</span></div>
              )}
            </div>
          </div>
        )}

        {/* Error message */}
        {status?.status === 'error' && status.error_message && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm">
            <div className="flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 text-red-500 mt-0.5" />
              <div>
                <h4 className="font-medium text-red-800">Kļūda:</h4>
                <p className="text-red-700">{status.error_message}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProcessingStatus;
