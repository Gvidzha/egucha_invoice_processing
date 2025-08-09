import React, { useState, useEffect, useRef } from 'react';
import { InvoiceAPI } from '../services/api';

interface AutocompleteInputProps {
  value: string;
  onChange: (value: string) => void;
  fieldName: string;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

const AutocompleteInput: React.FC<AutocompleteInputProps> = ({
  value,
  onChange,
  fieldName,
  placeholder,
  className = "",
  disabled = false
}) => {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [filteredSuggestions, setFilteredSuggestions] = useState<string[]>([]);
  const [activeSuggestion, setActiveSuggestion] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // Ielādē ieteikumus kad components tiek mount
  useEffect(() => {
    const loadSuggestions = async () => {
      try {
        const fieldSuggestions = await InvoiceAPI.getFieldSuggestions(fieldName, 15);
        setSuggestions(fieldSuggestions);
      } catch (error) {
        console.error('Kļūda ielādējot ieteikumus:', error);
      }
    };

    loadSuggestions();
  }, [fieldName]);

  // Filtrē ieteikumus pēc input vērtības
  useEffect(() => {
    if (value && suggestions.length > 0) {
      const filtered = suggestions.filter(suggestion =>
        suggestion.toLowerCase().includes(value.toLowerCase()) &&
        suggestion.toLowerCase() !== value.toLowerCase()
      );
      setFilteredSuggestions(filtered.slice(0, 8)); // Maksimāli 8 ieteikumi
    } else {
      setFilteredSuggestions([]);
    }
    setActiveSuggestion(-1);
  }, [value, suggestions]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    onChange(newValue);
    setShowSuggestions(true);
  };

  const handleInputFocus = () => {
    if (filteredSuggestions.length > 0) {
      setShowSuggestions(true);
    }
  };

  const handleInputBlur = () => {
    // Delay hiding suggestions to allow clicking on them
    setTimeout(() => setShowSuggestions(false), 150);
  };

  const handleSuggestionClick = (suggestion: string) => {
    onChange(suggestion);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showSuggestions || filteredSuggestions.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setActiveSuggestion(prev => 
          prev < filteredSuggestions.length - 1 ? prev + 1 : 0
        );
        break;
      
      case 'ArrowUp':
        e.preventDefault();
        setActiveSuggestion(prev => 
          prev > 0 ? prev - 1 : filteredSuggestions.length - 1
        );
        break;
      
      case 'Enter':
        e.preventDefault();
        if (activeSuggestion >= 0 && activeSuggestion < filteredSuggestions.length) {
          handleSuggestionClick(filteredSuggestions[activeSuggestion]);
        }
        break;
      
      case 'Escape':
        setShowSuggestions(false);
        setActiveSuggestion(-1);
        break;
    }
  };

  return (
    <div className="relative">
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={handleInputChange}
        onFocus={handleInputFocus}
        onBlur={handleInputBlur}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        className={`
          w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
          disabled:bg-gray-100 disabled:text-gray-500
          ${className}
        `}
      />
      
      {showSuggestions && filteredSuggestions.length > 0 && (
        <div
          ref={suggestionsRef}
          className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-48 overflow-y-auto"
        >
          {filteredSuggestions.map((suggestion, index) => (
            <div
              key={index}
              onClick={() => handleSuggestionClick(suggestion)}
              className={`
                px-3 py-2 cursor-pointer text-sm
                ${index === activeSuggestion 
                  ? 'bg-blue-100 text-blue-900' 
                  : 'hover:bg-gray-100'
                }
              `}
            >
              <span className="text-gray-600">💡</span> {suggestion}
            </div>
          ))}
          
          {filteredSuggestions.length > 0 && (
            <div className="px-3 py-1 text-xs text-gray-500 border-t bg-gray-50">
              💾 Iepriekš ievadītās vērtības
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AutocompleteInput;