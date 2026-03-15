import { describe, expect, it, vi } from "vitest";

import { useDomMetrics } from "../use-dom-metrics";

describe("useDomMetrics", () => {
    it("measures mount time", () => {
        const { mountTimeMs, markAfterMount, markBeforeMount } = useDomMetrics();

        vi.spyOn(performance, "now")
            .mockReturnValueOnce(100)
            .mockReturnValueOnce(115);

        markBeforeMount();
        markAfterMount();

        expect(mountTimeMs.value).toBe(15);
    });

    it("counts DOM nodes", () => {
        const container = document.createElement("div");
        const span1 = document.createElement("span");
        const span2 = document.createElement("span");
        container.appendChild(span1);
        container.appendChild(span2);
        document.body.appendChild(container);

        const { domNodeCount, startObserving } = useDomMetrics();
        startObserving(container);

        expect(domNodeCount.value).toBe(2);

        document.body.removeChild(container);
    });
});
