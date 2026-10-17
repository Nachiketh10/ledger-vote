import { useEffect, useState } from "react";

function getTimeParts(targetDate) {
  const diff = Math.max(0, new Date(targetDate).getTime() - Date.now());
  const days = Math.floor(diff / 86400000);
  const hours = Math.floor((diff % 86400000) / 3600000);
  const minutes = Math.floor((diff % 3600000) / 60000);
  const seconds = Math.floor((diff % 60000) / 1000);
  return { diff, days, hours, minutes, seconds };
}

export function useCountdown(targetDate) {
  const [parts, setParts] = useState(() => getTimeParts(targetDate));

  useEffect(() => {
    const id = setInterval(() => setParts(getTimeParts(targetDate)), 1000);
    return () => clearInterval(id);
  }, [targetDate]);

  return parts;
}
