<script lang="ts">
	import { onMount } from 'svelte';
	import { base } from '$app/paths';
	import { writable } from 'svelte/store';
	import * as XLSX from 'xlsx';

	// Inline clusters data (no external dependency)
	const clusters = writable([
		{ code: 'AED', name: 'Arts, Entertainment, and Design' },
		{ code: 'AG', name: 'Agriculture' },
		{ code: 'AM', name: 'Advanced Manufacturing' },
		{ code: 'CON', name: 'Construction' },
		{ code: 'DT', name: 'Digital Technology' },
		{ code: 'ED', name: 'Education' },
		{ code: 'ENR', name: 'Energy and Natural Resources' },
		{ code: 'FS', name: 'Financial Services' },
		{ code: 'HET', name: 'Hospitality, Events, and Tourism' },
		{ code: 'HHS', name: 'Healthcare and Human Services' },
		{ code: 'ME', name: 'Management and Entrepreneurship' },
		{ code: 'MKT', name: 'Marketing and Sales' },
		{ code: 'PSS', name: 'Public Service and Safety' },
		{ code: 'SCT', name: 'Supply Chain and Transportation' }
	]);

	// Inline cluster colors
	function getClusterColor(code: string): string {
		const colors: Record<string, string> = {
			'AED': 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300',
			'AG': 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300',
			'AM': 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300',
			'CON': 'bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300',
			'DT': 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/40 dark:text-cyan-300',
			'ED': 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300',
			'ENR': 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300',
			'FS': 'bg-slate-100 text-slate-800 dark:bg-slate-700/40 dark:text-slate-300',
			'HET': 'bg-pink-100 text-pink-800 dark:bg-pink-900/40 dark:text-pink-300',
			'HHS': 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300',
			'ME': 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-300',
			'MKT': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300',
			'PSS': 'bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-300',
			'SCT': 'bg-teal-100 text-teal-800 dark:bg-teal-900/40 dark:text-teal-300'
		};
		return colors[code] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
	}

	interface InstitutionEntry {
		name: string;
		program: string;
		degree_type: string | null;
		ircs: string | null;
		key_features: string | null;
	}

	interface HSProgram {
		name: string;
		ircs: string[];
		community_colleges: InstitutionEntry[];
		universities: InstitutionEntry[];
		other: InstitutionEntry[] | null;
	}

	interface ClusterGroup {
		cluster_code: string;
		cluster_name: string;
		hs_programs: HSProgram[];
	}

	interface CrosswalkStats {
		total: number;
		unique_institutions: number;
		by_institution_type: Record<string, number>;
	}

	let groupedData: ClusterGroup[] = [];
	let stats: CrosswalkStats | null = null;
	let loading = true;
	let error = '';
	let selectedCluster = '';
	let expandedPrograms: Set<string> = new Set();

	function toggleProgram(key: string) {
		if (expandedPrograms.has(key)) {
			expandedPrograms.delete(key);
		} else {
			expandedPrograms.add(key);
		}
		expandedPrograms = expandedPrograms;
	}

	function expandAll() {
		const allKeys: string[] = [];
		groupedData.forEach(cluster => {
			cluster.hs_programs.forEach(prog => {
				allKeys.push(`${cluster.cluster_code}|${prog.name}`);
			});
		});
		expandedPrograms = new Set(allKeys);
	}

	function collapseAll() {
		expandedPrograms = new Set();
	}

	$: filteredData = selectedCluster
		? groupedData.filter(g => g.cluster_code === selectedCluster)
		: groupedData;

	$: totalPrograms = filteredData.reduce((sum, c) => sum + c.hs_programs.length, 0);
	$: totalConnections = filteredData.reduce((sum, c) =>
		sum + c.hs_programs.reduce((psum, p) =>
			psum + p.community_colleges.length + p.universities.length + (p.other?.length || 0), 0), 0);

	async function loadStaticData() {
		loading = true;
		error = '';
		try {
			const response = await fetch(`${base}/crosswalk-data.json`);
			if (!response.ok) throw new Error('Failed to load data');
			const json = await response.json();
			stats = json.stats;
			groupedData = json.data.sort((a: ClusterGroup, b: ClusterGroup) =>
				a.cluster_name.localeCompare(b.cluster_name)
			);
		} catch (e: any) {
			error = e.message || 'Failed to load pathways';
			groupedData = [];
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		loadStaticData();
	});

	let exporting = false;

	async function exportToExcel() {
		if (filteredData.length === 0) return;
		exporting = true;
		try {
			const wb = XLSX.utils.book_new();
			const crosswalkRows: any[] = [];
			crosswalkRows.push(['Cluster Code', 'Cluster Name', 'HS Program', 'Industry Credentials', 'Institution Type', 'Institution Name', 'Post-Secondary Program', 'Degree Type']);

			filteredData.forEach(cluster => {
				cluster.hs_programs.forEach(program => {
					const ircs = program.ircs.join('; ');
					program.community_colleges.forEach(cc => {
						crosswalkRows.push([cluster.cluster_code, cluster.cluster_name, program.name, ircs, 'Community College', cc.name, cc.program || '', cc.degree_type || '']);
					});
					program.universities.forEach(uni => {
						crosswalkRows.push([cluster.cluster_code, cluster.cluster_name, program.name, ircs, 'University', uni.name, uni.program || '', uni.degree_type || '']);
					});
					if (program.community_colleges.length === 0 && program.universities.length === 0) {
						crosswalkRows.push([cluster.cluster_code, cluster.cluster_name, program.name, ircs, '', '', '', '']);
					}
				});
			});

			const wsMain = XLSX.utils.aoa_to_sheet(crosswalkRows);
			wsMain['!cols'] = [{ wch: 12 }, { wch: 30 }, { wch: 35 }, { wch: 50 }, { wch: 18 }, { wch: 35 }, { wch: 40 }, { wch: 12 }];
			XLSX.utils.book_append_sheet(wb, wsMain, 'Crosswalk');

			const date = new Date().toISOString().split('T')[0];
			const clusterSuffix = selectedCluster ? `-${selectedCluster}` : '';
			XLSX.writeFile(wb, `MD-CTE-Crosswalk${clusterSuffix}-${date}.xlsx`);
		} catch (e) {
			console.error('Export failed:', e);
		} finally {
			exporting = false;
		}
	}
</script>

<svelte:head>
	<title>Post-Secondary Crosswalk - Maryland CTE</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-slate-900">
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<header class="mb-8">
			<h1 class="text-3xl font-bold text-gray-900 dark:text-white">Maryland CTE Post-Secondary Crosswalk</h1>
			<p class="mt-2 text-gray-600 dark:text-gray-300">Map your high school CTE program to Maryland colleges and credentials.</p>
		</header>

		{#if stats}
			<div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
				<div class="bg-white dark:bg-slate-800 rounded-lg p-4 shadow-sm">
					<div class="text-2xl font-bold text-gray-900 dark:text-white">{stats.total}</div>
					<div class="text-sm text-gray-500 dark:text-gray-400">Pathway Connections</div>
				</div>
				<div class="bg-white dark:bg-slate-800 rounded-lg p-4 shadow-sm">
					<div class="text-2xl font-bold text-gray-900 dark:text-white">{stats.unique_institutions}</div>
					<div class="text-sm text-gray-500 dark:text-gray-400">MD Institutions</div>
				</div>
				<div class="bg-white dark:bg-slate-800 rounded-lg p-4 shadow-sm">
					<div class="text-2xl font-bold text-gray-900 dark:text-white">{stats.by_institution_type['Community College'] || 0}</div>
					<div class="text-sm text-gray-500 dark:text-gray-400">Community Colleges</div>
				</div>
				<div class="bg-white dark:bg-slate-800 rounded-lg p-4 shadow-sm">
					<div class="text-2xl font-bold text-gray-900 dark:text-white">{stats.by_institution_type['University'] || 0}</div>
					<div class="text-sm text-gray-500 dark:text-gray-400">Universities</div>
				</div>
			</div>
		{/if}

		<div class="flex flex-wrap gap-4 mb-8">
			<select bind:value={selectedCluster} class="px-4 py-2 rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-gray-900 dark:text-white">
				<option value="">All 14 Clusters</option>
				{#each $clusters as cluster}
					<option value={cluster.code}>{cluster.code} — {cluster.name}</option>
				{/each}
			</select>
			<button on:click={() => selectedCluster = ''} class="px-4 py-2 rounded-lg bg-gray-200 dark:bg-slate-700 text-gray-700 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-slate-600">Reset</button>
			<button on:click={exportToExcel} disabled={exporting || loading} class="px-4 py-2 rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:opacity-50">
				{exporting ? 'Exporting...' : 'Export Excel'}
			</button>
		</div>

		{#if loading}
			<div class="text-center py-20">
				<div class="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
				<p class="mt-4 text-gray-500">Loading...</p>
			</div>
		{:else if error}
			<div class="bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 p-4 rounded-lg">{error}</div>
		{:else}
			<div class="flex justify-between items-center mb-4">
				<span class="text-sm text-gray-500 dark:text-gray-400">{totalPrograms} programs · {totalConnections} connections</span>
				<div class="flex gap-2">
					<button on:click={expandAll} class="text-sm text-blue-600 dark:text-blue-400 hover:underline">Expand All</button>
					<button on:click={collapseAll} class="text-sm text-gray-500 hover:underline">Collapse All</button>
				</div>
			</div>

			<div class="space-y-8">
				{#each filteredData as cluster (cluster.cluster_code)}
					<section>
						<div class="flex items-center gap-3 mb-4">
							<span class="px-3 py-1 rounded-full text-sm font-semibold {getClusterColor(cluster.cluster_code)}">{cluster.cluster_code}</span>
							<h2 class="text-xl font-semibold text-gray-900 dark:text-white">{cluster.cluster_name}</h2>
							<span class="text-sm text-gray-500">({cluster.hs_programs.length})</span>
						</div>

						<div class="space-y-3">
							{#each cluster.hs_programs as program (program.name)}
								{@const programKey = `${cluster.cluster_code}|${program.name}`}
								{@const isExpanded = expandedPrograms.has(programKey)}

								<div class="bg-white dark:bg-slate-800 rounded-lg shadow-sm overflow-hidden">
									<button on:click={() => toggleProgram(programKey)} class="w-full px-4 py-3 flex items-center gap-3 hover:bg-gray-50 dark:hover:bg-slate-700/50">
										<svg class="w-5 h-5 text-gray-400 transition-transform {isExpanded ? 'rotate-90' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
										</svg>
										<div class="flex-1 text-left">
											<h3 class="font-semibold text-gray-900 dark:text-white">{program.name}</h3>
											<p class="text-sm text-gray-500 dark:text-gray-400">{program.ircs.length} IRCs · {program.community_colleges.length} CCs · {program.universities.length} Universities</p>
										</div>
									</button>

									{#if isExpanded}
										<div class="border-t border-gray-100 dark:border-slate-700 p-4">
											<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
												<div>
													<h4 class="font-semibold text-amber-700 dark:text-amber-400 mb-2">Credentials (IRCs)</h4>
													{#if program.ircs.length > 0}
														<div class="space-y-1">
															{#each program.ircs as irc}
																<div class="text-sm bg-amber-50 dark:bg-amber-900/30 text-amber-800 dark:text-amber-200 px-2 py-1 rounded">{irc}</div>
															{/each}
														</div>
													{:else}
														<p class="text-sm text-gray-400 italic">None listed</p>
													{/if}
												</div>
												<div>
													<h4 class="font-semibold text-emerald-700 dark:text-emerald-400 mb-2">Community Colleges</h4>
													{#if program.community_colleges.length > 0}
														<div class="space-y-2">
															{#each program.community_colleges as cc}
																<div class="text-sm bg-emerald-50 dark:bg-emerald-900/30 p-2 rounded">
																	<div class="font-medium text-emerald-800 dark:text-emerald-200">{cc.name}</div>
																	{#if cc.program}<div class="text-emerald-700 dark:text-emerald-300">{cc.program}</div>{/if}
																	{#if cc.degree_type}<div class="text-xs text-emerald-600 dark:text-emerald-400">{cc.degree_type}</div>{/if}
																</div>
															{/each}
														</div>
													{:else}
														<p class="text-sm text-gray-400 italic">None listed</p>
													{/if}
												</div>
												<div>
													<h4 class="font-semibold text-violet-700 dark:text-violet-400 mb-2">Universities</h4>
													{#if program.universities.length > 0}
														<div class="space-y-2">
															{#each program.universities as uni}
																<div class="text-sm bg-violet-50 dark:bg-violet-900/30 p-2 rounded">
																	<div class="font-medium text-violet-800 dark:text-violet-200">{uni.name}</div>
																	{#if uni.program}<div class="text-violet-700 dark:text-violet-300">{uni.program}</div>{/if}
																	{#if uni.degree_type}<div class="text-xs text-violet-600 dark:text-violet-400">{uni.degree_type}</div>{/if}
																</div>
															{/each}
														</div>
													{:else}
														<p class="text-sm text-gray-400 italic">None listed</p>
													{/if}
												</div>
											</div>
										</div>
									{/if}
								</div>
							{/each}
						</div>
					</section>
				{/each}
			</div>
		{/if}
	</div>
</div>
