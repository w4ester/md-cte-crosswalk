<script lang="ts">
	import { onMount } from 'svelte';
	import { base } from '$app/paths';
	import { clusters } from '$lib/stores';
	import { getClusterColor } from '$lib/stores';
	import * as XLSX from 'xlsx';

	// Types for grouped data
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

	// Filters
	let selectedCluster = '';

	// Accordion state - track which programs are expanded
	let expandedPrograms: Set<string> = new Set();

	function toggleProgram(key: string) {
		if (expandedPrograms.has(key)) {
			expandedPrograms.delete(key);
		} else {
			expandedPrograms.add(key);
		}
		expandedPrograms = expandedPrograms; // Trigger reactivity
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

	// Filtered data based on selected cluster
	$: filteredData = selectedCluster
		? groupedData.filter(g => g.cluster_code === selectedCluster)
		: groupedData;

	// Count totals
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

	function handleFilterChange() {
		// Filter is client-side only
	}

	// Excel Export functionality
	let exporting = false;

	async function exportToExcel() {
		if (filteredData.length === 0) return;
		exporting = true;

		try {
			// Create workbook
			const wb = XLSX.utils.book_new();

			// Sheet 1: Full Crosswalk (one row per pathway connection)
			const crosswalkRows: any[] = [];
			crosswalkRows.push([
				'Cluster Code',
				'Cluster Name',
				'HS Program',
				'Industry Credentials',
				'Institution Type',
				'Institution Name',
				'Post-Secondary Program',
				'Degree Type'
			]);

			filteredData.forEach(cluster => {
				cluster.hs_programs.forEach(program => {
					const ircs = program.ircs.join('; ');

					// Add community college rows
					program.community_colleges.forEach(cc => {
						crosswalkRows.push([
							cluster.cluster_code,
							cluster.cluster_name,
							program.name,
							ircs,
							'Community College',
							cc.name,
							cc.program || '',
							cc.degree_type || ''
						]);
					});

					// Add university rows
					program.universities.forEach(uni => {
						crosswalkRows.push([
							cluster.cluster_code,
							cluster.cluster_name,
							program.name,
							ircs,
							'University',
							uni.name,
							uni.program || '',
							uni.degree_type || ''
						]);
					});

					// If no institutions, still add a row for the program/IRCs
					if (program.community_colleges.length === 0 && program.universities.length === 0) {
						crosswalkRows.push([
							cluster.cluster_code,
							cluster.cluster_name,
							program.name,
							ircs,
							'',
							'',
							'',
							''
						]);
					}
				});
			});

			const wsMain = XLSX.utils.aoa_to_sheet(crosswalkRows);

			// Set column widths
			wsMain['!cols'] = [
				{ wch: 12 },  // Cluster Code
				{ wch: 30 },  // Cluster Name
				{ wch: 35 },  // HS Program
				{ wch: 50 },  // IRCs
				{ wch: 18 },  // Institution Type
				{ wch: 35 },  // Institution Name
				{ wch: 40 },  // Post-Secondary Program
				{ wch: 12 }   // Degree Type
			];
			XLSX.utils.book_append_sheet(wb, wsMain, 'Crosswalk');

			// Sheet 2: Summary by Program
			const summaryRows: any[] = [];
			summaryRows.push([
				'Cluster',
				'HS Program',
				'# IRCs',
				'# Community Colleges',
				'# Universities',
				'Total Pathways'
			]);

			filteredData.forEach(cluster => {
				cluster.hs_programs.forEach(program => {
					summaryRows.push([
						cluster.cluster_code,
						program.name,
						program.ircs.length,
						program.community_colleges.length,
						program.universities.length,
						program.community_colleges.length + program.universities.length
					]);
				});
			});

			const wsSummary = XLSX.utils.aoa_to_sheet(summaryRows);
			wsSummary['!cols'] = [
				{ wch: 8 },
				{ wch: 40 },
				{ wch: 10 },
				{ wch: 20 },
				{ wch: 15 },
				{ wch: 15 }
			];
			XLSX.utils.book_append_sheet(wb, wsSummary, 'Summary');

			// Sheet 3: IRCs by Program
			const ircRows: any[] = [];
			ircRows.push(['Cluster', 'HS Program', 'Industry-Recognized Credential']);

			filteredData.forEach(cluster => {
				cluster.hs_programs.forEach(program => {
					program.ircs.forEach(irc => {
						ircRows.push([cluster.cluster_code, program.name, irc]);
					});
				});
			});

			const wsIRCs = XLSX.utils.aoa_to_sheet(ircRows);
			wsIRCs['!cols'] = [{ wch: 8 }, { wch: 40 }, { wch: 60 }];
			XLSX.utils.book_append_sheet(wb, wsIRCs, 'IRCs');

			// Generate filename with date
			const date = new Date().toISOString().split('T')[0];
			const clusterSuffix = selectedCluster ? `-${selectedCluster}` : '';
			const filename = `MD-CTE-Crosswalk${clusterSuffix}-${date}.xlsx`;

			// Download
			XLSX.writeFile(wb, filename);
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

<div class="blueprint-bg min-h-screen">
	<div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">

		<!-- Page Header -->
		<header class="mb-10">
			<div class="flex items-start gap-4 mb-4">
				<div class="hidden sm:flex items-center justify-center w-14 h-14 rounded-lg bg-gradient-to-br from-msde-red to-msde-navy dark:from-msde-gold dark:to-msde-amber shadow-lg">
					<svg class="w-7 h-7 text-white dark:text-slate-900" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
					</svg>
				</div>
				<div class="flex-1">
					<h1 class="blueprint-heading text-3xl sm:text-4xl lg:text-5xl">
						Post-Secondary Crosswalk
					</h1>
					<p class="mt-3 text-gray-600 dark:text-gray-300 text-base sm:text-lg max-w-2xl leading-relaxed">
						Map your high school CTE program to Maryland colleges. Discover credentials you can earn and postsecondary pathways available to you.
					</p>
				</div>
			</div>

			<!-- Vision callout -->
			<div class="vision-callout mt-6">
				<div class="flex items-start gap-4">
					<span class="text-2xl sm:text-3xl" aria-hidden="true">◈</span>
					<div>
						<p class="font-display text-lg text-amber-900 dark:text-amber-100">The Vision: IRCs as College Credit</p>
						<p class="text-sm text-amber-800 dark:text-amber-200 mt-1.5 leading-relaxed">
							Industry-Recognized Credentials earned in high school could count toward college credit—like AP exams do.
							This crosswalk shows how pathways align. <strong class="font-semibold">The connection isn't automatic yet</strong>, but it should be.
						</p>
					</div>
				</div>
			</div>
		</header>

		<!-- Stats Grid -->
		{#if stats}
			<div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-10">
				<div class="stat-card">
					<div class="stat-number">{stats.total}</div>
					<div class="text-sm text-gray-500 dark:text-gray-400 font-medium mt-1.5">Pathway Connections</div>
				</div>
				<div class="stat-card">
					<div class="stat-number">{stats.unique_institutions}</div>
					<div class="text-sm text-gray-500 dark:text-gray-400 font-medium mt-1.5">MD Institutions</div>
				</div>
				<div class="stat-card">
					<div class="stat-number">{stats.by_institution_type['Community College'] || 0}</div>
					<div class="text-sm text-gray-500 dark:text-gray-400 font-medium mt-1.5">Community Colleges</div>
				</div>
				<div class="stat-card">
					<div class="stat-number">{stats.by_institution_type['University'] || 0}</div>
					<div class="text-sm text-gray-500 dark:text-gray-400 font-medium mt-1.5">Universities</div>
				</div>
			</div>
		{/if}

		<!-- Filter Section -->
		<div class="filter-section mb-8">
			<div class="flex flex-col sm:flex-row gap-4 items-start sm:items-end">
				<div class="flex-1 w-full sm:w-auto">
					<label for="cluster" class="block text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2">
						Filter by Career Cluster
					</label>
					<select
						id="cluster"
						bind:value={selectedCluster}
						on:change={handleFilterChange}
						class="blueprint-select"
					>
						<option value="">All 14 Clusters</option>
						{#each $clusters as cluster}
							<option value={cluster.code}>{cluster.code} — {cluster.name}</option>
						{/each}
					</select>
				</div>
				<button
					on:click={() => { selectedCluster = ''; handleFilterChange(); }}
					class="btn-secondary min-h-[44px] w-full sm:w-auto"
				>
					Reset Filter
				</button>
				<button
					on:click={exportToExcel}
					disabled={exporting || loading || filteredData.length === 0}
					class="btn-primary min-h-[44px] w-full sm:w-auto flex items-center justify-center gap-2"
				>
					{#if exporting}
						<svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						</svg>
						Exporting...
					{:else}
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
						</svg>
						Export Excel
					{/if}
				</button>
			</div>
		</div>

		<!-- Results -->
		{#if loading}
			<div class="flex flex-col items-center justify-center py-20">
				<div class="relative">
					<div class="w-12 h-12 border-4 border-[var(--blueprint-line)] rounded-full"></div>
					<div class="absolute top-0 left-0 w-12 h-12 border-4 border-[var(--blueprint-navy)] dark:border-[var(--blueprint-gold)] rounded-full border-t-transparent animate-spin"></div>
				</div>
				<p class="mt-4 text-gray-500 dark:text-gray-400 font-medium">Loading crosswalk data...</p>
			</div>
		{:else if error}
			<div class="bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-700/50 rounded-xl p-6 text-red-700 dark:text-red-300">
				<div class="flex items-center gap-3">
					<svg class="w-6 h-6 shrink-0" fill="currentColor" viewBox="0 0 20 20">
						<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
					</svg>
					<span class="font-medium">{error}</span>
				</div>
			</div>
		{:else if filteredData.length === 0}
			<div class="text-center py-20 pathway-card">
				<p class="text-gray-500 dark:text-gray-400 text-lg">No matching pathways found.</p>
			</div>
		{:else}
			<!-- Expand/Collapse Controls -->
			<div class="flex items-center justify-between mb-6 px-1">
				<p class="program-count">
					{totalPrograms} programs · {totalConnections} connections
				</p>
				<div class="flex items-center gap-1">
					<button
						on:click={expandAll}
						class="text-sm font-medium px-3 py-1.5 rounded-md transition-colors text-msde-navy dark:text-msde-gold hover:bg-msde-navy/5 dark:hover:bg-msde-gold/10"
					>
						Expand All
					</button>
					<span class="text-gray-300 dark:text-gray-600">|</span>
					<button
						on:click={collapseAll}
						class="text-sm font-medium px-3 py-1.5 rounded-md text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
					>
						Collapse All
					</button>
				</div>
			</div>

			<!-- Cluster Groups -->
			<div class="space-y-10">
				{#each filteredData as cluster (cluster.cluster_code)}
					<section>
						<!-- Cluster Header -->
						<div class="flex items-center gap-4 mb-5">
							<span class="cluster-tag {getClusterColor(cluster.cluster_code)}">
								{cluster.cluster_code}
							</span>
							<div class="flex items-baseline gap-3">
								<h2 class="blueprint-heading text-xl sm:text-2xl">{cluster.cluster_name}</h2>
								<span class="program-count">({cluster.hs_programs.length})</span>
							</div>
						</div>

						<!-- HS Programs -->
						<div class="space-y-3">
							{#each cluster.hs_programs as program (program.name)}
								{@const programKey = `${cluster.cluster_code}|${program.name}`}
								{@const isExpanded = expandedPrograms.has(programKey)}

								<div class="pathway-card">
									<!-- Program Header (Clickable) -->
									<button
										on:click={() => toggleProgram(programKey)}
										class="expand-btn"
										aria-expanded={isExpanded}
									>
										<!-- Chevron -->
										<svg
											class="w-5 h-5 shrink-0 chevron-icon text-msde-navy dark:text-msde-gold {isExpanded ? 'expanded' : ''}"
											fill="none" stroke="currentColor" viewBox="0 0 24 24"
										>
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
										</svg>

										<!-- Program Name -->
										<div class="flex-1 min-w-0">
											<h3 class="text-lg font-semibold text-gray-900 dark:text-white text-left">
												{program.name}
											</h3>
											<p class="program-count mt-0.5 text-left">
												{program.ircs.length} IRC{program.ircs.length !== 1 ? 's' : ''} ·
												{program.community_colleges.length} CC{program.community_colleges.length !== 1 ? 's' : ''} ·
												{program.universities.length} Universit{program.universities.length !== 1 ? 'ies' : 'y'}
											</p>
										</div>

										<!-- Visual indicator -->
										<div class="hidden sm:flex items-center gap-1.5 opacity-60">
											{#if program.ircs.length > 0}
												<span class="w-2 h-2 rounded-full bg-amber-500"></span>
											{/if}
											{#if program.community_colleges.length > 0}
												<span class="w-2 h-2 rounded-full bg-emerald-500"></span>
											{/if}
											{#if program.universities.length > 0}
												<span class="w-2 h-2 rounded-full bg-violet-500"></span>
											{/if}
										</div>
									</button>

									<!-- Expanded Content -->
									{#if isExpanded}
										<div class="pathway-content-enter border-t border-gray-100 dark:border-slate-700 p-5 sm:p-6">
											<div class="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8">

												<!-- Column 1: IRCs -->
												<div>
													<div class="column-header">
														<span class="text-lg">◈</span>
														<h4>Credentials</h4>
													</div>
													{#if program.ircs.length > 0}
														<div class="space-y-2">
															{#each program.ircs as irc}
																<div class="irc-pill">
																	{irc}
																</div>
															{/each}
														</div>
													{:else}
														<p class="text-sm text-gray-400 dark:text-gray-500 italic">No IRCs listed</p>
													{/if}
													<p class="mt-4 text-xs text-gray-500 dark:text-gray-400">
														Credentials earned through your HS program
													</p>
												</div>

												<!-- Column 2: Community Colleges -->
												<div>
													<div class="column-header">
														<span class="text-lg">⬡</span>
														<h4>Community Colleges</h4>
													</div>
													{#if program.community_colleges.length > 0}
														<div class="space-y-2.5">
															{#each program.community_colleges as inst}
																<div class="cc-card">
																	<div class="font-semibold text-emerald-900 dark:text-emerald-100 text-sm pr-4">{inst.name}</div>
																	{#if inst.program}
																		<div class="text-sm text-emerald-800 dark:text-emerald-200 mt-1 leading-snug">{inst.program}</div>
																	{/if}
																	{#if inst.degree_type}
																		<div class="text-xs text-emerald-700 dark:text-emerald-300 mt-1 font-mono">{inst.degree_type}</div>
																	{/if}
																</div>
															{/each}
														</div>
													{:else}
														<p class="text-sm text-gray-400 dark:text-gray-500 italic">No CC programs listed</p>
													{/if}
												</div>

												<!-- Column 3: Universities -->
												<div>
													<div class="column-header">
														<span class="text-lg">◆</span>
														<h4>Universities</h4>
													</div>
													{#if program.universities.length > 0}
														<div class="space-y-2.5">
															{#each program.universities as inst}
																<div class="uni-card">
																	<div class="font-semibold text-violet-900 dark:text-violet-100 text-sm pr-4">{inst.name}</div>
																	{#if inst.program}
																		<div class="text-sm text-violet-800 dark:text-violet-200 mt-1 leading-snug">{inst.program}</div>
																	{/if}
																	{#if inst.degree_type}
																		<div class="text-xs text-violet-700 dark:text-violet-300 mt-1 font-mono">{inst.degree_type}</div>
																	{/if}
																</div>
															{/each}
														</div>
													{:else}
														<p class="text-sm text-gray-400 dark:text-gray-500 italic">No university programs listed</p>
													{/if}
												</div>
											</div>

											<!-- Vision Note -->
											<div class="mt-8 pt-5 border-t border-dashed border-gray-200 dark:border-slate-700">
												<p class="text-xs text-gray-500 dark:text-gray-400 text-center max-w-xl mx-auto leading-relaxed">
													<strong>Future Vision:</strong> IRCs earned in <span class="font-medium">{program.name}</span> could grant credit at these institutions—advocacy needed to make this connection official.
												</p>
											</div>
										</div>
									{/if}
								</div>
							{/each}
						</div>
					</section>
				{/each}
			</div>

			<!-- Footer Summary -->
			<div class="mt-12 text-center">
				<span class="summary-pill">
					{filteredData.length} cluster{filteredData.length !== 1 ? 's' : ''} · {totalPrograms} programs · {totalConnections} postsec pathways
				</span>
			</div>
		{/if}
	</div>
</div>
