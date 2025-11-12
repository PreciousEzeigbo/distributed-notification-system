// Note: For proper TypeScript linting, install:
// npm install --save-dev @typescript-eslint/parser @typescript-eslint/eslint-plugin
// Then use parser: '@typescript-eslint/parser' and plugin: ['@typescript-eslint']
module.exports = {
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: 'module',
  },
  extends: ['eslint:recommended'],
  root: true,
  env: {
    node: true,
    jest: true,
    es6: true,
  },
  ignorePatterns: ['.eslintrc.js', 'dist', 'node_modules'],
  rules: {
    'no-unused-vars': 'off',
    'no-undef': 'off',
  },
};
