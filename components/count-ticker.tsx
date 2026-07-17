"use client";

import { useMotionValueEvent, useSpring } from "motion/react";
import { useEffect, useState } from "react";

export function CountTicker({ value }: { value: number }) {
  const spring = useSpring(value, { stiffness: 240, damping: 28 });
  const [display, setDisplay] = useState(value);

  useEffect(() => {
    spring.set(value);
  }, [spring, value]);

  useMotionValueEvent(spring, "change", (latest) => setDisplay(Math.round(latest)));
  return <span className="tnum">{display}</span>;
}
