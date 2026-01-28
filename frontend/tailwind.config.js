/** @type {import('tailwindcss').Config} */
export default {
	darkMode: 'class',
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			colors: {
				// MSDE Official Brand Colors (February 2025)
				'msde-red': '#BD0934',
				'msde-gold': '#FFC838',
				'msde-navy': '#1A4176',
				'msde-teal': '#5BA49C',
				'msde-orange': '#DF5F46',
				'msde-amber': '#E19C37',
				'msde-gray': '#454C5A',
				// Legacy Maryland state colors
				'md-red': '#E03C31',
				'md-gold': '#FFD200',
				'md-black': '#231F20',
				// CTE cluster colors
				'cluster-am': '#1E3A5F',
				'cluster-ag': '#2E7D32',
				'cluster-aed': '#7B1FA2',
				'cluster-con': '#E65100',
				'cluster-dt': '#0288D1',
				'cluster-ed': '#00796B',
				'cluster-enr': '#558B2F',
				'cluster-fs': '#5D4037',
				'cluster-hhs': '#C2185B',
				'cluster-het': '#F57C00',
				'cluster-me': '#455A64',
				'cluster-mkt': '#D32F2F',
				'cluster-pss': '#1565C0',
				'cluster-sct': '#37474F'
			},
			fontFamily: {
				sans: ['Montserrat', 'system-ui', 'sans-serif'],
				display: ['Montserrat', 'system-ui', 'sans-serif'],
				mono: ['JetBrains Mono', 'Menlo', 'monospace']
			}
		}
	},
	plugins: [require('@tailwindcss/typography')]
};
