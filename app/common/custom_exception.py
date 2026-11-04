import sys


class CustomException(Exception):
    def __init__(self, message: str, error_detail: Exception = None):
        self.error_message = self.get_detailed_error_message(message, error_detail)
        super().__init__(self.error_message)

    @staticmethod
    def get_detailed_error_message(message, error_detail):
        _, _, exc_tb = sys.exc_info()
        file_name = exc_tb.tb_frame.f_code.co_filename if exc_tb else "Unknown File"
        line_number = exc_tb.tb_lineno if exc_tb else "Unknown Line"
        return f"{message} | Error: {error_detail} | File: {file_name} | Line: {line_number}"

    def __str__(self):
        return self.error_message


class EmailFetchError(CustomException):
    """Raised when the IMAP agent fails to connect or fetch emails."""
    pass


class AttachmentError(CustomException):
    """Raised when a PDF attachment cannot be extracted or saved."""
    pass


class PDFDecryptionError(CustomException):
    """Raised when a password-protected PDF cannot be decrypted."""
    pass


class PDFExtractionError(CustomException):
    """Raised when text/table extraction from a PDF fails."""
    pass


class TemplateNotFoundError(CustomException):
    """Raised when no matching bank template is found for a document."""
    pass


class FieldExtractionError(CustomException):
    """Raised when a required field cannot be extracted by any method."""
    pass


class LLMExtractionError(CustomException):
    """Raised when the LLM fallback extraction fails or returns invalid output."""
    pass


class ValidationError(CustomException):
    """Raised when extracted data fails validation checks."""
    pass


class DuplicateInvoiceError(CustomException):
    """Raised when an invoice with the same file hash already exists."""
    pass


class DatabaseWriteError(CustomException):
    """Raised when writing a record to the database fails."""
    pass