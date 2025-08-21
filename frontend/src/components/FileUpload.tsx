import React, { useState, useCallback } from 'react';
import { Upload, FileText, AlertCircle, CheckCircle } from 'lucide-react';
import { InvoiceAPI, handleApiError } from '../services/api';
import type { UploadResponse } from '../types/invoice';

interface FileUploadProps {
  onFileUploaded: (response: UploadResponse) => void;
  onError: (error: string) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileUploaded, onError }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');

  // Atļautie failu tipi
  const allowedTypes = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp'];
  const maxSize = 10 * 1024 * 1024; // 10MB

  const validateFile = (file: File): string | null => {
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    
    if (!allowedTypes.includes(extension)) {
      return `Neatbalstīts faila tips. Atļautie: ${allowedTypes.join(', ')}`;
    }
    
    if (file.size > maxSize) {
      return `Fails pārāk liels. Maksimālais izmērs: ${maxSize / 1024 / 1024}MB`;
    }
    
    return null;
  };

  const handleFileUpload = async (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      onError(validationError);
      setUploadStatus('error');
      return;
    }

    setIsUploading(true);
    setUploadStatus('idle');

    try {
      const response = await InvoiceAPI.uploadFile(file);
      setUploadStatus('success');
      onFileUploaded(response);
    } catch (error) {
      const errorMessage = handleApiError(error);
      onError(errorMessage);
      setUploadStatus('error');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { files } = e.target;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const getStatusIcon = () => {
    switch (uploadStatus) {
      case 'success':
        return <CheckCircle className="w-8 h-8 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-8 h-8 text-red-500" />;
      default:
        return <Upload className="w-8 h-8 text-blue-500" />;
    }
  };

  const getStatusText = () => {
    if (isUploading) {
      return 'Augšupielādē...';
    }
    switch (uploadStatus) {
      case 'success':
        return 'Fails veiksmīgi augšupielādēts!';
      case 'error':
        return 'Augšupielādes kļūda';
      default:
        return 'Velciet failu šeit vai noklikšķiniet, lai izvēlētos';
    }
  };

  return (
    <div className="w-full max-w-lg mx-auto">
      <div
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
          transition-all duration-200 ease-in-out
          ${isDragOver ? 'border-blue-400 bg-blue-50' : 'border-gray-300'}
          ${isUploading ? 'opacity-50 cursor-not-allowed' : 'hover:border-blue-400 hover:bg-gray-50'}
          ${uploadStatus === 'success' ? 'border-green-400 bg-green-50' : ''}
          ${uploadStatus === 'error' ? 'border-red-400 bg-red-50' : ''}
        `}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => !isUploading && document.getElementById('file-input')?.click()}
      >
        <input
          id="file-input"
          type="file"
          className="hidden"
          accept={allowedTypes.join(',')}
          onChange={handleFileSelect}
          disabled={isUploading}
        />
        
        <div className="flex flex-col items-center space-y-4">
          {getStatusIcon()}
          
          <div>
            <p className="text-lg font-medium text-gray-700">
              {getStatusText()}
            </p>
            <p className="text-sm text-gray-500 mt-2">
              Atbalstītie formāti: PDF, JPG, PNG, TIFF, BMP
            </p>
            <p className="text-xs text-gray-400">
              Maksimālais izmērs: 10MB
            </p>
          </div>
          
          {isUploading && (
            <div className="w-full max-w-xs">
              <div className="bg-gray-200 rounded-full h-2">
                <div className="bg-blue-500 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
              </div>
            </div>
          )}
        </div>
      </div>
      
      <div className="mt-4 text-center">
        <FileText className="w-6 h-6 text-gray-400 mx-auto mb-2" />
        <p className="text-sm text-gray-600">
          Pavadzīmju apstrādes sistēma ar OCR
        </p>
      </div>
    </div>
  );
};

export default FileUpload;
