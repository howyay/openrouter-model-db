<script>
    let { min, max, step = 1, currentMin = $bindable(), currentMax = $bindable(), onchange } = $props();

    let trackEl;
    let dragging = $state(null); // 'min' | 'max' | null

    function pct(val) {
        if (max === min) return 0;
        return ((val - min) / (max - min)) * 100;
    }

    function valFromX(clientX) {
        const rect = trackEl.getBoundingClientRect();
        const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
        const raw = min + ratio * (max - min);
        // Snap to step
        return Math.round(raw / step) * step;
    }

    function onPointerDown(thumb, e) {
        e.preventDefault();
        dragging = thumb;
        trackEl.setPointerCapture(e.pointerId);
    }

    function onPointerMove(e) {
        if (!dragging) return;
        const val = valFromX(e.clientX);
        if (dragging === 'min') {
            currentMin = Math.min(val, currentMax);
            currentMin = Math.max(currentMin, min);
        } else {
            currentMax = Math.max(val, currentMin);
            currentMax = Math.min(currentMax, max);
        }
    }

    function onPointerUp(e) {
        if (!dragging) return;
        dragging = null;
        trackEl.releasePointerCapture(e.pointerId);
        onchange?.();
    }

    function onTrackClick(e) {
        if (e.target.classList.contains('thumb')) return;
        const val = valFromX(e.clientX);
        const distMin = Math.abs(val - currentMin);
        const distMax = Math.abs(val - currentMax);
        if (distMin <= distMax) {
            currentMin = Math.max(min, Math.min(val, currentMax));
        } else {
            currentMax = Math.min(max, Math.max(val, currentMin));
        }
        onchange?.();
    }

    function formatVal(v) {
        if (Number.isInteger(step) && step >= 1) return Math.round(v).toLocaleString();
        return v.toFixed(1);
    }
</script>

<div class="dual-range">
    <span class="range-label">{formatVal(currentMin)}</span>
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
        class="track"
        bind:this={trackEl}
        onpointermove={onPointerMove}
        onpointerup={onPointerUp}
        onclick={onTrackClick}
    >
        <div class="track-bg"></div>
        <div
            class="track-fill"
            style="left: {pct(currentMin)}%; right: {100 - pct(currentMax)}%"
        ></div>
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div
            class="thumb"
            style="left: {pct(currentMin)}%"
            onpointerdown={(e) => onPointerDown('min', e)}
            role="slider"
            aria-valuemin={min}
            aria-valuemax={currentMax}
            aria-valuenow={currentMin}
            tabindex="0"
        ></div>
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div
            class="thumb"
            style="left: {pct(currentMax)}%"
            onpointerdown={(e) => onPointerDown('max', e)}
            role="slider"
            aria-valuemin={currentMin}
            aria-valuemax={max}
            aria-valuenow={currentMax}
            tabindex="0"
        ></div>
    </div>
    <span class="range-label">{formatVal(currentMax)}</span>
</div>

<style>
    .dual-range {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 4px 0;
    }

    .range-label {
        font-family: var(--font-data);
        font-size: 13px;
        color: var(--text-dim);
        white-space: nowrap;
        min-width: 28px;
        flex-shrink: 0;
    }

    .range-label:first-child { text-align: right; }
    .range-label:last-child { text-align: left; }

    .track {
        position: relative;
        flex: 1;
        height: 24px;
        display: flex;
        align-items: center;
        cursor: pointer;
        touch-action: none;
    }

    .track-bg {
        position: absolute;
        left: 0;
        right: 0;
        height: 4px;
        border-radius: 2px;
        background: var(--bg-elevated);
    }

    .track-fill {
        position: absolute;
        height: 4px;
        border-radius: 2px;
        background: var(--accent);
        opacity: 0.6;
    }

    .thumb {
        position: absolute;
        width: 14px;
        height: 14px;
        border-radius: 50%;
        background: var(--accent);
        border: 2px solid var(--bg);
        transform: translateX(-50%);
        cursor: grab;
        z-index: 1;
        transition: box-shadow 0.15s;
    }

    .thumb:hover, .thumb:active {
        box-shadow: 0 0 0 4px var(--accent-muted);
        cursor: grabbing;
    }
</style>
