module.exports = {
    env: {
        es6: true,
        node: true
    },
    extends: [
        'airbnb-base'
    ],
    parserOptions: {
        "sourceType": "module"
    },
    rules: {
        'arrow-parens': 'off',
        'comma-dangle': 'off',
        indent: ['error', 4, {
            SwitchCase: 1
        }],
        'max-len': ['error', {
            code: 100,
        }],
        'no-continue': 'off',
        'no-debugger': 'off',
        'no-mixed-operators': 'off',
        'no-param-reassign': 'off',
        'no-plusplus': 'off',
        'no-underscore-dangle': 'off',
        'no-use-before-define': 'off',
        'no-multiple-empty-lines': ['error', { max: 1 }],
        'object-curly-newline': 'off',
        'space-before-function-paren': ['error', 'always'],
        'no-trailing-spaces': ['error'],
        'no-unused-expressions': 'off',
        'no-unused-vars': 'off'
    }
};
