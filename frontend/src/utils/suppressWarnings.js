// Suppress common React warnings during development
if (process.env.NODE_ENV === 'development') {
  // Store original console methods
  const originalWarn = console.warn;
  const originalError = console.error;
  
  // List of warnings to suppress
  const suppressedWarnings = [
    'Warning: validateDOMNesting',
    'Warning: React does not recognize',
    'Warning: componentWillReceiveProps has been renamed',
    'Warning: componentWillMount has been renamed',
    'Warning: componentWillUpdate has been renamed',
    'Warning: Failed prop type',
    'Warning: Each child in a list should have a unique "key" prop',
    'ResizeObserver loop limit exceeded',
    'Non-serializable values were found in the navigation state',
    'Material-UI: You have provided an out-of-range value',
    'MUI: You have provided an out-of-range value'
  ];
  
  // Override console.warn
  console.warn = (...args) => {
    const warningMessage = args.join(' ');
    const shouldSuppress = suppressedWarnings.some(warning => 
      warningMessage.includes(warning)
    );
    
    if (!shouldSuppress) {
      originalWarn.apply(console, args);
    }
  };
  
  // Override console.error for specific errors
  console.error = (...args) => {
    const errorMessage = args.join(' ');
    const shouldSuppress = suppressedWarnings.some(warning => 
      errorMessage.includes(warning)
    );
    
    if (!shouldSuppress) {
      originalError.apply(console, args);
    }
  };
}

export default {};