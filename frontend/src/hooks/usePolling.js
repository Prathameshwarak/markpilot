import { useEffect, useRef } from "react";

/** Poll only while the browser tab is visible; clears timers on unmount. */
export default function usePolling(callback, intervalMs = 30000, enabled = true) {
  const callbackRef = useRef(callback);
  useEffect(() => { callbackRef.current = callback; }, [callback]);
  useEffect(() => {
    if (!enabled) return undefined;
    let timer;
    const tick = () => {
      if (document.visibilityState === "visible") callbackRef.current?.();
    };
    timer = window.setInterval(tick, intervalMs);
    const onVisibility = () => { if (document.visibilityState === "visible") tick(); };
    document.addEventListener("visibilitychange", onVisibility);
    return () => { window.clearInterval(timer); document.removeEventListener("visibilitychange", onVisibility); };
  }, [intervalMs, enabled]);
}
