<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { base } from '$app/paths';
	import { browser } from '$app/environment';
	import { writable } from 'svelte/store';

	// Simple theme store for static build
	const theme = writable<'light' | 'dark'>('light');

	let mobileMenuOpen = false;

	$: currentPath = $page.url.pathname;
	$: isDark = $theme === 'dark';

	function toggleTheme() {
		theme.update(t => {
			const newTheme = t === 'light' ? 'dark' : 'light';
			if (browser) {
				localStorage.setItem('theme', newTheme);
				document.documentElement.classList.toggle('dark', newTheme === 'dark');
			}
			return newTheme;
		});
	}

	onMount(() => {
		// Initialize theme from localStorage or system preference
		const saved = localStorage.getItem('theme');
		const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
		const initialTheme = saved === 'dark' || (!saved && prefersDark) ? 'dark' : 'light';
		theme.set(initialTheme);
		document.documentElement.classList.toggle('dark', initialTheme === 'dark');
	});

	// Static version - crosswalk only
	$: navLinks = [
		{ href: `${base}/crosswalk`, label: 'Crosswalk', tooltip: 'Post-secondary crosswalk' }
	];
</script>

<div class="min-h-screen flex flex-col">
	<!-- Header -->
	<header class="bg-white/80 dark:bg-slate-900/80 backdrop-blur-lg border-b border-gray-200/60 dark:border-slate-700/60 sticky top-0 z-50">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
			<div class="flex justify-between items-center h-16">
				<!-- Logo -->
				<a href="{base}/" class="flex items-center gap-3 group relative">
					<div class="w-10 h-10 bg-gradient-to-br from-red-600 to-red-700 rounded-xl flex items-center justify-center shadow-sm group-hover:shadow-md transition-shadow">
						<span class="text-white font-bold text-lg">MD</span>
					</div>
					<div class="hidden xl:block">
						<h1 class="text-lg font-semibold text-gray-900 dark:text-gray-100 tracking-tight whitespace-nowrap">CTE Crosswalk</h1>
						<p class="text-xs text-gray-500 dark:text-gray-400 -mt-0.5 whitespace-nowrap">Career Pathway Guide</p>
					</div>
				</a>

				<!-- Desktop Nav -->
				<nav class="hidden lg:flex items-center gap-1">
					{#each navLinks as link}
						<a
							href={link.href}
							class="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 relative group
								{currentPath === link.href || currentPath === `${base}/crosswalk`
									? 'bg-gray-100 dark:bg-slate-800 text-gray-900 dark:text-gray-100'
									: 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-50 dark:hover:bg-slate-800'}"
						>
							{link.label}
						</a>
					{/each}
				</nav>

				<!-- Theme Toggle -->
				<div class="flex items-center gap-3">
					<button
						on:click={toggleTheme}
						class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors relative group"
						aria-label="Toggle theme"
					>
						{#if isDark}
							<svg class="w-5 h-5 text-yellow-500" fill="currentColor" viewBox="0 0 24 24">
								<path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"/>
							</svg>
						{:else}
							<svg class="w-5 h-5 text-gray-600" fill="currentColor" viewBox="0 0 24 24">
								<path d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/>
							</svg>
						{/if}
					</button>

					<div class="flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800">
						<div class="w-2 h-2 rounded-full bg-blue-500"></div>
						<span class="text-xs font-medium text-blue-700 dark:text-blue-400">Static</span>
					</div>

					<!-- Mobile menu button -->
					<button
						on:click={() => mobileMenuOpen = !mobileMenuOpen}
						class="lg:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
						aria-label="Toggle menu"
					>
						<svg class="w-5 h-5 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							{#if mobileMenuOpen}
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							{:else}
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
							{/if}
						</svg>
					</button>
				</div>
			</div>

			<!-- Mobile Nav -->
			{#if mobileMenuOpen}
				<nav class="lg:hidden py-4 border-t border-gray-100 dark:border-slate-700">
					<div class="flex flex-col gap-1">
						{#each navLinks as link}
							<a
								href={link.href}
								on:click={() => mobileMenuOpen = false}
								class="px-4 py-3 rounded-lg text-sm font-medium transition-colors
									{currentPath === link.href
										? 'bg-gray-100 dark:bg-slate-800 text-gray-900 dark:text-gray-100'
										: 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-slate-800'}"
							>
								{link.label}
							</a>
						{/each}
					</div>
				</nav>
			{/if}
		</div>
	</header>

	<!-- Main content -->
	<main class="flex-1">
		<slot />
	</main>

	<!-- Footer -->
	<footer class="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-t border-gray-200/60 dark:border-slate-700/60 mt-auto">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
			<div class="flex flex-col md:flex-row justify-between items-center gap-4">
				<div class="text-center md:text-left">
					<p class="text-sm font-medium text-gray-700 dark:text-gray-300">Maryland CTE Crosswalk</p>
					<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Post-secondary pathway reference guide</p>
				</div>

				<div class="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
					<span>Data source: MSDE Crosswalk v3.01</span>
					<a
						href="https://github.com/w4ester/md-cte-crosswalk"
						target="_blank"
						rel="noopener noreferrer"
						class="hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
					>
						GitHub
					</a>
				</div>
			</div>
		</div>
	</footer>
</div>
