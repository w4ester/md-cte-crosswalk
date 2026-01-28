<script lang="ts">
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	onMount(() => { window.location.href = `${base}/crosswalk`; });
</script>

<svelte:head>
	<title>Maryland CTE Crosswalk</title>
</svelte:head>

<div class="flex items-center justify-center min-h-screen">
	<p class="text-gray-500">Redirecting to crosswalk...</p>
</div>
