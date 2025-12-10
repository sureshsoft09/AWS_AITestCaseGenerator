/**
 * Extract error message from API response
 * Handles both string and object error formats
 */
export const extractErrorMessage = (err: any, defaultMessage: string): string => {
  if (!err.response?.data?.detail) {
    return defaultMessage;
  }

  const detail = err.response.data.detail;

  // If detail is a string, return it directly
  if (typeof detail === 'string') {
    return detail;
  }

  // If detail is an object, try to extract meaningful message
  if (typeof detail === 'object') {
    // Check for message field
    if (detail.message) {
      let message = detail.message;
      
      // If there are errors array, append them
      if (detail.errors && Array.isArray(detail.errors)) {
        const errorList = detail.errors
          .map((e: any) => {
            if (typeof e === 'string') return e;
            if (e.filename && e.error) return `${e.filename}: ${e.error}`;
            if (e.error) return e.error;
            return JSON.stringify(e);
          })
          .join(', ');
        message += ` - ${errorList}`;
      }
      
      return message;
    }

    // If it's a validation error array from FastAPI
    if (Array.isArray(detail)) {
      return detail
        .map((e: any) => {
          if (e.msg) return `${e.loc?.join('.') || 'Field'}: ${e.msg}`;
          return JSON.stringify(e);
        })
        .join(', ');
    }

    // Last resort: stringify the object
    try {
      return JSON.stringify(detail);
    } catch {
      return defaultMessage;
    }
  }

  return defaultMessage;
};
