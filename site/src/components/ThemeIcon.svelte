<script>
    let { mode, size = 16 } = $props();
</script>

{#if mode === 'light'}
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <circle cx="12" cy="12" r="4.5" />
        <path d="M12 2.5v2.5" />
        <path d="M12 19v2.5" />
        <path d="m4.93 4.93 1.77 1.77" />
        <path d="m17.3 17.3 1.77 1.77" />
        <path d="M2.5 12H5" />
        <path d="M19 12h2.5" />
        <path d="m4.93 19.07 1.77-1.77" />
        <path d="m17.3 6.7 1.77-1.77" />
    </svg>
{:else if mode === 'dark'}
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M21 12.8A8.8 8.8 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" />
    </svg>
{:else}
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <rect x="3" y="4" width="18" height="12" rx="2" />
        <path d="M8 20h8" />
        <path d="M12 16v4" />
    </svg>
{/if}
