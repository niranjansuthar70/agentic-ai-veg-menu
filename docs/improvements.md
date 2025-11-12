# Improvements & Future Enhancements

## 1. OCR Integration for Cost Optimization
Integrate Nanonets OCR for dishes-prices extraction to reduce API costs associated with large VLMs like Gemini. OCR APIs are typically 10-50x cheaper and faster for simple text extraction tasks.

## 2. Enhanced Knowledge Database
Build more robust knowledge database for dishes/ingredients with comprehensive nutritional profiles, regional variations, and allergen data. This will enable more accurate health scoring and better handling of diverse cuisines.

## 3. Custom Model Development
Fine-tune custom BERT/tree-based model for dish classification to remove dependencies on external APIs and databases. Hybrid approach with DistilBERT for semantic understanding and XGBoost for structured features will provide offline capability and cost reduction.

## 4. Data Validation with Pydantic
Integrate Pydantic for data verification to ensure robust request/response handling with automatic validation, type safety, and clear error messages. This will reduce runtime errors and improve data consistency across the application.