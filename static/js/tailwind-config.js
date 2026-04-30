// Квартиркинъ — Общая конфигурация Tailwind CSS
tailwind.config = {
    theme: {
        extend: {
            fontFamily: {
                sans: ['Plus Jakarta Sans', 'sans-serif'],
                serif: ['Playfair Display', 'serif'],
            },
            colors: {
                sand: {
                    50: '#FDFBF7',
                    100: '#F9F6F0',
                    200: '#F0EBE1',
                    300: '#E5DED0',
                    400: '#D4C9B8',
                    500: '#C4B5A0',
                    600: '#B09A80',
                    700: '#8B7A65',
                    800: '#6B5D4D',
                    900: '#4A4035',
                },
                sea: {
                    50: '#F0F9FA',
                    100: '#D9F0F2',
                    200: '#B8E5E8',
                    300: '#8BD4DA',
                    400: '#5AC0C8',
                    500: '#3BA8B3',
                    600: '#2D8A94',
                    700: '#266F78',
                    800: '#235B63',
                    900: '#214D54',
                },
                coral: {
                    300: '#FCA5A5',
                    400: '#F87171',
                    500: '#EF4444',
                }
            },
            boxShadow: {
                'soft': '0 25px 60px -12px rgba(0, 0, 0, 0.08)',
                'soft-lg': '0 35px 80px -12px rgba(0, 0, 0, 0.12)',
                'inner-soft': 'inset 0 1px 1px rgba(255, 255, 255, 0.15)',
            },
            borderRadius: {
                '4xl': '2rem',
                '5xl': '2.5rem',
            }
        }
    }
}