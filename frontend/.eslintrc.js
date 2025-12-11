module.exports = {
  extends: [
    'react-app',
    'react-app/jest'
  ],
  rules: {
    // Suppress unused variable warnings during development
    'no-unused-vars': 'off',
    '@typescript-eslint/no-unused-vars': 'off',
    // Allow console statements for debugging
    'no-console': 'off',
    // Suppress other common development warnings
    'no-debugger': 'off',
    'react-hooks/exhaustive-deps': 'off',
    // Suppress React warnings
    'react/jsx-no-target-blank': 'off',
    'react/no-unescaped-entities': 'off',
    'react/display-name': 'off',
    'react/prop-types': 'off',
    // Suppress import warnings
    'import/no-anonymous-default-export': 'off',
    'import/no-unused-modules': 'off',
    // Suppress accessibility warnings for development
    'jsx-a11y/anchor-is-valid': 'off',
    'jsx-a11y/alt-text': 'off',
    'jsx-a11y/click-events-have-key-events': 'off',
    'jsx-a11y/no-noninteractive-element-interactions': 'off',
    'jsx-a11y/no-static-element-interactions': 'off',
    // Suppress other common warnings
    'no-undef': 'off',
    'no-redeclare': 'off',
    'no-unreachable': 'off',
    'no-constant-condition': 'off',
    'no-empty': 'off',
    'no-irregular-whitespace': 'off',
    // TypeScript warnings
    '@typescript-eslint/no-explicit-any': 'off',
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/ban-ts-comment': 'off'
  },
  env: {
    browser: true,
    es6: true,
    node: true
  },
  ignorePatterns: [
    'node_modules/',
    'build/',
    'dist/',
    '*.min.js'
  ]
};
