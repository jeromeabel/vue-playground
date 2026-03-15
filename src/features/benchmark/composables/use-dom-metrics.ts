import { getCurrentInstance, onUnmounted, ref } from "vue";

export function useDomMetrics() {
    const mountTimeMs = ref(0);
    const domNodeCount = ref(0);
    const fps = ref(0);

    let t0 = 0;
    let observer: MutationObserver | null = null;
    let rafId = 0;
    let frameCount = 0;
    let lastFpsTime = 0;

    function markBeforeMount() {
        t0 = performance.now();
    }

    function markAfterMount() {
        mountTimeMs.value = Math.round(performance.now() - t0);
    }

    function countNodes(root: Element): number {
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT);
        let count = 0;
        while (walker.nextNode()) {
            count++;
        }
        return count;
    }

    function startObserving(container: HTMLElement) {
        domNodeCount.value = countNodes(container);

        observer?.disconnect();
        observer = new MutationObserver(() => {
            domNodeCount.value = countNodes(container);
        });
        observer.observe(container, { childList: true, subtree: true });
    }

    function startFpsCounter() {
        stopFpsCounter();
        lastFpsTime = performance.now();
        frameCount = 0;

        function tick() {
            frameCount++;
            const now = performance.now();
            const elapsed = now - lastFpsTime;
            if (elapsed >= 1000) {
                fps.value = Math.round((frameCount * 1000) / elapsed);
                frameCount = 0;
                lastFpsTime = now;
            }
            rafId = requestAnimationFrame(tick);
        }

        rafId = requestAnimationFrame(tick);
    }

    function stopFpsCounter() {
        if (rafId) {
            cancelAnimationFrame(rafId);
            rafId = 0;
        }
    }

    function cleanup() {
        observer?.disconnect();
        observer = null;
        stopFpsCounter();
    }

    if (getCurrentInstance()) {
        onUnmounted(cleanup);
    }

    return {
        mountTimeMs,
        domNodeCount,
        fps,
        markBeforeMount,
        markAfterMount,
        startObserving,
        startFpsCounter,
        stopFpsCounter,
    };
}
